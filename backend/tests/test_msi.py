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
