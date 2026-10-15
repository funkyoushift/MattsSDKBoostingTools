"""Use real per-player receipts to exercise ignored, delayed and uncertain grants."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import pytest

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def rig(monkeypatch):
    spec=importlib.util.spec_from_file_location('uvhm_verified_test',ROOT/'uvhm_progression.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    calls=[];complete=set();addr=[100]
    pc=NS(Pawn=object(),PlayerState=NS(_get_address=lambda:200),HasAuthority=lambda:True,
          _get_address=lambda:addr[0],_path_name=lambda:'world:guest',
          ServerIncrementChallengeForPlayer=lambda n,c:calls.append((n,c)))
    monkeypatch.setattr(m,'_complete',lambda pc,n:n in complete)
    return m,pc,calls,complete,addr


def test_delayed_flags_wait_without_duplicate_grants(rig):
    m,pc,calls,complete,_=rig;receipt={}
    assert not m.advance(pc,'first',receipt,100,.3)
    for now in (100.1,101,120):assert not m.advance(pc,'first',receipt,now,.3)
    assert calls==[('first',1)]
    complete.add('first')
    assert m.advance(pc,'first',receipt,121,.3) and receipt['state']=='verified'
    assert m.advance(pc,'first',receipt,122,.3) and len(calls)==1


def test_completed_challenge_is_never_regranted(rig):
    m,pc,calls,complete,_=rig;complete.add('first');receipt={}
    assert m.advance(pc,'first',receipt,100,.3)
    assert not calls and not receipt['sent']


def test_ignored_rpc_times_out_and_never_becomes_success(rig):
    m,pc,calls,_,_=rig;receipt={};m.advance(pc,'first',receipt,100,.3)
    with pytest.raises(RuntimeError,match='native completion not confirmed'):
        m.advance(pc,'first',receipt,131,.3)
    with pytest.raises(RuntimeError,match='no automatic retry'):
        m.advance(pc,'first',receipt,132,.3)
    assert calls==[('first',1)]


def test_readback_failure_occurs_before_any_first_grant(rig,monkeypatch):
    m,pc,calls,_,_=rig
    def fail(*a):raise RuntimeError('unavailable native readback')
    monkeypatch.setattr(m,'_complete',fail)
    with pytest.raises(RuntimeError,match='unavailable'):m.advance(pc,'first',{},100,.3)
    assert not calls


def test_uncertain_rpc_and_replaced_player_never_retry(rig):
    m,pc,calls,_,addr=rig;receipt={}
    def fail(n,c):calls.append((n,c));raise RuntimeError('uncertain RPC')
    pc.ServerIncrementChallengeForPlayer=fail
    with pytest.raises(RuntimeError):m.advance(pc,'first',receipt,100,.3)
    with pytest.raises(RuntimeError,match='no automatic retry'):m.advance(pc,'first',receipt,101,.3)
    addr[0]=101
    with pytest.raises(RuntimeError,match='target or challenge changed'):m.advance(pc,'first',receipt,102,.3)
    assert calls==[('first',1)]
