from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

RSS_SOURCES = [
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("Decrypt", "https://decrypt.co/feed"),
    ("CryptoSlate", "https://cryptoslate.com/feed/"),
    ("Bitcoin Magazine", "https://bitcoinmagazine.com/feed"),
    ("The Block", "https://www.theblock.co/rss.xml"),
    ("NewsBTC", "https://www.newsbtc.com/feed/"),
]


@dataclass(frozen=True)
class NewsItem:
    title: str
    source: str
    url: str
    published_at: Optional[datetime] = None
    summary: str = ""


def get_recent_news(limit: int = 15) -> list[NewsItem]:
    """Fetch recent crypto headlines from free RSS feeds."""
    items: list[NewsItem] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

    for source_name, feed_url in RSS_SOURCES:
        for item in _fetch_rss_items(source_name, feed_url):
            title_key = item.title.strip().lower()
            url_key = item.url.strip()
            if not title_key or title_key in seen_titles or url_key in seen_urls:
                continue

            seen_titles.add(title_key)
            if url_key:
                seen_urls.add(url_key)
            items.append(item)

    items.sort(
        key=lambda item: item.published_at or datetime.min,
        reverse=True,
    )
    return items[:limit]


def _fetch_rss_items(source_name: str, feed_url: str) -> list[NewsItem]:
    try:
        request = Request(feed_url, headers={"User-Agent": "CryptoAnalyst/0.1"})
        with urlopen(request, timeout=15) as response:
            xml_text = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return [
            NewsItem(
                title=f"{source_name} RSS unavailable: HTTP {exc.code}",
                source=source_name,
                url=feed_url,
            )
        ]
    except (URLError, TimeoutError) as exc:
        return [
            NewsItem(
                title=f"{source_name} RSS request failed: {exc}",
                source=source_name,
                url=feed_url,
            )
        ]

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return [
            NewsItem(
                title=f"{source_name} RSS returned unreadable XML",
                source=source_name,
                url=feed_url,
            )
        ]

    if root.tag.endswith("rss"):
        return _parse_rss_channel(source_name, root)

    return _parse_atom_feed(source_name, root)


def _parse_rss_channel(source_name: str, root: ET.Element) -> list[NewsItem]:
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for entry in channel.findall("item"):
        title = _text(entry, "title")
        url = _text(entry, "link")
        published = _parse_date(_text(entry, "pubDate"))
        summary = _text(entry, "description")

        if title:
            items.append(
                NewsItem(
                    title=title,
                    source=source_name,
                    url=url,
                    published_at=published,
                    summary=summary,
                )
            )

    return items


def _parse_atom_feed(source_name: str, root: ET.Element) -> list[NewsItem]:
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", namespace)
    if not entries:
        entries = root.findall("entry")

    items = []
    for entry in entries:
        title = _text(entry, "title") or _text(entry, "atom:title", namespace)
        url = _atom_link(entry, namespace)
        published = _parse_date(
            _text(entry, "published")
            or _text(entry, "updated")
            or _text(entry, "atom:published", namespace)
            or _text(entry, "atom:updated", namespace)
        )
        summary = _text(entry, "summary") or _text(entry, "atom:summary", namespace)

        if title:
            items.append(
                NewsItem(
                    title=title,
                    source=source_name,
                    url=url,
                    published_at=published,
                    summary=summary,
                )
            )

    return items


def _text(
    element: ET.Element,
    tag: str,
    namespace: Optional[dict[str, str]] = None,
) -> str:
    child = element.find(tag, namespace or {})
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _atom_link(entry: ET.Element, namespace: dict[str, str]) -> str:
    link = entry.find("atom:link", namespace) or entry.find("link")
    if link is None:
        return ""
    return link.attrib.get("href", "").strip()


def _parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
        return _normalize_datetime(parsed)
    except (TypeError, ValueError):
        pass

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return _normalize_datetime(parsed)
    except ValueError:
        return None


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
