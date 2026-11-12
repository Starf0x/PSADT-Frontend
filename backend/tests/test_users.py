import pytest
from fastapi.testclient import TestClient


def _login(client, user, pw):
    r = client.post("/api/auth/login", json={"username": user, "password": pw})
    assert r.status_code == 200, r.text
    client.headers["X-CSRF-Token"] = r.json()["csrf_token"]


@pytest.fixture()
def other(client):
    """Tweede client met eigen cookies, voor een andere gebruiker."""
    from app.main import app

    with TestClient(app) as c:
        yield c


def test_admin_manages_users(authed, other):
    r = authed.post("/api/users", json={"username": "piet", "password": "lang-genoeg-123", "role": "viewer"})
    assert r.status_code == 201
    uid = r.json()["id"]
    assert authed.post("/api/users", json={"username": "piet", "password": "lang-genoeg-123"}).status_code == 409
    assert authed.post("/api/users", json={"username": "kort", "password": "kort"}).status_code == 422

    _login(other, "piet", "lang-genoeg-123")
    assert other.get("/api/packages").status_code == 200
    assert other.post("/api/packages", json={"name": "X"}).status_code == 403
    assert other.get("/api/users").status_code == 403

    # rolwijziging trekt sessies in
    assert authed.put(f"/api/users/{uid}", json={"role": "editor"}).status_code == 200
    assert other.get("/api/auth/me").status_code == 401
    _login(other, "piet", "lang-genoeg-123")
    assert other.post("/api/packages", json={"name": "X"}).status_code == 201

    assert authed.delete(f"/api/users/{uid}").status_code == 204
    assert other.get("/api/auth/me").status_code == 401


def test_last_admin_protected(authed):
    me = next(u for u in authed.get("/api/users").json() if u["username"] == "admin")
    assert authed.put(f"/api/users/{me['id']}", json={"role": "viewer"}).status_code == 400
    assert authed.delete(f"/api/users/{me['id']}").status_code == 400


def test_viewer_can_check_and_export_but_not_write(authed, other):
    pid = authed.post("/api/packages", json={"name": "P"}).json()["id"]
    authed.post("/api/users", json={"username": "kijker", "password": "lang-genoeg-123", "role": "viewer"})
    _login(other, "kijker", "lang-genoeg-123")
    assert other.get(f"/api/packages/{pid}/script").status_code == 200
    assert other.post(f"/api/packages/{pid}/check").status_code == 200
    assert other.delete(f"/api/packages/{pid}").status_code == 403
    assert other.post("/api/snippets", json={"name": "s", "step": {"type": "progress"}}).status_code == 403
