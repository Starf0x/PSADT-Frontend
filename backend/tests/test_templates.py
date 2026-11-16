def test_template_roundtrip(authed):
    pid = authed.post("/api/packages", json={"name": "Chrome"}).json()["id"]
    data = authed.get(f"/api/packages/{pid}").json()["data"]
    data["app"]["vendor"] = "Google"
    data["install"]["main"] = [{"type": "msi", "file": "chrome.msi", "args": "/qn"}]
    assert authed.put(f"/api/packages/{pid}", json=data).status_code == 200

    r = authed.post("/api/templates", json={"name": "Browser", "description": "MSI silent", "package_id": pid})
    assert r.status_code == 201
    tid = r.json()["id"]
    assert r.json()["vendor"] == "Google" and r.json()["steps"] >= 1

    full = authed.get(f"/api/templates/{tid}").json()
    assert full["data"]["install"]["main"][0]["args"] == "/qn"

    # A template needs a new version: none, the template's own, or one that exists is refused.
    data["app"]["version"] = "1.0"
    authed.put(f"/api/packages/{pid}", json=data)
    tid2 = authed.post("/api/templates", json={"name": "Chrome 1.0", "package_id": pid}).json()["id"]
    assert authed.post("/api/packages", json={"template_id": tid2}).status_code == 422
    assert authed.post("/api/packages", json={"template_id": tid2, "version": "1.0"}).status_code == 409
    assert authed.post("/api/packages", json={"template_id": tid2, "version": "1.1"}).json()["data"]["app"]["version"] == "1.1"
    assert authed.post("/api/packages", json={"template_id": tid2, "version": " 1.1 "}).status_code == 409
    authed.delete(f"/api/templates/{tid2}")

    new = authed.post("/api/packages", json={"name": "Edge", "template_id": tid, "version": "2.0"}).json()
    assert new["name"] == "Edge" and new["data"]["app"]["name"] == "Edge"
    assert new["data"]["app"]["vendor"] == "Google"
    assert new["data"]["install"]["main"][0]["file"] == "chrome.msi"

    # Without a name the package takes the template's app name.
    same = authed.post("/api/packages", json={"template_id": tid, "version": "9.9"}).json()
    assert same["name"] == "Chrome" and same["data"]["app"]["vendor"] == "Google"
    assert authed.post("/api/packages", json={"name": " "}).status_code == 422

    # Changing the new package leaves the template alone.
    new["data"]["app"]["vendor"] = "Microsoft"
    authed.put(f"/api/packages/{new['id']}", json=new["data"])
    assert authed.get("/api/templates").json()[0]["vendor"] == "Google"

    r = authed.put(f"/api/templates/{tid}", json={"name": "Browsers", "description": ""})
    assert r.json()["name"] == "Browsers"
    assert authed.delete(f"/api/templates/{tid}").status_code == 204
    assert authed.get("/api/templates").json() == []
    assert authed.post("/api/packages", json={"name": "X", "template_id": tid, "version": "1"}).status_code == 404


def test_template_unknown_package(authed):
    assert authed.post("/api/templates", json={"name": "T", "package_id": 999}).status_code == 404



def test_uploads_get_random_names_on_disk(authed, tmp_path):
    from app import filestore
    pid = authed.post("/api/packages", json={"name": "A"}).json()["id"]
    other = authed.post("/api/packages", json={"name": "B"}).json()["id"]
    up = lambda p, body: authed.put(f"/api/packages/{p}/files/setup.exe/chunk?total={len(body)}&offset=0", content=body).json()  # noqa: E731
    assert up(pid, b"one")["name"] == "setup.exe"
    assert up(other, b"other")["name"] == "setup.exe"
    first = filestore.path(pid, "setup.exe")
    assert first.name != "setup.exe" and first.read_bytes() == b"one"
    assert filestore.path(other, "setup.exe").read_bytes() == b"other"  # other package untouched
    up(pid, b"newer")  # same name again: the name now points at the new upload
    assert filestore.path(pid, "setup.exe").read_bytes() == b"newer" and not first.exists()
    assert authed.get(f"/api/packages/{pid}/files").json() == [{"name": "setup.exe", "size": 5}]
    assert authed.delete(f"/api/packages/{pid}/files/setup.exe").status_code == 204
    assert authed.get(f"/api/packages/{pid}/files").json() == []


def test_old_files_folder_is_migrated(authed, tmp_path):
    from app import filestore
    pid = authed.post("/api/packages", json={"name": "Old"}).json()["id"]
    old = tmp_path / "packages" / str(pid) / "Files"
    old.mkdir(parents=True)
    (old / "app.msi").write_bytes(b"abc")
    assert authed.get(f"/api/packages/{pid}/files").json() == [{"name": "app.msi", "size": 3}]
    assert not old.exists() and filestore.path(pid, "app.msi").name != "app.msi"
