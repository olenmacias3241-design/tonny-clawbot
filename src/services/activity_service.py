"""Service layer for persisting and querying activities."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from src.models.activity import ActivityEvent, ActivityQuery
from src.models.activity_orm import ActivityORM


class ActivityService:
    """Service for storing and querying ActivityEvent objects."""

    def upsert_activities(self, db: Session, events: List[ActivityEvent]) -> int:
        """Insert or update a batch of activities. Returns number of upserted rows."""
        count = 0
        for event in events:
            existing = db.get(ActivityORM, event.id)
            if existing:
                # Minimal update for now
                existing.source = event.source
                existing.type = event.type
                existing.user_id = event.user_id
                existing.user_name = event.user_name
                existing.project_id = event.project_id
                existing.project_name = event.project_name
                existing.title = event.title
                existing.description = event.description
                existing.timestamp = event.timestamp
                existing.url = event.url
                existing.extra = event.metadata
            else:
                db.add(
                    ActivityORM(
                        id=event.id,
                        source=event.source,
                        type=event.type,
                        user_id=event.user_id,
                        user_name=event.user_name,
                        project_id=event.project_id,
                        project_name=event.project_name,
                        title=event.title,
                        description=event.description,
                        timestamp=event.timestamp,
                        url=event.url,
                        extra=event.metadata,
                    )
                )
            count += 1
        db.commit()
        return count

    def query_activities(self, db: Session, query: ActivityQuery) -> List[ActivityEvent]:
        """Query activities by user/project/time window/types."""
        stmt = select(ActivityORM)
        conditions = []

        if query.user_id:
            conditions.append(ActivityORM.user_id == query.user_id)
        if query.project_id:
            conditions.append(ActivityORM.project_id == query.project_id)
        if query.start_time:
            conditions.append(ActivityORM.timestamp >= query.start_time)
        if query.end_time:
            conditions.append(ActivityORM.timestamp <= query.end_time)
        if query.types:
            conditions.append(ActivityORM.type.in_(query.types))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(ActivityORM.timestamp.asc())

        results = db.execute(stmt).scalars().all()

        return [
            ActivityEvent(
                id=r.id,
                source=r.source,
                type=r.type,
                user_id=r.user_id,
                user_name=r.user_name,
                project_id=r.project_id,
                project_name=r.project_name,
                title=r.title,
                description=r.description,
                timestamp=r.timestamp,
                url=r.url,
                metadata=r.extra,
            )
            for r in results
        ]

