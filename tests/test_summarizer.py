"""Tests for the summarization service (fallback path)."""
from __future__ import annotations

from ingestion import summarizer


def test_summary_is_word_limited():
    content = " ".join(f"word{i}" for i in range(300)) + "."
    summary = summarizer.summarize("A long title", content)
    # The word-limit helper caps at MAX_WORDS (plus an ellipsis token).
    assert len(summary.split()) <= summarizer.MAX_WORDS + 1


def test_summary_falls_back_to_bullets():
    content = "First sentence here. Second sentence follows. Third one now. Fourth extra."
    bulletin, summary = summarizer.summarize_by_sentences("Title", content)
    bullets = [line for line in summary.splitlines() if line.startswith("- ")]
    assert len(bullets) == 3
    assert bulletin


def test_parse_llm_output_cleans_bullets():
    raw = (
        "TL;DR: Markets rallied on strong earnings.\n"
        "* **First** point.\n"
        "1. Second point.\n"
        "- Third point.\n"
        "- Third point.\n"  # duplicate should be dropped
    )
    bulletin, summary = summarizer._parse_llm_output(raw)
    assert bulletin == "Markets rallied on strong earnings."
    bullets = [line for line in summary.splitlines() if line.startswith("- ")]
    assert bullets == ["- First point.", "- Second point.", "- Third point."]


def test_summarize_article_uses_llm(monkeypatch):
    monkeypatch.setattr(
        summarizer.llm,
        "generate",
        lambda _: "TL;DR: A quick recap.\n- One.\n- Two.\n- Three.",
    )
    bulletin, summary = summarizer.summarize_article("T", "some content")
    assert bulletin == "A quick recap."
    assert summary.count("- ") == 3


def test_summary_handles_empty_content():
    summary = summarizer.summarize("Only a title", "")
    assert "Only a title" in summary
