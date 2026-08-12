---
title: Daily News Digest App — Learning Summary
tags: [learning, daily-news, mobile-app, digest, llm]
summary: Plan for a daily digest app: users submit free-text topics, a pipeline fetches from multiple sources, ranks by relevance, and an LLM produces a structured digest — provider-agnostic LLM access, embeddings-first relevance, and injected (never generated) facts.
---

# Daily News Digest App

## Key Concepts

- **Product**: mobile app where a user picks topics/free-text prompts and gets a daily digest from multiple sources (news, Hacker News, arXiv, later Twitter/Reddit). Inshorts-style UI — terse summary cards, tap to expand. App bears AI/hosting cost with per-user limits. V1 = one fixed user.
- **Core pipeline**: collect → match → rank + dedupe → summarize → deliver, run daily per user.
- **Normalized item schema**: every source adapter emits the same shape (`id, source, url, title, body, author, published_at, score, entities, tags`), so matching/summarizing/UI are source-agnostic.
- **Intent parser**: one-time LLM call (strict JSON schema) turning a free-text prompt into a stored "monitor" (categories, entities, keywords, embedding, sources, data_requests).
- **Entity resolver**: disambiguates named entities ("Oracle" company vs "oracle bones") and resolves to a stable ID + ticker (ORCL), enabling reliable NER matching + market-data lookup.
- **Relevance**: embeddings (pgvector) + cosine similarity = no per-item LLM call; an optional cheap y/n gate catches false positives. NER via spaCy/GLiNER.
- **Digest generation**: one LLM call per user/day → structured JSON (short ≤60-word + long per item). Structured output via function-calling / JSON-schema.
- **LLM roles**: intent parsing (one-time), relevance gate (optional), digest summarization (daily), judge (eval/guardrail).
- **LLM abstraction**: LiteLLM (one OpenAI-compatible interface over ~100 providers) + a thin `LLMService` mapping task → model, centralizing retries/parsing. Switch provider = edit config.
- **Evaluation**: golden eval set, precision@8 (relevance), BERTScore + LLM-judge faithfulness (summarization).
- **Mobile**: Expo (React Native) + TypeScript; Expo Go for testing; Android sideload APK; iOS preview via simulator, TestFlight later ($99/yr).
- **Dev vs prod**: Metro dev server + Fast Refresh streams JS (edit without rebuild); production bundles JS into the binary. Same code, different tooling.

## Important Relationships

- Intent parsing is **front-loaded** (subscription time); the daily job is **retrieval + vector math**, with summarization as the only recurring LLM call.
- Entity resolution is the bridge: it turns a fuzzy entity into a ticker/QID, unlocking both reliable matching and market-data lookup.
- The **hard rule** — "the LLM organizes, never invents" — is why stock price/analyst ratings are **injected structured facts**, not generated.
- The **shared item cache** is the cost lever: fetch + summarize once, dedupe across users, keeping an app-funded model viable.
- Expo's dev/prod split is the industry standard (Vite/Next, Flutter do the same); the application code never forks.

## Takeaways

1. Variable prompts work by decomposing them into structured monitors once, at add-time.
2. Keep the steady-state pipeline LLM-free until summarization (embeddings + NER).
3. Never trust an LLM with numbers, prices, URLs, or dates — inject them as facts.
4. Abstract LLM access behind LiteLLM + task→model config from day one.
5. Ship Android first (APK sideload); keep iOS at preview level until TestFlight is warranted.
6. Evaluate relevance with precision@8 on a labeled set; evaluate summaries with an LLM judge for faithfulness (offline).

## Sources

- React Native / Expo — https://expo.dev, https://reactnative.dev
- LiteLLM — https://github.com/BerriAI/litellm
- FastAPI — https://fastapi.tiangolo.com
- Hacker News Algolia API — https://hn.algolia.com/api
- arXiv API — https://arxiv.org/help/api
- pgvector — https://github.com/pgvector/pgvector
- TestFlight — https://developer.apple.com/testflight/
