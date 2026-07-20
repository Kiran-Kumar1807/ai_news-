"""User-related Pydantic schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    """User representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None = None
    created_at: datetime


class UserProfile(UserPublic):
    """User profile including selected interests."""

    interests: list[str] = []
