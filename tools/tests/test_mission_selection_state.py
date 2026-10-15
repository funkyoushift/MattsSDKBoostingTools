"""Forward/backward progress editing, distinct from gameplay proof."""
import copy
import json
from pathlib import Path
import sys

import pytest
import yaml

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT/'external_app/v22_parts_codes_fixed'))
from mission_selection_state import edit
from mission_save_boundary import canonical, member, record, mapping, BoundaryError
from mission_save_replay import inspect

SAVE = '''state:
  checkpoint_name: World_P.Before
  inventory: !native [{serial: AbC, count: 1}]
  experience: {level: 70, rank: 701}
  char_guid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
  char_name: Synthetic
missions:
  tracked_missions: [old]
  local_sets:
    first_set:
      status: completed
      missions:
        first:
          status: completed
    shared_set:
      status: completed
      flags: !nativeflags 17
      missions:
        future:
          status: completed
        parallel:
          status: Active
          objectives: {stay: {status: Active}}
world_state: !nativeworld {unchanged: 42}
timed_facts: {unchanged: abc}
'''


def spec():
    return dict(kind='selection', mission_set='shared_set', saved_mission='selected',
        past_missions=[['first_set','first'],['second_set','second']],
        future_missions=[['shared_set','future']],
        section=dict(checkpoint=5, station='World_P.Native', past_objectives=['earlier']))


def test_forward_selection_creates_missing_selected_and_prerequisite_preserves_gear_parallel_and_world():
    result = edit(SAVE, spec())
    before, after = yaml.compose(SAVE), yaml.compose(result['yaml'])
    selected = record(after,'shared_set','selected')
    assert member(selected,'status').value == 'Active'
    assert member(selected,'cursorposition').value == '5'
    assert member(record(after,'second_set','second'),'status').value == 'completed'
    assert member(member(selected,'objectives'),'earlier').value[0][1].value == 'Completed_PostFinished'
    assert canonical(record(before,'shared_set','parallel')) == canonical(record(after,'shared_set','parallel'))
    assert 'future' not in mapping(member(member(member(member(after,'missions'),'local_sets'),'shared_set'),'missions'))
    for name in ['world_state','timed_facts']:
        assert canonical(member(before,name)) == canonical(member(after,name))
    assert canonical(member(member(before,'state'),'inventory')) == canonical(member(member(after,'state'),'inventory'))
    assert member(member(member(member(after,'missions'),'local_sets'),'shared_set'),'flags').tag == '!nativeflags'
    assert result['receipt']['preserved_unowned_data'] and not result['receipt']['world_effects_verified']


def test_reselect_earlier_section_removes_later_selected_objectives():
    first = edit(SAVE,spec())['yaml']
    earlier = spec();earlier['section'].update(checkpoint=0,past_objectives=[])
    second = edit(first,earlier)['yaml']
    selected=record(yaml.compose(second),'shared_set','selected')
    assert mapping(member(selected,'objectives')) == {}
    assert member(selected,'cursorposition').value == '0'


def test_conflicting_dependency_ownership_is_rejected():
    bad=spec();bad['future_missions'].append(['first_set','first'])
    with pytest.raises(BoundaryError,match='Conflicting'):edit(SAVE,bad)


def test_native_omitted_zero_cursor_is_read_as_opening_but_not_a_later_checkpoint():
    selection=spec();selection['section'].update(checkpoint=0,initial_objectives=['earlier'])
    text=edit(SAVE,selection)['yaml']
    # Remove by node to cover the actual serializer's indentation.
    tree=yaml.compose(text);rec=record(tree,'shared_set','selected')
    rec.value=[(k,v) for k,v in rec.value if k.value!='cursorposition']
    result=inspect(yaml.serialize(tree),selection)
    assert result['cursor']==0 and result['mission_status']=='Active'
    assert result['cursor']!=5


def test_generated_dependency_order_fills_all_three_routes_before_rising_action_and_keeps_parallel_routes():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_selection_states.json').read_text(encoding='utf-8'))
    rows=data['missions'];target=rows['Mission_Main_SearchForLilith']
    past={m for _,m in target['past_missions']}
    assert {'mission_main_grasslands3','mission_main_mountains3','mission_main_shatteredlands3'} <= past
    shat=rows['Mission_Main_Shatteredlands3']
    assert 'mission_main_mountains1' not in {m for _,m in shat['future_missions']}
    assert 'mission_main_searchforlilith' in {m for _,m in shat['future_missions']}
    for name,row in rows.items():
        for _,past_name in row['past_missions']:
            ancestor=next(r for r in rows.values() if r['saved_mission']==past_name)
            assert ancestor['playthrough']['rank'] < row['playthrough']['rank']
        for section in row['sections'].values():
            assert section['placement'] in ('native', 'waypoint') and section['station'].split('.')[0].casefold()==section['world'].casefold()
            if section['placement'] == 'waypoint':
                assert section['start_waypoint']['map'].casefold() == section['world'].casefold()
                assert section['location'] == section['start_waypoint']['location']
                assert section['native_station_fallback'] is True
            else:
                assert 'location' not in section


def test_dlc_shared_set_uses_authored_mission_dependencies():
    rows=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_selection_states.json').read_text(encoding='utf-8'))['missions']
    target=rows['Mission_Main_Cowbell4']
    assert 'mission_main_cowbell3' in {m for _,m in target['past_missions']}
    assert 'mission_main_cowbell5' in {m for _,m in target['future_missions']}
    assert len(rows)==39 and sum(len(r['sections']) for r in rows.values())==506


def test_source_waypoints_use_previous_main_end_and_never_a_spanning_tracker_future_end():
    sys.path.insert(0, str(ROOT/'tools/mission_lab'))
    from build_selection_catalog import start_waypoint
    anchor = dict(map='World_P', location=dict(x=1, y=2, z=3))
    tracker = dict(name='long_tracker', completion_anchor=anchor)
    first = dict(index=1, objectives=[tracker])
    selected = dict(index=2, objectives=[dict(name='current'), tracker])
    definition = dict(groups=[first, selected])
    assert start_waypoint(definition, selected, (first, tracker), {}, None) is None
    selected['start_anchor'] = anchor
    assert start_waypoint(definition, selected, (first, tracker), {}, None)['source_rule'] == 'previous authored group completion'
    selected['objectives'].pop()
    selected.pop('start_anchor')
    assert start_waypoint(definition, selected, (first, tracker), {}, None)['source_rule'] == 'previous main objective completion'
    rows=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_selection_states.json').read_text(encoding='utf-8'))['missions']
    assert sum(s['placement']=='waypoint' for r in rows.values() for s in r['sections'].values())==326
    assert sum(s['placement']=='native' for r in rows.values() for s in r['sections'].values())==180
