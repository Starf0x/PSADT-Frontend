"""Removes uploaded installer files after the retention time an admin chose on the System page."""
import shutil
import time
from pathlib import Path

from .config import settings
from .db import get_setting

KEY = "upload_retention"
CHOICES = ("forever", "export", "1", "7", "30", "90")  # "export" = right after a successful export
DEFAULT = "forever"


def retention(db) -> str:
    v = get_setting(db, KEY, DEFAULT)
    return v if v in CHOICES else DEFAULT


def purge_old_uploads(db) -> int:
    """Deletes uploads older than the chosen number of days. Returns how many files went."""
    v = retention(db)
    if not v.isdigit():
        return 0
    cutoff = time.time() - int(v) * 86400
    removed = 0
    for f in (settings.data_dir / "packages").glob("*/Files/*"):
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)
            removed += 1
    return removed


def purge_package(files: Path) -> None:
    shutil.rmtree(files, ignore_errors=True)
