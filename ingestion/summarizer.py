"""AI-powered article summarization with a deterministic fallback.

Produces a one-line TL;DR "bulletin" plus a clean 3-bullet summary from a single
LLM call, and normalizes the output so the UI always renders consistent bullets.
"""
from __future__ import annotations

import re

from backend.logging_config import get_logger
from ingestion import llm

logger = get_logger("ai")

MAX_WORDS = 80
MAX_BULLETIN_CHARS = 160

_PROMPT = (
    "Summarize the following news article.\n"
    "Respond in EXACTLY this format and nothing else:\n"
    "TL;DR: <one punchy sentence, max 18 words>\n"
    "- <bullet 1>\n"
    "- <bullet 2>\n"
    "- <bullet 3>\n\n"
    "Rules:\n"
    "- Exactly 3 bullets, max 80 words across all bullets.\n"
    "- Clear, factual language. Do not invent facts.\n\n"
    "Title: {title}\n\n"
    "Content: {content}\n"
)

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_BULLET_PREFIX_RE = re.compile(r"^\s*(?:[-*•\u2022]|\d+[.)])\s*")
_TLDR_PREFIX_RE = re.compile(r"^\s*(?:tl;?dr|summary)\s*[:\-]\s*", re.IGNORECASE)


def _limit_words(text: str, max_words: int = MAX_WORDS) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(",;:") + "…"


def _clean_bullet(line: str) -> str:
    """Strip list markers/markdown and collapse whitespace from a bullet line."""
    line = _BULLET_PREFIX_RE.sub("", line)
    line = re.sub(r"\*\*|__|`", "", line)  # drop bold/inline-code markdown
    return re.sub(r"\s+", " ", line).strip()


def _format_bullets(bullets: list[str]) -> str:
    unique: list[str] = []
    for bullet in bullets:
        cleaned = _clean_bullet(bullet)
        if cleaned and cleaned not in unique:
            unique.append(cleaned)
    return _limit_words("\n".join(f"- {b}" for b in unique[:3]))


def _parse_llm_output(raw: str) -> tuple[str | None, str | None]:
    """Split raw model output into (bulletin, 3-bullet summary)."""
    bulletin: str | None = None
    bullets: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if bulletin is None and _TLDR_PREFIX_RE.match(stripped):
            bulletin = _TLDR_PREFIX_RE.sub("", stripped).strip()
            continue
        bullets.append(stripped)
    summary = _format_bullets(bullets) if bullets else None
    if bulletin:
        bulletin = _clean_bullet(bulletin)[:MAX_BULLETIN_CHARS] or None
    return bulletin, summary


def summarize_by_sentences(title: str, content: str) -> tuple[str, str]:
    """Fallback: derive a bulletin + 3-bullet summary from the leading text."""
    text = (content or "").strip() or title
    sentences = [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]
    if not sentences:
        sentences = [title]
    bulletin = sentences[0][:MAX_BULLETIN_CHARS]
    summary = _format_bullets(sentences[:3])
    return bulletin, summary


def summarize_article(title: str, content: str) -> tuple[str | None, str]:
    """Return ``(bulletin, summary)`` for an article.

    Uses the LLM router when configured, otherwise an extractive fallback.
    ``summary`` is always a clean 3-bullet block; ``bulletin`` is a one-liner.
    """
    prompt = _PROMPT.format(title=title, content=(content or "")[:6000])
    raw = llm.generate(prompt)
    if raw:
        bulletin, summary = _parse_llm_output(raw)
        if summary:
            if not bulletin:
                bulletin = summarize_by_sentences(title, content)[0]
            return bulletin, summary
    return summarize_by_sentences(title, content)


def summarize(title: str, content: str) -> str:
    """Backward-compatible helper returning only the 3-bullet summary."""
    return summarize_article(title, content)[1]
