"""Small helpers for reading/writing the Obsidian memory vault. Deliberately
tiny — Claude Code itself reads/writes richer notes via its normal file
tools per local/CLAUDE.md; this module only handles the raw daily-log
appends the voice loop needs to do outside of a Claude turn."""
import os
from datetime import datetime


def daily_note_path(vault_dir, when=None):
    when = when or datetime.now()
    daily_dir = os.path.join(vault_dir, "Daily")
    os.makedirs(daily_dir, exist_ok=True)
    return os.path.join(daily_dir, when.strftime("%Y-%m-%d") + ".md")


def append_voice_exchange(vault_dir, transcript, reply):
    now = datetime.now()
    path = daily_note_path(vault_dir, now)

    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(f"# {now.strftime('%Y-%m-%d')}\n\n")

    with open(path, "a") as f:
        f.write(f"- **{now.strftime('%H:%M')}** (voice) YOU: {transcript}\n")
        f.write(f"  ULTRON: {reply}\n")


def read_today(vault_dir):
    path = daily_note_path(vault_dir)
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        return f.read()
