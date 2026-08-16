# ULTRON OS

A personal AI assistant with three parts:

1. **Brain** (`backend/`) — FastAPI service that talks to Groq (free LLM) and remembers things in Supabase.
2. **WhatsApp bridge** (`whatsapp_bridge/`) — relays your personal WhatsApp messages to the brain and replies with what it says.
3. **HUD** (`hud/`) — a standalone, ember/red "reactor" interface you can put on a spare monitor or TV: hold Space to talk, it speaks back, the core pulses with your live voice amplitude, there's a wake-word mode, and a live memory panel.

For the full click-by-click setup (creating the Groq/Supabase/Render accounts, installing Python/Node/Git), see [`ULTRON_COMPLETE_BEGINNER_GUIDE.md`](./ULTRON_COMPLETE_BEGINNER_GUIDE.md). This README is the fast path once those accounts exist.

```
ultron/
├── backend/            FastAPI brain (Groq + Supabase)
├── whatsapp_bridge/    whatsapp-web.js relay
└── hud/                Standalone browser HUD
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

Say "learn that ...", "remember that ...", "save that ...", or "log that ..." in a message and it gets written to Supabase permanently.

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
- **Wake** button — continuous listening for the word "ultron"; say "ultron, what's my next move" and it fires automatically. Mutually exclusive with push-to-talk while active (holding Space still interrupts it).
- **Memory** button — opens a live panel reading `/memory`.
- **Link** button — reopen the connection modal to change the backend URL/password.

Requires a Chromium-based browser (Chrome/Edge) for speech recognition — Firefox and Safari don't support the Web Speech API's recognition side.

## Security notes

- Change `SHUBH_PASSWORD` away from the guide's default before deploying anywhere public — it's the only thing standing between the internet and your `/chat` and `/memory` endpoints.
- Keep the GitHub repo **private**. Never commit `.env` files (already covered by `.gitignore`).
- CORS is wide open (`allow_origins=["*"]`) so the HUD can reach the API from any origin. If you never open the HUD from anywhere but your own machine, you can tighten this to your specific origin in `backend/main.py`.

## What's not built yet

Two follow-ups mentioned but not implemented in this repo:
- **Tasker device-unlock bridge** — having Ultron trigger a Tasker profile to unlock a phone/device on command.
- **Always-on voice loop** — continuous conversation without needing to hold Space or say the wake word each time.

Say the word and either can be added next.
