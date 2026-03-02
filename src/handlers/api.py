"""FastAPI handlers for Claw Bot."""

import sys
from pathlib import Path

# 确保当前 Python 所在 venv 的 site-packages 优先，避免 uvicorn reload 等场景下找不到 python-pptx
_exe = getattr(sys, "executable", None)
if _exe:
    _venv_base = Path(_exe).resolve().parent.parent
    _py = f"python{sys.version_info.major}.{sys.version_info.minor}"
    _site = _venv_base / "lib" / _py / "site-packages"
    if _site.is_dir() and str(_site) not in sys.path:
        sys.path.insert(0, str(_site))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.bot.claw_bot import ClawBot
from src.models.message import BotRequest, BotResponse, Conversation
from src.models.activity import ActivityEvent
from src.models.notification import (
    EmailRequest,
    TelegramRequest,
    TelegramPhotoRequest,
    WhatsAppRequest,
    WhatsAppTemplateRequest,
    NotificationResponse,
    GenerateTableRequest,
    GeneratePptRequest,
)
from src.utils.config import get_settings
from src.utils.logger import log
from src.utils.email_sender import EmailSender
from src.utils.telegram_sender import TelegramSender
from src.utils.whatsapp_sender import WhatsAppSender
from src.services import ReportService, ActivityService
from src.db import Base, engine, get_db
from typing import List, Optional

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="An intelligent AI bot framework",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database, bot and services
Base.metadata.create_all(bind=engine)

# Static files and daily activities page
import os
from pathlib import Path
# 从 api 文件位置向上查找包含 static/guide.html 的目录，兼容从项目根或父目录启动
_api_dir = Path(__file__).resolve().parent
_static_dir = None
_project_root = None
for _ in range(5):
    candidate = _api_dir / "static"
    if (candidate / "guide.html").is_file():
        _static_dir = str(candidate)
        _project_root = _api_dir
        break
    _api_dir = _api_dir.parent
if _static_dir is None:
    _static_dir = str(Path(__file__).resolve().parent.parent / "static")
    _project_root = Path(__file__).resolve().parent.parent
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/daily")
async def daily_activities_page():
    """Serve the daily commits frontend page."""
    from fastapi.responses import FileResponse
    html_path = os.path.join(_static_dir, "activities.html")
    if os.path.isfile(html_path):
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.get("/guide")
@app.get("/guide/")
async def repository_guide_page():
    """仓库文档与代码分析：直接重定向到静态文件，避免路径解析差异。"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/guide.html", status_code=302)


@app.get("/chat")
async def chat_page():
    """与龙虾对话的前端页面。"""
    from fastapi.responses import FileResponse
    html_path = os.path.join(_static_dir, "chat.html")
    if os.path.isfile(html_path):
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Chat page not found")


bot = ClawBot()
email_sender = EmailSender()
telegram_sender = TelegramSender()
whatsapp_sender = WhatsAppSender()
report_service = ReportService()
activity_service = ActivityService()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "links": {
            "chat": "/chat",
            "guide": "/guide",
            "daily": "/daily",
            "api_docs": "/docs",
            "generate_table": "/api/generate-table",
            "generate_ppt": "/api/generate-ppt",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/chat", response_model=BotResponse)
async def chat(request: BotRequest):
    """Chat with the bot."""
    log.info(f"Received chat request: {request.message[:50]}...")
    response = await bot.process_message(request)
    return response


@app.post("/api/generate-table")
async def api_generate_table(request: GenerateTableRequest):
    """
    根据描述生成表格，直接返回可下载的 CSV 或 Excel 文件。
    Body: {"prompt": "表格描述", "format": "csv" 或 "xlsx"}
    """
    from fastapi.responses import Response
    from src.services.content_generator import generate_table_data, table_to_csv, table_to_xlsx

    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="请提供表格描述 prompt")
    try:
        rows = await generate_table_data(request.prompt.strip())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if (request.format or "csv").lower() == "xlsx":
        content = table_to_xlsx(rows)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="table.xlsx"'},
        )
    content = table_to_csv(rows)
    return Response(
        content=content.encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="table.csv"'},
    )


@app.post("/api/generate-ppt")
async def api_generate_ppt(request: GeneratePptRequest):
    """
    根据标题和主题生成 PPT，直接返回可下载的 .pptx 文件。
    Body: {"title": "汇报标题", "topic": "内容方向"}
    """
    import re
    from fastapi.responses import Response
    from src.services.content_generator import generate_ppt_outline, build_pptx_bytes

    if not request.title or not request.title.strip():
        raise HTTPException(status_code=400, detail="请提供标题 title")
    topic = (request.topic or "").strip() or "总体概述"
    try:
        outline = await generate_ppt_outline(request.title.strip(), topic)
        content = build_pptx_bytes(request.title.strip(), outline)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    safe_name = re.sub(r'[^\w\s\u4e00-\u9fff-]', "", request.title.strip())[:30] or "presentation"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.pptx"'},
    )


@app.post("/reports/user/daily")
async def generate_user_daily_report(
    user_name: str,
    date: str,
    activities: List[ActivityEvent],
    language: str = "zh",
):
    """
    Generate a daily report for a user from a list of activity events.

    这是一个用于“预览效果”的接口：
    - 调用方把某个用户在一天内的活动列表（ActivityEvent 数组）传进来
    - 系统调用大模型生成一份结构化的工作日报文本
    - 后续可以把活动收集和调度自动化，这个接口仍然可复用
    """
    log.info(
        f"Report request for user={user_name}, date={date}, "
        f"activities={len(activities)}, language={language}"
    )

    # 解析日期字符串（简单处理：只取 YYYY-MM-DD）
    from datetime import datetime

    parsed_date = datetime.fromisoformat(date)

    report_text = await report_service.generate_user_daily_report(
        user_name=user_name,
        date=parsed_date,
        activities=activities,
        language=language,
    )

    return {
        "user_name": user_name,
        "date": parsed_date.date().isoformat(),
        "language": language,
        "activity_count": len(activities),
        "report": report_text,
    }


@app.get("/config/github-repos")
async def list_github_repos():
    """返回已配置的 GitHub 仓库列表（用于前端展示）。"""
    repos = settings.get_github_repos()
    return {"repos": [f"{o}/{r}" for o, r in repos]}


@app.get("/api/download/generated/{filename}")
async def download_generated(filename: str):
    """下载聊天中生成的表格、文档或 PPT 文件。"""
    import re
    from fastapi.responses import FileResponse
    from src.services.content_generator import _generated_dir

    if not re.match(r"^(table_[a-f0-9]+\.(csv|xlsx)|ppt_[a-f0-9]+\.pptx|doc_[a-f0-9]+\.md|word_[a-f0-9]+\.docx)$", filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    base = _generated_dir()
    path = base / filename
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="文件不存在或已过期，请重新在聊天里生成后再点下载。",
        )
    if filename.endswith(".csv"):
        media = "text/csv; charset=utf-8"
    elif filename.endswith(".xlsx"):
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filename.endswith(".md"):
        media = "text/markdown; charset=utf-8"
    elif filename.endswith(".docx"):
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        media = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    return FileResponse(path, filename=filename, media_type=media)


@app.get("/api/config/default-guide-repo")
async def get_default_guide_repo():
    """返回配置中的第一个仓库，供文档/代码分析页默认使用。"""
    repos = settings.get_github_repos()
    if not repos:
        return {"repo": None}
    o, r = repos[0]
    return {"repo": f"{o}/{r}"}


@app.get("/api/docs/code-analysis")
async def get_code_analysis(repo: Optional[str] = None):
    """分析仓库代码结构；可选 repo=owner/repo 指定 GitHub 仓库。"""
    from pathlib import Path
    from src.services.code_analyzer import analyze_codebase
    from src.services.repo_fetcher import ensure_repo_cloned, normalize_repo

    if repo:
        owner, name = normalize_repo(repo)
        if not owner or not name:
            raise HTTPException(status_code=400, detail="repo 格式应为 owner/repo")
        try:
            repo_root = ensure_repo_cloned(owner, name)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return analyze_codebase(repo_root, section_descriptions={})
    src_root = Path(__file__).resolve().parent.parent
    return analyze_codebase(src_root)


@app.get("/api/docs/project-guide")
async def get_project_guide(repo: Optional[str] = None):
    """返回项目说明文档（Markdown）；可选 repo=owner/repo 指定 GitHub 仓库。"""
    from pathlib import Path
    from src.services.repo_fetcher import ensure_repo_cloned, normalize_repo, read_guide_from_repo

    if repo:
        owner, name = normalize_repo(repo)
        if not owner or not name:
            raise HTTPException(status_code=400, detail="repo 格式应为 owner/repo")
        try:
            repo_root = ensure_repo_cloned(owner, name)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        content = read_guide_from_repo(repo_root)
        if content:
            return {"content": content}
        raise HTTPException(status_code=404, detail="该仓库未找到 PROJECT_GUIDE.md 或 README.md")
    guide_path = (_project_root / "PROJECT_GUIDE.md") if _project_root else Path(__file__).resolve().parent.parent / "PROJECT_GUIDE.md"
    if isinstance(guide_path, Path):
        guide_path = str(guide_path)
    if os.path.isfile(guide_path):
        with open(guide_path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    raise HTTPException(status_code=404, detail="Project guide not found")


@app.get("/activities")
async def list_activities(
    user_id: str,
    date: str,
    end_date: Optional[str] = None,
    db=Depends(get_db),
):
    """
    按用户和日期（或日期范围）查询原始活动列表。
    - date: 起始日期 YYYY-MM-DD
    - end_date: 可选，结束日期 YYYY-MM-DD，不传则只查 date 当天（日报）；传则查区间（周报）
    """
    from datetime import datetime, timezone, timedelta

    try:
        day_start = datetime.fromisoformat(date).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

    start = datetime(day_start.year, day_start.month, day_start.day, tzinfo=timezone.utc)
    if end_date:
        try:
            day_end = datetime.fromisoformat(end_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
        end = datetime(day_end.year, day_end.month, day_end.day, tzinfo=timezone.utc) + timedelta(days=1)
    else:
        end = start + timedelta(days=1)

    from src.models.activity import ActivityQuery

    query = ActivityQuery(user_id=user_id, start_time=start, end_time=end)
    activities = activity_service.query_activities(db, query)

    return {
        "user_id": user_id,
        "date": day_start.isoformat(),
        "end_date": end_date,
        "count": len(activities),
        "activities": [a.model_dump(mode="json") for a in activities],
    }


@app.post("/activities/github/sync")
async def sync_github_activities(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    hours: int = 24,
    db=Depends(get_db),
):
    """
    Sync recent GitHub activities (commits + PRs) into the database.

    - owner/repo 不填：同步配置中的所有仓库（GITHUB_REPOS 或 GITHUB_DEFAULT_OWNER/REPO）
    - owner/repo 指定：只同步该仓库
    - hours: 拉取最近多少小时的数据（默认 24）
    """
    from datetime import datetime, timezone, timedelta

    settings = get_settings()
    repos = settings.get_github_repos()

    if owner and repo:
        repos = [(owner, repo)]
    elif not repos:
        raise HTTPException(
            status_code=400,
            detail="GitHub 仓库未配置。请在 .env 中设置 GITHUB_REPOS 或 GITHUB_DEFAULT_OWNER/GITHUB_DEFAULT_REPO",
        )

    from src.providers.github_provider import GitHubProvider

    provider = GitHubProvider()
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    total_fetched = 0
    total_upserted = 0
    results = []

    for o, r in repos:
        try:
            events = await provider.fetch_repo_activities(owner=o, repo=r, since=since, until=now)
            upserted = activity_service.upsert_activities(db, events)
            total_fetched += len(events)
            total_upserted += upserted
            results.append({"owner": o, "repo": r, "fetched": len(events), "upserted": upserted})
        except Exception as e:
            results.append({"owner": o, "repo": r, "error": str(e)})

    return {
        "hours": hours,
        "repos": results,
        "total_fetched": total_fetched,
        "total_upserted": total_upserted,
    }


@app.get("/reports/user/daily/auto")
async def generate_user_daily_report_auto(
    user_id: str,
    date: str,
    language: str = "zh",
    db=Depends(get_db),
):
    """
    Generate a daily report for a user based on activities stored in DB.

    - user_id: 对应 ActivityEvent.user_id（你可以用邮箱、登录名等做约定）
    - date: YYYY-MM-DD
    """
    from datetime import datetime, timezone, timedelta

    try:
        day = datetime.fromisoformat(date).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    from src.models.activity import ActivityQuery

    query = ActivityQuery(
        user_id=user_id,
        start_time=start,
        end_time=end,
    )
    activities = activity_service.query_activities(db, query)

    if not activities:
        return {
            "user_id": user_id,
            "date": day.isoformat(),
            "language": language,
            "activity_count": 0,
            "report": "当天未找到任何活动记录。",
        }

    # 推断 user_name（取第一个事件的 user_name）
    user_name = activities[0].user_name or user_id

    report_text = await report_service.generate_user_daily_report(
        user_name=user_name,
        date=start,
        activities=activities,
        language=language,
    )

    return {
        "user_id": user_id,
        "user_name": user_name,
        "date": day.isoformat(),
        "language": language,
        "activity_count": len(activities),
        "report": report_text,
    }


@app.get("/conversations")
async def list_conversations() -> List[str]:
    """List all conversations."""
    return bot.list_conversations()


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> Conversation:
    """Get a specific conversation."""
    conversation = bot.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    success = bot.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "conversation_id": conversation_id}


@app.post("/send-email", response_model=NotificationResponse)
async def send_email(request: EmailRequest):
    """Send an email."""
    log.info(f"Email send request to: {request.to}")
    try:
        success = email_sender.send_email(
            to=request.to,
            subject=request.subject,
            body=request.body,
            html=request.html,
            cc=request.cc,
            bcc=request.bcc,
        )
        if success:
            return NotificationResponse(
                success=True, message="Email sent successfully"
            )
        else:
            return NotificationResponse(
                success=False,
                message="Failed to send email",
                error="Check logs for details",
            )
    except Exception as e:
        log.error(f"Email sending error: {e}")
        return NotificationResponse(success=False, message="Error", error=str(e))


@app.post("/send-telegram", response_model=NotificationResponse)
async def send_telegram(request: TelegramRequest):
    """Send a Telegram message."""
    log.info(f"Telegram message request: {request.text[:50]}...")
    try:
        success = telegram_sender.send_message(
            text=request.text,
            chat_id=request.chat_id,
            parse_mode=request.parse_mode,
            disable_notification=request.disable_notification,
        )
        if success:
            return NotificationResponse(
                success=True, message="Telegram message sent successfully"
            )
        else:
            return NotificationResponse(
                success=False,
                message="Failed to send Telegram message",
                error="Check logs for details",
            )
    except Exception as e:
        log.error(f"Telegram sending error: {e}")
        return NotificationResponse(success=False, message="Error", error=str(e))


@app.post("/send-telegram-photo", response_model=NotificationResponse)
async def send_telegram_photo(request: TelegramPhotoRequest):
    """Send a photo via Telegram."""
    log.info(f"Telegram photo request: {request.photo_url}")
    try:
        success = telegram_sender.send_photo(
            photo_url=request.photo_url,
            caption=request.caption,
            chat_id=request.chat_id,
        )
        if success:
            return NotificationResponse(
                success=True, message="Telegram photo sent successfully"
            )
        else:
            return NotificationResponse(
                success=False,
                message="Failed to send Telegram photo",
                error="Check logs for details",
            )
    except Exception as e:
        log.error(f"Telegram photo sending error: {e}")
        return NotificationResponse(success=False, message="Error", error=str(e))


@app.get("/telegram/updates")
async def get_telegram_updates():
    """Get Telegram bot updates (useful for getting chat_id)."""
    updates = telegram_sender.get_updates()
    return updates


@app.post("/send-whatsapp", response_model=NotificationResponse)
async def send_whatsapp(request: WhatsAppRequest):
    """Send a WhatsApp message."""
    log.info(f"WhatsApp message request to: {request.to}")
    try:
        success = whatsapp_sender.send_message(
            to=request.to,
            message=request.message,
            media_url=request.media_url,
            use_business_api=request.use_business_api,
        )
        if success:
            return NotificationResponse(
                success=True, message="WhatsApp message sent successfully"
            )
        else:
            return NotificationResponse(
                success=False,
                message="Failed to send WhatsApp message",
                error="Check logs for details",
            )
    except Exception as e:
        log.error(f"WhatsApp sending error: {e}")
        return NotificationResponse(success=False, message="Error", error=str(e))


@app.post("/send-whatsapp-template", response_model=NotificationResponse)
async def send_whatsapp_template(request: WhatsAppTemplateRequest):
    """Send a WhatsApp template message."""
    log.info(f"WhatsApp template request to: {request.to}")
    try:
        success = whatsapp_sender.send_template_message(
            to=request.to,
            template_name=request.template_name,
            language_code=request.language_code,
            parameters=request.parameters,
        )
        if success:
            return NotificationResponse(
                success=True, message="WhatsApp template sent successfully"
            )
        else:
            return NotificationResponse(
                success=False,
                message="Failed to send WhatsApp template",
                error="Check logs for details",
            )
    except Exception as e:
        log.error(f"WhatsApp template sending error: {e}")
        return NotificationResponse(success=False, message="Error", error=str(e))


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    log.info(f"{settings.app_name} v{settings.app_version} starting...")
    log.info(f"Using AI provider: {settings.default_ai_provider}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    log.info(f"{settings.app_name} shutting down...")
