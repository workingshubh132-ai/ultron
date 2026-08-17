# Reaching Ultron From Your Phone (Tailscale)

The local stack (Claude Code + Obsidian + this HUD) is built to run on one computer. This is how you reach that same engine from your phone, anywhere, without exposing anything to the public internet - using [Tailscale](https://tailscale.com), which is free for personal use (unlimited devices under your own account as of its current pricing).

**Before doing this, make sure you actually want to.** Every message through this hits real Claude usage on your Claude Pro plan - the mentor/friend conversations you want to have all day are a much better fit for the free cloud/WhatsApp stack in the repo root. This is for when you specifically want the Claude-Code engine (real file/task access, your Obsidian memory) reachable when you're not at your computer - not as your primary way of talking to Ultron.

## How it works

Tailscale creates a private network between only the devices you log into it with - your laptop and your phone, nothing else. It's not a public tunnel; nobody else can reach your machine through it, even though it works over the regular internet. Your phone gets a stable address for your laptop that works from anywhere, not just your home WiFi.

```
Your phone (talk.html, browser mic/speech)
      │  Tailscale private network
      ▼
Your laptop, local/hud/server.py  ──►  claude -p "..." (Claude Code, real engine)
      │
      ▼
memory-vault/ (same Obsidian vault either way)
```

## 1. Install Tailscale on both devices

- Laptop: [tailscale.com/download](https://tailscale.com/download), then `tailscale up` and log in (any account - Google is fine)
- Phone: Tailscale app from the Play Store / App Store, log in with the **same account**

Once both are connected, note your laptop's Tailscale address - either run `tailscale ip -4` on the laptop, or look it up in the Tailscale admin console. It'll look like `100.x.x.x`, or a hostname like `your-laptop.tailXXXX.ts.net` if you've enabled MagicDNS.

## 2. Set a real token and open the bind address

In `local/.env`:

```
ULTRON_HUD_BIND=0.0.0.0
ULTRON_REMOTE_TOKEN=pick-something-long-and-random-here
```

Don't reuse a password from anywhere else. This token is the only thing standing between your Claude Code engine (which can read, write, and run things on your machine) and anyone who can reach this port - which, with `ULTRON_HUD_BIND=0.0.0.0`, technically includes your home WiFi too, not just Tailscale. The server refuses `/chat` outright with no token set, but don't treat that as a substitute for picking a real one.

## 3. Start it

```bash
cd local
./run.sh
```

The terminal will print the bind address it's listening on. If you set `ULTRON_HUD_BIND=0.0.0.0` without a token, it'll print a loud warning and keep running with `/chat` refusing everything - that's intentional, not a bug.

## 4. Open `talk.html` on your phone

Go to `http://<your-tailscale-address>:8765/talk.html` in your phone's browser (Chrome or Edge - Safari and Firefox don't support the Web Speech API this uses). Tap **Link**, it'll prefill with the current address - paste in your `ULTRON_REMOTE_TOKEN` as the token, save.

From there it's the same interface as the cloud HUD: hold anywhere to talk isn't a thing on mobile (no spacebar), so use **Loop** for hands-free, or just type - actually, there's no text input built in here, it's voice-first. Tap **Wake** or **Loop** and speak.

## Notes

- This reuses the exact same `/chat` shape as the cloud stack, which is why `talk.html` is a near-copy of `hud/index.html` - point either HUD at either backend and it works, since they speak the same protocol.
- Closing your laptop or losing WiFi at home takes this down - Tailscale connects devices, it doesn't keep your laptop running. If you want this reachable while your laptop is asleep, that's a separate (and more involved) problem this doesn't solve.
- The remote `/chat` path and the local voice loop (`voice/ultron_voice.py`) run as separate processes with separate Claude Code sessions - talking to Ultron from your phone and from your desk mic at the same time won't fight over the same conversation thread, but both read/write the same `memory-vault/`, so context still carries over either way.
