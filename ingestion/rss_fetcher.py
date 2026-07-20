"""Fetch and parse RSS feeds into extracted articles."""
from __future__ import annotations

import feedparser

from backend.config import settings
from backend.logging_config import get_logger
from ingestion.article_extractor import ExtractedArticle, extract
from ingestion.feeds import RSS_FEEDS, FeedSource

logger = get_logger("ingestion")


def fetch_feed(source: FeedSource, limit: int | None = None) -> list[ExtractedArticle]:
    """Fetch a single feed and return the extracted articles."""
    limit = limit or settings.max_articles_per_feed
    logger.info("Fetching feed", extra={"ctx_source": source.name, "ctx_url": source.url})
    parsed = feedparser.parse(source.url)
    if getattr(parsed, "bozo", 0) and not parsed.entries:
        logger.warning(
            "Feed failed to parse",
            extra={"ctx_source": source.name, "ctx_error": str(getattr(parsed, "bozo_exception", ""))},
        )
        return []

    articles: list[ExtractedArticle] = []
    for entry in parsed.entries[:limit]:
        article = extract(entry, source.name)
        if article is not None:
            articles.append(article)
    logger.info(
        "Fetched feed entries",
        extra={"ctx_source": source.name, "ctx_count": len(articles)},
    )
    return articles


def fetch_all(feeds: list[FeedSource] | None = None) -> list[ExtractedArticle]:
    """Fetch all configured feeds, deduplicating by article hash."""
    feeds = feeds or RSS_FEEDS
    seen: set[str] = set()
    results: list[ExtractedArticle] = []
    for source in feeds:
        try:
            for article in fetch_feed(source):
                if article.article_hash not in seen:
                    seen.add(article.article_hash)
                    results.append(article)
        except Exception as exc:  # pragma: no cover - network errors
            logger.error(
                "Error fetching feed",
                extra={"ctx_source": source.name, "ctx_error": str(exc)},
            )
    return results
