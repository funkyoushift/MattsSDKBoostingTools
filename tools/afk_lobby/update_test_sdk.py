"""Refresh the staged SDK from the verified installed test; preserve original backups."""
from pathlib import Path
import hashlib
import json
import os
import zipfile

root = Path(__file__).resolve().parents[2]
manifest_path = root / "output/afk-lobby/manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
record = next(f for f in manifest["files"] if f["source"].endswith(".sdkmod"))
installed, staged = Path(record["source"]), Path(record["built"])
installed_hash = hashlib.sha256(installed.read_bytes()).hexdigest()
assert installed_hash in [record.get(k) for k in ("original_sha256", "test_sha256", "previous_test_sha256")]
names = ["afk_lobby.py", "afk_social.py", "shift_overlay.py", "shift_capture.py", "backend_actions.py", "external_bridge.py", "serial_rewards.py"]
changes = {"MattsSDKBoostingTools/" + name: (root / "mod_extracted/MattsSDKBoostingTools" / name).read_bytes() for name in names}
for name, data in changes.items():
    compile(data, name, "exec")
tmp = staged.with_suffix(".next.sdkmod")
with zipfile.ZipFile(installed) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
    for info in src.infolist():
        dst.writestr(info, changes.get(info.filename, src.read(info.filename)))
    for name, data in changes.items():
        if name not in src.namelist():
            dst.writestr(name, data)
with zipfile.ZipFile(installed) as src, zipfile.ZipFile(tmp) as dst:
    assert dst.testzip() is None
    for name in src.namelist():
        assert dst.read(name) == changes.get(name, src.read(name)), name
os.replace(tmp, staged)
record["previous_test_sha256"] = installed_hash
record["test_sha256"] = hashlib.sha256(staged.read_bytes()).hexdigest()
manifest["sdk_changed"] = names
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("Staged SDK verified; unrelated installed members and original backups preserved.")
