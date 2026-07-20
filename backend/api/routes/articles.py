"""Article detail and analytics routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.article import ArticleDetail
from backend.services.article_service import (
    count_articles,
    count_by_category,
    count_by_day,
    get_article,
)

router = APIRouter(tags=["articles"])


@router.get("/articles/analytics")
def articles_analytics(db: Session = Depends(get_db)) -> dict:
    """Return aggregate analytics used by the dashboard."""
    return {
        "total_articles": count_articles(db),
        "by_category": count_by_category(db),
        "by_day": count_by_day(db),
    }


@router.get("/articles/{article_id}", response_model=ArticleDetail)
def read_article(article_id: int, db: Session = Depends(get_db)) -> ArticleDetail:
    """Return the full detail of a single article."""
    article = get_article(db, article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Article not found."
        )
    return ArticleDetail.model_validate(article)
