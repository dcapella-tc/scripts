"""Discover RSS feed URLs from HTML pages (link rel=alternate type=application/rss+xml)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; RSSFeedDiscover/1.0; +https://example.invalid/bot)"
)


def _tag_attr_as_str(value: object) -> str | None:
    """Coerce BeautifulSoup attribute values (str, list, etc.) to a single string."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [x for x in value if isinstance(x, str)]
        return " ".join(parts) if parts else None
    return None


def _rel_has_alternate(rel: str | None) -> bool:
    if not rel:
        return False
    tokens = rel.lower().split()
    return "alternate" in tokens


def _type_is_rss_xml(type_attr: str | None) -> bool:
    if not type_attr:
        return False
    base = type_attr.split(";", 1)[0].strip().lower()
    return base == "application/rss+xml"


def _absolute_rss_url_from_html(html: str, effective_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("link"):
        if not _rel_has_alternate(_tag_attr_as_str(tag.get("rel"))):
            continue
        if not _type_is_rss_xml(_tag_attr_as_str(tag.get("type"))):
            continue
        href = _tag_attr_as_str(tag.get("href"))
        if not href:
            continue
        return urljoin(effective_url, href.strip())
    return None


def discover_rss_feed_url(page_url: str, *, timeout: float = 20.0) -> str | None:
    """GET ``page_url``, parse HTML, return the first RSS autodiscovery ``href`` as an absolute URL.

    Follows redirects. Resolves relative ``href`` against the final response URL after redirects.
    Returns ``None`` if the request fails, the status is not success, or no matching ``<link>`` exists.
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    try:
        with httpx.Client(
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            response = client.get(page_url)
    except httpx.HTTPError:
        return None

    if response.status_code >= 400:
        return None

    effective = str(response.url)
    return _absolute_rss_url_from_html(response.text, effective)


def _load_urls_json(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("urls.json must contain a JSON array of strings")
    out: list[str] = []
    for item in data:
        if not isinstance(item, str):
            raise ValueError("urls.json must contain only strings")
        out.append(item)
    return out


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    base = Path(__file__).resolve().parent
    urls_path = base / "urls.json"
    if argv:
        urls_path = Path(argv[0]).expanduser()

    try:
        urls = _load_urls_json(urls_path)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"Error loading {urls_path}: {e}", file=sys.stderr)
        return 1

    for url in urls:
        feed = discover_rss_feed_url(url)
        if feed is None:
            print(f"{url}\t(no RSS link found)")
        else:
            print(f"{url}\t{feed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
