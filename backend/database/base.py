"""Database engine, session factory and declarative base."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


def _engine_kwargs(url: str) -> dict:
    # SQLite (used in tests) needs a special connect arg for threaded access.
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


_db_url = settings.sqlalchemy_database_url
engine = create_engine(_db_url, **_engine_kwargs(_db_url))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
