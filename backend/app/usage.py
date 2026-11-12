"""Daily anonymous usage check-in, the same as My Audiobook Collection.

Once a day, and straight after an update, the app says it is running: the app name,
the version, where it runs (docker/lxc/other), how many days this install has been
going, and a random id made once per install. Nothing about packages, files or users
is ever sent. It is disclosed in the README and can be turned off with PSADT_USAGE_OPTOUT=1, and PSADT_USAGE_URL (+ PSADT_USAGE_TOKEN) points it
at your own collector instead. A failure is logged and retried at the next hourly look.
"""
import base64
import json
import os
import socket
import urllib.request
import uuid
from datetime import date, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from .db import get_setting, set_setting

# The author's own collector (the same as My Audiobook Collection), in plain sight on purpose:
# this is disclosed telemetry. The token that collector expects ships in this public code.
DEFAULT_URL = "https://hkjhykihflhfg5.the-airheads.com/webhook"
DEFAULT_TOKEN = base64.b64decode(
    "ZjgwMjRlYzQ5YThmYTljN2NhZjlmYTg0MTdmOWUzNjhjZGFhYzkwYjhmZWQ1N2ZhY2Q5NjQzMzEwNzMxOWYwOQ==").decode()

SINCE, LAST, LAST_VERSION, INSTALL_ID = "usage_since", "usage_last", "usage_last_version", "usage_install_id"


def platform(root: str = "/") -> str:
    def read(p: str) -> str:
        try:
            return Path(root, p).read_text(errors="replace")
        except OSError:
            return ""
    if Path(root, ".dockerenv").exists():
        return "docker"
    if "container=lxc" in read("proc/1/environ").split("\0") or read("run/systemd/container").strip() == "lxc":
        return "lxc"
    return "other"


def days_since(since: str, today: str) -> int:
    return (date.fromisoformat(today) - date.fromisoformat(since)).days + 1


def opted_out(db: Session) -> bool:
    return os.environ.get("PSADT_USAGE_OPTOUT") == "1"


def _install_id(db: Session) -> str:
    i = get_setting(db, INSTALL_ID, "")
    if not i:
        i = str(uuid.uuid4())
        set_setting(db, INSTALL_ID, i)
    return i


def _post(url: str, token: str, body: dict) -> None:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "X-Webhook-Token": token})
    with urllib.request.urlopen(req, timeout=10) as res:  # noqa: S310 - fixed https URL or the operator's own
        if res.status >= 300:
            raise OSError(f"answered {res.status}")


def report_once(db: Session, version: str, now: datetime | None = None, post=_post) -> dict | None:
    if opted_out(db):
        return None
    own = os.environ.get("PSADT_USAGE_URL", "")
    url = own or DEFAULT_URL
    token = os.environ.get("PSADT_USAGE_TOKEN", "") or ("" if own else DEFAULT_TOKEN)
    if not url or not token:
        return None
    now = now or datetime.now()
    today = now.date().isoformat()
    if get_setting(db, LAST, "") == today and get_setting(db, LAST_VERSION, "") == version:
        return None
    since = get_setting(db, SINCE, "") or today
    where = platform()
    body = {"appName": "PSADT Frontend", "version": version, "date": today, "time": now.strftime("%H:%M:%S"),
            "computerName": (os.environ.get("HOST_HOSTNAME") or socket.gethostname()) if own else _install_id(db),
            "platform": where, "dck": where == "docker", "days": days_since(since, today)}
    try:
        post(url, token, body)
    except Exception as e:  # noqa: BLE001 - never stops the app
        print(f"[psadt-frontend] usage check-in not sent: {e}", flush=True)
        return None
    set_setting(db, SINCE, since)
    set_setting(db, LAST, today)
    set_setting(db, LAST_VERSION, version)
    return body
