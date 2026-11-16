from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Package, Template, User, get_db
from ..psadt.schema import PackageData
from ..security import current_user, editor_for_writes

router = APIRouter(prefix="/api/templates", tags=["templates"], dependencies=[Depends(editor_for_writes)])


class TemplateIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    package_id: int  # the package whose configuration is saved (files are not copied)


class TemplateEdit(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


def _get(db: Session, tid: int) -> Template:
    tpl = db.get(Template, tid)
    if tpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")
    return tpl


def _out(t: Template) -> dict:
    app = t.data.get("app", {})
    steps = sum(len(t.data.get(k, {}).get(p, [])) for k in ("install", "uninstall", "repair") for p in ("pre", "main", "post"))
    return {"id": t.id, "name": t.name, "description": t.description, "app": app.get("name", ""),
            "vendor": app.get("vendor", ""), "version": app.get("version", ""), "steps": steps, "updated_at": t.updated_at.isoformat()}


@router.get("")
def list_templates(db: Session = Depends(get_db)):
    return [_out(t) for t in db.scalars(select(Template).order_by(Template.name))]


@router.get("/{tid}")
def get_template(tid: int, db: Session = Depends(get_db)):
    tpl = _get(db, tid)
    return {**_out(tpl), "data": tpl.data}


@router.post("", status_code=201)
def create_template(data: TemplateIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    pkg = db.get(Package, data.package_id)
    if pkg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package not found")
    try:
        content = PackageData.model_validate(pkg.data).model_dump()
    except ValidationError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    tpl = Template(name=data.name, description=data.description, data=content, created_by=user.id)
    db.add(tpl)
    db.commit()
    return _out(tpl)


@router.put("/{tid}")
def edit_template(tid: int, data: TemplateEdit, db: Session = Depends(get_db)):
    tpl = _get(db, tid)
    tpl.name, tpl.description = data.name, data.description
    db.commit()
    return _out(tpl)


@router.delete("/{tid}", status_code=204)
def delete_template(tid: int, db: Session = Depends(get_db)):
    db.delete(_get(db, tid))
    db.commit()
