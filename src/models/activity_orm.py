"""SQLAlchemy ORM models for activities."""

from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, JSON

from src.db import Base


class ActivityORM(Base):
    """ORM model for normalized activity events."""

    __tablename__ = "activities"

    id = Column(String, primary_key=True, index=True)
    source = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    user_name = Column(String, nullable=True)
    project_id = Column(String, nullable=True, index=True)
    project_name = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    url = Column(String, nullable=True)
    # attribute name cannot be "metadata" with SQLAlchemy declarative
    extra = Column("metadata", JSON, nullable=True)

