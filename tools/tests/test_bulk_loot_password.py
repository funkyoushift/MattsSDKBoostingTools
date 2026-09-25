from __future__ import annotations
import ast
from pathlib import Path
from types import SimpleNamespace
import pytest
ROOT = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools'
def load(file, names):
    tree = ast.parse((ROOT / file).read_text(encoding='utf-8'))
    ns = {'MAX_ITEM_LEVEL': 70}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), file, 'exec'), ns)
    return ns

def test_bulk_password_checked_before_conversion_and_not_cached():
    ns=load('backend_actions.py', {'give_serials'}); calls=[]
    ns['_parse_serial_text']=lambda text:text.splitlines()
    ns['serial_rewards']=SimpleNamespace(needs_async_serial_resolution=lambda _:False, _resolve_give_serial_strings=lambda rows:rows)
    ns['_finish_give_serials']=lambda rows, **kw: calls.append((rows,kw)) or {'ok':True}
    send=ns['give_serials']; text='\n'.join(str(i) for i in range(71))
    for pw in (None,'wrong',True):
        assert send(text,bulk_loot_password=pw)['password_required']
    assert not calls
    assert send(text,bulk_loot_password='funkyou')['ok']
    assert calls[0][1]['bulk_authorized']
    assert 'bulk_loot_password' not in calls[0][1]
    assert send(text)['password_required']
    assert send('\n'.join(str(i) for i in range(70)))['ok']
    assert not calls[-1][1]['bulk_authorized']

def test_low_level_queue_rejects_over_seventy_before_any_side_effect():
    ns=load('serial_rewards.py', {'_queue_serial_delivery_sequence'})
    class ReachedAllowedQueue(Exception):pass
    def allowed(_):raise ReachedAllowedQueue()
    ns['_serial_delivery_mode_key']=allowed
    queue=ns['_queue_serial_delivery_sequence']
    with pytest.raises(PermissionError):queue(['code']*71,[0],scope_label='host')
    with pytest.raises(ReachedAllowedQueue):queue(['code']*70,[1],scope_label='guest')
    with pytest.raises(ReachedAllowedQueue):queue(['code']*952,[1],scope_label='guest',bulk_authorized=True)

def test_resolved_count_is_checked_too():
    ns=load('backend_actions.py', {'_deliver_serials_with_target'})
    assert ns['_deliver_serials_with_target'](['code']*71,'local')['password_required']
