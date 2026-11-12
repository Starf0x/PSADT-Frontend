from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..db import User, UserSession, get_db
from ..security import hash_password, require_admin

router = APIRouter(prefix="/api/users", tags=["users"], dependencies=[Depends(require_admin)])

Role = Literal["admin", "editor", "viewer"]
Username = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9._@-]+$")


class UserIn(BaseModel):
    username: str = Username
    password: str = Field(min_length=12, max_length=256)
    role: Role = "editor"


class UserUpdate(BaseModel):
    role: Role | None = None
    password: str | None = Field(default=None, min_length=12, max_length=256)
    unlock: bool = False


def _out(u: User) -> dict:
    return {"id": u.id, "username": u.username, "role": u.role,
            "locked": u.locked_until is not None, "created_at": u.created_at.isoformat()}


def _get(db: Session, uid: int) -> User:
    u = db.get(User, uid)
    if u is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return u


def _admins(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.role == "admin"))


def _revoke(db: Session, uid: int) -> None:
    db.execute(delete(UserSession).where(UserSession.user_id == uid))


@router.get("")
def list_users(db: Session = Depends(get_db)):
    return [_out(u) for u in db.scalars(select(User).order_by(User.username))]


@router.post("", status_code=201)
def create_user(data: UserIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == data.username)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    u = User(username=data.username, password_hash=hash_password(data.password), role=data.role)
    db.add(u)
    db.commit()
    return _out(u)


@router.put("/{uid}")
def update_user(uid: int, data: UserUpdate, db: Session = Depends(get_db)):
    u = _get(db, uid)
    if data.role and data.role != u.role:
        if u.role == "admin" and _admins(db) <= 1:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "At least one administrator must remain")
        u.role = data.role
        _revoke(db, u.id)
    if data.password:
        u.password_hash = hash_password(data.password)
        _revoke(db, u.id)
    if data.unlock:
        u.locked_until = None
        u.failed_logins = 0
    db.commit()
    return _out(u)


@router.delete("/{uid}", status_code=204)
def delete_user(uid: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    u = _get(db, uid)
    if u.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot delete yourself")
    _revoke(db, u.id)
    db.delete(u)
    db.commit()
