"""Practice placement must survive streaming, respawn and interrupted cleanup."""
import importlib.util
import sys
from pathlib import Path
from types import ModuleType,SimpleNamespace as NS

import pytest

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def scene(monkeypatch):
    pkg=ModuleType('placement_test');pkg.__path__=[str(ROOT)]
    monkeypatch.setitem(sys.modules,pkg.__name__,pkg)
    spec=importlib.util.spec_from_file_location(pkg.__name__+'.mission_practice_placement',ROOT/'mission_practice_placement.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    clock=NS(now=100.,frame=1)
    hooks=set();controllers={};events=[]
    def struct(name,**kw):return NS(**kw)
    sdk=NS(make_struct=struct,find_object=lambda cls,path:controllers.get(path),
           hooks=NS(add_hook=lambda h,t,n,f:hooks.add(n),has_hook=lambda h,t,n:n in hooks,
                    remove_hook=lambda h,t,n:hooks.discard(n)))
    monkeypatch.setitem(sys.modules,'unrealsdk',sdk)
    monkeypatch.setitem(sys.modules,'unrealsdk.hooks',NS(Type=NS(POST=1)))
    monkeypatch.setattr(mod.time,'monotonic',lambda:clock.now)
    monkeypatch.setattr(mod,'_frame',lambda:clock.frame)
    pawns=[];rows=[]
    world=NS(_get_address=lambda:1)
    for i in range(2):
        move=NS(GravityScale=1.5,MovementMode=1,CustomMovementMode=7)
        move._get_address=lambda i=i:100+i
        def mode(value,custom,move=move):move.MovementMode=value;move.CustomMovementMode=custom
        move.SetMovementMode=mode;move.StopMovementImmediately=lambda:None
        pawn=NS(CharacterMovement=move,location=NS(X=0.,Y=float(i*200),Z=100.),
                teleports=0,fail_next=False,discard_next=False,
                CapsuleComponent=NS(GetScaledCapsuleRadius=lambda:40.,GetScaledCapsuleHalfHeight=lambda:100.))
        pawn._get_address=lambda i=i:200+i
        pawn.GetLevel=lambda:NS(OwningWorld=world)
        pawn._path_name=lambda i=i:'Pawn'+str(i)
        pawn.K2_GetActorLocation=lambda pawn=pawn:pawn.location
        pawn.K2_GetActorRotation=lambda:NS()
        def teleport(point,rotation,pawn=pawn):
            pawn.teleports+=1
            if pawn.fail_next:pawn.fail_next=False;return False
            if pawn.discard_next:pawn.discard_next=False;return True
            pawn.location=point;return True
        pawn.K2_TeleportTo=teleport
        pc=NS(Pawn=pawn,_path_name=lambda i=i:'PC'+str(i))
        controllers[pc._path_name()]=pc;pawns.append(pawn)
        rows.append(dict(pc=pc,label='Player'+str(i)))
    def floor(pawn,move,point,distance):
        return NS(bBlockingHit=True,bWalkableFloor=True,FloorDist=point['Z']-100.,
                  HitResult=NS(bStartPenetrating=False))
    monkeypatch.setattr(mod,'_floor',floor)
    job=dict(state='running',ok=True,anchor=dict(location=dict(x=1000.,y=0.,z=100.)))
    def start(count=1,journal=None):mod.start(job,rows[:count],journal or events.append)
    def tick(seconds=.2,frames=1):clock.now+=seconds;clock.frame+=frames;mod.tick()
    def pump(count=20):
        for _ in range(count):tick()
    return NS(mod=mod,clock=clock,pawns=pawns,rows=rows,controllers=controllers,events=events,
              hooks=hooks,job=job,start=start,tick=tick,pump=pump,floor=floor)


def assert_restored(pawn):
    move=pawn.CharacterMovement
    assert (move.GravityScale,move.MovementMode,move.CustomMovementMode)==(1.5,1,7)


def test_encounter_waits_for_streamed_navigation_instead_of_landing_on_pit_floor(scene,monkeypatch):
    s=scene;s.job['navigation_scene']={'actor':{'map':'Test'}};ready=[False]
    monkeypatch.setattr(s.mod,'_navigation_probe',lambda *a:dict(X=1100.,Y=20.,Z=103.) if ready[0] else None)
    monkeypatch.setattr(s.mod,'_grounded_probe',lambda *a:pytest.fail('Encounter must not use the pit floor'))
    s.start();s.pump(6)
    assert s.job['placement'][0]['phase']=='floor'
    assert s.pawns[0].CharacterMovement.GravityScale==0.
    ready[0]=True;s.pump()
    assert s.job['phase']=='world_ready'
    assert s.pawns[0].location.X==1100. and s.pawns[0].location.Y==20.
    assert any(e['event']=='placement_navigation_landing_issued' for e in s.events)
    assert_restored(s.pawns[0])


def test_missing_encounter_navigation_rolls_back_without_falling(scene,monkeypatch):
    s=scene;s.job['navigation_scene']={'actor':{'map':'Test'}}
    monkeypatch.setattr(s.mod,'_navigation_probe',lambda *a:None)
    s.start();s.pump(80);s.pump()
    assert s.job['state']=='stopped'
    assert s.pawns[0].location.X==0.
    assert_restored(s.pawns[0]);assert not s.hooks


@pytest.mark.parametrize('offset',[-8.17529296875,25.])
def test_navigation_height_uses_measured_collision_offset_then_rechecks(scene,monkeypatch,offset):
    s=scene;calls=[]
    monkeypatch.setitem(sys.modules,'placement_test.mission_completion_placement',
                        NS(navigation_point=lambda *a:dict(X=1000.,Y=20.,Z=0.)))
    def floor(pawn,move,point,distance):
        calls.append(dict(point))
        return NS(bBlockingHit=True,bWalkableFloor=True,HitResult=NS(bStartPenetrating=False),
                  FloorDist=offset if len(calls)==1 else 3.)
    monkeypatch.setattr(s.mod,'_floor',floor)
    result=s.mod._navigation_probe(s.pawns[0],s.pawns[0].CharacterMovement,{})
    assert result==dict(X=1000.,Y=20.,Z=106.-offset)
    assert len(calls)==2 and calls[0]['Z']==103.
    assert s.pawns[0].teleports==0


@pytest.mark.parametrize('fault',['penetrating','unwalkable','too_far','nonfinite','recheck_failed','recheck_negative'])
def test_navigation_adjustment_never_waives_supported_landing(scene,monkeypatch,fault):
    s=scene;calls=[]
    monkeypatch.setitem(sys.modules,'placement_test.mission_completion_placement',
                        NS(navigation_point=lambda *a:dict(X=1000.,Y=20.,Z=0.)))
    def floor(*args):
        calls.append(1)
        return NS(bBlockingHit=not(fault=='recheck_failed' and len(calls)>1),
                  bWalkableFloor=fault!='unwalkable',HitResult=NS(bStartPenetrating=fault=='penetrating'),
                  FloorDist=-51. if fault=='too_far' else float('nan') if fault=='nonfinite' else -8.)
    monkeypatch.setattr(s.mod,'_floor',floor)
    assert s.mod._navigation_probe(s.pawns[0],s.pawns[0].CharacterMovement,{}) is None
    assert len(calls)==(2 if fault.startswith('recheck') else 1)
    assert s.pawns[0].teleports==0


def test_waits_for_floor_and_later_frames_before_ready(scene,monkeypatch):
    s=scene;s.start();s.tick()
    monkeypatch.setattr(s.mod,'_floor',lambda *a:NS(bBlockingHit=False,bWalkableFloor=False))
    s.pump(3)
    assert s.job['phase']=='placement' and s.pawns[0].CharacterMovement.GravityScale==0
    monkeypatch.setattr(s.mod,'_floor',s.floor)
    s.pump()
    assert s.job['phase']=='world_ready' and s.job['state']=='running'
    assert_restored(s.pawns[0]);assert not s.hooks


@pytest.mark.parametrize('fault',['none','missing_hit','penetrating','sideways','deep','nonfinite','capsule_blocked'])
def test_loaded_surface_requires_native_line_and_capsule_support(scene,monkeypatch,fault):
    s=scene;sdk=sys.modules['unrealsdk'];calls=[]
    hit=NS(bBlockingHit=True,bStartPenetrating=fault=='penetrating',
           ImpactPoint=NS(X=1002. if fault=='sideways' else 1000.,Y=0.,
                          Z=float('nan') if fault=='nonfinite' else -6000. if fault=='deep' else 0.))
    def trace(**kw):calls.append(kw);return fault!='missing_hit',kw['ActorsToIgnore'],hit
    lib=NS(LineTraceSingle=trace);prior=sdk.find_object
    sdk.find_object=lambda cls,path:lib if cls=='KismetSystemLibrary' else prior(cls,path)
    own=NS(GetLevel=s.pawns[0].GetLevel)
    streamed=NS(_path_name=lambda:'/Game/Map/_Generated_/Cell.Map:Character',GetLevel=s.pawns[0].GetLevel)
    old=NS(GetLevel=lambda:NS(OwningWorld=NS(_get_address=lambda:2)))
    sdk.find_all=lambda *a,**k:[own,streamed,old]
    if fault=='capsule_blocked':monkeypatch.setattr(s.mod,'_floor',lambda *a:NS(bBlockingHit=False))
    point=s.mod._grounded_probe(s.pawns[0],s.pawns[0].CharacterMovement,dict(X=1000.,Y=0.,Z=900.))
    assert point==(dict(X=1000.,Y=0.,Z=103.) if fault=='none' else None)
    assert calls[0]['ActorsToIgnore']==[own,streamed]


def test_loaded_indoor_floor_avoids_lifting_player_into_ceiling(scene,monkeypatch):
    s=scene;s.job['anchor']['location']['z']=900.
    monkeypatch.setattr(s.mod,'_grounded_probe',lambda *a:dict(X=1000.,Y=0.,Z=103.))
    original=s.pawns[0].K2_TeleportTo
    def teleport(point,rotation):
        if point.Z>400. or abs(point.X-s.pawns[0].location.X)<.01:return False
        return original(point,rotation)
    s.pawns[0].K2_TeleportTo=teleport
    s.start();s.pump()
    assert s.job['phase']=='world_ready'
    assert any(e['event']=='placement_loaded_surface' for e in s.events)
    assert s.pawns[0].teleports==1
    assert_restored(s.pawns[0]);assert not s.hooks


@pytest.mark.parametrize('cancel',[False,True])
def test_already_at_supported_destination_needs_no_teleport_even_for_cleanup(scene,monkeypatch,cancel):
    s=scene
    monkeypatch.setattr(s.mod,'_grounded_probe',lambda *a:dict(X=0.,Y=0.,Z=100.))
    s.pawns[0].K2_TeleportTo=lambda *a:pytest.fail('No native teleport is needed at the supported destination')
    s.start();s.tick()
    if cancel:s.mod.cancel()
    s.pump()
    assert s.job['state']==('cancelled' if cancel else 'running')
    assert s.job['phase']=='placement' if cancel else s.job['phase']=='world_ready'
    assert_restored(s.pawns[0]);assert not s.hooks


def test_explicit_cleanup_reconciles_safe_native_respawn_without_teleport(scene):
    s=scene;s.start();s.tick();s.mod.cancel();s.pump()
    record=s.job['placement'][0];record['cleanup_error']='Player left origin during native recovery'
    s.pawns[0].location.X=9000.
    count=s.pawns[0].teleports
    assert s.mod.retry_cleanup(s.job,s.events.append)
    s.pump()
    assert s.job['state']=='cancelled' and s.pawns[0].teleports==count
    assert 'cleanup_error' not in record and not record['held']
    assert s.events[-2]['event']=='placement_cleanup_verified' and not s.events[-2]['origin_returned']


@pytest.mark.parametrize('unsafe',['floor','movement','identity'])
def test_cleanup_reconciliation_does_not_clear_unverified_recovery(scene,monkeypatch,unsafe):
    s=scene;s.start();s.tick();s.mod.cancel();s.pump()
    record=s.job['placement'][0];record['cleanup_error']='Previous location changed'
    count=s.pawns[0].teleports
    if unsafe=='floor':monkeypatch.setattr(s.mod,'_floor',lambda *a:NS(bBlockingHit=False))
    elif unsafe=='movement':s.pawns[0].CharacterMovement.MovementMode=6
    else:s.pawns[0]._get_address=lambda:999
    assert s.mod.retry_cleanup(s.job,s.events.append)
    s.pump()
    assert s.job['state']=='uncertain' and record['cleanup_error']
    assert s.pawns[0].teleports==count


def test_same_frame_cannot_finish_landing(scene):
    s=scene;s.start();s.tick()
    for _ in range(20):s.tick(.2,0)
    assert s.job['placement'][0]['phase']=='floor'
    s.pump();assert s.job['phase']=='world_ready'


def test_map_loading_pawn_is_not_grounded(scene):
    s=scene
    assert s.mod.players_grounded(s.rows)
    s.pawns[0].CharacterMovement.MovementMode=0
    assert not s.mod.players_grounded(s.rows)


def test_floor_uses_native_adjusted_arrival(scene,monkeypatch):
    s=scene
    original=s.pawns[0].K2_TeleportTo
    def teleport(point,rotation):
        point.X+=25
        return original(point,rotation)
    s.pawns[0].K2_TeleportTo=teleport
    s.start();s.tick()
    assert s.job['placement'][0]['probe']['X']==1025
    s.pump();assert s.job['phase']=='world_ready'


def test_negative_sweep_distance_is_not_a_landing_solution(scene,monkeypatch):
    s=scene;s.start();s.tick()
    def floor(pawn,move,point,distance):
        found=s.floor(pawn,move,point,distance)
        if point['X']!=0:found.FloorDist=-40.
        return found
    monkeypatch.setattr(s.mod,'_floor',floor)
    s.pump(5)
    assert s.job['placement'][0]['phase']=='floor'
    assert s.pawns[0].teleports==1
    s.mod.cancel();s.pump();assert_restored(s.pawns[0])


def test_successful_line_floor_does_not_use_failed_sweep_distance(scene,monkeypatch):
    s=scene
    def floor(pawn,move,point,distance):
        found=s.floor(pawn,move,point,distance)
        found.bLineTrace=True;found.LineDist=found.FloorDist;found.FloorDist=-40.
        return found
    monkeypatch.setattr(s.mod,'_floor',floor)
    assert s.mod.players_grounded(s.rows)
    s.start();s.pump()
    assert s.job['phase']=='world_ready' and s.pawns[0].location.Z==103.
    assert_restored(s.pawns[0]);assert not s.hooks


def test_native_teleport_refresh_of_movement_is_held_before_next_frame(scene):
    s=scene;original=s.pawns[0].K2_TeleportTo
    def teleport(point,rotation):
        result=original(point,rotation)
        s.pawns[0].CharacterMovement.GravityScale=1.5
        return result
    s.pawns[0].K2_TeleportTo=teleport
    s.start();s.pump()
    assert s.job['phase']=='world_ready'
    assert_restored(s.pawns[0]);assert not s.hooks


def test_delayed_native_movement_refresh_keeps_bounded_hold(scene):
    s=scene;s.start();s.tick()
    move=s.pawns[0].CharacterMovement
    move.GravityScale=1.5;move.MovementMode=3
    s.tick()
    assert move.GravityScale==0 and move.MovementMode==5
    assert any(e['event']=='placement_hold_refreshed' for e in s.events)
    s.pump()
    assert s.job['phase']=='world_ready'
    assert_restored(s.pawns[0]);assert not s.hooks


def test_delayed_refresh_after_return_keeps_hold_until_floor_loads(scene,monkeypatch):
    s=scene;s.start();s.tick();s.mod.cancel();s.tick()
    monkeypatch.setattr(s.mod,'_floor',lambda *args:NS(bBlockingHit=False))
    move=s.pawns[0].CharacterMovement
    move.GravityScale=1.5;move.MovementMode=3
    s.tick()
    assert move.GravityScale==0 and move.MovementMode==5
    assert s.job['placement'][0]['held']
    monkeypatch.setattr(s.mod,'_floor',s.floor);s.pump()
    assert_restored(s.pawns[0]);assert not s.hooks


def test_hold_refresh_rejects_displacement_instead_of_continuing(scene):
    s=scene;s.start();s.tick()
    s.pawns[0].location.Z-=200
    s.pawns[0].CharacterMovement.GravityScale=1.5
    s.tick()
    assert s.mod._active['rollback']
    assert not any(e['event']=='placement_hold_refreshed' for e in s.events)
    s.pump();assert_restored(s.pawns[0]);assert not s.hooks


def test_high_encounter_waypoint_uses_confirmed_vertical_floor(scene,monkeypatch):
    s=scene;s.job['anchor']['location']['z']=3305.
    distances=[]
    def bounded_floor(pawn,move,point,distance):
        distances.append(distance)
        floor=s.floor(pawn,move,point,distance)
        if floor.FloorDist>distance:return NS(bBlockingHit=False)
        return floor
    monkeypatch.setattr(s.mod,'_floor',bounded_floor)
    s.start();s.pump()
    assert s.job['phase']=='world_ready' and s.pawns[0].location.Z==103.
    assert max(distances)==5000.
    assert_restored(s.pawns[0]);assert not s.hooks


@pytest.mark.parametrize('outcome', ['success', 'false', 'raise'])
def test_return_teleport_keeps_hold_during_unloaded_floor(scene, monkeypatch, outcome):
    s=scene;s.start();s.tick()
    original=s.pawns[0].K2_TeleportTo
    def teleport(point, rotation):
        original(point, rotation)
        s.pawns[0].CharacterMovement.GravityScale=1.5
        if outcome=='raise':raise RuntimeError('native return failed')
        return outcome=='success'
    s.pawns[0].K2_TeleportTo=teleport
    monkeypatch.setattr(s.mod,'_floor',lambda *args:NS(bBlockingHit=False))
    s.mod.cancel();s.tick();s.tick()
    assert s.job['placement'][0]['held']
    assert s.pawns[0].CharacterMovement.GravityScale==0
    assert s.pawns[0].CharacterMovement.MovementMode==5


def test_landing_hold_survives_native_refresh_until_readback(scene):
    s=scene;original=s.pawns[0].K2_TeleportTo
    def teleport(point, rotation):
        result=original(point, rotation)
        s.pawns[0].CharacterMovement.GravityScale=1.5
        return result
    s.pawns[0].K2_TeleportTo=teleport
    s.start()
    for _ in range(15):
        s.tick()
        if s.job['placement'][0]['phase']=='restore':break
    assert s.job['placement'][0]['phase']=='restore'
    assert s.pawns[0].CharacterMovement.GravityScale==0
    s.pump();assert_restored(s.pawns[0])


def test_teleport_repossession_does_not_hold_replacement(scene):
    s=scene
    old_move=s.pawns[0].CharacterMovement
    stale=NS(active=False,reads=0)
    class GuardedMovement:
        def __getattr__(self,name):
            if stale.active:
                stale.reads+=1
                raise RuntimeError('Destroyed movement wrapper')
            return getattr(old_move,name)
        def __setattr__(self,name,value):setattr(old_move,name,value)
    s.pawns[0].CharacterMovement=GuardedMovement()
    replacement=NS(_get_address=lambda:999,_path_name=lambda:'Replacement')
    def teleport(*args):
        s.controllers['PC0'].Pawn=replacement
        stale.active=True
        return True
    s.pawns[0].K2_TeleportTo=teleport
    s.start();s.pump()
    assert s.job['state']=='uncertain'
    assert not hasattr(replacement,'CharacterMovement')
    assert stale.reads==0


def test_true_teleport_but_falling_never_reports_ready(scene):
    s=scene;s.start()
    for _ in range(15):
        s.tick()
        if s.job['placement'][0]['phase']=='verify':break
    s.pawns[0].location=NS(X=1000.,Y=0.,Z=-500.)
    s.pump()
    assert s.job['state']=='stopped' and s.job['phase']=='placement'
    assert_restored(s.pawns[0]);assert not s.hooks


def test_cancel_restores_exact_nondefault_settings_and_position(scene):
    s=scene;s.start();s.tick();s.mod.cancel();s.pump()
    assert s.job['state']=='cancelled' and s.pawns[0].location.X==0
    assert_restored(s.pawns[0]);assert not s.hooks


def test_timeout_restores_without_desktop_polling(scene,monkeypatch):
    s=scene;s.start();s.tick()
    monkeypatch.setattr(s.mod,'_floor',lambda pawn,move,point,d:s.floor(pawn,move,point,d) if point['X']==0 else NS(bBlockingHit=False))
    s.tick(16);s.pump()
    assert s.job['state']=='stopped';assert_restored(s.pawns[0])


def test_second_player_failure_cleans_first_player(scene):
    s=scene;s.pawns[1].fail_next=True;s.start(2);s.pump()
    assert s.job['state']=='stopped'
    for pawn in s.pawns:assert_restored(pawn)
    assert not s.hooks


def test_respawn_never_restores_old_fields_onto_replacement(scene):
    s=scene;s.start();s.tick()
    replacement=NS(_get_address=lambda:999,_path_name=lambda:'Replacement')
    s.controllers['PC0'].Pawn=replacement;s.pump()
    assert s.job['state']=='uncertain'
    assert not hasattr(replacement,'CharacterMovement')
    assert s.job['placement'][0]['held']


def test_guest_unpossession_does_not_block_host_cleanup(scene):
    s=scene;s.start(2);s.tick();s.controllers['PC1'].Pawn=None;s.pump()
    assert s.job['state']=='uncertain';assert_restored(s.pawns[0])
    assert s.job['placement'][1]['cleanup_error']


def test_persistent_journal_failure_cannot_leave_gravity_disabled(scene):
    s=scene;s.start();s.tick()
    def failed(event):raise OSError('disk full')
    s.mod._active['journal']=failed
    s.pump()
    assert s.job['state']=='uncertain';assert_restored(s.pawns[0]);assert not s.hooks
    assert s.pawns[0].location.X==0 and s.pawns[0].location.Z==100


def test_frame_read_failure_still_restores_every_player(scene,monkeypatch):
    s=scene;s.start(2);s.tick()
    def failed():raise RuntimeError('frame unavailable')
    monkeypatch.setattr(s.mod,'_frame',failed);s.pump()
    assert s.job['state']=='uncertain'
    for pawn in s.pawns:
        assert_restored(pawn)
        assert pawn.location.X==0 and pawn.location.Z==100
    assert not s.hooks


def test_cleanup_failure_stays_uncertain_and_pending(scene):
    s=scene;s.start();s.tick()
    def failed(*args):raise RuntimeError('movement restore failed')
    s.pawns[0].CharacterMovement.SetMovementMode=failed
    s.mod.cancel();s.pump()
    assert s.job['state']=='uncertain' and s.job['placement'][0]['restore_pending']


def test_unloaded_return_keeps_protection_until_explicit_cleanup_retry(scene,monkeypatch):
    s=scene;s.start();s.tick()
    monkeypatch.setattr(s.mod,'_floor',lambda *args:NS(bBlockingHit=False))
    def failed():raise RuntimeError('frame unavailable')
    monkeypatch.setattr(s.mod,'_frame',failed)
    s.tick();s.tick();s.tick(11)
    assert s.job['state']=='uncertain' and s.job['placement'][0]['held']
    assert s.pawns[0].CharacterMovement.GravityScale==0 and not s.hooks
    monkeypatch.setattr(s.mod,'_floor',s.floor)
    assert s.mod.retry_cleanup(s.job,s.events.append)
    s.pump()
    assert s.job['state']=='cancelled' and not s.hooks
    assert_restored(s.pawns[0]);assert s.pawns[0].location.X==0


def test_explicit_retry_can_recover_failed_origin_teleport(scene,monkeypatch):
    s=scene;s.start();s.tick();s.pawns[0].fail_next=True
    s.mod.cancel();s.pump()
    assert s.job['state']=='uncertain' and s.pawns[0].teleports==2
    assert s.mod.retry_cleanup(s.job,s.events.append)
    s.pump()
    assert s.job['state']=='cancelled' and s.pawns[0].teleports==3
    assert_restored(s.pawns[0]);assert s.pawns[0].location.X==0
