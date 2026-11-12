from datetime import date

from app.psadt.generator import generate, q
from app.psadt.schema import MsiStep, PackageData, default_package


def test_quote_escapes_single_and_smart_quotes():
    assert q("it's") == "'it''s'"
    assert q("a\u2019b") == "'a\u2019\u2019b'"


def test_generate_contains_template_parts():
    d = default_package("Demo")
    d.app.vendor = "Acme"
    d.app.processes_to_close = ["chrome"]
    d.install.main.append(MsiStep(type="msi", file="setup.msi", args="ALLUSERS=1"))
    d = PackageData.model_validate(d.model_dump())
    s = generate(d, date(2026, 1, 1))
    assert "AppName = 'Demo'" in s and "AppProcessesToClose = @('chrome')" in s
    assert 'Start-ADTMsiProcess -Action Install -FilePath "$($adtSession.DirFiles)\\setup.msi" -AdditionalArgumentList \'ALLUSERS=1\'' in s
    assert "function Uninstall-ADTDeployment" in s and "Open-ADTSession" in s
    assert "$PSScriptRoot\\PSAppDeployToolkit\\PSAppDeployToolkit.psd1" in s


def test_injection_stays_inside_string():
    d = default_package("x'; Remove-Item C:\\ -Recurse; '")
    s = generate(d)
    assert "AppName = 'x''; Remove-Item C:\\ -Recurse; '''" in s


def test_crud_and_script(authed):
    r = authed.post("/api/packages", json={"name": "Notepad++"})
    assert r.status_code == 201
    pid = r.json()["id"]
    data = r.json()["data"]
    data["app"]["version"] = "8.6"
    data["install"]["main"] = [{"type": "exe", "file": "npp.exe", "args": "/S"}]
    assert authed.put(f"/api/packages/{pid}", json=data).status_code == 200
    script = authed.get(f"/api/packages/{pid}/script").text
    assert "Start-ADTProcess -FilePath \"$($adtSession.DirFiles)\\npp.exe\" -ArgumentList '/S'" in script
    dl = authed.get(f"/api/packages/{pid}/script?download=1")
    assert dl.content.startswith(b"\xef\xbb\xbf") and b"\r\n" in dl.content
    assert authed.get("/api/packages").json()[0]["version"] == "8.6"
    assert authed.delete(f"/api/packages/{pid}").status_code == 204


def test_invalid_step_rejected(authed):
    pid = authed.post("/api/packages", json={"name": "X"}).json()["id"]
    bad = default_package("X").model_dump()
    bad["install"]["main"] = [{"type": "exe", "file": "..\\..\\evil.exe"}]
    assert authed.put(f"/api/packages/{pid}", json=bad).status_code == 422
    bad["install"]["main"] = [{"type": "msi"}]
    assert authed.put(f"/api/packages/{pid}", json=bad).status_code == 422
    bad["install"]["main"] = [{"type": "shell", "cmd": "rm -rf /"}]
    assert authed.put(f"/api/packages/{pid}", json=bad).status_code == 422


def test_upload_rules(authed):
    pid = authed.post("/api/packages", json={"name": "X"}).json()["id"]
    ok = authed.post(f"/api/packages/{pid}/files", files={"file": ("setup.msi", b"data")})
    assert ok.status_code == 201
    assert authed.post(f"/api/packages/{pid}/files", files={"file": ("evil.dll", b"x")}).status_code == 400
    assert authed.post(f"/api/packages/{pid}/files", files={"file": ("app.msix", b"x")}).status_code == 201
    r = authed.post(f"/api/packages/{pid}/files", files={"file": ("../../etc/passwd.txt", b"x")})
    assert r.status_code == 201 and r.json()["name"] == "passwd.txt"
    assert [f["name"] for f in authed.get(f"/api/packages/{pid}/files").json()] == ["app.msix", "passwd.txt", "setup.msi"]
    assert authed.delete(f"/api/packages/{pid}/files/setup.msi").status_code == 204


def test_requires_login(client):
    assert client.get("/api/packages").status_code == 401
