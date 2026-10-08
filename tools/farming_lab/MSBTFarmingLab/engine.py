"""Separate host-local controls, reflected settings first, with owned restoration."""
import itertools
import math
import time
import mods_base
import unrealsdk
from . import skill_resources
import importlib
importlib.reload(skill_resources) # read-only helper; retain no objects across a local code reload

# One-time upgrade of this session's initially read-only lab module. All hooks
# must already be off; the file bridge performs cleanup before reloading engine.
from . import native
if getattr(native,'REVISION',0)<2:
    import importlib
    from . import profiles
    if any(h.owned for h in native._hooks.values()):raise RuntimeError('Turn native tests off before upgrading')
    importlib.reload(profiles);importlib.reload(native)

WORDS = ('ammo','clip','reload','fire','recoil','sway','accuracy','spread','skill','cooldown','grenade','glid','timer','duration','critical','vendor','refresh','inventory','stock','damagecauser')
def props(cls):
    seen = set()
    for owner in itertools.islice(cls._superfields(), 64):
        for p in itertools.islice(owner._properties(), 4096):
            n = str(p.Name)
            if n not in seen: seen.add(n); yield p

def encode(v, depth=2):
    if v is None or type(v) in (bool,int,float,str): return v
    if isinstance(v, unrealsdk.unreal.UObject):
        return {'object':v._path_name(),'class':v.Class._path_name()}
    if depth and isinstance(v,unrealsdk.unreal.WrappedArray):
        return [encode(x,depth-1) for x in itertools.islice(v,48)]
    if depth and isinstance(v, unrealsdk.unreal.WrappedStruct):
        out = {}
        for p in itertools.islice(v._type._properties(), 60):
            try: out[str(p.Name)] = encode(getattr(v,str(p.Name)),depth-1)
            except Exception as exc: out[str(p.Name)] = {'error':str(exc)}
        return {'struct':str(v._type.Name),'fields':out}
    return str(v)[:700]

def describe(obj, words=WORDS):
    if obj is None: return None
    rows = []
    for p in props(obj.Class):
        n = str(p.Name)
        if not any(w.lower() in n.lower() for w in words): continue
        row = {'name':n,'offset':int(p.Offset_Internal),'type':str(p.Class.Name)}
        try: row['value']=encode(getattr(obj,n))
        except Exception as exc: row['error']=str(exc)
        rows.append(row)
    functions=[]
    for owner in itertools.islice(obj.Class._superfields(),64):
        for f in owner._fields():
            if isinstance(f,unrealsdk.unreal.UFunction) and any(w.lower() in str(f.Name).lower() for w in words):
                functions.append(f._path_name())
    return {'object':obj._path_name(),'class':obj.Class._path_name(),'address':hex(obj._get_address()),'properties':rows,'functions':functions[:150]}

def probe(r):
    words=tuple(r.get('words',WORDS))
    kind=r.get('kind','roots')
    if kind=='weapon_state':
        pc,pawn=local()
        return {'ammo_lock':bool(pc.InfiniteAmmoLock.bLocked),'clip_lock':bool(pc.InfiniteClipLock.bLocked),
            'ammo_regen':float(pawn.ammoregenrate.Value),
            'weapons':[{'weapon':describe(w,('ammo','clip','usemode','heat')),
                'behaviors':[describe(b,('ammo','clip','regen','consume','reload','cost','free','size')) for b in w.behaviors]}
                for w in weapons(pawn)]}
    if kind=='named_instances':
        query=str(r.get('query','')).lower()
        return [describe(o,words) for o in itertools.islice((o for o in unrealsdk.find_all(r['class'],False)
            if query in o._path_name().lower()),min(25,int(r.get('limit',10))))]
    if kind=='script_handlers':
        return [{'script':s._path_name(),'handlers':encode(s.CachedActionHandlers,5)}
            for skill in mods_base.get_pc().Pawn.OakSkillContainer.skills for s in skill.SkillScripts
            if 'ActionSkill' in str(s.Class.Name)]
    if kind=='class_functions':
        cls=unrealsdk.find_class(r['class'])
        return list(dict.fromkeys(f._path_name() for owner in cls._superfields() for f in owner._fields()
            if isinstance(f,unrealsdk.unreal.UFunction) and any(w.lower() in str(f.Name).lower() for w in words)))
    if kind=='component_types':
        return [{'type':o._path_name(),'index':int(o.InternalIndex),'address':hex(o._get_address()),'size':o._get_struct_size()}
            for o in unrealsdk.find_all('ScriptStruct') if 'SkillComponent' in str(o.Name) or 'VaultPower' in str(o.Name)]
    if kind=='resources':
        return resources(mods_base.get_pc().Pawn)
    if kind=='charge_pools':
        from .skill_resources import stats
        return stats(mods_base.get_pc().Pawn)
    if kind=='enum':
        enum=unrealsdk.find_enum(r['path'])
        return {k:int(v) for k,v in enum.__members__.items()}
    if kind=='schema':
        obj=unrealsdk.find_object(r.get('class','Function'),r['path'])
        rows=[]
        for p in props(obj):
            row={'name':str(p.Name),'offset':int(p.Offset_Internal),'type':str(p.Class.Name),'flags':int(p.PropertyFlags)}
            for a in ('Struct','PropertyClass','Enum'):
                try: row[a]=getattr(p,a)._path_name()
                except Exception: pass
            rows.append(row)
        return rows
    if kind=='chain':
        v=unrealsdk.find_object(r.get('class','Object'),r['path'])
        for field in r.get('fields',[]):
            v=v[field] if type(field) is int else getattr(v,field)
        return encode(v,4)
    if kind=='skill_scripts':
        pc=mods_base.get_pc()
        rows=[]
        for skill in pc.Pawn.OakSkillContainer.skills:
            scripts=list(skill.SkillScripts)
            if any(any(w.lower() in str(s.Class.Name).lower() for w in words) for s in scripts):
                rows.append({'skill':skill._path_name(),'scripts':[describe(s,('',)) for s in scripts]})
        return rows[:12]
    if kind=='roots':
        pc=mods_base.get_pc();pawn=pc.Pawn if pc else None
        return {'pc':describe(pc,words),'pawn':describe(pawn,words)}
    if kind=='object':
        obj=unrealsdk.find_object(r.get('class','Object'),r['path'])
        return describe(obj,words)
    if kind=='classes':
        rows=[]
        for cls in unrealsdk.find_all('Class'):
            if any(w.lower() in str(cls.Name).lower() for w in words): rows.append(cls._path_name())
        return {'classes':rows[:400]}
    if kind=='instances':
        return [describe(obj,words) for obj in itertools.islice((o for o in unrealsdk.find_all(r['class'],False) if 'Default__' not in str(o.Name)), min(25,int(r.get('limit',10))))]
    raise ValueError('Unknown probe')

FEATURES={
    'god_mode':('God Mode','local player; native damage permission'),
    'infinite_ammo':('Infinite Ammo','local player'),
    'no_reload':('No Reload','local player'),
    'instant_reload':('Instant Reload','owned weapons'),
    'no_recoil':('No Recoil / Sway','owned weapons'),
    'super_accuracy':('Super Accuracy','owned weapons'),
    'rapid_fire':('Rapid Fire','owned weapons; 99 shots/sec requested'),
    'critical_hits':('Critical Hit Boost','local player; trainer value, effect under test'),
    'skill_cooldown':('Instant Skill Cooldown','local player; resource refill'),
    'skill_duration':('Unlimited Skill Duration','local player; resource refill'),
    'grenade_cooldown':('Instant Grenade Cooldown','owned gadget; 0.1 sec on next activation'),
    'vendor_refresh':('Vendor Refresh On Close','host vendors while in use'),
    'glide_duration':('Unlimited Glide Duration','local movement; no vault-power cost while gliding'),
    'legendary_roll':('Weighted Loot High Roll','host process; native experiment, not guaranteed legendary'),
}
_enabled=set()
_snapshots={}
_errors={}
_owner=None
_last_tick=0.0
_reads={}
_last_vendor=0.0
_vendor_paths=[]

def local():
    pc=mods_base.get_pc();pawn=pc.Pawn if pc else None
    if pc is None or pawn is None or not pc.HasAuthority():
        raise RuntimeError('Load a character into your hosted world first')
    return pc,pawn

def identity(pc,pawn):
    return (pc._path_name(),pc._get_address(),pawn._path_name(),pawn._get_address(),pawn.GetLevel()._path_name())

def read_path(obj,path):
    for field in path:obj=getattr(obj,field)
    return obj

def write_path(obj,path,value):
    for field in path[:-1]:obj=getattr(obj,field)
    setattr(obj,path[-1],value)

def edit(feature,obj,path,value):
    path=tuple(path.split('.'));key=(feature,obj._path_name(),obj._get_address(),path)
    current=read_path(obj,path)
    if type(current) not in (bool,int,float):raise TypeError('Expected a scalar reflected field')
    if isinstance(current,float) and not math.isfinite(current):raise ValueError('Non-finite game value')
    if key not in _snapshots:
        _snapshots[key]={'class':obj.Class._path_name(),'original':current,'written':value}
    write_path(obj,path,value)
    actual=read_path(obj,path)
    if isinstance(value,float):matches=math.isclose(actual,value,rel_tol=1e-6,abs_tol=1e-7)
    else:matches=actual==value
    if not matches:raise RuntimeError('Setting readback failed: '+'.'.join(path))
    _snapshots[key]['written']=actual

def restore(feature):
    skipped=[];errors=[]
    for key,snapshot in list(_snapshots.items()):
        name,path,address,fields=key
        if name!=feature:continue
        try:
            obj=unrealsdk.find_object(snapshot['class'],path)
            if obj is None or obj._get_address()!=address:
                skipped.append(path+' (object expired)')
            elif read_path(obj,fields)==snapshot['written']:
                write_path(obj,fields,snapshot['original'])
                if read_path(obj,fields)!=snapshot['original']:raise RuntimeError('Restore readback failed')
            else:skipped.append(path+'.'+'.'.join(fields)+' (changed by game or another mod)')
            del _snapshots[key]
        except Exception as exc:errors.append(str(exc))
    return {'ok':not errors,'errors':errors,'skipped_changed_or_expired':skipped}

def inherits(obj,name):
    return any(str(c.Name)==name for c in obj.Class._superfields())

def weapons(pawn):
    seen=set()
    for slot in pawn.EquippedInventorySlots.items:
        obj=slot.InstancedInventory
        if obj is not None and inherits(obj,'Weapon') and obj.owner==pawn and obj._path_name() not in seen:
            seen.add(obj._path_name());yield obj

def skill_library():
    return unrealsdk.find_object('GbxSkillComponentFunctions_ActionSkill','/Script/OakGame.Default__GbxSkillComponentFunctions_ActionSkill')

def resources(pawn):
    library=skill_library()
    return {'cooldown':float(library.GetCooldown(pawn)), 'duration':float(library.GetDuration(pawn)),
            'cooldown_percent':float(library.GetCooldownAsPercent(pawn)), 'duration_percent':float(library.GetDurationAsPercent(pawn))}

def apply(feature,pc,pawn):
    global _last_vendor,_vendor_paths
    if feature=='god_mode':
        edit(feature,pawn,'bCanBeDamaged',False)
        _reads[feature]={'can_be_damaged':bool(pawn.bCanBeDamaged)}
    elif feature in ('infinite_ammo','no_reload'):
        field='InfiniteAmmoLock' if feature=='infinite_ammo' else 'InfiniteClipLock'
        edit(feature,pc,field+'.bLocked',True)
        _reads[feature]={'locked':bool(read_path(pc,(field,'bLocked')))}
    elif feature=='critical_hits':
        edit(feature,pawn,'DamageCauserData.DefaultCriticalHitChance.Value',1000000.0)
        _reads[feature]={'chance_value':float(pawn.DamageCauserData.DefaultCriticalHitChance.Value),'base_unchanged':float(pawn.DamageCauserData.DefaultCriticalHitChance.BaseValue)}
    elif feature in ('instant_reload','no_recoil','super_accuracy','rapid_fire'):
        count=0
        for weapon in weapons(pawn):
            for b in weapon.behaviors:
                if feature=='rapid_fire' and inherits(b,'WeaponBehavior_Fire'):
                    edit(feature,b,'firerate.Value',99.0)
                    if b.BurstFireDelay.Value>0:edit(feature,b,'BurstFireDelay.Value',.01)
                    count+=1
                elif feature=='instant_reload' and inherits(b,'WeaponBehavior_Reload'):
                    edit(feature,b,'ReloadTime.Value',.05);edit(feature,b,'MinReloadTime.Value',.05)
                    if inherits(b,'WeaponBehavior_StockReload') and b.TapedReloadTime.Value>0:edit(feature,b,'TapedReloadTime.Value',.05)
                    count+=1
                elif feature=='no_recoil':
                    if inherits(b,'WeaponBehavior_Fire'):edit(feature,b,'RecoilScale.Value',0.0);count+=1
                    elif inherits(b,'WeaponBehavior_Sway'):
                        edit(feature,b,'scale.Value',0.0);edit(feature,b,'ZoomScale.Value',0.0);count+=1
                elif feature=='super_accuracy':
                    if inherits(b,'WeaponBehavior_Fire'):
                        for field in ('spread','accuracyimpulse','BurstAccuracyImpulseScale'):edit(feature,b,field+'.Value',0.0)
                        if inherits(b,'WeaponBehavior_OakFire'):edit(feature,b,'movementaccuracymaxvalue.Value',0.0)
                        count+=1
                    elif inherits(b,'WeaponBehavior_Sway'):
                        edit(feature,b,'AccuracyScale.Value',0.0);edit(feature,b,'ZoomAccuracyScale.Value',0.0);count+=1
        if not count:raise RuntimeError('No compatible owned weapon behavior is equipped')
        _reads[feature]={'behaviors':count}
    elif feature in ('skill_cooldown','skill_duration'):
        library=skill_library();mode=unrealsdk.find_enum('EOakActionSkillResourceRefillMode').Normal
        before=resources(pawn)
        charge_refs=list(skill_resources.references(pawn)) if feature=='skill_cooldown' else []
        if feature=='skill_cooldown':library.RefillCooldown(pawn,1.0,mode)
        elif before['duration']>0:library.RefillDuration(pawn,1.0,mode)
        charges=[]
        if feature=='skill_cooldown':
            from .skill_resources import references,library as charge_library
            lib=charge_library()
            for reference,row in charge_refs:
                if row['charges']<row['max_charges']:lib.RefillCooldown(reference,9999.0)
                lib.RefillVirtualCooldown(reference,1.0,unrealsdk.find_enum('EOakActionSkillResourceRefillMode').MissingPercent)
                charges.append(dict(row,after=int(lib.GetCharges(reference))))
        _reads[feature]={'before':before,'after':resources(pawn),'charge_pools':charges}
    elif feature=='grenade_cooldown':
        gadget=pawn.GetGrenadeGadget()
        if gadget is None or gadget.owner!=pawn:raise RuntimeError('No owned grenade gadget equipped')
        edit(feature,gadget,'CooldownTime.Value',.1)
        _reads[feature]={'cooldown_time':float(gadget.CooldownTime.Value)}
    elif feature=='vendor_refresh':
        now=time.monotonic()
        if now-_last_vendor>.5:
            _vendor_paths=[o._path_name() for o in unrealsdk.find_all('OakVendingMachine',False) if 'Default__' not in str(o.Name) and o.HasAuthority()]
            _last_vendor=now
        using=0
        for path in _vendor_paths:
            vendor=unrealsdk.find_object('OakVendingMachine',path)
            if vendor is not None and len(vendor.CurrentUsablePlayers)>0:
                edit(feature,vendor,'bShuffleCalledWhileInUse',True);using+=1
        _reads[feature]={'loaded_vendors':len(_vendor_paths),'vendors_in_use':using}
    elif feature=='glide_duration':
        from .native import hook
        cleanup=hook(feature).disable()
        if not cleanup['ok']:raise RuntimeError(cleanup['error'])
        movement=pawn.OakCharacterMovement
        edit(feature,movement,'VaultPowerCost_Glide.Value',0.0)
        _reads[feature]={'vault_power_cost':float(movement.VaultPowerCost_Glide.Value),'gliding':bool(movement.bIsGliding)}
    elif feature=='legendary_roll':
        from .native import hook
        result=hook(feature).enable(0)
        if not result['ok']:raise RuntimeError(result['error'])
        _reads[feature]=result

def set_feature(feature,enabled):
    global _owner
    if feature not in FEATURES or type(enabled) is not bool:raise ValueError('Unknown feature or invalid enabled value')
    if not enabled:
        _enabled.discard(feature)
        _reads.pop(feature,None)
        result=restore(feature)
        if feature in ('glide_duration','legendary_roll'):
            from .native import hook
            native_result=hook(feature).disable()
            result=dict(result,ok=result['ok'] and native_result['ok'],native=native_result)
        _errors[feature]='' if result['ok'] else str(result)
        return dict(result,feature=feature,enabled=False)
    try:
        pc,pawn=local();ident=identity(pc,pawn)
        if _owner is not None and _owner!=ident:
            result=off()
            if not result['ok']:raise RuntimeError('Previous world restore is incomplete')
        _owner=ident
        apply(feature,pc,pawn);_enabled.add(feature);_errors[feature]=''
        return {'ok':True,'feature':feature,'enabled':True,'readback':_reads.get(feature)}
    except Exception as exc:
        result=set_feature(feature,False);_errors[feature]=str(exc)
        return {'ok':False,'feature':feature,'error':str(exc),'rollback':result}

def status():
    features={}
    for name,(label,scope) in FEATURES.items():
        row=dict(label=label,scope=scope,enabled=name in _enabled,error=_errors.get(name,''),
                 owned_fields=sum(k[0]==name for k in _snapshots),readback=_reads.get(name))
        if name=='legendary_roll':
            from .native import hook
            row['native']=hook(name).status()
        elif name in ('infinite_ammo','no_reload'):
            try:
                field='InfiniteAmmoLock' if name=='infinite_ammo' else 'InfiniteClipLock'
                row['actual_locked']=bool(getattr(mods_base.get_pc(),field).bLocked)
            except Exception:row['actual_locked']=None
        elif name=='god_mode':
            try:row['actual_invulnerable']=not bool(mods_base.get_pc().Pawn.bCanBeDamaged)
            except Exception:row['actual_invulnerable']=None
        features[name]=row
    return {'features':features,'local_test':True,'starts_off':True,'travel_turns_off':True}

def off():
    results={name:set_feature(name,False) for name in FEATURES}
    return {'ok':all(v['ok'] for v in results.values()),'message':'All local tests requested OFF. Completed refills, shots and generated loot are not undone.','results':results}

def tick():
    global _last_tick
    if not _enabled:return
    now=time.monotonic()
    if now-_last_tick<.1:return
    _last_tick=now
    try:
        pc,pawn=local()
        if identity(pc,pawn)!=_owner:off();return
    except Exception:off();return
    for feature in tuple(_enabled):
        try:apply(feature,pc,pawn)
        except Exception as exc:
            set_feature(feature,False);_errors[feature]=str(exc)

def lab_action(payload):
    op=payload.get('op')
    if op=='status':return {'ok':True,**status()}
    if op=='off':return off()
    if op=='test_skill_charge':
        if _enabled:raise RuntimeError('Turn local tests off before a charge refill trial')
        pc,pawn=local()
        reference,row=next(skill_resources.references(pawn))
        if row['charges']<=0:raise RuntimeError('An available charge is required for this trial')
        lib=skill_resources.library()
        try:
            lib.ConsumeCharges(reference,1)
            consumed=int(lib.GetCharges(reference))
            apply('skill_cooldown',pc,pawn)
            refilled=int(lib.GetCharges(reference))
            return {'ok':consumed==row['charges']-1 and refilled==row['max_charges'],
                'before':row,'after_consume':consumed,'after_refill':refilled,
                'message':'Owned skill-charge refill trial; long-press gameplay still requires testing.'}
        finally:
            difference=row['charges']-int(lib.GetCharges(reference))
            if difference>0:lib.AddCharges(reference,difference)
            elif difference<0:lib.ConsumeCharges(reference,-difference)
    if op=='test_lifecycle':
        import sys
        parent=sys.modules[__package__]
        from MattsSDKBoostingTools import backend_actions as backend
        parent.mod.disable()
        removed=not hasattr(backend,'farming_lab_action') and not parent.enabled
        parent.mod.enable()
        return {'ok':removed and parent.enabled and not _enabled,'message':'Local lab disable/enable completed; tests are OFF.','bindings_removed_while_disabled':removed,'features_off_after_enable':not _enabled}
    if op!='set':raise ValueError('Unknown farming lab action')
    result=set_feature(payload.get('feature'),payload.get('enabled'))
    result['message']=(FEATURES[payload['feature']][0]+(' ON' if payload['enabled'] else ' OFF')) if result['ok'] else result.get('error',str(result))
    return result

def install_integration():
    """Use MSBT's existing game-thread dispatch; no separate network listener."""
    import sys
    from MattsSDKBoostingTools import backend_actions as backend, external_bridge as bridge, quick_menu_registry as registry
    parent=sys.modules[__package__]
    if getattr(parent,'_lab_bindings',None):
        if not hasattr(parent,'_lab_catalog_entries'):
            saved_registry,saved_catalog,_=parent._lab_catalog
            parent._lab_catalog_entries={name:saved_registry.ACTION_CATALOG.get(name) for name in saved_catalog}
        for index,(obj,name,old,replacement) in enumerate(parent._lab_bindings):
            if obj is backend and name=='farming_lab_action' and getattr(obj,name,None) is replacement:
                setattr(obj,name,lab_action);parent._lab_bindings[index]=(obj,name,old,lab_action)
        parent.mod.on_enable=on_mod_enable;parent.mod.on_disable=on_mod_disable
        return
    bindings=[];catalog={};entries={};assignable=registry.ASSIGNABLE_ACTIONS
    def bind(obj,name,value):
        old=getattr(obj,name,None);bindings.append((obj,name,old,value));setattr(obj,name,value)
    old_handle=bridge._handle_action;old_qm=backend.run_quick_menu_action;old_refresh=bridge._refresh_status_snapshot
    def handle(name,payload=None):
        if name!='farming_lab':return old_handle(name,payload)
        result=backend.farming_lab_action(dict(payload or {}));refresh(force=True);return result
    def quick(name,payload=None,**kwargs):
        if name=='lab_all_off':return backend.farming_lab_action({'op':'off'})
        if name.startswith('lab_') and name.rsplit('_',1)[-1] in ('on','off'):
            feature,mode=name[4:].rsplit('_',1)
            if feature in FEATURES:return backend.farming_lab_action({'op':'set','feature':feature,'enabled':mode=='on'})
        return old_qm(name,payload,**kwargs)
    def refresh(*args,**kwargs):
        old_refresh(*args,**kwargs)
        if isinstance(bridge._status_snapshot,dict):bridge._status_snapshot={**bridge._status_snapshot,'farming_lab':status()}
    bind(backend,'farming_lab_action',lab_action)
    bind(bridge,'_handle_action',handle);bind(backend,'run_quick_menu_action',quick);bind(bridge,'_refresh_status_snapshot',refresh)
    actions={'lab_all_off':'Farming Lab: All Off'}
    for feature,(label,_) in FEATURES.items():
        for mode in ('on','off'):actions['lab_'+feature+'_'+mode]='Lab: '+label+' '+mode.title()
    for name,label in actions.items():
        catalog[name]=registry.ACTION_CATALOG.get(name)
        entries[name]={'basic':label,'aliases':[]};registry.ACTION_CATALOG[name]=entries[name]
    registry.ASSIGNABLE_ACTIONS=frozenset(assignable)|set(actions)
    parent._lab_bindings=bindings;parent._lab_catalog=(registry,catalog,assignable)
    parent._lab_catalog_entries=entries
    parent._lab_original_options=list(parent.mod.options)
    from mods_base import ButtonOption
    parent.mod.options=list(parent.mod.options)+[
        ButtonOption(label+' '+mode.title(),on_press=lambda _,f=feature,e=mode=='on':set_feature(f,e))
        for feature,(label,_) in FEATURES.items() for mode in ('on','off')]
    # The initial bootstrap is already loaded; install lifecycle callbacks in
    # place so the running session gets the same cleanup as the saved source.
    parent.mod.on_disable=on_mod_disable
    parent.mod.on_enable=on_mod_enable
    refresh(force=True)

def uninstall_integration():
    import sys
    parent=sys.modules[__package__]
    for obj,name,old,replacement in reversed(getattr(parent,'_lab_bindings',[])):
        if getattr(obj,name,None) is replacement:
            if old is None:delattr(obj,name)
            else:setattr(obj,name,old)
    parent._lab_bindings=[]
    if getattr(parent,'_lab_catalog',None):
        registry,catalog,assignable=parent._lab_catalog
        entries=getattr(parent,'_lab_catalog_entries',{})
        removed=set()
        for name,old in catalog.items():
            if registry.ACTION_CATALOG.get(name) is not entries.get(name):continue
            if old is None:registry.ACTION_CATALOG.pop(name,None)
            else:registry.ACTION_CATALOG[name]=old
            removed.add(name)
        registry.ASSIGNABLE_ACTIONS=frozenset((set(registry.ASSIGNABLE_ACTIONS)-(removed-set(assignable)))|(set(assignable)&removed))
        parent._lab_catalog=None;parent._lab_catalog_entries={}
    if hasattr(parent,'_lab_original_options'):parent.mod.options=parent._lab_original_options

def on_mod_disable():
    import sys
    parent=sys.modules[__package__]
    result=off()
    if not result['ok']:raise RuntimeError('Local lab cleanup incomplete: '+str(result))
    uninstall_integration();parent.on_disable()

def on_mod_enable():
    import sys
    parent=sys.modules[__package__]
    parent.on_enable();install_integration()

import sys as _sys
_parent=_sys.modules.get(__package__)
if _parent is not None and getattr(_parent,'enabled',False):install_integration()
