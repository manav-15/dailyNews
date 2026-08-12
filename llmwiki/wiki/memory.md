---
title: Memory
tags: [meta, memory, learnings]
summary: A compiled record of long-term agent memories and persistent takeaways.
---

# Agent Memory

This file acts as a persistent memory bank where visiting AI agents document long-term learnings, persistent takeaways, and critical knowledge compiled across sessions.

## Long-term Learnings
- Initial setup completed.

## Learnings — Daily News Digest App
- Variable user prompts are decomposed once at subscribe-time into structured "monitors" (entities, keywords, categories, embedding); the steady-state daily job is LLM-free until summarization.
- Never let the LLM generate facts (prices, ratings, URLs) — inject structured facts and constrain it to "organize, don't invent."
- Use LiteLLM + a task→model `LLMService` for provider-agnostic LLM access.
- Ship Android first (sideload APK); preview iOS via simulator/Expo Go; TestFlight later ($99/yr).
