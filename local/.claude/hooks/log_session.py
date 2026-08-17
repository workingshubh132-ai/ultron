#!/usr/bin/env python3
"""Stop hook: appends a one-line summary of every Claude Code session run in
this project to today's daily note in the Obsidian vault, and pings the HUD
status server if it's running. Reads the hook payload Claude Code sends on
stdin (session_id, cwd, last_assistant_message, ...)."""
import json
import os
import sys
import urllib.request
from datetime import datetime

PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
VAULT_DAILY_DIR = os.path.join(PROJECT_DIR, "memory-vault", "Daily")
STATUS_SERVER_URL = os.environ.get("ULTRON_STATUS_URL", "http://127.0.0.1:8765")


def main():
    if os.environ.get("ULTRON_VOICE_TURN"):
        # voice/vault.py already writes a richer YOU/ULTRON entry for this turn
        return

    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    summary = (payload.get("last_assistant_message") or "").strip()
    if not summary:
        return

    now = datetime.now()
    os.makedirs(VAULT_DAILY_DIR, exist_ok=True)
    daily_path = os.path.join(VAULT_DAILY_DIR, now.strftime("%Y-%m-%d") + ".md")

    if not os.path.exists(daily_path):
        with open(daily_path, "w") as f:
            f.write(f"# {now.strftime('%Y-%m-%d')}\n\n")

    line = f"- **{now.strftime('%H:%M')}** — {summary}\n"
    with open(daily_path, "a") as f:
        f.write(line)

    # Best-effort: tell the HUD something just happened. The HUD/voice loop
    # may not be running (e.g. plain interactive `claude` in this project),
    # so failures here are silently ignored.
    try:
        req = urllib.request.Request(
            f"{STATUS_SERVER_URL}/event",
            data=json.dumps({"type": "session_end", "summary": summary}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=0.5)
    except Exception:
        pass


if __name__ == "__main__":
    main()
