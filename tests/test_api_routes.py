"""Tests for health, categories, feed and article API routes."""
from __future__ import annotations

from backend.core.categories import CATEGORIES
from backend.database.session import session_scope
from backend.schemas.article import ArticleCreate
from backend.services.article_service import create_article
from ingestion.article_extractor import compute_hash


def _auth_headers(client, email="user@example.com"):
    client.post("/register", json={"email": email, "password": "password123"})
    token = client.post(
        "/login", json={"email": email, "password": "password123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("ok", "degraded")
    names = {c["name"] for c in body["components"]}
    assert {"database", "gemini", "scheduler"} <= names


def test_categories_endpoint(client):
    resp = client.get("/categories")
    assert resp.status_code == 200
    assert resp.json()["categories"] == CATEGORIES


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "docs" in resp.json()


def _seed(title="Story", category="Technology"):
    url = f"https://example.com/{title}"
    with session_scope() as db:
        create_article(
            db,
            ArticleCreate(
                title=title,
                source="Test",
                article_url=url,
                content="full content body",
                summary="- point",
                category=category,
                article_hash=compute_hash(title, url),
            ),
        )


def test_article_detail_and_404(client):
    _seed("Detail", "Finance")
    listing = client.get("/articles/analytics").json()
    assert listing["total_articles"] == 1

    # Fetch the article via the feed to obtain its id.
    headers = _auth_headers(client)
    client.post("/preferences", json={"interests": ["Finance"]}, headers=headers)
    feed = client.get("/feed", headers=headers).json()
    assert len(feed) == 1
    article_id = feed[0]["id"]

    detail = client.get(f"/articles/{article_id}")
    assert detail.status_code == 200
    assert detail.json()["content"] == "full content body"

    assert client.get("/articles/999999").status_code == 404


def test_preferences_and_feed_flow(client):
    _seed("AI item", "Artificial Intelligence")
    _seed("Sports item", "Sports")
    headers = _auth_headers(client, "flow@example.com")

    resp = client.post(
        "/preferences",
        json={"interests": ["Artificial Intelligence"]},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["interests"] == ["Artificial Intelligence"]

    feed = client.get("/feed", headers=headers).json()
    assert {a["category"] for a in feed} == {"Artificial Intelligence"}
