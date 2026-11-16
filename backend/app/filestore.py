"""Uploaded files of one package.

On disk every upload gets a random name in packages/<id>/blobs/, so nothing is ever overwritten by
another upload. packages/<id>/files.json links the real file name (what the app shows and what the
export puts in Files/) to that random name. Uploading the same real name again in the same package
points the name at the new upload and only then removes the old one.
"""
import hashlib
import json
import os
import secrets
import shutil
import threading
from pathlib import Path

from .config import settings

_lock = threading.Lock()


def package_dir(pid: int) -> Path:
    return settings.data_dir / "packages" / str(int(pid))


def blobs_dir(pid: int) -> Path:
    return package_dir(pid) / "blobs"


def _index_path(pid: int) -> Path:
    return package_dir(pid) / "files.json"


def _read(pid: int) -> dict[str, str]:
    try:
        return json.loads(_index_path(pid).read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _write(pid: int, index: dict[str, str]) -> None:
    path = _index_path(pid)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(index, indent=1, sort_keys=True), "utf-8")
    tmp.replace(path)


def _migrate(pid: int) -> None:
    """Older versions kept files under their real name in packages/<id>/Files; move them over once."""
    old = package_dir(pid) / "Files"
    if not old.is_dir():
        return
    index = _read(pid)
    blobs_dir(pid).mkdir(parents=True, exist_ok=True)
    for f in sorted(old.iterdir()):
        if f.is_file() and not f.name.startswith(".") and f.name not in index:
            blob = secrets.token_hex(16)
            f.replace(blobs_dir(pid) / blob)
            index[f.name] = blob
    _write(pid, index)
    shutil.rmtree(old, ignore_errors=True)


def entries(pid: int) -> dict[str, Path]:
    """Real name -> file on disk, only for files that still exist (retention may have removed some)."""
    with _lock:
        _migrate(pid)
        index = _read(pid)
        found = {name: blobs_dir(pid) / blob for name, blob in index.items() if (blobs_dir(pid) / blob).is_file()}
        if len(found) != len(index):
            _write(pid, {n: index[n] for n in found})
        return dict(sorted(found.items(), key=lambda kv: kv[0].lower()))


def path(pid: int, name: str) -> Path | None:
    return entries(pid).get(name)


def part_path(pid: int, name: str) -> Path:
    """Where a chunked upload of this real name collects its pieces (random-looking, fixed per name)."""
    blobs_dir(pid).mkdir(parents=True, exist_ok=True)
    return blobs_dir(pid) / (".part-" + hashlib.sha256(name.encode()).hexdigest()[:32])


def add(pid: int, name: str, src: Path) -> None:
    """Store a finished upload under a new random name and link the real name to it."""
    with _lock:
        _migrate(pid)
        blob = secrets.token_hex(16)
        blobs_dir(pid).mkdir(parents=True, exist_ok=True)
        src.replace(blobs_dir(pid) / blob)
        index = _read(pid)
        old = index.get(name)
        index[name] = blob
        _write(pid, index)
        if old:
            (blobs_dir(pid) / old).unlink(missing_ok=True)


def remove(pid: int, name: str) -> bool:
    with _lock:
        _migrate(pid)
        index = _read(pid)
        blob = index.pop(name, None)
        if blob is None:
            return False
        _write(pid, index)
        (blobs_dir(pid) / blob).unlink(missing_ok=True)
        return True


def remove_all(pid: int) -> None:
    """Drop every uploaded file of a package (the package itself stays)."""
    with _lock:
        shutil.rmtree(blobs_dir(pid), ignore_errors=True)
        shutil.rmtree(package_dir(pid) / "Files", ignore_errors=True)
        try:
            os.unlink(_index_path(pid))
        except OSError:
            pass
