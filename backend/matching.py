"""Deterministic item-matching for the digest pipeline.

Tier 1 of the retrieval & matching roadmap (docs/plan.md §"Retrieval &
matching"): token-boundary lexical matching weighted by BM25, plus an
exact-phrase bonus for multi-word keywords. Replaces the v1 substring-overlap
scorer.

Higher tiers (dense embeddings + hybrid, NER/entity resolution, LLM y/n gate)
are intended to plug in behind the same ``BM25.score`` interface so
``pipeline.py`` keeps its shape. Matching never invents content — it only
orders items that a source adapter already fetched.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass, field

from llm import STOPWORDS

# Bonus added per exact multi-word keyword phrase found verbatim in the item
# text. Comparable to a single mid-frequency BM25 term hit; a whole phrase
# ("oracle corp") is a stronger signal than its words ("oracle", "corp").
PHRASE_BONUS = 2.0

# BM25 free parameters. k1 controls term-frequency saturation; b controls
# document-length normalization (b=1 full, b=0 none).
K1 = 1.2
B = 0.75

# Word-boundary tokenizer: lowercase runs of letters/digits. Boundaries (not
# substrings) are what stop "ai" from matching "said"/"chair".
_WORD = re.compile(r"[a-z0-9]+")


@dataclass
class Query:
    """A monitor's keywords decomposed into matchable units."""

    terms: list[str] = field(default_factory=list)   # content words
    phrases: list[str] = field(default_factory=list)  # normalized multi-word phrases


def tokenize(text: str) -> list[str]:
    """Lowercase, split on word boundaries, drop stopwords."""
    return [w for w in _WORD.findall((text or "").lower()) if w not in STOPWORDS]


def build_query(keywords) -> Query:
    """Expand raw monitor keywords (words or phrases) into a Query.

    Each keyword contributes its content words (for term matching) and, if it
    is a phrase, the whole phrase (for exact-phrase matching). This is what
    lets a phrase keyword like "oracle corp" match both "Oracle" (via the word
    "oracle") and "Oracle Corporation" (via the phrase "oracle corp").
    """
    terms: list[str] = []
    phrases: list[str] = []
    for kw in keywords or []:
        kw = (kw or "").strip().lower()
        if not kw:
            continue
        words = _WORD.findall(kw)
        terms.extend(w for w in words if w not in STOPWORDS)
        if len(words) > 1:
            phrases.append(" ".join(words))
    return Query(_dedupe(terms), _dedupe(phrases))


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


class BM25:
    """BM25 scorer over a pre-tokenized corpus.

    Construct once per pipeline run from the shared item cache (stable document
    frequencies); then ``score`` re-ranks candidate items. Deterministic, no
    model, no network.
    """

    def __init__(self, corpus: list[list[str]]):
        self.n = len(corpus)
        self.avgdl = (sum(len(d) for d in corpus) / self.n) if self.n else 0.0
        self._df: Counter = Counter()
        for doc in corpus:
            self._df.update(set(doc))

    def idf(self, term: str) -> float:
        # Smoothed IDF (Robertson et al.). Terms absent from the cache score
        # high (rare -> discriminating); terms in every document approach zero.
        df = self._df.get(term, 0)
        return math.log(1.0 + (self.n - df + 0.5) / (df + 0.5))

    def score(self, query: Query, doc_tokens: list[str], raw_text: str = "") -> float:
        """Score a candidate item's tokens against a monitor query.

        ``doc_tokens`` and ``raw_text`` describe the SAME item: tokens for the
        BM25 term match, raw text for the exact-phrase check.
        """
        if not doc_tokens:
            return 0.0
        tf = Counter(doc_tokens)
        doc_len = len(doc_tokens)
        length_norm = 1.0 - B + B * (doc_len / self.avgdl if self.avgdl else 1.0)

        total = 0.0
        for term in query.terms:
            f = tf.get(term, 0)
            if f == 0:
                continue
            total += self.idf(term) * (f * (K1 + 1.0)) / (f + K1 * length_norm)

        raw = (raw_text or "").lower()
        total += PHRASE_BONUS * sum(1 for p in query.phrases if p in raw)
        return total
