"""Extract UE pak v3 (BL4 uiresources) files."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path


PAK_MAGIC = 0x5A6F12E1
FOOTER = 44


def read_fstring(data: bytes, off: int) -> tuple[str, int]:
    (n,) = struct.unpack_from("<i", data, off)
    off += 4
    if n == 0:
        return "", off
    if n < 0:
        nbytes = (-n) * 2
        raw = data[off : off + nbytes]
        off += nbytes
        return raw.decode("utf-16-le", "replace").rstrip("\x00"), off
    raw = data[off : off + n]
    off += n
    return raw.decode("utf-8", "replace").rstrip("\x00"), off


def parse_entry_fields(buf: bytes, off: int) -> tuple[dict, int]:
    offset, size, usize, method = struct.unpack_from("<qqqi", buf, off)
    off += 28
    digest = buf[off : off + 20]
    off += 20
    blocks = []
    if method != 0:
        (nblocks,) = struct.unpack_from("<i", buf, off)
        off += 4
        for _ in range(nblocks):
            start, end = struct.unpack_from("<qq", buf, off)
            off += 16
            blocks.append((start, end))
        enc = buf[off]
        off += 1
        (block_size,) = struct.unpack_from("<I", buf, off)
        off += 4
    else:
        (nblocks,) = struct.unpack_from("<i", buf, off)
        off += 4
        enc = buf[off]
        off += 1
        block_size = 0
    return (
        {
            "offset": offset,
            "size": size,
            "uncompressed": usize,
            "method": method,
            "hash": digest.hex(),
            "blocks": blocks,
            "encrypted": bool(enc),
            "block_size": block_size,
        },
        off,
    )


def parse_pak(path: Path) -> dict:
    data = path.read_bytes()
    magic, version, index_off, index_size = struct.unpack_from("<iiQQ", data, len(data) - FOOTER)
    if magic != PAK_MAGIC:
        raise RuntimeError(f"bad magic {hex(magic)}")
    index = data[index_off : index_off + index_size]
    off = 0
    mount, off = read_fstring(index, off)
    (count,) = struct.unpack_from("<i", index, off)
    off += 4
    files = []
    for _ in range(count):
        name, off = read_fstring(index, off)
        fields, off = parse_entry_fields(index, off)
        fields["name"] = name
        files.append(fields)
    return {"version": version, "mount": mount, "files": files, "raw": data, "index_left": len(index) - off}


def extract_payload(pak: bytes, entry: dict) -> bytes:
    if entry["method"] == 0:
        # Skip in-file FPakEntry header: 8+8+8+4+20+4+1 = 53
        start = entry["offset"] + 53
        return pak[start : start + entry["uncompressed"]]
    chunks = []
    for start, end in entry["blocks"]:
        chunks.append(zlib.decompress(pak[start:end]))
    return b"".join(chunks)


def main() -> None:
    root = Path(__file__).resolve().parent
    out_root = root / "_extracted"
    for name in (
        "pakchunk990-Windows_990_P.pak",
        "pakchunk970-Windows_970_P.pak",
    ):
        pak_path = root / "_paks" / name
        info = parse_pak(pak_path)
        dest = out_root / pak_path.stem
        dest.mkdir(parents=True, exist_ok=True)
        print("=" * 72)
        print(f"{name} ver={info['version']} mount={info['mount']!r} n={len(info['files'])} leftover={info['index_left']}")
        for e in info["files"]:
            payload = extract_payload(info["raw"], e)
            safe = e["name"].replace("\\", "/").lstrip("/")
            out = dest / safe
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(payload)
            print(f"  {e['name']:55} meth={e['method']} raw={e['size']:8} out={len(payload):8} enc={e['encrypted']}")


if __name__ == "__main__":
    main()
