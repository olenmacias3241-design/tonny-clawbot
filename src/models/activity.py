"""Activity models for project and user work tracking."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class ActivityEvent(BaseModel):
    """Normalized activity event from any external system."""

    id: str = Field(..., description="Unique activity ID (source+id)")
    source: str = Field(..., description="Source system, e.g. github, gitlab, jira")
    type: str = Field(
        ...,
        description=(
            "Event type, e.g. commit, pr_opened, pr_merged, issue_updated, task_moved"
        ),
    )
    user_id: Optional[str] = Field(
        default=None, description="Internal user identifier (if mapped)"
    )
    user_name: Optional[str] = Field(
        default=None, description="Display name from source system"
    )
    project_id: Optional[str] = Field(
        default=None, description="Internal project identifier (if mapped)"
    )
    project_name: Optional[str] = Field(
        default=None, description="Project/repository name from source system"
    )
    title: Optional[str] = Field(
        default=None, description="Short title for the activity"
    )
    description: Optional[str] = Field(
        default=None, description="Human-readable description or summary"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the activity happened"
    )
    url: Optional[str] = Field(
        default=None, description="URL to view this activity in the source system"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Raw metadata payload from the source system"
    )


class ActivityQuery(BaseModel):
    """Query parameters for fetching activities."""

    user_id: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None  # e.g. "owner/repo" 按仓库筛选
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    types: Optional[List[str]] = None

