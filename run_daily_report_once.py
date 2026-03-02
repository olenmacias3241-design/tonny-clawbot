"""One-off script: sync GitHub activities for last 24h and generate a daily report for one user.

Usage (example):
    poetry run python run_daily_report_once.py --user-id you@example.com --date 2026-02-26
Make sure environment variables are set:
    - OPENAI_API_KEY or ANTHROPIC_API_KEY (depending on your default_ai_provider)
    - GITHUB_TOKEN
    - GITHUB_DEFAULT_OWNER
    - GITHUB_DEFAULT_REPO
"""

import argparse
import asyncio
from datetime import datetime, timezone, timedelta

from src.utils.config import get_settings
from src.db import Base, engine, SessionLocal
from src.providers.github_provider import GitHubProvider
from src.services import ActivityService, ReportService
from src.models.activity import ActivityQuery


async def main(user_id: str, date_str: str, hours: int = 24) -> None:
    settings = get_settings()

    # Ensure DB tables exist
    Base.metadata.create_all(bind=engine)

    # Parse date
    day = datetime.fromisoformat(date_str).date()
    start_of_day = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    end_of_day = start_of_day + timedelta(days=1)

    # Sync GitHub activities for last `hours` hours (all configured repos)
    repos = settings.get_github_repos()
    if not repos:
        raise RuntimeError("请在 .env 中配置 GITHUB_REPOS 或 GITHUB_DEFAULT_OWNER/GITHUB_DEFAULT_REPO")

    provider = GitHubProvider()
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)
    all_events = []
    for owner, repo in repos:
        events = await provider.fetch_repo_activities(owner=owner, repo=repo, since=since, until=now)
        all_events.extend(events)
        print(f"  {owner}/{repo}: {len(events)} events")

    db = SessionLocal()
    activity_service = ActivityService()
    upserted = activity_service.upsert_activities(db, all_events)
    print(f"Synced {len(all_events)} events from {len(repos)} repo(s), upserted {upserted} into DB.")

    # Query activities for the given user and day
    query = ActivityQuery(
        user_id=user_id,
        start_time=start_of_day,
        end_time=end_of_day,
    )
    activities = activity_service.query_activities(db, query)
    print(f"Found {len(activities)} activities for user {user_id} on {day}.")

    # Generate report
    report_service = ReportService()
    user_name = activities[0].user_name if activities else user_id
    report_text = await report_service.generate_user_daily_report(
        user_name=user_name,
        date=start_of_day,
        activities=activities,
        language="zh",
    )

    print("\n===== AI 生成的日报 =====\n")
    print(report_text)
    print("\n===== 结束 =====\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run one-off daily report generation.")
    parser.add_argument("--user-id", required=True, help="User ID to generate report for (matches ActivityEvent.user_id)")
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    parser.add_argument("--hours", type=int, default=24, help="How many recent hours to sync from GitHub")
    args = parser.parse_args()

    asyncio.run(main(user_id=args.user_id, date_str=args.date, hours=args.hours))

