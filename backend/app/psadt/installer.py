"""Recognise the kind of setup.exe from marker strings in the file, and its silent install arguments."""
from pathlib import Path

# Checked in this order: wrappers (Burn, InstallShield, Advanced Installer) can contain the other markers too.
KINDS = [
    ("WiX Burn", (b".wixburn",), "/quiet /norestart"),
    ("InstallShield", (b"InstallShield",), '/s /v"/qn REBOOT=ReallySuppress"'),
    ("Advanced Installer", (b"Advanced Installer",), "/exenoui /qn /norestart"),
    ("Inno Setup", (b"Inno Setup Setup Data", b"InnoSetupLdrWindow", b"JR.Inno.Setup"), "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"),
    ("NSIS", (b"Nullsoft.NSIS", b"NullsoftInst", b"Nullsoft Install System"), "/S"),
    ("Squirrel", (b"SquirrelSetup", b"Squirrel.Windows", b"squirrel.exe"), "--silent"),
]
HEAD = 16 * 1024 * 1024  # markers sit in the stub/manifest near the start, or in the overlay at the end
TAIL = 4 * 1024 * 1024


def detect(path: Path) -> dict | None:
    """{"installer": name, "args": silent arguments} or None when the kind is unknown."""
    size = path.stat().st_size
    with path.open("rb") as f:
        data = f.read(HEAD)
        if size > HEAD:
            f.seek(max(HEAD, size - TAIL))
            data += f.read(TAIL)
    for name, markers, args in KINDS:
        if any(m in data for m in markers):
            return {"installer": name, "args": args}
    return None
