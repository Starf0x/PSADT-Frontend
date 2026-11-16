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

    new = authed.post("/api/packages", json={"name": "Edge", "template_id": tid}).json()
    assert new["name"] == "Edge" and new["data"]["app"]["name"] == "Edge"
    assert new["data"]["app"]["vendor"] == "Google"
    assert new["data"]["install"]["main"][0]["file"] == "chrome.msi"

    # Without a name the package takes the template's app name.
    same = authed.post("/api/packages", json={"template_id": tid}).json()
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
    assert authed.post("/api/packages", json={"name": "X", "template_id": tid}).status_code == 404


def test_template_unknown_package(authed):
    assert authed.post("/api/templates", json={"name": "T", "package_id": 999}).status_code == 404
