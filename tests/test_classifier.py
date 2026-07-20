"""Tests for the classification service (fallback path)."""
from __future__ import annotations

from backend.core.categories import CATEGORIES
from ingestion import classifier


def test_classify_returns_valid_category():
    category = classifier.classify("Some neutral headline", "generic content")
    assert category in CATEGORIES


def test_classify_ai_article():
    category = classifier.classify(
        "OpenAI releases new GPT model",
        "The new large language model uses deep learning and neural networks.",
    )
    assert category == "Artificial Intelligence"


def test_classify_security_article():
    category = classifier.classify(
        "Major data breach exposes millions",
        "Hackers exploited a vulnerability to deploy ransomware and malware.",
    )
    assert category == "Cybersecurity"


def test_keyword_matching_uses_word_boundaries():
    # "Argentina"/"captain"/"again" must NOT match the short keyword "ai".
    category = classifier.classify_by_keywords(
        "Argentina captain scores again in football match",
        "The player and coach celebrated the goal in the league championship.",
    )
    assert category == "Sports"
    assert category != "Artificial Intelligence"


def test_normalize_maps_model_output():
    assert classifier._normalize("Finance") == "Finance"
    assert classifier._normalize("The category is Sports.") == "Sports"
    assert classifier._normalize("nonsense") is None
