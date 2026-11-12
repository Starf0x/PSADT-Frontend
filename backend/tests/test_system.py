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
    authed.post("/api/users", json={"username": "viewer1", "display_name": "Viewer1 Test", "password": "a-long-password-1", "role": "viewer"})
    authed.post("/api/auth/logout")
    csrf = authed.post("/api/auth/login", json={"username": "viewer1", "password": "a-long-password-1"}).json()["csrf_token"]
    authed.headers["X-CSRF-Token"] = csrf
    assert authed.get("/api/system/update").status_code == 403


def test_version_compare():
    assert system._version_tuple("v0.1.22") > system._version_tuple("0.1.11")
    assert system._version_tuple("v0.1.0") > system._version_tuple("0.0.94")


def test_retention_setting_and_purge(authed, tmp_path):
    import os
    import time

    assert authed.get("/api/system/settings").json()["upload_retention"] == "forever"
    pid = authed.post("/api/packages", json={"name": "R"}).json()["id"]
    authed.post(f"/api/packages/{pid}/files", files={"file": ("old.msi", b"x")})
    authed.post(f"/api/packages/{pid}/files", files={"file": ("new.msi", b"x")})
    old = tmp_path / "packages" / str(pid) / "Files" / "old.msi"
    past = time.time() - 8 * 86400
    os.utime(old, (past, past))
    assert authed.put("/api/system/settings", json={"upload_retention": "bogus"}).status_code == 422
    r = authed.put("/api/system/settings", json={"upload_retention": "7"}).json()
    assert r["removed"] == 1
    assert [f["name"] for f in authed.get(f"/api/packages/{pid}/files").json()] == ["new.msi"]


def test_release_notes(authed, monkeypatch):
    text = "# x\n\n## 0.9.0\n- Not released yet\n\n## 0.5.0\n- Big thing\n- Small thing\n\n## 0.1.0\n- Old\n"
    monkeypatch.setattr(system, "_notes_text", lambda lang: text)
    monkeypatch.setattr(system, "current_version", lambda: "0.1.0")
    monkeypatch.setattr(system, "newest_release", lambda: ("v0.5.0", None))
    r = authed.get("/api/system/release-notes?lang=nl").json()
    assert r["newer"] is True and r["notes"] == [{"version": "0.5.0", "items": ["Big thing", "Small thing"]}]
    monkeypatch.setattr(system, "newest_release", lambda: ("v0.1.0", None))
    r = authed.get("/api/system/release-notes").json()
    assert r["newer"] is False and r["notes"][0]["items"] == ["Old"]


def test_shipped_release_notes_cover_current_version():
    from app.main import APP_VERSION

    for lang in ("en", "nl", "de"):
        versions = [n["version"] for n in system.parse_notes((system.NOTES_DIR / f"{lang}.md").read_text())]
        assert APP_VERSION in versions, f"release-notes/{lang}.md has no section for {APP_VERSION}"
