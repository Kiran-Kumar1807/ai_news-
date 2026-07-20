"""Tests for configuration helpers (DB URL normalization, CORS parsing)."""
from backend.config import Settings


def test_postgres_scheme_is_normalized():
    s = Settings(database_url="postgres://user:pass@host:5432/db")
    assert s.sqlalchemy_database_url == "postgresql+psycopg2://user:pass@host:5432/db"


def test_driverless_postgresql_scheme_is_normalized():
    s = Settings(database_url="postgresql://user:pass@host/db")
    assert s.sqlalchemy_database_url == "postgresql+psycopg2://user:pass@host/db"


def test_explicit_driver_and_sqlite_are_left_untouched():
    s = Settings(database_url="postgresql+psycopg2://user:pass@host/db")
    assert s.sqlalchemy_database_url == "postgresql+psycopg2://user:pass@host/db"
    s2 = Settings(database_url="sqlite+pysqlite:///./x.db")
    assert s2.sqlalchemy_database_url == "sqlite+pysqlite:///./x.db"


def test_cors_origins_parsing():
    assert Settings(cors_origins="*").cors_allow_origins == ["*"]
    assert Settings(cors_origins="").cors_allow_origins == ["*"]
    assert Settings(
        cors_origins="https://a.com, https://b.com"
    ).cors_allow_origins == ["https://a.com", "https://b.com"]
