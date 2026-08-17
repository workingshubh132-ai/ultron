---
tags: [ultron, index]
---

# Ultron — Memory Vault

This folder is Ultron's persistent memory. Open it as an Obsidian vault (Obsidian → Open folder as vault → `memory-vault/`) if you want to browse/edit it with a nice UI — the files are plain markdown either way, so Claude Code and any editor can read/write them directly without Obsidian running.

## Structure

- [[Daily]] — one note per day, auto-appended by a `Stop` hook every time a Claude Code session ends in this project, and by the voice loop after each exchange. This is the raw activity log.
- [[Projects]] — one note per project Ultron helps with: current state, decisions made, what's next. Ultron updates these itself when something changes.
- [[People]] — notes on people you work with, so Ultron doesn't need to be re-told who someone is.
- [[Preferences]] — standing preferences and rules ("always deploy to staging first", "never message the team after 9pm"). Ultron checks this before acting on anything ambiguous.

## How it gets written

1. **Automatically** — every Claude Code session run from `local/` ends by appending a one-line summary to today's daily note (see `.claude/hooks/log_session.py` + `.claude/settings.json`).
2. **By Ultron itself** — `CLAUDE.md` in `local/` instructs it to update `Projects/`, `People/`, and `Preferences/` notes directly when something worth remembering happens, using `[[wikilinks]]` to connect related notes.
3. **By the voice loop** — each spoken exchange gets appended to the daily note too (see `voice/vault.py`).

There's nothing to configure to make this work beyond pointing everything at this folder — see `local/README.md`.
