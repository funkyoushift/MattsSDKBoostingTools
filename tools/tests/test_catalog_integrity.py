"""Generated catalog hashes must survive checkout newline conversion only."""
import hashlib
import importlib.util
import json
from pathlib import Path

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
