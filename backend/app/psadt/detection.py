"""Genereert een Intune-detectiescript: output + exit 0 = geïnstalleerd, geen output = niet geïnstalleerd."""
from .generator import q
from .schema import PackageData

HIVES = {"HKLM": "HKEY_LOCAL_MACHINE", "HKCU": "HKEY_CURRENT_USER", "HKCR": "HKEY_CLASSES_ROOT", "HKU": "HKEY_USERS"}
UNINSTALL = ("HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
             "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall")


def reg_path(key: str) -> str:
    hive, _, rest = key.partition("\\")
    hive = HIVES.get(hive.rstrip(":").upper(), hive.rstrip(":").upper())
    return f"Registry::{hive}\\{rest}"


def generate_detection(data: PackageData) -> str:
    out = [
        f"# Intune-detectiescript voor {data.app.name} {data.app.version}".rstrip(),
        "# Gegenereerd door PSADT Frontend. Alle regels moeten kloppen.",
        "$ErrorActionPreference = 'SilentlyContinue'",
        "",
    ]
    if not data.detection:
        out += ["# Geen detectieregels ingesteld.", "exit 0", ""]
        return "\n".join(out)
    for i, r in enumerate(data.detection, 1):
        out.append(f"# Regel {i}: {r.type}")
        if r.type == "msi":
            paths = ", ".join(q(f"Registry::{u}\\{r.product_code}") for u in UNINSTALL)
            out.append(f"$app = Get-ItemProperty -LiteralPath {paths} | Select-Object -First 1")
            out.append("if (-not $app) { exit 0 }")
            if r.min_version:
                out.append(f"if ([version]$app.DisplayVersion -lt [version]{q(r.min_version)}) {{ exit 0 }}")
        elif r.type == "file":
            out.append(f"$item = Get-Item -LiteralPath ([Environment]::ExpandEnvironmentVariables({q(r.path)}))")
            out.append("if (-not $item) { exit 0 }")
            if r.min_version:
                out.append(f"if ($item.VersionInfo.FileVersionRaw -lt [version]{q(r.min_version)}) {{ exit 0 }}")
        elif r.type == "registry":
            path = q(reg_path(r.key))
            if r.name:
                out.append(f"$val = (Get-ItemProperty -LiteralPath {path} -Name {q(r.name)}).{q(r.name)}")
                out.append("if ($null -eq $val) { exit 0 }")
                if r.value:
                    out.append(f"if ([string]$val -ne {q(r.value)}) {{ exit 0 }}")
            else:
                out.append(f"if (-not (Test-Path -LiteralPath {path})) {{ exit 0 }}")
        out.append("")
    out += ["Write-Output 'Installed'", "exit 0", ""]
    return "\n".join(out)
