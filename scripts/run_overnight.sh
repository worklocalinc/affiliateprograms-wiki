#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT/../logs"
mkdir -p "$LOG_DIR"

source "$HOME/ai-shared/secrets/.env" >/dev/null 2>&1 || true

# Ensure keys are exported for child processes (many entries in .env are not exported by default).
if [[ -n "${BRAVE_API_KEY:-}" ]]; then export BRAVE_API_KEY; fi
if [[ -n "${GOOGLE_PSE_API_KEY:-}" ]]; then export GOOGLE_PSE_API_KEY; fi

# Always run against the dedicated Affiliate Wiki DB (avoid accidental use of other project DBs).
# Does not print the URL.
DATABASE_URL="$(/home/skynet/google-cloud-sdk/bin/gcloud secrets versions access latest --secret=database_url_affiliate_wiki --project superapp-466313)"
export DATABASE_URL

# Google PSE fallback for discovery when Brave is rate-limited.
# Does not print keys/ids.
if [[ -z "${GOOGLE_PSE_API_KEY:-}" ]]; then
  GOOGLE_PSE_API_KEY="$(
    /home/skynet/google-cloud-sdk/bin/gcloud secrets versions access latest \
      --secret=GOOGLE_PSE_API_KEY \
      --project superapp-466313 2>/dev/null || true
  )"
  if [[ -n "${GOOGLE_PSE_API_KEY:-}" ]]; then export GOOGLE_PSE_API_KEY; fi
fi
if [[ -z "${GOOGLE_PSE_ENGINE_ID:-}" ]]; then
  GOOGLE_PSE_ENGINE_ID="$(
    /home/skynet/google-cloud-sdk/bin/gcloud secrets versions access latest \
      --secret=GOOGLE_PSE_ENGINE_ID \
      --project superapp-466313 2>/dev/null || true
  )"
  if [[ -n "${GOOGLE_PSE_ENGINE_ID:-}" ]]; then export GOOGLE_PSE_ENGINE_ID; fi
fi

if [[ -z "${BRAVE_API_KEY:-}" ]]; then
  echo "Missing BRAVE_API_KEY (set in ~/ai-shared/secrets/.env)" >&2
  exit 2
fi

LOG="$LOG_DIR/overnight-$(date +%F).log"
PIDFILE="$LOG_DIR/overnight.pid"

nohup "$HOME/affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python" \
  "$HOME/affiliateprograms-wiki/scripts/affiliate_wiki/overnight_runner.py" \
  >>"$LOG" 2>&1 &

echo $! > "$PIDFILE"
echo "Started: pid=$(cat "$PIDFILE") log=$LOG"
