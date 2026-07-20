"""Article-related Pydantic schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleSummary(BaseModel):
    """Lightweight article representation for feed listings."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source: str
    article_url: str
    summary: str | None = None
    category: str
    published_at: datetime | None = None
    created_at: datetime


class ArticleDetail(ArticleSummary):
    """Full article representation, including raw content."""

    content: str
    article_hash: str


class ArticleCreate(BaseModel):
    """Internal schema used by the ingestion pipeline."""

    title: str
    source: str
    article_url: str
    content: str = ""
    summary: str | None = None
    category: str
    article_hash: str
    published_at: datetime | None = None
