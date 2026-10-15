"""Automated native picker inputs; no desktop coordinates or arbitrary execution.

Pending-focus layout comes from OakUIDataCollector_LoadCharacter::OnDelayedFocus
and the separately qualified Steam/Epic complete function bodies in the manifest.
The pending focus field is diagnostic only. Replay uses the native save-slot
selector and requires exact character GUID readback before any disk edit.
"""
import json
import time
from importlib.resources import files

NAME = 'mission_character_loader'
_task = None
_next_at = 0.
ACTIONS = dict(up='action_ui_menu_nav_up', down='action_ui_menu_nav_down', select='action_ui_menu_nav_select')


def _collector(pc, engine):
    import unrealsdk
    spec = json.loads(files(__package__).joinpath('mission_loader_builds.json').read_text())
    profile = spec['profiles'].get(engine.profile)
    if not profile or engine.read(engine.base+int(profile['rva'],16),32).hex() != profile['fingerprint']:
        raise RuntimeError('Character picker executable evidence differs')
    prefix = pc.Player._path_name()+'.'
    rows = [o for o in unrealsdk.find_all('OakUIDataCollector_LoadCharacter',exact=False)
            if o._path_name().startswith(prefix)]
    if len(rows) != 1:
        raise RuntimeError('The local character picker collector is unavailable or ambiguous')
    raw = engine.read(rows[0]._get_address()+spec['focused_slot_offset'],8)
    return rows[0], raw.hex() if raw[:4] != bytes(4) and raw[4:] != bytes(4) else None


def _input(pc, action):
    import unrealsdk
    prefix = pc.Player._path_name()+'.'
    rows = [o for o in unrealsdk.find_all('EnhancedInputLocalPlayerSubsystem',exact=False)
            if o._path_name().startswith(prefix)]
    if len(rows) != 1:
        raise RuntimeError('The local native input subsystem is unavailable or ambiguous')
    fn = unrealsdk.find_object('Function','/Script/EnhancedInput.EnhancedInputSubsystemInterface:InjectInputVectorForAction')
    target = unrealsdk.find_object('InputAction', '/Game/UI/Data/input/'+ACTIONS[action]+'.'+ACTIONS[action])
    value = unrealsdk.make_struct('/Script/CoreUObject.Vector',X=1.,Y=0.,Z=0.)
    # Interface functions need explicit binding; UObject field lookup omits them.
    unrealsdk.unreal.BoundFunction(fn,rows[0])(target,value,[],[])


def inspect(pc, engine):
    collector, focus = _collector(pc, engine)
    # Read-only context from SelectCharacter -> 15d510a -> 41f638a.
    # SaveManager.GetState (3b18a0) returns the cached pointer at manager+520.
    manager=engine.u64(pc._get_address()+0x398)
    state=engine.u64(manager+0x520) if manager else 0
    active=engine.read(state+0x38,8).hex() if state else None
    return dict(ok=True,focus=focus,profile=engine.profile,selection_method='native_save_slot',
                manual_input_required=engine.profile not in ('steam-25372571','epic-4845623'),
                automatic_selection_verified=engine.profile=='steam-25372571',
                focus_available=bool(focus),menu_may_appear=True,
                native_context=dict(controller=hex(pc._get_address()),collector=hex(collector._get_address()),
                                    character_class_fname=active,
                                    last_played_slot_raw=engine.read(collector._get_address()+0x108,40).hex(),
                                    focused_slot_raw=engine.read(collector._get_address()+0xe0,40).hex()))


def pulse(pc, engine, action):
    if action not in ACTIONS:
        raise ValueError('Unsupported character picker action')
    _, focus = _collector(pc, engine)
    if not focus:
        raise RuntimeError('Wait for the character picker to focus an existing character')
    _input(pc,action)
    return dict(ok=True,action=action,focus_before=focus)


def stop():
    global _task
    _task = None
    from . import camera_tick
    camera_tick.set_needed(NAME,False)


def start(lease, role, cycle, save):
    global _task,_next_at
    if _task:
        raise RuntimeError('An automatic character selection is already active')
    task = dict(role=role,cycle=cycle,started=time.monotonic(),steps=0,visited=[],selected=False)
    lease.setdefault('loader',{})[str(cycle)+'_'+role] = task
    _task = (lease,task,save)
    _next_at = 0.
    save()
    from . import camera_tick
    camera_tick.register(NAME,_tick,priority=90)
    camera_tick.set_needed(NAME,True)
    return dict(ok=True,automatic_selection=True,menu_may_appear=True)


def _tick(*_args):
    global _next_at
    if not _task or time.monotonic() < _next_at:
        return
    lease,task,save = _task
    now = time.monotonic()
    _next_at = now+.15
    try:
        if lease.get('closed'):
            stop();return
        if now-task['started'] > 25 or task['steps'] > 128:
            raise RuntimeError('Automatic character selection timed out; no save was written by this selector')
        from .mission_save_replay import _host
        pc,engine,guid,_ = _host()
        expected = lease['original_guid'] if task['role']=='other' else lease['holding_guid']
        if guid != expected:
            raise RuntimeError('Loaded character changed during automatic selection')
        _,focus = _collector(pc,engine)
        if not focus:
            return
        if 'last_focus' not in task:
            task['last_focus'] = focus
            if task['role']=='other' and 'original_picker_focus' not in lease:
                lease['original_picker_focus'] = focus
            save()
        pending = task.get('pending_focus')
        if pending == focus:
            if now-task['input_at']>3:
                raise RuntimeError('The picker did not respond to its native navigation input')
            return
        if pending:
            task.pop('pending_focus');task['last_focus']=focus
        target = lease['original_picker_focus']
        select = focus != target if task['role']=='other' else focus == target
        if select:
            # Stop the pump and journal before the single commit input.
            task['selected'] = True
            task['commit'] = 'issued'
            save();stop();pulse(pc,engine,'select')
            task['commit'] = 'returned';save();return
        if focus in task['visited']:
            raise RuntimeError('The original character was not found in the picker')
        task['visited'].append(focus)
        task['pending_focus']=focus;task['input_at']=now;task['steps']+=1
        save();pulse(pc,engine,'down' if task['role']=='other' else 'up')
        save()
    except Exception as exc:
        task['error']=str(exc);save();stop()


def clear_runtime_state():
    stop()


def _direct_function(engine, name, restype, *argtypes):
    import ctypes as C
    spec=json.loads(files(__package__).joinpath('mission_loader_builds.json').read_text())
    profile=spec['direct'][engine.profile][name]
    address=engine.base+int(profile['rva'],16)
    if engine.read(address,32).hex()!=profile['fingerprint']:
        raise RuntimeError('Native character loader executable evidence differs')
    return C.WINFUNCTYPE(restype,*argtypes)(address)


def refresh_saves(pc,engine):
    import ctypes as C
    collector,_=_collector(pc,engine)
    _direct_function(engine,'read_saves',None,C.c_void_p)(collector._get_address())
    return dict(ok=True,refresh_requested=True)


def select_slot(pc,engine,slot):
    import ctypes as C
    import re
    import struct
    if not isinstance(slot,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',slot):
        raise ValueError('Invalid native save slot')
    import unrealsdk
    collector,_=_collector(pc,engine)
    token=unrealsdk.make_struct('/Script/CoreUObject.SToken',Name=slot)
    name=struct.unpack('<Q',engine.read(token._get_address()+4,8))[0]
    # SelectCharacter binding 8e3183a forwards the FName and return-to-game bool
    # to 8e31d64. It validates/selects the save and performs native late join.
    _direct_function(engine,'select_slot',None,C.c_void_p,C.c_uint64,C.c_ubyte)(
        collector._get_address(),name,1)
    return dict(ok=True,selection_requested=True,selection_method='native_save_slot',
                verified=False)
