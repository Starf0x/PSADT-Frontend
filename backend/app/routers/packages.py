import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import Package, User, get_db
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


def _script(pkg: Package) -> str:
    try:
        return generate(PackageData.model_validate(pkg.data))
    except (ValidationError, ValueError) as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))


@router.get("/{pid}/script")
def get_script(pid: int, download: bool = False, db: Session = Depends(get_db)):
    text = _script(_get(db, pid))
    if not download:
        return Response(text, media_type="text/plain; charset=utf-8")
    # Windows PowerShell 5.1 heeft een BOM nodig voor UTF-8; regeleinden CRLF
    body = "\ufeff" + text.replace("\n", "\r\n")
    return Response(body.encode("utf-8"), media_type="application/octet-stream",
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
