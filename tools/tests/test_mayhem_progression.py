"""Target isolation, non-destructive ranks and shared-fact failure handling."""
import importlib.util
from pathlib import Path
import sys
import types
import pytest


@pytest.fixture
def setup(monkeypatch):
    sdk = types.ModuleType('unrealsdk')
    monkeypatch.setitem(sys.modules, 'unrealsdk', sdk)
    path = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools/mayhem_progression.py'
    spec = importlib.util.spec_from_file_location('mayhem_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    values = {module.HIGHEST_RANK: 10, module.INTRO_STATUS: 'Available', 'global.mayhem_level': 3}
    writes = []
    class Facts:
        def ReadFact(self, **kw):
            value = values[kw['AddressString']]
            return (None, str(value), value if isinstance(value, int) else 1, True)
        def WriteFact(self, **kw):
            writes.append(kw)
            values[kw['AddressString']] = kw['AsInt'] if kw['AsName'] == 'None' else kw['AsName']
    facts = Facts()
    sdk.find_object = lambda *args: facts
    player = types.SimpleNamespace(PlayerState=types.SimpleNamespace(HighestUnlockedMayhemLevel=10),
                                   Pawn=object(), HasAuthority=lambda: True)
    return module, player, facts, values, writes


def test_rank_twenty_prepares_access_without_changing_active_difficulty(setup):
    mod, player, _, values, writes = setup
    other = types.SimpleNamespace(HighestUnlockedMayhemLevel=0)
    result = mod.boost(player, 20, 'Papa')
    assert result['ok'] and result['rank'] == 20
    assert player.PlayerState.HighestUnlockedMayhemLevel == 20
    assert other.HighestUnlockedMayhemLevel == 0
    assert values[mod.INTRO_STATUS] == 'Completed'
    assert values['global.mayhem_level'] == 3
    assert {w['AddressString'] for w in writes} == {mod.HIGHEST_RANK, mod.INTRO_STATUS}


@pytest.mark.parametrize('rank', [0, 21, -1, 1.5, True, 'garbage'])
def test_invalid_rank_has_no_writes(setup, rank):
    mod, player, _, _, writes = setup
    with pytest.raises(ValueError): mod.boost(player, rank, 'Papa')
    assert player.PlayerState.HighestUnlockedMayhemLevel == 10 and not writes


def test_never_lowers_unlocks_and_is_idempotent(setup):
    mod, player, _, values, writes = setup
    player.PlayerState.HighestUnlockedMayhemLevel = 20
    values[mod.HIGHEST_RANK] = 20
    values[mod.INTRO_STATUS] = 'Completed'
    assert mod.boost(player, 5, 'Papa')['rank'] == 20
    assert not writes


def test_partial_failure_is_reported_without_fake_rollback(setup):
    mod, player, facts, _, writes = setup
    def fail(**kw): raise RuntimeError('bridge failure')
    facts.WriteFact = fail
    result = mod.boost(player, 20, 'Papa')
    assert not result['ok'] and result['applied'] == ['player rank']
    assert player.PlayerState.HighestUnlockedMayhemLevel == 20


def test_preflight_failure_does_not_change_player(setup):
    mod, player, facts, _, _ = setup
    def fail(**kw): raise RuntimeError('missing fact')
    facts.ReadFact = fail
    with pytest.raises(RuntimeError): mod.boost(player, 20, 'Papa')
    assert player.PlayerState.HighestUnlockedMayhemLevel == 10


def test_backend_rejects_missing_named_target_and_multiple_scope(monkeypatch):
    from test_quick_menu_last_command import _load_backend_actions
    backend = _load_backend_actions()
    targets = types.ModuleType('MattsSDKBoostingTools.farming_targets')
    progression = types.ModuleType('MattsSDKBoostingTools.mayhem_progression')
    def unavailable(*args): raise RuntimeError('Selected player left')
    targets.resolve = unavailable
    progression.boost = lambda *args: pytest.fail('Must not mutate an unresolved target')
    monkeypatch.setitem(sys.modules, targets.__name__, targets)
    monkeypatch.setitem(sys.modules, progression.__name__, progression)
    assert not backend.mayhem_boost({'target_player': '1|Papa', 'mayhem_rank': 20})['ok']
    assert not backend.mayhem_boost({'target_scope': 'all', 'mayhem_rank': 20})['ok']
