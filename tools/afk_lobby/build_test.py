"""Build an additive test from installed archives; never writes the game directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import zipfile
import zlib
from pak_v3 import parse_pak, extract_payload, read_fstring, parse_entry_fields

ROOT = Path(__file__).resolve().parents[2]
CHANGED = ("backend_actions.py", "external_bridge.py", "serial_rewards.py", "afk_lobby.py")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(game, output):
    game, output = game.resolve(), output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_sdk = game / "sdk_mods/MattsSDKBoostingTools.sdkmod"
    source_pak = game / "OakGame/Content/Paks/pakchunk90-Windows_90_P.pak"
    originals = output / "originals"
    originals.mkdir(exist_ok=True)
    for source in (source_sdk, source_pak):
        backup = originals / source.name
        if backup.exists():
            assert backup.read_bytes() == source.read_bytes(), "Installed source changed since this build. Use a new output folder."
        else:
            shutil.copy2(source, backup)
    replacements = {"MattsSDKBoostingTools/" + name: (ROOT / "mod_extracted/MattsSDKBoostingTools" / name).read_bytes() for name in CHANGED}
    for name, data in replacements.items():
        compile(data, name, "exec")
    sdk = output / source_sdk.name
    with zipfile.ZipFile(source_sdk) as src, zipfile.ZipFile(sdk, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            dst.writestr(info, replacements.pop(info.filename, src.read(info.filename)))
        for name, data in replacements.items():
            dst.writestr(name, data)
    with zipfile.ZipFile(source_sdk) as src, zipfile.ZipFile(sdk) as dst:
        assert dst.testzip() is None
        for name in src.namelist():
            if name.rsplit("/", 1)[-1] not in CHANGED:
                assert src.read(name) == dst.read(name), name
    pak = parse_pak(source_pak)
    raw = pak["raw"]
    controller = "js/dashboard/dashboard_controller.js"
    entry = next(e for e in pak["files"] if e["name"] == controller)
    old_js = extract_payload(raw, entry)
    assert b"window.MsbtAfkShiftLink" not in old_js, "Already patched"
    new_js = old_js + b"\n" + (Path(__file__).with_name("shift_link.js").read_bytes() + b"\n" + Path(__file__).with_name("shift_float.js").read_bytes())
    magic, version, index_offset, index_size = struct.unpack_from("<IIQQ", raw, len(raw) - 44)
    assert magic == 0x5A6F12E1 and version == 3
    old_index = raw[index_offset:index_offset + index_size]
    assert hashlib.sha1(old_index).digest() == raw[-20:]
    chunks = [zlib.compress(new_js[i:i+65536]) for i in range(0, len(new_js), 65536)]
    compressed = b"".join(chunks)
    cursor = index_offset + 57 + 16 * len(chunks)
    blocks = []
    for chunk in chunks:
        blocks.append((cursor, cursor + len(chunk)))
        cursor += len(chunk)
    def fields(offset):
        return (struct.pack("<qqqi", offset, len(compressed), len(new_js), 1)
                + hashlib.sha1(compressed).digest() + struct.pack("<i", len(blocks))
                + b"".join(struct.pack("<qq", a, b) for a, b in blocks) + struct.pack("<BI", 0, 65536))
    _, pos = read_fstring(old_index, 0)
    count, = struct.unpack_from("<i", old_index, pos)
    pos += 4
    parts = [old_index[:pos]]
    for _ in range(count):
        start = pos
        name, fields_start = read_fstring(old_index, pos)
        _, pos = parse_entry_fields(old_index, fields_start)
        parts.append(old_index[start:fields_start] + (fields(index_offset) if name == controller else old_index[fields_start:pos]))
    index = b"".join(parts)
    data = raw[:index_offset] + fields(0) + compressed
    rebuilt = data + index + struct.pack("<IIQQ", magic, version, len(data), len(index)) + hashlib.sha1(index).digest()
    target = output / source_pak.name
    target.write_bytes(rebuilt)
    check = parse_pak(target)
    assert check["index_left"] == 0 and len(check["files"]) == len(pak["files"])
    for before, after in zip(pak["files"], check["files"]):
        assert before["name"] == after["name"]
        payload = extract_payload(rebuilt, after)
        assert payload == (new_js if before["name"] == controller else extract_payload(raw, before))
        packed = b"".join(rebuilt[a:b] for a,b in after["blocks"]) if after["method"] else payload
        assert hashlib.sha1(packed).hexdigest() == after["hash"]
    (output / "dashboard_controller.js").write_bytes(new_js)
    manifest = {"game": str(game), "sdk_changed": list(CHANGED), "pak_files_verified": count,
                "pak_changed": [controller], "files": []}
    for source, built in ((source_sdk, sdk), (source_pak, target)):
        manifest["files"].append({"source": str(source), "built": str(built), "original_sha256": sha(source.read_bytes()), "test_sha256": sha(built.read_bytes())})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("game", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.game, args.output)
