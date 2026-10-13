"""Authored DLC coordinates must survive omitted registry-group fields."""
import importlib.util
import json
import copy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('practice_catalog_builder',ROOT/'tools/mission_lab/build_practice_catalog.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)


def test_tracker_dependencies_do_not_reinterpret_failure_or_compound_conditions():
    external=dict(structtype="Asset'/Script/GbxGame.ObjectiveTypeSettings_External'",subtype='InternalObjective',internalobjective='Child')
    assert builder.completion_dependencies(external)==['Child']
    assert builder.completion_dependencies(dict(external,subtype='Other'))==[]
    resolve=dict(structtype="Asset'/Script/GbxGame.MissionObjectiveAspect_ResolveObjective'",
                 condition=dict(structtype="Asset'/Script/GbxGame.ObjectiveValueEvaluator_ObjectiveStatus'",objective='Child'))
    custom=dict(structtype="Asset'/Script/GbxGame.ObjectiveTypeSettings_Custom'",aspects=[dict(data=resolve)])
    assert builder.completion_dependencies(custom)==['Child']
    for changed in (dict(resolve,type='Fail'),dict(resolve,type='Deactivate'),
                    dict(resolve,condition=dict(resolve['condition'],condition='NotCompleted'))):
        assert builder.completion_dependencies(dict(custom,aspects=[dict(data=changed)]))==[]


def test_rescue_summary_objectives_follow_native_child_completion():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_bytes())['missions']
    group=data['Mission_Main_Harmonica4']['groups'][16]['objectives']
    assert next(o for o in group if o['name']=='MeleeConsoles')['wait_for_objectives']==['ShootLastServer']
    assert next(o for o in group if o['name']=='RescueFL4K')['wait_for_objectives']==['PlaceHarmonytHand']
    assert 'wait_for_objectives' not in next(o for o in group if o['name']=='LaunchShips')


def test_required_optional_children_retain_their_authored_scene_metadata():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_bytes())['missions']
    mission=data['Mission_Side_PlanetaryEscape']
    objectives={o['name']:o for g in mission['groups'] for o in g['objectives']}
    assert objectives['Find_Enriched_Erridium']['wait_for_objectives']==['Break_Locker_1']
    child=objectives['Break_Locker_1']
    assert child['optional'] and child['completion_maps']
    source=json.loads((builder.SOURCE/mission['source']).read_bytes())
    gameplay=builder.resolve(source,child['pointer'])['graph_data']['gameplay']
    assert 'OakInteract' in gameplay['structtype']


def test_composite_dependencies_match_explicit_authored_parent_links():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_bytes())['missions']
    mission=data['Mission_Main_Harmonica4']
    objectives={o['name']:o for g in mission['groups'] for o in g['objectives']}
    source=json.loads((builder.SOURCE/mission['source']).read_bytes())
    for name in ('TakeHands','PlaceHands'):
        parent=objectives[name];raw=builder.resolve(source,parent['pointer'])
        children=parent['wait_for_objectives']
        assert len(children)==int(raw['graph_data']['gameplay']['numsubobjectives'])
        assert all(builder.resolve(source,objectives[c]['pointer'])['parentobjective']==name for c in children)


def test_dynamic_scene_waypoint_requires_one_exact_paired_actor():
    gameplay=dict(structtype="Asset'/Script/OakGame.ObjectiveTypeSettings_OakTravel'",
        detectionmethod='Dynamic',targetactor='NPC',
        additionalwaypoints=[dict(runtimeactor='NPC',staticactor='Arrival')])
    address='registry.harmonica_p.top.base.arrival.__nochannel'
    aliases={'arrival':[dict(map='Harmonica_P',registryname='Arrival')]}
    points={address:[dict(location=dict(x='1',y='2',z='3'),pointer='/waypoint')]}
    assert builder.dynamic_scene_anchor(gameplay,aliases,points)['location']==dict(x=1,y=2,z=3)
    assert builder.dynamic_scene_anchor(dict(gameplay,detectionmethod='Map'),aliases,points) is None
    assert builder.dynamic_scene_anchor(dict(gameplay,targetactor='Other'),aliases,points) is None
    assert builder.dynamic_scene_anchor(dict(gameplay,additionalwaypoints=gameplay['additionalwaypoints']*2),aliases,points) is None
    assert builder.dynamic_scene_anchor(gameplay,{'arrival':aliases['arrival']*2},points) is None
    assert builder.dynamic_scene_anchor(gameplay,aliases,dict(points,**{address.replace('.base.','.other.'):points[address]})) is None
    invalid=copy.deepcopy(points);invalid[address][0]['location']['z']='nan'
    assert builder.dynamic_scene_anchor(gameplay,aliases,invalid) is None


def test_rescue_resume_scene_keeps_checkpoint_completion_unresolved():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_bytes())['missions']
    group=data['Mission_Main_Harmonica4']['groups'][1]
    objective=next(o for o in group['objectives'] if o['name']=='TalktoChew')
    anchor=objective['scene_anchor']
    source=json.loads((builder.SOURCE/anchor['source']).read_bytes())
    point=builder.resolve(source,anchor['pointer'])
    paired=builder.resolve(source,anchor['gameplay_pointer'])
    assert paired==dict(runtimeactor='NPC_MrChew',staticactor='H4_AIN_MRChewArrives')
    assert anchor['map']=='Harmonica_P' and anchor['actor']==point['staticaddress']
    assert anchor['location']=={k:float(v) for k,v in point['loc'].items()}
    assert 'completion_anchor' not in objective
    assert data['Mission_Main_Harmonica4']['groups'][2]['start_anchor'] is None


def test_encounter_stages_at_its_declared_preceding_target_inside_radius():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_bytes())['missions']
    objectives=data['Mission_Main_Harmonica4']['groups'][7]['objectives']
    combat=next(o for o in objectives if o['name']=='KillTediore2')
    entry=next(o for o in objectives if o['name']=='TravelToCombat1')
    assert combat['encounter_scene']['radius']==8000.
    assert combat['encounter_scene']['previousobjective']=='TravelToCombat1'
    assert combat['scene_anchor']==entry['completion_anchor']
    assert combat['completion_anchor']!=combat['scene_anchor']
    # The marker remains an area centre, never replaced with a guessed point.
    assert combat['encounter_scene']['center']==combat['completion_anchor']['location']


def test_encounter_entry_rejects_outside_wrong_map_and_ambiguous_predecessors():
    anchor=dict(map='World_P',location=dict(x=1.,y=2.,z=3.))
    scene=dict(actor=dict(map='World_P'),radius=100.,center=dict(x=0.,y=0.,z=0.),previousobjective='Enter')
    def groups(point):return [dict(index=0,objectives=[dict(name='Enter',completion_anchor=point),dict(name='Combat',encounter_scene=scene)])]
    for point in (dict(anchor,map='Other'),dict(anchor,location=dict(x=101.,y=0.,z=0.))):
        g=groups(point);builder.encounter_staging(g);assert 'scene_anchor' not in g[0]['objectives'][1]
    g=groups(anchor);g[0]['objectives'].append(dict(name='Enter',completion_anchor=dict(anchor,location=dict(x=2.,y=2.,z=3.))))
    builder.encounter_staging(g);assert 'scene_anchor' not in g[0]['objectives'][1]


def test_missing_group_resolves_only_one_authored_registry_address():
    actor=dict(map='Harmonica_P',registryname='Volume_TradingUp_GoToMiningCamp')
    address='registry.harmonica_p.top.base.volume_tradingup_gotominingcamp.__nochannel'
    point=dict(location=dict(x='1',y='2',z='3'),pointer='/actual-waypoint')
    assert builder.actor_locations(actor,{address:[point]})==[(address,point)]
    assert builder.actor_locations(actor,{address:[point],address.replace('.base.','.other.'):[point]})==[]
    assert builder.actor_locations(dict(actor,groupname='Other'),{address:[point]})==[]
    assert builder.actor_locations(actor,{address.replace('harmonica_p','world_p'):[point]})==[]


def test_escort_uses_destination_instead_of_start_or_current_npc():
    assert builder.completion_fields(dict(structtype="Asset'/Script/OakGame.ObjectiveTypeSettings_OakEscort'"))==('endnode',)
    assert builder.completion_fields(dict(structtype="Asset'/Script/OakGame.ObjectiveTypeSettings_OakExchangeItem'"))==('node','npc')


def test_completion_anchors_retain_exact_authored_targets_without_guessing():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_bytes())['missions']
    opening=data['Mission_Main_Harmonica4']['groups'][0]['objectives'][0]
    assert opening['completion_anchor']==data['Mission_Main_Harmonica4']['groups'][1]['start_anchor']
    count=0
    for name,mission in data.items():
        for group in mission['groups']:
            for objective in group['objectives']:
                anchor=objective.get('completion_anchor')
                if not anchor:continue
                count+=1
                assert anchor['mission']==name and anchor['objective']==objective['name']
                assert anchor['map'].casefold() in objective['completion_maps']
                assert not objective.get('travel_map')
                assert not any(issue.get('objective')==objective['name'] for issue in group['unresolved'])
    assert count>0


def test_explicit_map_arrival_overrides_actor_waypoint_map():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_bytes())['missions']
    enter=next(o for g in data['Mission_Main_Grasslands3']['groups'] for o in g['objectives'] if o['name']=='EnterFortress')
    assert enter['travel_map']=='fortress_grasslands_p'
    assert enter['completion_maps']==['fortress_grasslands_p']
    return_world=next(o for g in data['Mission_Main_Grasslands3']['groups'] for o in g['objectives'] if o['name']=='INVISTravelToWorldP')
    assert return_world['travel_map']=='world_p' and return_world['completion_maps']==['world_p']


def test_unused_map_field_does_not_override_trigger_map():
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_bytes())['missions']
    objective=next(o for g in data['Mission_DLC_Viola']['groups'] for o in g['objectives'] if o['name']=='Viola_Travel_Return_From_Phase_1')
    assert 'travel_map' not in objective
    assert objective['completion_maps']==['viola_elpisvile_p']


def test_only_placed_pickups_have_static_completion_targets():
    gameplay=dict(structtype="Asset'/Script/OakGame.ObjectiveTypeSettings_OakPickup'",
                  pickupspawnstrategy=dict(structtype="Asset'/Script/GbxGame.GbxPickupObjectiveSpawnStrategy_Placed'",
                                           pickupspawner='Spawner_TU_GeodeRock'))
    assert builder.completion_aliases(gameplay)==[('pickupspawnstrategy.pickupspawner','Spawner_TU_GeodeRock')]
    gameplay['pickupspawnstrategy']['structtype']="Asset'/Script/GbxGame.GbxPickupObjectiveSpawnStrategy_EnemyDrop'"
    assert builder.completion_aliases(gameplay)==[]
    assert builder.completion_aliases(dict(structtype="Asset'/Script/OakGame.ObjectiveTypeSettings_OakPickup'"))==[]


def test_barter_up_pickup_anchor_uses_authored_spawner_waypoint():
    doc=json.loads((ROOT/'external_app/v22_parts_codes_fixed/matt_editor/LegitItems/Nexus-Data-Mission4.json').read_bytes())
    entry=doc['mission']['records'][0]['entries'][103]
    pickup=entry['__dep_entries'][34]['obj_takeshinyrock']['graph_data']['gameplay']
    assert builder.completion_aliases(pickup)==[('pickupspawnstrategy.pickupspawner','Spawner_TU_GeodeRock')]
    waypoint=entry['__dep_entries'][65]['wp_obj_takeshinyrock_mission_side_harmonica_tradingup']
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_bytes())
    anchor=data['missions']['Mission_Side_Harmonica_TradingUp']['groups'][6]['start_anchor']
    assert anchor['actor']==waypoint['staticaddress']
    assert anchor['location']=={k:float(v) for k,v in waypoint['loc'].items()}


def test_barter_up_authored_trigger_coordinate_is_recovered_exactly():
    source=ROOT/'external_app/v22_parts_codes_fixed/matt_editor/LegitItems/Nexus-Data-Mission4.json'
    doc=json.loads(source.read_bytes());entry=doc['mission']['records'][0]['entries'][103]
    mission=entry['mission_side_harmonica_tradingup']
    aliases={}
    for _,v in builder.walk(mission['alias_nodes']):
        if isinstance(v,dict) and isinstance(v.get('alias'),dict):
            for name in v['alias'].values():aliases[name]=v['aliasdata']['actor']
    locations={}
    for path,v in builder.walk(entry['__dep_entries']):
        if isinstance(v,dict) and v.get('staticaddress') and v.get('loc'):
            locations.setdefault(v['staticaddress'].casefold(),[]).append(dict(location=v['loc'],pointer=path))
    result=builder.actor_locations(aliases['Volume_TradingUp_GoToMiningCamp'],locations)
    assert len(result)==1
    assert result[0][0]=='registry.harmonica_p.top.base.volume_tradingup_gotominingcamp.__nochannel'
    data=json.loads((ROOT/'mod_extracted/MattsSDKBoostingTools/mission_practice_catalog.json').read_bytes())
    anchor=data['missions']['Mission_Side_Harmonica_TradingUp']['groups'][2]['start_anchor']
    assert anchor['actor']==result[0][0]
    assert anchor['location']=={k:float(v) for k,v in result[0][1]['location'].items()}
