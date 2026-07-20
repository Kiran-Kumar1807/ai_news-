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
    summary = summarizer.summarize_by_sentences("Title", content)
    bullets = [line for line in summary.splitlines() if line.startswith("- ")]
    assert len(bullets) == 3


def test_summary_handles_empty_content():
    summary = summarizer.summarize("Only a title", "")
    assert "Only a title" in summary
