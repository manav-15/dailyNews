"""Source adapters: fetch candidate items and normalize to a common shape.

Adapters filter to recent items (config.RECENT_WINDOW_HOURS) so the digest
reflects the latest news rather than evergreen / back-catalog content.
"""
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Optional

import httpx

import config

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


@dataclass
class Item:
    source: str
    source_id: str
    url: str = ""
    title: str = ""
    body: str = ""
    author: str = ""
    published_at: str = ""
    score: int = 0
    extra: dict = field(default_factory=dict)


def _cutoff_ts() -> int:
    return int(time.time()) - config.RECENT_WINDOW_HOURS * 3600


def _is_recent(iso: str, cutoff_ts: int) -> bool:
    if not iso:
        return False
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() >= cutoff_ts
    except ValueError:
        return True  # unparseable -> keep rather than drop blindly


def _rfc2822_ts(datestr: str) -> Optional[float]:
    try:
        return parsedate_to_datetime(datestr).timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


class HackerNewsAdapter:
    """Hacker News via the Algolia API, newest-first within the recency window."""

    source = "hackernews"

    def fetch(self, keywords: List[str]) -> List[Item]:
        cutoff = _cutoff_ts()
        items: List[Item] = []
        for kw in keywords:
            try:
                r = httpx.get(
                    "https://hn.algolia.com/api/v1/search_by_date",
                    params={
                        "query": kw,
                        "tags": "story",
                        "numericFilters": f"created_at_i>{cutoff}",
                        "hitsPerPage": config.ITEMS_PER_SOURCE,
                    },
                    timeout=15.0,
                )
                r.raise_for_status()
                for hit in r.json().get("hits", []):
                    if int(hit.get("created_at_i") or 0) < cutoff:
                        continue
                    oid = str(hit.get("objectID", ""))
                    if not oid:
                        continue
                    items.append(
                        Item(
                            source=self.source,
                            source_id=oid,
                            url=hit.get("url") or f"https://news.ycombinator.com/item?id={oid}",
                            title=hit.get("title") or "",
                            body=(hit.get("story_text") or "")[:2000],
                            author=hit.get("author") or "",
                            published_at=hit.get("created_at") or "",
                            score=hit.get("points") or 0,
                        )
                    )
            except Exception:
                continue
        return items


class ArxivAdapter:
    """arXiv via the public Atom API, newest-first within the recency window."""

    source = "arxiv"

    def fetch(self, keywords: List[str]) -> List[Item]:
        q = " OR ".join(f'all:"{kw}"' for kw in keywords)
        if not q:
            return []
        cutoff = _cutoff_ts()
        try:
            r = httpx.get(
                "http://export.arxiv.org/api/query",
                params={
                    "search_query": q,
                    "max_results": config.ITEMS_PER_SOURCE,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                },
                timeout=20.0,
            )
            r.raise_for_status()
            root = ET.fromstring(r.text)
            items: List[Item] = []
            for entry in root.findall("atom:entry", ATOM_NS):
                eid = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
                published = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
                if not eid or not _is_recent(published, cutoff):
                    continue
                items.append(
                    Item(
                        source=self.source,
                        source_id=eid,
                        url=eid,
                        title=(entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip(),
                        body=(entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip()[:2000],
                        author=", ".join(
                            a.findtext("atom:name", default="", namespaces=ATOM_NS)
                            for a in entry.findall("atom:author", ATOM_NS)
                        ),
                        published_at=published,
                    )
                )
            return items
        except Exception:
            return []


class GoogleNewsAdapter:
    """Google News RSS search (free, no key) — general topical news."""

    source = "google_news"

    def fetch(self, keywords: List[str]) -> List[Item]:
        cutoff = _cutoff_ts()
        items: List[Item] = []
        for kw in keywords:
            try:
                r = httpx.get(
                    "https://news.google.com/rss/search",
                    params={"q": kw, "hl": "en-US", "gl": "US", "ceid": "US:en"},
                    headers={"User-Agent": "Mozilla/5.0 (compatible; daily-digest/0.1)"},
                    timeout=15.0,
                )
                r.raise_for_status()
                root = ET.fromstring(r.text)
                for node in root.iter("item"):
                    title = (node.findtext("title") or "").strip()
                    link = (node.findtext("link") or "").strip()
                    pubdate = (node.findtext("pubDate") or "").strip()
                    if not title or not link:
                        continue
                    ts = _rfc2822_ts(pubdate)
                    if ts is not None and ts < cutoff:
                        continue
                    items.append(
                        Item(
                            source=self.source,
                            source_id=link,
                            url=link,
                            title=title,
                            body=(node.findtext("description") or "").strip()[:2000],
                            author=(node.findtext("source") or "").strip(),
                            published_at=pubdate,
                        )
                    )
            except Exception:
                continue
        return items


ADAPTERS = [GoogleNewsAdapter(), HackerNewsAdapter(), ArxivAdapter()]
