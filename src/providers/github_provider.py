"""GitHub provider to fetch activities and normalize to ActivityEvent."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx

from src.models.activity import ActivityEvent
from src.utils.config import get_settings
from src.utils.logger import log


class GitHubProvider:
    """Fetch commits and PRs from GitHub as ActivityEvent objects."""

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        settings = get_settings()
        self.token = token or getattr(settings, "github_token", None)
        self.base_url = base_url
        if not self.token:
            log.warning("GitHub token not configured; GitHub sync will likely fail.")

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def fetch_repo_activities(
        self,
        owner: str,
        repo: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[ActivityEvent]:
        """Fetch commits and PRs from a single repository."""
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(days=1)
        if until is None:
            until = datetime.now(timezone.utc)

        async with httpx.AsyncClient(base_url=self.base_url, headers=self._headers(), timeout=30) as client:
            # Commits
            params_commits = {
                "since": since.isoformat(),
                "until": until.isoformat(),
            }
            commits_url = f"/repos/{owner}/{repo}/commits"
            log.info(f"Fetching GitHub commits: {owner}/{repo} {params_commits}")
            commits_resp = await client.get(commits_url, params=params_commits)
            commits_resp.raise_for_status()
            commits = commits_resp.json()

            # Pull requests (updated within window)
            params_prs = {
                "state": "all",
                "sort": "updated",
                "direction": "desc",
                "per_page": 50,
            }
            prs_url = f"/repos/{owner}/{repo}/pulls"
            log.info(f"Fetching GitHub PRs: {owner}/{repo} {params_prs}")
            prs_resp = await client.get(prs_url, params=params_prs)
            prs_resp.raise_for_status()
            prs = prs_resp.json()

        events: List[ActivityEvent] = []

        # Normalize commits
        for c in commits:
            commit = c.get("commit", {})
            author = commit.get("author", {})
            ts_str = author.get("date")
            if not ts_str:
                continue
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts < since or ts > until:
                continue

            events.append(
                ActivityEvent(
                    id=f"github-commit-{c.get('sha')}",
                    source="github",
                    type="commit",
                    user_id=str(author.get("email") or author.get("name") or ""),
                    user_name=author.get("name"),
                    project_id=f"{owner}/{repo}",
                    project_name=f"{owner}/{repo}",
                    title=commit.get("message", "").split("\n")[0][:200],
                    description=commit.get("message"),
                    timestamp=ts,
                    url=c.get("html_url"),
                    metadata={
                        "sha": c.get("sha"),
                        "verification": commit.get("verification"),
                    },
                )
            )

        # Normalize PRs
        for pr in prs:
            updated_at_str = pr.get("updated_at")
            if not updated_at_str:
                continue
            updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            if updated_at < since or updated_at > until:
                continue

            user = pr.get("user") or {}
            merged = pr.get("merged_at") is not None
            state = pr.get("state")

            event_type = "pr_opened"
            if merged:
                event_type = "pr_merged"
            elif state == "closed":
                event_type = "pr_closed"

            events.append(
                ActivityEvent(
                    id=f"github-pr-{pr.get('id')}",
                    source="github",
                    type=event_type,
                    user_id=str(user.get("id") or ""),
                    user_name=user.get("login"),
                    project_id=f"{owner}/{repo}",
                    project_name=f"{owner}/{repo}",
                    title=pr.get("title"),
                    description=pr.get("body"),
                    timestamp=updated_at,
                    url=pr.get("html_url"),
                    metadata={
                        "state": state,
                        "merged": merged,
                        "number": pr.get("number"),
                    },
                )
            )

        return events

