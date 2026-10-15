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
    assert 12 in choices and 22 in choices
    assert not any(i in choices for i in range(13, 22))
    assert all(any(g['index'] == i for g in mission['groups']) for i in range(13, 22))


def test_reused_parent_appears_once_without_removing_beacon_execution():
    mission = catalog['missions']['Mission_Main_Mountains1']
    names = [o['name'] for _, o in selection.main_groups('Mission_Main_Mountains1', mission)]
    assert names.count('MTN1_Reach_Calders_Office') == 1
    assert names.count('Obj_FindDefiantCalder_PlayerFacing') == 1
    assert 'MTN1_Place_Beacon_1a' not in names
    assert 'Office_Reached_Breadcrumb' not in names
    assert any(o['name'] == 'MTN1_Place_Beacon_1a' for g in mission['groups'] for o in g['objectives'])


def test_identical_labels_with_distinct_source_identity_are_not_merged():
    d = dict(groups=[dict(index=i, objectives=[dict(name=n, title='Follow Calder')]) for i, n in enumerate(['A', 'B'])])
    assert len(list(selection.main_groups('other', d))) == 2


def test_hidden_tracker_does_not_hide_visible_main_boss_objective():
    mission=catalog['missions']['Mission_Main_Shatteredlands3']
    choices={g['index']:o['name'] for g,o in selection.main_groups('Mission_Main_Shatteredlands3',mission)}
    assert choices[28]=='_KillRip_FortFrontBadAss_Sub0'


def test_visible_parent_hides_only_its_visible_child_choices():
    d=dict(groups=[dict(index=0,objectives=[dict(name='parent',title='Main',wait_for_objectives=['child']),
                                           dict(name='child',title='Internal')])])
    assert [o['name'] for _,o in selection.main_groups('other',d)]==['parent']


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
