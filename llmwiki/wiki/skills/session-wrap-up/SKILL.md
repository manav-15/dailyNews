---
name: session-wrap-up
description: Wraps up a work session by compiling literal user prompts, summarizing accomplishments, and capturing next steps in the wiki.
---

# Session Wrap-Up Skill

This skill is triggered when the user indicates a session is ending. The agent MUST execute every step below before yielding.

## Procedure

### 1. Compile Literal Prompts

Collect every **literal user prompt** from the current session — the exact text the user typed, unparaphrased and unsummarized. Do not include system messages, agent responses, or tool outputs.

Store them in a timestamped file:

```
llmwiki/wiki/sessions/<YYYY-MM-DD>-<slug>.md
```

The slug is a 2-4 word kebab-case summary of the session's main topic (e.g., `hld-creation`, `backend-bootstrap`, `provider-abstraction`).

File template:

```markdown
---
title: Session <YYYY-MM-DD> — <Title>
tags: [session, <topic-tags>]
summary: <One-line session summary>
---

# Session: <YYYY-MM-DD> — <Title>

## Prompts

1. <literal prompt 1>
2. <literal prompt 2>
...
```

- Number prompts in chronological order (1-based).
- Preserve the exact text — do not edit, rephrase, or truncate.
- If a prompt is very long (>500 words), include it verbatim but note the length.

### 2. Summarize Accomplishments

Append a `## Summary` section listing what was done this session — deliverables created, decisions made, files changed. Keep it factual and terse (no motivational language).

### 3. Identify Next Steps

Append a `## Potential Next Steps` section with 2-5 concrete, actionable next steps derived from the session's work. Each step should be one sentence describing a specific increment.

### 4. Ask for User Input

Append a `## User Next Steps` section with the placeholder:

```markdown
_(Ask the user: "Do you have a list of next action items planned? I'll record them here." — then fill in their response.)_
```

The agent MUST actually ask the user this question and record the answer before finalizing.

### 5. Update Wiki

- Append a wrap-up entry to `llmwiki/wiki/log.md`:
  ```
  ## [YYYY-MM-DD] wrap-up | Session wrap-up: <slug>.
  - Prompts, summary, and next steps stored in `wiki/sessions/<filename>.md`.
  ```
- Update `llmwiki/wiki/context.md` to clear the current session state and note the wrap-up.
- Add the session file to `llmwiki/wiki/index.md` under a `## Sessions` section (create the section if it doesn't exist).

## Files Created
- `llmwiki/wiki/sessions/<YYYY-MM-DD>-<slug>.md` — compiled prompts, summary, next steps
- Updated: `llmwiki/wiki/log.md`, `llmwiki/wiki/context.md`, `llmwiki/wiki/index.md`