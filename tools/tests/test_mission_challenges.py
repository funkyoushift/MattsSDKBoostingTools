from mission_profile_fixture import exec_with_profiles
import importlib.util
import importlib.resources
import json
import struct
import sys
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


def test_mission_credit_probe_reports_missing_bits_without_issuing_callbacks(mod,monkeypatch):
    entry=dict(challenge='Achievement',source='old.json',missions=['Mission_A','Mission_B'])
    monkeypatch.setattr(mod,'MISSION_CREDIT_CATALOG',dict(game_build=25234898,entries=[entry]))
    monkeypatch.setattr(mod,'MISSION_CREDIT_DEFINITIONS',{'Achievement':entry})
    calls=[]
    def read(engine,pc,data):
        calls.append((pc,data))
        return dict(count=1,credited={0})
    monkeypatch.setattr(mod,'read_player',read)
    result=mod.inspect_mission_credit_catalog('engine',[dict(pc='guest',label='Guest')],['Achievement'])
    assert result[0]['players']==[dict(player='Guest',verified=True,count=1,
                                      credited=['Mission_A'],missing=['Mission_B'])]
    assert calls==[('guest',dict(challenge='Achievement',missions=['Mission_A','Mission_B']))]
    with pytest.raises(ValueError,match='Unknown authored'):
        mod.inspect_mission_credit_catalog('engine',[dict(pc='guest',label='Guest')],['Other'])


def test_live_definition_probe_preserves_unknown_fnames(mod,monkeypatch):
    challenge='Challenges_Achievements_55_Harmonica_Activities'
    known='ZoneActivity_Intro_Safehouse_Horde'
    monkeypatch.setattr(mod,'MISSION_NAME_CANDIDATES',[known])
    monkeypatch.setattr(mod,'_name',lambda engine,name:b'challenge' if name==challenge else b'known123')
    monkeypatch.setattr(mod,'sparse_entries',lambda engine,address,stride,maximum:[2000])
    def read(address,size):
        return {2000:b'challenge',3800:b'\x01\x01\x01',4000:b'known123',
                4024:b'unknown1'}[(address)]
    engine=NS(ensure_world=lambda:None,u64=lambda address:{2008:2100,2100:3000}[address],
              array=lambda address,limit:(4000,2),read=read)
    pc=NS(OakChallengeManager=NS(_get_address=lambda:1000),HasAuthority=lambda:True)
    result=mod.inspect_live_definition(engine,pc,challenge)
    assert result==dict(count=2,flags='010101',missions=[known,dict(unresolved_fname=b'unknown1'.hex())],
                        all_names_resolved=False)


def test_raw_live_progress_probe_reads_both_counters_without_inferred_credit(mod,monkeypatch):
    challenge='Challenges_Achievements_55_Harmonica_Activities'
    name=b'12345678'
    monkeypatch.setattr(mod,'_name',lambda engine,value:name)
    monkeypatch.setattr(mod,'sparse_entries',lambda engine,address,stride,maximum:{
        1000+0x290:[2000],1000+0x3d8:[3000],3008:[4000]}[address])
    library=NS(GetChallengeProgressForPlayer=lambda **kwargs:3,
               IsChallengeCompleteForPlayer=lambda **kwargs:False)
    unreal=NS(FGameDataHandle=lambda *args:args)
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(find_object=lambda *args:library))
    monkeypatch.setitem(sys.modules,'unrealsdk.unreal',unreal)
    def read(address,size):
        return {5000+0x394:struct.pack('<i',2),2000:name,3000:struct.pack('<i',2),
                6000:name,7000:struct.pack('<q',3),8000:struct.pack('<I',5)}[address]
    engine=NS(ensure_world=lambda:None,
              u64=lambda address:{2008:2500,4000:2500,4008:7000}[address],
              array=lambda address,limit:{5000+0x1300:(6000,1),6008:(8000,1)}[address],
              read=read)
    pc=NS(PlayerState=NS(_get_address=lambda:5000,PlayerId=2,PlayerNamePrivate='Guest'),
          Pawn=object(),OakChallengeManager=NS(_get_address=lambda:1000),HasAuthority=lambda:True)
    result=mod.inspect_live_player_progress(engine,pc,challenge)
    assert result==dict(player='Guest',player_id=2,native_counter=3,record_counter=3,
                        challenge_complete=False,raw_record_present=True,raw_bit_words=['0x5'])


def test_current_harmonica_flags_require_exact_definition_and_coherent_player_count(mod,monkeypatch):
    challenge='Challenges_Achievements_55_Harmonica_Activities'
    data=mod.credit_definition(challenge)
    monkeypatch.setattr(mod,'_name',lambda engine,value:b'12345678')
    monkeypatch.setattr(mod,'sparse_entries',lambda engine,address,stride,maximum:{
        1000+0x290:[2000],1000+0x3d8:[3000],3008:[4000]}[address])
    library=NS(GetChallengeProgressForPlayer=lambda **kwargs:0)
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(find_object=lambda *args:library))
    monkeypatch.setitem(sys.modules,'unrealsdk.unreal',NS(FGameDataHandle=lambda *args:args))
    flags=[b'\x01\x00\x01']
    def read(address,size):
        if address==5000+0x394:return struct.pack('<i',2)
        if address in (2000,*[9000+i*24 for i in range(len(data['missions']))]):return b'12345678'
        if address==2500+0x320:return flags[0]
        if address==3000:return struct.pack('<i',2)
        if address==7000:return struct.pack('<q',0)
        raise AssertionError('Unexpected native read')
    engine=NS(profile='steam-26007962',ensure_world=lambda:None,
              u64=lambda address:{2008:2100,2100:2500,4000:2100,4008:7000}[address],
              array=lambda address,limit:{2500+0x328:(9000,len(data['missions'])),
                                        5000+0x1300:(6000,0)}[address],read=read)
    pc=NS(PlayerState=NS(_get_address=lambda:5000,PlayerId=2,PlayerNamePrivate='Guest'),
          Pawn=object(),OakChallengeManager=NS(_get_address=lambda:1000),
          HasAuthority=lambda:True,_path_name=lambda:'guest')
    assert mod.read_player(engine,pc,data)['credited']==set()
    engine.profile='epic-26007962'
    with pytest.raises(RuntimeError,match='counting rules changed'):
        mod.read_player(engine,pc,data)
    engine.profile='steam-26007962'
    with pytest.raises(RuntimeError,match='counting rules changed'):
        mod.read_player(engine,pc,dict(challenge='Other',missions=data['missions']))
    flags[0]=b'\x01\x00\x00'
    with pytest.raises(RuntimeError,match='counting rules changed'):
        mod.read_player(engine,pc,data)


def test_authored_credit_callback_targets_only_missing_guest_and_reconciles(mod,monkeypatch):
    challenge='Challenges_Achievements_59_Harmonica_Mission01'
    data=mod.credit_definition(challenge)
    assert len(data['missions'])==1
    host,guest=object(),object();issued=[];events=[];guest_credited=set()
    def read(engine,pc,definition):
        assert definition==data
        credited={0} if pc is host else set(guest_credited)
        return dict(pid=1 if pc is host else 2,path='host' if pc is host else 'guest',
                    player='Host' if pc is host else 'Guest',count=len(credited),
                    credited=credited,manager=100,entry=200,progress=300)
    monkeypatch.setattr(mod,'read_player',read)
    monkeypatch.setattr(mod,'native_address',lambda e,r:r)
    monkeypatch.setattr(mod,'native_fingerprint',lambda e,r,f:f)
    monkeypatch.setattr(mod,'_name',lambda e,n:b'12345678')
    def factory(*signature):
        def bind(address):
            def invoke(manager,pid,entry,progress,event):
                assert pid==2 and events[-1]['event']=='issued'
                issued.append(pid);guest_credited.add(0)
            return invoke
        return bind
    monkeypatch.setattr(mod.C,'WINFUNCTYPE',factory)
    engine=NS(read=lambda a,n:bytes.fromhex(mod.FINGERPRINT))
    party=[dict(pc=host),dict(pc=guest)]
    with pytest.raises(mod.CreditPending) as pending:
        mod.credit_completed(engine,party,data['missions'][0],events.append,challenge_id=challenge)
    receipt=pending.value.receipt
    assert receipt['challenge']==challenge and issued==[2]
    loaded=NS(_path_name=lambda:'guest')
    assert mod.reconcile(engine,[dict(pc=loaded,state=NS(PlayerId=2))],receipt,events.append)['count']==1
    assert issued==[2] and events[-1]['event']=='challenge_verified'


def test_authored_credit_definition_mismatch_does_not_issue_callback(mod,monkeypatch):
    challenge='Challenges_Achievements_59_Harmonica_Mission01'
    data=mod.credit_definition(challenge)
    monkeypatch.setattr(mod,'read_player',lambda *args:(_ for _ in ()).throw(
        RuntimeError('Mission credit counting rules changed')))
    with pytest.raises(RuntimeError,match='counting rules changed'):
        mod.credit_completed(None,[dict(pc=object())],data['missions'][0],
                             lambda event:pytest.fail('No callback should be journaled'),
                             challenge_id=challenge)


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


def test_deferred_host_mismatch_still_checks_guest_credit(mod,monkeypatch):
    host=NS(_path_name=lambda:'host');guest=NS(_path_name=lambda:'guest')
    seen=[];deferred=[]
    def read(engine,pc):
        seen.append(pc)
        if pc is host:
            raise mod.CreditReadbackMismatch('Host counters disagree')
        return dict(count=1,credited={0},player='Guest')
    monkeypatch.setattr(mod,'read_player',read)
    party=[dict(pc=host,state=NS(PlayerId=1)),dict(pc=guest,state=NS(PlayerId=2))]
    result=mod.credit_completed(None,party,mod.MISSIONS[0],lambda event:None,
                                on_mismatch=deferred.append)
    assert seen==[host,guest]
    assert deferred==[dict(mission=mod.MISSIONS[0],player_id=1,player_path='host',
                           reason='Host counters disagree')]
    assert result[0]['unverified'] and result[1]['already_credited']


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
