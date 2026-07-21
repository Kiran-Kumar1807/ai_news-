"""AI-powered article categorization with a deterministic fallback."""
from __future__ import annotations

import re
from functools import cache

from backend.core.categories import CATEGORIES, CATEGORY_KEYWORDS, DEFAULT_CATEGORY
from backend.logging_config import get_logger
from ingestion import llm

logger = get_logger("ai")


@cache
def _keyword_pattern(keyword: str) -> re.Pattern[str]:
    """Compile a word-boundary regex for a keyword/phrase (case-insensitive)."""
    return re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)

_PROMPT = (
    "You are a precise news classifier. Classify the following article into "
    "exactly ONE of these categories: {categories}.\n"
    "Respond with ONLY the category name, nothing else.\n\n"
    "Title: {title}\n\n"
    "Content: {content}\n"
)


def _normalize(text: str) -> str | None:
    """Map arbitrary model output onto a known category name."""
    cleaned = text.strip().strip(".").strip()
    lowered = cleaned.lower()
    for category in CATEGORIES:
        if category.lower() == lowered:
            return category
    # Model sometimes returns the category embedded in a sentence.
    for category in CATEGORIES:
        if category.lower() in lowered:
            return category
    return None


def classify_by_keywords(title: str, content: str) -> str:
    """Heuristic keyword-based classification used when Gemini is unavailable.

    Matches on whole words/phrases (via ``\\b`` boundaries) so short tokens like
    "ai" do not spuriously match words such as "Argentina" or "captain". The
    title is weighted more heavily than the body.
    """
    title_text = title or ""
    body_text = content or ""
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            pattern = _keyword_pattern(keyword)
            score += 2 * len(pattern.findall(title_text))
            score += len(pattern.findall(body_text))
        if score:
            scores[category] = score
    if not scores:
        return DEFAULT_CATEGORY
    return max(scores, key=lambda c: scores[c])


def classify(title: str, content: str) -> str:
    """Return the best-matching category for an article.

    Uses Gemini when configured, otherwise a keyword heuristic. Always returns
    one of :data:`CATEGORIES`.
    """
    prompt = _PROMPT.format(
        categories=", ".join(CATEGORIES),
        title=title,
        content=(content or "")[:4000],
    )
    raw = llm.generate(prompt)
    if raw:
        normalized = _normalize(raw)
        if normalized:
            return normalized
        logger.warning("Unrecognized category from model", extra={"ctx_raw": raw})
    return classify_by_keywords(title, content)
