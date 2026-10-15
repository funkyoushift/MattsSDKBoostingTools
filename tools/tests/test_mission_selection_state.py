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


def test_closer_native_arrival_keeps_later_station_unlock_incomplete():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_selection_states.json').read_text(encoding='utf-8'))
    chosen=copy.deepcopy(data['missions']['Mission_Main_Harmonica2'])
    chosen['section']=chosen.pop('sections')['16']
    result=edit(SAVE,chosen)
    objective_states=mapping(member(record(yaml.compose(result['yaml']),chosen['mission_set'],chosen['saved_mission']),'objectives'))
    assert chosen['section']['station']=='Harmonica_P.FT_Harmonica_IslandHub'
    assert 'obj_invis_useflakcomputer' not in objective_states
    assert result['receipt']['filled_station_objectives']==0


def test_only_cross_map_dlc_openings_explicitly_restore_the_current_objective():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_selection_states.json').read_bytes())['missions']
    selected=[]
    for name,row in data.items():
        for key,section in row['sections'].items():
            if not section.get('restore_active_objectives'):continue
            chosen=copy.deepcopy(row);chosen['section']=chosen.pop('sections')[key]
            result=edit(SAVE,chosen);tree=yaml.compose(result['yaml'])
            states=mapping(member(record(tree,chosen['mission_set'],chosen['saved_mission']),'objectives'))
            assert section['checkpoint']==0 and not section['past_objectives']
            assert set(states)==set(section['initial_objectives'])
            assert all(member(v,'status').value=='Active' for _,v in states.values())
            selected.append(name.casefold())
    assert set(selected)=={'mission_main_cowbell0','mission_main_harmonica0','mission_dlc_mandolin'}
    assert 'restore_active_objectives' not in data['Mission_Main_Shatteredlands1']['sections']['0']


def test_selected_chained_set_cursor_is_cleared_without_changing_parallel_progress():
    import mission_selection_state as selection
    tree=yaml.compose(SAVE)
    local=member(member(tree,'missions'),'local_sets')
    group=member(local,'shared_set')
    selection.put(group,'cursorposition',yaml.ScalarNode('tag:yaml.org,2002:int','1'))
    parallel=canonical(member(member(group,'missions'),'parallel'))
    result=edit(yaml.serialize(tree),spec());after=yaml.compose(result['yaml'])
    repaired=member(member(member(after,'missions'),'local_sets'),'shared_set')
    assert 'cursorposition' not in mapping(repaired)
    assert canonical(member(member(repaired,'missions'),'parallel'))==parallel
    assert result['receipt']['preserved_unowned_data']


def test_initial_travel_state_rejects_future_or_non_entry_progress():
    bad=spec();bad['section'].update(restore_active_objectives=['future'],initial_objectives=['now'])
    with pytest.raises(BoundaryError,match='initial travel'):edit(SAVE,bad)


def test_native_save_can_omit_unmaterialized_objectives_before_map_travel():
    chosen=spec();chosen['section'].update(checkpoint=0,past_objectives=[],initial_objectives=['travel'])
    result=edit(SAVE,chosen)['yaml']
    tree=yaml.compose(result);rec=record(tree,'shared_set','selected');node=member(rec,'objectives')
    # Native zero/empty facts are omitted rather than serialized as empty maps.
    line_start=result.rfind('\n',0,node.start_mark.index)+1
    line_end=result.find('\n',node.end_mark.index)
    stripped=result[:line_start]+result[line_end+1:]
    state=inspect(stripped,chosen)
    assert state['mission_status']=='Active' and state['cursor']==0
    assert state['objectives']=={}


def test_source_required_station_objective_and_final_flag_are_filled_only_in_owned_past():
    selection=spec();selection['section']['station_prerequisites']=[
        dict(mission_set='first_set',mission='first',objective='native_unlock')]
    result=edit(SAVE,selection);tree=yaml.compose(result['yaml']);rec=record(tree,'first_set','first')
    assert member(member(member(rec,'objectives'),'native_unlock'),'status').value=='Completed_PostFinished'
    assert member(member(rec,'final'),'native_unlock_endstate').value=='completed'
    assert result['receipt']['filled_station_objectives']==1
    before=yaml.compose(SAVE)
    assert canonical(member(before,'world_state'))==canonical(member(tree,'world_state'))
    assert canonical(member(member(before,'state'),'inventory'))==canonical(member(member(tree,'state'),'inventory'))


@pytest.mark.parametrize('flag',[
    dict(mission_set='shared_set',mission='future',objective='unlock'),
    dict(mission_set='shared_set',mission='parallel',objective='unlock'),
    dict(mission_set='shared_set',mission='selected',objective='not_yet_done'),
])
def test_station_cannot_fill_future_or_unowned_objective_progress(flag):
    selection=spec();selection['section']['station_prerequisites']=[flag]
    with pytest.raises(BoundaryError,match='future or unrelated'):edit(SAVE,selection)


GENERATED = json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_selection_states.json').read_text(encoding='utf-8'))['missions']
STATION_CASES = [(name, key) for name,row in GENERATED.items() for key,section in row['sections'].items() if section.get('station_prerequisites')]


@pytest.mark.parametrize('name,key',STATION_CASES)
def test_every_generated_station_gate_survives_the_actual_save_edit(name,key):
    selection=copy.deepcopy(GENERATED[name]);selection['section']=selection.pop('sections')[key]
    result=edit(SAVE,selection);tree=yaml.compose(result['yaml'])
    for flag in selection['section']['station_prerequisites']:
        rec=record(tree,flag['mission_set'],flag['mission'])
        assert member(member(member(rec,'objectives'),flag['objective']),'status').value=='Completed_PostFinished'
        assert member(member(rec,'final'),flag['objective']+'_endstate').value=='completed'
    assert member(member(tree,'state'),'checkpoint_name').value==selection['section']['station']
    assert result['receipt']['preserved_unowned_data']


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
                assert section['native_station_fallback'] is (section['start_waypoint'].get('source_rule') not in (
                    'return to preceding collection section start','previous main section completion area'))
            else:
                assert 'location' not in section


def test_dlc_shared_set_uses_authored_mission_dependencies():
    rows=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_selection_states.json').read_text(encoding='utf-8'))['missions']
    target=rows['Mission_Main_Cowbell4']
    assert 'mission_main_cowbell3' in {m for _,m in target['past_missions']}
    assert 'mission_main_cowbell5' in {m for _,m in target['future_missions']}
    assert len(rows)==39 and sum(len(r['sections']) for r in rows.values())==126


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
    assert sum(s['placement']=='waypoint' for r in rows.values() for s in r['sections'].values())==79
    assert sum(s['placement']=='native' for r in rows.values() for s in r['sections'].values())==47
