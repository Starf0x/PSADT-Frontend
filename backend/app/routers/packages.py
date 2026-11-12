import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

import re

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import Export, Package, User, get_db, get_setting
from ..psadt.detection import generate_detection
from ..psadt.export import build_intunewin, build_zip, to_windows
from ..psadt.generator import generate
from ..psadt.msi import read_properties
from ..psadt.schema import FILE_RE, PackageData, default_package
from ..psadt.validate import validate_package
from ..retention import purge_package, retention
from ..security import current_user, editor_for_writes, require_admin

router = APIRouter(prefix="/api/packages", tags=["packages"], dependencies=[Depends(editor_for_writes)])

ALLOWED_EXT = {".msi", ".msp", ".mst", ".exe", ".zip", ".cab", ".ps1", ".psm1", ".reg", ".xml", ".ini", ".cfg",
               ".json", ".txt", ".bat", ".cmd", ".vbs", ".ico", ".png", ".lnk", ".config",
               ".msix", ".msixbundle", ".appx", ".appxbundle", ".cer"}
CHECK_LINE = re.compile(r"^\d+:\d+ ")
CHECK_PS1 = Path(__file__).resolve().parents[1] / "psadt" / "check.ps1"


class NewPackage(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def _get(db: Session, pid: int) -> Package:
    pkg = db.get(Package, pid)
    if pkg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package not found")
    return pkg


def files_dir(pid: int) -> Path:
    return settings.data_dir / "packages" / str(int(pid)) / "Files"


def _summary(p: Package) -> dict:
    app = p.data.get("app", {})
    return {"id": p.id, "name": p.name, "vendor": app.get("vendor", ""), "version": app.get("version", ""),
            "updated_at": p.updated_at.isoformat()}


@router.get("")
def list_packages(db: Session = Depends(get_db)):
    return [_summary(p) for p in db.scalars(select(Package).order_by(Package.updated_at.desc()))]


@router.post("", status_code=201)
def create_package(data: NewPackage, db: Session = Depends(get_db), user: User = Depends(current_user)):
    content = default_package(data.name)
    content.app.author = (user.display_name or user.username)[:100]  # the signed-in user, by full name
    pkg = Package(name=data.name, data=content.model_dump(), created_by=user.id)
    db.add(pkg)
    db.commit()
    return {"id": pkg.id, "name": pkg.name, "data": pkg.data}


@router.get("/{pid}")
def get_package(pid: int, db: Session = Depends(get_db)):
    pkg = _get(db, pid)
    return {"id": pkg.id, "name": pkg.name, "data": pkg.data}


@router.put("/{pid}")
def update_package(pid: int, data: PackageData, db: Session = Depends(get_db)):
    pkg = _get(db, pid)
    pkg.data = data.model_dump()
    pkg.name = data.app.name
    db.commit()
    return {"id": pkg.id, "name": pkg.name, "data": pkg.data}


@router.delete("/{pid}", status_code=204)
def delete_package(pid: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    pkg = _get(db, pid)
    db.delete(pkg)
    db.commit()
    shutil.rmtree(files_dir(pid).parent, ignore_errors=True)


def _data(pkg: Package) -> PackageData:
    try:
        return PackageData.model_validate(pkg.data)
    except ValidationError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))


def _script(pkg: Package) -> str:
    try:
        return generate(_data(pkg))
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))


def _slug(pkg: Package) -> str:
    a = pkg.data.get("app", {})
    raw = "_".join(x for x in (a.get("vendor"), a.get("name"), a.get("version")) if x) or f"package{pkg.id}"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("_")[:100] or f"package{pkg.id}"


def _cleanup(*paths: Path) -> None:
    for p in paths:
        p.unlink(missing_ok=True)


@router.get("/{pid}/detection")
def get_detection(pid: int, download: bool = False, db: Session = Depends(get_db)):
    pkg = _get(db, pid)
    text = generate_detection(_data(pkg))
    if not download:
        return Response(text, media_type="text/plain; charset=utf-8")
    return Response(to_windows(text), media_type="application/octet-stream",
                    headers={"Content-Disposition": f'attachment; filename="Detect_{_slug(pkg)}.ps1"'})


@router.get("/{pid}/export/{fmt}")
def export(pid: int, fmt: str, tasks: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if fmt not in ("zip", "intunewin"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown format")
    pkg = _get(db, pid)
    script = _script(pkg)
    if not settings.toolkit_zip.is_file():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            f"PSADT toolkit not found at {settings.toolkit_zip}; see README")
    items, _ = validate_package(pkg.data, _uploaded(pid), True)
    errors = [i["text"].format(**i["vars"]) for i in items if i["level"] == "error"]
    if errors:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Fix the problems shown in the check first: " + "; ".join(errors))
    after_export = retention(db) == "export"
    tmp = settings.data_dir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=tmp, suffix=".zip")
    os.close(fd)
    zip_path = Path(name)
    log_path = pkg.data.get("app", {}).get("log_path") or get_setting(db, "log_path", "")
    build_zip(settings.toolkit_zip, script, files_dir(pid), zip_path, log_path)
    if after_export:
        tasks.add_task(purge_package, files_dir(pid))
    if fmt == "zip":
        _count(db, pkg, user, fmt)
        tasks.add_task(_cleanup, zip_path)
        return FileResponse(zip_path, filename=f"{_slug(pkg)}.zip", media_type="application/zip")
    out = zip_path.with_suffix(".intunewin")
    build_intunewin(zip_path, out)
    zip_path.unlink()
    _count(db, pkg, user, fmt)
    tasks.add_task(_cleanup, out)
    return FileResponse(out, filename=f"{_slug(pkg)}.intunewin", media_type="application/octet-stream")


def _count(db: Session, pkg: Package, user: User, fmt: str) -> None:
    version = str(pkg.data.get("app", {}).get("version") or "")[:50]
    db.add(Export(user_id=user.id, package_id=pkg.id, package_name=pkg.name[:100], fmt=fmt, app_version=version))
    db.commit()


@router.get("/{pid}/script")
def get_script(pid: int, download: bool = False, db: Session = Depends(get_db)):
    text = _script(_get(db, pid))
    if not download:
        return Response(text, media_type="text/plain; charset=utf-8")
    return Response(to_windows(text), media_type="application/octet-stream",
                    headers={"Content-Disposition": 'attachment; filename="Invoke-AppDeployToolkit.ps1"'})


def _uploaded(pid: int) -> set[str]:
    d = files_dir(pid)
    return {f.name for f in d.iterdir() if f.is_file()} if d.exists() else set()


@router.get("/{pid}/validate")
def validate(pid: int, db: Session = Depends(get_db)):
    """Everything that is checked before a download: settings, files, toolkit and syntax."""
    pkg = _get(db, pid)
    items, script = validate_package(pkg.data, _uploaded(pid), settings.toolkit_zip.is_file())
    syntax = _syntax(script) if script else {"available": False, "errors": []}
    for err in syntax["errors"]:
        items.append({"level": "error", "text": "PowerShell syntax error: {msg}", "vars": {"msg": err}})
    if syntax.get("failed"):
        items.append({"level": "warning", "vars": {},
                      "text": "The script could not be checked, because PowerShell did not start on the server. This is a server problem, not a mistake in your package."})
    return {"ok": not any(i["level"] == "error" for i in items), "items": items,
            "syntax_checked": syntax["available"], "retention": retention(db)}


@router.post("/{pid}/check")
def check_script(pid: int, db: Session = Depends(get_db)):
    return _syntax(_script(_get(db, pid)))


def _syntax(text: str) -> dict:
    if shutil.which(settings.pwsh_path) is None:
        return {"available": False, "errors": []}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "script.ps1"
        path.write_text(text, encoding="utf-8")
        # PowerShell writes a cache in $HOME on start; the app's home (/opt/psadt-frontend on LXC)
        # is read-only, so give it a throwaway home.
        env = {**os.environ, "HOME": tmp, "XDG_CACHE_HOME": tmp, "XDG_DATA_HOME": tmp, "XDG_CONFIG_HOME": tmp,
               "DOTNET_CLI_HOME": tmp, "POWERSHELL_TELEMETRY_OPTOUT": "1", "POWERSHELL_UPDATECHECK": "Off"}
        try:
            res = subprocess.run(
                [settings.pwsh_path, "-NoProfile", "-NonInteractive", "-File", str(CHECK_PS1), "-Path", str(path)],
                capture_output=True, text=True, timeout=60, env=env,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            return {"available": True, "errors": [], "failed": str(e)[:2000]}
    lines = [line for line in res.stdout.splitlines() if line.strip()]
    errors = [line for line in lines if CHECK_LINE.match(line)]
    if res.returncode != 0 or len(errors) != len(lines):
        # PowerShell itself did not run properly: a server problem, not an error in the package.
        return {"available": True, "errors": [], "failed": (res.stderr or res.stdout).strip()[:2000] or f"exit code {res.returncode}"}
    return {"available": True, "errors": errors}


@router.get("/{pid}/files")
def list_files(pid: int, db: Session = Depends(get_db)):
    _get(db, pid)
    d = files_dir(pid)
    if not d.exists():
        return []
    return [{"name": f.name, "size": f.stat().st_size} for f in sorted(d.iterdir()) if f.is_file()]


@router.post("/{pid}/files", status_code=201)
async def upload_file(pid: int, file: UploadFile, db: Session = Depends(get_db)):
    _get(db, pid)
    name = Path(file.filename or "").name
    if not FILE_RE.match(name) or name in (".", "..") or Path(name).suffix.lower() not in ALLOWED_EXT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File name or type not allowed")
    d = files_dir(pid)
    d.mkdir(parents=True, exist_ok=True)
    limit = settings.max_upload_mb * 1024 * 1024
    tmp = d / f".{name}.part"
    size = 0
    try:
        with tmp.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File is too large")
                out.write(chunk)
        tmp.replace(d / name)
    finally:
        tmp.unlink(missing_ok=True)
    return {"name": name, "size": size}


CHUNK_MAX = 16 * 1024 * 1024


@router.put("/{pid}/files/{name}/chunk")
async def upload_chunk(pid: int, name: str, offset: int, total: int, request: Request, db: Session = Depends(get_db)):
    """Upload a file in pieces, so a reverse proxy with a body-size limit (Zoraxy, Cloudflare...) never sees a big request.

    Pieces must arrive in order: offset is where this piece starts. The file appears once offset + piece = total.
    """
    _get(db, pid)
    if not FILE_RE.match(name) or name in (".", "..") or Path(name).suffix.lower() not in ALLOWED_EXT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File name or type not allowed")
    if total < 0 or total > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File is too large")
    d = files_dir(pid)
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / f".{name}.part"
    have = tmp.stat().st_size if offset and tmp.exists() else 0
    if offset != have:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Expected offset {have}")
    size = offset
    with tmp.open("ab" if offset else "wb") as out:
        async for chunk in request.stream():
            size += len(chunk)
            if size - offset > CHUNK_MAX or size > total:
                out.truncate(offset)
                raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Piece is too large")
            out.write(chunk)
    done = size == total
    if done:
        tmp.replace(d / name)
    return {"name": name, "size": size, "done": done}


@router.get("/{pid}/files/{name}/msi")
def msi_properties(pid: int, name: str, db: Session = Depends(get_db)):
    """ProductCode, version, name and manufacturer read from an uploaded MSI."""
    _get(db, pid)
    if not FILE_RE.match(name) or name in (".", "..") or not name.lower().endswith(".msi"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid file name")
    path = files_dir(pid) / name
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found")
    try:
        return read_properties(path)
    except (ValueError, OSError, struct.error):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "This is not a valid MSI file")


@router.delete("/{pid}/files/{name}", status_code=204)
def delete_file(pid: int, name: str, db: Session = Depends(get_db)):
    _get(db, pid)
    if not FILE_RE.match(name) or name in (".", ".."):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid file name")
    path = files_dir(pid) / name
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found")
    path.unlink()
