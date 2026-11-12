from app.config import settings


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


def test_language_per_user(authed):
    assert authed.get("/api/auth/me").json()["language"] == "en"
    assert authed.put("/api/auth/language", json={"language": "fr"}).status_code == 422
    assert authed.put("/api/auth/language", json={"language": "de"}).status_code == 204
    assert authed.get("/api/auth/me").json()["language"] == "de"
    authed.post("/api/users", json={"username": "other", "password": "a-long-password-1"})
    authed.post("/api/auth/logout")
    other = authed.post("/api/auth/login", json={"username": "other", "password": "a-long-password-1"}).json()
    assert other["language"] == "en"
