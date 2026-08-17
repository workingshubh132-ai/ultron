#!/usr/bin/env python3
"""ULTRON's local voice loop: mic -> faster-whisper -> Claude Code (headless,
via engine.py) -> local TTS. Writes hud/status.json for the HUD and appends
each exchange to the Obsidian vault. Run from local/, or set
ULTRON_ENGINE_DIR / ULTRON_VAULT_DIR to point elsewhere."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine  # noqa: E402
import listen  # noqa: E402
import speak  # noqa: E402
import status  # noqa: E402
import vault  # noqa: E402

STOP_PHRASES = ["shut down", "go to sleep", "that's all ultron", "power down"]


def is_stop_phrase(text):
    lowered = text.lower()
    return any(phrase in lowered for phrase in STOP_PHRASES)


def main():
    print("ULTRON local voice loop - Ctrl+C to stop.")
    print(f"Engine dir: {engine.ENGINE_DIR}")
    print(f"Vault dir:  {engine.VAULT_DIR}")
    print(f"Permission mode: {engine.PERMISSION_MODE} | Allowed tools: {engine.ALLOWED_TOOLS or '(none - Bash stays gated)'}")

    session_id = None
    status.update(state="idle", current_tool=None, last_transcript="", last_reply="")

    def on_tool_use(name):
        status.update(state="thinking", current_tool=name)

    try:
        while True:
            status.update(state="listening", current_tool=None)
            audio = listen.record_utterance()
            if audio is None:
                status.update(state="idle")
                continue

            transcript = listen.transcribe(audio)
            if not transcript:
                status.update(state="idle")
                continue

            print(f"YOU: {transcript}")
            status.update(state="thinking", last_transcript=transcript, current_tool=None)
            status.append_history("user", transcript)

            if is_stop_phrase(transcript):
                speak.speak("Going quiet. Say the word when you need me.")
                status.update(state="offline")
                break

            reply, session_id, is_error = engine.run_claude_turn(transcript, session_id, on_tool_use=on_tool_use)
            if is_error:
                print("[ultron] turn returned an error")
            print(f"ULTRON: {reply}")

            status.update(state="speaking", last_reply=reply, current_tool=None)
            status.append_history("ultron", reply)
            vault.append_voice_exchange(engine.VAULT_DIR, transcript, reply)

            speak.speak(reply)
            status.update(state="idle")

    except KeyboardInterrupt:
        pass
    finally:
        status.update(state="offline", current_tool=None)
        print("\nULTRON offline.")


if __name__ == "__main__":
    main()
