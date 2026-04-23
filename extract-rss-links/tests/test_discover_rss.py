"""Tests for RSS feed URL discovery from HTML (no network)."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx

from main import (
    KEY_ORIGINAL_URL,
    KEY_RSS_URL,
    _absolute_rss_url_from_html,
    build_feed_mapping,
    discover_rss_feed_url,
    save_feed_mapping,
)


class TestAbsoluteRssUrlFromHtml(unittest.TestCase):
    def test_relative_href(self) -> None:
        html = '<html><head><link rel="alternate" type="application/rss+xml" href="/feed.xml"/></head></html>'
        self.assertEqual(
            _absolute_rss_url_from_html(html, "https://example.com/blog/page"),
            "https://example.com/feed.xml",
        )

    def test_absolute_href(self) -> None:
        html = (
            '<link rel="alternate" type="application/rss+xml" '
            'href="https://cdn.example.net/rss"/>'
        )
        self.assertEqual(
            _absolute_rss_url_from_html(html, "https://example.com/"),
            "https://cdn.example.net/rss",
        )

    def test_type_with_charset(self) -> None:
        html = (
            '<link rel="alternate" type="application/rss+xml; charset=utf-8" href="feed.rss"/>'
        )
        self.assertEqual(
            _absolute_rss_url_from_html(html, "https://site.example/news/"),
            "https://site.example/news/feed.rss",
        )

    def test_rel_stylesheet_alternate(self) -> None:
        html = (
            '<link rel="stylesheet alternate" type="application/rss+xml" href="a.xml"/>'
        )
        self.assertEqual(
            _absolute_rss_url_from_html(html, "https://x.test/"),
            "https://x.test/a.xml",
        )

    def test_no_matching_link(self) -> None:
        html = '<html><head><title>x</title></head></html>'
        self.assertIsNone(_absolute_rss_url_from_html(html, "https://example.com/"))

    def test_first_match_wins(self) -> None:
        html = (
            '<link rel="alternate" type="application/rss+xml" href="first.xml"/>'
            '<link rel="alternate" type="application/rss+xml" href="second.xml"/>'
        )
        self.assertEqual(
            _absolute_rss_url_from_html(html, "https://example.com/"),
            "https://example.com/first.xml",
        )

    def test_case_insensitive_type_and_rel(self) -> None:
        html = '<link rel="Alternate" type="Application/RSS+XML" HREF="r.xml"/>'
        self.assertEqual(
            _absolute_rss_url_from_html(html, "https://z.example/"),
            "https://z.example/r.xml",
        )


class TestDiscoverRssFeedUrl(unittest.TestCase):
    def test_http_error_returns_none(self) -> None:
        with patch("main.httpx.Client") as mock_client_cls:
            instance = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = instance
            instance.get.side_effect = httpx.RequestError("boom", request=MagicMock())
            self.assertIsNone(discover_rss_feed_url("https://example.com/"))

    def test_non_success_status_returns_none(self) -> None:
        with patch("main.httpx.Client") as mock_client_cls:
            instance = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = instance
            resp = MagicMock()
            resp.status_code = 404
            instance.get.return_value = resp
            self.assertIsNone(discover_rss_feed_url("https://example.com/missing"))

    def test_success_returns_absolute_url(self) -> None:
        with patch("main.httpx.Client") as mock_client_cls:
            instance = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = instance
            resp = MagicMock()
            resp.status_code = 200
            resp.url = "https://example.com/final/"
            resp.text = (
                '<link rel="alternate" type="application/rss+xml" href="atom.xml"/>'
            )
            instance.get.return_value = resp
            self.assertEqual(
                discover_rss_feed_url("https://example.com/start"),
                "https://example.com/final/atom.xml",
            )


class TestBuildFeedMapping(unittest.TestCase):
    def test_keys_and_rss_none(self) -> None:
        urls = ["https://a.example/", "https://b.example/"]
        with patch(
            "main.discover_rss_feed_url",
            side_effect=["https://a.example/feed.xml", None],
        ):
            rows = build_feed_mapping(urls)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][KEY_ORIGINAL_URL], "https://a.example/")
        self.assertEqual(rows[0][KEY_RSS_URL], "https://a.example/feed.xml")
        self.assertEqual(rows[1][KEY_ORIGINAL_URL], "https://b.example/")
        self.assertIsNone(rows[1][KEY_RSS_URL])


class TestSaveFeedMapping(unittest.TestCase):
    def test_roundtrip_json(self) -> None:
        rows = [
            {KEY_ORIGINAL_URL: "https://x.example/", KEY_RSS_URL: None},
            {
                KEY_ORIGINAL_URL: "https://y.example/blog",
                KEY_RSS_URL: "https://y.example/blog/rss",
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.json"
            save_feed_mapping(path, rows)
            text = path.read_text(encoding="utf-8")
            loaded = json.loads(text)
        self.assertEqual(loaded, rows)
        self.assertTrue(text.endswith("\n"))


if __name__ == "__main__":
    unittest.main()
