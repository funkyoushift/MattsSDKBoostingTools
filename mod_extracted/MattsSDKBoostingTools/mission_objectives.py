"""One explicitly selected active objective through its native outcome handler."""
import ctypes as C
import json
import os
import struct
import time
import uuid
from pathlib import Path
from importlib.resources import files

LABELS = json.loads(files(__package__).joinpath('mission_objective_labels.json').read_text(encoding='utf-8'))
LABELS = {mission: {name.casefold(): title for name, title in labels.items()}
          for mission, labels in LABELS.items()}
_preview = None
_last = None
_interrupted_checked = False


def _restore_interrupted():
    global _last,_interrupted_checked
    if _last is not None or _interrupted_checked:return
    from mods_base import SETTINGS_DIR
    folder=Path(SETTINGS_DIR)/'msbt_objectives'
    candidates=[]
    if folder.exists():
        for path in folder.glob('*.json'):
            record=json.loads(path.read_text(encoding='utf-8'))
            if record.get('coordinated') and not record.get('closed') and record.get('state') in ('running','uncertain','stopped'):
                candidates.append(record)
    _interrupted_checked=True
    if candidates:
        _last=max(candidates,key=lambda r:r['time'])
        _last.update(state='interrupted',ok=False,
                     message='An objective run was interrupted by a game restart. Inspect current progress, then close its record before new work.')


class _CompletionOwner:
    @property
    def _job(self):return _last
    @property
    def _runtime(self):return _progress()._runtime
    @_runtime.setter
    def _runtime(self,value):_progress()._runtime=value
    def _journal(self,event):
        _last.setdefault('events',[]).append(dict(time=time.time(),**event))
        if event.get('event')=='issued':
            _last.update(state='uncertain',ok=False)
        elif event.get('event')=='returned':
            _last.update(state='running',ok=True,returned=True)
        _save()
    def __getattr__(self,name):return getattr(_progress(),name)


def conflict(action):
    _restore_interrupted()
    return bool(_last and _last.get('coordinated') and _last['state'] in ('running','uncertain','stopped','interrupted') and
                not action.startswith('mission_objective_') and not action.endswith(('_preview','_status')) and
                (action.startswith('mission_') or action in ('full_progress_start','full_progress_resume','full_progress_step')))


def _begin_context(rows):
    from .mission_completion_context import begin
    host=next(r['pc'] for r in rows if r['host'])
    _last.update(coordinated=True,ok=True,state='running',completion_path='objective_graph',
                 target=host._path_name(),completion_context=begin(rows,host._path_name()),
                 name=_last['mission'],events=[],objective_runs={})


def _result():
    return dict(ok=_last['state'] in ('running','completed','replayed') and _last.get('ok',True),state=_last['state'],id=_last['id'],
                mission=_last['mission'],coordinated=True,
                restart_supported=_last['state'] in ('completed','replayed'),
                replay_supported=_last.get('replay_supported',False),
                completion_context=_last.get('completion_context'),
                message=_last.get('message','Preparing the selected objective; no other steps are advanced.'))


def _progress():
    from . import mission_progression
    return mission_progression


def read(engine, row):
    import unrealsdk
    from .mission_challenges import sparse_entries
    record = int(row['record'], 16)
    # A private SDK-owned struct is used only to decode the runtime token. No
    # game-owned memory is written by this read operation.
    token = unrealsdk.make_struct('/Script/CoreUObject.SToken', Name='None')
    states = {engine.read(engine.base+rva, 8).hex(): value for value, rva in
              ((3,0xcb80830),(4,0xcb80870),(10,0xcb80898),(11,0xcb808a8),
               (12,0xcb808a0),(13,0xcb808b0))}
    rows = []
    for address in sparse_entries(engine, record+0x30, 32, 2048):
        entry = engine.read(address, 32)
        ptr = struct.unpack_from('<Q', entry, 16)[0]
        if not ptr:
            continue
        if engine.u64(ptr) != engine.base+0xb973940 or engine.u64(ptr+0x28) != record:
            raise RuntimeError('Objective runtime identity changed')
        definition, storage = engine.u64(ptr+0x40), engine.u64(ptr+0x48)
        fact = engine.fact(storage, 0x20) if storage else None
        C.memmove(token._get_address(), entry[:12], 12)
        name = str(token.Name)
        rows.append(dict(token=entry[:12].hex(), name=name, pointer=hex(ptr),
                         hidden=bool(engine.read(definition+0x3ab,1)[0]),
                         state=states.get((fact or {}).get('fname')), fact=fact))
    return rows


def _signature(rows):
    return sorted((r['token'], (r['fact'] or {}).get('raw')) for r in rows)


def preview(payload):
    global _preview
    m = _progress()
    engine = m._engine()
    snapshot = engine.snapshot()
    names = m.select(snapshot, payload.get('scope', 'current'), payload.get('missions'))
    if len(names) != 1:
        raise ValueError('Choose one mission or the current tracked bounty')
    name = names[0]
    row = m._row(snapshot, name)
    if m._state(row) != 'active':
        raise ValueError('The selected mission must be active to advance one objective')
    objectives = read(engine, row)
    ident = uuid.uuid4().hex
    _preview = dict(id=ident, name=name, token=row['token'], pid=os.getpid(),
                    world=engine.world_address, binding=m._binding(m._party()),
                    signature=_signature(objectives), consumed=False)
    choices = [dict(token=o['token'], name=o['name'],
                    title=LABELS.get(name, {}).get(o['name'].casefold(), o['name'].replace('_',' ')))
               for o in objectives if o['state']==4 and not o['hidden']]
    return dict(ok=True, preview_id=ident, mission=name, objectives=choices,
                message='Choose one active objective. The final objective can naturally finish its mission.')


def _save():
    from mods_base import SETTINGS_DIR
    folder = Path(SETTINGS_DIR)/'msbt_objectives'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder/(_last['id']+'.json')
    temporary=path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(_last,stream,ensure_ascii=False,indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary,path)


def complete(payload):
    global _last
    _restore_interrupted()
    m = _progress()
    if payload.get('acknowledge_shared_progress') is not True:
        raise ValueError('Acknowledge shared host and party progress')
    if m._job and m._job['state'] in ('running','uncertain'):
        raise ValueError('Finish or reconcile the existing mission job first')
    if not _preview or _preview['id']!=payload.get('preview_id') or _preview['consumed']:
        raise ValueError('Refresh objectives before advancing another step')
    if _last and _last['state'] in ('uncertain', 'running','stopped','interrupted'):
        raise ValueError('Read objective status to reconcile the previous call first')
    engine = m._engine()
    snapshot = engine.snapshot()
    row = m._row(snapshot, _preview['name'])
    if (os.getpid()!=_preview['pid'] or engine.world_address!=_preview['world'] or
            m._binding(m._party())!=_preview['binding'] or row['token']!=_preview['token'] or
            m._state(row)!='active'):
        raise ValueError('Mission, world or party changed; refresh objectives')
    objectives = read(engine,row)
    if _signature(objectives)!=_preview['signature']:
        raise ValueError('Objectives changed; refresh before advancing')
    candidates = [o for o in objectives if o['token']==payload.get('objective_token')
                  and o['state']==4 and not o['hidden']]
    if len(candidates)!=1:
        raise ValueError('Choose one currently active visible objective')
    selected = candidates[0]
    from .mission_execution import DATA, require_coverage
    definition=DATA.get(_preview['name'])
    if definition is not None:require_coverage(_preview['name'],definition=definition)
    m.require_clear_journals()
    expected='4157415641545657534883ec3889d3488b054ae090084831e04889442430488b'
    if engine.read(engine.base+0x3df18e0,32).hex()!=expected:
        raise RuntimeError('Objective outcome handler differs from the tested build')
    _preview['consumed']=True
    _last=dict(id=uuid.uuid4().hex, time=time.time(), state='uncertain',
               mission=_preview['name'], token=row['token'], objective=selected,
               pid=os.getpid(),world=engine.world_address,binding=_preview['binding'],
               before=objectives)
    if definition is not None:
        _begin_context(m._party())
        _last.update(phase='complete',message='Preparing the selected objective and its required scene.')
        _save()
        return step(dict(job_id=_last['id']))
    _save()
    C.WINFUNCTYPE(None,C.c_void_p,C.c_uint8)(engine.base+0x3df18e0)(int(selected['pointer'],16),1)
    _last['returned']=True
    _save()
    return status()


def status():
    _restore_interrupted()
    if not _last:
        return dict(ok=True,state='idle',message='No objective has been advanced in this session.')
    if _last.get('closed'):return _result()
    if _last['state']=='interrupted':return _result()
    if _last.get('coordinated') and _last['state'] in ('completed','replayed','cancelled'):
        # This receipt describes settled work. Later replay/travel must not
        # turn it into an uncertain job or re-open its recovery controls.
        return _result()
    if _last.get('coordinated'):
        ctx=_last['completion_context']
        if ctx.get('travel') or ctx.get('placement') or _last.get('phase') in ('prepare','return'):
            return _result()
    m=_progress();engine=m._engine();snapshot=engine.snapshot()
    if (os.getpid()!=_last['pid'] or engine.world_address!=_last['world'] or
            m._binding(m._party()) != _last['binding']):
        return dict(ok=False,state='uncertain',message='World or party changed; previous objective result cannot be verified here.')
    row=m._row(snapshot,_last['mission'])
    if row['token'] != _last['token']:
        return dict(ok=False,state='uncertain',message='Mission instance changed; previous objective result cannot be verified here.')
    after=read(engine,row)
    selected=next((o for o in after if o['token']==_last['objective']['token']),None)
    if _last.get('operation') == 'replay':
        # The native rewind may use an authored earlier checkpoint and resets
        # its companion/later objectives too. Confirm a playable checkpoint,
        # not restoration of rewards or an exact historical world snapshot.
        active = [o for o in after if o['state'] == 4 and not o['hidden'] and
                  (not _last.get('coordinated') or o['token'] in _last['replay_tokens'])]
        confirmed = (m._state(row) == 'active' and selected is not None and
                     selected['state'] not in (10, 11, 12, 13) and bool(active))
        if confirmed:
            _last.update(state='replayed', after=after,ok=True,
                         message='Mission returned to its replay checkpoint. Play the objective again; items and ranks are retained.')
            _save()
        if _last.get('coordinated'):
            if not confirmed:_last['message']='Replay issued once; waiting for the game to activate its checkpoint.'
            return _result()
        return dict(ok=bool(confirmed), state=_last['state'], id=_last['id'],
                    mission=_last['mission'], restart_supported=True, replay_supported=False,
                    message='Mission returned to its replay checkpoint. Play the objective again; items and ranks are retained.'
                    if confirmed else 'Replay issued once; waiting for the game to activate its checkpoint. Check objective status.')
    # Completed_InProgress/Finishing/PostFinishing are still executing authored
    # finish work. Only Completed_PostFinished is a settled objective result.
    # The final objective is destroyed when its mission settles as Completed.
    # Match the same mission instance above; disappearance alone is not success.
    terminal = selected is None and _last.get('returned') and m._state(row) == 'completed'
    confirmed=(selected is not None and selected['state'] == 13) or terminal
    if confirmed and _last.get('coordinated') and not terminal:
        receipt=_last.get('objective_runs',{}).get(_last['mission'],{})
        by_token={o['token']:o for o in after}
        confirmed=all(by_token.get(token,{}).get('state')==13 for token in receipt.get('issued',[]))
    finishing=selected and selected['state'] in (10,11,12)
    if confirmed:
        _last.update(state='completed',after=after,mission_state=m._state(row),ok=True,
                     replay_supported=m._state(row)=='active' and not _last['mission'].startswith('bounty:'),
                     message='Objective advanced; mission is '+str(m._state(row))+'.')
        _save()
    elif finishing and not _last.get('paused'):
        _last.update(state='running',after=after)
        _save()
    if _last.get('coordinated'):
        if not confirmed:_last['message']='Waiting for the selected objective to finish; no completion call repeated.'
        return _result()
    return dict(ok=bool(confirmed),state=_last['state'],id=_last['id'],
                coordinated=bool(_last.get('coordinated')),
                mission=_last['mission'], restart_supported=not _last['mission'].startswith('bounty:'),
                replay_supported=bool(confirmed) and m._state(row)=='active' and not _last['mission'].startswith('bounty:'),
                message=('Objective advanced; mission is '+str(m._state(row))+'.') if confirmed
                else 'Objective is finishing its authored actions. Refresh objective status; no completion call repeated.' if finishing
                else 'Objective call issued once; result not yet confirmed. Refresh objective status; no retry issued.')


def step(payload):
    if not _last or payload.get('job_id')!=_last['id']:raise ValueError('Objective run identifier changed')
    if not _last.get('coordinated') or _last['state']!='running':return status()
    owner=_CompletionOwner()
    try:
        from . import mission_completion_context as context
        if not context.observe(owner):return _result()
        _last.update(world=_last['completion_context']['world'])
        if _last.get('paused'):return status()
        m=_progress();engine=m._engine();row=m._row(engine.snapshot(),_last['mission'])
        if engine.world_address!=_last['world'] or m._binding(m._party())!=_last['binding']:
            raise RuntimeError('World or players changed during objective preparation')
        if row['token']!=_last['token']:raise RuntimeError('Mission instance changed; no objective call repeated')
        from .mission_execution import DATA,advance
        definition=DATA[_last['mission']]
        if _last.get('operation')=='replay':
            if _last['phase']=='prepare':
                if not context.prepare_reset(owner,_last['mission'],row,definition):return _result()
                selected=next((o for o in read(engine,row) if o['token']==_last['objective']['token']),None)
                if selected is None or selected['state']!=13:raise RuntimeError('Selected objective changed before replay')
                record,objective=int(row['record'],16),int(selected['pointer'],16)
                expected='5657534883ec404889d74889ce488b053a90df034831e04889442438e8212a64'
                if (engine.u64(record)!=engine.base+0xb973820 or engine.u64(objective+0x28)!=record or
                        engine.read(engine.base+0x89068f2,32).hex()!=expected):
                    raise RuntimeError('Objective replay differs from the reviewed game build')
                from .mission_effects import reset_interactions
                reset_interactions(_last['mission'],owner._journal,selected['name'])
                # Commit the phase before calling native code. A lost return
                # can never cause another rewind on the next step.
                _last.update(phase='return',state='uncertain',ok=False)
                owner._journal(dict(event='issued',operation='objective_replay',objective=selected))
                C.WINFUNCTYPE(None,C.c_void_p,C.c_void_p)(engine.base+0x89068f2)(record,objective)
                owner._journal(dict(event='returned',operation='objective_replay'))
                return _result()
            if _last['phase']=='return':
                if not context.travel_to(owner,_last['mission'],row,definition['title'],_last['replay_map']):return _result()
                _last.update(phase='settle',replay_wait_started=time.monotonic());_save()
                return status()
            result=status()
            if result['state']!='replayed' and time.monotonic()-_last['replay_wait_started']>120:
                raise RuntimeError('Replay opening did not activate; inspect before continuing')
            return result
        else:
            current=status()
            if current['state']=='completed':return current
            context.expect_finish(owner,_last['mission'],row,definition)
            receipt=_last['objective_runs'].setdefault(_last['mission'],dict(issued=[]))
            result=advance(engine,row,_last['mission'],receipt,owner._journal,definition=definition,
                           selected_token=_last['objective']['token'],current_map=context.map_name(context.world()),
                           before_outcome=lambda objective:context.objective_ready(owner,_last['mission'],row,definition,objective))
            _last['message']=result['message'];_save()
            return status() if result.get('issued') or result['ready'] else _result()
    except Exception as exc:
        from .mission_completion_placement import stop
        if not stop(owner,str(exc),'stopped'):
            _last.update(state='uncertain' if _last['state']=='uncertain' else 'stopped',ok=False,message=str(exc));_save()
    return _result()


def cancel(payload):
    if not _last or payload.get('job_id')!=_last['id']:raise ValueError('Objective run identifier changed')
    if _last.get('coordinated') and _last['state'] in ('running','uncertain','stopped'):
        from .mission_completion_placement import stop
        _last['paused']=True
        if not stop(_CompletionOwner(),retry=True):
            issued=bool(_last.get('returned') or _last['completion_context'].get('travel') or
                        any(r.get('issued') for r in _last.get('objective_runs',{}).values()))
            _last.update(state='uncertain' if issued else 'cancelled',ok=False,
                         message='Objective setup stopped. Applied progress remains; read status before another action.')
            _save()
    return status()


def recover(payload):
    if not _last or payload.get('job_id')!=_last['id']:raise ValueError('Objective run identifier changed')
    if payload.get('acknowledge_shared_progress') is not True:raise ValueError('Allow changes to shared lobby progress')
    mode=payload.get('mode')
    if mode not in ('continue','close'):raise ValueError('Choose continue or close')
    if not _last.get('coordinated'):return status()
    if _last['pid']!=os.getpid() or _last['state']=='interrupted':
        if mode!='close':raise ValueError('The original game session ended; close this record after inspecting current progress')
        _last.update(state='cancelled',ok=False,closed=True,paused=True,replay_supported=False,
                     message='Interrupted objective record closed. No calls repeated and no completion claimed.')
        _save();return _result()
    from .mission_completion_placement import stop
    if mode=='close':
        if stop(_CompletionOwner(),retry=True):
            child=_last['completion_context'].get('placement',{})
            if any(r.get('held') or r.get('restore_pending') or r.get('cleanup_error') for r in child.get('placement',[])):
                return _result()
            _last['completion_context'].pop('placement',None)
        _last.update(state='cancelled',ok=False,paused=True,closed=True,replay_supported=False,
                     message='Objective run closed without repeating calls or claiming completion. Applied progress remains.')
        _save();return _result()
    from .mission_completion_context import observe
    if not observe(_CompletionOwner()):return _result()
    _last['world']=_last['completion_context']['world']
    # An unknown native return may only be reconciled by readback, never by
    # re-entering the issuing phase. Travel remains guarded by its receipt.
    receipt=_last.get('objective_runs',{}).get(_last['mission'],{})
    if receipt.get('pending'):
        m=_progress();engine=m._engine();row=m._row(engine.snapshot(),_last['mission'])
        if row['token']!=_last['token'] or m._binding(m._party())!=_last['binding']:
            raise RuntimeError('Mission or players changed; unknown outcome cannot be reconciled')
        child=next((o for o in read(engine,row) if o['token']==receipt['pending']),None)
        if child is not None and child['state']==13:
            receipt.pop('pending');receipt['progress_at']=time.monotonic();_save()
        elif child is None and m._state(row)=='completed':
            _last['returned']=True;receipt.pop('pending');_save()
        else:return status()
    if _last.get('operation')=='replay' and _last.get('phase')=='return' and not _last.get('returned'):
        # Rebind safely, then verify native rewind before returning to its map.
        m=_progress();engine=m._engine();row=m._row(engine.snapshot(),_last['mission'])
        selected=next((o for o in read(engine,row) if o['token']==_last['objective']['token']),None)
        if row['token']!=_last['token'] or selected is None or selected['state'] in (10,11,12,13):return status()
        _last['returned']=True;_save()
    if status()['state'] in ('completed','replayed'):return status()
    _last.update(state='running',ok=True,paused=False);_save()
    return step(dict(job_id=_last['id']))


def replay_last(payload):
    """Use the native objective checkpoint rewind, including authored reset actions.

    Recovered 89068f2 -> 89069ca -> objective teardown/reset actions, saved
    counters/end-state reset, group rewind, and normal objective activation.
    This intentionally preserves character rewards and progression outside the
    mission. A completed mission must be reopened through the mission action.
    """
    global _last, _preview
    _restore_interrupted()
    if payload.get('acknowledge_shared_progress') is not True:
        raise ValueError('Acknowledge shared host and party progress')
    m = _progress()
    if m._job and m._job['state'] in ('running', 'uncertain'):
        raise ValueError('Finish or reconcile the existing mission job first')
    if not _last or _last.get('operation') == 'replay':
        raise ValueError('No completed objective is available to replay')
    result = status()
    if not result.get('replay_supported'):
        raise ValueError('Check the last objective result. If its mission finished, use Reopen mission.')
    engine = m._engine()
    row = m._row(engine.snapshot(), _last['mission'])
    if row.get('generated') or row.get('replication_type') != 0:
        raise ValueError('Generated bounty replay is not supported yet')
    objectives = read(engine, row)
    selected = next((o for o in objectives if o['token'] == _last['objective']['token']), None)
    if selected is None or selected['state'] != 13:
        raise ValueError('The last objective is no longer completed; refresh its status')
    from .mission_execution import DATA,objectives as authored_objectives,require_coverage
    definition=DATA.get(_last['mission'])
    if definition is None:raise ValueError('Authored replay data is unavailable for this mission')
    require_coverage(_last['mission'],definition=definition)
    authored_rows=authored_objectives(engine,row,definition)
    authored=next(o for o in authored_rows if o['token']==selected['token'])
    from .mission_completion_context import map_name,world
    maps=authored.get('completion_maps') or [definition.get('execution_map')]
    current=map_name(world())
    destination=current if current in maps else maps[0] if len(maps)==1 else None
    if not destination:raise ValueError('The objective replay map is unresolved')
    m.require_clear_journals()
    record, objective = int(row['record'], 16), int(selected['pointer'], 16)
    expected = '5657534883ec404889d74889ce488b053a90df034831e04889442438e8212a64'
    if (engine.u64(record) != engine.base + 0xb973820 or
            engine.u64(objective + 0x28) != record or
            engine.read(engine.base + 0x89068f2, 32).hex() != expected):
        raise RuntimeError('Objective replay differs from the reviewed game build')
    previous = _last
    _preview = None
    _last = dict(id=uuid.uuid4().hex, time=time.time(), operation='replay', state='uncertain',
                 previous_id=previous['id'], mission=previous['mission'], token=row['token'],
                 objective=selected, before=objectives, pid=os.getpid(),
                 world=engine.world_address, binding=m._binding(m._party()))
    _begin_context(m._party())
    _last.update(phase='prepare',replay_map=destination,
                 replay_tokens=[o['token'] for o in authored_rows if o.get('group',999999)<=authored['group']],
                 message='Refreshing the mission area before replaying its checkpoint.')
    _save()
    return step(dict(job_id=_last['id']))
