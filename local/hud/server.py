#!/usr/bin/env python3
"""Tiny local server for the Ultron HUD: serves the static HUD page and
exposes /status, /vault/today, and a /event sink for the Stop hook. Stdlib
only (psutil is optional, used for /status system stats if installed) so
running the HUD never needs anything beyond python3 itself."""
import json
import os
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HUD_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DIR = os.path.dirname(HUD_DIR)
STATUS_PATH = os.environ.get("ULTRON_STATUS_PATH", os.path.join(HUD_DIR, "status.json"))
VAULT_DIR = os.environ.get("ULTRON_VAULT_DIR", os.path.join(LOCAL_DIR, "memory-vault"))
PORT = int(os.environ.get("ULTRON_HUD_PORT", "8765"))

_lock = threading.Lock()

_DEFAULT_STATUS = {
    "state": "offline",
    "current_tool": None,
    "last_transcript": "",
    "last_reply": "",
    "history": [],
    "updated_at": None,
}


def _read_status():
    try:
        with open(STATUS_PATH) as f:
            return json.load(f)
    except Exception:
        return dict(_DEFAULT_STATUS)


def _write_status(data):
    data["updated_at"] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(STATUS_PATH), exist_ok=True)
    tmp_path = STATUS_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f)
    os.replace(tmp_path, STATUS_PATH)


def _system_stats():
    try:
        import psutil

        return {"cpu_percent": psutil.cpu_percent(interval=0.1), "mem_percent": psutil.virtual_memory().percent}
    except ImportError:
        return None


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
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/status":
            with _lock:
                data = _read_status()
            data["system"] = _system_stats()
            self._send_json(data)
            return

        if path == "/vault/today":
            today_path = os.path.join(VAULT_DIR, "Daily", datetime.now().strftime("%Y-%m-%d") + ".md")
            text = ""
            if os.path.exists(today_path):
                with open(today_path) as f:
                    text = f.read()
            self._send_json({"text": text})
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
        if path == "/event":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {}

            with _lock:
                data = _read_status()
                history = data.get("history", [])
                history.append({
                    "role": "session",
                    "text": payload.get("summary", ""),
                    "ts": datetime.now().isoformat(),
                })
                data["history"] = history[-30:]
                _write_status(data)
            self._send_json({"ok": True})
            return

        self.send_response(404)
        self.end_headers()


def main():
    if not os.path.exists(STATUS_PATH):
        _write_status(dict(_DEFAULT_STATUS))
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Ultron HUD server on http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
