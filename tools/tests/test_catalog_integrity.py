"""Generated catalog hashes must survive checkout newline conversion only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest


ROOT = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools'
spec = importlib.util.spec_from_file_location('msbt_catalog_integrity_test', ROOT / 'catalog_integrity.py')
integrity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrity)


def test_practice_catalog_accepts_exact_committed_bytes_and_windows_checkout():
    data = (ROOT / 'mission_practice_catalog.json').read_bytes()
    expected = json.loads((ROOT / 'mission_save_replay.json').read_text(encoding='utf-8'))['catalog_sha256']
    assert hashlib.sha256(data).hexdigest() != expected
    assert integrity.verified_digest(data, expected, 'changed') == expected
    assert integrity.verified_digest(data.replace(b'\r\n', b'\n'), expected, 'changed') == expected


def test_integrity_rejects_any_non_newline_content_change():
    data = (ROOT / 'mission_practice_catalog.json').read_bytes()
    expected = json.loads((ROOT / 'mission_save_replay.json').read_text(encoding='utf-8'))['catalog_sha256']
    tampered = data.replace(b'"version": 1', b'"version": 2', 1)
    assert tampered != data
    with pytest.raises(RuntimeError, match='changed'):
        integrity.verified_digest(tampered, expected, 'changed')


def test_station_catalog_accepts_both_line_endings():
    data = (ROOT / 'travelstations.json').read_bytes()
    expected = json.loads((ROOT / 'mission_selection_states.json').read_text(encoding='utf-8'))['travel_stations_sha256']
    assert integrity.verified_digest(data, expected, 'changed') == expected
    assert integrity.verified_digest(data.replace(b'\r\n', b'\n'), expected, 'changed') == expected


def test_selection_specification_uses_verified_catalog_on_windows(monkeypatch):
    import importlib.resources
    monkeypatch.setattr(importlib.resources, 'files', lambda _: ROOT)
    package = ModuleType('selection_integrity_test')
    package.__path__ = [str(ROOT)]
    monkeypatch.setitem(sys.modules, package.__name__, package)
    monkeypatch.setitem(sys.modules, package.__name__ + '.catalog_integrity', integrity)
    module_spec = importlib.util.spec_from_file_location(package.__name__ + '.mission_selection_specs',
                                                         ROOT / 'mission_selection_specs.py')
    module = importlib.util.module_from_spec(module_spec)
    monkeypatch.setitem(sys.modules, module_spec.name, module)
    module_spec.loader.exec_module(module)
    data = json.loads((ROOT / 'mission_selection_states.json').read_text(encoding='utf-8'))
    name, checkpoint = next((name, checkpoint) for name, row in data['missions'].items()
                            for checkpoint, section in row['sections'].items() if not section.get('spawn_issue'))
    result = module.specification(name, checkpoint)
    assert result['catalog_sha256'] == data['catalog_sha256']
    assert result['section']['checkpoint'] == int(checkpoint)
