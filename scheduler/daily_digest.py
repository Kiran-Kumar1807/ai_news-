"""Daily email digest generation and delivery."""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.session import session_scope
from backend.logging_config import get_logger
from backend.models import Article, User
from backend.services.article_service import list_articles
from backend.services.user_service import get_user_interests
from scheduler.email_client import send_email

logger = get_logger("email")

MAX_ARTICLES_PER_CATEGORY = 3


def _greeting_name(user: User) -> str:
    return user.full_name or user.email.split("@")[0]


def build_digest_html(user: User, articles_by_category: dict[str, list[Article]]) -> str:
    """Render the HTML body for a user's daily digest."""
    parts = [
        f"<h2>Good Morning {_greeting_name(user)}</h2>",
        "<h3>Today's News Digest</h3>",
    ]
    for category, articles in articles_by_category.items():
        parts.append(f"<h4>Category: {category}</h4>")
        for article in articles:
            summary = (article.summary or "").replace("\n", "<br>")
            parts.append(
                f"<p><strong>{article.title}</strong><br>{summary}<br>"
                f'<a href="{article.article_url}">Read More</a></p>'
            )
    return "\n".join(parts)


def build_digest_text(user: User, articles_by_category: dict[str, list[Article]]) -> str:
    """Render a plain-text fallback body for a user's daily digest."""
    lines = [f"Good Morning {_greeting_name(user)}", "", "Today's News Digest", ""]
    for category, articles in articles_by_category.items():
        lines.append(f"Category: {category}")
        for article in articles:
            lines.append(article.title)
            for bullet in (article.summary or "").split("\n"):
                lines.append(bullet)
            lines.append(f"Read More: {article.article_url}")
            lines.append("")
    return "\n".join(lines)


def _collect_for_user(db: Session, user: User) -> dict[str, list[Article]]:
    interests = get_user_interests(db, user.id) or None
    articles = list_articles(db, categories=interests, limit=30)
    grouped: dict[str, list[Article]] = defaultdict(list)
    for article in articles:
        if len(grouped[article.category]) < MAX_ARTICLES_PER_CATEGORY:
            grouped[article.category].append(article)
    return dict(grouped)


def send_daily_digests() -> int:
    """Build and send the daily digest to every user. Returns emails sent."""
    sent = 0
    with session_scope() as db:
        users = list(db.scalars(select(User)).all())
        for user in users:
            grouped = _collect_for_user(db, user)
            if not grouped:
                continue
            html = build_digest_html(user, grouped)
            text = build_digest_text(user, grouped)
            if send_email(user.email, "Your Daily News Digest", html, text):
                sent += 1
    logger.info("Daily digests processed", extra={"ctx_sent": sent})
    return sent


if __name__ == "__main__":  # pragma: no cover
    from backend.logging_config import configure_logging

    configure_logging()
    send_daily_digests()
