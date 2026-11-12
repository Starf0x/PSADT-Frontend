from collections.abc import Iterator
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .config import settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="admin")
    language: Mapped[str] = mapped_column(String(8), default="en", server_default="en")
    # Full name shown in the app and used as script author; username is only for signing in.
    display_name: Mapped[str] = mapped_column(String(100), default="", server_default="")
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserSession(Base):
    __tablename__ = "sessions"
    # sha256 van het cookie-token; het token zelf wordt nooit opgeslagen
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    csrf_token: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Package(Base):
    __tablename__ = "packages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    data: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Snippet(Base):
    __tablename__ = "snippets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    step: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Export(Base):
    """One row per successful download of a package (.zip or .intunewin), for the counters."""
    __tablename__ = "exports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    package_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    package_name: Mapped[str] = mapped_column(String(100))
    fmt: Mapped[str] = mapped_column(String(16))
    app_version: Mapped[str] = mapped_column(String(50), default="")  # a package counts once per version
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Setting(Base):
    """Simple key/value settings that admins change in the app (e.g. upload retention)."""
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))


def get_setting(db: Session, key: str, default: str) -> str:
    row = db.get(Setting, key)
    return row.value if row else default


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.get(Setting, key)
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))
    db.commit()


engine = None
SessionLocal: sessionmaker | None = None


def init_db(url: str | None = None) -> None:
    global engine, SessionLocal
    if url is None:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        url = settings.db_url
    engine = create_engine(url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    _add_missing_columns()


def _add_missing_columns() -> None:
    """create_all makes new tables but never new columns; add the few we added later."""
    from sqlalchemy import inspect, text

    added = {
        "users": {"language": "VARCHAR(8) NOT NULL DEFAULT 'en'", "display_name": "VARCHAR(100) NOT NULL DEFAULT ''"},
        "exports": {"app_version": "VARCHAR(50) NOT NULL DEFAULT ''"},
    }
    with engine.begin() as con:
        for table, cols in added.items():
            have = {c["name"] for c in inspect(con).get_columns(table)}
            for name, sql in cols.items():
                if name not in have:
                    con.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sql}"))


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db
