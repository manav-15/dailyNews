# Deploying Daily Digest

Two pieces: the **backend on Railway** (Postgres) and the **Android APK** you sideload.

## 1. Backend → Railway

1. **Railway** → **New Project** → **Deploy from GitHub repo** → select `dailyNews`.
2. Point the service at the backend: set **Root Directory** to `backend/` (Settings → Root Directory). `backend/railway.json` also declares the Dockerfile + `/health` healthcheck.
3. Add the **PostgreSQL** plugin — Railway injects `DATABASE_URL` automatically (the app already reads it; SQLite → Postgres is a free swap).
4. Add **Variables**:
   | Var | Value |
   |---|---|
   | `API_KEY` | a random secret — `openssl rand -hex 32` |
   | `LLM_API_KEY` | your DeepSeek key |
   | `LLM_MODEL` | `deepseek-v4-flash` |
   | `LLM_BASE_URL` | `https://api.deepseek.com` (default, optional) |
5. **Deploy.** Copy the public URL: `https://<service>.up.railway.app`.

Smoke-test: `curl https://<service>.up.railway.app/health` → `{"status":"ok"}`.

## 2. Build the Android APK

```bash
./scripts/build-apk.sh
```

This ensures `mobile/.env` exists and runs EAS Build with the `preview` profile (produces a plain **APK**).

Prereqs (one-time):
```bash
npm i -g eas-cli
eas login          # free Expo account
```

Set these in `mobile/.env` before building:

```bash
EXPO_PUBLIC_API_URL=https://<service>.up.railway.app
EXPO_PUBLIC_API_KEY=<same API_KEY as the backend>
```

> Leave `EXPO_PUBLIC_API_URL` empty to fall back to local dev (`10.0.2.2:8000` on the emulator).

### Local build (alternative, no Expo account)

Requires the Android SDK (already set up on this machine):

```bash
cd mobile
npx expo prebuild -p android
npx expo run:android --variant release
# APK: android/app/build/outputs/apk/release/app-release.apk
```

## 3. Sideload the APK

1. Get the `.apk` onto your phone (EAS gives a download link; or AirDrop / Drive / USB for a local build).
2. Open it → allow **"Install unknown apps"** for the source app.
3. Open **Daily Digest** — it talks to the Railway URL; the **Refresh digest** button triggers generation on demand (no cron yet).

## Environment reference

| Var | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend (Railway auto) | Postgres connection |
| `API_KEY` | backend | shared auth key (`X-API-Key`) |
| `LLM_API_KEY` / `LLM_MODEL` / `LLM_BASE_URL` | backend | DeepSeek / OpenAI-compatible LLM |
| `EXPO_PUBLIC_API_URL` | mobile build | backend URL |
| `EXPO_PUBLIC_API_KEY` | mobile build | must match backend `API_KEY` |

## Security notes

- The key embedded in the APK is **extractable** — it stops casual abuse and protects your LLM spend, but not a determined attacker. Move to real user auth for a multi-user product.
- Never commit `API_KEY` or `.env` — both are gitignored (`.env` files).
