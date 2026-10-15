"""Captured timeline replay must retain equipment earned after bookmarking."""
import copy
import hashlib
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parents[2] / 'external_app/v22_parts_codes_fixed'))
from mission_save_bookmarks import capture, edit
from mission_save_boundary import BoundaryError, canonical, member

GUID = 'a' * 32
SAVED = '''state:
  char_guid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
  char_name: Synthetic
  checkpoint_name: Map_P.Station
  inventory: !native [{serial: NewGearCase}]
  experience: {level: 70, rank: 200}
save_game_header: !native_header {identity: keep}
missions:
  local_sets:
    missionset_test:
      missions:
        mission_test:
          status: Active
          cursorposition: 3
          objectives:
            encounter: {status: Active}
            next: {status: NotStarted}
world_state: !native_world {door: closed}
timed_facts: {encounter: 0}
progression: {unlocks: [keep]}
globals: {unowned: keep}
'''


def spec():
    return dict(kind='bookmark', guid=GUID, mission='Mission_Test',
                section=dict(checkpoint=3, world='map_p', initial_objectives=['encounter']))


def test_bookmark_rewinds_timeline_but_keeps_current_gear_levels_and_unowned_fields():
    captured = capture(SAVED, spec())
    assert 'inventory' not in captured['snapshot']
    assert 'char_guid' not in captured['snapshot']
    current = SAVED.replace('NewGearCase', 'EarnedLaterCase').replace('level: 70', 'level: 71')
    current = current.replace('cursorposition: 3', 'cursorposition: 9').replace('door: closed', 'door: open')
    result = edit(current, dict(captured['spec'], bookmark_snapshot=captured['snapshot']))
    before, after, original = map(yaml.compose, (current, result['yaml'], SAVED))
    for field in ('state', 'save_game_header', 'progression', 'globals'):
        assert canonical(member(before, field)) == canonical(member(after, field))
    for field in ('missions', 'world_state', 'timed_facts'):
        assert canonical(member(original, field)) == canonical(member(after, field))
    assert not result['receipt']['world_effects_verified']


@pytest.mark.parametrize('change', ['character', 'cursor', 'objectives', 'map'])
def test_capture_rejects_unsaved_or_mismatched_gameplay(change):
    current = SAVED
    if change == 'character': current = current.replace(GUID, 'b' * 32)
    if change == 'cursor': current = current.replace('cursorposition: 3', 'cursorposition: 4')
    if change == 'objectives': current = current.replace('encounter: {status: Active}', 'encounter: {status: Completed}')
    if change == 'map': current = current.replace('Map_P.Station', 'Other_P.Station')
    with pytest.raises(BoundaryError): capture(current, spec())


def test_restore_rejects_changed_snapshot_wrong_character_and_inconsistent_metadata():
    captured = capture(SAVED, spec())
    metadata = dict(captured['spec'], bookmark_snapshot=captured['snapshot'])
    with pytest.raises(BoundaryError): edit(SAVED.replace(GUID, 'b' * 32), metadata)
    with pytest.raises(BoundaryError): edit(SAVED, dict(metadata, bookmark_snapshot=metadata['bookmark_snapshot']+' '))
    bad = copy.deepcopy(metadata)
    bad['section']['checkpoint'] = 4
    with pytest.raises(BoundaryError): edit(SAVED, bad)
    bad = dict(metadata, bookmark_snapshot=captured['snapshot']+'inventory: [unsupported]\n')
    bad['snapshot_sha256'] = hashlib.sha256(bad['bookmark_snapshot'].encode()).hexdigest()
    with pytest.raises(BoundaryError): edit(SAVED, bad)


def test_restore_clears_future_world_fields_that_did_not_exist_when_bookmarked():
    original = SAVED.replace('world_state: !native_world {door: closed}\n', '').replace('timed_facts: {encounter: 0}\n', '')
    captured = capture(original, spec())
    result = edit(SAVED, dict(captured['spec'], bookmark_snapshot=captured['snapshot']))
    assert 'world_state' not in result['yaml'] and 'timed_facts' not in result['yaml']
    assert set(result['receipt']['cleared_fields']) == {'world_state', 'timed_facts'}
    assert canonical(yaml.compose(result['yaml'])) == canonical(yaml.compose(original))
