"""Personalized feed generation."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models import Article
from backend.services.article_service import list_articles
from backend.services.user_service import get_user_interests


def get_personalized_feed(
    db: Session, user_id: int, limit: int = 50, offset: int = 0
) -> list[Article]:
    """Return articles matching the user's interests, newest first.

    If the user has selected no interests, the global latest feed is returned so
    that the experience is never empty.
    """
    interests = get_user_interests(db, user_id)
    categories = interests or None
    return list_articles(db, categories=categories, limit=limit, offset=offset)
