"""The daily digest pipeline: collect -> match -> rank -> summarize -> store."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

import config
from adapters import ADAPTERS, Item
from llm import llm
from models import Digest, Item as ItemModel, Monitor, User


def relevance_score(item: Item, monitor: Monitor) -> int:
    """Keyword-overlap score (embeddings/LLM gate are the production upgrade)."""
    text = f"{item.title or ''} {item.body or ''}".lower()
    keywords = monitor.keywords or []
    return sum(1 for kw in keywords if kw and kw.lower() in text)


def _build_topic(monitor: Monitor, items: list[Item]) -> dict:
    result = llm.summarize_topic(monitor.raw_prompt, items)
    shorts = result.get("shorts", {})
    return {
        "topic": monitor.raw_prompt,
        "keywords": monitor.keywords or [],
        "summary": result.get("summary", ""),
        "items": [
            {
                "id": f"{it.source}:{it.source_id}",
                "source": it.source,
                "title": it.title,
                "short": shorts.get(f"{it.source}:{it.source_id}") or it.title,
                "long": it.body or it.title,
                "url": it.url,
                "author": it.author,
                "published_at": it.published_at,
                "score": it.score,
            }
            for it in items
        ],
    }


def run_pipeline(user_id: int, db: Session) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError(f"unknown user {user_id}")

    monitors = db.query(Monitor).filter(Monitor.user_id == user_id).all()
    today = datetime.now(timezone.utc).date().isoformat()

    # Collect + dedupe across sources.
    collected: dict[str, Item] = {}
    for monitor in monitors:
        keywords = monitor.keywords or monitor.raw_prompt.split()
        for adapter in ADAPTERS:
            for item in adapter.fetch(keywords):
                collected[f"{item.source}:{item.source_id}"] = item

    # Upsert items into the shared cache.
    for item in collected.values():
        exists = (
            db.query(ItemModel)
            .filter(ItemModel.source == item.source, ItemModel.source_id == item.source_id)
            .first()
        )
        if exists is None:
            db.add(
                ItemModel(
                    source=item.source,
                    source_id=item.source_id,
                    url=item.url,
                    title=item.title,
                    body=item.body,
                    author=item.author,
                    published_at=item.published_at,
                    score=item.score,
                )
            )
    db.commit()

    # Rank per monitor and assemble the digest.
    topics = []
    for monitor in monitors:
        scored = [(relevance_score(it, monitor), it) for it in collected.values() if relevance_score(it, monitor) > 0]
        scored.sort(key=lambda pair: (-pair[0], pair[1].published_at or ""))
        top = [it for _, it in scored[: config.MAX_ITEMS_PER_TOPIC]]
        topics.append(_build_topic(monitor, top))

    content = {
        "date": today,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topics": topics,
    }

    digest = db.query(Digest).filter(Digest.user_id == user_id, Digest.date == today).first()
    if digest is None:
        db.add(Digest(user_id=user_id, date=today, content=content))
    else:
        digest.content = content
    db.commit()
    return content
