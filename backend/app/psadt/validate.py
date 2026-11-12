"""Pre-export check: everything that would make a package fail or behave unexpectedly.

Each item has a level ("error" blocks the export, "warning" does not), an English text with
{placeholders}, and the values for them, so the browser can translate it.
"""
from pydantic import ValidationError

from .generator import generate
from .schema import WINDOWS_PREFIX, PackageData

FILE_FIELDS = ("file", "transforms")
PHASE_NAMES = {"pre": "Pre", "main": "Main", "post": "Post"}
KIND_NAMES = {"install": "Install", "uninstall": "Uninstall", "repair": "Repair"}


def _item(level: str, text: str, **vars) -> dict:
    return {"level": level, "text": text, "vars": vars}


def validate_package(raw: dict, uploaded: set[str], toolkit_ok: bool) -> tuple[list[dict], str | None]:
    """Returns (items, script). script is None when the package cannot be generated."""
    items: list[dict] = []
    if not toolkit_ok:
        items.append(_item("error", "The PSADT toolkit is missing on the server; see README"))
    try:
        data = PackageData.model_validate(raw)
    except ValidationError as e:
        for err in e.errors():
            items.append(_item("error", "Invalid setting {field}: {msg}",
                               field=" › ".join(str(x) for x in err["loc"]), msg=err["msg"]))
        return items, None

    for kind in ("install", "uninstall", "repair"):
        phases = getattr(data, kind)
        for phase in ("pre", "main", "post"):
            for i, step in enumerate(getattr(phases, phase), 1):
                for f in FILE_FIELDS:
                    name = getattr(step, f, None)
                    if name and not name.startswith(WINDOWS_PREFIX) and name not in uploaded:
                        items.append(_item("error", "{kind} › {phase}, step {n}: file {file} has not been uploaded",
                                           kind=KIND_NAMES[kind], phase=PHASE_NAMES[phase], n=i, file=name))

    if not data.install.main:
        items.append(_item("warning", "The install has no main step, so nothing gets installed"))
    if not data.uninstall.main:
        items.append(_item("warning", "The uninstall has no main step"))
    if not data.detection:
        items.append(_item("warning", "There are no detection rules; Intune cannot tell whether the app is installed"))
    if not data.app.vendor or not data.app.version:
        items.append(_item("warning", "Vendor or version is empty; the file name and Intune details will be incomplete"))
    if not uploaded:
        items.append(_item("warning", "No files have been uploaded"))

    try:
        script = generate(data)
    except ValueError as e:
        items.append(_item("error", "The script could not be generated: {msg}", msg=str(e)))
        script = None
    return items, script
