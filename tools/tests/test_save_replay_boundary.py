"""Replay edits must restore observed outcomes and preserve character data."""
import importlib.util
from pathlib import Path
import sys

import pytest
import yaml

SOURCE = Path(__file__).parents[1] / 'mission_lab/save_replay_boundary.py'
spec = importlib.util.spec_from_file_location('save_replay_boundary', SOURCE)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

OBSERVED = '''state:
  checkpoint_name: World_P.OldStation
  inventory: !native [{serial: AbC, count: 1}]
  experience: {level: 70, rank: 701}
  currency: 999
missions:
  tracked_missions: [selected]
  local_sets:
    selected_set:
      missions:
        selected:
          status: Active
          cursorposition: 3
          ui_flags: 17
          final:
            first_endstate: completed
            parent_endstate: deactivated
            fight_endstate: completed
          objectives:
            first:
              status: Completed_PostFinished
            parent:
              status: Deactivated_PostFinished
            fight:
              status: Completed_PostFinished
            later:
              status: Active
    previous_set:
      missions:
        previous:
          status: completed
    future_set:
      missions:
        future:
          status: Active
        future_two:
          status: completed
        parallel:
          status: Active
globals:
  movegrant_glide: TRUE
gbx_discovery_pc: {map: visible}
'''


def boundary(**kwargs):
    fields = dict(mission_set='selected_set', mission='selected', checkpoint=2,
                  station='World_P.NativeStation', past_objectives=('first', 'parent'),
                  future_objectives=('fight', 'later'),
                  future_missions=(('future_set', 'future'), ('future_set', 'future_two')))
    fields.update(kwargs)
    return m.Boundary(**fields)


def selected(text):
    return m.record(yaml.compose(text), 'selected_set', 'selected')


def test_completed_selected_mission_reopens_with_observed_active_evidence():
    current = OBSERVED.replace('status: Active', 'status: completed', 1)
    edited, receipt = m.prepare(current, OBSERVED, boundary())
    assert m.member(selected(edited), 'status').value == 'Active'
    assert receipt['selected_mission_reopened'] is True
    assert m.canonical(m.member(m.member(yaml.compose(edited), 'state'), 'inventory')) == m.canonical(m.member(m.member(yaml.compose(current), 'state'), 'inventory'))


def test_restores_missing_past_preserves_native_branch_and_character():
    current = OBSERVED.replace('            first:\n              status: Completed_PostFinished\n', '')
    current = current.replace('parent:\n              status: Deactivated_PostFinished', 'parent:\n              status: Active')
    edited, receipt = m.prepare(current, OBSERVED, boundary())
    objectives = m.member(selected(edited), 'objectives')
    assert set(m.mapping(objectives)) == {'first', 'parent'}
    assert m.member(m.member(objectives, 'parent'), 'status').value == 'Deactivated_PostFinished'
    assert set(m.mapping(m.member(selected(edited), 'final'))) == {'first_endstate', 'parent_endstate'}
    before, after = yaml.compose(current), yaml.compose(edited)
    for field in ('globals', 'gbx_discovery_pc'):
        assert m.canonical(m.member(before, field)) == m.canonical(m.member(after, field))
    for field in ('inventory', 'experience', 'currency'):
        assert m.canonical(m.member(m.member(before, 'state'), field)) == m.canonical(m.member(m.member(after, 'state'), field))
    sets = m.member(m.member(after, 'missions'), 'local_sets')
    assert set(m.mapping(m.member(m.member(sets, 'future_set'), 'missions'))) == {'parallel'}
    assert receipt['preserved_unowned_data'] and not receipt['installed']


def test_clears_entire_future_set_without_touching_previous():
    current = OBSERVED.replace('        parallel:\n          status: Active\n', '')
    edited, _ = m.prepare(current, current, boundary())
    sets = m.member(m.member(yaml.compose(edited), 'missions'), 'local_sets')
    assert set(m.mapping(sets)) == {'selected_set', 'previous_set'}


def test_fills_missing_previous_mission_set_from_exact_completed_template():
    current = OBSERVED.replace('    previous_set:\n      missions:\n        previous:\n          status: completed\n', '')
    edited, _ = m.prepare(current, OBSERVED, boundary(past_missions=(('previous_set', 'previous'),)))
    assert m.member(m.record(yaml.compose(edited), 'previous_set', 'previous'), 'status').value == 'completed'


def test_repairs_previous_mission_without_copying_rewards():
    current = OBSERVED.replace('previous:\n          status: completed', 'previous:\n          status: Active')
    edited, _ = m.prepare(current, OBSERVED, boundary(past_missions=(('previous_set', 'previous'),)))
    assert m.member(m.record(yaml.compose(edited), 'previous_set', 'previous'), 'status').value == 'completed'


def test_reused_objective_future_ownership_wins():
    edited, _ = m.prepare(OBSERVED, OBSERVED, boundary(past_objectives=('first', 'parent', 'fight')))
    assert 'fight' not in m.mapping(m.member(selected(edited), 'objectives'))


def test_missing_past_evidence_refuses_candidate():
    observed = OBSERVED.replace('            first:\n              status: Completed_PostFinished\n', '')
    with pytest.raises(m.BoundaryError, match='Missing earlier objective evidence'):
        m.prepare(OBSERVED, observed, boundary())


def test_nonterminal_past_evidence_refuses_candidate():
    observed = OBSERVED.replace('first:\n              status: Completed_PostFinished', 'first:\n              status: Active')
    with pytest.raises(m.BoundaryError, match='not observed terminal'):
        m.prepare(OBSERVED, observed, boundary())


def test_unknown_objective_refuses_silent_future_contamination():
    with pytest.raises(m.BoundaryError, match='no reviewed boundary ownership'):
        m.prepare(OBSERVED, OBSERVED, boundary(future_objectives=('fight',)))


def test_duplicate_protected_keys_refuse_candidate():
    with pytest.raises(m.BoundaryError, match='duplicate save key'):
        m.prepare(OBSERVED.replace('  currency: 999', '  currency: 999\n  currency: 100'), OBSERVED, boundary())


def test_does_not_force_active_previous_mission_from_unverified_template():
    with pytest.raises(m.BoundaryError, match='not observed completed'):
        m.prepare(OBSERVED, OBSERVED.replace('previous:\n          status: completed', 'previous:\n          status: Active'),
                  boundary(past_missions=(('previous_set', 'previous'),)))


def test_preserves_scalar_tags_and_quotes():
    current = OBSERVED.replace('cursorposition: 3', 'cursorposition: !nativecursor "3"')
    current = current.replace('checkpoint_name: World_P.OldStation', "checkpoint_name: !nativecheckpoint 'World_P.OldStation'")
    edited, _ = m.prepare(current, OBSERVED, boundary())
    assert m.member(selected(edited), 'cursorposition').tag == '!nativecursor'
    assert m.member(selected(edited), 'cursorposition').value == '2'
    assert m.member(m.member(yaml.compose(edited), 'state'), 'checkpoint_name').tag == '!nativecheckpoint'


def test_retains_unowned_future_set_metadata():
    current = OBSERVED.replace('        parallel:\n          status: Active\n', '')
    current = current.replace('    future_set:\n      missions:', '    future_set:\n      ui_flags: !nativeflag 8\n      missions:')
    edited, _ = m.prepare(current, current, boundary())
    sets = m.member(m.member(yaml.compose(edited), 'missions'), 'local_sets')
    future = m.member(sets, 'future_set')
    assert m.member(future, 'ui_flags').tag == '!nativeflag'
    assert m.mapping(m.member(future, 'missions')) == {}


def test_conflicting_casefolded_evidence_is_rejected():
    current = OBSERVED.replace('            first:', '            FIRST:\n              status: Deactivated_PostFinished\n            first:')
    with pytest.raises(m.BoundaryError, match='Conflicting case-insensitive'):
        m.prepare(current, current, boundary())


def test_preserves_tagged_objective_mapping_and_empty_opening():
    current = OBSERVED.replace('          objectives:\n', '          objectives: !nativeobjectives\n')
    edited, _ = m.prepare(current, OBSERVED, boundary(checkpoint=0, past_objectives=(), future_objectives=('first', 'parent', 'fight', 'later')))
    objectives = m.member(selected(edited), 'objectives')
    assert objectives.tag == '!nativeobjectives'
    assert m.mapping(objectives) == {}
    assert m.mapping(m.member(selected(edited), 'final')) == {}
