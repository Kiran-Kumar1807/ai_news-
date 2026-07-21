"""Tests for the Gemini client throttling and retry behavior."""
from ingestion import gemini_client


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModel:
    """Raises a rate-limit error for the first ``fail_times`` calls."""

    def __init__(self, text="ok", fail_times=0, error="429 quota exceeded"):
        self.text = text
        self.fail_times = fail_times
        self.error = error
        self.calls = 0

    def generate_content(self, prompt):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError(self.error)
        return _FakeResponse(self.text)


def _no_throttle(monkeypatch):
    monkeypatch.setattr(gemini_client.time, "sleep", lambda *_: None)
    monkeypatch.setattr(gemini_client, "_throttle", lambda: None)


def test_generate_retries_then_succeeds(monkeypatch):
    _no_throttle(monkeypatch)
    monkeypatch.setattr(gemini_client.settings, "gemini_max_retries", 2)
    model = _FakeModel(text="hello", fail_times=1)
    monkeypatch.setattr(gemini_client, "_get_model", lambda: model)

    assert gemini_client.generate("prompt") == "hello"
    assert model.calls == 2


def test_generate_gives_up_after_retries(monkeypatch):
    _no_throttle(monkeypatch)
    monkeypatch.setattr(gemini_client.settings, "gemini_max_retries", 2)
    model = _FakeModel(fail_times=99)
    monkeypatch.setattr(gemini_client, "_get_model", lambda: model)

    assert gemini_client.generate("prompt") is None
    assert model.calls == 3  # initial + 2 retries


def test_generate_does_not_retry_non_rate_errors(monkeypatch):
    _no_throttle(monkeypatch)
    monkeypatch.setattr(gemini_client.settings, "gemini_max_retries", 2)
    model = _FakeModel(fail_times=99, error="500 internal error")
    monkeypatch.setattr(gemini_client, "_get_model", lambda: model)

    assert gemini_client.generate("prompt") is None
    assert model.calls == 1  # no retry for non-rate-limit errors


def test_parse_retry_delay():
    msg = "429 quota exceeded. Please retry in 16.6s retry_delay { seconds: 16 }"
    assert gemini_client._parse_retry_delay(msg) == 16.6
    assert gemini_client._parse_retry_delay("no delay here") is None
