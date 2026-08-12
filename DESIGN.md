# Daily Digest — Design System

> Category: News & Media (mobile)
> Inshorts-style daily news digest. Editorial, scannable, calm. Dark-first, single-accent.

## 1. Visual Theme & Atmosphere

A calm, editorial reading surface. The page recedes so stories carry the weight: a deep near-black canvas, hairline borders instead of shadows, and one restrained blue accent reserved for actions and selection. Density is moderate — a topic reads as a "section" (synthesis paragraph up top, item rows below), never a wall of identical cards. Content is the hierarchy; chrome is quiet.

**Key characteristics:**
- Dark-first: deep page background with two stepped surface layers.
- Hairline separators (`1px`) do the layering; no heavy shadows, no gradients.
- One accent (`#4f8cff`) for the primary action, focus, and tappable affordances — used sparingly.
- Generous vertical rhythm: sections breathe, items are separated by hairline, not by box borders.
- Rounded corners kept small (10–12px) and consistent.

## 2. Color Palette & Roles

| Token | Value | Role |
|---|---|---|
| `bg` | `#0b0d10` | Page background |
| `surface` | `#14171c` | Topic card surface |
| `surfaceAlt` | `#1a1e24` | Input / chip / elevated surface |
| `border` | `#23272f` | Hairline separators, card outline |
| `text` | `#e8ebef` | Primary text (titles, summaries) |
| `textMuted` | `#9aa3ad` | Secondary text (short summaries) |
| `textFaint` | `#6b7480` | Metadata (source · author · time) |
| `accent` | `#4f8cff` | Primary action, selection, links |
| `accentText` | `#7ea9ff` | On-dark accent text / topic names |
| `danger` | `#ff6b6b` | Error state |

## 3. Typography Rules

| Role | Size | Weight | Line Height | Use |
|---|---|---|---|---|
| App title | 26 | 700 | 32 | Header brand |
| Topic title | 17 | 700 | 24 | Topic name in card |
| Item title | 15 | 600 | 21 | Story headline |
| Body / summary | 14 | 400 | 21 | Topic synthesis + short summaries |
| Meta | 12 | 400 | 16 | source · author · score · time |
| Button | 15 | 600 | 20 | Action labels |

- System font stack (SF Pro on iOS, Roboto on Android).
- Letter spacing: 0 for body; tight (`-0.3`) only on the app title.

## 4. Spacing & Layout

- Page horizontal padding: `20px`.
- Section vertical gap: `24px`.
- Card padding: `16px`, radius `12px`.
- Item gap: `12px`, separated by hairline (`1px #23272f`) — no per-item boxes.
- Control row gap: `8px`.

## 5. Components

- **Header** — app title + muted date/subtitle, left-aligned.
- **Topic composer** — single input row (surfaceAlt, radius 10) + primary "Add" button; topic chips wrap below.
- **Topic chip** — `surfaceAlt`, radius 16, small type; removable (`×`).
- **Primary button** — accent fill, radius 10, full width on the refresh action.
- **Topic card** — `surface`, radius 12, hairline outline; topic title, synthesis paragraph, then item rows.
- **Item row** — headline (item title), meta line (source · author · score), short summary; whole row tappable (opens URL).

## 6. Do / Don't

- Do: hairline separators, one accent, scannable hierarchy, muted metadata.
- Don't: gradients, heavy shadows, over-rounded cards, stock "glass" effects, more than one accent, text on low-contrast surfaces.
