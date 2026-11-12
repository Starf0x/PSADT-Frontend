"""Bouwt het deploybare pakket (ZIP) en een .intunewin, zonder Windows-tools."""
import base64
import hashlib
import hmac
import os
import re
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

SCRIPT_NAME = "Invoke-AppDeployToolkit.ps1"
SETUP_FILE = "Invoke-AppDeployToolkit.exe"
CHUNK = 1024 * 1024


def to_windows(text: str) -> bytes:
    """UTF-8 met BOM en CRLF, zodat Windows PowerShell 5.1 het script goed leest."""
    return ("﻿" + text.replace("\r\n", "\n").replace("\n", "\r\n")).encode("utf-8")


CONFIG_NAME = "Config/config.psd1"
LOG_PATH_RE = re.compile(r"^(\s*LogPath = )'[^'\r\n]*'", re.M)  # Toolkit.LogPath; MSI.LogPath is $null


def set_log_path(config: str, log_path: str) -> str:
    """Puts the chosen log folder in the package's Config/config.psd1 (Toolkit.LogPath)."""
    return LOG_PATH_RE.sub(lambda m: f"{m.group(1)}'{log_path}'", config, count=1)


def build_zip(toolkit_zip: Path, script: str, files_dir: Path, out: Path, log_path: str = "") -> None:
    with zipfile.ZipFile(toolkit_zip) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            name = info.filename
            # Template-script en placeholder-bestand in Files/ vervangen we
            if name == SCRIPT_NAME or (name.startswith("Files/") and not info.is_dir()):
                continue
            if name == CONFIG_NAME and log_path:
                text = src.read(info).decode("utf-8-sig")
                dst.writestr(info, set_log_path(text, log_path).encode("utf-8-sig"))
                continue
            with src.open(info) as fsrc, dst.open(info, "w") as fdst:
                while chunk := fsrc.read(CHUNK):
                    fdst.write(chunk)
        dst.writestr(SCRIPT_NAME, to_windows(script))
        if files_dir.is_dir():
            for f in sorted(files_dir.iterdir()):
                if f.is_file() and not f.name.startswith("."):
                    dst.write(f, f"Files/{f.name}")


def build_intunewin(content_zip: Path, out: Path, setup_file: str = SETUP_FILE) -> None:
    """Zelfde formaat als IntuneWinAppUtil: AES-256-CBC + HMAC-SHA256, metadata in Detection.xml."""
    key, mac_key, iv = os.urandom(32), os.urandom(32), os.urandom(16)
    enc_path = out.with_suffix(".enc")
    digest = hashlib.sha256()
    mac = hmac.new(mac_key, iv, hashlib.sha256)
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    padder = padding.PKCS7(128).padder()
    size = 0
    try:
        with content_zip.open("rb") as fin, enc_path.open("wb") as fout:
            fout.write(b"\0" * 32 + iv)
            while chunk := fin.read(CHUNK):
                size += len(chunk)
                digest.update(chunk)
                ct = encryptor.update(padder.update(chunk))
                mac.update(ct)
                fout.write(ct)
            ct = encryptor.update(padder.finalize()) + encryptor.finalize()
            mac.update(ct)
            fout.write(ct)
            fout.seek(0)
            mac_value = mac.digest()
            fout.write(mac_value)
        b64 = lambda b: base64.b64encode(b).decode()  # noqa: E731
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ApplicationInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ToolVersion="1.8.6.0">
  <Name>{setup_file}</Name>
  <UnencryptedContentSize>{size}</UnencryptedContentSize>
  <FileName>IntunePackage.intunewin</FileName>
  <SetupFile>{setup_file}</SetupFile>
  <EncryptionInfo>
    <EncryptionKey>{b64(key)}</EncryptionKey>
    <MacKey>{b64(mac_key)}</MacKey>
    <InitializationVector>{b64(iv)}</InitializationVector>
    <Mac>{b64(mac_value)}</Mac>
    <ProfileIdentifier>ProfileVersion1</ProfileIdentifier>
    <FileDigest>{b64(digest.digest())}</FileDigest>
    <FileDigestAlgorithm>SHA256</FileDigestAlgorithm>
  </EncryptionInfo>
</ApplicationInfo>
"""
        with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
            z.write(enc_path, "IntuneWinPackage/Contents/IntunePackage.intunewin")
            z.writestr("IntuneWinPackage/Metadata/Detection.xml", xml.encode("utf-8"))
    finally:
        enc_path.unlink(missing_ok=True)
