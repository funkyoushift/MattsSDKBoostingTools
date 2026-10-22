"""Read-only exact executable and complete-body evidence, not Epic live proof."""
import hashlib
import json
from pathlib import Path

import pefile
import pytest

from tools.compare_native_card_builds import decode

ROOT = Path(__file__).parents[2]
SDK = ROOT / 'mod_extracted/MattsSDKBoostingTools'
KEY = 'epic-6d531d91'
EVIDENCE = json.loads((ROOT / 'docs/native-missions/EPIC_6D531D91_PROFILE.json').read_text())
PROFILES = json.loads((SDK / 'mission_build_profiles.json').read_text())


def test_exact_hash_profile_and_complete_correspondence():
    profile = PROFILES[KEY]
    assert profile['sha256'] == EVIDENCE['files'][1]['sha256']
    assert not EVIDENCE['missing'] and not EVIDENCE['conflicts']
    assert len(EVIDENCE['spans']) == 37
    assert len(EVIDENCE['addresses']) == 51
    assert not EVIDENCE['live_epic'] and not EVIDENCE['game_files_modified']
    assert profile['addresses'] == {
        k: EVIDENCE['addresses'][v]
        for k, v in PROFILES['steam-26007962']['addresses'].items()}
    assert set(profile['fingerprints']) == set(PROFILES['steam-26007962']['fingerprints'])


def test_installed_complete_bodies_and_runtime_fingerprints():
    paths = [Path(row['path']) for row in EVIDENCE['files']]
    if not all(path.is_file() for path in paths):
        pytest.skip('Qualified current Steam and Epic executables are not installed')
    for row, path in zip(EVIDENCE['files'], paths):
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == row['sha256']
    source, target = [pefile.PE(str(path), fast_load=True) for path in paths]
    references = {}
    for row in EVIDENCE['spans']:
        a, b, size = row['steam_rva'], row['epic_rva'], row['size']
        old, new = source.get_data(a, size), target.get_data(b, size)
        assert hashlib.sha256(old).hexdigest() == row['steam_sha256']
        assert hashlib.sha256(new).hexdigest() == row['epic_sha256']
        an, _, ar, ac = decode(old, a)
        bn, _, br, bc = decode(new, b)
        assert an == bn and ac == bc and len(ar) == len(br)
        for x, y in zip(ar, br):
            assert x['kind'] == y['kind'] and x['offset'] == y['offset']
            if x['kind'] == 'branch' and a <= x['target'] < a + size:
                assert y['target'] - b == x['target'] - a
            references.setdefault(x['target'], set()).add(y['target'])
    assert all(len(v) == 1 for v in references.values())
    profile = PROFILES[KEY]
    for key, fingerprint in profile['fingerprints'].items():
        assert target.get_data(int(profile['addresses'][key], 16), len(bytes.fromhex(fingerprint))).hex() == fingerprint
    for filename in ('mission_loader_builds.json', 'dialogue_native_builds.json'):
        data = json.loads((SDK / filename).read_text())
        pairs = [(data['profiles']['steam-26007962'], data['profiles'][KEY])]
        if 'direct' in data:
            pairs.extend((v, data['direct'][KEY][k]) for k, v in data['direct']['steam-26007962'].items() if isinstance(v, dict))
        for old, new in pairs:
            assert EVIDENCE['addresses'][old['rva']] == new['rva']
            fingerprint = new['fingerprint']
            assert target.get_data(int(new['rva'], 16), len(bytes.fromhex(fingerprint))).hex() == fingerprint
