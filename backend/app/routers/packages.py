import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import re

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import Package, User, get_db
from ..psadt.detection import generate_detection
from ..psadt.export import build_intunewin, build_zip, to_windows
from ..psadt.generator import generate
from ..psadt.schema import FILE_RE, PackageData, default_package
from ..security import current_user

router = APIRouter(prefix="/api/packages", tags=["packages"], dependencies=[Depends(current_user)])

ALLOWED_EXT = {".msi", ".msp", ".mst", ".exe", ".zip", ".cab", ".ps1", ".psm1", ".reg", ".xml", ".ini", ".cfg",
               ".json", ".txt", ".bat", ".cmd", ".vbs", ".ico", ".png", ".lnk", ".config"}
CHECK_PS1 = Path(__file__).resolve().parents[1] / "psadt" / "check.ps1"


class NewPackage(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def _get(db: Session, pid: int) -> Package:
    pkg = db.get(Package, pid)
    if pkg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pakket niet gevonden")
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
    pkg = Package(name=data.name, data=default_package(data.name).model_dump(), created_by=user.id)
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
def delete_package(pid: int, db: Session = Depends(get_db)):
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
def export(pid: int, fmt: str, tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if fmt not in ("zip", "intunewin"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Onbekend formaat")
    pkg = _get(db, pid)
    script = _script(pkg)
    if not settings.toolkit_zip.is_file():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            f"PSADT-toolkit niet gevonden op {settings.toolkit_zip}; zie README")
    tmp = settings.data_dir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=tmp, suffix=".zip")
    os.close(fd)
    zip_path = Path(name)
    build_zip(settings.toolkit_zip, script, files_dir(pid), zip_path)
    if fmt == "zip":
        tasks.add_task(_cleanup, zip_path)
        return FileResponse(zip_path, filename=f"{_slug(pkg)}.zip", media_type="application/zip")
    out = zip_path.with_suffix(".intunewin")
    build_intunewin(zip_path, out)
    zip_path.unlink()
    tasks.add_task(_cleanup, out)
    return FileResponse(out, filename=f"{_slug(pkg)}.intunewin", media_type="application/octet-stream")


@router.get("/{pid}/script")
def get_script(pid: int, download: bool = False, db: Session = Depends(get_db)):
    text = _script(_get(db, pid))
    if not download:
        return Response(text, media_type="text/plain; charset=utf-8")
    return Response(to_windows(text), media_type="application/octet-stream",
                    headers={"Content-Disposition": 'attachment; filename="Invoke-AppDeployToolkit.ps1"'})


@router.post("/{pid}/check")
def check_script(pid: int, db: Session = Depends(get_db)):
    text = _script(_get(db, pid))
    if shutil.which(settings.pwsh_path) is None:
        return {"available": False, "errors": []}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "script.ps1"
        path.write_text(text, encoding="utf-8")
        res = subprocess.run(
            [settings.pwsh_path, "-NoProfile", "-NonInteractive", "-File", str(CHECK_PS1), "-Path", str(path)],
            capture_output=True, text=True, timeout=60,
        )
    errors = [line for line in res.stdout.splitlines() if line.strip()]
    if res.returncode != 0 and not errors:
        errors = [res.stderr.strip()[:500] or "Onbekende fout bij controle"]
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
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bestandsnaam of -type niet toegestaan")
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
                    raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Bestand is te groot")
                out.write(chunk)
        tmp.replace(d / name)
    finally:
        tmp.unlink(missing_ok=True)
    return {"name": name, "size": size}


@router.delete("/{pid}/files/{name}", status_code=204)
def delete_file(pid: int, name: str, db: Session = Depends(get_db)):
    _get(db, pid)
    if not FILE_RE.match(name) or name in (".", ".."):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ongeldige bestandsnaam")
    path = files_dir(pid) / name
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bestand niet gevonden")
    path.unlink()
