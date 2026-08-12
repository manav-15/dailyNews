"""Provider-agnostic LLM access.

For the local demo there is no LLM endpoint/API key, so every method falls back
to a deterministic implementation. The LiteLLM-backed path is a single swap
point: set LLM_PROVIDER/LLM_MODEL/LLM_API_KEY and implement `_llm_*` with litellm.
"""
import re

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
        self.provider = config.LLM_PROVIDER
        self.model = config.LLM_MODEL
        self.api_key = config.LLM_API_KEY
        self.enabled = bool(self.provider and self.api_key)

    def parse_intent(self, raw_prompt: str) -> dict:
        """Free-text prompt -> {keywords, categories, sources, data_requests}."""
        if self.enabled:
            return self._llm_parse_intent(raw_prompt)
        return self._fallback_parse_intent(raw_prompt)

    def summarize_topic(self, topic: str, items: list) -> str:
        """One-paragraph synthesis of a topic's ranked items."""
        if self.enabled:
            return self._llm_summarize_topic(topic, items)
        if not items:
            return "No new stories matched today."
        n = len(items)
        titles = "; ".join((it.title or "")[:60] for it in items[:3])
        return f"{n} new {'story' if n == 1 else 'stories'} matched. Top: {titles}."

    def short_summary(self, item) -> str:
        """≤60-word per-item summary. Deterministic fallback uses title/body."""
        if self.enabled:
            return self._llm_short_summary(item)
        if item.title:
            return item.title
        body = (item.body or "").strip()
        return body[:140] if body else "(no text)"

    # --- deterministic fallback ---

    @staticmethod
    def _fallback_parse_intent(raw_prompt: str) -> dict:
        words = re.findall(r"[a-z0-9]+", raw_prompt.lower())
        keywords = [w for w in words if w not in STOPWORDS][:10] or words[:10]
        cats = sorted({c for c, kws in CATEGORY_KEYWORDS.items() if any(k in kw or kw in k for kw in keywords for k in kws)})
        return {
            "keywords": keywords,
            "categories": cats,
            "sources": list(config.DEFAULT_SOURCES),
            "data_requests": [],
        }

    # --- LLM hooks (LiteLLM swap point) ---

    def _llm_parse_intent(self, raw_prompt: str) -> dict:
        raise NotImplementedError("LiteLLM intent parsing not wired; set it in llm.py")

    def _llm_summarize_topic(self, topic: str, items: list) -> str:
        raise NotImplementedError("LiteLLM topic summary not wired; set it in llm.py")

    def _llm_short_summary(self, item) -> str:
        raise NotImplementedError("LiteLLM item summary not wired; set it in llm.py")


llm = LLMService()
