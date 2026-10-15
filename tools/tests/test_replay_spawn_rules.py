"""Replay beginnings use authored context and earlier accessible native stations."""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / 'tools/mission_lab'))
from replay_spawn_rules import choose_station, station_context, station_requirements


def point(x, world='World_P', objective='step'):
    return dict(map=world, location=dict(x=x, y=0, z=0), objective=objective)


def test_mission_beginning_uses_its_own_entry_instead_of_a_remote_prerequisite():
    from build_selection_catalog import start_waypoint
    entry=point(100);definition=dict(entry_anchor=entry,predecessor='prior',groups=[])
    prior=dict(groups=[dict(index=9,objectives=[dict(completion_anchor=point(90000))])])
    result=start_waypoint(definition,dict(index=0),None,{'prior':prior},lambda _,row: [(row['groups'][0],row['groups'][0]['objectives'][0])])
    assert result==dict(entry,source_rule='authored mission entry')
    assert station_context(definition,dict(index=0),dict(name='start'),result,1,{},first_section=True)==('World_P',[result],'authored mission entry')


def test_wrath_beginning_is_at_its_mission_giver_not_zadras_lab():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_selection_states.json').read_text())['missions']
    start=data['Mission_Main_Shatteredlands1']['sections']['0']
    assert start['start_waypoint']['source_rule']=='authored mission entry'
    assert start['location']==dict(x=51065.662628,y=-164759.321477,z=16551.216278)
    assert 'zadra' not in start['station'].lower()


def test_parallel_evidence_collection_returns_to_crime_scene_instead_of_locked_station():
    from build_selection_catalog import start_waypoint
    definition=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_text())['missions']['Mission_DLC_Mandolin']
    by_index={g['index']:g for g in definition['groups']}
    anchor=start_waypoint(definition,by_index[8],(by_index[7],by_index[7]['objectives'][0]),{},None)
    assert anchor['objective']=='Mandolin_Crime_Scene_Echo_Scan'
    assert anchor['source_rule']=='return to preceding collection section start'
    assert anchor['location']==dict(x=-52005.222252,y=-45277.645714,z=46305.0)


def test_investigation_picker_keeps_travel_and_next_section_begins_at_finished_table():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_selection_states.json').read_text())['missions']
    sections=data['Mission_DLC_Mandolin']['sections']
    assert sections['4']['initial_objectives']==['mandolin_reach_crime_scene']
    assert all(str(i) not in sections for i in range(5,9))
    following=sections['9']
    assert following['start_waypoint']['source_rule']=='previous main section completion area'
    assert following['location']==dict(x=-52005.222252,y=-45277.645714,z=46305.0)
    assert following['native_station_fallback'] is False
    assert {'mandolin_place_bottle','mandolin_place_paper','mandolin_place_head'} <= set(following['past_objectives'])


@pytest.mark.parametrize('far,cross_map,reused',[(True,False,False),(False,True,False),(False,False,True)])
def test_collection_return_requires_a_nearby_same_map_strictly_past_point(far,cross_map,reused):
    from build_selection_catalog import start_waypoint
    earlier=dict(index=0,objectives=[dict(name='scan',completion_anchor=point(0))])
    previous=dict(index=1,start_anchor=point(0,objective='scan'),objectives=[
        dict(name='collect',wait_for_objectives=['a','b']),dict(name='a',completion_anchor=point(5000)),
        dict(name='b',completion_anchor=point(6000))])
    selected=dict(index=2,objectives=[dict(name='place',completion_anchor=point(2000 if far else 10,'Other_P' if cross_map else 'World_P'))])
    if reused:selected['objectives'].append(dict(name='scan'))
    assert start_waypoint(dict(groups=[earlier,previous,selected]),selected,
                          (previous,previous['objectives'][0]),{},None) is None


def station(name, x, **extra):
    return dict(station='World_P.'+name, world='World_P', typedef='Respawn', x=str(x), y='0', z='0', **extra)


def rows():
    return {'past':dict(mission_set='past_set',definition=dict(groups=[dict(index=0,objectives=[dict(name='unlock')])])),
            'selected':dict(mission_set='selected_set',definition=dict(groups=[dict(index=0,objectives=[dict(name='earlier')])])),
            'future':dict(mission_set='future_set',definition=dict(groups=[dict(index=0,objectives=[dict(name='later')])]))}


def gate(mission, objective):
    return json.dumps(dict(structtype="Asset'/Script/GbxGame.MissionDependencyCondition_Objective'",
                          mission="mission'"+mission+"'",objective=objective))


def test_nearby_respawn_beats_alphabetical_map_entrance_and_send_only():
    entries=[station('AAA_Entrance',0),station('Nearby',100),dict(station('SendOnly',101),typedef='fast_travel_sendonly')]
    picked, location, requirements=choose_station(entries,'world_p',[point(102)],'selected',set(),{'past'},rows())
    assert picked['station']=='World_P.Nearby' and location['x']==100 and requirements==[]


def test_native_receive_only_point_is_valid_but_send_only_and_unreviewed_transitions_are_not():
    entries=[station('FarRespawn',0),dict(station('Arrival',100),typedef='DestinationOnly'),
             dict(station('Send',101),typedef='fast_travel_sendonly'),dict(station('Exit',102),typedef='Level')]
    assert choose_station(entries,'World_P',[point(102)],'selected',set(),set(),rows())[0]['station']=='World_P.Arrival'


def test_future_station_gate_is_rejected_and_owned_past_gate_is_recorded():
    entries=[station('Future',102,dependency=gate('future','later')),
             station('Past',100,dependency=gate('past','unlock')),station('Further',0)]
    picked,_,requirements=choose_station(entries,'World_P',[point(102)],'selected',set(),{'past'},rows())
    assert picked['station']=='World_P.Past'
    assert requirements==[dict(mission_set='past_set',mission='past',objective='unlock')]
    assert station_requirements(station('Current',0,dependency=gate('selected','earlier')),'selected',set(),{'past'},rows()) is None
    assert station_requirements(station('Current',0,dependency=gate('selected','earlier')),'selected',{'earlier'},{'past'},rows())


@pytest.mark.parametrize('condition',[
    '(missions.past_set.past.Final.unlock_endstate == Completed)',
    '(missions.past_set.past.Status == Completed)',
])
def test_positive_owned_completion_expression_is_supported(condition):
    assert station_requirements(station('Gate',0,dependency=condition),'selected',set(),{'past'},rows()) is not None


@pytest.mark.parametrize('condition',[
    '(missions.future_set.future.Status == Completed)',
    '(missions.past_set.past.Status != Active)',
    '(missions.past_set.past.Status == Completed) || unknown',
    '(missions.wrong_set.past.Final.unlock_endstate == Completed)',
    gate('past','not_in_definition'),
])
def test_future_unknown_compound_and_wrong_identity_conditions_do_not_unlock_station(condition):
    assert station_requirements(station('Gate',0,dependency=condition),'selected',set(),{'past'},rows()) is None


def test_composite_uses_required_substep_locations_without_exposing_them_as_sections():
    primary=dict(name='tracker',completion_anchor=point(999))
    first=dict(index=1,objectives=[primary,dict(name='required_child',hidden=True,completion_anchor=point(100)),
                                   dict(name='optional',optional=True,completion_anchor=point(9999))])
    later=dict(index=2,objectives=[primary])
    world,points,basis=station_context(dict(groups=[first,later],execution_map='World_P'),first,primary,None,3,{})
    assert world=='World_P' and [p['location']['x'] for p in points]==[100]
    assert basis=='required section waypoints'


def test_no_point_does_not_guess_alphabetical_station():
    assert choose_station([station('AAA',0)],'World_P',[],'selected',set(),set(),rows()) is None


def test_native_fast_travel_arrival_does_not_require_completing_its_future_unlock():
    definitions=rows()
    for row in definitions.values():row['campaign']='story'
    entries=[station('FarRespawn',0),dict(station('NearbyFT',100,dependency=gate('future','later')),typedef='fast_travel')]
    chosen,_,flags=choose_station(entries,'World_P',[point(101)],'selected',set(),set(),definitions)
    assert chosen['station']=='World_P.NearbyFT' and flags==[]
    definitions['future']['campaign']='unowned_other_pack'
    assert choose_station(entries,'World_P',[point(101)],'selected',set(),set(),definitions)[0]['station']=='World_P.FarRespawn'
    entries[1]['dependency']=gate('future','unknown_objective')
    definitions['future']['campaign']='story'
    assert choose_station(entries,'World_P',[point(101)],'selected',set(),set(),definitions)[0]['station']=='World_P.FarRespawn'


def test_all_previous_unresolved_arrivals_now_have_authored_departure_or_entry_locations():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_selection_states.json').read_text(encoding='utf-8'))['missions']
    for name,index in [('mission_main_cowbell0','0'),('Mission_Main_Harmonica0','0'),('Mission_DLC_Mandolin','0')]:
        section=data[name]['sections'][index]
        assert section['world']=='World_P'
        assert 'unresolved' not in section['station_selection']
        assert section['station_anchors'][0]['pointer']
    # These are internal travel steps now contained within a guide section.
    assert '29' not in data['Mission_Main_Shatteredlands3']['sections']
    assert '11' not in data['Mission_Main_City2']['sections']
    chase=data['Mission_Main_Harmonica2']['sections']['16']
    assert chase['station']=='Harmonica_P.FT_Harmonica_IslandHub'
    assert chase['station_prerequisites']==[]


def test_previous_section_fallback_uses_only_finished_required_completion_points():
    from build_selection_catalog import preceding_required_anchor
    required=dict(name='required',completion_anchor=point(100))
    optional=dict(name='child',optional_for_spawn=True,completion_anchor=point(999))
    tracker=dict(name='tracker',completion_anchor=point(9999))
    definition=dict(groups=[dict(index=1,objectives=[required,optional,tracker]),dict(index=2,objectives=[tracker])])
    assert preceding_required_anchor(definition,1,2)==required['completion_anchor']
    definition['groups'][0]['objectives'].append(dict(name='other',completion_anchor=point(200)))
    assert preceding_required_anchor(definition,1,2) is None
    definition['groups'][0]['objectives']=[required,dict(name='travel',travel_map='Other_P')]
    assert preceding_required_anchor(definition,1,2) is None
    definition['groups'][0]['objectives']=[dict(name='enemy',scene_anchor=point(100))]
    assert preceding_required_anchor(definition,1,2) is None


def test_all_supported_sections_have_an_authored_nearby_station_and_safe_gate_ownership():
    folder=ROOT/'mod_extracted/MattsSDKBoostingTools'
    data=json.loads((folder/'mission_selection_states.json').read_text(encoding='utf-8'))['missions']
    stations={s['station']:s for s in json.loads((folder/'travelstations.json').read_text())['stations']}
    assert len(data)==39 and sum(len(r['sections']) for r in data.values())==126
    for row in data.values():
        for section in row['sections'].values():
            assert not section.get('spawn_issue')
            native=stations[section['station']]
            assert native['typedef'].casefold() in ('respawn','fast_travel','destinationonly')
            assert native['world'].casefold()==section['world'].casefold()
            assert section['station_location']=={k:float(native[k]) for k in ('x','y','z')}
            assert section['station_anchors']
            assert all(p['map'].casefold()==section['world'].casefold() for p in section['station_anchors'])
            for flag in section['station_prerequisites']:
                owner=[flag['mission_set'],flag['mission']]
                assert owner in row['past_missions'] or (owner==[row['mission_set'],row['saved_mission']]
                    and flag['objective'] in section['past_objectives'])
    rescue=data['Mission_Main_Harmonica4']['sections']
    assert rescue['5']['station']=='VolcanoFortress_P.FTS_VolcanoFortress_Start'
    assert 'placehands' in rescue['5']['past_objectives']
    assert rescue['13']['world']=='VolcanoFortress_P'
    assert rescue['5']['station_prerequisites'][0]['objective']=='placehands'


def test_boss_arrival_policy_requires_native_destination_and_authored_boss_reference():
    from replay_spawn_rules import retain_native_boss_arrival
    boss=dict(scene_anchor=dict(gameplay_pointer='/objective/graph_data/gameplay/bossfight'))
    assert retain_native_boss_arrival(dict(typedef='DestinationOnly'),boss)
    for kind in ('respawn','fast_travel',''):
        assert not retain_native_boss_arrival(dict(typedef=kind),boss)
    assert not retain_native_boss_arrival(dict(typedef='DestinationOnly'),dict(name='KillSomething'))


def test_native_arena_arrivals_are_not_overridden_by_earlier_barrier_triggers():
    from replay_spawn_rules import retain_native_boss_arrival
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_selection_states.json').read_text(encoding='utf-8'))['missions']
    native=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_text())['missions']
    expected=[('Mission_DLC_Mandolin',37),('Mission_Main_Cowbell3',29),('Mission_Main_Cowbell5',9)]
    for name,index in expected:
        # Bosses remain executable inside their larger route, not separate choices.
        assert str(index) not in data[name]['sections']
        group=next(g for g in native[name]['groups'] if g['index']==index)
        assert any(retain_native_boss_arrival(dict(typedef='DestinationOnly'),o) for o in group['objectives'])
    assert set(data['Mission_Main_Shatteredlands3']['sections'])=={'0','8','22'}
    assert set(data['Mission_Main_City3']['sections'])=={'0','7','11'}
