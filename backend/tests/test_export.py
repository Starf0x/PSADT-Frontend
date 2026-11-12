import base64
import hashlib
import hmac
import io
import re
import zipfile

import pytest
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.config import settings
from app.psadt.detection import generate_detection
from app.psadt.schema import PackageData, default_package


@pytest.fixture()
def toolkit(tmp_path, monkeypatch):
    z = tmp_path / "toolkit.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("Invoke-AppDeployToolkit.ps1", "template")
        f.writestr("Invoke-AppDeployToolkit.exe", b"MZ")
        f.writestr("PSAppDeployToolkit/PSAppDeployToolkit.psd1", "@{}")
        f.writestr("Files/Add Setup Files Here.txt", "")
    monkeypatch.setattr(settings, "toolkit_zip", z)
    return z


def _pkg(authed):
    pid = authed.post("/api/packages", json={"name": "Demo"}).json()["id"]
    authed.post(f"/api/packages/{pid}/files", files={"file": ("setup.msi", b"msi-bytes")})
    return pid


def test_zip_export(authed, toolkit):
    pid = _pkg(authed)
    r = authed.get(f"/api/packages/{pid}/export/zip")
    assert r.status_code == 200 and 'filename="Demo.zip"' in r.headers["content-disposition"]
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = set(z.namelist())
    assert {"Invoke-AppDeployToolkit.exe", "PSAppDeployToolkit/PSAppDeployToolkit.psd1", "Files/setup.msi"} <= names
    assert "Files/Add Setup Files Here.txt" not in names
    script = z.read("Invoke-AppDeployToolkit.ps1")
    assert script.startswith(b"\xef\xbb\xbf") and b"AppName = 'Demo'" in script
    assert not list((settings.data_dir / "tmp").iterdir())  # tijdelijke bestanden opgeruimd


def test_intunewin_roundtrip(authed, toolkit):
    pid = _pkg(authed)
    r = authed.get(f"/api/packages/{pid}/export/intunewin")
    assert r.status_code == 200
    outer = zipfile.ZipFile(io.BytesIO(r.content))
    xml = outer.read("IntuneWinPackage/Metadata/Detection.xml").decode()
    get = lambda tag: re.search(f"<{tag}>(.*?)</{tag}>", xml).group(1)  # noqa: E731
    blob = outer.read("IntuneWinPackage/Contents/IntunePackage.intunewin")
    key, mac_key = base64.b64decode(get("EncryptionKey")), base64.b64decode(get("MacKey"))
    mac, iv, ct = blob[:32], blob[32:48], blob[48:]
    assert iv == base64.b64decode(get("InitializationVector"))
    assert hmac.new(mac_key, iv + ct, hashlib.sha256).digest() == mac == base64.b64decode(get("Mac"))
    dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    unpad = padding.PKCS7(128).unpadder()
    plain = unpad.update(dec.update(ct) + dec.finalize()) + unpad.finalize()
    assert len(plain) == int(get("UnencryptedContentSize"))
    assert hashlib.sha256(plain).digest() == base64.b64decode(get("FileDigest"))
    assert "Files/setup.msi" in zipfile.ZipFile(io.BytesIO(plain)).namelist()
    assert get("SetupFile") == "Invoke-AppDeployToolkit.exe"


def test_export_without_toolkit(authed, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "toolkit_zip", tmp_path / "missing.zip")
    pid = authed.post("/api/packages", json={"name": "X"}).json()["id"]
    assert authed.get(f"/api/packages/{pid}/export/zip").status_code == 503


def test_detection_script():
    d = default_package("App").model_dump()
    d["detection"] = [
        {"type": "msi", "product_code": "{12345678-1234-1234-1234-123456789012}", "min_version": "1.2"},
        {"type": "file", "path": "%ProgramFiles%\\App\\app.exe", "min_version": "3.0.0"},
        {"type": "registry", "key": "HKLM\\SOFTWARE\\App", "name": "Ver", "value": "x'y"},
    ]
    s = generate_detection(PackageData.model_validate(d))
    assert "Registry::HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{12345678" in s
    assert "[version]'1.2'" in s and "FileVersionRaw -lt [version]'3.0.0'" in s
    assert "'Registry::HKEY_LOCAL_MACHINE\\SOFTWARE\\App'" in s and "-ne 'x''y'" in s
    assert s.rstrip().endswith("Write-Output 'Installed'\nexit 0")


def test_bad_detection_rejected(authed):
    pid = authed.post("/api/packages", json={"name": "X"}).json()["id"]
    d = default_package("X").model_dump()
    d["detection"] = [{"type": "msi", "product_code": "geen-guid"}]
    assert authed.put(f"/api/packages/{pid}", json=d).status_code == 422


def test_snippets(authed):
    r = authed.post("/api/snippets", json={"name": "Stil", "step": {"type": "exe", "file": "s.exe", "args": "/S"}})
    assert r.status_code == 201
    assert authed.get("/api/snippets").json()[0]["step"]["args"] == "/S"
    assert authed.post("/api/snippets", json={"name": "x", "step": {"type": "bad"}}).status_code == 422
    assert authed.delete(f"/api/snippets/{r.json()['id']}").status_code == 204


def test_validate_and_export_gate(authed, toolkit):
    pid = _pkg(authed)
    data = authed.get(f"/api/packages/{pid}").json()["data"]
    data["install"]["main"] = [{"type": "msi", "action": "Install", "file": "missing.msi"}]
    authed.put(f"/api/packages/{pid}", json=data)
    v = authed.get(f"/api/packages/{pid}/validate").json()
    assert v["ok"] is False
    assert any(i["level"] == "error" and i["vars"].get("file") == "missing.msi" for i in v["items"])
    assert authed.get(f"/api/packages/{pid}/export/zip").status_code == 422

    data["install"]["main"][0]["file"] = "setup.msi"
    authed.put(f"/api/packages/{pid}", json=data)
    assert authed.get(f"/api/packages/{pid}/validate").json()["ok"] is True
    assert authed.get(f"/api/packages/{pid}/export/zip").status_code == 200


def test_export_removes_uploads_when_chosen(authed, toolkit):
    pid = _pkg(authed)
    authed.put("/api/system/settings", json={"upload_retention": "export"})
    assert authed.get(f"/api/packages/{pid}/export/zip").status_code == 200
    assert authed.get(f"/api/packages/{pid}/files").json() == []


def test_log_path_default_and_override(authed, toolkit):
    cfg = "@{\n    MSI = @{\n        LogPath = $null\n    }\n    Toolkit = @{\n        LogPath = '$envWinDir\\Logs\\Software'\n    }\n}\n"
    with zipfile.ZipFile(toolkit, "a") as f:
        f.writestr("Config/config.psd1", cfg.encode("utf-8-sig"))
    pid = _pkg(authed)

    def logpath():
        z = zipfile.ZipFile(io.BytesIO(authed.get(f"/api/packages/{pid}/export/zip").content))
        return z.read("Config/config.psd1").decode("utf-8-sig")

    assert "LogPath = '$envWinDir\\Logs\\Software'" in logpath()  # untouched without a setting
    assert authed.put("/api/system/settings", json={"log_path": "C:\\Bad'Path"}).status_code == 422
    assert authed.put("/api/system/settings", json={"log_path": "C:\\Logs\\Intune"}).json()["log_path"] == "C:\\Logs\\Intune"
    out = logpath()
    assert "LogPath = 'C:\\Logs\\Intune'" in out and "LogPath = $null" in out

    data = authed.get(f"/api/packages/{pid}").json()["data"]
    data["app"]["log_path"] = "$envProgramData\\MyLogs"
    assert authed.put(f"/api/packages/{pid}", json=data).status_code == 200
    assert "LogPath = '$envProgramData\\MyLogs'" in logpath()


def test_export_counter(authed, toolkit):
    pid = _pkg(authed)
    assert authed.get("/api/stats").json() == {"total": 0, "mine": 0, "per_user": []}
    authed.get(f"/api/packages/{pid}/export/zip")
    authed.get(f"/api/packages/{pid}/export/intunewin")
    s = authed.get("/api/stats").json()
    assert s["total"] == 2 and s["mine"] == 2 and s["per_user"][0]["count"] == 2 and s["per_user"][0]["me"]
