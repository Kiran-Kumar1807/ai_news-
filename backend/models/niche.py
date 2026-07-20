"""Niche (interest category) ORM model."""
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Niche(Base):
    """An interest category a user can subscribe to (mirrors news categories)."""

    __tablename__ = "niches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    niche_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    preferences: Mapped[list[UserPreference]] = relationship(
        "UserPreference", back_populates="niche", cascade="all, delete-orphan"
    )


from backend.models.preference import UserPreference  # noqa: E402
