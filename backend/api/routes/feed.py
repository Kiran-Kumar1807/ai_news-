"""Personalized feed route."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user
from backend.database.session import get_db
from backend.models import User
from backend.schemas.article import ArticleSummary
from backend.services.feed_service import get_personalized_feed

router = APIRouter(tags=["feed"])


@router.get("/feed", response_model=list[ArticleSummary])
def read_feed(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ArticleSummary]:
    """Return the authenticated user's personalized news feed."""
    articles = get_personalized_feed(db, current_user.id, limit=limit, offset=offset)
    return [ArticleSummary.model_validate(a) for a in articles]
