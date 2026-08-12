---
name: learning-session
description: Conducts a research or learning session on any concept, technology, or topic, storing the discussion and final summary in the wiki.
---

# Learning Session Skill

This skill is triggered when the user wants to research or understand something — a concept, technology, framework, pattern, or any topic. The agent acts as a research partner, and the entire discussion plus a final synthesis is persisted in the wiki.

## Procedure

### 1. Establish the Topic

The agent MUST ask the user to state the learning topic explicitly. If the user already stated it in the trigger prompt, confirm it back:

> "Starting a learning session on: **<topic>**. I'll create a wiki entry at `llmwiki/wiki/learnings/<topic-slug>/`. Ready?"

### 2. Create the Topic Directory

```
llmwiki/wiki/learnings/<topic-slug>/
├── discussion.md    — The full Q&A/discussion transcript
├── summary.md       — Final condensed synthesis
└── references.md    — External links, papers, docs cited
```

- `<topic-slug>` is a kebab-case version of the topic (e.g., `kv-caching`, `react-server-components`, `mlx-inference-pipeline`).
- Create all three files. Start with a header and YAML frontmatter in each.

### 3. Conduct the Discussion

The agent engages in a research conversation:
- Answer the user's questions with depth and precision.
- **Show the answer in the chat first.** The user reads the answer before it gets archived.
- After showing the answer, **then** persist the Q&A pair to `discussion.md`. The write to disk is a background archival step — the conversation flows in chat.
- Cite sources: include links to official docs, papers, blog posts, or source code.
- Format each exchange in `discussion.md` as:

```markdown
### Q: <user question>

<agent answer with sources>
```


**IMPORTANT — How to persist each Q&A pair:**

- The first Q&A pair is written when you create the file via `write`. That's fine.
- For EVERY subsequent Q&A pair, you MUST **append** to `discussion.md` — NEVER use `write` again, because `write` replaces the entire file and previous Q&A pairs will be lost.
- To append: (1) `read` the file to get the current snapshot tag, then (2) use `edit` with `INS.TAIL:` and the body rows.
- Example of appending a new Q&A:
  ```
  edit:
    [llmwiki/wiki/learnings/<topic-slug>/discussion.md#<tag>]
    INS.TAIL:
    +### Q: <user question>
    +
    +**Answer:**
    +
    +...answer body...
  ```
- At the end of each answer in chat, ask: "More on this topic, or ready for the summary?"

### 4. Synthesize the Summary (After Session Ends Only)

**Do NOT write the summary until the user explicitly signals the session is over** (e.g., "ready for the summary", "that's enough", "wrap it up"). The summary is a post-session artifact, not something done mid-session. When the user gives the signal:


```markdown
---
title: <Topic> — Learning Summary
tags: [learning, <topic-tags>]
summary: <One-line synthesis>
---

# <Topic>

## Key Concepts
- <Concept 1>: <1-2 sentence explanation>
- <Concept 2>: ...

## Important Relationships
- <How concepts connect, trade-offs, dependencies>

## Takeaways
- <3-5 actionable or memorable conclusions>

## Sources
- <Link/source 1>
- ...
```

### 5. Cross-Reference and Index

- If the topic relates to existing wiki pages, add a `## See Also` section in `summary.md` with links.
- If the topic is relevant to the project (e.g., a technology we might use), add a note in `llmwiki/wiki/memory.md` under `## Learnings` summarizing the decision relevance.
- Append a log entry to `llmwiki/wiki/log.md`:
  ```
  ## [YYYY-MM-DD] learn | Learning session: <topic>.
  - Discussion, summary, and references stored in `wiki/learnings/<topic-slug>/`.
  ```
- Add the summary page to `llmwiki/wiki/index.md` under a `## Learnings` section (create if missing).

## Files Created
- `llmwiki/wiki/learnings/<topic-slug>/discussion.md` — Full Q&A transcript
- `llmwiki/wiki/learnings/<topic-slug>/summary.md` — Condensed synthesis
- `llmwiki/wiki/learnings/<topic-slug>/references.md` — External sources
- Updated: `llmwiki/wiki/log.md`, `llmwiki/wiki/memory.md`, `llmwiki/wiki/index.md`