"""Article persistence logic used by the API and ingestion pipeline."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models import Article
from backend.schemas.article import ArticleCreate


def article_exists(db: Session, article_hash: str) -> bool:
    return db.scalar(select(Article.id).where(Article.article_hash == article_hash)) is not None


def get_article(db: Session, article_id: int) -> Article | None:
    return db.get(Article, article_id)


def create_article(db: Session, data: ArticleCreate) -> Article | None:
    """Insert a new article; returns ``None`` if a duplicate hash exists."""
    if article_exists(db, data.article_hash):
        return None
    article = Article(**data.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def list_articles(
    db: Session,
    categories: list[str] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Article]:
    """Return articles, optionally filtered by category, newest first."""
    stmt = select(Article)
    if categories:
        stmt = stmt.where(Article.category.in_(categories))
    stmt = (
        stmt.order_by(
            Article.published_at.desc().nullslast(),
            Article.created_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def count_articles(db: Session) -> int:
    return db.scalar(select(func.count(Article.id))) or 0


def count_by_category(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(Article.category, func.count(Article.id)).group_by(Article.category)
    ).all()
    return {category: count for category, count in rows}


def count_by_day(db: Session, days: int = 14) -> dict[str, int]:
    """Return ingestion counts grouped by day (ISO date string)."""
    rows = db.execute(
        select(func.date(Article.created_at), func.count(Article.id)).group_by(
            func.date(Article.created_at)
        )
    ).all()
    result = {str(day): count for day, count in rows if day is not None}
    return dict(sorted(result.items())[-days:])
