import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace as NS

import pytest

ROOT = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def native(monkeypatch):
    package = ModuleType('recorded_test'); package.__path__ = [str(ROOT)]
    monkeypatch.setitem(sys.modules, 'recorded_test', package)
    calls = []; events = []
    floor = NS(usable=True, distance=2.)
    helper = NS(_floor=lambda *a: floor, _usable=lambda f: f.usable, _distance=lambda f: f.distance,
                _vector=lambda p: p, _point=lambda p: p, players_grounded=lambda r: True)
    monkeypatch.setitem(sys.modules, 'recorded_test.mission_practice_placement', helper)
    spec = importlib.util.spec_from_file_location('recorded_test.mission_recorded_placement', ROOT / 'mission_recorded_placement.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    move = NS(MovementMode=1, CustomMovementMode=0, GravityScale=1.5, _get_address=lambda: 4)
    def mode(value, custom): move.MovementMode=value; move.CustomMovementMode=custom
    move.SetMovementMode=mode
    pawn = NS(CharacterMovement=move, _get_address=lambda: 5, _path_name=lambda: 'world:pawn',
              CapsuleComponent=NS(GetScaledCapsuleHalfHeight=lambda:50.),
              K2_GetActorRotation=lambda: {}, K2_GetActorLocation=lambda: dict(X=1., Y=2., Z=3.))
    def teleport(*a):
        calls.append('teleport'); move.GravityScale=1.; return True
    pawn.K2_TeleportTo = teleport
    rows = [dict(pc=NS(Pawn=pawn, _path_name=lambda: 'world:pc'))]
    job = dict(anchor=dict(location=dict(x=1., y=2., z=3.)))
    return NS(module=module, rows=rows, job=job, events=events, calls=calls, pawn=pawn, floor=floor, helper=helper)


def test_native_teleport_preserves_gravity_without_flying_hold(native):
    n=native; n.module.start(n.job,n.rows,n.events.append)
    assert n.calls==['teleport'] and n.pawn.CharacterMovement.GravityScale==1.5
    assert n.pawn.CharacterMovement.MovementMode==1 and n.job['phase']=='recorded_verify'


@pytest.mark.parametrize('result',[False,'exception'])
def test_native_rejection_or_exception_restores_settings_and_never_retries(native,result):
    n=native
    def teleport(*a):
        n.calls.append('teleport'); n.pawn.CharacterMovement.GravityScale=1.
        if result=='exception':raise RuntimeError('uncertain')
        return result
    n.pawn.K2_TeleportTo=teleport
    with pytest.raises(RuntimeError):n.module.start(n.job,n.rows,n.events.append)
    assert n.calls==['teleport'] and n.pawn.CharacterMovement.GravityScale==1.5
    assert n.job['state']=='uncertain' and not n.job['recorded_placement'][0]['returned']


def test_unloaded_or_nonwalkable_location_never_moves_player(native):
    n=native; n.floor.usable=False
    with pytest.raises(RuntimeError,match='not loaded'):n.module.start(n.job,n.rows,n.events.append)
    assert not n.calls and not n.events


def test_waypoint_uses_collision_grounded_point_for_placement_and_verification(native, monkeypatch):
    n=native; n.job['ground_to_waypoint']=True
    n.helper._grounded_probe=lambda *args: dict(X=1.,Y=2.,Z=103.)
    n.pawn.K2_TeleportTo=lambda point,rotation: n.calls.append(point) or True
    n.module.start(n.job,n.rows,n.events.append)
    assert n.calls==[dict(X=1.,Y=2.,Z=103.)]
    assert n.job['anchor']['location']['z']==103.
    n.pawn.K2_GetActorLocation=lambda: dict(X=1.,Y=2.,Z=103.)
    monkeypatch.setattr(n.module.time,'monotonic',lambda:n.job['recorded_verify_since']+1.)
    assert n.module.verify(n.job,n.rows)


def test_unloaded_waypoint_never_teleports_or_applies_movement_hold(native):
    n=native; n.job['ground_to_waypoint']=True
    n.helper._grounded_probe=lambda *args:None
    with pytest.raises(RuntimeError,match='Native station retained'):
        n.module.start(n.job,n.rows,n.events.append)
    assert not n.calls and not n.events


def test_waypoint_inside_floor_raises_only_query_by_measured_capsule_height(native):
    n=native;n.job['ground_to_waypoint']=True;probes=[]
    def probe(pawn,move,point):
        probes.append(dict(point))
        return None if len(probes)==1 else dict(X=1.,Y=2.,Z=80.)
    n.helper._grounded_probe=probe
    n.module.start(n.job,n.rows,n.events.append)
    assert probes==[dict(X=1.,Y=2.,Z=3.),dict(X=1.,Y=2.,Z=103.)]
    assert n.calls==['teleport'] and n.job['anchor']['location']['z']==80.


def test_verification_requires_same_pawn_and_grounding(native,monkeypatch):
    n=native; n.module.start(n.job,n.rows,n.events.append)
    monkeypatch.setattr(n.module.time,'monotonic',lambda:n.job['recorded_verify_since']+1.)
    n.helper.players_grounded=lambda r:False
    assert not n.module.verify(n.job,n.rows)
    n.pawn._get_address=lambda:999
    with pytest.raises(RuntimeError,match='Players changed'):n.module.verify(n.job,n.rows)
