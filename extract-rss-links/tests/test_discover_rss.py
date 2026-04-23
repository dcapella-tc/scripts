"""Tests for RSS feed URL discovery from HTML (no network)."""

import unittest
from unittest.mock import MagicMock, patch

import httpx

from main import _absolute_rss_url_from_html, discover_rss_feed_url


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


if __name__ == "__main__":
    unittest.main()
