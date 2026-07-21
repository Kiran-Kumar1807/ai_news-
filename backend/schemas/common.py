"""Miscellaneous shared schemas."""
from __future__ import annotations

from pydantic import BaseModel


class Message(BaseModel):
    message: str


class HealthComponent(BaseModel):
    name: str
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    components: list[HealthComponent]


class CategoriesResponse(BaseModel):
    categories: list[str]


class IngestResultResponse(BaseModel):
    fetched: int
    stored: int
    duplicates: int
