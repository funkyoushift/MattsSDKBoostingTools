import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import sys
import pytest


@pytest.fixture
def rig(monkeypatch):
    callbacks={};sent=[];clock=[100.]
    hooks=NS(Type=NS(POST='post'),add_hook=lambda path,kind,key,fn:callbacks.update({key:fn}),
             remove_hook=lambda path,kind,key:callbacks.pop(key))
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(hooks=hooks))
    monkeypatch.setitem(sys.modules,'unrealsdk.hooks',hooks)
    p=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools/dlc_refresh.py'
    spec=importlib.util.spec_from_file_location('refresh_test',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    monkeypatch.setattr(m.time,'monotonic',lambda:clock[0])
    def row(name,addr,host=False):
        state=NS(_get_address=lambda:addr+1)
        pc=NS(_get_address=lambda:addr,_path_name=lambda:name,PlayerState=state,HasAuthority=lambda:True,
              Client_RequestDLCEntitlements=lambda:sent.append(name))
        return dict(label=name,host=host,pc=pc,state=state)
    rows=[row('Host',100,True),row('Guest',200)]
    return m,rows,callbacks,sent,clock


def test_waits_for_real_server_ack_without_repeating_refresh(rig):
    m,rows,callbacks,sent,clock=rig
    child=m.begin(rows);assert sent==['Guest'] and len(callbacks)==1
    for _ in range(5):assert not m.ready(child['id'],rows)
    assert sent==['Guest']
    callback=next(iter(callbacks.values()))
    callback(rows[0]['pc'],None,None,None)
    assert not m.ready(child['id'],rows)
    callback(rows[1]['pc'],None,None,None)
    assert m.ready(child['id'],rows) and not callbacks
    assert sent==['Guest']


def test_timeout_cannot_release_mission_work(rig):
    m,rows,callbacks,sent,clock=rig;child=m.begin(rows);clock[0]=116
    with pytest.raises(RuntimeError,match='no missions sent'):m.ready(child['id'],rows)
    assert sent==['Guest']
    m.cancel(child['id']);assert not callbacks


def test_new_character_never_substitutes_for_expected_guest(rig):
    m,rows,callbacks,sent,clock=rig;child=m.begin(rows)
    replacement=NS(_get_address=lambda:999)
    rows[1]['state']=replacement;rows[1]['pc'].PlayerState=replacement
    with pytest.raises(RuntimeError,match='lobby changed'):m.ready(child['id'],rows)
    assert sent==['Guest']


def test_solo_needs_no_client_roundtrip(rig):
    m,rows,callbacks,sent,clock=rig;child=m.begin(rows[:1])
    assert m.ready(child['id'],rows[:1]) and not sent and not callbacks


def test_failed_dispatch_removes_hook_and_does_not_repeat(rig):
    m,rows,callbacks,sent,clock=rig
    def fail():sent.append('Guest');raise RuntimeError('unknown RPC result')
    rows[1]['pc'].Client_RequestDLCEntitlements=fail
    with pytest.raises(RuntimeError,match='unknown RPC'):m.begin(rows)
    assert sent==['Guest'] and not callbacks and m._state is None
