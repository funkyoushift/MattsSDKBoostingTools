import importlib.util
import hashlib
import ast
from pathlib import Path


def test_loaded_archive_identity_does_not_change_after_replacement(tmp_path):
    source = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/runtime_identity.py'
    archive = tmp_path / 'test.sdkmod'
    archive.write_bytes(b'loaded bytes')
    namespace = {'__file__':str(archive) + '/MattsSDKBoostingTools/runtime_identity.py', '__package__':'test_package'}
    exec(compile(source.read_text(), str(source), 'exec'), namespace)
    original = namespace['LOADED_SDK'].copy()
    archive.write_bytes(b'new installed bytes')
    assert namespace['LOADED_SDK'] == original
    assert original['sha256'] == hashlib.sha256(b'loaded bytes').hexdigest()
    assert namespace['capture']()['sha256'] != original['sha256']


def test_version_exists_before_bridge_import_captures_identity():
    source = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/__init__.py'
    body = ast.parse(source.read_text(encoding='utf-8')).body
    version = next(i for i, node in enumerate(body) if isinstance(node, ast.AnnAssign)
                   and isinstance(node.target, ast.Name) and node.target.id == '__version__')
    bridge = next(i for i, node in enumerate(body) if isinstance(node, ast.ImportFrom)
                  and node.module == 'external_bridge')
    assert version < bridge
