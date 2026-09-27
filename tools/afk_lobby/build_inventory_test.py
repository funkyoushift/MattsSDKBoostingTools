"""Overlay inventory diagnostics onto the unchanged published SDK archive."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    root = Path(__file__).resolve().parents[2]
    source = root / 'mod_extracted/MattsSDKBoostingTools'
    base = root / 'MattsSDKBoostingTools.sdkmod'
    output = root / 'output/inventory-audit'
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'MattsSDKBoostingTools.sdkmod'
    temporary = output / 'inventory-test.tmp'
    prefix = 'MattsSDKBoostingTools/'
    names = ('backend_actions.py', 'external_bridge.py', 'afk_inventory_capture.py',
             'afk_inventory_recovery.py', 'afk_inventory_native_recovery.py')
    patches = {prefix + name: (source / name).read_bytes() for name in names}
    for path, data in patches.items():
        compile(data, path, 'exec')
    with ZipFile(base) as old, ZipFile(temporary, 'w', ZIP_DEFLATED) as new:
        for entry in old.infolist():
            if entry.filename not in patches:
                new.writestr(entry, old.read(entry))
        for path, data in patches.items():
            new.writestr(path, data)
    with ZipFile(base) as old, ZipFile(temporary) as new:
        assert new.testzip() is None
        assert new.read(prefix + 'afk_lobby.py') == old.read(prefix + 'afk_lobby.py')
    temporary.replace(target)
    receipt = dict(read_only=False, automatic_cleanup_enabled=False, installed=False,
                   native_recovery_adapter_enabled=True, password_required=True,
                   sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                   base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
                   release_afk_lobby_unchanged=True, overlay_files=list(names))
    (output / 'build.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
