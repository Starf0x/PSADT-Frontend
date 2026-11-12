"""Bouwt Invoke-AppDeployToolkit.ps1 uit gevalideerde pakketdata.

Alle gebruikersinvoer komt in PowerShell-strings tussen enkele quotes (geen variabele-expansie);
alleen bestandsnamen die door FILE_RE zijn gevalideerd komen in een dubbel gequote pad.
Het script wordt op de server nooit uitgevoerd.
"""
from datetime import date
from pathlib import Path

from .schema import PSADT_VERSION, PackageData

_DIR = Path(__file__).parent
HEADER = (_DIR / "template_header.ps1").read_text()
FOOTER = (_DIR / "template_footer.ps1").read_text()
I = "    "


def q(value: str) -> str:
    """PowerShell single-quoted literal. Ook 'slimme' quotes verdubbelen, PowerShell ziet die als '."""
    for ch in ("'", "‘", "’", "‚", "‛"):
        value = value.replace(ch, ch * 2)
    return f"'{value}'"


FILES_TOKEN = "{Files}"


def args(value: str) -> str:
    """Arguments as a PowerShell string. "{Files}" becomes the package's Files folder on the PC;
    everything else stays literal (escaped for a double-quoted string)."""
    if FILES_TOKEN not in value:
        return q(value)
    def lit(part: str) -> str:
        for ch in ("`", "$", '"', "“", "”", "„"):
            part = part.replace(ch, "`" + ch)
        return part
    return '"' + "$($adtSession.DirFiles)".join(lit(x) for x in value.split(FILES_TOKEN)) + '"'


def _files(name: str) -> str:
    return f'"$($adtSession.DirFiles)\\{name}"'


def _codes(codes: list[int]) -> str:
    return "@(" + ", ".join(str(c) for c in codes) + ")"


def _step(s) -> list[str]:
    out = [f"## {line}" for line in s.comment.splitlines() if line.strip()]
    t = s.type
    if t == "welcome":
        parts = ["Show-ADTInstallationWelcome"]
        parts.append("-CloseProcesses $adtSession.AppProcessesToClose")
        if s.allow_defer:
            parts.append(f"-AllowDefer -DeferTimes {s.defer_times}")
        if s.check_disk_space:
            parts.append("-CheckDiskSpace")
        if s.persist_prompt:
            parts.append("-PersistPrompt")
        if s.countdown:
            parts.append(f"-CloseProcessesCountdown {s.countdown}")
        out += [
            "if ($adtSession.AppProcessesToClose.Count -gt 0)",
            "{",
            I + " ".join(parts),
            "}",
            "else",
            "{",
            I + " ".join(p for p in parts if not p.startswith("-CloseProcesses")),
            "}",
        ]
    elif t == "progress":
        out.append("Show-ADTInstallationProgress" + (f" -StatusMessage {q(s.message)}" if s.message else ""))
    elif t == "msi":
        cmd = f"Start-ADTMsiProcess -Action {s.action}"
        if s.file:
            cmd += f" -FilePath {_files(s.file)}"
        elif s.product_code:
            cmd += f" -ProductCode {q(s.product_code)}"
        else:
            raise ValueError("MSI step needs a file or ProductCode")
        if s.transforms:
            cmd += f" -Transforms {_files(s.transforms)}"
        if s.args:
            cmd += f" -AdditionalArgumentList {args(s.args)}"
        out.append(cmd)
    elif t == "exe":
        cmd = f"Start-ADTProcess -FilePath {_files(s.file)}"
        if s.args:
            cmd += f" -ArgumentList {args(s.args)}"
        if s.ignore_exit_codes.strip():
            codes = [c for c in s.ignore_exit_codes.replace(" ", "").split(",") if c]
            cmd += " -IgnoreExitCodes " + ", ".join(c if c.lstrip("-").isdigit() else q(c) for c in codes)
        out.append(cmd)
    elif t == "uninstall_app":
        cmd = f"Uninstall-ADTApplication -Name {q(s.name)} -NameMatch {s.name_match}"
        if s.args:
            cmd += f" -AdditionalArgumentList {args(s.args)}"
        out.append(cmd)
    elif t == "registry":
        cmd = f"Set-ADTRegistryKey -LiteralPath {q(s.key)}"
        if s.name:
            cmd += f" -Name {q(s.name)} -Value {q(s.value)} -Type {s.value_type}"
        out.append(cmd)
    elif t == "remove_registry":
        cmd = f"Remove-ADTRegistryKey -LiteralPath {q(s.key)}"
        cmd += f" -Name {q(s.name)}" if s.name else " -Recurse"
        out.append(cmd)
    elif t == "copy_file":
        out.append(f"Copy-ADTFile -Path {_files(s.file)} -Destination {q(s.destination)}")
    elif t == "remove_file":
        out.append(f"Remove-ADTFile -LiteralPath {q(s.path)}")
    elif t == "remove_folder":
        out.append(f"Remove-ADTFolder -LiteralPath {q(s.path)}")
    elif t == "custom":
        out += s.code.splitlines()
    return out


PHASE_TITLES = {"pre": "Pre-{0}", "main": "{0}", "post": "Post-{0}"}
PHASE_VALUES = {"pre": '"Pre-$($adtSession.DeploymentType)"', "main": "$adtSession.DeploymentType",
                "post": '"Post-$($adtSession.DeploymentType)"'}


def _function(kind: str, phases) -> list[str]:
    lines = [f"function {kind}-ADTDeployment", "{", I + "[CmdletBinding()]", I + "param", I + "(", I + ")", ""]
    for key in ("pre", "main", "post"):
        lines += [
            I + "##================================================",
            I + f"## MARK: {PHASE_TITLES[key].format(kind)}",
            I + "##================================================",
            I + f"$adtSession.InstallPhase = {PHASE_VALUES[key]}",
            "",
        ]
        for step in getattr(phases, key):
            lines += [I + line if line else "" for line in _step(step)]
            lines.append("")
    lines.append("}")
    return lines


def generate(data: PackageData, script_date: date | None = None) -> str:
    a = data.app
    procs = "@(" + ", ".join(q(p) for p in a.processes_to_close) + ")"
    vars_ = [
        "##================================================",
        "## MARK: Variables",
        "##================================================",
        "",
        "# Generated by PSADT Frontend.",
        "$adtSession = @{",
        I + "# App variables.",
        I + f"AppVendor = {q(a.vendor)}",
        I + f"AppName = {q(a.name)}",
        I + f"AppVersion = {q(a.version)}",
        I + f"AppArch = {q(a.arch)}",
        I + f"AppLang = {q(a.lang)}",
        I + f"AppRevision = {q(a.revision)}",
        I + f"AppSuccessExitCodes = {_codes(a.success_exit_codes)}",
        I + f"AppRebootExitCodes = {_codes(a.reboot_exit_codes)}",
        I + f"AppProcessesToClose = {procs}",
        I + f"AppScriptVersion = {q(a.script_version)}",
        I + f"AppScriptDate = {q((script_date or date.today()).isoformat())}",
        I + f"AppScriptAuthor = {q(a.author)}",
        I + f"RequireAdmin = ${'true' if a.require_admin else 'false'}",
        "",
        I + "# Install Titles (Only set here to override defaults set by the toolkit).",
        I + "InstallName = ''",
        I + "InstallTitle = ''",
        "",
        I + "# Script variables.",
        I + "DeployAppScriptFriendlyName = $MyInvocation.MyCommand.Name",
        I + "DeployAppScriptParameters = $PSBoundParameters",
        I + f"DeployAppScriptVersion = '{PSADT_VERSION}'",
        "}",
        "",
    ]
    body = vars_ + _function("Install", data.install) + [""] + _function("Uninstall", data.uninstall) + [""]
    body += _function("Repair", data.repair) + ["", ""]
    return HEADER.rstrip("\n") + "\n\n\n" + "\n".join(body) + FOOTER
