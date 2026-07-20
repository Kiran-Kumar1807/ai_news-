"""Tests for personalized feed generation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend.schemas.article import ArticleCreate
from backend.services.article_service import create_article
from backend.services.feed_service import get_personalized_feed
from backend.services.user_service import create_user, set_user_interests
from ingestion.article_extractor import compute_hash


def _make_article(db, title, category, minutes_ago=0):
    published = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return create_article(
        db,
        ArticleCreate(
            title=title,
            source="Test",
            article_url=f"https://example.com/{title}",
            content="content",
            summary="- point",
            category=category,
            article_hash=compute_hash(title, f"https://example.com/{title}"),
            published_at=published,
        ),
    )


def test_feed_filters_by_interests(db):
    user = create_user(db, "feed@example.com", "password123", "Feed User")
    _make_article(db, "AI story", "Artificial Intelligence", minutes_ago=10)
    _make_article(db, "Sports story", "Sports", minutes_ago=5)
    _make_article(db, "Finance story", "Finance", minutes_ago=1)

    set_user_interests(db, user.id, ["Artificial Intelligence", "Finance"])
    feed = get_personalized_feed(db, user.id)

    categories = {a.category for a in feed}
    assert categories == {"Artificial Intelligence", "Finance"}


def test_feed_sorted_by_latest(db):
    user = create_user(db, "sort@example.com", "password123", None)
    _make_article(db, "older", "Technology", minutes_ago=60)
    _make_article(db, "newer", "Technology", minutes_ago=1)
    set_user_interests(db, user.id, ["Technology"])

    feed = get_personalized_feed(db, user.id)
    assert feed[0].title == "newer"


def test_feed_without_interests_returns_latest(db):
    user = create_user(db, "empty@example.com", "password123", None)
    _make_article(db, "any", "Business", minutes_ago=1)
    feed = get_personalized_feed(db, user.id)
    assert len(feed) == 1
