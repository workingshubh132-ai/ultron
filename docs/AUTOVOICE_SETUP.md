# Hands-Free Voice on Your Phone (Tasker + AutoVoice)

Say "ultron" (or whatever trigger word you pick) anywhere on your phone, no app open, and it talks back — same brain as WhatsApp and the HUD, just triggered by voice instead of typing. This reuses `/chat` as-is; nothing in `backend/` needs to change.

Like `TASKER_SETUP.md`, this is manual setup in the Tasker app, not an importable file — AutoVoice's exact menu wording has shifted across versions and I can't test against a real device from here, so treat the steps below as the shape of it and adapt to what you actually see on screen. The Tasker mechanism itself (Event → Plugin → AutoVoice → Recognized, with `%avcomm`/`%avcommnofilter` populated after) is long-standing and stable; I checked the current variable names against AutoVoice's own docs before writing this.

## Requirements

- [Tasker](https://play.google.com/store/apps/details?id=net.dinglisch.android.taskerm) (paid)
- [AutoVoice](https://play.google.com/store/apps/details?id=com.joaomgcd.autovoice) (paid, a few dollars) — the premium tier is what gets you always-on background listening; free AutoVoice can still do voice recognition, but you have to trigger listening yourself (e.g. via a widget/shortcut) rather than it running in the background all the time
- Your backend's URL and `SHUBH_PASSWORD`, same as `TASKER_SETUP.md`

## 1. Turn on continuous listening in AutoVoice

Open the AutoVoice app itself (not Tasker) → its own settings → find the continuous/always-on listening toggle and turn it on. On Android 10+, it'll also prompt Tasker for background/microphone permissions the first time — grant them, or none of this works while the screen is off.

Set your trigger word here (or in the profile's Recognized condition — see below, they interact). Use "ultron" to match the rest of this repo, or whatever you actually want to say out loud.

## 2. Build the Tasker profile

1. **Profiles** tab → **+** → **Event** → **Plugin** → **AutoVoice** → **Recognized**
2. Set the **Command Filter** to `ultron` (or your trigger word) — this is both what tells the profile when to fire and what gets stripped out of the recognized text for you
3. Link it to a new task, call it `UltronVoice`

## 3. Build the `UltronVoice` task

The goal: take what you said after the trigger word, send it to `/chat`, speak back whatever comes back, and unlock the screen immediately if the reply says an unlock was queued (no need to wait for the Tasker unlock-poll cycle from `TASKER_SETUP.md` when you triggered it by voice directly).

1. **Code → JavaScriptlet** — build the request body safely (voice transcripts can contain quotes/punctuation that would break hand-built JSON):
   ```javascript
   setLocal('json_body', JSON.stringify({ message: local('avcommnofilter'), device: 'tasker-voice' }));
   ```
2. **Net → HTTP Request**
   - Method: `POST`
   - URL: `https://YOUR-BACKEND-URL/chat`
   - Headers: `Content-Type:application/json` and `x-shubh-token:YOUR_PASSWORD`
   - Body: `%json_body`
   - Output variable: default (`%http_data` holds the response body)
3. **Code → JavaScriptlet** — pull the reply out of the response:
   ```javascript
   setLocal('reply_text', JSON.parse(local('http_data')).reply);
   ```
4. **Plugin → AutoVoice → Speak**, text: `%reply_text`
5. **Task → If**: `%reply_text` `Contains` `Unlock queued`
6. Inside the If: **Display → Unlock Screen**
7. Close the If block

## 4. Test it

Say "ultron, what should I do today" (or your trigger word + anything). It should recognize, hit `/chat`, and speak the reply back within a couple of seconds. Try "ultron, unlock my phone" to confirm the immediate-unlock branch fires too.

## Notes

- This and the polling setup in `TASKER_SETUP.md` are complementary, not either/or: this path is instant but only works while your phone is actively listening; the poll-based unlock still matters for commands sent over WhatsApp when you're not talking to the phone at all.
- `%avcomm` (the full phrase including the trigger word) is also available if you want the LLM to see the whole thing including "ultron" - most of the time `%avcommnofilter` (just what came after) is what you want, since there's no reason to spend tokens on your own wake word.
- Continuous background listening is a real battery/privacy tradeoff - your phone's mic is active listening for the trigger word whenever the screen is on (and possibly off, depending on your AutoVoice settings). Decide if that's a tradeoff you actually want before turning it on permanently.
