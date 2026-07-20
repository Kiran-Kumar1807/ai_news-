"""User ORM model."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """A registered application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    preferences: Mapped[list[UserPreference]] = relationship(
        "UserPreference", back_populates="user", cascade="all, delete-orphan"
    )


from backend.models.preference import UserPreference  # noqa: E402  (avoid circular import)
