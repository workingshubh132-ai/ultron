"""Reads/writes hud/status.json - the only thing connecting the voice loop
to the HUD (a plain file on disk, polled by hud/server.py)."""
import json
import os
from datetime import datetime

STATUS_PATH = os.environ.get(
    "ULTRON_STATUS_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hud", "status.json"),
)

_DEFAULTS = {
    "state": "offline",
    "current_tool": None,
    "last_transcript": "",
    "last_reply": "",
    "history": [],
}


def _read():
    try:
        with open(STATUS_PATH) as f:
            return json.load(f)
    except Exception:
        return dict(_DEFAULTS)


def _write(data):
    data["updated_at"] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(STATUS_PATH), exist_ok=True)
    tmp_path = STATUS_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f)
    os.replace(tmp_path, STATUS_PATH)


def update(**kwargs):
    data = _read()
    data.update(kwargs)
    _write(data)


def append_history(role, text, cap=30):
    data = _read()
    history = data.get("history", [])
    history.append({"role": role, "text": text, "ts": datetime.now().isoformat()})
    data["history"] = history[-cap:]
    _write(data)
