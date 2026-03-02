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
            )
            has_ppt_topic = any(x in msg for x in _ppt_any)
            has_ppt_phrase = any(k in msg for k in _ppt_phrases)
            short_and_do_ppt = len(msg_raw) < 120 and ("做" in msg_raw or "弄" in msg_raw or "生成" in msg_raw) and has_ppt_topic
            is_ppt = has_ppt_phrase or short_and_do_ppt or has_ppt_topic and "做" in msg_raw
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
                    if len(topic) > 50:
                        title = topic[:30].strip() + "…"
                    else:
                        title = topic or title
                    name = await generate_ppt_and_save(title, topic)
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
                    name = await generate_docx_and_save(msg_raw.strip())
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
                    name = await generate_document_and_save(msg_raw.strip())
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
