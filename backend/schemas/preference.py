"""Preference-related Pydantic schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PreferenceUpdate(BaseModel):
    """Payload for replacing a user's selected interests."""

    interests: list[str] = Field(
        default_factory=list,
        description="List of category names the user is interested in.",
    )


class PreferenceResponse(BaseModel):
    interests: list[str]
