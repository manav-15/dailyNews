"""Source adapters: fetch candidate items and normalize to a common shape."""
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

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


def _iso(dt) -> str:
    return dt.isoformat()


class HackerNewsAdapter:
    """Hacker News via the Algolia API (free, no key)."""

    source = "hackernews"

    def fetch(self, keywords: List[str]) -> List[Item]:
        items: List[Item] = []
        for kw in keywords:
            try:
                r = httpx.get(
                    "https://hn.algolia.com/api/v1/search",
                    params={"query": kw, "tags": "story", "hitsPerPage": config.ITEMS_PER_SOURCE},
                    timeout=15.0,
                )
                r.raise_for_status()
                for hit in r.json().get("hits", []):
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
                # A single keyword/source failure must not break the digest.
                continue
        return items


class ArxivAdapter:
    """arXiv via the public Atom API (free, no key)."""

    source = "arxiv"

    def fetch(self, keywords: List[str]) -> List[Item]:
        q = " OR ".join(f'all:"{kw}"' for kw in keywords)
        if not q:
            return []
        try:
            r = httpx.get(
                "http://export.arxiv.org/api/query",
                params={"search_query": q, "max_results": config.ITEMS_PER_SOURCE},
                timeout=20.0,
            )
            r.raise_for_status()
            root = ET.fromstring(r.text)
            items: List[Item] = []
            for entry in root.findall("atom:entry", ATOM_NS):
                eid = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
                if not eid:
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
                        published_at=(entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip(),
                    )
                )
            return items
        except Exception:
            return []


ADAPTERS = [HackerNewsAdapter(), ArxivAdapter()]
