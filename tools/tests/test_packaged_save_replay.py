"""Packaged reference scope and protected data, using synthetic character fields."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
import yaml

ROOT = Path(__file__).parents[2]
HELPERS = ROOT / 'external_app/v22_parts_codes_fixed'
sys.path.insert(0, str(HELPERS))
import mission_save_replay as helper
from mission_save_boundary import BoundaryError, canonical, member

MANIFEST = json.loads((ROOT / 'mod_extracted/MattsSDKBoostingTools/mission_save_replay.json').read_text(encoding='utf-8'))
OBSERVED = (HELPERS / 'mission_save_observed.yaml').read_text(encoding='utf-8')
STATE = '''state:
  char_guid: 12345678-1234-1234-1234-123456789abc
  char_name: Test Hunter
  checkpoint_name: World_P.OldStation
  inventory: !native [{serial: AbCase, count: 1}]
  currencies: {cash: 78, eridium: 91}
  experience: {level: 70, specialization: 701}
save_game_header: !native_header {identity: keep}
'''


def spec(index):
    result = copy.deepcopy(MANIFEST)
    result['section'] = result.pop('sections')[str(index)]
    return result


@pytest.mark.parametrize('checkpoint', [28, 32])
def test_packaged_boundary_retains_character_and_native_header(checkpoint):
    original = STATE + OBSERVED
    result = helper.edit(original, spec(checkpoint))
    before, after = yaml.compose(original), yaml.compose(result['yaml'])
    for key in ('inventory', 'currencies', 'experience', 'char_guid', 'char_name'):
        assert canonical(member(member(before, 'state'), key)) == canonical(member(member(after, 'state'), key))
    assert canonical(member(before, 'save_game_header')) == canonical(member(after, 'save_game_header'))
    assert helper.inspect(result['yaml'], spec(checkpoint))['cursor'] == checkpoint


def test_parallel_mountains_branch_is_preserved_not_deleted_as_future():
    tree = yaml.compose(STATE + OBSERVED)
    sets = member(member(tree, 'missions'), 'local_sets')
    extra = yaml.compose('missionset_main_mountains1: {missions: {mission_main_mountains1: {status: Active}}}')
    sets.value.extend(extra.value)
    text = yaml.serialize(tree)
    result = helper.edit(text, spec(28))
    after = member(member(yaml.compose(result['yaml']), 'missions'), 'local_sets')
    assert canonical(member(after, 'missionset_main_mountains1')) == canonical(member(sets, 'missionset_main_mountains1'))


def test_unreviewed_later_story_and_wrong_reference_refuse_edit():
    tree = yaml.compose(STATE + OBSERVED)
    member(member(tree, 'missions'), 'local_sets').value.extend(yaml.compose('missionset_main_unknown_later: {missions: {later: {status: completed}}}').value)
    with pytest.raises(BoundaryError, match='other story progress'):
        helper.edit(yaml.serialize(tree), spec(28))
    bad = spec(28)
    bad['template_sha256'] = '0' * 64
    with pytest.raises(BoundaryError, match='reference data differs'):
        helper.edit(STATE + OBSERVED, bad)


def test_reference_contains_mission_records_only():
    tree = yaml.compose(OBSERVED)
    assert [k.value for k, _ in tree.value] == ['missions']
    assert hashlib.sha256(OBSERVED.encode()).hexdigest() == MANIFEST['template_sha256']
    for personal in ('char_guid', 'save_game_header', 'inventory', 'steamid', 'Loveless'):
        assert personal not in OBSERVED
