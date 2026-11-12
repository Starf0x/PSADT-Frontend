"""Read the Property table of an MSI file (no Windows needed).

An MSI is an OLE compound file. Table streams have encoded names, strings live in a shared
string pool, and a table is stored column by column.
"""
import struct
from pathlib import Path

import olefile

_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._"
WANTED = ("ProductCode", "ProductVersion", "ProductName", "Manufacturer", "UpgradeCode")


def _decode(name: str) -> str:
    out = []
    for ch in name:
        c = ord(ch)
        if 0x3800 <= c < 0x4800:
            c -= 0x3800
            out += [_CHARS[c & 0x3F], _CHARS[(c >> 6) & 0x3F]]
        elif 0x4800 <= c < 0x4840:
            out.append(_CHARS[c - 0x4800])
        elif c == 0x4840:
            out.append("!")  # marks a table stream
        else:
            out.append(ch)
    return "".join(out)


def _strings(pool: bytes, data: bytes) -> tuple[list[str], int]:
    words = struct.unpack(f"<{len(pool) // 2}H", pool[: len(pool) // 2 * 2])
    codepage = words[0] | (words[1] << 16)
    ref_size = 3 if codepage & 0x80000000 else 2
    enc = {65001: "utf-8", 0: "cp1252"}.get(codepage & 0xFFFF, f"cp{codepage & 0xFFFF}")
    strings, offset, i = [""], 0, 1
    count = len(words) // 2
    while i < count:
        size, refs = words[i * 2], words[i * 2 + 1]
        if size == 0 and refs == 0:
            strings.append(""); i += 1; continue
        if size == 0:  # strings over 64 KB: the length follows in the next entry
            size = (words[i * 2 + 3] << 16) + words[i * 2 + 2]; i += 2
        else:
            i += 1
        try:
            strings.append(data[offset:offset + size].decode(enc, "replace"))
        except LookupError:
            strings.append(data[offset:offset + size].decode("cp1252", "replace"))
        offset += size
    return strings, ref_size


def read_properties(path: Path) -> dict[str, str]:
    """Return the useful properties of the MSI; raises ValueError if it is not a readable MSI."""
    if not olefile.isOleFile(str(path)):
        raise ValueError("This is not a valid MSI file")
    with olefile.OleFileIO(str(path)) as ole:
        streams = {_decode(e[0]): e for e in ole.listdir() if len(e) == 1}
        try:
            pool = ole.openstream(streams["!_StringPool"]).read()
            data = ole.openstream(streams["!_StringData"]).read()
            table = ole.openstream(streams["!Property"]).read()
        except KeyError:
            raise ValueError("This is not a valid MSI file")
    strings, ref = _strings(pool, data)
    rows = len(table) // (2 * ref)

    def cell(col: int, row: int) -> str:
        start = (col * rows + row) * ref
        idx = int.from_bytes(table[start:start + ref], "little")
        return strings[idx] if idx < len(strings) else ""

    props = {cell(0, r): cell(1, r) for r in range(rows)}
    return {k: props[k] for k in WANTED if k in props}
