# Daily News Digest

A mobile app that generates a **daily digest** of news/content from multiple sources based on user-selected topics or free-text prompts. Inshorts-style UI: a terse summary per topic, tap to expand into detail.

## Structure

- `backend/` — FastAPI + SQLAlchemy (SQLite) + the digest pipeline (collect → match → rank → summarize → store).
- `mobile/` — Expo (React Native) app.
- `docs/plan.md` — detailed v1 plan.
- `llmwiki/` — knowledge base + the planning learning session.

## Prerequisites

- Python 3.11+ with [`uv`](https://docs.astral.sh/uv/)
- Node 18+ with npm
- (optional) Android SDK/emulator for the emulator demo

## Backend

```bash
cd backend
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

Endpoints:

| Method | Path | Purpose |
|---|---|---|
| `PUT` | `/topics` | set topics: `{"topics":[{"raw_prompt":"oracle cloud"}]}` |
| `POST` | `/refresh` | **trigger digest generation on demand** |
| `GET` | `/digest/today` | today's digest |
| `GET` | `/digest/{date}` | a past digest |
| `GET` | `/health` | liveness |

## Mobile app

```bash
cd mobile
npm install
npm run web                 # browser preview
# or:
npx expo start              # then press `a` (Android) / `i` (iOS) / `w` (web)
```

- Android emulator reaches the backend at `http://10.0.2.2:8000`; iOS simulator/web use `http://localhost:8000`. Change `API_BASE` in `mobile/App.tsx` for other hosts (e.g. a physical device on your LAN).
- The app has a **Refresh digest** button that calls `POST /refresh`, so you can trigger the pipeline on demand during development.

## Notes

- **LLM is abstracted** behind `backend/llm.py` (`LLMService`). With no `LLM_API_KEY` set it uses a deterministic fallback (keyword intent parsing + extractive summaries); set `LLM_PROVIDER`/`LLM_MODEL`/`LLM_API_KEY` to wire a real model (LiteLLM hook).
- Storage defaults to SQLite; set `DATABASE_URL` to use Postgres (pgvector for embeddings later).
- Sources: Hacker News (Algolia) + arXiv, both free/no-key.
