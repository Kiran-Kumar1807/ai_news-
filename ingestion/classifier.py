"""AI-powered article categorization with a deterministic fallback."""
from __future__ import annotations

from backend.core.categories import CATEGORIES, CATEGORY_KEYWORDS, DEFAULT_CATEGORY
from backend.logging_config import get_logger
from ingestion import gemini_client

logger = get_logger("ai")

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
    """Heuristic keyword-based classification used when Gemini is unavailable."""
    text = f"{title} {content}".lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(text.count(keyword) for keyword in keywords)
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
    raw = gemini_client.generate(prompt)
    if raw:
        normalized = _normalize(raw)
        if normalized:
            return normalized
        logger.warning("Unrecognized category from model", extra={"ctx_raw": raw})
    return classify_by_keywords(title, content)
