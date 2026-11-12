import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import db as dbmod
from app.config import settings


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "admin_password", "correct-horse-battery")
    monkeypatch.setattr(settings, "cookie_secure", False)
    monkeypatch.setenv("PSADT_USAGE_OPTOUT", "1")  # tests never phone home
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    dbmod.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    dbmod.SessionLocal = sessionmaker(dbmod.engine, expire_on_commit=False)
    dbmod.Base.metadata.create_all(dbmod.engine)
    from app.main import app

    with TestClient(app) as c:
        yield c
    dbmod.SessionLocal = None


@pytest.fixture()
def authed(client):
    csrf = client.post("/api/auth/login", json={"username": "admin", "password": "correct-horse-battery"}).json()["csrf_token"]
    client.headers["X-CSRF-Token"] = csrf
    return client
