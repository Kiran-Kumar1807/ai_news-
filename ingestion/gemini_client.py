"""Thin wrapper around the Google Gemini API.

Isolates the third-party dependency so the rest of the codebase can depend on a
small, testable surface. When no API key is configured (or the SDK is missing)
``generate`` returns ``None`` and callers fall back to heuristics.
"""
from __future__ import annotations

import re
import threading
import time
from functools import lru_cache

from backend.config import settings
from backend.logging_config import get_logger

logger = get_logger("ai")

_rate_lock = threading.Lock()
_last_call_ts = 0.0

_RETRY_DELAY_RE = re.compile(r"retry(?:_delay)?[^0-9]*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)


def _throttle() -> None:
    """Block until enough time has passed to respect ``gemini_max_rpm``."""
    global _last_call_ts
    rpm = max(1, settings.gemini_max_rpm)
    min_interval = 60.0 / rpm
    with _rate_lock:
        wait = min_interval - (time.monotonic() - _last_call_ts)
        if wait > 0:
            time.sleep(wait)
        _last_call_ts = time.monotonic()


def _is_rate_limit_error(message: str) -> bool:
    lowered = message.lower()
    return "429" in message or "quota" in lowered or "rate limit" in lowered


def _parse_retry_delay(message: str) -> float | None:
    match = _RETRY_DELAY_RE.search(message)
    return float(match.group(1)) if match else None


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
    """Generate text for ``prompt``; returns ``None`` on any failure.

    Calls are throttled to ``gemini_max_rpm`` and retried with backoff on
    rate-limit (429) responses before falling back to heuristics.
    """
    model = _get_model()
    if model is None:
        return None

    for attempt in range(settings.gemini_max_retries + 1):
        _throttle()
        try:
            response = model.generate_content(prompt)
            return (response.text or "").strip() or None
        except Exception as exc:  # pragma: no cover - network/SDK errors
            message = str(exc)
            if _is_rate_limit_error(message) and attempt < settings.gemini_max_retries:
                delay = _parse_retry_delay(message) or 60.0 / max(1, settings.gemini_max_rpm)
                logger.warning(
                    "Gemini rate-limited; backing off",
                    extra={"ctx_delay": round(delay, 2), "ctx_attempt": attempt + 1},
                )
                time.sleep(delay)
                continue
            logger.error("Gemini generation failed", extra={"ctx_error": message})
            return None
    return None
