#!/usr/bin/env bash
# Starts the Ultron local stack: HUD server, then the voice loop in the
# foreground. Ctrl+C stops both.
set -euo pipefail

LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$LOCAL_DIR"

if ! command -v claude >/dev/null 2>&1; then
  echo "claude CLI not found on PATH. Install Claude Code first: https://claude.com/claude-code" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found on PATH." >&2
  exit 1
fi

if [ -f .env ]; then
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
fi

PORT="${ULTRON_HUD_PORT:-8765}"

echo "Starting HUD server on http://127.0.0.1:${PORT} ..."
python3 hud/server.py &
HUD_PID=$!

cleanup() {
  echo ""
  echo "Shutting down..."
  kill "$HUD_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 1

if command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:${PORT}" || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:${PORT}" || true
else
  echo "Open http://127.0.0.1:${PORT} in a browser to see the HUD."
fi

echo "Starting voice loop..."
python3 voice/ultron_voice.py
