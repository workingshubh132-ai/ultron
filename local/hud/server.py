#!/usr/bin/env python3
"""Local server for the Ultron HUD - serves the static HUD page(s) and
exposes /status, /vault/today, /memory, /event, and (if ULTRON_REMOTE_TOKEN
is set) POST /chat, which runs a real headless Claude Code turn. That last
one is what makes this reachable from your phone over Tailscale worthwhile:
same engine, same vault, whether you're at your desk or not.

Binds to 127.0.0.1 only by default - set ULTRON_HUD_BIND=0.0.0.0 deliberately
if you want it reachable from other devices (see docs/REMOTE_ACCESS_SETUP.md).
/chat always requires ULTRON_REMOTE_TOKEN to be set and matched, no matter
what it's bound to - there's no way to trigger a Claude Code turn through
this server without it."""
import json
import os
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HUD_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DIR = os.path.dirname(HUD_DIR)

sys.path.insert(0, os.path.join(LOCAL_DIR, "voice"))
import engine  # noqa: E402
import status  # noqa: E402
import vault  # noqa: E402

VAULT_DIR = os.environ.get("ULTRON_VAULT_DIR", os.path.join(LOCAL_DIR, "memory-vault"))
PORT = int(os.environ.get("ULTRON_HUD_PORT", "8765"))
BIND_ADDR = os.environ.get("ULTRON_HUD_BIND", "127.0.0.1")
REMOTE_TOKEN = os.environ.get("ULTRON_REMOTE_TOKEN")

_lock = threading.Lock()
_session_lock = threading.Lock()
_session_id = None


def _system_stats():
    try:
        import psutil

        return {"cpu_percent": psutil.cpu_percent(interval=0.1), "mem_percent": psutil.virtual_memory().percent}
    except ImportError:
        return None


def _token_matches(headers):
    return bool(REMOTE_TOKEN) and headers.get("x-shubh-token") == REMOTE_TOKEN


def _softly_authorized(headers):
    """Used by read-only endpoints: open when no token is configured at all
    (plain local-only use, unchanged from before remote access existed),
    required once a token is set."""
    if not REMOTE_TOKEN:
        return True
    return _token_matches(headers)


def _vault_memory_snapshot():
    items = []
    for folder in ("Preferences", "Projects"):
        folder_path = os.path.join(VAULT_DIR, folder)
        if not os.path.isdir(folder_path):
            continue
        for fname in sorted(os.listdir(folder_path)):
            if not fname.endswith(".md"):
                continue
            with open(os.path.join(folder_path, fname)) as f:
                body = f.read()
            if body.startswith("---"):
                end = body.find("---", 3)
                if end != -1:
                    body = body[end + 3:]
            items.append({"topic": f"{folder}/{os.path.splitext(fname)[0]}", "details": body.strip()[:600]})
    return items


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep the terminal quiet - the voice loop's own prints matter more

    def _send_json(self, payload, status_code=200):
        body = json.dumps(payload).encode()
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, x-shubh-token")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/status":
            if not _softly_authorized(self.headers):
                self._send_json({"detail": "Wrong or missing token."}, 403)
                return
            with _lock:
                data = status.read()
            data["system"] = _system_stats()
            self._send_json(data)
            return

        if path == "/vault/today":
            if not _softly_authorized(self.headers):
                self._send_json({"detail": "Wrong or missing token."}, 403)
                return
            today_path = os.path.join(VAULT_DIR, "Daily", datetime.now().strftime("%Y-%m-%d") + ".md")
            text = ""
            if os.path.exists(today_path):
                with open(today_path) as f:
                    text = f.read()
            self._send_json({"text": text})
            return

        if path == "/memory":
            if not _softly_authorized(self.headers):
                self._send_json({"detail": "Wrong or missing token."}, 403)
                return
            self._send_json(_vault_memory_snapshot())
            return

        if path == "/":
            path = "/index.html"
        file_path = os.path.normpath(os.path.join(HUD_DIR, path.lstrip("/")))
        if not file_path.startswith(HUD_DIR) or not os.path.isfile(file_path):
            self.send_response(404)
            self.end_headers()
            return

        content_type = "text/html" if file_path.endswith(".html") else "application/octet-stream"
        with open(file_path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/chat":
            if not _token_matches(self.headers):
                self._send_json({"detail": "Wrong or missing x-shubh-token. Set ULTRON_REMOTE_TOKEN to enable /chat."}, 403)
                return

            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {}

            message = (payload.get("message") or "").strip()
            if not message:
                self._send_json({"detail": "message is required"}, 400)
                return

            global _session_id
            with _session_lock:
                current_session = _session_id

            with _lock:
                status.update(state="thinking", current_tool=None, last_transcript=message)
                status.append_history("user", message)

            def on_tool_use(name):
                with _lock:
                    status.update(state="thinking", current_tool=name)

            reply, new_session_id, is_error = engine.run_claude_turn(message, current_session, on_tool_use=on_tool_use)

            with _session_lock:
                _session_id = new_session_id

            with _lock:
                status.update(state="idle", current_tool=None, last_reply=reply)
                status.append_history("ultron", reply)

            vault.append_voice_exchange(VAULT_DIR, message, reply)

            self._send_json({
                "status": "error" if is_error else "success",
                "reply": reply,
                "timestamp": datetime.now().isoformat(),
            })
            return

        if path == "/event":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {}

            with _lock:
                status.append_history("session", payload.get("summary", ""))
            self._send_json({"ok": True})
            return

        self.send_response(404)
        self.end_headers()


def main():
    if status.read().get("state") is None:
        status.update(state="offline")

    if BIND_ADDR != "127.0.0.1" and not REMOTE_TOKEN:
        print(
            "[ultron] WARNING: bound to a non-localhost address with no ULTRON_REMOTE_TOKEN set - "
            "/chat will refuse everything until you set one. Read-only endpoints are reachable to "
            "anyone who can reach this address, though.",
            file=sys.stderr,
        )

    server = ThreadingHTTPServer((BIND_ADDR, PORT), Handler)
    print(f"Ultron HUD server on http://{BIND_ADDR}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
