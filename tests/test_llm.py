"""Tests for the multi-provider LLM router."""
from ingestion import llm


def test_is_available_reflects_config(monkeypatch):
    for key in ("groq_api_key", "gemini_api_key", "openrouter_api_key"):
        monkeypatch.setattr(llm.settings, key, "")
    assert llm.is_available() is False
    monkeypatch.setattr(llm.settings, "groq_api_key", "k")
    assert llm.is_available() is True


def test_generate_fails_over_to_next_provider(monkeypatch):
    calls = []

    def boom(_prompt):
        calls.append("groq")
        raise RuntimeError("429 rate limit")

    def ok(_prompt):
        calls.append("gemini")
        return "answer"

    monkeypatch.setattr(
        llm, "_PROVIDERS", {"groq": (lambda: True, boom), "gemini": (lambda: True, ok)}
    )
    monkeypatch.setattr(llm.settings, "llm_provider_order", "groq,gemini")

    assert llm.generate("p") == "answer"
    assert calls == ["groq", "gemini"]


def test_generate_returns_none_when_all_fail(monkeypatch):
    def boom(_prompt):
        raise RuntimeError("429")

    monkeypatch.setattr(llm, "_PROVIDERS", {"groq": (lambda: True, boom)})
    monkeypatch.setattr(llm.settings, "llm_provider_order", "groq")
    assert llm.generate("p") is None


def test_only_enabled_providers_run(monkeypatch):
    calls = []

    monkeypatch.setattr(
        llm,
        "_PROVIDERS",
        {
            "groq": (lambda: False, lambda _p: calls.append("groq") or "x"),
            "gemini": (lambda: True, lambda _p: (calls.append("gemini"), "g")[1]),
        },
    )
    monkeypatch.setattr(llm.settings, "llm_provider_order", "groq,gemini")
    assert llm.generate("p") == "g"
    assert calls == ["gemini"]


def test_openai_chat_parses_content(monkeypatch):
    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": " hi "}}]}

    monkeypatch.setattr(llm.requests, "post", lambda *a, **k: FakeResp())
    assert llm._openai_chat("http://x", "k", "m", "p") == "hi"
