"""Execute the real sequencer with failed native package-open attempts."""
import ast
from pathlib import Path
from types import SimpleNamespace


def sequencer():
    path = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/serial_rewards.py'
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_process_pending_serial_delivery_sequences')
    clock = [100.0]
    opened = [0]
    calls = []
    player = object()
    seq = {'chunks': [['item']], 'index': 0, 'stage': 'open', 'targets': [0], 'afk_player_state': player, 'post_open_delay': 3}
    env = {'time': SimpleNamespace(time=lambda: clock[0]),
           '_pending_serial_delivery_sequences': [seq],
           '_gbc_session_world_and_gamestate': lambda: ('world', SimpleNamespace(PlayerArray=[player])),
           '_set_serial_delivery_status': lambda *a, **kw: None,
           '_open_all_live_reward_packages': lambda: 999,
           '_open_target_reward_packages': lambda targets: (calls.append(clock[0]) or opened[0]),
           '_clamp_serial_delivery_delay': float}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), 'exec'), env)
    return env, seq, clock, opened, calls


def test_zero_open_does_not_advance_or_resend_and_recovers():
    env, seq, clock, opened, calls = sequencer()
    tick = env['_process_pending_serial_delivery_sequences']
    tick()
    assert seq['stage'] == 'open' and seq['index'] == 0
    clock[0] += 1
    tick()
    assert len(calls) == 1
    clock[0] += 1
    opened[0] = 1
    tick()
    assert seq['stage'] == 'post_open_wait' and seq['index'] == 0
    assert 'open_wait_started' not in seq
    clock[0] += 3
    tick()
    assert seq['index'] == 1 and not env['_pending_serial_delivery_sequences']


def test_open_timeout_is_failure_not_completion():
    env, seq, clock, opened, calls = sequencer()
    tick = env['_process_pending_serial_delivery_sequences']
    tick()
    clock[0] += 30
    tick()
    assert seq['index'] == 0 and seq['afk_error']
    assert not env['_pending_serial_delivery_sequences']


def test_target_open_does_not_fall_back_to_host_manager():
    path=Path(__file__).resolve().parents[2]/'mod_extracted/MattsSDKBoostingTools/serial_rewards.py'
    fn=next(n for n in ast.parse(path.read_text(encoding='utf-8')).body
            if isinstance(n,ast.FunctionDef) and n.name=='_open_target_reward_packages')
    calls=[]
    host=SimpleNamespace(Server_OpenAllPackages=lambda:calls.append('host'))
    guest=SimpleNamespace(Server_OpenAllPackages=lambda:calls.append('guest'))
    managers={0:host,1:None}
    env={'_manager_for_player_index':managers.get,'_log_warning':lambda _:None}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'),env)
    assert env['_open_target_reward_packages']([1])==0 and calls==[]
    managers[1]=guest
    assert env['_open_target_reward_packages']([1])==1 and calls==['guest']
