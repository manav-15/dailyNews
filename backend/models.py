"""SQLAlchemy ORM models."""
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, Integer, String, Text, UniqueConstraint

from db import Base


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    timezone = Column(String, default="UTC")


class Monitor(Base):
    """A parsed topic/prompt subscription for a user."""

    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    raw_prompt = Column(Text, nullable=False)
    keywords = Column(JSON, default=list)
    categories = Column(JSON, default=list)
    sources = Column(JSON, default=list)
    data_requests = Column(JSON, default=list)
    created_at = Column(String, default=now_iso)


class Item(Base):
    """Deduped, normalized content item from a source adapter."""

    __tablename__ = "items"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_item_source"),)

    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    url = Column(String)
    title = Column(String)
    body = Column(Text)
    author = Column(String)
    published_at = Column(String)
    score = Column(Integer, default=0)


class Digest(Base):
    """One generated digest per user per day."""

    __tablename__ = "digests"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_digest_user_date"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    content = Column(JSON, nullable=False)
    created_at = Column(String, default=now_iso)
