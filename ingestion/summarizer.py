"""AI-powered article summarization with a deterministic fallback."""
from __future__ import annotations

import re

from backend.logging_config import get_logger
from ingestion import gemini_client

logger = get_logger("ai")

MAX_WORDS = 80

_PROMPT = (
    "Summarize the following news article as exactly 3 concise bullet points.\n"
    "Rules:\n"
    "- Maximum 80 words total.\n"
    "- Use clear, factual language.\n"
    "- Do not invent facts; preserve important details.\n"
    "- Start each bullet with '- '.\n\n"
    "Title: {title}\n\n"
    "Content: {content}\n"
)

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _limit_words(text: str, max_words: int = MAX_WORDS) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(",;:") + "…"


def summarize_by_sentences(title: str, content: str) -> str:
    """Fallback extractive summary: first three sentences as bullets."""
    text = (content or "").strip() or title
    sentences = [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]
    if not sentences:
        sentences = [title]
    bullets = sentences[:3]
    summary = "\n".join(f"- {b}" for b in bullets)
    return _limit_words(summary)


def summarize(title: str, content: str) -> str:
    """Return a 3-bullet, <=80 word summary for an article.

    Uses Gemini when configured, otherwise an extractive fallback.
    """
    prompt = _PROMPT.format(title=title, content=(content or "")[:6000])
    raw = gemini_client.generate(prompt)
    if raw:
        return _limit_words(raw)
    return summarize_by_sentences(title, content)
