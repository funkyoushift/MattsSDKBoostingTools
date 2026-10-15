"""Real queue functions with disconnected, late and independently failing players."""
import ast
import importlib.util
from collections import deque
from pathlib import Path
from types import SimpleNamespace as NS

import pytest


def environment():
    source = (Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools/backend_actions.py').read_text(encoding='utf-8')
    functions = {'uvh_boost_tick', 'uvh_boost_status', 'uvh_boost_cancel', 'uvh_boost_resume', '_uvh_stop_uncertain', '_uvh_queue_for_pc'}
    nodes = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name in functions]
    calls = []
    pc = NS(ServerIncrementChallengeForPlayer=lambda *a: calls.append(a), HasAuthority=lambda: True,
            Pawn=object(),PlayerState=NS(_get_address=lambda:200),_get_address=lambda:100,_path_name=lambda:'world:pc',
            GetLevel=lambda: NS(OwningWorld=NS(_path_name=lambda: 'world')))
    notes = []
    clock=[100.]
    step_path=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools/uvhm_progression.py'
    spec=importlib.util.spec_from_file_location('queue_native_step',step_path)
    step=importlib.util.module_from_spec(spec);spec.loader.exec_module(step)
    step._complete=lambda pc,name:any(n==name for n,c in calls)
    env = dict(Any=object, deque=deque, time=NS(monotonic=lambda: clock[0]), get_pc=lambda: pc,
               _uvh_queue=deque([('UVH 1', 'first', .3), ('UVH 1', 'last', .3)]),
               _uvh_targets=[pc], _uvh_paused_queue=deque(), _uvh_paused_targets=[],
               _uvh_next_at=0., _uvh_running=True, _uvh_failed_count=0, _uvh_sent_count=0,
               _uvh_uncertain=False, _uvh_step_receipts=[], _uvh_native_verified=False,
               _uvh_native_step=step.advance, _uvh_last_status='', _full_progress_queue_guard=None,
               _full_progress_uvh_failed=0, _full_progress_queue_is_current=lambda: True,
               _uvh_live=lambda p: p is not None, _uvh_set_status=notes.append,
               _uvh_obj_addr=id, _uvh_obj_path=lambda c: 'world:pc', _uvh_build_plan=lambda i: [('UVH 1', 'first', .3), ('UVH 1', 'last', .3)])
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<uvhm>', 'exec'), env)
    def tick():
        clock[0]+=1.;env['uvh_boost_tick']()
    return env, pc, calls, notes, tick


@pytest.mark.parametrize('full_progress', [False, True])
def test_failure_is_never_reported_as_success_or_retried(full_progress):
    e, pc, calls, notes, tick = environment()
    def fail(*a):
        calls.append(a); raise RuntimeError('uncertain RPC')
    pc.ServerIncrementChallengeForPlayer = fail
    if full_progress: e['_full_progress_queue_guard'] = True
    tick(); tick()
    assert len(calls) == 1
    assert e['uvh_boost_status']()['uncertain'] and not e['uvh_boost_status']()['ok']
    assert not e['uvh_boost_resume']()['ok']
    assert e['_full_progress_uvh_failed'] == int(full_progress)


def test_missing_target_stops_before_consuming_or_sending_next_step():
    e, pc, calls, notes, tick = environment(); e['_uvh_targets'].append(None)
    tick()
    assert not calls and len(e['_uvh_paused_queue']) == 2 and e['_uvh_uncertain']


def test_late_target_cannot_receive_only_tail_of_plan():
    e, pc, calls, notes, tick = environment(); tick()
    ok, message = e['_uvh_queue_for_pc'](NS(), [0])
    assert not ok and len(e['_uvh_targets']) == 1


def test_finished_queue_reports_sent_requests_without_verified_unlocks():
    e, pc, calls, notes, tick = environment(); tick(); tick();tick();tick()
    status = e['uvh_boost_status']()
    assert len(calls) == 2 and status['ok'] and not status['completion_verified']
    assert status['native_completion_verified'] and not status['saved_progress_verified']
    assert 'not verified' in notes[-1]


def test_confirmed_step_allows_next_tick_without_a_second_delay():
    e,pc,calls,notes,tick=environment()
    tick()  # First request, still waiting for its native readback.
    assert calls==[('first',1)]
    tick()  # Native completion confirmed.
    assert len(calls)==1
    e['uvh_boost_tick']()  # Same clock, next tick: no extra .3s pause.
    assert calls==[('first',1),('last',1)]
    e['uvh_boost_tick']()
    assert len(calls)==2  # An unconfirmed request still cannot be repeated.


def test_resume_never_substitutes_a_different_player():
    e, pc, calls, notes, tick = environment(); e['uvh_boost_cancel']()
    e['_uvh_paused_targets'] = [None]
    assert not e['uvh_boost_resume']()['ok'] and not calls


def test_repeated_cancel_preserves_remaining_steps():
    e, pc, calls, notes, tick = environment()
    e['uvh_boost_cancel']();e['uvh_boost_cancel']()
    assert len(e['_uvh_paused_queue'])==2 and not calls


def test_full_progress_roster_guard_stops_before_native_call():
    e, pc, calls, notes, tick = environment()
    e['_full_progress_queue_guard']=True;e['_full_progress_queue_is_current']=lambda:False
    tick()
    assert not calls and e['_full_progress_uvh_failed']==1 and e['_uvh_uncertain']
