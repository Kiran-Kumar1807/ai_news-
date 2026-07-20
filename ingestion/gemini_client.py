"""Thin wrapper around the Google Gemini API.

Isolates the third-party dependency so the rest of the codebase can depend on a
small, testable surface. When no API key is configured (or the SDK is missing)
``generate`` returns ``None`` and callers fall back to heuristics.
"""
from __future__ import annotations

from functools import lru_cache

from backend.config import settings
from backend.logging_config import get_logger

logger = get_logger("ai")


@lru_cache
def _get_model():
    """Return a configured Gemini model instance, or ``None`` if unavailable."""
    if not settings.gemini_enabled:
        return None
    try:
        import google.generativeai as genai
    except ImportError:  # pragma: no cover - depends on environment
        logger.warning("google-generativeai not installed; using fallbacks")
        return None

    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(settings.gemini_model)


def is_available() -> bool:
    """Return whether Gemini generation is currently usable."""
    return _get_model() is not None


def generate(prompt: str) -> str | None:
    """Generate text for ``prompt``; returns ``None`` on any failure."""
    model = _get_model()
    if model is None:
        return None
    try:
        response = model.generate_content(prompt)
        return (response.text or "").strip() or None
    except Exception as exc:  # pragma: no cover - network/SDK errors
        logger.error("Gemini generation failed", extra={"ctx_error": str(exc)})
        return None
