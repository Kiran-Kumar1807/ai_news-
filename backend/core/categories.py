"""Canonical set of news categories used across the application."""
from __future__ import annotations

CATEGORIES: list[str] = [
    "Artificial Intelligence",
    "Finance",
    "Business",
    "Technology",
    "Cybersecurity",
    "Politics",
    "Sports",
    "Esports",
    "Healthcare",
    "Startups",
]

DEFAULT_CATEGORY = "Technology"

# Keyword hints used by the heuristic classifier fallback (no Gemini key).
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Artificial Intelligence": [
        "ai", "artificial intelligence", "machine learning", "llm", "gpt",
        "neural", "deep learning", "openai", "gemini", "anthropic", "model",
    ],
    "Finance": [
        "stock", "market", "finance", "bank", "inflation", "interest rate",
        "investor", "earnings", "crypto", "bitcoin", "economy", "trading",
    ],
    "Business": [
        "business", "company", "revenue", "acquisition", "merger", "ceo",
        "profit", "enterprise", "corporate", "quarterly",
    ],
    "Technology": [
        "technology", "gadget", "software", "hardware", "device", "app",
        "smartphone", "chip", "cloud", "internet",
    ],
    "Cybersecurity": [
        "security", "hack", "breach", "malware", "ransomware", "vulnerability",
        "phishing", "cyber", "exploit", "data leak",
    ],
    "Politics": [
        "election", "government", "senate", "policy", "president", "congress",
        "parliament", "vote", "political", "minister",
    ],
    "Sports": [
        "match", "game", "tournament", "league", "player", "coach", "goal",
        "championship", "olympic", "football", "cricket", "nba",
    ],
    "Esports": [
        "esports", "valorant", "league of legends", "dota", "counter-strike",
        "tournament prize", "twitch", "gaming championship",
    ],
    "Healthcare": [
        "health", "medical", "disease", "vaccine", "hospital", "patient",
        "drug", "clinical", "wellness", "medicine",
    ],
    "Startups": [
        "startup", "seed round", "series a", "venture", "funding", "founder",
        "vc", "raised", "y combinator", "incubator",
    ],
}
