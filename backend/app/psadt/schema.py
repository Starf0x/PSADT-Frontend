"""Pydantic-modellen voor een PSADT-pakket. Alleen deze stap-types bestaan; alles wordt gevalideerd."""
import re
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

PSADT_VERSION = "4.1.8"
FILE_RE = re.compile(r"^[\w.\- ()]{1,128}$")
PROC_RE = re.compile(r"^[\w.\- ]{1,64}$")
GUID_RE = re.compile(r"^\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}$")
REG_RE = re.compile(r"^(HKLM|HKCU|HKCR|HKU|HKEY_LOCAL_MACHINE|HKEY_CURRENT_USER|HKEY_CLASSES_ROOT|HKEY_USERS):?\\.+")

Text = Annotated[str, Field(max_length=2000)]


# Programs that are already on every Windows PC; an EXE step may use them as "windows:<name>".
WINDOWS_PREFIX = "windows:"
WINDOWS_EXES = ("winget.exe", "msiexec.exe", "powershell.exe", "cmd.exe", "dism.exe", "reg.exe", "regsvr32.exe", "wusa.exe")


def _exe(v: str) -> str:
    if v.startswith(WINDOWS_PREFIX):
        if v[len(WINDOWS_PREFIX):] not in WINDOWS_EXES:
            raise ValueError("Unknown Windows program")
        return v
    return _file(v)


def _file(v: str | None) -> str | None:
    if v and (not FILE_RE.match(v) or v in (".", "..")):
        raise ValueError("Invalid file name")
    return v


class _Step(BaseModel):
    comment: Annotated[str, Field(max_length=200)] = ""


class WelcomeStep(_Step):
    type: Literal["welcome"]
    allow_defer: bool = True
    defer_times: Annotated[int, Field(ge=0, le=99)] = 3
    check_disk_space: bool = True
    persist_prompt: bool = True
    countdown: Annotated[int, Field(ge=0, le=86400)] = 0


class ProgressStep(_Step):
    type: Literal["progress"]
    message: Text = ""


class MsiStep(_Step):
    type: Literal["msi"]
    action: Literal["Install", "Uninstall", "Repair", "Patch"] = "Install"
    file: str | None = None
    product_code: str | None = None
    transforms: str | None = None
    args: Text = ""

    _vf = field_validator("file", "transforms")(classmethod(lambda cls, v: _file(v)))

    @field_validator("product_code")
    @classmethod
    def _guid(cls, v):
        if v and not GUID_RE.match(v):
            raise ValueError("ProductCode must be a GUID, e.g. {xxxxxxxx-...}")
        return v

    @model_validator(mode="after")
    def _target(self):
        if not self.file and not self.product_code:
            raise ValueError("MSI step needs a file or ProductCode")
        return self


class ExeStep(_Step):
    type: Literal["exe"]
    file: str
    args: Text = ""
    ignore_exit_codes: Annotated[str, Field(pattern=r"^[0-9, *]*$", max_length=100)] = ""

    _vf = field_validator("file")(classmethod(lambda cls, v: _exe(v)))


class UninstallAppStep(_Step):
    type: Literal["uninstall_app"]
    name: Annotated[str, Field(min_length=1, max_length=200)]
    name_match: Literal["Contains", "Exact", "Wildcard", "Regex"] = "Contains"
    args: Text = ""


class RegistryStep(_Step):
    type: Literal["registry"]
    key: Annotated[str, Field(max_length=500)]
    name: Annotated[str, Field(max_length=200)] = ""
    value: Text = ""
    value_type: Literal["String", "ExpandString", "DWord", "QWord", "MultiString", "Binary"] = "String"

    @field_validator("key")
    @classmethod
    def _key(cls, v):
        if not REG_RE.match(v):
            raise ValueError("Registry key must start with HKLM\\, HKCU\\, ...")
        return v


class RemoveRegistryStep(RegistryStep):
    type: Literal["remove_registry"]


class CopyFileStep(_Step):
    type: Literal["copy_file"]
    file: str
    destination: Annotated[str, Field(min_length=1, max_length=500)]

    _vf = field_validator("file")(classmethod(lambda cls, v: _file(v)))


class RemovePathStep(_Step):
    type: Literal["remove_file", "remove_folder"]
    path: Annotated[str, Field(min_length=3, max_length=500)]


class CustomStep(_Step):
    type: Literal["custom"]
    code: Annotated[str, Field(max_length=20000)]


Step = Annotated[
    WelcomeStep | ProgressStep | MsiStep | ExeStep | UninstallAppStep | RegistryStep | RemoveRegistryStep
    | CopyFileStep | RemovePathStep | CustomStep,
    Field(discriminator="type"),
]


class Phases(BaseModel):
    pre: list[Step] = []
    main: list[Step] = []
    post: list[Step] = []


LOG_PATH_PATTERN = r"^$|^[^'\r\n\"`]{3,260}$"


class AppInfo(BaseModel):
    vendor: Annotated[str, Field(max_length=100)] = ""
    name: Annotated[str, Field(min_length=1, max_length=100)]
    version: Annotated[str, Field(max_length=50)] = ""
    arch: Literal["", "x86", "x64", "arm64"] = ""
    lang: Annotated[str, Field(max_length=10)] = "EN"
    revision: Annotated[str, Field(max_length=10)] = "01"
    author: Annotated[str, Field(max_length=100)] = ""
    script_version: Annotated[str, Field(max_length=20)] = "1.0.0"
    success_exit_codes: list[Annotated[int, Field(ge=-2147483648, le=4294967295)]] = [0]
    reboot_exit_codes: list[Annotated[int, Field(ge=-2147483648, le=4294967295)]] = [1641, 3010]
    processes_to_close: list[Annotated[str, Field(pattern=PROC_RE.pattern)]] = []
    require_admin: bool = True
    # Folder for the PSADT log on the client; empty = the default chosen on the System page.
    log_path: Annotated[str, Field(pattern=LOG_PATH_PATTERN)] = ""


class MsiDetection(BaseModel):
    type: Literal["msi"]
    product_code: str
    min_version: Annotated[str, Field(pattern=r"^$|^\d+(\.\d+){0,3}$")] = ""

    @field_validator("product_code")
    @classmethod
    def _guid(cls, v):
        if not GUID_RE.match(v):
            raise ValueError("ProductCode must be a GUID, e.g. {xxxxxxxx-...}")
        return v


class FileDetection(BaseModel):
    type: Literal["file"]
    path: Annotated[str, Field(min_length=3, max_length=500)]
    min_version: Annotated[str, Field(pattern=r"^$|^\d+(\.\d+){0,3}$")] = ""


class RegistryDetection(BaseModel):
    type: Literal["registry"]
    key: Annotated[str, Field(max_length=500)]
    name: Annotated[str, Field(max_length=200)] = ""
    value: Annotated[str, Field(max_length=500)] = ""

    @field_validator("key")
    @classmethod
    def _key(cls, v):
        if not REG_RE.match(v):
            raise ValueError("Registry key must start with HKLM\\, HKCU\\, ...")
        return v


Detection = Annotated[MsiDetection | FileDetection | RegistryDetection, Field(discriminator="type")]


class PackageData(BaseModel):
    app: AppInfo
    install: Phases = Phases()
    uninstall: Phases = Phases()
    repair: Phases = Phases()
    detection: list[Detection] = []


def default_package(name: str) -> PackageData:
    """Zelfde startpunt als het officiële v4-template."""
    welcome_install = WelcomeStep(type="welcome")
    welcome_other = WelcomeStep(type="welcome", allow_defer=False, check_disk_space=False, persist_prompt=False, countdown=60)
    progress = ProgressStep(type="progress")
    return PackageData(
        app=AppInfo(name=name),
        install=Phases(pre=[welcome_install, progress]),
        uninstall=Phases(pre=[welcome_other, progress]),
        repair=Phases(pre=[welcome_other, progress]),
    )
