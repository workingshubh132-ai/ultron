---
tags: [project]
status: active
---

# Example - ultron-os

This is a placeholder showing the format Ultron expects for a project note. Delete it once you've added your own, or keep it as a template.

## State

Scaffolding the local Ultron stack (this repo, `local/`): Claude Code engine, this vault, the voice loop, and the HUD.

## Decisions

- Went with `faster-whisper` for STT and `pyttsx3` (with optional Piper upgrade) for TTS — both install with plain `pip`, no compiled binaries required to get started.
- Permission mode defaults to `acceptEdits` + a curated allowlist rather than `bypassPermissions` — see [[Preferences/Example - coding style]] for the reasoning on caution around voice-triggered actions.

## Next

- Nothing yet — this is a template.
