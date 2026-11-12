import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .config import settings
from .db import User, UserSession, get_db, utcnow

COOKIE_NAME = "psadt_session"
CSRF_HEADER = "X-CSRF-Token"
_ph = PasswordHasher()
# Dummy-hash zodat onbekende gebruikers even lang duren (geen user-enumeratie via timing)
_DUMMY_HASH = _ph.hash(secrets.token_hex(16))


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return _ph.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except VerificationError:
        return False


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: User) -> tuple[str, UserSession]:
    token = secrets.token_urlsafe(32)
    sess = UserSession(
        id=_digest(token),
        user_id=user.id,
        csrf_token=secrets.token_urlsafe(32),
        expires_at=utcnow() + timedelta(hours=settings.session_hours),
    )
    db.execute(delete(UserSession).where(UserSession.expires_at < utcnow()))
    db.add(sess)
    db.commit()
    return token, sess


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def current_session(request: Request, db: Session = Depends(get_db)) -> UserSession:
    token = request.cookies.get(COOKIE_NAME)
    sess = db.get(UserSession, _digest(token)) if token else None
    if sess is None or _aware(sess.expires_at) < utcnow():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        sent = request.headers.get(CSRF_HEADER, "")
        if not secrets.compare_digest(sent, sess.csrf_token):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid CSRF token")
    return sess


def current_user(sess: UserSession = Depends(current_session), db: Session = Depends(get_db)) -> User:
    user = db.get(User, sess.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    return user


ROLES = ("admin", "editor", "viewer")
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrators only")
    return user


def editor_for_writes(request: Request, user: User = Depends(current_user)) -> User:
    """Viewers mogen alles lezen, exporteren en de syntax controleren, maar niets wijzigen."""
    if user.role == "viewer" and request.method in WRITE_METHODS and not request.url.path.endswith("/check"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You have read-only access")
    return user


def ensure_admin(db: Session) -> None:
    if db.scalar(select(User).limit(1)) is not None:
        return
    password = settings.admin_password
    if not password:
        password = secrets.token_urlsafe(16)
        print(f"[psadt-frontend] First start: admin password for '{settings.admin_username}': {password}", flush=True)
    db.add(User(username=settings.admin_username, display_name="Administrator", password_hash=hash_password(password), role="admin"))
    db.commit()
