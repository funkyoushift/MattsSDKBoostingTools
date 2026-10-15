import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace as N, ModuleType

import pytest

path = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools/mission_replay_spawners.py'
package = ModuleType('replay_spawner_tests')
package.__path__ = [str(path.parent)]
sys.modules[package.__name__] = package
spec = importlib.util.spec_from_file_location('replay_spawner_tests.mission_replay_spawners', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

SPEC = dict(map='World_P', group='base', registry='support', source='native.json', pointer='/objective/spawner')
CURRENT = N(_get_address=lambda: 100, _path_name=lambda: '/Maps/World_P.World_P')


def actor(world):
    return N(GetLevel=lambda: N(OwningWorld=world))


class Component:
    def __init__(self, registry='support', living=(), fail=False, world=CURRENT):
        self.FactsConduit = N(GroupName=N(Name='None'), RegistryName=N(Name=N(Name=registry)))
        self.living, self.fail, self.calls = list(living), fail, []
        self.owner = actor(world)

    def GetOwner(self):
        return self.owner

    def _path_name(self):
        return '/Game/Maps/WorldLevels/World_P/Cell.World_P:PersistentLevel.Spawn.Component'

    def GetAliveActors(self, actor_type, grouped):
        assert (actor_type, grouped) == (2, False)
        return self.living

    def ResetSpawner(self, destroy):
        self.calls.append(destroy)
        if self.fail:
            raise RuntimeError('Uncertain native call')


def run(components, transaction=None, specifications=None, world='World_P', owner_world=None):
    sdk = N(find_all=lambda name, exact: components)
    current = CURRENT if world == 'World_P' else N(_get_address=lambda: 200, _path_name=lambda: '/Maps/' + world + '.' + world)
    m.world = lambda: current
    owner = actor(owner_world if owner_world is not None else current)
    engine = N(check_build=lambda: None)
    return m.refresh_loaded(sdk, engine, owner, specifications or [SPEC],
                            transaction if transaction is not None else {}, lambda receipt: None)


def test_scoped_false_reset_leaves_other_spawners_untouched():
    selected, unrelated = Component(), Component('other')
    result = run([selected, unrelated])
    assert selected.calls == [False] and unrelated.calls == []
    assert result['reset_requests'] == 1 and result['spawn_verified'] is False


def test_preserves_existing_living_enemies():
    selected = Component(living=[object()])
    assert run([selected])['reset_requests'] == 0 and selected.calls == []


def test_returned_reset_is_not_reissued():
    selected, transaction = Component(), {}
    run([selected], transaction)
    run([selected], transaction)
    assert selected.calls == [False]


def test_uncertain_reset_is_not_reissued():
    selected, transaction = Component(fail=True), {}
    with pytest.raises(RuntimeError, match='Uncertain native call'):
        run([selected], transaction)
    with pytest.raises(RuntimeError, match='unconfirmed'):
        run([selected], transaction)
    assert selected.calls == [False]


def test_ambiguous_identity_stops_before_mutation():
    a, b = Component(), Component()
    with pytest.raises(RuntimeError, match='ambiguous'):
        run([a, b])
    assert a.calls == b.calls == []


def test_wrong_map_is_deferred():
    selected = Component()
    assert run([selected], world='Intro_P')['deferred']
    assert selected.calls == []


def test_missing_source_evidence_is_rejected():
    bad = dict(SPEC)
    del bad['pointer']
    selected = Component()
    with pytest.raises(ValueError, match='source evidence'):
        run([selected], specifications=[bad])
    assert selected.calls == []


def test_same_map_stale_world_component_is_never_reset():
    old_world = N(_get_address=lambda: 99, _path_name=CURRENT._path_name)
    stale, selected = Component(world=old_world), Component()
    assert run([stale, selected])['reset_requests'] == 1
    assert stale.calls == [] and selected.calls == [False]


def test_stale_player_world_stops_before_mutation():
    old_world = N(_get_address=lambda: 99, _path_name=CURRENT._path_name)
    selected = Component()
    with pytest.raises(RuntimeError, match='current world'):
        run([selected], owner_world=old_world)
    assert selected.calls == []
