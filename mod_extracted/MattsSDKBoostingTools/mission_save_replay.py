"""Solo save-backed replay bridge. Disk edits belong to the desktop process.

Uses the native save-slot selector with exact original/holding GUID binding.
Only source-backed maps/starts and explicitly scoped spawners are accepted.
"""
from .mission_native import native_address, native_fingerprint
import hashlib
from importlib.resources import files
import json
import math
import os
import re
from pathlib import Path
import struct
import time
import uuid

SESSION = uuid.uuid4().hex
_lease = None
STEAM_111_SAVE_GUARD = ('Save-backed replay is paused for Steam game 1.11 until a '
                        'current save can be checked; no save was edited.')


def specification(name, checkpoint):
    spec = json.loads(files(__package__).joinpath('mission_save_replay.json').read_text(encoding='utf-8'))
    if name != spec['mission'] or str(checkpoint) not in spec['sections']:
        from .mission_selection_specs import specification as selection_specification
        return selection_specification(name, checkpoint)
    catalog = files(__package__).joinpath('mission_practice_catalog.json').read_bytes()
    if hashlib.sha256(catalog).hexdigest() != spec['catalog_sha256']:
        raise RuntimeError('Replay catalog changed; reference data needs review')
    spec['section'] = spec.pop('sections')[str(checkpoint)]
    from .mission_selection_specs import specification as selection_specification
    # The reviewed legacy section supplies its own boundary; prerequisites are
    # mission-wide even when this internal step is hidden by the main picker.
    spec['selection_fallback'] = selection_specification(name, 0)
    spec['selection_fallback']['section'] = dict(spec['section'])
    return spec


def bookmark_specification(spec, guid):
    from .mission_execution import DATA
    section = spec.get('section', {})
    name = spec.get('mission')
    catalog_bytes = files(__package__).joinpath('mission_practice_catalog.json').read_bytes()
    catalog_hash = hashlib.sha256(catalog_bytes).hexdigest()
    compatible = json.loads(catalog_bytes).get('bookmark_compatible_catalog_sha256', [])
    if spec.get('kind') != 'bookmark' or spec.get('guid') != guid or spec.get('catalog_sha256') not in [catalog_hash,*compatible] or name not in DATA:
        raise ValueError('Bookmark character, mission or game data differs')
    groups = [g for g in DATA[name]['groups'] if g['index'] == section.get('checkpoint')]
    if len(groups) != 1:
        raise ValueError('Bookmark objective section is not in this game data')
    owned = {o['name'].casefold() for o in groups[0]['objectives']}
    wanted = section.get('initial_objectives', [])
    point = section.get('location', {})
    placement = section.get('placement', 'exact')
    if (not wanted or not set(wanted).issubset(owned) or placement not in ('native', 'exact')
            or (placement == 'exact' and (set(point) != {'x','y','z'}
                or not all(math.isfinite(float(v)) and abs(float(v)) < 1e9 for v in point.values())))
            or not re.fullmatch(r'[A-Za-z0-9_]+\.[A-Za-z0-9_]+', str(section.get('station', '')))
            or section['station'].split('.')[0].casefold() != str(section.get('world','')).casefold()):
        raise ValueError('Bookmark starting point is invalid')
    spec = dict(spec)
    spec['force_travel'] = True
    spec['section'] = dict(section, placement=placement, refresh_after_load=False)
    return spec


def capture_bookmark():
    _idle_progress()
    if _lease and not _lease.get('closed'):
        raise RuntimeError('Finish or stop replay setup before bookmarking')
    pc, engine, guid, world = _host()
    from . import mission_progression as m
    from .mission_execution import DATA, objectives
    snapshot = engine.snapshot()
    name = m.select(snapshot, 'current')[0]
    if name not in DATA:
        raise ValueError('The current mission has no readable objective data')
    row = m._row(snapshot, name)
    rec = int(row['record'], 16)
    if engine.u64(rec) != native_address(engine, 0xb973820):
        raise RuntimeError('Saved mission record identity differs')
    value = engine.fact(engine.u64(rec+0xa8), 0x60)
    from .mission_cursor import value as cursor_value
    cursor = cursor_value(value)
    wanted = [o['name'].casefold() for o in objectives(engine,row,DATA[name]) if o.get('group') == cursor and o['state'] == 4]
    if not wanted:
        raise RuntimeError('Wait until a mission objective is active before bookmarking')
    pawn = pc.Pawn
    movement = getattr(pawn, 'CharacterMovement', None) if pawn is not None else None
    if movement is None or int(movement.MovementMode) != 1:
        raise RuntimeError('Stand on foot at the point you want to bookmark')
    actual = pawn.K2_GetActorLocation()
    location = {axis.lower(): float(getattr(actual, axis)) for axis in ('X','Y','Z')}
    if not all(math.isfinite(v) and abs(v) < 1e9 for v in location.values()):
        raise RuntimeError('The current player position is unavailable; no bookmark captured')
    return dict(ok=True,pid=os.getpid(),session=SESSION,guid=guid,spec=dict(kind='bookmark',guid=guid,
        mission=name,title=m._metadata(name)['title'],
        catalog_sha256=hashlib.sha256(files(__package__).joinpath('mission_practice_catalog.json').read_bytes()).hexdigest(),
        section=dict(checkpoint=cursor,world=world,placement='exact',location=location,
                     initial_objectives=wanted,refresh_after_load=False)))


def _host():
    from . import mission_progression as m
    rows = m._party()
    if len(rows) != 1 or not rows[0]['host']:
        raise RuntimeError('Save-backed replay currently requires a solo host')
    pc = rows[0]['pc']
    fields = pc.PlayerState.ActiveCharGuid
    guid = ''.join(f'{int(getattr(fields, k)) & 0xffffffff:08x}' for k in ('A', 'B', 'C', 'D'))
    if guid == '0' * 32:
        raise RuntimeError('Wait for the character to finish loading')
    engine = m._engine()
    engine.check_build()
    from .mission_completion_context import world, map_name
    from .mission_completion_placement import _same_world
    w = world()
    if w is None or not _same_world(pc, w):
        raise RuntimeError('Wait for the current map to finish loading')
    return pc, engine, guid, map_name(w)


def _save():
    from mods_base import SETTINGS_DIR
    folder = Path(SETTINGS_DIR) / 'msbt_save_replay'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (_lease['id'] + '.json')
    temp = path.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as stream:
        json.dump(_lease, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def conflict(action):
    return bool(_lease and not _lease.get('closed') and not action.startswith('mission_save_replay_')
                and not action.endswith(('_status', '_preview'))
                and (action.startswith('mission_') or action.startswith('full_progress_')))


def _once(key, function):
    calls = _lease.setdefault('calls', {})
    prior = calls.get(key)
    if prior:
        if prior['state'] == 'returned':
            return prior['result']
        raise RuntimeError('An earlier replay action is unconfirmed; inspect it instead of repeating')
    calls[key] = dict(state='issued', time=time.time())
    _save()
    try:
        result = function()
    except Exception as exc:
        calls[key]['error'] = str(exc)
        _save()
        raise
    calls[key] = dict(state='returned', result=result, time=time.time())
    _save()
    return result


def _idle_progress():
    from . import mission_progression as m
    job = m.status()
    if not job.get('closed') and (job.get('state') in ('running', 'uncertain', 'interrupted') or job.get('challenge_pending')):
        raise RuntimeError('An unfinished mission run needs inspection or closure before save replay')


def _place(pc, section, cycle):
    from . import mission_recorded_placement as placement
    job = dict(anchor=dict(location=section['location']), ground_to_waypoint=section.get('placement') == 'waypoint',
               exact_location=section.get('placement') == 'exact')
    _lease.setdefault('placement_jobs', {})[str(cycle)] = job
    def journal(event):
        _lease.setdefault('events', []).append(event)
        _save()
    placement.start(job, [dict(pc=pc, host=True)], journal)
    _save()
    return dict(ok=True, placement_requested=True, message='Checking normal movement at the recorded beginning')


def _station_section(spec):
    section = spec['section']
    location = section.get('station_location', {})
    if (spec.get('kind') != 'selection' or set(location) != {'x','y','z'}
            or not all(isinstance(v, (int,float)) and math.isfinite(v) and abs(v) < 1e9 for v in location.values())):
        raise RuntimeError('This replay has no authored native station location')
    return dict(section, location=location, placement='waypoint')


def _world_address():
    from .mission_completion_context import world
    current = world()
    if current is None:
        raise RuntimeError('Wait for the mission map to finish loading')
    return current._get_address()


def dispatch(action, payload):
    global _lease
    suffix = action.removeprefix('mission_save_replay_')
    if suffix == 'capture':
        return capture_bookmark()
    if suffix == 'loader_inspect':
        from . import mission_character_loader as loader
        pc,engine,_,_ = _host()
        return loader.inspect(pc,engine)
    if suffix == 'status':
        result = dict(ok=True, pid=os.getpid(), session=SESSION, loaded=False,
                      background_loading=True, lease=_lease['id'] if _lease and not _lease.get('closed') else None)
        if _lease:
            result['calls'] = _lease.get('calls', {})
            result['lease_data'] = {k: _lease[k] for k in ('id', 'original_guid', 'spec')}
            result['loader'] = _lease.get('loader',{})
        try:
            pc, engine, guid, world = _host()
            result.update(loaded=True, guid=guid, world=world)
            if _lease and 'travel_world' in _lease:
                result['travel_loaded'] = _world_address() != _lease['travel_world']
        except RuntimeError as exc:
            message = str(exc)
            if message in (
                'Mission run stopped: gameplay world left or changing',
                'Mission run stopped: no possessed gameplay controller',
                'Mission run stopped: controller belongs to another world',
                'Mission run stopped: world instance changed; explicit reload required',
            ):
                message = 'Waiting for the character and mission map to finish loading.'
            result['message'] = message
        return result
    if suffix == 'begin':
        if _lease and not _lease.get('closed'):
            raise RuntimeError('A save replay already owns the controls; inspect or close it first')
        if payload.get('acknowledge_shared_progress') is not True:
            raise ValueError('Acknowledge the replay changes first')
        _idle_progress()
        pc, engine, guid, world = _host()
        if getattr(engine, 'profile', None) == 'steam-26007962':
            raise RuntimeError(STEAM_111_SAVE_GUARD)
        spec = (bookmark_specification(payload['bookmark_spec'], guid) if payload.get('bookmark_spec')
                else specification(payload.get('mission'), payload.get('checkpoint')))
        if spec.get('kind') == 'selection':
            from .mission_dlc import inspect, requirement
            from .mission_progression import _party
            access = requirement(spec['mission'], inspect(_party()))
            if access and not access['allowed']:
                raise ValueError(access['reason'])
        ident = payload.get('id')
        if not isinstance(ident, str) or len(ident) != 32 or any(c not in '0123456789abcdef' for c in ident):
            raise ValueError('A desktop replay identity is required')
        _lease = dict(id=ident, session=SESSION, pid=os.getpid(), original_guid=guid,
                      spec=spec, calls={}, closed=False)
        _save()
        return dict(ok=True, id=_lease['id'], session=SESSION, pid=os.getpid(), guid=guid,
                    spec=spec, background_loading=True)
    if suffix == 'restore_guard':
        if _lease and not _lease.get('closed') and payload.get('id') != _lease['id']:
            raise RuntimeError('Another save replay owns these controls')
        _idle_progress()
        pc, engine, guid, world = _host()
        return dict(ok=True, loaded=True, guid=guid, world=world, session=SESSION, pid=os.getpid(),
                    lease=_lease['id'] if _lease and not _lease.get('closed') else None)
    if not _lease or _lease.get('closed') or payload.get('id') != _lease['id'] or payload.get('session') != SESSION:
        raise RuntimeError('Replay session changed; no action issued')
    if suffix == 'close':
        from . import mission_character_loader as loader
        loader.stop()
        _lease['closed'] = True
        _save()
        return dict(ok=True, message='Replay controls released; applied save changes and backup retained')
    pc, engine, guid, world = _host()
    cycle = payload.get('cycle', 0)
    if type(cycle) is not int or cycle not in (0, 1):
        raise ValueError('Invalid replay loading cycle')
    spec = _lease['spec']
    section = spec['section']
    if suffix == 'loader_bind':
        slots=payload.get('slots',{})
        holding=payload.get('holding_guid','')
        if (guid!=_lease['original_guid'] or set(slots)!= {'original','other'}
                or any(not isinstance(v,str) or not re.fullmatch(r'C_[0-9]{1,10}',v) for v in slots.values())
                or slots['original']==slots['other'] or not re.fullmatch(r'[a-f0-9]{32}',holding)
                or holding==guid):
            raise ValueError('Automatic reload requires two distinct native saves and character identities')
        if _lease.get('slots') and (_lease['slots']!=slots or _lease['holding_guid']!=holding):
            raise RuntimeError('Automatic reload character binding changed')
        _lease.update(slots=slots,holding_guid=holding);_save()
        return dict(ok=True,bound=True)
    if suffix in ('loader_refresh', 'loader_select'):
        from . import mission_character_loader as loader
        role=payload.get('role')
        if role not in ('other','original') or ((role=='other') != (guid==_lease['original_guid'])):
            raise RuntimeError('Character binding does not match native loading step')
        if not _lease.get('slots') or (role=='original' and guid!=_lease.get('holding_guid')):
            raise RuntimeError('Native loader character identity differs')
        if suffix=='loader_refresh':
            return _once(f'loader_refresh_{role}_{cycle}',lambda:loader.refresh_saves(pc,engine))
        if payload.get('slot')!=_lease['slots'][role]:
            raise RuntimeError('Native loader save slot differs')
        return _once(f'loader_select_{role}_{cycle}',lambda:loader.select_slot(pc,engine,payload.get('slot')))
    if suffix == 'loader_pulse':
        from . import mission_character_loader as loader
        step = payload.get('step')
        if type(step) is not int or not 0 <= step < 128:
            raise ValueError('A bounded unique selector step is required')
        return _once('loader_pulse_'+str(step),lambda:loader.pulse(pc,engine,payload.get('input')))
    if suffix == 'picker':
        role = payload.get('role')
        if role not in ('other', 'original'):
            raise ValueError('Choose the next character-loading step')
        if (role == 'other') != (guid == _lease['original_guid']):
            raise RuntimeError('Character binding does not match this loading step')
        def open_picker():
            from . import backend_actions as backend
            backend.set_target_player(0)
            return backend.load_character_late_join()
        return _once(f'picker_{role}_{cycle}', open_picker)
    if guid != _lease['original_guid']:
        raise RuntimeError('Select the original character before preparing its replay area')
    if suffix == 'travel':
        def travel():
            from .backend_actions import travel_to_station
            _lease['travel_world'] = _world_address()
            _save()
            return travel_to_station(section['station'])
        return _once('travel', travel)
    if world != section['world'].casefold():
        raise RuntimeError('The target map has not loaded; no placement or spawner reset issued')
    if suffix == 'station_check':
        station = _station_section(spec)
        if 'travel_world' in _lease and _world_address() == _lease['travel_world']:
            return dict(ok=True,at_station=False,placement_ready=False,message='Waiting for the refreshed mission map')
        if pc.Pawn is None:
            return dict(ok=True,at_station=False,placement_ready=False,message='Waiting for the character at the selected station')
        actual = pc.Pawn.K2_GetActorLocation()
        distance = math.sqrt(sum((float(getattr(actual,k.upper()))-station['location'][k])**2 for k in ('x','y','z')))
        if not math.isfinite(distance):
            return dict(ok=True,at_station=False,placement_ready=False,message='Waiting for a readable character position')
        # Operational arrival tolerance (15 metres), not a claimed native rule.
        # Authored station origins and the actual pawn spawn have small offsets.
        if distance <= 1500.:
            return dict(ok=True, at_station=True, distance=distance, placement_ready=False)
        from . import mission_recorded_placement as placement
        try:
            placement.preflight(dict(anchor=dict(location=station['location']),ground_to_waypoint=True),[dict(pc=pc,host=True)])
        except RuntimeError as exc:
            if str(exc).startswith(('Stand on foot','Recorded location is not loaded')):
                return dict(ok=True,at_station=False,distance=distance,placement_ready=False,
                            message='The game arrived away from the selected respawn station. '+str(exc))
            raise
        return dict(ok=True,at_station=False,distance=distance,placement_ready=True)
    if suffix == 'station_place':
        return _once('station_place',lambda:_place(pc,_station_section(spec),'station'))
    if suffix == 'station_placement_status':
        _station_section(spec)
        from . import mission_recorded_placement as placement
        job = _lease.get('placement_jobs',{}).get('station')
        if not job:
            raise RuntimeError('No respawn station placement was issued')
        return dict(ok=True,placement_verified=placement.verify(job,[dict(pc=pc,host=True)]))
    if suffix == 'check':
        from . import mission_progression as m
        from .mission_execution import objectives, DATA
        row = m._row(engine.snapshot(), spec['mission'])
        record = int(row['record'], 16)
        if engine.u64(record) != native_address(engine, 0xb973820):
            raise RuntimeError('Saved mission record identity differs')
        value = engine.fact(engine.u64(record + 0xa8), 0x60)
        from .mission_cursor import value as cursor_value
        cursor = cursor_value(value)
        rows = objectives(engine, row, DATA[spec['mission']])
        wanted = {n.casefold() for n in section['initial_objectives']}
        states = {o['name'].casefold(): o['state'] for o in rows if o['name'].casefold() in wanted}
        generic = spec.get('kind') in ('bookmark', 'selection')
        required = wanted if generic or section['checkpoint'] == 28 else {'killboss'}
        boundary_ready = (cursor == section['checkpoint'] and all(states.get(n) == 4 for n in required)
                          and (spec.get('kind') == 'bookmark' or not any(o['state'] == 4 and o.get('group', 0) < section['checkpoint'] for o in rows)))
        if spec.get('force_travel') and engine.world_address == _lease.get('travel_world'):
            boundary_ready = False
        encounter_ready = False
        if generic:
            # Loaded state is verified; arbitrary encounter readiness is not.
            return dict(ok=True,cursor=cursor,objectives=states,boundary_ready=boundary_ready,
                        encounter_ready=boundary_ready,encounter_verified=False)
        if payload.get('encounter') and boundary_ready:
            import unrealsdk
            from .mission_completion_context import world as current_world
            from .mission_completion_placement import _same_world
            w = current_world()
            if section['checkpoint'] == 32:
                bosses = [b for b in unrealsdk.find_all('OakBossFight', exact=False)
                          if _same_world(b, w) and str(b.BossFightName) == 'Boss_Callis_Fortress']
                encounter_ready = len(bosses) == 1 and int(bosses[0].GetBossFightState()) == 2
            else:
                found = {}
                for c in unrealsdk.find_all('SpawnerComponent', exact=False):
                    if not _same_world(c.GetOwner(), w):
                        continue
                    name = str(c.FactsConduit.RegistryName.Name.Name).casefold()
                    if name in ('spawner_shat3_ripmudmouth', 'spawner_shat3_ripmudmouthadds'):
                        if name in found:
                            raise RuntimeError('Encounter spawner identity is ambiguous')
                        found[name] = len(list(c.GetAliveActors(2, False)))
                encounter_ready = len(found) == 2 and all(n > 0 for n in found.values())
        return dict(ok=True, cursor=cursor, objectives=states, boundary_ready=boundary_ready,
                    encounter_ready=encounter_ready)
    if suffix == 'placement_ready':
        if section.get('placement') == 'native':
            raise RuntimeError('This mission state uses the native respawn point; no custom placement allowed')
        from . import mission_recorded_placement as placement
        try:
            placement.preflight(dict(anchor=dict(location=section['location']),
                                     ground_to_waypoint=section.get('placement') == 'waypoint'), [dict(pc=pc, host=True)])
        except RuntimeError as exc:
            if str(exc).startswith(('Stand on foot', 'Recorded location is not loaded')):
                return dict(ok=True, placement_ready=False, message=str(exc))
            raise
        return dict(ok=True, placement_ready=True)
    if suffix == 'place':
        if section.get('placement') == 'native':
            raise RuntimeError('This mission state uses the native respawn point; no custom placement allowed')
        return _once(f'place_{cycle}', lambda: _place(pc, section, cycle))
    if suffix == 'placement_status':
        from . import mission_recorded_placement as placement
        job = _lease.get('placement_jobs', {}).get(str(cycle))
        if not job:
            raise RuntimeError('No recorded placement was issued for this loading cycle')
        ready = placement.verify(job, [dict(pc=pc, host=True)])
        return dict(ok=True, placement_verified=ready)
    if suffix == 'refresh':
        if not section['refresh_after_load']:
            return dict(ok=True, reset_requests=0)
        def refresh():
            from .mission_replay_spawners import refresh_loaded
            specs = [dict(map='World_P', group='base', registry='spawner_shat3_ripmudmouthadds',
                          source='Nexus-Data-Mission0.json', pointer=spec['spawner_source_pointer'])]
            result = refresh_loaded(__import__('unrealsdk'), engine, pc, specs, _lease,
                                    lambda event: (_lease.setdefault('events', []).append(event), _save()))
            if result['deferred']:
                raise RuntimeError('The selected encounter spawner has not loaded')
            return dict(ok=True, **result)
        return _once('refresh', refresh)
    if suffix == 'track':
        from . import mission_progression as m
        row = m._row(engine.snapshot(), spec['mission'])
        import unrealsdk
        token = unrealsdk.make_struct('/Script/CoreUObject.SToken',
                                     Hash=struct.unpack('<i', bytes.fromhex(row['token'])[:4])[0], Name=spec['mission'])
        if engine.read(token._get_address(), 12).hex() != row['token']:
            raise RuntimeError('Replay tracking identity differs')
        _once('track', lambda: (pc.ServerRequestTrackMission(token, int(pc.PlayerState.StableIndex)), dict(ok=True))[1])
        return dict(ok=True, tracked=row['token'] in engine.snapshot()['tracked'])
    raise ValueError('Unsupported save replay action')
