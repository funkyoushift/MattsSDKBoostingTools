"""Native lease identity and one-shot behavior without game mutations."""
import ast
import copy
import json
import struct
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as N

import pytest

ROOT = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools'


def test_bookmark_uses_actual_catalog_membership_and_requires_matching_character(runtime, monkeypatch):
    m, state, _ = runtime
    data = json.loads((ROOT / 'mission_practice_catalog.json').read_text(encoding='utf-8'))['missions']
    monkeypatch.setitem(sys.modules, m.__package__+'.mission_execution', N(DATA=data))
    spec = m.specification('Mission_Main_Shatteredlands3', 28)
    spec.update(kind='bookmark', guid=state['guid'])
    spec['section']['initial_objectives'] = [n.casefold() for n in spec['section']['initial_objectives']]
    result = m.bookmark_specification(spec, state['guid'])
    assert result['force_travel'] and not result['section']['refresh_after_load']
    native = copy.deepcopy(spec);native['section'].pop('location');native['section']['placement'] = 'native'
    assert m.bookmark_specification(native, state['guid'])['section']['placement'] == 'native'
    for field, value in [('guid', 'c'*32), ('catalog_sha256', '0'*64)]:
        bad = dict(spec, **{field:value})
        with pytest.raises(ValueError): m.bookmark_specification(bad, state['guid'])
    for field, value in [('location', dict(x=float('nan'), y=0, z=0)), ('initial_objectives', ['unrelated_objective'])]:
        bad = copy.deepcopy(spec);bad['section'][field] = value
        with pytest.raises(ValueError): m.bookmark_specification(bad, state['guid'])


def test_native_spawn_state_cannot_issue_custom_placement(runtime):
    m, _, payload = runtime
    m._lease['spec']['section']['placement'] = 'native'
    m._place = lambda *args: pytest.fail('Native respawn state must not teleport')
    for action in ('place', 'placement_ready'):
        with pytest.raises(RuntimeError, match='native respawn point'):
            m.dispatch('mission_save_replay_'+action, payload)
    assert 'place_0' not in m._lease['calls']


def test_forward_dlc_selection_rechecks_ownership_before_acquiring_lease(runtime,monkeypatch):
    m,_,_=runtime
    m._lease=None
    progress=sys.modules[m.__package__+'.mission_progression'];progress._party=lambda:[]
    monkeypatch.setitem(sys.modules,m.__package__+'.mission_dlc',N(inspect=lambda rows:{},
        requirement=lambda *args:dict(allowed=False,reason='DLC access is required')))
    with pytest.raises(ValueError,match='DLC access'):
        m.dispatch('mission_save_replay_begin',dict(id='c'*32,mission='Mission_Main_Cowbell4',checkpoint=0,acknowledge_shared_progress=True))
    assert m._lease is None


def test_state_capture_has_no_position_or_grounding_dependency(runtime, monkeypatch):
    m, state, _ = runtime
    m._lease['closed'] = True
    name = 'Mission_Main_Shatteredlands3'
    engine = N(profile='steam-25372571',base=100, snapshot=lambda: {}, u64=lambda addr: 100+0xb973820 if addr==0x1000 else 0,
               fact=lambda *args: dict(tag=2, raw=(b'\x02'+bytes(11)+struct.pack('<i',28)).hex()))
    m._host = lambda: (N(), engine, state['guid'], 'world_p')
    progress = sys.modules[m.__package__+'.mission_progression']
    progress.select = lambda *_: [name]
    progress._row = lambda *_: dict(record='0x1000')
    progress._metadata = lambda *_: dict(title='Synthetic')
    monkeypatch.setitem(sys.modules,m.__package__+'.mission_execution',N(DATA={name:{}},
        objectives=lambda *_:[dict(name='KillMudmouth',group=28,state=4)]))
    captured = m.capture_bookmark()
    assert captured['spec']['section']['placement'] == 'native'
    assert 'location' not in captured['spec']['section']


@pytest.fixture
def runtime(monkeypatch):
    import importlib.resources
    monkeypatch.setattr(importlib.resources,"files",lambda _:ROOT)
    package = ModuleType('save_replay_test_runtime')
    package.__path__ = [str(ROOT)]
    monkeypatch.setitem(sys.modules, package.__name__, package)
    spec = importlib.util.spec_from_file_location(package.__name__ + '.mission_save_replay', ROOT / 'mission_save_replay.py')
    m = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, m)
    spec.loader.exec_module(m)
    m.files = lambda _: ROOT
    m._save = lambda: None
    progress = N(status=lambda: dict(state='idle'))
    monkeypatch.setitem(sys.modules, package.__name__ + '.mission_progression', progress)
    state = {'guid': 'a' * 32, 'world': 'world_p', 'calls': 0}
    m._host = lambda: (N(), N(), state['guid'], state['world'])
    m.dispatch('mission_save_replay_begin', dict(id='b' * 32, mission='Mission_Main_Shatteredlands3', checkpoint=28, acknowledge_shared_progress=True))
    payload = dict(id='b' * 32, session=m.SESSION)
    return m, state, payload


def test_unconfirmed_native_call_is_not_repeated(runtime):
    m, state, _ = runtime
    def fail():
        state['calls'] += 1
        raise RuntimeError('Native call interrupted')
    with pytest.raises(RuntimeError, match='interrupted'):
        m._once('operation', fail)
    with pytest.raises(RuntimeError, match='unconfirmed'):
        m._once('operation', fail)
    assert state['calls'] == 1


def test_returned_native_receipt_is_reconciled_without_resend(runtime):
    m, state, _ = runtime
    def perform():
        state['calls'] += 1
        return dict(ok=True)
    assert m._once('operation', perform) == m._once('operation', perform)
    assert state['calls'] == 1


def test_wrong_character_map_or_session_blocks_placement(runtime):
    m, state, p = runtime
    m._place = lambda *args: pytest.fail('Placement must not execute')
    state['guid'] = 'c' * 32
    with pytest.raises(RuntimeError, match='original character'):
        m.dispatch('mission_save_replay_place', p)
    state.update(guid='a' * 32, world='intro_p')
    with pytest.raises(RuntimeError, match='target map'):
        m.dispatch('mission_save_replay_place', p)
    with pytest.raises(RuntimeError, match='session changed'):
        m.dispatch('mission_save_replay_place', dict(p, session='stale'))


def test_lease_blocks_progress_mutations_but_allows_reads_and_close(runtime):
    m, _, p = runtime
    assert m.conflict('mission_start') and m.conflict('full_progress_start')
    assert not m.conflict('mission_status') and not m.conflict('mission_practice_preview')
    m.dispatch('mission_save_replay_close', p)
    assert not m.conflict('full_progress_start')


def test_actual_backend_router_delegates_save_actions(monkeypatch):
    text = (ROOT / 'backend_actions.py').read_text(encoding='utf-8')
    tree = ast.parse(text)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('full_progress_conflict', 'run_quick_menu_action')]
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), *functions], type_ignores=[])
    pkg = ModuleType('backend_save_router_test');pkg.__path__ = []
    native = N(conflict=lambda _: False, dispatch=lambda key, payload: dict(ok=True, delegated=key))
    pkg.mission_save_replay = native
    monkeypatch.setitem(sys.modules, pkg.__name__, pkg)
    monkeypatch.setitem(sys.modules, pkg.__name__ + '.mission_save_replay', native)
    namespace = dict(__package__=pkg.__name__)
    exec(compile(ast.fix_missing_locations(module), '<backend router>', 'exec'), namespace)
    assert namespace['full_progress_conflict']('mission_practice_preview') is False
    assert namespace['run_quick_menu_action']('mission_save_replay_status')['delegated'] == 'mission_save_replay_status'


@pytest.mark.parametrize('state', ['running', 'uncertain', 'interrupted'])
def test_existing_progress_blocks_begin_and_restore(runtime, monkeypatch, state):
    m, _, p = runtime
    progress = sys.modules[m.__package__ + '.mission_progression']
    monkeypatch.setattr(progress, 'status', lambda: dict(state=state))
    with pytest.raises(RuntimeError, match='unfinished mission'):
        m.dispatch('mission_save_replay_restore_guard', p)
    m.dispatch('mission_save_replay_close', p)
    with pytest.raises(RuntimeError, match='unfinished mission'):
        m.dispatch('mission_save_replay_begin', dict(id='d' * 32, acknowledge_shared_progress=True))


def test_placement_uses_guarded_helper_and_separate_verification(runtime, monkeypatch):
    m, _, p = runtime
    calls = []
    placement = N(start=lambda job, rows, journal: calls.append(('start', job['anchor']['location'])),
                  verify=lambda job, rows: calls.append(('verify', len(rows))) or True)
    monkeypatch.setitem(sys.modules, m.__package__ + '.mission_recorded_placement', placement)
    assert m.dispatch('mission_save_replay_place', p)['placement_requested']
    assert m.dispatch('mission_save_replay_place', p)['placement_requested']
    assert m.dispatch('mission_save_replay_placement_status', p)['placement_verified']
    assert [c[0] for c in calls] == ['start', 'verify']


def test_bridge_routes_and_queues_save_replay():
    tree = ast.parse((ROOT / 'external_bridge.py').read_text(encoding='utf-8'))
    assignments = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_PROGRESS_JOB_ACTIONS' for t in n.targets)]
    scope = {};exec(compile(ast.Module(body=assignments, type_ignores=[]), '<bridge queue>', 'exec'), scope)
    assert 'mission_save_replay_placement_status' in scope['_PROGRESS_JOB_ACTIONS']
    assert 'mission_save_replay_placement_ready' in scope['_PROGRESS_JOB_ACTIONS']
    route = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_handle_action')
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'startswith'
               and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == 'mission_save_replay_'
               for n in ast.walk(route))


def test_unloaded_destination_never_records_a_teleport(runtime, monkeypatch):
    m, _, p = runtime
    def not_ready(*args):
        raise RuntimeError('Recorded location is not loaded or cannot fit this player.')
    placement = N(preflight=not_ready)
    monkeypatch.setitem(sys.modules, m.__package__ + '.mission_recorded_placement', placement)
    assert not m.dispatch('mission_save_replay_placement_ready', p)['placement_ready']
    assert 'place_0' not in m._lease['calls']
    placement.preflight = lambda *args: None
    assert m.dispatch('mission_save_replay_placement_ready', p)['placement_ready']


def test_automatic_loader_is_bound_to_both_characters_slots_and_once_receipts(runtime,monkeypatch):
    m,state,p=runtime;calls=[]
    monkeypatch.setitem(sys.modules,m.__package__+'.mission_character_loader',N(
        select_slot=lambda pc,engine,slot:(calls.append(slot) or dict(ok=True)),
        refresh_saves=lambda *a:dict(ok=True)))
    binding=dict(p,slots=dict(original='C_17',other='C_15'),holding_guid='c'*32)
    assert m.dispatch('mission_save_replay_loader_bind',binding)['bound']
    request=dict(p,role='other',cycle=0,slot='C_15')
    m.dispatch('mission_save_replay_loader_select',request);m.dispatch('mission_save_replay_loader_select',request)
    assert calls==['C_15']
    with pytest.raises(RuntimeError,match='slot differs'):
        m.dispatch('mission_save_replay_loader_select',dict(request,slot='C_99'))
    state['guid']='d'*32
    with pytest.raises(RuntimeError,match='identity differs'):
        m.dispatch('mission_save_replay_loader_select',dict(p,role='original',slot='C_17'))
    state['guid']='c'*32
    m.dispatch('mission_save_replay_loader_select',dict(p,role='original',slot='C_17'))
    assert calls==['C_15','C_17']


def test_automatic_loader_rejects_ambiguous_or_rebound_identities(runtime):
    m,state,p=runtime
    with pytest.raises(ValueError):
        m.dispatch('mission_save_replay_loader_bind',dict(p,slots=dict(original='C_17',other='C_17'),holding_guid='c'*32))
    m.dispatch('mission_save_replay_loader_bind',dict(p,slots=dict(original='C_17',other='C_15'),holding_guid='c'*32))
    with pytest.raises(RuntimeError,match='binding changed'):
        m.dispatch('mission_save_replay_loader_bind',dict(p,slots=dict(original='C_17',other='C_9'),holding_guid='d'*32))
