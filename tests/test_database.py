"""Tests for database operations: dedup, hashing, analytics."""
from __future__ import annotations

from backend.schemas.article import ArticleCreate
from backend.services.article_service import (
    count_articles,
    count_by_category,
    create_article,
)
from backend.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_interests,
    set_user_interests,
)
from ingestion.article_extractor import compute_hash


def _article(title, category="Technology"):
    url = f"https://example.com/{title}"
    return ArticleCreate(
        title=title,
        source="Test",
        article_url=url,
        content="content",
        summary="- s",
        category=category,
        article_hash=compute_hash(title, url),
    )


def test_hash_is_stable_and_unique():
    a = compute_hash("Title", "https://x.com/a")
    b = compute_hash("Title", "https://x.com/a")
    c = compute_hash("Other", "https://x.com/b")
    assert a == b
    assert a != c


def test_duplicate_articles_are_rejected(db):
    first = create_article(db, _article("Same"))
    assert first is not None
    duplicate = create_article(db, _article("Same"))
    assert duplicate is None
    assert count_articles(db) == 1


def test_count_by_category(db):
    create_article(db, _article("A", "Finance"))
    create_article(db, _article("B", "Finance"))
    create_article(db, _article("C", "Sports"))
    counts = count_by_category(db)
    assert counts["Finance"] == 2
    assert counts["Sports"] == 1


def test_user_persistence_and_interests(db):
    user = create_user(db, "DB@Example.com", "password123", "DB User")
    # Email is normalized to lowercase.
    assert get_user_by_email(db, "db@example.com") is not None

    set_user_interests(db, user.id, ["Finance", "Sports", "NotACategory"])
    interests = get_user_interests(db, user.id)
    assert set(interests) == {"Finance", "Sports"}

    # Replacing interests overwrites the previous selection.
    set_user_interests(db, user.id, ["Politics"])
    assert get_user_interests(db, user.id) == ["Politics"]
