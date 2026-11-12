from app.routers import system


def test_update_status_and_request(authed, monkeypatch, tmp_path):
    monkeypatch.setattr(system, "newest_release", lambda: ("v9.9.9", None))
    monkeypatch.setattr(system, "install_method", lambda: "docker")
    r = authed.get("/api/system/update").json()
    assert r["newest"] == "9.9.9" and r["newer"] is True and r["install"] == "docker"
    assert authed.post("/api/system/update").status_code == 409

    monkeypatch.setattr(system, "install_method", lambda: "lxc")
    assert authed.post("/api/system/update").status_code == 202
    assert (tmp_path / "update-wanted").exists()
    assert authed.get("/api/system/update").json()["pending"] is True


def test_update_admin_only(authed):
    authed.post("/api/users", json={"username": "viewer1", "password": "a-long-password-1", "role": "viewer"})
    authed.post("/api/auth/logout")
    csrf = authed.post("/api/auth/login", json={"username": "viewer1", "password": "a-long-password-1"}).json()["csrf_token"]
    authed.headers["X-CSRF-Token"] = csrf
    assert authed.get("/api/system/update").status_code == 403


def test_version_compare():
    assert system._version_tuple("v0.1.22") > system._version_tuple("0.1.11")
    assert system._version_tuple("v0.1.0") > system._version_tuple("0.0.94")
