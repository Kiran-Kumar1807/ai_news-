"""User preference (many-to-many between users and niches)."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class UserPreference(Base):
    """Association row linking a user to a subscribed niche."""

    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", "niche_id", name="uq_user_niche"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    niche_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("niches.id", ondelete="CASCADE"), index=True, nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="preferences")
    niche: Mapped[Niche] = relationship("Niche", back_populates="preferences")


from backend.models.niche import Niche  # noqa: E402
from backend.models.user import User  # noqa: E402
