# ULTRON — Local (Claude Code + Obsidian + Voice + HUD)

This is the other kind of Ultron in this repo: not the cloud/WhatsApp stack in `../backend` and `../hud`, but a fully local "personal Jarvis" built from four pieces, same idea as the `@chase.h.ai`-style breakdown — Claude Code as the engine, Obsidian as memory, a local voice pipeline as ears/mouth, one HUD as the face. Everything runs on your own machine; nothing here talks to Render, Groq, Supabase, or WhatsApp.

```
local/
├── CLAUDE.md            Ultron's persona + how it should use the vault (auto-loaded by Claude Code)
├── .claude/
│   ├── settings.json    Stop hook wiring
│   └── hooks/log_session.py   appends a line to today's vault note whenever a session here ends
├── memory-vault/         Obsidian vault - Ultron's memory, plain markdown
├── voice/                mic -> faster-whisper -> Claude Code -> TTS loop
├── hud/                  status display (ember/red, not Jarvis blue) + tiny local server
├── run.sh                starts the HUD server + voice loop together
└── requirements.txt
```

## How it fits together

```
   you talk
      │
      ▼
 voice/listen.py  (mic, energy-based auto-stop, faster-whisper STT)
      │  transcript
      ▼
 voice/ultron_voice.py  ──spawns──►  claude -p "<transcript>" --output-format stream-json
      │                                   (cwd = local/, so CLAUDE.md + the vault hook apply)
      │  reply text + live tool-use events
      ├──► voice/speak.py         (TTS - spoken back to you)
      ├──► voice/vault.py         (appended to memory-vault/Daily/<today>.md)
      └──► hud/status.json        (state, current tool, history - polled by the HUD)
                                          │
                                          ▼
                                   hud/index.html  (polls hud/server.py every second)
```

Claude Code is the actual brain here — the voice loop doesn't call any LLM API directly, it just shells out to your existing `claude` CLI in headless mode (`-p`) and streams the events back. Everything Claude Code can normally do (read/edit files, run commands, browse) it can do here too, gated by `ULTRON_PERMISSION_MODE`/`ULTRON_ALLOWED_TOOLS` below.

## Setup

### 1. Requirements

- [Claude Code](https://claude.com/claude-code) installed and logged in (`claude` on your PATH — `claude --version` should work)
- Python 3.10+
- A working microphone/speakers
- (Optional) [Obsidian](https://obsidian.md) if you want a nice UI for the vault — it's just markdown files either way, so this is purely cosmetic

```bash
cd local
cp .env.example .env
pip install -r requirements.txt
```

`sounddevice` needs PortAudio available on your system. On macOS/Windows the pip wheel bundles it; on Linux install it first if the import fails: `sudo apt install libportaudio2` (Debian/Ubuntu) or the equivalent for your distro.

### 2. Open the vault in Obsidian (optional but recommended)

Obsidian → "Open folder as vault" → select `local/memory-vault/`. You'll see `Ultron Home.md` and the example notes in `Projects/` and `Preferences/` — replace those with your own.

**Fill in `Preferences/About Me.md` before your first real conversation.** This is what actually makes Ultron feel like it knows you instead of a fresh chatbot every session — `CLAUDE.md` tells it to read that note before anything non-mechanical. Ten minutes filling it in now saves weeks of it re-learning who you are.

### 3. Run it

```bash
./run.sh
```

This starts the HUD server (`http://127.0.0.1:8765`, opens automatically in your browser) and then the voice loop in your terminal. Speak after "listening" appears; it auto-stops after ~1.2s of silence and sends what you said to Claude Code. Say "shut down" or "go to sleep" to end the session.

You can also run the pieces separately:

```bash
python3 hud/server.py       # HUD only
python3 voice/ultron_voice.py   # voice loop only (HUD is optional, this works without it)
```

## Permissions — read this before you turn it on

There's no one standing by to click "approve" on a voice-triggered tool call — headless mode can't show an interactive prompt, so any tool call that isn't pre-approved either gets denied or (in more permissive modes) just runs. That matters more here than in normal Claude Code use, because voice is transcribed, and transcription is imperfect.

The default in `.env.example`:

```
ULTRON_PERMISSION_MODE=acceptEdits
ULTRON_ALLOWED_TOOLS=Read,Grep,Glob,Edit,Write,WebFetch,WebSearch,TodoWrite
```

Out of the box this means Ultron can read, search, edit, and write files, and browse the web, hands-free — but **Bash is not in the allowlist**, so it can't run arbitrary shell commands until you explicitly add them. That's deliberate: I'm not going to hand you a "safe" wildcard like `Bash(git *)` as a default, because that also covers `git push --force` and `git reset --hard`, and I have no way to guarantee what you consider safe for a voice-triggered agent. Add specific patterns once you've decided you trust them:

```
ULTRON_ALLOWED_TOOLS=Read,Grep,Glob,Edit,Write,WebFetch,WebSearch,TodoWrite,Bash(git status),Bash(git diff),Bash(npm test),Bash(git commit *)
```

`ULTRON_PERMISSION_MODE=bypassPermissions` exists and removes every guardrail, including for tools not in the allowlist at all. Only reach for it on a machine/sandbox where you genuinely don't mind a misheard command running unsupervised — never as a default.

## Voice pipeline details

- **STT**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper), fully local, CPU by default. `WHISPER_MODEL_SIZE=base.en` is the default (fast, decent accuracy); bump to `small.en` or `medium.en` for better accuracy at the cost of latency, or set `WHISPER_DEVICE=cuda` if you have an NVIDIA GPU.
- **Turn-taking**: no wake word by default — it's push-to-talk-by-voice: the loop waits for you to start speaking (energy threshold), then auto-stops after a pause. A real wake-word ("hey ultron") needs an always-listening keyword spotter (e.g. `openwakeword`), which isn't wired in here to keep the dependency list short; it's a clean addition on top of `voice/listen.py` if you want it.
- **TTS**: [pyttsx3](https://github.com/nateshmbhat/pyttsx3) by default — uses your OS's built-in voices, zero model downloads, works immediately. For noticeably better voice quality, install [Piper](https://github.com/OHF-Voice/piper1-gpl) (`pip install piper-tts` or the standalone binary) and a voice model (`.onnx` file, downloadable from Piper's voice list), then set:
  ```
  TTS_ENGINE=piper
  PIPER_EXE=piper
  PIPER_MODEL=/path/to/en_US-some-voice-medium.onnx
  ```

## The HUD

`hud/index.html` is a pure status display — it does not capture audio itself (the Python voice loop does that). It polls `hud/server.py`'s `/status` endpoint once a second and shows: the core (idle/listening/thinking/speaking, colored and pulsing to match), which tool Claude Code is currently using (parsed live from `--output-format stream-json`), a scrolling activity feed, today's vault note, and CPU/memory. `server.py` is stdlib-only (no extra install) except `psutil` for the CPU/mem tiles, which degrades gracefully if it's missing.

Point a second monitor or an old tablet's browser at `http://<your-machine-ip>:8765` on your LAN if you want the wall-mounted-display look — the server binds to `127.0.0.1` by default for safety; change the bind address in `hud/server.py` deliberately if you want LAN access, and know that doing so exposes your activity feed and vault contents to anything on that network.

## Memory (the vault)

See `memory-vault/Ultron Home.md` for the schema. Short version: `Daily/` is an automatic activity log (written by the `Stop` hook for any Claude Code session run in `local/`, and by the voice loop for spoken exchanges), `Projects/`, `People/`, and `Preferences/` are notes Ultron maintains itself per the instructions in `CLAUDE.md`. `Daily/*.md` is gitignored by default since it's raw transcript-derived personal activity; `Projects/`, `People/`, and `Preferences/` are not, since you may want those version-controlled — decide for yourself whether that's what you want before committing.
