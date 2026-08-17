# ULTRON OS

Two separate ways to build a personal Ultron in this repo — pick one, or run both:

1. **Cloud + WhatsApp** (`backend/`, `whatsapp_bridge/`, `hud/`) — a FastAPI brain on Groq + Supabase, deployed to Render, that you text on WhatsApp; plus a browser HUD that talks to it directly. Always-on, reachable from your phone anywhere. Covered below.
2. **Local** (`local/`) — the other well-known "personal Jarvis" recipe: Claude Code itself as the thinking/acting engine, an Obsidian vault as memory, a fully local voice pipeline (faster-whisper + TTS) as ears/mouth, and a status-display HUD as the face. Everything runs on your own machine, nothing leaves it except normal Claude Code API calls. See [`local/README.md`](./local/README.md) — different enough from the stack below that it gets its own doc.

They don't depend on each other. The rest of this README is the cloud/WhatsApp stack.

For the full click-by-click setup of that stack (creating the Groq/Supabase/Render accounts, installing Python/Node/Git), see [`ULTRON_COMPLETE_BEGINNER_GUIDE.md`](./ULTRON_COMPLETE_BEGINNER_GUIDE.md). This README is the fast path once those accounts exist.

```
ultron/
├── backend/            FastAPI brain (Groq + Supabase)
├── whatsapp_bridge/    whatsapp-web.js relay
├── hud/                Standalone browser HUD (talks to backend/ over the internet)
├── docs/
│   └── TASKER_SETUP.md Manual steps for the phone-unlock bridge
└── local/              The other stack: Claude Code + Obsidian + local voice + a status HUD
```

## 1. Backend

```bash
cd backend
cp .env.example .env      # fill in GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY, SHUBH_PASSWORD
pip install -r requirements.txt
uvicorn main:app --reload
```

Check `http://127.0.0.1:8000/status` — you should see `ULTRON BRAIN ONLINE`.

**Endpoints:**
- `GET /status` — health check, no auth
- `POST /chat` — `{ "message": "...", "device": "..." }`, requires header `x-shubh-token: <SHUBH_PASSWORD>`
- `GET /memory` — returns everything Ultron has learned, requires the same header (used by the HUD's memory panel)
- `POST /device/command` / `GET /device/poll` — the Tasker unlock queue, see below

Say "learn that ...", "remember that ...", "save that ...", or "log that ..." in a message and it gets written to Supabase permanently. Say "unlock my phone" and it queues an unlock command for Tasker to pick up.

### Deploy to Render

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port 10000`
- Add the four env vars from `.env` in the Render dashboard — **use a real password for `SHUBH_PASSWORD`, not the guide's default.**

You'll get a public URL like `https://ultron-brain.onrender.com`.

## 2. WhatsApp bridge

```bash
cd whatsapp_bridge
cp .env.example .env      # BACKEND_URL, SHUBH_TOKEN (same value as SHUBH_PASSWORD), MY_NUMBER
npm install
npm start
```

Scan the printed QR code with a **second** phone/WhatsApp account (Linked Devices). Message that account from your personal number — only messages from `MY_NUMBER` get relayed to the brain.

## 3. HUD

The HUD is a single static file — no build step, no server required.

```bash
cd hud
python -m http.server 8080
# open http://localhost:8080 in Chrome or Edge
```

(Opening `index.html` directly by double-clicking also works in most cases, but serving it locally avoids occasional browser restrictions on microphone access.)

On first load it'll prompt you to **Link**: paste your Render URL and your `SHUBH_PASSWORD`. That's stored in the browser's `localStorage`, nowhere else.

**Controls:**
- **Hold Space** — push-to-talk. The core brightens and reacts to your real voice amplitude via the Web Audio API while you're speaking.
- **Release Space** — sends the transcript to `/chat`, reply is spoken back with the browser's speech synthesis.
- **Wake** button — continuous listening for the word "ultron"; say "ultron, what's my next move" and it fires automatically.
- **Loop** button — hands-free continuous conversation: no wake word, no held key. It listens, sends whatever you said after ~1.5s of silence, speaks the reply, then starts listening again automatically. Say "stop listening" (or "go to sleep") to end it. Mutually exclusive with Wake — turning one on turns the other off, since only one continuous recognizer can run at a time.
- **Memory** button — opens a live panel reading `/memory`.
- **Link** button — reopen the connection modal to change the backend URL/password.

Requires a Chromium-based browser (Chrome/Edge) for speech recognition — Firefox and Safari don't support the Web Speech API's recognition side.

## Security notes

- Change `SHUBH_PASSWORD` away from the guide's default before deploying anywhere public — it's the only thing standing between the internet and your `/chat` and `/memory` endpoints.
- Keep the GitHub repo **private**. Never commit `.env` files (already covered by `.gitignore`).
- CORS is wide open (`allow_origins=["*"]`) so the HUD can reach the API from any origin. If you never open the HUD from anywhere but your own machine, you can tighten this to your specific origin in `backend/main.py`.

## Device unlock (Tasker)

The backend can queue a command ("unlock my phone" in chat/WhatsApp, or `POST /device/command`) that your Android phone consumes by polling `GET /device/poll` from Tasker. The polling/queue code is in `backend/main.py`; the Tasker-side profile has to be built by hand in the Tasker app on your phone (there's no importable file — see [`docs/TASKER_SETUP.md`](./docs/TASKER_SETUP.md) for exact steps and why).
