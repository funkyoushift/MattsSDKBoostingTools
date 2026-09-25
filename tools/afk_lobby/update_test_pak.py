"""Refresh the test PAK from the verified original, preserving other entries."""
from build_test import *
output = ROOT / "output/afk-lobby"
manifest_path = output / "manifest.json"
manifest = json.loads(manifest_path.read_text())
record = next(f for f in manifest["files"] if f["source"].endswith(".pak"))
installed = Path(record["source"])
installed_hash = sha(installed.read_bytes())
assert installed_hash in [record.get(k) for k in ("original_sha256", "test_sha256", "previous_test_sha256")]
source_pak = output / "originals" / installed.name
assert sha(source_pak.read_bytes()) == record["original_sha256"]
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
record["previous_test_sha256"] = installed_hash
record["test_sha256"] = sha(target.read_bytes())
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Verified {count} PAK entries; only dashboard controller changed.")
