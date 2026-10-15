"""Build identity and group-range checks precede every direct stage call."""
import importlib.util
import struct
import sys
from pathlib import Path
from types import ModuleType,SimpleNamespace as NS

import pytest

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'
SELECT=bytes.fromhex('56574883ec2889d64889cfe8863564f84885c074214889c189f2e86f50f3ff48')
REWIND=bytes.fromhex('4157415641554154565755534881eca80000000f29b4249000000089d74889ce')


@pytest.fixture
def stage(monkeypatch):
    import importlib.resources
    monkeypatch.setattr(importlib.resources,"files",lambda _:ROOT)
    pkg=ModuleType('stage_test');pkg.__path__=[str(ROOT)];monkeypatch.setitem(sys.modules,'stage_test',pkg)
    spec=importlib.util.spec_from_file_location('stage_test.mission_reset',ROOT/'mission_reset.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    calls=[];events=[];effects=[];base=0x10000000
    pointers={0x1000:base+0xb973820,0x10a8:0x4000,0x2000:base+0xb973940,0x2028:0x1000,0x2040:0x3000}
    data={base+0x8905d9e:SELECT,base+0x89069ca:REWIND,0x303c:struct.pack('<ii',28,28)}
    for rva in (0xcb80870,0xcb80898,0xcb808a8,0xcb808a0,0xcb808b0):data[base+rva]=struct.pack('<Q',rva)
    facts={0x20:dict(known_status='active'),0x60:dict(tag=2,raw=(b'\x02'+b'\0'*11+struct.pack('<i',28)).hex())}
    engine=NS(profile='steam-25372571', base=base,ensure_world=lambda:None,check_build=lambda:None,u64=lambda a:pointers[a],read=lambda a,n:data[a][:n],fact=lambda storage,offset:facts[offset])
    monkeypatch.setitem(sys.modules,'stage_test.mission_effects',NS(reset_interactions=lambda *a,**k:effects.append(k)))
    monkeypatch.setattr(m.C,'WINFUNCTYPE',lambda *types:lambda address:lambda *args:calls.append((address-base,args)))
    row=dict(record='0x1000',replication_type=0,source_identity=dict(name='mission'))
    obj=dict(pointer='0x2000',name='Mudmouth')
    return NS(m=m,engine=engine,row=row,obj=obj,data=data,calls=calls,events=events,effects=effects,base=base,facts=facts)


def test_direct_stage_uses_native_cursor_and_rewind_without_outcomes(stage):
    s=stage;s.m.stage_checkpoint(s.engine,s.row,s.obj,28,s.events.append)
    assert s.calls==[(0xf19ee4,(0x1000,4,False)),(0x8905d9e,(0x1000,28)),(0x89069ca,(0x1000,28))]
    assert not any(rva==0x3df18e0 for rva,_ in s.calls)
    assert s.effects[0]=={'validate_only':True}


@pytest.mark.parametrize('change',['fingerprint','range','generated','replication'])
def test_invalid_build_or_selection_stops_before_effects_and_calls(stage,change):
    s=stage
    if change=='fingerprint':s.data[s.base+0x8905d9e]=b'\0'*32
    elif change=='range':s.data[0x303c]=struct.pack('<ii',1,3)
    elif change=='generated':s.row['generated']=True
    else:s.row['replication_type']=1
    with pytest.raises(RuntimeError):s.m.stage_checkpoint(s.engine,s.row,s.obj,28,s.events.append)
    assert not s.calls and not s.effects and not s.events


@pytest.mark.parametrize('failure',['activation','cursor'])
def test_unconfirmed_native_readback_prevents_following_call(stage,failure):
    s=stage
    s.facts[0x20 if failure=='activation' else 0x60]={}
    with pytest.raises(RuntimeError,match='not confirmed'):
        s.m.stage_checkpoint(s.engine,s.row,s.obj,28,s.events.append)
    assert [rva for rva,_ in s.calls]==([0xf19ee4] if failure=='activation' else [0xf19ee4,0x8905d9e])


@pytest.mark.parametrize('state',['active','completed','unavailable'])
def test_stale_prior_actions_are_cancelled_without_outcomes_or_finish_traversal(stage,monkeypatch,state):
    s=stage;pointer=0x5000;native=s.engine.u64
    addresses={pointer:s.base+0xb973940,pointer+0x28:0x1000,pointer+0x40:0x6000,pointer+0x48:0x7000,
               s.base+0xb973940+0xd0:s.base+0xdcb1dc,s.base+0xb973940+0xc8:s.base+0x105bc10}
    s.engine.u64=lambda a:addresses[a] if a in addresses else native(a)
    s.data[s.base+0xce3c18]=bytes.fromhex('564883ec204889cee8650000004889f1e81f0000004889f1e84b020000b9d001')
    s.data[s.base+0xdcb1dc]=bytes.fromhex('56534883ec2889d34889cee8300000004885c074224889c189dae8c9da270048')
    s.data[0x6040]=struct.pack('<i',3)
    completed=s.data[s.base+0xcb808b0].hex()
    previous=[dict(fname=s.data[s.base+0xcb80870].hex() if state=='active' else completed if state=='completed' else None)]
    fact=s.engine.fact;s.engine.fact=lambda storage,offset:previous[0] if storage==0x7000 else fact(storage,offset)
    def factory(*types):
        def bind(address):
            def call(*args):
                s.calls.append((address-s.base,args))
                if address-s.base==0xdcb1dc:previous[0]=dict(fname=completed)
            return call
        return bind
    monkeypatch.setattr(s.m.C,'WINFUNCTYPE',factory)
    s.m.stage_checkpoint(s.engine,s.row,s.obj,28,s.events.append,earlier=[dict(name='Old bomb',pointer=hex(pointer))])
    rvas=[rva for rva,_ in s.calls]
    assert rvas==[0xf19ee4,0x8905d9e]+([0xce3c18,0xdcb1dc] if state=='active' else [])+[0x89069ca]
    assert 0x3df18e0 not in rvas
