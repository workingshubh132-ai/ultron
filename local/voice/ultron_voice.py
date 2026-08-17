#!/usr/bin/env python3
"""ULTRON's local voice loop: mic -> faster-whisper -> Claude Code (headless,
as the engine) -> local TTS. Writes hud/status.json for the HUD and appends
each exchange to the Obsidian vault. Run from local/, or set
ULTRON_ENGINE_DIR / ULTRON_VAULT_DIR to point elsewhere."""
import json
import os
import subprocess
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import listen  # noqa: E402
import speak  # noqa: E402
import status  # noqa: E402
import vault  # noqa: E402

LOCAL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(LOCAL_DIR, ".env"))
except ImportError:
    pass

ENGINE_DIR = os.environ.get("ULTRON_ENGINE_DIR", LOCAL_DIR)
VAULT_DIR = os.environ.get("ULTRON_VAULT_DIR", os.path.join(LOCAL_DIR, "memory-vault"))
PERMISSION_MODE = os.environ.get("ULTRON_PERMISSION_MODE", "acceptEdits")
ALLOWED_TOOLS = os.environ.get("ULTRON_ALLOWED_TOOLS", "Read,Grep,Glob,Edit,Write,WebFetch,WebSearch,TodoWrite")
CLAUDE_BIN = os.environ.get("ULTRON_CLAUDE_BIN", "claude")

STOP_PHRASES = ["shut down", "go to sleep", "that's all ultron", "power down"]

VOICE_SYSTEM_NOTE = (
    "Keep replies short and speakable out loud - a couple of sentences, "
    "no markdown formatting, no code blocks unless explicitly asked to show code."
)


def is_stop_phrase(text):
    lowered = text.lower()
    return any(phrase in lowered for phrase in STOP_PHRASES)


def _drain(stream, sink):
    for line in stream:
        sink.append(line)


def run_claude_turn(transcript, session_id):
    cmd = [
        CLAUDE_BIN, "-p", transcript,
        "--output-format", "stream-json",
        "--verbose",
        "--permission-mode", PERMISSION_MODE,
        "--append-system-prompt", VOICE_SYSTEM_NOTE,
    ]
    if ALLOWED_TOOLS:
        cmd += ["--allowedTools", ALLOWED_TOOLS]
    if session_id:
        cmd += ["--resume", session_id]

    env = dict(os.environ)
    env["ULTRON_VOICE_TURN"] = "1"  # tells the Stop hook to skip its own logging

    proc = subprocess.Popen(
        cmd, cwd=ENGINE_DIR, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )

    stderr_lines = []
    stderr_thread = threading.Thread(target=_drain, args=(proc.stderr, stderr_lines), daemon=True)
    stderr_thread.start()

    reply = ""
    new_session_id = session_id
    is_error = False

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        etype = event.get("type")
        if etype == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    status.update(state="thinking", current_tool=block.get("name"))
        elif etype == "result":
            reply = event.get("result", "") or ""
            new_session_id = event.get("session_id") or session_id
            is_error = bool(event.get("is_error"))

    proc.wait()
    stderr_thread.join(timeout=2)

    if proc.returncode != 0 and not reply:
        reply = "Something broke on the engine side - check the terminal."
        is_error = True
        print(f"[ultron] claude exited {proc.returncode}: {''.join(stderr_lines)}", file=sys.stderr)

    return reply, new_session_id, is_error


def main():
    print("ULTRON local voice loop - Ctrl+C to stop.")
    print(f"Engine dir: {ENGINE_DIR}")
    print(f"Vault dir:  {VAULT_DIR}")
    print(f"Permission mode: {PERMISSION_MODE} | Allowed tools: {ALLOWED_TOOLS or '(none - Bash stays gated)'}")

    session_id = None
    status.update(state="idle", current_tool=None, last_transcript="", last_reply="")

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

            reply, session_id, is_error = run_claude_turn(transcript, session_id)
            if is_error:
                print("[ultron] turn returned an error")
            print(f"ULTRON: {reply}")

            status.update(state="speaking", last_reply=reply, current_tool=None)
            status.append_history("ultron", reply)
            vault.append_voice_exchange(VAULT_DIR, transcript, reply)

            speak.speak(reply)
            status.update(state="idle")

    except KeyboardInterrupt:
        pass
    finally:
        status.update(state="offline", current_tool=None)
        print("\nULTRON offline.")


if __name__ == "__main__":
    main()
