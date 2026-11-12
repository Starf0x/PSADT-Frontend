import struct

from app.psadt.msi import _decode, _strings


def test_stream_name_decoding():
    # "!Property" as Windows Installer stores it: table marker + pairs of name characters
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._"
    name = "Property"
    enc = chr(0x4840) + "".join(chr(0x3800 + chars.index(a) + (chars.index(b) << 6)) for a, b in zip(name[::2], name[1::2]))
    assert _decode(enc) == "!Property"


def test_string_pool():
    pool = struct.pack("<8H", 1252, 0, 11, 1, 5, 1, 0, 0)
    strings, ref = _strings(pool, b"ProductCodeHello")
    assert strings == ["", "ProductCode", "Hello", ""] and ref == 2


def test_msi_endpoint_rejects_non_msi(authed):
    pid = authed.post("/api/packages", json={"name": "M"}).json()["id"]
    authed.post(f"/api/packages/{pid}/files", files={"file": ("setup.msi", b"not an msi")})
    assert authed.get(f"/api/packages/{pid}/files/setup.msi/msi").status_code == 422
    assert authed.get(f"/api/packages/{pid}/files/missing.msi/msi").status_code == 404
    assert authed.get(f"/api/packages/{pid}/files/setup.exe/msi").status_code == 400


def test_msix_detection():
    from app.psadt.detection import generate_detection
    from app.psadt.schema import PackageData, default_package
    d = default_package("x").model_dump()
    d["detection"] = [{"type": "msix", "name": "Claude", "min_version": "1.2"},
                      {"type": "msix", "name": "Claude", "method": "DISM"}]
    text = generate_detection(PackageData.model_validate(d))
    assert "Get-AppxProvisionedPackage -Online | Where-Object DisplayName -like '*Claude*'" in text
    assert "[version]'1.2'" in text
    assert "/get-provisionedappxpackages | Select-String -SimpleMatch -Pattern 'Claude'" in text


def test_registry_hkcr_allowed():
    from app.psadt.schema import RegistryStep
    RegistryStep(type="registry", key="HKEY_CLASSES_ROOT\\.foo")
