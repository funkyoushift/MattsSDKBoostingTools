"""Exercise the real queue function with independently failing party targets."""
import ast
from collections import deque
from pathlib import Path
from types import SimpleNamespace


def queue_env(fail):
    source=(Path(__file__).resolve().parents[2]/'mod_extracted/MattsSDKBoostingTools/backend_actions.py').read_text(encoding='utf-8')
    tree=ast.parse(source)
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='complete_challenges_tick')
    calls=[]; notes=[]
    env=dict(_challenge_queue=deque([('A',1)]),_challenge_targets=['one','two'],_challenge_next_at=0,
        _challenge_running=True,_challenge_ok=0,_challenge_failed=0,_challenge_total_steps=1,
        _challenge_granted=set(),_challenge_granted_by_target={},_challenge_attempts={},
        _CHALLENGE_BATCH_SIZE=4,_CHALLENGE_STEP_DELAY_SECONDS=.1,_CHALLENGE_STATUS_EVERY=50,
        time=SimpleNamespace(monotonic=lambda:100),get_pc=lambda:True,_uvh_live=lambda _:True,
        _challenge_grant_amount=lambda n:n,_challenge_delay_for_amount=lambda n:.1,
        _challenge_set_status=notes.append,_challenge_finish_reconcile=lambda targets:'')
    def send(target,challenge,amount):
        calls.append(target)
        if fail(target,calls.count(target)):raise RuntimeError('not ready')
    env['_challenge_increment_one']=send
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'<queue>','exec'),env)
    def tick():env['_challenge_next_at']=0;env['complete_challenges_tick']()
    return env,calls,tick


def test_retries_only_failed_player_and_never_counts_partial_as_success():
    env,calls,tick=queue_env(lambda target,n:target=='two' and n==1)
    tick();assert env['_challenge_ok']==0 and env['_challenge_queue']
    assert env['_challenge_granted_by_target']=={'one':{'A'},'two':set()}
    tick();assert calls==['one','two','two']
    assert env['_challenge_ok']==1 and env['_challenge_failed']==0


def test_permanent_partial_failure_is_reported_after_three_attempts():
    env,calls,tick=queue_env(lambda target,n:target=='two')
    for _ in range(3):tick()
    assert calls==['one','two','two','two']
    assert env['_challenge_ok']==0 and env['_challenge_failed']==1
    assert not env['_challenge_running']
    assert env['_challenge_granted_by_target']['two']==set()
