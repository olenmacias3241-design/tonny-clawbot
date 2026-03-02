"""AI-powered report generation service for activities."""

from datetime import datetime
from typing import List, Optional

from src.bot.ai_provider import get_ai_provider, AIProvider
from src.models.activity import ActivityEvent
from src.utils.logger import log


class ReportService:
    """Service to generate daily/weekly reports from activity events."""

    def __init__(self, ai_provider: Optional[str] = None):
        self.ai: AIProvider = get_ai_provider(ai_provider)

    async def generate_user_daily_report(
        self,
        user_name: str,
        date: datetime,
        activities: List[ActivityEvent],
        language: str = "zh",
    ) -> str:
        """Generate a natural language daily report for a user."""
        log.info(
            f"Generating daily report for user={user_name}, "
            f"date={date.date()}, activities={len(activities)}"
        )

        # Prepare a compact, model-friendly summary of activities
        activity_summaries = [
            {
                "time": a.timestamp.isoformat(),
                "source": a.source,
                "type": a.type,
                "project": a.project_name,
                "title": a.title,
                "description": a.description,
            }
            for a in sorted(activities, key=lambda x: x.timestamp)
        ]

        system_prompt_zh = (
            "你是一个资深的工程管理助手，擅长根据工程活动记录（代码提交、PR、任务变更、文档更新等）"
            "自动生成清晰、客观、可读性强的工作日报。"
            "请避免流水账，按主题归纳，突出产出、进展、风险与下一步计划。"
        )

        system_prompt_en = (
            "You are an experienced engineering manager assistant. "
            "Given a list of activity events (commits, pull requests, task changes, "
            "documentation updates, etc.), you generate a clear and concise daily work report. "
            "Group related activities, highlight outcomes, progress, risks, and next steps."
        )

        system_prompt = system_prompt_zh if language.startswith("zh") else system_prompt_en

        user_prompt = {
            "user_name": user_name,
            "date": date.strftime("%Y-%m-%d"),
            "activities": activity_summaries,
            "requirements": {
                "language": "zh" if language.startswith("zh") else "en",
                "sections": [
                    "今日主要工作内容（按模块/项目分组）",
                    "关键产出与里程碑",
                    "遇到的问题 / 风险点",
                    "明日/下一步计划（如果从活动中能推断）",
                ]
                if language.startswith("zh")
                else [
                    "Main work items today (grouped by project/module)",
                    "Key outcomes and milestones",
                    "Issues / risks encountered",
                    "Plan for tomorrow / next steps (if can be inferred)",
                ],
            },
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Here are today's activity events for one person. "
                    "Please generate a structured daily work report as requested.\n\n"
                    f"Input (JSON):\n{user_prompt}"
                ),
            },
        ]

        try:
            response = await self.ai.generate_response(
                messages, temperature=0.4, max_tokens=1200
            )
            return response
        except Exception as e:
            # Fallback: return a deterministic, rule-based summary so the pipeline can run
            log.error(f"AI report generation failed, using fallback summary: {e}")
            return self._fallback_daily_report(
                user_name=user_name, date=date, activities=activities, language=language
            )

    def _fallback_daily_report(
        self,
        user_name: str,
        date: datetime,
        activities: List[ActivityEvent],
        language: str,
    ) -> str:
        activities_sorted = sorted(activities, key=lambda x: x.timestamp)
        if language.startswith("zh"):
            lines = [
                f"【日报（兜底汇总）】{user_name} - {date.strftime('%Y-%m-%d')}",
                "",
                f"活动条数：{len(activities_sorted)}",
                "",
                "今日主要工作内容：",
            ]
            if not activities_sorted:
                lines.append("- 无活动记录（可能是 user_id 匹配规则不一致，或当天确实没有可见活动）")
            else:
                for a in activities_sorted[:200]:
                    ts = a.timestamp.isoformat()
                    proj = a.project_name or "-"
                    title = a.title or a.type
                    lines.append(f"- [{ts}] ({a.source}/{proj}) {a.type}: {title}")
            lines += [
                "",
                "风险/提示：",
                "- 若需要更像人写的总结，请配置可用的大模型 API Key（当前 AI 调用失败已自动降级）。",
            ]
            return "\n".join(lines)
        else:
            lines = [
                f"Daily report (fallback) - {user_name} - {date.strftime('%Y-%m-%d')}",
                "",
                f"Activity count: {len(activities_sorted)}",
                "",
                "Main activities:",
            ]
            if not activities_sorted:
                lines.append("- No activity records found (user_id mapping may not match).")
            else:
                for a in activities_sorted[:200]:
                    ts = a.timestamp.isoformat()
                    proj = a.project_name or "-"
                    title = a.title or a.type
                    lines.append(f"- [{ts}] ({a.source}/{proj}) {a.type}: {title}")
            lines += [
                "",
                "Notes:",
                "- Configure a working LLM API key for a higher quality narrative report.",
            ]
            return "\n".join(lines)

