"""In-app updates, the same way My Audiobook Collection does them.

The app runs as an unprivileged user and cannot update itself, and should not be able to.
On an LXC install it leaves a file in its own data folder; a root systemd path unit sees it
and runs /usr/local/bin/psadt-frontend-update, which only ever does that one fixed thing.
Docker installs update by pulling a newer image.
"""
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import retention as ret
from ..config import settings
from ..db import get_db, get_setting, set_setting
from ..psadt.schema import LOG_PATH_PATTERN
from ..security import require_admin

router = APIRouter(prefix="/api/system", tags=["system"], dependencies=[Depends(require_admin)])

REPO = "Starf0x/PSADT-Frontend"
PSADT_LOG_PATH = r"$envWinDir\Logs\Software"  # PSADT 4 default (Toolkit.LogPath)
SRC_DIR = Path("/opt/psadt-frontend-src")
PATH_UNIT = Path("/etc/systemd/system/psadt-frontend-update.path")
_cache: dict = {"at": 0.0, "ttl": 0, "tag": None, "error": None}


def _version_tuple(v: str | None) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v or "")[:3])


def current_version() -> str:
    from ..main import APP_VERSION

    return APP_VERSION


def newest_release() -> tuple[str | None, str | None]:
    """Newest version tag on GitHub, cached for an hour (10 minutes after an error)."""
    if time.time() - _cache["at"] < _cache["ttl"]:
        return _cache["tag"], _cache["error"]
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/tags?per_page=100",
                                     headers={"Accept": "application/vnd.github+json", "User-Agent": "psadt-frontend"})
        with urllib.request.urlopen(req, timeout=10) as r:
            tags = [t["name"] for t in json.load(r) if re.fullmatch(r"v?\d+\.\d+\.\d+", t["name"])]
        _cache.update(tag=max(tags, key=_version_tuple) if tags else None, error=None, ttl=3600)
    except Exception as e:  # noqa: BLE001 - network trouble must never break the page
        _cache.update(error=f"Could not reach GitHub: {e}", ttl=600)
    _cache["at"] = time.time()
    return _cache["tag"], _cache["error"]


def install_method() -> str:
    if (SRC_DIR / ".git").exists() and PATH_UNIT.exists():
        return "lxc"
    if Path("/.dockerenv").exists():
        return "docker"
    return "other"


def _read_json(name: str):
    try:
        return json.loads((settings.data_dir / name).read_text())
    except (OSError, ValueError):
        return None


@router.get("/update")
def update_status():
    newest, error = newest_release()
    current = current_version()
    return {
        "current": current,
        "newest": newest.lstrip("v") if newest else None,
        "newer": bool(newest) and _version_tuple(newest) > _version_tuple(current),
        "error": error,
        "install": install_method(),
        "progress": _read_json("update-progress.json"),
        "last": _read_json("update-said.json"),
        "pending": (settings.data_dir / "update-wanted").exists(),
    }


@router.post("/update", status_code=status.HTTP_202_ACCEPTED)
def request_update():
    if install_method() != "lxc":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only an LXC install can update itself; for Docker pull the new image")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    progress = {"at": now, "step": 0, "of": 6, "doing": "Waiting for the updater to start", "done": False}
    (settings.data_dir / "update-progress.json").write_text(json.dumps(progress))
    (settings.data_dir / "update-wanted").write_text(now)
    return progress


class SettingsIn(BaseModel):
    upload_retention: str | None = None
    log_path: str | None = Field(default=None, pattern=LOG_PATH_PATTERN)


def _settings(db: Session) -> dict:
    return {"upload_retention": ret.retention(db), "choices": list(ret.CHOICES),
            "log_path": get_setting(db, "log_path", ""), "log_path_default": PSADT_LOG_PATH}


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    return _settings(db)


@router.put("/settings")
def put_settings(body: SettingsIn, db: Session = Depends(get_db)):
    removed = 0
    if body.upload_retention is not None:
        if body.upload_retention not in ret.CHOICES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown retention choice")
        set_setting(db, ret.KEY, body.upload_retention)
        removed = ret.purge_old_uploads(db)
    if body.log_path is not None:
        set_setting(db, "log_path", body.log_path.strip())
    return {**_settings(db), "removed": removed}
