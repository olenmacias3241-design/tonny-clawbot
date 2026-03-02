"""Core Claw Bot implementation."""

import uuid
from typing import Dict, Optional
from src.models.message import Conversation, BotRequest, BotResponse
from src.bot.ai_provider import get_ai_provider, AIProvider
from src.utils.logger import log
from src.utils.config import get_settings


class ClawBot:
    """Main Claw Bot class."""

    @staticmethod
    def _normalize_for_match(text: str) -> str:
        """全角英数转半角，便于命中「ＰＰＴ」「ppt」等。"""
        if not text:
            return text
        out = []
        for c in text:
            if "\uff01" <= c <= "\uff5e":
                out.append(chr(ord(c) - 0xFEE0))
            else:
                out.append(c)
        return "".join(out)

    def __init__(self, ai_provider: Optional[str] = None):
        """Initialize Claw Bot."""
        self.settings = get_settings()
        self.ai_provider: AIProvider = get_ai_provider(ai_provider)
        self.conversations: Dict[str, Conversation] = {}
        log.info("Claw Bot initialized")

    def _get_or_create_conversation(self, conversation_id: Optional[str] = None) -> Conversation:
        """Get existing conversation or create a new one."""
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]

        new_id = conversation_id or str(uuid.uuid4())
        conversation = Conversation(id=new_id)

        # Add system message
        conversation.add_message(
            role="system",
            content="You are Claw Bot, an intelligent AI assistant. You are helpful, harmless, and honest.",
        )

        self.conversations[new_id] = conversation
        log.info(f"Created new conversation: {new_id}")
        return conversation

    @staticmethod
    def _build_conversation_context(messages: list, max_messages: int = 30, max_chars: int = 8000) -> str:
        """把对话消息格式化为供「做文档/做PPT」使用的上下文，包含用户提供的资料与讨论内容。"""
        lines = []
        count = 0
        total = 0
        for m in messages:
            if getattr(m, "role", None) == "system":
                continue
            role = getattr(m, "role", "user")
            content = (getattr(m, "content", None) or "").strip()
            if not content:
                continue
            label = "用户" if role == "user" else "助手"
            line = f"{label}：{content}"
            if total + len(line) + 1 > max_chars and lines:
                break
            lines.append(line)
            total += len(line) + 1
            count += 1
            if count >= max_messages:
                break
        return "\n".join(lines) if lines else ""

    async def _classify_generation_intent(
        self, msg_raw: str, conversation: Conversation
    ) -> Optional[str]:
        """
        根据当前对话和用户最新消息，用 AI 判断用户是否希望生成 PPT/文档/Word/表格。
        返回 generate_ppt | generate_document | generate_word | generate_table | None。
        用于在关键词未命中时仍能理解「把上面的做到PPT里」等表述。
        """
        ctx = self._build_conversation_context(conversation.messages[:-1], max_messages=8, max_chars=2000)
        prompt = f"""用户最新一条消息：「{msg_raw}」
对话上下文（前几条，供参考）：
{ctx[:1500] if ctx else '（无）'}

请判断用户此刻是否希望你**直接生成并给出下载链接**的产物。只选其一回复，不要任何解释：
- generate_ppt：用户希望生成 PPT/幻灯片/汇报（包括「把上面的内容做到PPT里」「把对话内容做成汇报」等）
- generate_document：用户希望生成 Markdown 文档
- generate_word：用户希望生成 Word 文档
- generate_table：用户希望生成表格/Excel/CSV
- none：只是普通聊天、追问、或不需要生成文件

只回复上述英文标签之一。"""
        try:
            raw = await self.ai_provider.generate_response(
                [{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=20,
            )
            label = (raw or "").strip().lower()
            for k in ("generate_ppt", "generate_document", "generate_word", "generate_table"):
                if k in label:
                    return k
            return None
        except Exception as e:
            log.warning(f"Intent classification failed: {e}")
            return None

    async def process_message(self, request: BotRequest) -> BotResponse:
        """Process a user message and generate a response."""
        try:
            conversation = self._get_or_create_conversation(request.conversation_id)
            conversation.add_message(
                role="user", content=request.message, metadata=request.metadata
            )
            msg_raw = (request.message or "").strip()
            msg_norm = self._normalize_for_match(msg_raw)
            msg = msg_norm.lower()
            # 聊天中直接做表格：包含「表格」「做表」等，或短消息里带「表」
            _table_keywords = (
                "表格", "做表", "生成表", "excel", "csv", "列",
                "成绩表", "数据表", "销售表", "人员表", "统计表", "名单表",
                "名单", "明细表", "汇总表", "做一个表", "弄个表", "学生表",
                "生成表格", "做个表", "给我一个表", "table",
            )
            has_table_keyword = any(k in (request.message or "") for k in _table_keywords)
            short_msg_with_biao = len(msg_raw) < 500 and "表" in msg_raw
            is_table = len(msg_raw) < 600 and (has_table_keyword or short_msg_with_biao)
            # 聊天中直接做 PPT：规范化后匹配，并放宽「做+ppt/幻灯片/汇报/演示」即视为做 PPT
            _ppt_any = ("ppt", "pptx", "幻灯片", "汇报", "演示")
            _ppt_phrases = (
                "做好ppt", "做ppt", "帮我做ppt", "直接做好ppt", "生成ppt", "做一个ppt",
                "直接把ppt做好", "把ppt做好", "直接做好", "做个ppt", "弄个ppt",
                "帮我做", "直接做", "做一个", "做一份", "生成一个",
                "加入到ppt", "加入到 ppt", "做到ppt里", "做到 ppt", "把上面的内容加入",
                "把上面的内容做到", "把这些做到ppt", "把刚才说的做成", "根据上面的内容做",
                "把对话内容做成", "上面的内容做", "内容加入到ppt", "做成ppt", "做成 ppt",
                "把如上的内容", "如上的内容添加", "添加到ppt", "添加到 ppt", "把以上内容",
            )
            has_ppt_topic = any(x in msg for x in _ppt_any)
            has_ppt_phrase = any(k in msg for k in _ppt_phrases)
            short_and_do_ppt = len(msg_raw) < 120 and ("做" in msg_raw or "弄" in msg_raw or "生成" in msg_raw or "加入" in msg_raw) and has_ppt_topic
            is_ppt = has_ppt_phrase or short_and_do_ppt or (has_ppt_topic and ("做" in msg_raw or "加入" in msg_raw))
            _doc_keywords = (
                "创建文档", "写文档", "生成文档", "做个文档", "写一份文档", "写一个文档",
                "帮我写文档", "帮我写一份文档", "生成一份文档", "创建一份文档",
            )
            is_doc = any(k in msg_raw for k in _doc_keywords) and len(msg_raw) < 800
            _word_keywords = (
                "做word", "做 word", "生成word", "生成 word", "写word", "写 word",
                "word文档", "生成word文档", "做个word", "写一份word", "帮我做word", "生成一份word",
            )
            is_word = any(k in msg_raw for k in _word_keywords) and len(msg_raw) < 800
            # 关键词未命中时，根据当前语境用 AI 判断是否要做 PPT/文档/Word/表格（避免枚举不全）
            if not (is_table or is_ppt or is_doc or is_word) and len(msg_raw) <= 400:
                hint_words = (
                    "ppt", "文档", "word", "表格", "幻灯片", "汇报", "演示",
                    "做成", "生成", "写到", "放到", "加入", "添加", "弄成", "搞成", "导出",
                    "做到", "放进", "弄到", "搞到", "上面的", "如上的", "以上的", "对话内容", "这些内容",
                )
                if any(h in msg_raw for h in hint_words):
                    intent = await self._classify_generation_intent(msg_raw, conversation)
                    if intent == "generate_ppt":
                        is_ppt = True
                        log.info(f"Intent classified as PPT: {msg_raw[:60]}...")
                    elif intent == "generate_document":
                        is_doc = True
                        log.info(f"Intent classified as document: {msg_raw[:60]}...")
                    elif intent == "generate_word":
                        is_word = True
                        log.info(f"Intent classified as Word: {msg_raw[:60]}...")
                    elif intent == "generate_table":
                        is_table = True
                        log.info(f"Intent classified as table: {msg_raw[:60]}...")
            if is_table and not is_ppt:
                log.info(f"Table intent detected, generating table for: {msg_raw[:80]}...")
                try:
                    from src.services.content_generator import generate_table_and_save
                    csv_name, xlsx_name = await generate_table_and_save(request.message.strip())
                    base = "/api/download/generated"
                    reply = "表格已生成。\n\n" + f"[下载 CSV]({base}/{csv_name})"
                    if xlsx_name:
                        reply += f"\n[下载 Excel]({base}/{xlsx_name})"
                    else:
                        reply += "\n（未安装 openpyxl，暂无法生成 Excel；CSV 可用 Excel 直接打开。安装：pip install openpyxl）"
                    log.info(f"Table generated: {csv_name}, xlsx={xlsx_name}")
                    conversation.add_message(role="assistant", content=reply)
                    return BotResponse(
                        message=reply,
                        conversation_id=conversation.id,
                        metadata={"message_count": len(conversation.messages)},
                    )
                except Exception as e:
                    log.warning(f"Generate table in chat failed: {e}")
                    err = str(e)
                    if "403" in err or "region" in err.lower():
                        reply = f"表格生成失败（API 或地区限制）：{err}\n请检查模型与 Key 后重试。"
                    else:
                        reply = f"表格生成失败，请换一种描述或稍后重试。\n错误：{err}"
                    conversation.add_message(role="assistant", content=reply)
                    return BotResponse(
                        message=reply,
                        conversation_id=conversation.id,
                        metadata={"message_count": len(conversation.messages)},
                        error=err,
                    )
            if is_ppt:
                log.info(f"PPT intent detected, msg_norm={msg_norm[:100]!r}")
                try:
                    from src.services.content_generator import (
                        generate_ppt_and_save,
                        generate_ppt_from_structured_text,
                    )
                    base = "/api/download/generated"
                    # 若消息里是「幻灯片1：封面」+ 标题/副标题 + 要点 的格式，直接解析生成
                    if "幻灯片" in msg_raw and ("标题：" in msg_raw or "副标题：" in msg_raw):
                        name = generate_ppt_from_structured_text(msg_raw)
                        if name:
                            reply = f"PPT 已根据你提供的内容生成。\n\n[下载 PPT]({base}/{name})"
                            conversation.add_message(role="assistant", content=reply)
                            return BotResponse(
                                message=reply,
                                conversation_id=conversation.id,
                                metadata={"message_count": len(conversation.messages)},
                            )
                    # 否则按主题用 AI 生成大纲再做成 PPT
                    title = "汇报"
                    topic = msg_raw
                    for t in ("的ppt", "的 ppt", "汇报", "演示", "帮我直接做好", "直接做好", "做好", "做一个", "做一份"):
                        if t in msg:
                            topic = msg_raw.replace(t, " ").strip() or topic
                            break
                    topic = topic.strip() or "通用汇报"
                    ctx = self._build_conversation_context(conversation.messages[:-1])
                    # 无历史对话时，把本条消息当作「用户提供的需求与资料」
                    if not (ctx and ctx.strip()) and msg_raw:
                        ctx = f"用户（本次需求与资料）：\n{msg_raw}"
                    # 用户说「把上面的内容/把这些/把刚才说的/如上的内容 加入/做到/添加 PPT」且确有对话历史时，用对话内容做主题
                    if ctx and ctx.strip() and any(k in msg_raw for k in (
                        "上面的内容", "这些内容", "刚才说的", "对话内容", "上面说的", "如上的内容", "以上内容",
                    )):
                        if any(k in msg_raw for k in ("加入", "做到", "做成", "做到ppt", "加入到", "添加")):
                            title = "汇报"
                            topic = "根据当前对话内容生成汇报，请按对话中的要点整理成页。"
                    if len(topic) > 50 and title != "汇报":
                        title = topic[:30].strip() + "…"
                    elif title == "汇报" and topic and topic != "通用汇报" and len(topic) <= 50:
                        title = topic or title
                    name = await generate_ppt_and_save(title, topic, conversation_context=ctx)
                    reply = f"PPT 已生成。\n\n[下载 PPT]({base}/{name})"
                    conversation.add_message(role="assistant", content=reply)
                    return BotResponse(
                        message=reply,
                        conversation_id=conversation.id,
                        metadata={"message_count": len(conversation.messages)},
                    )
                except Exception as e:
                    log.warning(f"Generate ppt in chat failed: {e}")
                    err = str(e)
                    if "403" in err or "region" in err.lower():
                        reply = f"PPT 生成失败（API 或地区限制）：{err}\n请检查模型与 Key 后重试。"
                    else:
                        reply = f"PPT 生成失败，请稍后重试或换一个主题。\n错误：{err}"
                    conversation.add_message(role="assistant", content=reply)
                    return BotResponse(
                        message=reply,
                        conversation_id=conversation.id,
                        metadata={"message_count": len(conversation.messages)},
                        error=err,
                    )

            if is_word:
                log.info(f"Word intent detected: {msg_raw[:80]}...")
                try:
                    from src.services.content_generator import generate_docx_and_save
                    ctx = self._build_conversation_context(conversation.messages[:-1])
                    if not (ctx and ctx.strip()) and msg_raw:
                        ctx = f"用户（本次需求与资料）：\n{msg_raw}"
                    name = await generate_docx_and_save(msg_raw.strip(), conversation_context=ctx)
                    base = "/api/download/generated"
                    reply = f"Word 文档已生成。\n\n[下载 Word]({base}/{name})"
                    conversation.add_message(role="assistant", content=reply)
                    return BotResponse(
                        message=reply,
                        conversation_id=conversation.id,
                        metadata={"message_count": len(conversation.messages)},
                    )
                except Exception as e:
                    log.warning(f"Generate word failed: {e}")
                    reply = f"Word 生成失败：{e}"
                    conversation.add_message(role="assistant", content=reply)
                    return BotResponse(
                        message=reply,
                        conversation_id=conversation.id,
                        metadata={"message_count": len(conversation.messages)},
                        error=str(e),
                    )

            # 聊天操控电脑（传统龙虾能力）：运行白名单内命令
            if getattr(self.settings, "enable_computer_control", False):
                _run_keywords = ("运行", "执行", "跑一下", "帮我运行", "帮我执行", "帮我跑", "操控电脑", "跑 ")
                if any(k in msg_raw for k in _run_keywords):
                    from src.services.computer_control import run_command_safe
                    ok, out = run_command_safe(msg_raw)
                    reply = out
                    log.info(f"Computer control: ok={ok}, out_len={len(reply)}")
                    conversation.add_message(role="assistant", content=reply)
                    return BotResponse(
                        message=reply,
                        conversation_id=conversation.id,
                        metadata={"message_count": len(conversation.messages)},
                    )

            if is_doc:
                log.info(f"Document intent detected: {msg_raw[:80]}...")
                try:
                    from src.services.content_generator import generate_document_and_save
                    ctx = self._build_conversation_context(conversation.messages[:-1])
                    if not (ctx and ctx.strip()) and msg_raw:
                        ctx = f"用户（本次需求与资料）：\n{msg_raw}"
                    name = await generate_document_and_save(msg_raw.strip(), conversation_context=ctx)
                    base = "/api/download/generated"
                    reply = f"文档已生成。\n\n[下载 Markdown]({base}/{name})"
                    conversation.add_message(role="assistant", content=reply)
                    return BotResponse(
                        message=reply,
                        conversation_id=conversation.id,
                        metadata={"message_count": len(conversation.messages)},
                    )
                except Exception as e:
                    log.warning(f"Generate document failed: {e}")
                    reply = f"文档生成失败：{e}"
                    conversation.add_message(role="assistant", content=reply)
                    return BotResponse(
                        message=reply,
                        conversation_id=conversation.id,
                        metadata={"message_count": len(conversation.messages)},
                        error=str(e),
                    )

            # 正常对话
            recent_messages = conversation.get_recent_messages(
                self.settings.max_context_messages
            )
            messages = [
                {"role": m.role, "content": m.content} for m in recent_messages
            ]
            log.info(f"Generating response for conversation: {conversation.id}")
            model_override = getattr(request, "model", None) if request else None
            response_content = await self.ai_provider.generate_response(
                messages, model=model_override
            )
            conversation.add_message(role="assistant", content=response_content)
            return BotResponse(
                message=response_content,
                conversation_id=conversation.id,
                metadata={"message_count": len(conversation.messages)},
            )

        except Exception as e:
            log.error(f"Error processing message: {e}")
            err_msg = str(e)
            settings = get_settings()
            if "403" in err_msg or "Forbidden" in err_msg:
                model = getattr(settings, "openai_model", "") if settings.default_ai_provider == "openai" else getattr(settings, "anthropic_model", "")
                if "region" in err_msg.lower() or "not available" in err_msg.lower():
                    hint = (
                        f"当前模型在你所在地区不可用。当前模型: {model}\n\n"
                        "若使用 OpenRouter，建议在 .env 改用对地区限制较少的模型，例如：\n"
                        "OPENAI_MODEL=meta-llama/llama-3.1-8b-instant\n"
                        "或 OPENAI_MODEL=llama-3.1-8b-instant\n"
                        "或 OPENAI_MODEL=llama-3.3-70b-versatile\n\n"
                        "或在聊天页「模型」下拉里直接选上述 Llama 模型再发消息。"
                    )
                else:
                    hint = (
                        f"API 返回 403。当前模型: {model}\n\n"
                        "建议在 .env 中改用通用模型（多数账户可用）：\n"
                        "OPENAI_MODEL=gpt-4o-mini 或 OPENAI_MODEL=gpt-3.5-turbo\n\n"
                        "若 Key 有效仍 403，请到 OpenAI/OpenRouter 控制台检查模型权限与账户余额。"
                    )
            elif "API key" in err_msg or "not configured" in err_msg or "configured" in err_msg:
                hint = "请检查 .env：OPENAI_API_KEY 或 ANTHROPIC_API_KEY，以及 DEFAULT_AI_PROVIDER=openai 或 anthropic。"
            else:
                hint = err_msg
            return BotResponse(
                message=f"抱歉，处理消息时出错。{hint}",
                conversation_id=request.conversation_id or "error",
                error=err_msg,
            )

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self.conversations.get(conversation_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            log.info(f"Deleted conversation: {conversation_id}")
            return True
        return False

    def list_conversations(self) -> list[str]:
        """List all conversation IDs."""
        return list(self.conversations.keys())
