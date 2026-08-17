# Free Voice on Your Phone (Termux)

No Tasker, no AutoVoice, no paid anything. Tap a home-screen icon, say something, Ultron replies out loud. Not fully hands-free (you tap to start it — see the note at the bottom on how close you can get to hands-free for free), but it costs nothing and takes maybe 15 minutes.

Uses [Termux](https://f-droid.org/packages/com.termux/) - a real terminal on your phone - plus its companion **Termux:API** app, which exposes Android's own speech recognition and text-to-speech to shell scripts. Both are free and open source.

## 1. Install (all from F-Droid, not the Play Store)

Termux's Play Store build has been abandoned for years and is missing features - [F-Droid](https://f-droid.org/) is the actually-maintained source. Install these three, all free:

- [Termux](https://f-droid.org/packages/com.termux/) - the terminal itself
- [Termux:API](https://f-droid.org/packages/com.termux.api/) - a *separate* companion app. The `termux-api` package inside Termux only works if this app is also installed - it's what actually holds the Android permissions.
- [Termux:Widget](https://f-droid.org/packages/com.termux.widget/) - lets a script show up as a tappable home-screen icon

Open Termux:API once after installing so Android registers it, and grant it microphone access when asked (you may need to do this manually in Android's app settings if it doesn't prompt).

## 2. Set up Termux

In the Termux app:

```bash
pkg update
pkg install termux-api jq curl
```

## 3. Configure your backend details

```bash
cat > ~/.ultron_env <<'EOF'
ULTRON_BACKEND_URL=https://your-app.onrender.com
ULTRON_TOKEN=your_shubh_password
EOF
```

Use your actual Render URL and the same password as `SHUBH_PASSWORD` in `backend/.env`.

## 4. Create the script

```bash
mkdir -p ~/.shortcuts
cat > ~/.shortcuts/ultron.sh <<'SCRIPT'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

CONFIG="$HOME/.ultron_env"
[ -f "$CONFIG" ] && source "$CONFIG"

BACKEND_URL="${ULTRON_BACKEND_URL:?Set ULTRON_BACKEND_URL in ~/.ultron_env}"
TOKEN="${ULTRON_TOKEN:?Set ULTRON_TOKEN in ~/.ultron_env}"

TRANSCRIPT="$(termux-speech-to-text)"

if [ -z "$TRANSCRIPT" ]; then
  termux-tts-speak "Didn't catch that."
  exit 0
fi

BODY="$(jq -n --arg msg "$TRANSCRIPT" '{message: $msg, device: "termux"}')"

RESPONSE="$(curl -s -X POST "$BACKEND_URL/chat" \
  -H "Content-Type: application/json" \
  -H "x-shubh-token: $TOKEN" \
  -d "$BODY")"

REPLY="$(echo "$RESPONSE" | jq -r '.reply // "Something went wrong on the backend."')"

termux-tts-speak "$REPLY"
SCRIPT
chmod +x ~/.shortcuts/ultron.sh
```

(`jq -n --arg` builds the JSON body safely - it properly escapes whatever you actually said, including quotes or punctuation, instead of risking malformed JSON from a hand-built string.)

## 5. Add the home-screen widget

Long-press your home screen → Widgets → **Termux:Widget** → drop it on your home screen → pick `ultron.sh` from the list.

## 6. Test it

Tap the widget. Android's speech recognizer will pop up listening - say something. It should hit `/chat` and speak the reply back through your phone's TTS voice within a couple seconds.

## How close this gets to "hands-free"

This is tap-to-talk, not wake-word. Android's speech recognizer needs to be actively invoked (`termux-speech-to-text` opens it), and nothing here runs continuously in the background listening for a trigger word - that's specifically what the paid AutoVoice plugin buys you (see `AUTOVOICE_SETUP.md`), by keeping a recognizer alive in the background with OS permissions Termux alone doesn't get you.

If you want to push closer to hands-free without spending anything, **[Automate by LlamaLab](https://llamalab.com/automate/)** is a free flow-based automation app with both an HTTP Request block and a Speech Recognition block, so the same "listen → hit /chat → speak reply" flow is buildable in it too. I couldn't verify from here exactly how close its speech recognition block gets to true always-on background listening (its docs weren't reachable from this session) - worth exploring yourself if tap-to-talk isn't good enough, but I'm not going to write you exact steps for a flow I haven't been able to check.
