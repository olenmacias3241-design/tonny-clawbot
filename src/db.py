"""Database setup for Claw Bot AI."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.utils.config import get_settings


settings = get_settings()

engine = create_engine(settings.database_url, future=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    """FastAPI-style dependency for DB sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

