"""Capture archive identity once at module load, never re-hash on status polls."""
import hashlib
from pathlib import Path
import sys


def capture():
    source = str(__file__).replace('\\', '/')
    archive = source.split('.sdkmod/', 1)[0] + '.sdkmod' if '.sdkmod/' in source else ''
    result = {'version':getattr(sys.modules.get(__package__), '__version__', None),
              'sdkmod_path':archive, 'sha256':None}
    if archive:
        try:
            result['sha256'] = hashlib.sha256(Path(archive).read_bytes()).hexdigest()
        except OSError:
            pass
    return result


LOADED_SDK = capture()
