"""Tests for the daily digest, email client and scheduler wiring."""
from __future__ import annotations

from backend.models import User
from backend.schemas.article import ArticleCreate
from backend.services.article_service import create_article
from backend.services.user_service import create_user, set_user_interests
from ingestion.article_extractor import compute_hash
from scheduler import daily_digest, email_client, scheduler


def _seed_article(db, title, category):
    url = f"https://example.com/{title}"
    create_article(
        db,
        ArticleCreate(
            title=title,
            source="Test",
            article_url=url,
            content="content",
            summary="- point one\n- point two\n- point three",
            category=category,
            article_hash=compute_hash(title, url),
        ),
    )


def test_email_client_disabled_returns_false():
    # No SMTP credentials configured in the test environment.
    assert email_client.send_email("to@example.com", "Subj", "<p>hi</p>") is False


def test_build_digest_html_and_text():
    user = User(email="digest@example.com", full_name="Digest User", password_hash="x")

    class _Article:
        title = "Headline"
        summary = "- a\n- b"
        article_url = "https://example.com/x"

    grouped = {"Artificial Intelligence": [_Article()]}
    html = daily_digest.build_digest_html(user, grouped)
    assert "Good Morning Digest User" in html
    assert "Read More" in html
    text = daily_digest.build_digest_text(user, grouped)
    assert "Category: Artificial Intelligence" in text


def test_send_daily_digests_counts(db, monkeypatch):
    user = create_user(db, "d@example.com", "password123", "D")
    set_user_interests(db, user.id, ["Finance"])
    _seed_article(db, "Finance news", "Finance")

    sent: list[str] = []

    def _fake_send(to, subject, html, text=""):
        sent.append(to)
        return True

    monkeypatch.setattr(daily_digest, "send_email", _fake_send)
    count = daily_digest.send_daily_digests()
    assert count == 1
    assert sent == ["d@example.com"]


def test_scheduler_has_jobs():
    sched = scheduler.create_scheduler()
    job_ids = {job.id for job in sched.get_jobs()}
    assert {"hourly_ingestion", "daily_digest"} <= job_ids


def test_start_and_shutdown_scheduler():
    from backend.scheduler_state import scheduler_status

    sched = scheduler.start_scheduler()
    assert scheduler_status() is True
    scheduler.shutdown_scheduler(sched)
    assert scheduler_status() is False
