"""Configured RSS feed sources."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str


RSS_FEEDS: list[FeedSource] = [
    FeedSource("TechCrunch", "https://techcrunch.com/feed/"),
    FeedSource("BBC News", "https://feeds.bbci.co.uk/news/rss.xml"),
    FeedSource("Reuters", "https://www.reutersagency.com/feed/"),
    FeedSource("ESPN", "https://www.espn.com/espn/rss/news"),
    FeedSource("Hacker News", "https://hnrss.org/frontpage"),
    FeedSource("The Verge", "https://www.theverge.com/rss/index.xml"),
]
