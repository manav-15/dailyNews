# DailyNews Design Specification

This is the design source of truth for agents working on the DailyNews mobile interface. It is derived from the current API payload and `mobile/App.tsx`. Use it before modifying UI, content hierarchy, or visual tokens.

The supported directions are **Morning Paper** and **Signal Room**. Choose one direction for an implemented screen; do not mix their visual systems.

## Product model

DailyNews is a personal daily digest. A user follows multiple free-form topics. A refresh creates one digest per day, ordered by the user's topic monitors. Each topic can have zero or more matched stories; the current backend caps a topic at `MAX_ITEMS_PER_TOPIC`, which defaults to **8**. The intended editorial density is 5–6 stories when enough matching stories exist.

Do not fabricate content or derive unsupported scores, trend arrows, reading times, categories, images, or cross-topic summaries in the client.

## Current API contract

`GET /digest/today` and `POST /refresh` return the following shape. Treat all fields marked optional as genuinely optional: the app must remain useful when they are absent.

```ts
type Digest = {
  date: string;                    // YYYY-MM-DD
  generated_at?: string;           // ISO date-time
  topics: DigestTopic[];
};

type DigestTopic = {
  topic: string;                   // user's original topic prompt
  summary?: string;                // LLM editorial synthesis, 1–2 sentences
  items: DigestItem[];             // 0–8 currently; visually optimize 5–6
};

type DigestItem = {
  id: string;
  source: string;
  title?: string;
  short?: string;                  // LLM item summary, target maximum 60 words
  long?: string;                   // source body or title fallback; do not show in feed
  url?: string;                    // external source URL
  author?: string;
  published_at?: string;           // ISO date-time when supplied by source
  score?: number;                  // internal relevance score
};
```

### Content semantics

- `topic.summary` is a topic-level synthesis, not an article. Render it once above that topic’s stories and never make it a link.
- `item.title` is the article headline. It is optional in the API, so use `item.short` only as a fallback label when it is missing.
- `item.short` is the story-level summary. It is generated for every item when the LLM succeeds; the fallback may equal `title`. Show it below the headline only when it is non-empty and differs from the displayed headline.
- `item.long` is preserved source text for future detail views. Do not place it in the digest feed.
- `source` is the required attribution. `author`, `published_at`, and `score` are supporting metadata, not editorial hierarchy.
- `url` can be absent. Make the row pressable only when it exists. Do not show an external-link affordance when no URL exists.
- `score` is an internal keyword-overlap ranking input. Do not label it “importance,” “quality,” or a user-facing score. Omit it in both directions unless the product later defines a meaningful interpretation.

## Shared content and interaction requirements

### Digest home

1. Show the product name and `generated_at` when present; otherwise say “Your daily briefing.”
2. Keep topic management available, but subordinate it to reading: `Follow a topic` opens the existing topic input; removing a topic requires an explicit remove affordance rather than tapping its reading navigation chip.
3. Render topic sections in the order returned by `digest.topics`.
4. Each topic section shows: topic name, story count, optional topic synthesis, then all returned story rows.
5. A six-story topic should fit naturally in the feed. For 7–8 returned items, render all items without truncation unless an explicit “Show all” interaction is designed and implemented.
6. For zero items, show the topic name and its synthesis/fallback message, followed by “No new matching stories today.” Do not render an empty card or an inactive link list.

### StoryRow component

The complete row is the reading unit and has this order:

1. Headline: `title`, falling back to `short`, then `Untitled story`.
2. Short summary: `short`, only when distinct from the rendered headline.
3. Attribution: `source`, optional `author`, and optional formatted `published_at`.
4. External-link icon/label only if `url` is present.

Rows must have a minimum 44px tap target. If `url` exists, the entire row opens it. If unavailable, render the row as static content with no misleading pressed state. Never add a nested `Read` button: it fragments an already clear target.

### Typography and accessibility

- Body and summary text must remain readable at system text scaling.
- Support long topic prompts, long headlines, and missing summaries without clipping.
- Preserve visible focus/pressed feedback and sufficient contrast.
- Editorial serif is reserved for topic-level hierarchy; all interactive text, metadata, and long-form summaries use the UI sans serif.

## Direction A — Morning Paper (recommended default)

### Intent

A warm personal front page. This is the best all-topics default: a reader can scan each followed topic’s editorial synthesis and six linked stories in one calm vertical flow.

### Screen structure

```text
DailyNews                                      Thu, Aug 14
Updated 08:15

Follow a topic                                 Refresh briefing

AI & Computing · 6 stories
One-to-two sentence topic synthesis.
------------------------------------------------
Article headline                              ↗
Short item summary, when different from title.
Reuters · Author · Aug 14
------------------------------------------------
... remaining stories

India · 5 stories
...
```

### Tokens

| Token | Value | Use |
|---|---|---|
| `bg` | `#F7F1E8` | Main canvas |
| `surface` | `#FFFAF5` | Composer / optional small control surface |
| `ink` | `#2C2824` | Primary text |
| `muted` | `#6A5E55` | Summary and metadata |
| `line` | `#DCCFC2` | Story separators |
| `accent` | `#BD5137` | Primary action, selected topic, topical rule |
| `titleFont` | `Newsreader`, fallback `Georgia` | Masthead and topic headings |
| `uiFont` | `DM Sans`, fallback system sans | Controls, stories, metadata |

### Rules

- Use whitespace and thin separators to group content. Avoid cards around every story and avoid shadows.
- The topic name and count lead the section. The synthesis follows immediately; story rows are subordinate evidence.
- Use the accent sparingly. It must not become a second text color for every source or headline.
- Keep all stories visible in the vertical feed. A horizontal topic chip rail may jump to sections, but it must not hide topics.

## Direction B — Signal Room

### Intent

A warm, focused intelligence terminal for readers who want a concise interpretation before the source list. It uses the existing `summary` as the editorial signal and the linked stories as evidence.

### Screen structure

```text
SIGNAL / 08.14                                  Updated 08:15

[ AI & Computing ] [ India ] [ Climate ]

AI & Computing · 6 signals
What matters today
One-to-two sentence topic synthesis.

Evidence · 6 stories
------------------------------------------------
Article headline                              ↗
Short item summary, when different from title.
Reuters · Author · Aug 14
------------------------------------------------
... remaining stories
```

### Tokens

| Token | Value | Use |
|---|---|---|
| `bg` | `#25221F` | Main canvas |
| `ink` | `#E9DEC8` | Primary text |
| `muted` | `#B7AA9C` | Summary and metadata |
| `line` | `#70675B` | Story separators |
| `signal` | `#A8C8B1` | Section labels and restrained semantic emphasis |
| `accent` | `#D79C45` | Selected topic chip and primary action |
| `titleFont` | `Source Serif 4`, fallback `Georgia` | Topic and “What matters” headings |
| `uiFont` | `IBM Plex Sans`, fallback system sans | Controls, stories, metadata |

### Rules

- Do not claim “What changed” or “Why it matters” as separate facts: the existing payload only provides one synthesis. Label the block `What matters today` unless backend data is added.
- `signal` is meaningful emphasis only—section labels or selected key phrasing—not decoration.
- Do not add charts, trend arrows, confidence scores, or an analyst dashboard without reliable additional data.
- In all-topics mode, stack topic sections. In focus mode, topic chips navigate between topic sections without changing the payload or order.

## Implementation guardrails for agents

1. Read this file and inspect the actual types in `mobile/App.tsx` before a visual change.
2. Keep API field names and topic-sync behavior unchanged unless the task explicitly includes backend work.
3. Maintain the `short !== title` duplicate-suppression behavior when implementing the new StoryRow.
4. Do not assume a URL, author, date, summary, or title exists.
5. Do not use `long` or `score` in the list UI.
6. Verify these cases: no digest; no topics; a topic with 0, 1, 5, 6, and 8 items; missing `short`; `short === title`; missing `url`; long topic/headline; small screen.

