#!/usr/bin/env bash
# Build a sideloadable Android APK via EAS Build (cloud).
set -euo pipefail

cd "$(dirname "$0")/../mobile"

# Ensure mobile/.env exists (source of EXPO_PUBLIC_API_URL / EXPO_PUBLIC_API_KEY).
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "Created mobile/.env from .env.example."
  else
    echo "ERROR: mobile/.env and .env.example are missing." >&2
    exit 1
  fi
fi

if ! grep -qE 'EXPO_PUBLIC_API_URL=https?://' .env; then
  echo "WARNING: EXPO_PUBLIC_API_URL is not set in mobile/.env." >&2
  echo "         The APK will fall back to localhost and won't reach the cloud backend." >&2
fi

if ! grep -qE 'EXPO_PUBLIC_API_KEY=.+' .env; then
  echo "WARNING: EXPO_PUBLIC_API_KEY is empty in mobile/.env." >&2
  echo "         The app will not send the X-API-Key header (backend will reject it)." >&2
fi

echo "Building preview APK via EAS Build…"
npx eas-cli build --platform android --profile preview "$@"
