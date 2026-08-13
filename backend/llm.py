"""Provider-agnostic LLM access.

Talks to any OpenAI-compatible `/chat/completions` endpoint (DeepSeek, OpenAI,
Ollama, vLLM, Groq, …) via httpx. With no LLM_API_KEY, every method falls back
to a deterministic implementation so the pipeline still runs offline.
"""
import json
import re

import httpx

import config

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "about", "what", "whats", "is", "are", "was", "were", "be", "being", "been",
    "i", "you", "he", "she", "it", "we", "they", "my", "your", "me", "want", "would",
    "like", "know", "please", "tell", "news", "daily", "get", "give", "about", "some",
}

CATEGORY_KEYWORDS = {
    "technology": ["tech", "software", "ai", "ml", "cloud", "startup", "code", "programming", "llm", "database"],
    "finance": ["stock", "market", "price", "earnings", "investment", "money", "bank", "economy", "analyst"],
    "geopolitics": ["geopolitic", "war", "diplomacy", "election", "government", "policy", "sanction"],
    "science": ["science", "research", "physics", "space", "climate", "medical", "biology"],
}


class LLMService:
    def __init__(self):
        self.base_url = config.LLM_BASE_URL.rstrip("/")
        self.model = config.LLM_MODEL
        self.api_key = config.LLM_API_KEY

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _chat(self, messages: list[dict], json_mode: bool = False) -> str:
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "thinking": {"type": "disabled"},
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        r = httpx.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=90.0,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    # ---- public API ----

    def parse_intent(self, raw_prompt: str) -> dict:
        """Free-text prompt -> {keywords, categories, sources, data_requests}."""
        if self.enabled:
            try:
                return self._llm_parse_intent(raw_prompt)
            except Exception:
                pass
        return self._fallback_parse_intent(raw_prompt)

    def summarize_topic(self, topic: str, items: list) -> dict:
        """Return {"summary": str, "shorts": {item_id: str}} for a topic's items."""
        if self.enabled and items:
            try:
                return self._llm_summarize_topic(topic, items)
            except Exception:
                pass
        return self._fallback_summarize_topic(topic, items)

    # ---- LLM implementations ----

    def _llm_parse_intent(self, raw_prompt: str) -> dict:
        content = self._chat(
            [
                {
                    "role": "system",
                    "content": (
                        "Extract search keywords and categories from a news-topic prompt. "
                        'Return strict JSON: {"keywords": ["..."], "categories": ["..."]}. '
                        "keywords: lowercased, <=10, concrete search terms. "
                        "categories: a subset of technology, finance, geopolitics, science, business, ai."
                    ),
                },
                {"role": "user", "content": raw_prompt},
            ],
            json_mode=True,
        )
        data = json.loads(content)
        keywords = [str(k).lower().strip() for k in data.get("keywords", []) if k][:10]
        categories = [str(c).lower().strip() for c in data.get("categories", []) if c]
        if not keywords:
            keywords = self._fallback_parse_intent(raw_prompt)["keywords"]
        return {
            "keywords": keywords,
            "categories": categories,
            "sources": list(config.DEFAULT_SOURCES),
            "data_requests": [],
        }

    def _llm_summarize_topic(self, topic: str, items: list) -> dict:
        lines = []
        for it in items:
            item_id = f"{it.source}:{it.source_id}"
            body = (it.body or "").strip().replace("\n", " ")[:400]
            lines.append(f"ID: {item_id}\nTitle: {it.title}\nBody: {body}")
        items_text = "\n\n".join(lines)
        content = self._chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a news digest editor. Given a topic and a list of items, "
                        "write a one-to-two-sentence synthesis of the topic, and a short summary "
                        "(<=60 words) for EVERY item. Return strict JSON: "
                        '{"summary": "...", "items": [{"id": "<item id>", "short": "..."}]}. '
                        "Only use the provided items. Never invent facts, numbers, URLs, or sources."
                    ),
                },
                {"role": "user", "content": f"Topic: {topic}\n\nItems:\n{items_text}"},
            ],
            json_mode=True,
        )
        data = json.loads(content)
        shorts = {str(i.get("id")): (i.get("short") or "").strip() for i in data.get("items", [])}
        return {"summary": (data.get("summary") or "").strip(), "shorts": shorts}

    # ---- deterministic fallbacks ----

    @staticmethod
    def _fallback_parse_intent(raw_prompt: str) -> dict:
        words = re.findall(r"[a-z0-9]+", raw_prompt.lower())
        keywords = [w for w in words if w not in STOPWORDS][:10] or words[:10]
        cats = sorted(
            {c for c, kws in CATEGORY_KEYWORDS.items() if any(k in kw or kw in k for kw in keywords for k in kws)}
        )
        return {
            "keywords": keywords,
            "categories": cats,
            "sources": list(config.DEFAULT_SOURCES),
            "data_requests": [],
        }

    @staticmethod
    def _fallback_summarize_topic(topic: str, items: list) -> dict:
        if not items:
            return {"summary": "No new stories matched today.", "shorts": {}}
        n = len(items)
        titles = "; ".join((it.title or "")[:60] for it in items[:3])
        summary = f"{n} new {'story' if n == 1 else 'stories'} matched. Top: {titles}."
        shorts = {f"{it.source}:{it.source_id}": (it.title or "") for it in items}
        return {"summary": summary, "shorts": shorts}


llm = LLMService()
