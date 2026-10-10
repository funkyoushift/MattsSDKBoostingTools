"""Farming controls with independent party-player ownership; never persisted.

All game interaction is called on the existing backend game-thread queue.
"""
import math
import time
from contextlib import contextmanager
import mods_base
import unrealsdk
from .farming_definitions import FEATURES
from . import farming_skill_resources as skill_resources
_snapshots={}
_last_tick=0.0
_reads={}
_last_vendor=0.0
_vendor_paths=[]
_sessions={}
_editing_owner=None
_world=None
_changed=False
GLOBAL_FEATURES=frozenset(('vendor_refresh','legendary_roll'))

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
    global _changed
    path=tuple(path.split('.'));key=(feature,obj._path_name(),obj._get_address(),path)
    current=read_path(obj,path)
    if type(current) not in (bool,int,float):raise TypeError('Expected a scalar reflected field')
    if isinstance(current,float) and not math.isfinite(current):raise ValueError('Non-finite game value')
    if key not in _snapshots:
        _snapshots[key]={'class':obj.Class._path_name(),'original':current,'written':value,'owner':_editing_owner}
    elif _snapshots[key].get('owner')!=_editing_owner:
        raise RuntimeError('This field still belongs to another farming target; turn its control off first')
    if current!=value:write_path(obj,path,value);_changed=True
    actual=read_path(obj,path)
    if isinstance(value,float):matches=math.isclose(actual,value,rel_tol=1e-6,abs_tol=1e-7)
    else:matches=actual==value
    if not matches:raise RuntimeError('Setting readback failed: '+'.'.join(path))
    _snapshots[key]['written']=actual

def restore(feature,owner=None):
    skipped=[];errors=[]
    for key,snapshot in list(_snapshots.items()):
        name,path,address,fields=key
        if name!=feature:continue
        if owner is not None and snapshot.get('owner')!=owner:continue
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
            from .farming_skill_resources import library as charge_library
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
        from .farming_native import hook
        cleanup=hook(feature).disable()
        if not cleanup['ok']:raise RuntimeError(cleanup['error'])
        movement=pawn.OakCharacterMovement
        edit(feature,movement,'VaultPowerCost_Glide.Value',0.0)
        _reads[feature]={'vault_power_cost':float(movement.VaultPowerCost_Glide.Value),'gliding':bool(movement.bIsGliding)}
    elif feature=='legendary_roll':
        from .farming_native import hook
        result=hook(feature).enable(0)
        if not result['ok']:raise RuntimeError(result['error'])
        _reads[feature]=result

@contextmanager
def using(session):
    global _reads,_editing_owner,_changed
    previous=_reads,_editing_owner,_changed
    _reads=session['reads'];_editing_owner=session['key'];_changed=False
    try:yield
    finally:
        if _changed:notify_network(session)
        _reads,_editing_owner,_changed=previous


def notify_network(session):
    actors=[session['pc'],session['pawn']]
    try:actors.extend(weapons(session['pawn']))
    except Exception:pass
    for actor in actors:
        try:
            force=getattr(actor,'ForceNetUpdate',None)
            if callable(force):force()
        except Exception:pass  # Expired actors must not block restoration of the others.


def world_identity():
    pc,pawn=local();level=pawn.GetLevel()
    return pc._get_address(),level._path_name(),level._get_address()


def session_for(pc,pawn,label,index=None,global_scope=False):
    key=identity(pc,pawn)+(global_scope,)
    if key not in _sessions:
        _sessions[key]=dict(key=key,pc=pc,pawn=pawn,label=label,index=index,global_scope=global_scope,
                            enabled=set(),errors={},reads={})
    session=_sessions[key];session.update(label=label,index=index)
    return session


def disable_feature(session,feature):
    session['enabled'].discard(feature);session['reads'].pop(feature,None)
    result=restore(feature,session['key'])
    notify_network(session)
    if feature=='legendary_roll':
        from .farming_native import hook
        native=hook(feature).disable()
        result=dict(result,ok=result['ok'] and native['ok'],native=native)
    session['errors'][feature]='' if result['ok'] else str(result)
    return dict(result,feature=feature,enabled=False,target=session['label'])


def set_feature(feature,enabled,pc=None,pawn=None,label='Local',index=None):
    global _world
    if feature not in FEATURES or type(enabled) is not bool:raise ValueError('Unknown feature or invalid enabled value')
    if pc is None:pc,pawn=local()
    if feature in GLOBAL_FEATURES:pc,pawn=local();label='Whole lobby';index=None
    session=session_for(pc,pawn,label,index,feature in GLOBAL_FEATURES)
    if not enabled:return disable_feature(session,feature)
    try:
        world=world_identity()
        if _world is not None and _world!=world:
            if not off()['ok']:raise RuntimeError('Previous world restore is incomplete')
            session=session_for(pc,pawn,label,index,feature in GLOBAL_FEATURES)
        _world=world
        with using(session):apply(feature,pc,pawn)
        session['enabled'].add(feature);session['errors'][feature]=''
        return dict(ok=True,feature=feature,enabled=True,target=label,readback=session['reads'].get(feature))
    except Exception as exc:
        rollback=disable_feature(session,feature);session['errors'][feature]=str(exc)
        return dict(ok=False,feature=feature,target=label,error=str(exc),rollback=rollback)


def status():
    # Cached wrappers can outlive travel/disconnect. Build readback targets from
    # the current roster, comparing stored scalar identities without touching
    # the old session pc/pawn. A Python try/except cannot catch a native AV.
    live = {}
    if _sessions:
        try:
            from . import farming_targets
            for target in farming_targets.party():
                pc = target['pc']
                pawn = pc.Pawn if pc is not None else None
                if pawn is not None:
                    live[identity(pc, pawn)] = (pc, pawn)
        except Exception:
            live = {}
    features={}
    for name,(label,scope) in FEATURES.items():
        targets=[]
        for session in _sessions.values():
            if (name in GLOBAL_FEATURES)!=session['global_scope']:continue
            row=dict(key=str(session['key']),label=session['label'],index=session['index'],
                     enabled=name in session['enabled'],error=session['errors'].get(name,''),
                     owned_fields=sum(k[0]==name and s.get('owner')==session['key'] for k,s in _snapshots.items()),
                     readback=session['reads'].get(name))
            try:
                current = live.get(session['key'][:-1])
                row['live'] = current is not None
                if current is None:
                    targets.append(row)
                    continue
                pc, pawn = current
                if name in ('infinite_ammo','no_reload'):
                    field='InfiniteAmmoLock' if name=='infinite_ammo' else 'InfiniteClipLock'
                    row['actual_locked']=bool(getattr(pc,field).bLocked)
                elif name=='god_mode':row['actual_invulnerable']=not bool(pawn.bCanBeDamaged)
            except Exception:pass
            targets.append(row)
        row=dict(label=label,scope=scope,global_scope=name in GLOBAL_FEATURES,
                 enabled=any(t['enabled'] for t in targets),targets=targets,
                 error='; '.join(t['label']+': '+t['error'] for t in targets if t['error']),
                 owned_fields=sum(t['owned_fields'] for t in targets))
        if name=='legendary_roll':
            from .farming_native import hook
            row['native']=hook(name).status()
        features[name]=row
    return dict(features=features,player_targeting=True,experimental_loot_roll=True,starts_off=True,travel_turns_off=True)


def off():
    global _world
    results=[]
    for session in list(_sessions.values()):
        for feature in FEATURES:
            if (feature in GLOBAL_FEATURES)==session['global_scope']:
                results.append(disable_feature(session,feature))
    for feature in FEATURES:results.append(restore(feature))
    from .farming_native import hook
    for feature in ('glide_duration','legendary_roll'):results.append(hook(feature).disable())
    ok=all(r['ok'] for r in results)
    if ok:_sessions.clear();_world=None
    return dict(ok=ok,message='All farming controls requested OFF for every player. Completed refills and generated loot are not undone.',results=results)


def tick():
    global _last_tick
    if not any(s['enabled'] for s in _sessions.values()):return
    now=time.monotonic()
    if now-_last_tick<.1:return
    _last_tick=now
    try:
        if world_identity()!=_world:off();return
    except Exception:off();return
    from . import farming_targets
    for session in list(_sessions.values()):
        try:valid=farming_targets.current(session['pc'],session['pawn'])
        except Exception:valid=False
        if not valid:
            for feature in tuple(session['enabled']):disable_feature(session,feature)
            if not any(s.get('owner')==session['key'] for s in _snapshots.values()):
                _sessions.pop(session['key'],None)
            continue
        for feature in tuple(session['enabled']):
            try:
                with using(session):apply(feature,session['pc'],session['pawn'])
            except Exception as exc:
                disable_feature(session,feature);session['errors'][feature]=str(exc)


def action(payload,targets=None):
    op=payload.get('op')
    if op=='status':return dict(ok=True,**status())
    if op=='off':return off()
    if op!='set':raise ValueError('Unknown farming control action')
    feature,enabled=payload.get('feature'),payload.get('enabled')
    if feature not in FEATURES or type(enabled) is not bool:raise ValueError('Unknown feature or invalid enabled value')
    if feature in GLOBAL_FEATURES or targets is None:results=[set_feature(feature,enabled)]
    else:results=[set_feature(feature,enabled,t['pc'],t['pc'].Pawn,t['label'],t['index']) for t in targets]
    ok=bool(results) and all(r['ok'] for r in results)
    message=FEATURES[feature][0]+(' ON' if enabled else ' OFF')+' â€” '+', '.join(r.get('target','') for r in results)
    if not ok:message+=': '+'; '.join(r.get('error',str(r)) for r in results if not r['ok'])
    return dict(ok=ok,feature=feature,enabled=enabled if ok else None,message=message,results=results)


def clear_runtime_state(*_args,**_kwargs):
    result=off()
    if not result['ok']:unrealsdk.logging.error('[MSBT Farming] '+str(result))
    return result

# Always restore before travel, including title screens where no pawn is present.
from mods_base import hook as _hook
from unrealsdk.hooks import Type as _Type
@_hook('OakGame.OakPlayerController:ClientTravel',_Type.PRE,immediately_enable=True,
       hook_identifier='msbt_farming_travel_oak_v1')
@_hook('Engine.PlayerController:ClientTravel',_Type.PRE,immediately_enable=True,
       hook_identifier='msbt_farming_travel_engine_v1')
def _before_travel(*args,**kwargs):
    clear_runtime_state()
