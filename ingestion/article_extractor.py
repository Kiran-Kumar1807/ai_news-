"""Extraction and normalization of article fields from RSS entries."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from time import mktime

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


@dataclass
class ExtractedArticle:
    title: str
    source: str
    article_url: str
    content: str
    published_at: datetime | None
    article_hash: str


def clean_html(text: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    if not text:
        return ""
    no_tags = _HTML_TAG_RE.sub(" ", text)
    return _WS_RE.sub(" ", no_tags).strip()


def compute_hash(title: str, url: str) -> str:
    """Return a stable SHA-256 hash identifying an article for deduplication."""
    basis = f"{(title or '').strip().lower()}|{(url or '').strip().lower()}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def _parse_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        value = getattr(entry, attr, None)
        if value:
            try:
                return datetime.fromtimestamp(mktime(value), tz=timezone.utc)
            except (OverflowError, ValueError):
                continue
    return None


def _extract_content(entry) -> str:
    if getattr(entry, "content", None):
        raw = entry.content[0].get("value", "")
    else:
        raw = getattr(entry, "summary", "") or getattr(entry, "description", "")
    return clean_html(raw)


def extract(entry, source: str) -> ExtractedArticle | None:
    """Build an :class:`ExtractedArticle` from a feedparser entry.

    Returns ``None`` if the entry lacks a title or link.
    """
    title = clean_html(getattr(entry, "title", "")).strip()
    url = (getattr(entry, "link", "") or "").strip()
    if not title or not url:
        return None

    content = _extract_content(entry)
    return ExtractedArticle(
        title=title,
        source=source,
        article_url=url,
        content=content or title,
        published_at=_parse_date(entry),
        article_hash=compute_hash(title, url),
    )
