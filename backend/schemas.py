"""Pydantic schemas for API request/response bodies."""
from typing import List, Optional

from pydantic import BaseModel


class TopicIn(BaseModel):
    raw_prompt: str


class TopicsIn(BaseModel):
    topics: List[TopicIn]


class MonitorOut(BaseModel):
    id: int
    raw_prompt: str
    keywords: List[str] = []
    categories: List[str] = []
    sources: List[str] = []

    class Config:
        from_attributes = True


class DigestItem(BaseModel):
    id: str
    source: str
    title: Optional[str] = None
    short: Optional[str] = None
    long: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None
    score: Optional[int] = None


class DigestTopic(BaseModel):
    topic: str
    summary: Optional[str] = None
    items: List[DigestItem] = []


class DigestOut(BaseModel):
    date: str
    generated_at: Optional[str] = None
    topics: List[DigestTopic] = []
