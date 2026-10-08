"""Restoration, conflict, feature failure, and instruction boundary regressions."""
import importlib.util
from pathlib import Path
import sys
import types
import pytest
import capstone
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'work/lab-deps'))

HERE=Path(__file__).resolve().parents[2]/'mod_extracted/MattsSDKBoostingTools'
@pytest.fixture
def modules(monkeypatch):
    package=types.ModuleType('lab_test');package.__path__=[str(HERE)]
    monkeypatch.setitem(sys.modules,'lab_test',package)
    mods=types.ModuleType('mods_base');sdk=types.ModuleType('unrealsdk')
    monkeypatch.setitem(sys.modules,'mods_base',mods);monkeypatch.setitem(sys.modules,'unrealsdk',sdk)
    production=types.ModuleType('MattsSDKBoostingTools.guaranteed_drops');production.NativeMemory=object
    monkeypatch.setitem(sys.modules,'MattsSDKBoostingTools.guaranteed_drops',production)
    monkeypatch.setitem(sys.modules,'lab_test.guaranteed_drops',production)
    mods.hook=lambda *a,**k:lambda fn:fn
    hooks=types.ModuleType('unrealsdk.hooks');hooks.Type=types.SimpleNamespace(PRE='PRE')
    monkeypatch.setitem(sys.modules,'unrealsdk.hooks',hooks)
    import importlib
    engine=importlib.import_module('lab_test.farming_controls');native=importlib.import_module('lab_test.farming_native')
    yield engine,native,mods,sdk
    for k in list(sys.modules):
        if k.startswith('lab_test'):sys.modules.pop(k,None)

class Obj:
    Class=types.SimpleNamespace(_path_name=lambda:'Fake')
    def __init__(self):self.value=2.75
    def _path_name(self):return 'owner.field'
    def _get_address(self):return 1234

def test_exact_snapshot_restore_preserves_fractional_original(modules):
    e,_,_,sdk=modules;obj=Obj();sdk.find_object=lambda *_:obj
    e.edit('test',obj,'value',99.0);e.edit('test',obj,'value',99.0)
    assert e.restore('test')['ok'];assert obj.value==2.75;assert not e._snapshots

def test_changed_and_replaced_objects_are_not_overwritten(modules):
    e,_,_,sdk=modules;obj=Obj();sdk.find_object=lambda *_:obj
    e.edit('test',obj,'value',99.0);obj.value=6.5
    result=e.restore('test');assert result['ok'];assert result['skipped_changed_or_expired'];assert obj.value==6.5
    e.edit('test',obj,'value',99.0);replacement=Obj();replacement._get_address=lambda:9876;sdk.find_object=lambda *_:replacement
    assert e.restore('test')['ok'];assert replacement.value==2.75

def test_failed_readback_keeps_snapshot_for_restore(modules):
    e,_,_,sdk=modules;obj=Obj();sdk.find_object=lambda *_:obj
    original=e.write_path;e.write_path=lambda *_:None
    with pytest.raises(RuntimeError):e.edit('test',obj,'value',99.0)
    e.write_path=original
    assert e.restore('test')['ok'];assert obj.value==2.75

def test_world_change_turns_features_off(modules):
    e,_,_,_=modules;e._sessions['test']={'enabled':{'infinite_ammo'}};e._world=('old',);e.world_identity=lambda:('new',)
    calls=[];e.off=lambda:calls.append('off')
    e.tick();assert calls==['off']

def test_god_mode_changes_native_damage_permission_and_restores(modules):
    e,_,_,sdk=modules;pawn=Obj();pawn.bCanBeDamaged=True
    sdk.find_object=lambda *_:pawn
    e.apply('god_mode',None,pawn)
    assert pawn.bCanBeDamaged is False
    assert e.restore('god_mode')['ok'] and pawn.bCanBeDamaged is True

def test_glide_uses_only_owned_power_cost_and_restores(modules):
    e,n,_,sdk=modules;movement=Obj();movement.VaultPowerCost_Glide=types.SimpleNamespace(Value=7.5,BaseValue=15.0)
    movement.bIsGliding=True;pawn=types.SimpleNamespace(OakCharacterMovement=movement)
    sdk.find_object=lambda *_:movement
    n.hook=lambda _:types.SimpleNamespace(disable=lambda:{'ok':True})
    e.apply('glide_duration',None,pawn)
    assert movement.VaultPowerCost_Glide.Value==0 and movement.VaultPowerCost_Glide.BaseValue==15
    assert e.restore('glide_duration')['ok'] and movement.VaultPowerCost_Glide.Value==7.5


class FakeMemory:
    base=0x140000000
    def __init__(self,profile):
        self.storage={self.base+profile['rva']+i:b for i,b in enumerate(profile['context'])}
        self.api=types.SimpleNamespace(VirtualProtect=lambda *_:True)
    def validate(self):pass
    def read(self,address,size):return bytes(self.storage.get(address+i,0) for i in range(size))
    def write(self,address,data):self.storage.update({address+i:b for i,b in enumerate(data)})
    def restore_protections(self):pass

@pytest.mark.parametrize('name',['glide_duration','legendary_roll'])
def test_native_roundtrip_and_foreign_patch_refusal(modules,name):
    _,n,_,_=modules;p=n.PROFILES[name];m=FakeMemory(p);h=n.NativeHook(name,lambda:m);h.allocate=lambda:0x180000000
    assert h.enable(1234)['active'];assert h.disable()['ok'];assert not h.owned
    assert m.read(m.base+p['rva'],len(p['context']))==p['context']
    assert h.enable(1234)['active'];m.write(m.base+p['rva'],b'\xcc')
    assert not h.disable()['ok'];assert h.owned;assert m.read(m.base+p['rva'],1)==b'\xcc'

def test_unqualified_context_refuses_before_allocation(modules):
    _,n,_,_=modules;p=n.PROFILES['glide_duration'];m=FakeMemory(p);m.write(m.base+p['rva']+20,b'\xcc')
    h=n.NativeHook('glide_duration',lambda:m);h.allocate=lambda:pytest.fail('must not allocate')
    assert not h.enable()['ok'];assert not h.owned

@pytest.mark.parametrize('name',['glide_duration','legendary_roll'])
def test_generated_code_boundaries_and_preserved_flags(modules,name):
    _,n,_,_=modules;p=n.PROFILES[name];code=0x180000000;site=0x140000000+p['rva']
    data=n.make_code(name,code,code+0x1000,site,p['original'])
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);ins=list(md.disasm(data[:-8],code))
    assert sum(i.size for i in ins)==len(data)-8
    assert ins[0].mnemonic=='pushfq';assert sum(i.mnemonic=='popfq' for i in ins)==1
    import struct
    assert ins[-1].mnemonic=='jmp';assert struct.unpack('<Q',data[-8:])[0]==site+len(p['original'])
    branch=next(i for i in ins if i.mnemonic in ('jne','jl'))
    assert int(branch.op_str,16)==next(i.address for i in ins if i.mnemonic=='popfq')

@pytest.mark.parametrize('matches',[True,False])
def test_glide_machine_code_owner_scope_and_flags(modules,matches):
    import struct
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_64
    from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RDI,UC_X86_REG_RSP,UC_X86_REG_EFLAGS,UC_X86_REG_XMM0,UC_X86_REG_XMM1,UC_X86_REG_XMM7
    _,n,_,_=modules;p=n.PROFILES['glide_duration'];code=0x180000000;site=0x140000000+p['rva'];timer=0x300000;owner=0x400000
    u=Uc(UC_ARCH_X86,UC_MODE_64)
    for address,size in ((code,0x2000),(site&~0xfff,0x1000),(timer,0x1000),(0x200000,0x1000)):u.mem_map(address,size)
    u.mem_write(code,n.make_code('glide_duration',code,code+0x1000,site,p['original']))
    u.mem_write(code+0x1000,struct.pack('<Qf',owner,.5));u.mem_write(timer+0x30,struct.pack('<f',10));u.mem_write(timer+0xc8,struct.pack('<f',2))
    u.reg_write(UC_X86_REG_RAX,timer);u.reg_write(UC_X86_REG_RDI,owner if matches else owner+1);u.reg_write(UC_X86_REG_RSP,0x200800);u.reg_write(UC_X86_REG_EFLAGS,0x202)
    u.reg_write(UC_X86_REG_XMM0,struct.unpack('<I',struct.pack('<f',10))[0]);u.reg_write(UC_X86_REG_XMM1,0)
    u.emu_start(code,site+len(p['original']),count=100)
    assert struct.unpack('<f',u.mem_read(timer+0xc8,4))[0]==(9.5 if matches else 2)
    value=struct.unpack('<f',struct.pack('<I',u.reg_read(UC_X86_REG_XMM7)&0xffffffff))[0]
    assert value==pytest.approx(.95 if matches else .2)
    assert u.reg_read(UC_X86_REG_RAX)==timer;assert u.reg_read(UC_X86_REG_RSP)==0x200800;assert u.reg_read(UC_X86_REG_EFLAGS)==0x202

@pytest.mark.parametrize('total,expected',[(100,0x7ffe),(89,1234)])
def test_weighted_roll_machine_code_predicate_and_relocated_division(modules,total,expected):
    import struct
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_64
    from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RDI,UC_X86_REG_RSP,UC_X86_REG_XMM0
    _,n,_,_=modules;p=n.PROFILES['legendary_roll'];code=0x180000000;site=0x140000000+p['rva'];table=0x300000
    divisor=site+len(p['original'])+struct.unpack('<i',p['original'][13:17])[0]
    u=Uc(UC_ARCH_X86,UC_MODE_64)
    for address,size in ((code,0x2000),(site&~0xfff,0x1000),(divisor&~0xfff,0x1000),(table,0x1000),(0x200000,0x1000)):u.mem_map(address,size)
    u.mem_write(code,n.make_code('legendary_roll',code,code+0x1000,site,p['original']))
    u.mem_write(table,struct.pack('<f',total));u.mem_write(divisor,struct.pack('<f',32767))
    u.reg_write(UC_X86_REG_RAX,1234);u.reg_write(UC_X86_REG_RDI,table);u.reg_write(UC_X86_REG_RSP,0x200800)
    u.emu_start(code,site+len(p['original']),count=100)
    value=struct.unpack('<f',struct.pack('<I',u.reg_read(UC_X86_REG_XMM0)&0xffffffff))[0]
    assert u.reg_read(UC_X86_REG_RAX)==expected;assert value==pytest.approx(expected/32767)
    assert u.reg_read(UC_X86_REG_RDI)==table;assert u.reg_read(UC_X86_REG_RSP)==0x200800

@pytest.fixture(params=['steam-25372571','epic-4845623'])
def charge_fixture(modules,request):
    import struct
    e,_,_,sdk=modules;s=e.skill_resources
    storage={}
    def put(address,fmt,*values):
        storage.update({address+i:b for i,b in enumerate(struct.pack(fmt,*values))})
    base=0x140000000
    profile=s.BUILDS[request.param]['charges']
    memory=types.SimpleNamespace(base=base,build=request.param,validate=lambda:None,
        read=lambda a,n:bytes(storage[a+i] for i in range(n)))
    s._memory=memory
    storage.update({base+profile['getter']+i:b for i,b in enumerate(profile['getter_context'])})
    put(base+profile['struct_global'],'<Q',0x5000)
    put(base+profile['vtable']+8,'<Q',base+profile['getter'])
    prop=lambda name,offset:types.SimpleNamespace(Name=name,Offset_Internal=offset)
    cls=types.SimpleNamespace(_get_address=lambda:0x5000,_properties=lambda:[prop('MaxCharges',224),prop('Charges',236)])
    attr=types.SimpleNamespace(_properties=lambda:[prop('Value',4),prop('BaseValue',8)])
    lib=types.SimpleNamespace(GetMaxCharges=lambda _:1,GetCharges=lambda _:1)
    sdk.find_object=lambda _,path:attr if path.endswith('GbxAttributeInteger') else lib if 'Default__' in path else cls
    sdk.make_struct=lambda name,**kw:types.SimpleNamespace(**kw)
    pawn=types.SimpleNamespace()
    script=types.SimpleNamespace(Class=types.SimpleNamespace(Name='SkillScript_ActionSkill_Test'))
    skill=types.SimpleNamespace(SkillOwner=pawn,SkillScripts=[script],Name='OwnedSkill',_get_address=lambda:0x6000,_path_name=lambda:'Pawn.OwnedSkill')
    pawn.OakSkillContainer=types.SimpleNamespace(skills=[skill])
    put(0x6028,'<QII',0x7000,1,1);put(0x7000,'<Q',0x8000)
    put(0x8000,'<Q',base+profile['entry_vtable']);put(0x8018,'<Q',0x9000)
    put(0x9000,'<Q',base+profile['vtable']);put(0x9008,'<4i',-1467502208,1220013203,-1798327152,1004771384)
    put(0x9000+224,'<iii',4132,1,1);put(0x9000+236,'<i',1)
    return s,pawn,skill,put,lib,storage

def test_charge_reference_validates_signed_guid_and_attribute_value_offset(charge_fixture):
    s,pawn,_,_,_,_=charge_fixture
    reference,row=next(s.references(pawn))
    assert row['charges']==row['max_charges']==1
    assert reference.ComponentID.A==-1467502208

def test_charge_reference_skips_foreign_owner_before_pointer_reads(charge_fixture):
    s,pawn,skill,_,_,_=charge_fixture;skill.SkillOwner=object()
    assert list(s.references(pawn))==[]

def test_charge_reference_rejects_invalid_array_bounds(charge_fixture):
    s,pawn,_,put,_,_=charge_fixture;put(0x6028,'<QII',0x7000,257,257)
    with pytest.raises(RuntimeError,match='component list'):list(s.references(pawn))

def test_charge_reference_rejects_sdk_native_mismatch(charge_fixture):
    s,pawn,_,_,lib,_=charge_fixture;lib.GetCharges=lambda _:0
    with pytest.raises(RuntimeError,match='readback'):list(s.references(pawn))

def test_charge_reference_rejects_changed_getter(charge_fixture):
    s,pawn,_,_,_,storage=charge_fixture;profile=s.BUILDS[s._memory.build]['charges'];storage[0x140000000+profile['getter']]=0
    with pytest.raises(RuntimeError,match='Unqualified'):list(s.references(pawn))

def test_glide_cleanup_does_not_hide_failed_scalar_restore(modules):
    e,n,_,_=modules
    e.restore=lambda *args:{'ok':False,'error':'scalar restore failed'}
    n.hook=lambda _:types.SimpleNamespace(disable=lambda:{'ok':True})
    result=e.off()
    assert not result['ok'] and any(r.get('error')=='scalar restore failed' for r in result['results'])

def test_action_rejects_invalid_activation_and_off_remains_available(modules):
    e,_,_,_=modules
    with pytest.raises(ValueError):e.action({'op':'set','feature':'god_mode','enabled':'yes'})
    assert e.action({'op':'off'})['ok']

def test_travel_cleanup_restores_before_world_teardown(modules):
    e,_,_,_=modules;calls=[]
    e.off=lambda:calls.append('off') or {'ok':True}
    e._before_travel()
    assert calls==['off']

def test_farming_http_dispatch_and_status_snapshot():
    from test_bridge_perf_bounds import _load_bridge
    bridge=_load_bridge();calls=[]
    bridge.backend_actions.farming_lab_action=lambda payload:calls.append(payload) or {'ok':True}
    bridge.backend_actions.get_status=lambda **kwargs:{'farming_lab':{'features':{'god_mode':{'enabled':False}}}}
    payload={'op':'set','feature':'god_mode','enabled':True}
    assert bridge._handle_action('farming_lab',payload)['ok']
    assert calls==[payload]
    assert not bridge._get_status_snapshot()['farming_lab']['features']['god_mode']['enabled']

def test_all_farming_quick_menu_actions_dispatch_through_shared_backend(monkeypatch):
    from tests.test_quick_menu_last_command import _load_backend_actions
    backend=_load_backend_actions();calls=[]
    monkeypatch.setattr(backend,'farming_lab_action',lambda p:calls.append(p) or {'ok':True})
    for feature in backend.farming_controls.FEATURES:
        for enabled,mode in ((True,'on'),(False,'off')):
            key=f'farming_{feature}_{mode}'
            assert backend.quick_menu_registry.assign_quick_menu_slot({'page':0,'slot':1,'action':key})['ok']
            assert backend.run_quick_menu_action(key,{'player_index':99})['ok']
            assert calls[-1]=={'op':'set','feature':feature,'enabled':enabled}
    assert backend.run_quick_menu_action('farming_all_off',{})['ok']
    assert calls[-1]=={'op':'off'}
