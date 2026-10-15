from mission_profile_fixture import exec_with_profiles
import importlib.util
import importlib.resources
import json
import struct
import time
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

ROOT = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def mod(monkeypatch):
    monkeypatch.setattr(importlib.resources, 'files', lambda package: ROOT)
    spec=importlib.util.spec_from_file_location('credit_test',ROOT/'mission_challenges.py')
    module=importlib.util.module_from_spec(spec)
    exec_with_profiles(spec, module, monkeypatch)
    return module


def test_source_list_is_fully_covered(mod):
    catalog={x['name'] for x in json.loads((ROOT/'mission_catalog.json').read_text())}
    assert len(mod.MISSIONS)==len(set(mod.MISSIONS))==98
    assert set(mod.MISSIONS)<=catalog
    assert mod.DATA['goals']==[10,25,50,75,98]


def test_campaign_unlock_matches_exact_authored_definition(mod):
    import hashlib
    source=ROOT.parents[1]/'external_app/v22_parts_codes_fixed/matt_editor/LegitItems'/mod.CAMPAIGN['source']
    raw=source.read_bytes();row=json.loads(raw)
    for key in mod.CAMPAIGN['pointer'].strip('/').split('/'):
        row=row[int(key)] if isinstance(row,list) else row[key]
    assert hashlib.sha256(raw).hexdigest()==mod.CAMPAIGN['sha256']
    assert row['challenge']==mod.CAMPAIGN['challenge']
    assert row['busecustommissionlist']==row['bcompleteeachmissiononce']=='true'
    assert row['missiondefs']==["mission'"+n+"'" for n in mod.CAMPAIGN['missions']]
    assert mod.CAMPAIGN['goals']==[1] and len(mod.CREDIT_MISSIONS)==99


def test_campaign_callback_credits_only_missing_guest_and_reconciles_without_reissue(mod,monkeypatch):
    host,guest=object(),object();calls=[];events=[];credited=set()
    def read(engine,pc,data):
        assert data is mod.CAMPAIGN
        return dict(pid=1 if pc is host else 2,path='host' if pc is host else 'guest',
                    player='Host' if pc is host else 'Guest',count=int(pc is host or bool(credited)),
                    credited={0} if pc is host or credited else set(),manager=100,entry=200,progress=300)
    monkeypatch.setattr(mod,'read_player',read)
    monkeypatch.setattr(mod,'native_address',lambda e,r:r)
    monkeypatch.setattr(mod,'native_fingerprint',lambda e,r,f:f)
    monkeypatch.setattr(mod,'_name',lambda e,n:b'12345678')
    def factory(*signature):
        def bind(address):
            def invoke(manager,pid,entry,progress,event):
                assert events[-1]['event']=='issued' and events[-1]['challenge']==mod.CAMPAIGN['challenge']
                calls.append(pid);credited.add(0)
            return invoke
        return bind
    monkeypatch.setattr(mod.C,'WINFUNCTYPE',factory)
    engine=NS(read=lambda a,n:bytes.fromhex(mod.FINGERPRINT))
    rows=[dict(pc=host),dict(pc=guest)]
    with pytest.raises(mod.CreditPending) as pending:
        mod.credit_completed(engine,rows,mod.CAMPAIGN['missions'][0],events.append)
    assert calls==[2] and [e['event'] for e in events]==['issued','returned']
    receipt=pending.value.receipt
    loaded=NS(_path_name=lambda:'guest')
    monkeypatch.setattr(mod,'read_player',lambda e,p,d:read(e,guest,d))
    assert mod.reconcile(engine,[dict(pc=loaded,state=NS(PlayerId=2))],receipt,events.append)['count']==1
    assert calls==[2] and events[-1]['event']=='challenge_verified'


def test_campaign_recovery_never_falls_back_to_grassroots(mod,monkeypatch):
    pc=NS(_path_name=lambda:'guest');seen=[]
    receipt=dict(challenge=mod.CAMPAIGN['challenge'],player_path='guest',player_id=2,
                 before_count=0,before_credit=[],index=0,issued_at=time.time())
    def read(e,p,data):
        seen.append(data['challenge']);return dict(pid=2,path='guest',count=0,credited=set())
    monkeypatch.setattr(mod,'read_player',read)
    with pytest.raises(mod.CreditPending):
        mod.reconcile(None,[dict(pc=pc,state=NS(PlayerId=2))],receipt,lambda e:None)
    assert seen==[mod.CAMPAIGN['challenge']]


def test_duplicate_credit_is_skipped(mod):
    assert not mod.needs_credit({'count':2,'credited':{1,5}},5)
    assert mod.needs_credit({'count':2,'credited':{1,5}},6)
    with pytest.raises(RuntimeError):
        mod.needs_credit({'count':35,'credited':set()},6)


def test_verification_requires_exact_bit_and_count_change(mod):
    before=dict(pid=1,path='guest',count=2,credited={1,5})
    after=dict(pid=1,path='guest',count=3,credited={1,5,6})
    assert mod.verified(before,after,6)
    for update in [dict(pid=2),dict(path='new_guest'),dict(count=4),dict(credited={1,5,7})]:
        assert not mod.verified(before,dict(after,**update),6)


def test_concurrent_mission_credit_does_not_strand_verified_target(mod):
    before=dict(pid=257,path='guest',count=2,credited={1,5})
    after=dict(pid=257,path='guest',count=4,credited={1,5,6,7})
    assert mod.verified(before,after,6)
    assert not mod.verified(before,dict(after,credited={1,5,7,8}),6)
    assert not mod.verified(before,dict(after,count=3,credited={1,6,7}),6)


def test_freed_sparse_slot_is_not_dereferenced(mod):
    reads=[]
    def read(address,size):
        reads.append((address,size))
        if address==0x128:return struct.pack('<ii',3,128)
        if address==0x110:return bytes([5,0,0,0])
        raise AssertionError('Unexpected native read')
    engine=NS(array=lambda a,m:(0x1000,3),u64=lambda a:0,read=read)
    assert mod.sparse_entries(engine,0x100,32,16)==[0x1000,0x1040]
    assert all(a<0x1000 for a,n in reads)


def test_nonlisted_mission_has_no_native_access(mod):
    assert mod.credit_completed(None,[{'pc':None}],'Mission_Main_Beach',lambda x:None)==[]


def test_existing_credit_does_not_issue_callback(mod,monkeypatch):
    monkeypatch.setattr(mod,'read_player',lambda e,p:dict(count=1,credited={0},player='guest'))
    journal=[]
    result=mod.credit_completed(None,[{'pc':None}],mod.MISSIONS[0],journal.append)
    assert result[0]['already_credited'] and not journal


def test_preflight_mismatch_never_issues_callback(mod,monkeypatch):
    monkeypatch.setattr(mod,'read_player',lambda e,p:dict(count=35,credited=set(),player='guest'))
    journal=[]
    with pytest.raises(RuntimeError):
        mod.credit_completed(None,[{'pc':None}],mod.MISSIONS[0],journal.append)
    assert not journal


def test_pending_credit_waits_without_a_second_write(mod,monkeypatch):
    pc=NS(_path_name=lambda:'guest')
    party=[dict(pc=pc,state=NS(PlayerId=1))]
    receipt=dict(player_path='guest',player_id=1,before_count=2,before_credit=[1,5],index=6,issued_at=time.time())
    monkeypatch.setattr(mod,'read_player',lambda e,p:dict(pid=1,path='guest',count=2,credited={1,5}))
    journal=[]
    with pytest.raises(mod.CreditPending):mod.reconcile(None,party,receipt,journal.append)
    assert not journal
    monkeypatch.setattr(mod,'read_player',lambda e,p:dict(pid=1,path='guest',count=3,credited={1,5,6}))
    assert mod.reconcile(None,party,receipt,journal.append)['count']==3
    assert journal[0]['event']=='challenge_verified'


def test_unsettled_credit_times_out_without_retry(mod,monkeypatch):
    pc=NS(_path_name=lambda:'guest')
    receipt=dict(player_path='guest',player_id=1,before_count=2,before_credit=[1,5],index=6,issued_at=time.time()-20)
    monkeypatch.setattr(mod,'read_player',lambda e,p:dict(pid=1,path='guest',count=2,credited={1,5}))
    with pytest.raises(mod.CreditUncertain):mod.reconcile(None,[dict(pc=pc,state=NS(PlayerId=1))],receipt,lambda e:None)
