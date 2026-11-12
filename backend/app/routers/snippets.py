from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Snippet, User, get_db
from ..psadt.schema import Step
from ..security import current_user, editor_for_writes

router = APIRouter(prefix="/api/snippets", tags=["snippets"], dependencies=[Depends(editor_for_writes)])


class SnippetIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    step: Step


def _out(s: Snippet) -> dict:
    return {"id": s.id, "name": s.name, "step": s.step}


@router.get("")
def list_snippets(db: Session = Depends(get_db)):
    return [_out(s) for s in db.scalars(select(Snippet).order_by(Snippet.name))]


@router.post("", status_code=201)
def create_snippet(data: SnippetIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    s = Snippet(name=data.name, step=data.step.model_dump(), created_by=user.id)
    db.add(s)
    db.commit()
    return _out(s)


@router.delete("/{sid}", status_code=204)
def delete_snippet(sid: int, db: Session = Depends(get_db)):
    s = db.get(Snippet, sid)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Snippet not found")
    db.delete(s)
    db.commit()
