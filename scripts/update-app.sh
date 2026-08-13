#!/usr/bin/env bash
# Push an OTA (JS-only) update to the installed app via EAS Update.
# Usage: ./scripts/update-app.sh "changed the header"
set -euo pipefail

cd "$(dirname "$0")/../mobile"

MSG="${1:-update}"
echo "Publishing OTA update to the 'preview' channel…"
npx eas-cli update --channel preview --message "$MSG"
