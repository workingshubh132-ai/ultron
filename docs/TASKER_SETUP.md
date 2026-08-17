# Tasker Device-Unlock Bridge

Ultron can queue an "unlock" command from chat or WhatsApp (say "unlock my phone"). Your Android phone picks it up by polling the backend with Tasker and performs the actual unlock locally. The backend side (`/device/command` and `/device/poll` in `backend/main.py`) is already built and covered by the same `SHUBH_PASSWORD` auth as everything else. This doc is the Tasker-side setup, which has to be done by hand in the Tasker app on your phone — there's no file to import, because Tasker's project XML format is too easy to get subtly wrong without a real device to test against, and importing a broken profile is worse than none.

## Requirements

- [Tasker](https://play.google.com/store/apps/details?id=net.dinglisch.android.taskerm) (paid app)
- Your phone has Device Administrator access granted to Tasker, so Tasker's own "Unlock Screen" action can dismiss the keyguard (Tasker prompts for this the first time you use that action)
- Your backend's URL and `SHUBH_PASSWORD`

## 1. Create the polling Task

In Tasker:

1. **Tasks** tab → **+** → name it `UltronPoll`
2. Add action **Net → HTTP Request**
   - Method: `GET`
   - URL: `https://YOUR-BACKEND-URL/device/poll`
   - Headers: `x-shubh-token:YOUR_PASSWORD`
   - Output variable: leave default (`%HTTPD` holds the response body as text)
3. Add action **Alert → Flash** (optional, for debugging) with text `%HTTPD` so you can see what came back while testing
4. Add action **Variables → Variable Search Replace**
   - Variable: `%HTTPD`
   - Search: `unlock`
   - Store Result In: `%FoundUnlock`
   - (This is a cheap way to check the JSON contains an unlock command without a full JSON parse action — Tasker's JSON actions vary by version, this string check is simpler and good enough here.)
5. Add action **Task → If**: `%FoundUnlock` `Set`
6. Inside the If block, add action **Display → Unlock Screen**
7. Close the If block

## 2. Create the polling Profile

1. **Profiles** tab → **+** → **Time**
2. Set it to repeat: **From** now, **To** 11:59 PM, **Repeat** every 1 minute (or however often you want it checked — every 30-60s is reasonable and keeps battery impact low)
3. Link it to the `UltronPoll` task you just made

## 3. Test it

1. Message Ultron (WhatsApp or the HUD): `"unlock my phone"`
2. Wait for the next poll interval
3. Tasker's Flash alert (if you left it in) should show a response containing `"unlock"`, and the screen should unlock on the next poll

Remove the Flash alert step once you've confirmed it works — it's only there so you can see what's happening during setup.

## Notes

- The command queue is **in-memory** on the backend. If Render's free tier spins your service down from inactivity, the queue is empty when it wakes back up — this is fine for "unlock my phone right now" but don't rely on it for anything that needs to survive a backend restart.
- `/device/poll` **consumes** whatever is pending — each poll clears the queue, so two devices polling the same backend would race for commands. This is designed for a single device.
- Widen this the same way as chat: add a new phrase to `UNLOCK_KEYWORDS` in `backend/main.py`, or POST directly to `/device/command` with `{"action": "your_action"}` and give it a matching Tasker If-branch for other actions beyond unlock (e.g. "do not disturb on", "find my phone", etc).
- If you also set up [`AUTOVOICE_SETUP.md`](./AUTOVOICE_SETUP.md) (say a trigger word to talk to Ultron directly, no WhatsApp needed), that path unlocks immediately without waiting for a poll cycle - this polling setup still matters for anything sent over WhatsApp when you're not actively talking to the phone.
