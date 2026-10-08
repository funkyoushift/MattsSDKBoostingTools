"""Experimental farming controls, scoped to the host and never persisted.

All game interaction is called on the existing backend game-thread queue.
"""
import math
import time
import mods_base
import unrealsdk
from .farming_definitions import FEATURES
from . import farming_skill_resources as skill_resources
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

def set_feature(feature,enabled):
    global _owner
    if feature not in FEATURES or type(enabled) is not bool:raise ValueError('Unknown feature or invalid enabled value')
    if not enabled:
        _enabled.discard(feature)
        _reads.pop(feature,None)
        result=restore(feature)
        if feature in ('glide_duration','legendary_roll'):
            from .farming_native import hook
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
            from .farming_native import hook
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
    return {'features':features,'experimental_loot_roll':True,'starts_off':True,'travel_turns_off':True}

def off():
    results={name:set_feature(name,False) for name in FEATURES}
    return {'ok':all(v['ok'] for v in results.values()),'message':'All farming controls requested OFF. Completed refills, shots and generated loot are not undone.','results':results}

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


def action(payload):
    op=payload.get('op')
    if op=='status':return {'ok':True,**status()}
    if op=='off':return off()
    if op!='set':raise ValueError('Unknown farming control action')
    result=set_feature(payload.get('feature'),payload.get('enabled'))
    result['message']=(FEATURES[payload['feature']][0]+(' ON' if payload['enabled'] else ' OFF')) if result['ok'] else result.get('error',str(result))
    return result

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
