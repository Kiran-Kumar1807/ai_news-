"""Pytest fixtures and test configuration.

Configures an isolated SQLite database and disables the scheduler *before* any
backend module (which builds the engine at import time) is imported.
"""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("ENABLE_SCHEDULER", "false")
# Force-disable all LLM providers so tests exercise the deterministic heuristic
# fallbacks and never call a live API, even when real keys are present in the env.
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

# Build a single shared in-memory engine and patch it into the app modules so
# every session sees the same schema and data.
_test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

import backend.database.base as db_base  # noqa: E402

db_base.engine = _test_engine
db_base.SessionLocal = _TestSessionLocal

import backend.database.session as db_session  # noqa: E402

db_session.SessionLocal = _TestSessionLocal

from backend.database.base import Base  # noqa: E402
import backend.models  # noqa: E402,F401
from backend.services.user_service import ensure_niches  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_database():
    """Recreate all tables and seed niches before every test."""
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    session = _TestSessionLocal()
    try:
        ensure_niches(session)
    finally:
        session.close()
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def db():
    """Provide a database session bound to the test engine."""
    session = _TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """Provide a FastAPI TestClient with the scheduler disabled."""
    from fastapi.testclient import TestClient

    from backend.main import app

    with TestClient(app) as test_client:
        yield test_client
