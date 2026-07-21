"""Provider-agnostic LLM router with automatic failover across free-tier APIs.

Tries each configured provider in ``llm_provider_order`` and moves on to the
next as soon as one is rate-limited or errors, so the combined free quotas of
several providers approximate seamless, non-blocking service. When every
provider is unavailable ``generate`` returns ``None`` and callers fall back to
heuristics.
"""
from __future__ import annotations

import threading
import time

import requests

from backend.config import settings
from backend.logging_config import get_logger
from ingestion import gemini_client

logger = get_logger("ai")

# Per-provider light throttle so a burst doesn't instantly trip a provider's
# rate limit; failover (not sleeping) is the primary mechanism.
_locks_guard = threading.Lock()
_locks: dict[str, threading.Lock] = {}
_last_ts: dict[str, float] = {}


def _throttle(name: str, rpm: int) -> None:
    if rpm <= 0:
        return
    with _locks_guard:
        lock = _locks.setdefault(name, threading.Lock())
    min_interval = 60.0 / rpm
    with lock:
        wait = min_interval - (time.monotonic() - _last_ts.get(name, 0.0))
        if wait > 0:
            time.sleep(wait)
        _last_ts[name] = time.monotonic()


def _openai_chat(base_url: str, api_key: str, model: str, prompt: str) -> str | None:
    """Call an OpenAI-compatible ``/chat/completions`` endpoint."""
    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        },
        timeout=settings.llm_timeout_seconds,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return (content or "").strip() or None


def _groq(prompt: str) -> str | None:
    _throttle("groq", settings.groq_max_rpm)
    return _openai_chat(
        "https://api.groq.com/openai/v1",
        settings.groq_api_key,
        settings.groq_model,
        prompt,
    )


def _openrouter(prompt: str) -> str | None:
    _throttle("openrouter", settings.openrouter_max_rpm)
    return _openai_chat(
        "https://openrouter.ai/api/v1",
        settings.openrouter_api_key,
        settings.openrouter_model,
        prompt,
    )


def _gemini(prompt: str) -> str | None:
    # gemini_client applies its own throttle + 429 retry.
    return gemini_client.generate(prompt)


# name -> (enabled_check, call)
_PROVIDERS = {
    "groq": (lambda: settings.groq_enabled, _groq),
    "gemini": (lambda: settings.gemini_enabled, _gemini),
    "openrouter": (lambda: settings.openrouter_enabled, _openrouter),
}


def _enabled_providers() -> list[str]:
    order = [p.strip().lower() for p in settings.llm_provider_order.split(",") if p.strip()]
    return [name for name in order if name in _PROVIDERS and _PROVIDERS[name][0]()]


def is_available() -> bool:
    """Return whether at least one LLM provider is configured."""
    return bool(_enabled_providers())


def generate(prompt: str) -> str | None:
    """Generate text via the first provider that succeeds; ``None`` if all fail."""
    for name in _enabled_providers():
        _, call = _PROVIDERS[name]
        try:
            text = call(prompt)
            if text:
                return text
        except Exception as exc:  # pragma: no cover - network/SDK errors
            logger.warning(
                "LLM provider failed; trying next",
                extra={"ctx_provider": name, "ctx_error": str(exc)[:300]},
            )
            continue
    return None
