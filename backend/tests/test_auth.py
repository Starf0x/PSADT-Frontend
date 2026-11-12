import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from app import db as dbmod
from app.config import settings


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(settings, "admin_password", "correct-horse-battery")
    monkeypatch.setattr(settings, "cookie_secure", False)
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    dbmod.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    dbmod.SessionLocal = sessionmaker(dbmod.engine, expire_on_commit=False)
    dbmod.Base.metadata.create_all(dbmod.engine)
    from app.main import app

    with TestClient(app) as c:
        yield c
    dbmod.SessionLocal = None


def login(c, pw="correct-horse-battery"):
    return c.post("/api/auth/login", json={"username": "admin", "password": pw})


def test_login_sets_httponly_cookie(client):
    r = login(client)
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert client.get("/api/auth/me").json()["username"] == "admin"


def test_unauthenticated_and_wrong_password(client):
    assert client.get("/api/auth/me").status_code == 401
    assert login(client, "fout").status_code == 401


def test_csrf_required_for_writes(client):
    csrf = login(client).json()["csrf_token"]
    assert client.post("/api/auth/logout").status_code == 403
    assert client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_lockout_after_failed_attempts(client):
    for _ in range(settings.max_failed_logins):
        login(client, "fout")
    assert login(client).status_code == 429


def test_security_headers(client):
    h = client.get("/api/health").headers
    assert "default-src 'self'" in h["content-security-policy"]
    assert h["x-frame-options"] == "DENY"
