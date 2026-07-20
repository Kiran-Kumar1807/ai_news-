"""Tests for the ingestion pipeline (extractor, fetcher, orchestration)."""
from __future__ import annotations

import feedparser

from ingestion import article_extractor, ingest, rss_fetcher
from ingestion.article_extractor import clean_html, compute_hash, extract
from ingestion.feeds import FeedSource

SAMPLE_RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
<title>Example</title>
<item>
  <title>AI breakthrough announced</title>
  <link>https://example.com/ai</link>
  <description>&lt;p&gt;A new machine learning model was released.&lt;/p&gt;</description>
  <pubDate>Tue, 01 Jul 2025 10:00:00 GMT</pubDate>
</item>
<item>
  <title>Market rallies on earnings</title>
  <link>https://example.com/finance</link>
  <description>Stocks climbed after strong bank earnings.</description>
  <pubDate>Tue, 01 Jul 2025 09:00:00 GMT</pubDate>
</item>
</channel></rss>"""


def test_clean_html_strips_tags():
    assert clean_html("<p>Hello   <b>world</b></p>") == "Hello world"
    assert clean_html("") == ""


def test_extract_builds_article():
    parsed = feedparser.parse(SAMPLE_RSS)
    article = extract(parsed.entries[0], "Example")
    assert article is not None
    assert article.title == "AI breakthrough announced"
    assert article.source == "Example"
    assert article.published_at is not None
    assert article.article_hash == compute_hash(article.title, article.article_url)


def test_extract_returns_none_without_link():
    class Entry:
        title = "No link"

    assert extract(Entry(), "Example") is None


def test_fetch_feed_uses_feedparser(monkeypatch):
    parsed = feedparser.parse(SAMPLE_RSS)
    monkeypatch.setattr(rss_fetcher.feedparser, "parse", lambda url: parsed)
    articles = rss_fetcher.fetch_feed(FeedSource("Example", "https://x"))
    assert len(articles) == 2


def test_fetch_all_deduplicates(monkeypatch):
    parsed = feedparser.parse(SAMPLE_RSS)
    monkeypatch.setattr(rss_fetcher.feedparser, "parse", lambda url: parsed)
    feeds = [FeedSource("A", "https://a"), FeedSource("B", "https://b")]
    articles = rss_fetcher.fetch_all(feeds)
    # Same content in both feeds -> deduplicated by hash.
    assert len(articles) == 2


def test_run_ingestion_stores_articles(monkeypatch):
    parsed = feedparser.parse(SAMPLE_RSS)
    extracted = [extract(e, "Example") for e in parsed.entries]
    monkeypatch.setattr(ingest, "fetch_all", lambda: extracted)

    result = ingest.run_ingestion()
    assert result.fetched == 2
    assert result.stored == 2
    assert result.duplicates == 0

    # Running again stores nothing new (dedup).
    result2 = ingest.run_ingestion()
    assert result2.stored == 0
    assert result2.duplicates == 2


def test_parse_date_handles_missing(monkeypatch):
    class Entry:
        pass

    assert article_extractor._parse_date(Entry()) is None
