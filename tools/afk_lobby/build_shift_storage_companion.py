"""Build an uninstalled SDK storage candidate; no game files are changed."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

SOURCE = Path(__file__).with_name('shift_storage_companion.py')
README = "Shift Management Storage Companion, derived from the optional v4.4 SDK companion.\nOffline candidate: same-process loopback transport requires live validation.\n"

def build(output, write_manifest=True):
    # Reject broken Python before producing an installable archive.
    sources = {
        '__init__.py': SOURCE,
        'shift_peer_process.py': SOURCE.with_name('shift_peer_process.py'),
        'shift_background.py': SOURCE.with_name('shift_background.py'),
        'shift_background_native.py': SOURCE.with_name('shift_background_native.py'),
    }
    for source in sources.values():
        compile(source.read_bytes(), str(source), 'exec')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'ShiftManagement.sdkmod'
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        entries = [('ShiftManagement/' + name, source.read_bytes()) for name, source in sources.items()]
        entries.append(('ShiftManagement/README.txt', README.encode()))
        for name, data in entries:
            entry = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, data)
    with zipfile.ZipFile(target) as archive:
        assert set(archive.namelist()) == {'ShiftManagement/' + name for name in sources} | {'ShiftManagement/README.txt'}
        assert {name.split('/')[0] for name in archive.namelist()} == {target.stem}
        for name, source in sources.items():
            assert archive.read('ShiftManagement/' + name) == source.read_bytes()
        assert archive.testzip() is None
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    receipt = {'companion_sha256': digest, 'archive': target.name,
               'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               'upstream_archive_sha256': '3e31ba6dfb91f014627df7cb9c453a34c8d13d2b49e1c6855bb8955f36ded440',
               'peer_source_sha256': hashlib.sha256(sources['shift_peer_process.py'].read_bytes()).hexdigest(),
               'background_source_sha256': hashlib.sha256(sources['shift_background.py'].read_bytes()).hexdigest(),
               'background_native_source_sha256': hashlib.sha256(sources['shift_background_native.py'].read_bytes()).hexdigest(),
               'status': 'offline candidate; same-process loopback bridge and installation unverified'}
    if write_manifest:
        (output / 'manifest.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    print(json.dumps(build(parser.parse_args().output)))
