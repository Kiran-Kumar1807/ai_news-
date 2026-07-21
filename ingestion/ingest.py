"""End-to-end ingestion pipeline: fetch -> dedupe -> classify -> summarize -> store."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.database.session import session_scope
from backend.logging_config import get_logger
from backend.schemas.article import ArticleCreate
from backend.services.article_service import article_exists, create_article
from ingestion import classifier, summarizer
from ingestion.article_extractor import ExtractedArticle
from ingestion.rss_fetcher import fetch_all

logger = get_logger("ingestion")


@dataclass
class IngestResult:
    fetched: int
    stored: int
    duplicates: int


def _process_one(db: Session, article: ExtractedArticle) -> bool:
    """Classify, summarize and store a single article. Returns True if stored."""
    if article_exists(db, article.article_hash):
        return False

    category = classifier.classify(article.title, article.content)
    bulletin, summary = summarizer.summarize_article(article.title, article.content)

    payload = ArticleCreate(
        title=article.title,
        source=article.source,
        article_url=article.article_url,
        content=article.content,
        bulletin=bulletin,
        summary=summary,
        category=category,
        article_hash=article.article_hash,
        published_at=article.published_at,
    )
    return create_article(db, payload) is not None


def run_ingestion() -> IngestResult:
    """Run the full ingestion pipeline once and return counts."""
    articles = fetch_all()
    stored = 0
    duplicates = 0

    with session_scope() as db:
        for article in articles:
            try:
                if _process_one(db, article):
                    stored += 1
                else:
                    duplicates += 1
            except Exception as exc:  # pragma: no cover - defensive
                db.rollback()
                logger.error(
                    "Failed to process article",
                    extra={"ctx_url": article.article_url, "ctx_error": str(exc)},
                )

    result = IngestResult(fetched=len(articles), stored=stored, duplicates=duplicates)
    logger.info(
        "Ingestion complete",
        extra={
            "ctx_fetched": result.fetched,
            "ctx_stored": result.stored,
            "ctx_duplicates": result.duplicates,
        },
    )
    return result


if __name__ == "__main__":  # pragma: no cover
    from backend.logging_config import configure_logging

    configure_logging()
    run_ingestion()
