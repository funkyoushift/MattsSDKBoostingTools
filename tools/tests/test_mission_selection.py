import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools'
spec = importlib.util.spec_from_file_location('selection', ROOT / 'mission_selection.py')
selection = importlib.util.module_from_spec(spec); spec.loader.exec_module(selection)
catalog = json.loads((ROOT / 'mission_practice_catalog.json').read_bytes())


def test_vehicle_section_keeps_execution_steps_but_hides_internal_choices():
    mission = catalog['missions']['Mission_Main_Shatteredlands3']
    choices = dict((g['index'], o['name']) for g, o in selection.main_groups('Mission_Main_Shatteredlands3', mission))
    assert set(choices)=={0,8,22}
    assert not any(i in choices for i in range(12, 22))
    assert all(any(g['index'] == i for g in mission['groups']) for i in range(13, 22))


def test_reused_parent_appears_once_without_removing_beacon_execution():
    mission = catalog['missions']['Mission_Main_Mountains1']
    names = [o['name'] for _, o in selection.main_groups('Mission_Main_Mountains1', mission)]
    assert names.count('MTN1_Reach_Calders_Office') == 1
    assert [g['index'] for g,_ in selection.main_groups('Mission_Main_Mountains1',mission)]==[0,12,27]
    assert len(names)==3
    assert 'MTN1_Place_Beacon_1a' not in names
    assert 'Office_Reached_Breadcrumb' not in names
    assert any(o['name'] == 'MTN1_Place_Beacon_1a' for g in mission['groups'] for o in g['objectives'])


def test_identical_labels_with_distinct_source_identity_are_not_merged():
    d = dict(groups=[dict(index=i, objectives=[dict(name=n, title='Follow Calder')]) for i, n in enumerate(['A', 'B'])])
    assert len(list(selection.main_groups('other', d))) == 2


def test_main_queen_section_keeps_approach_and_internal_bosses_in_execution():
    mission=catalog['missions']['Mission_Main_Shatteredlands3']
    choices={g['index']:o['name'] for g,o in selection.main_groups('Mission_Main_Shatteredlands3',mission)}
    assert choices[22]=='ReturnRamp'
    assert 28 not in choices and 32 not in choices
    assert any(o['name']=='_KillRip_FortFrontBadAss_Sub0' for g in mission['groups'] for o in g['objectives'])


def test_visible_parent_hides_only_its_visible_child_choices():
    d=dict(groups=[dict(index=0,objectives=[dict(name='parent',title='Main',wait_for_objectives=['child']),
                                           dict(name='child',title='Internal')])])
    assert [o['name'] for _,o in selection.main_groups('other',d)]==['parent']


def test_crime_scene_is_one_section_without_removing_any_gameplay_steps():
    import copy
    mission=catalog['missions']['Mission_DLC_Mandolin'];before=copy.deepcopy(mission)
    choices={g['index']:(g,o) for g,o in selection.main_groups('Mission_DLC_Mandolin',mission)}
    assert choices[4][1]['title']=='Crime-scene investigation'
    assert choices[4][0]['replay_end_index']==8
    assert not any(i in choices for i in range(5,9))
    assert 9 in choices and mission==before


def test_changed_investigation_source_does_not_silently_hide_steps():
    import copy, pytest
    mission=copy.deepcopy(catalog['missions']['Mission_DLC_Mandolin'])
    end=next(g for g in mission['groups'] if g['index']==8)
    end['objectives']=[o for o in end['objectives'] if o['name']!='Mandolin_Place_Head']
    with pytest.raises(ValueError, match='source changed'):
        list(selection.main_groups('Mission_DLC_Mandolin',mission))


def test_all_twenty_one_story_missions_use_reviewed_guide_sections_without_deleting_steps():
    import copy
    rules=selection.replay_sections()
    story = {n:r for n,r in rules.items() if r.get('basis') is None}
    assert len(story)==21 and sum(len(r['sections']) for r in story.values())==65
    for name,rule in rules.items():
        definition=catalog['missions'][name];before=copy.deepcopy(definition)
        groups=list(selection.main_groups(name,definition))
        assert [(g['index'],o['name']) for g,o in groups]==[(s['checkpoint'],s['objective']) for s in rule['sections']]
        assert all(groups[i][0]['replay_end_index']==groups[i+1][0]['index']-1 for i in range(len(groups)-1))
        assert definition==before


def test_every_selectable_dlc_has_main_sections_and_retains_all_execution_steps():
    import copy
    selectors=json.loads((ROOT/'mission_selection_states.json').read_bytes())['missions']
    dlc={n:r for n,r in selectors.items() if r['campaign']!='story'}
    assert len(dlc)==18
    assert sum(len(selection.replay_sections()[n]['sections']) for n in dlc)==61
    for name in dlc:
        definition=catalog['missions'][name];before=copy.deepcopy(definition)
        choices=list(selection.main_groups(name,definition))
        assert choices[0][0]['index']==selection.replay_sections()[name].get('entry_checkpoint',0)
        assert choices[-1][0]['replay_end_index']==max(g['index'] for g in definition['groups'])
        assert set(dlc[name]['sections'])=={str(g['index']) for g,_ in choices}
        assert definition==before


def test_dlc_routes_keep_switches_and_pickups_inside_their_main_sections():
    expected={'Mission_Main_Cowbell4':[0,15,21,29],
              'Mission_Main_Harmonica3_Lava':[0,1,5],
              'Mission_Main_Harmonica3_Logistics':[0,7,14],
              'Mission_DLC_Mandolin':[0,4,9,17,18,27,33],
              'Mission_Main_Harmonica4':[0,5,13,17]}
    for name,indices in expected.items():
        assert [g['index'] for g,_ in selection.main_groups(name,catalog['missions'][name])]==indices


def test_reviewed_section_rejects_changed_native_identity():
    import copy,pytest
    name='Mission_Main_City3';definition=copy.deepcopy(catalog['missions'][name])
    section=selection.replay_sections()[name]['sections'][1]
    next(g for g in definition['groups'] if g['index']==section['checkpoint'])['objectives']=[]
    with pytest.raises(ValueError,match='source changed'):list(selection.main_groups(name,definition))


def test_recorded_starts_match_source_identity_and_remain_unverified():
    recorded = json.loads((ROOT / 'mission_recorded_starts.json').read_bytes())
    count = 0
    for name, starts in recorded.items():
        for index, start in starts.items():
            group = next(g for g in catalog['missions'][name]['groups'] if g['index'] == int(index))
            assert any(o['name'].casefold() == start['objective'] for o in group['objectives'])
            assert start['source_hashes'] == catalog['source_hashes']
            assert not start['replay_verified'] and not start['spawn_verified']
            count += 1
    assert count == 6
