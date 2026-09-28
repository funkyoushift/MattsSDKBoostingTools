"""Local installation unlock shared by desktop, Quick Menu and AFK actions."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile


def _path():
    # Stable across replacement of the SDK archive, separate for another install path.
    installation = os.path.normcase(os.path.abspath(str(Path(__file__).parent.parent)))
    key = hashlib.sha256(installation.encode('utf-8')).hexdigest()[:24]
    return Path(os.environ['LOCALAPPDATA']) / 'MattsSDKBoostingTools' / 'unlocks' / (key + '.json')


def authorized(password=None):
    path = _path()
    try:
        saved = json.loads(path.read_text(encoding='utf-8'))
        if saved == {'schema':1, 'unlocked':True}:
            return True
    except (OSError, ValueError):
        pass
    if not isinstance(password, str) or not hmac.compare_digest(password.encode('utf-8'), b'funkyou'):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix=path.stem, suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump({'schema':1, 'unlocked':True}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return True
