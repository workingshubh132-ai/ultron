"""Shared Claude Code invocation - the actual "engine" call. Used by both
the local mic voice loop (ultron_voice.py) and the remote /chat endpoint
(hud/server.py) so a phone reaching in over Tailscale gets the exact same
brain, permissions, and vault as talking to it at your desk."""
import json
import os
import subprocess
import sys
import threading

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

SPEAKABLE_SYSTEM_NOTE = (
    "Keep replies short and speakable out loud - a couple of sentences, "
    "no markdown formatting, no code blocks unless explicitly asked to show code."
)


def _drain(stream, sink):
    for line in stream:
        sink.append(line)


def run_claude_turn(message, session_id, on_tool_use=None):
    """Runs one headless Claude Code turn and returns (reply, new_session_id,
    is_error). on_tool_use(name), if given, is called live as tool_use
    events stream in - callers use this to update status.json."""
    cmd = [
        CLAUDE_BIN, "-p", message,
        "--output-format", "stream-json",
        "--verbose",
        "--permission-mode", PERMISSION_MODE,
        "--append-system-prompt", SPEAKABLE_SYSTEM_NOTE,
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
                if block.get("type") == "tool_use" and on_tool_use:
                    on_tool_use(block.get("name"))
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
