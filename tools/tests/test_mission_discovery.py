"""Offline source catalog and prerequisite checks, not guest-save proof."""
import importlib.util
import importlib.resources
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools'

@pytest.fixture
def mod(monkeypatch):
    monkeypatch.setattr(importlib.resources, 'files', lambda package: ROOT)
    spec = importlib.util.spec_from_file_location('discovery_test', ROOT / 'mission_discovery.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('scope', ['map_locations', 'travel_stations'])
def test_parent_before_child_and_no_dummy_discoveries(mod, scope):
    planned = mod.plan(scope, {})
    names = [r['name'] for r in planned]
    assert len(names) == len(set(names)) > 0
    seen = set()
    for row in mod.CATALOG:
        name = row['gbx_discovery_location_meta_data']
        if name not in names:
            continue
        assert row['parentlocation'] in (None, 'None', '') or row['parentlocation'] in seen
        assert 'RaceDummy' not in row['locationtype']
        assert 'DiscoveryNothing' not in row['locationtype']
        seen.add(name)
    with pytest.raises(ValueError):
        mod.plan(scope, {}, names[:1])

def test_repairs_require_unique_completed_ordinary_parent(mod):
    assert all(r['blocked_reason'] for r in mod.plan('travel_requirements', {'missions': []}))
    key, (parent, _) = next(iter(mod.CHECKPOINTS.items()))
    row = dict(source_identity={'name': parent}, generated=0, replication_type=0,
               status_fact={'known_status': 'completed'})
    assert not mod.plan('travel_requirements', {'missions': [row]}, [key])[0]['blocked_reason']
    for field, value in [('generated', 1), ('replication_type', 1)]:
        invalid = dict(row, **{field: value})
        assert mod.plan('travel_requirements', {'missions': [invalid]}, [key])[0]['blocked_reason']
    assert mod.plan('travel_requirements', {'missions': [row, row]}, [key])[0]['blocked_reason']

def test_unknown_selection_rejected(mod):
    with pytest.raises(ValueError):
        mod.plan('travel_requirements', {'missions': []}, ['invented'])


@pytest.mark.parametrize('key', [
    'travel_beach_safehouse', 'travel_cello_power_cell', 'travel_mountains_entry',
    'travel_city_entry', 'travel_city_safehouse', 'travel_shattered_generator',
])
def test_station_claim_repairs_have_unambiguous_positive_source_requirement(mod, key):
    parent, address = mod.CHECKPOINTS[key]
    stations = json.loads((ROOT / 'travelstations.json').read_text())['stations']
    evidence = [r.get('dependency', '') for r in stations
                if address + ' == Completed' in r.get('dependency', '')]
    assert evidence and all('||' not in expr and '!=' not in expr for expr in evidence)
    assert parent == address.split('.')[2]
    assert mod.plan('travel_requirements', {'missions': []}, [key])[0]['blocked_reason']
