from typing import Literal

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import User, UserSession, get_db, utcnow
from ..security import (
    COOKIE_NAME,
    _aware,
    create_session,
    current_session,
    current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class PasswordIn(BaseModel):
    current_password: str = Field(max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


def _me(user: User, sess: UserSession) -> dict:
    return {"username": user.username, "role": user.role, "language": user.language or "en", "csrf_token": sess.csrf_token}


@router.post("/login")
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == data.username))
    if user and user.locked_until and _aware(user.locked_until) > utcnow():
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Account temporarily locked")
    if not verify_password(data.password, user.password_hash if user else None):
        if user:
            user.failed_logins += 1
            if user.failed_logins >= settings.max_failed_logins:
                user.locked_until = utcnow() + timedelta(minutes=settings.lockout_minutes)
                user.failed_logins = 0
            db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password")
    user.failed_logins = 0
    user.locked_until = None
    token, sess = create_session(db, user)
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.session_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
    )
    return _me(user, sess)


@router.post("/logout", status_code=204)
def logout(response: Response, sess: UserSession = Depends(current_session), db: Session = Depends(get_db)):
    db.execute(delete(UserSession).where(UserSession.id == sess.id))
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me")
def me(user: User = Depends(current_user), sess: UserSession = Depends(current_session)):
    return _me(user, sess)


@router.post("/password", status_code=204)
def change_password(
    data: PasswordIn,
    user: User = Depends(current_user),
    sess: UserSession = Depends(current_session),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    # Alle andere sessies van deze gebruiker intrekken
    db.execute(delete(UserSession).where(UserSession.user_id == user.id, UserSession.id != sess.id))
    db.commit()


class LanguageIn(BaseModel):
    language: Literal["en", "nl", "de"]


@router.put("/language", status_code=204)
def set_language(data: LanguageIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Each user picks their own UI language; it follows them to every device."""
    user.language = data.language
    db.commit()
