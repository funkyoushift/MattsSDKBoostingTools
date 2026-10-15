"""Lobby-wide replay jumps using authored preceding completion anchors."""
import json
import os
import struct
import time
import uuid
from importlib.resources import files
from pathlib import Path

CATALOG = json.loads(files(__package__).joinpath('mission_practice_catalog.json').read_text(encoding='utf-8'))
DATA = CATALOG['missions']
RECORDED = json.loads(files(__package__).joinpath('mission_recorded_starts.json').read_text(encoding='utf-8'))
_preview = None
_job = None
STALL_TIMEOUT = 420.  # Longer than the shared native finish-action guard.

def _progress():
    from . import mission_progression
    return mission_progression

class _CompletionOwner:
    """Use the shared travel guard while keeping the two job journals separate."""
    @property
    def _job(self):return _job
    @property
    def _runtime(self):return _progress()._runtime
    @_runtime.setter
    def _runtime(self,value):_progress()._runtime=value
    def _journal(self,event):_save(event)
    def __getattr__(self,name):return getattr(_progress(),name)

def _world():
    from mods_base import ENGINE
    return getattr(getattr(ENGINE,'GameViewport',None),'World',None)

def _map(world):
    return world._path_name().split('.')[-1].casefold()

def _roster(rows):
    from .campaign_replay import roster
    return roster(rows)


def _return_map(definition,selected,checkpoint,anchor):
    """Keep an unplayed map-arrival step on its source-authored approach map."""
    destination=selected.get('travel_map')
    if destination:
        if anchor and anchor['map'].casefold()!=destination:return anchor['map'].casefold()
        for group in sorted(definition['groups'],key=lambda g:g['index'],reverse=True):
            if group['index']>=checkpoint:continue
            maps={m for o in group['objectives'] for m in o.get('completion_maps',[]) if m!=destination}
            if len(maps)>1:raise RuntimeError('Replay approach map is ambiguous; no travel or reset issued')
            if maps:return next(iter(maps))
        raise RuntimeError('Replay approach map is unresolved; the selected arrival will not be consumed')
    if anchor:return anchor['map'].casefold()
    maps=selected.get('completion_maps') or [definition.get('execution_map')]
    if len(maps)!=1 or not maps[0]:raise RuntimeError('Selected replay map is unresolved or ambiguous')
    return maps[0]

def conflict(action):
    return bool(_job and _job['state'] in ('running','uncertain') and
                not action.startswith('mission_practice_') and
                not action.endswith(('_preview','_status')) and
                (action.startswith('mission_') or action in ('full_progress_start','full_progress_resume','full_progress_step')))

def _save(event=None):
    if event is not None:_job.setdefault('events',[]).append(dict(time=time.time(),**event))
    from mods_base import SETTINGS_DIR
    folder=Path(SETTINGS_DIR)/'msbt_practice';folder.mkdir(parents=True,exist_ok=True)
    path=folder/(_job['id']+'.json');temp=path.with_suffix('.tmp')
    with temp.open('w',encoding='utf-8') as f:
        json.dump(_job,f,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(temp,path)

def preview(payload):
    global _preview
    m=_progress();engine=m._engine();snapshot=engine.snapshot()
    names=m.select(snapshot,payload.get('scope','current'),payload.get('missions'))
    if len(names)!=1 or names[0] not in DATA:raise ValueError('Choose one mission for replay')
    name=names[0]
    try:
        row=m._row(snapshot,name);state=m._state(row)
    except ValueError:
        row=None;state=None
    from .mission_dlc import inspect,requirement
    rows=m._party();access=requirement(name,inspect(rows))
    reason=(access['reason'] if access and not access['allowed'] else
            'Mission prerequisites are not available' if state not in ('active','accepted','completed','available') else None)
    choices=[]
    from .mission_selection_specs import catalog as selection_catalog
    selection_row=selection_catalog()['missions'].get(name,{})
    from .mission_execution import coverage_error
    from .mission_selection import main_groups
    for g,primary in main_groups(name,DATA[name]):
        visible=[primary]
        anchor=g['start_anchor']
        recorded=RECORDED.get(name,{}).get(str(g['index']))
        if (recorded and recorded['source_hashes']==CATALOG['source_hashes'] and
                recorded['objective'].casefold()==primary['name'].casefold()):
            anchor=dict(mission=name,map=recorded['world'].rsplit('.',1)[-1],location=recorded['location'],
                        objective=primary['name'],recorded=True,replay_verified=False,
                        checkpoint=recorded['checkpoint']['name'])
        beginning=g['index']==0
        save_supported = ((name == 'Mission_Main_Shatteredlands3' and g['index'] in (28, 32))
                          or str(g['index']) in selection_row.get('sections',{}))
        choices.append(dict(index=g['index'],title='Mission beginning' if beginning else ' / '.join(o['title'] for o in visible),
                            objectives=[o['name'] for o in visible],anchor=anchor,
                            save_backed_supported=save_supported,
                            save_backed_reason=access['reason'] if access and not access['allowed'] else None,
                            beginning=beginning,
                            blocked_reason=reason or coverage_error(name,g['index']) or
                            (None if DATA[name].get('execution_map') else 'Mission opening map is not resolved'),
                            placement='recorded_start' if anchor and anchor.get('recorded') else 'mission_opening' if beginning else 'preceding_completion' if anchor else 'objective_scene'))
    ident=uuid.uuid4().hex
    _preview=dict(id=ident,name=name,token=row['token'] if row else None,world=engine.world_address,
                  binding=m._binding(rows),choices=choices,pid=os.getpid())
    return dict(ok=True,preview_id=ident,mission=name,title=DATA[name]['title'],choices=choices,
                message='Main objectives only; internal steps initialize their section. Recorded starts are experimental. Moves everyone together; character rewards are retained.')

def start(payload):
    global _job,_preview
    m=_progress()
    from .backend_actions import full_progress_conflict
    if full_progress_conflict('mission_practice_start'):
        raise ValueError('Finish or stop the full-progress run before preparing a replay checkpoint')
    if payload.get('acknowledge_shared_progress') is not True:raise ValueError('Allow changes to shared lobby progress')
    if _job and _job['state'] in ('running','uncertain'):raise ValueError('Inspect or stop the existing replay jump')
    if m._job and m._job['state'] in ('running','uncertain'):raise ValueError('Finish or reconcile the existing mission job')
    m.require_clear_journals()
    if not _preview or payload.get('preview_id')!=_preview['id']:raise ValueError('Refresh the selected mission first')
    choice=next((r for r in _preview['choices'] if r['index']==payload.get('checkpoint')),None)
    if choice is None or choice['blocked_reason']:raise ValueError(choice['blocked_reason'] if choice else 'Choose a replay checkpoint')
    from .mission_execution import require_coverage
    require_coverage(_preview['name'], choice['index'])
    engine=m._engine();rows=m._party();row=m._row(engine.snapshot(),_preview['name'])
    if os.getpid()!=_preview['pid'] or engine.world_address!=_preview['world'] or m._binding(rows)!=_preview['binding'] or row['token']!=_preview['token']:
        raise ValueError('Mission or lobby changed; refresh replay choices')
    # Recheck entitlement immediately before travel/reset, including an anchor
    # that belongs to an earlier DLC mission.
    from .mission_dlc import inspect,requirement
    report=inspect(rows)
    for name in {_preview['name'], *([choice['anchor']['mission']] if choice['anchor'] else [])}:
        access=requirement(name,report)
        if access and not access['allowed']:raise ValueError(access['reason'])
    _job=dict(id=uuid.uuid4().hex,state='running',ok=True,phase='checkpoint_unload' if choice['index']>0 else 'prepare',name=_preview['name'],
              checkpoint=choice['index'],anchor=choice['anchor'],selected_objective=choice['objectives'][0],roster=_roster(rows),binding=m._binding(rows),
              token=row['token'],world=engine.world_address,pid=os.getpid(),started=time.time(),progress_at=time.monotonic(),issued=[],teleported=[],events=[],
              message='Preparing the selected replay checkpoint; everyone moves together.')
    from .mission_completion_context import begin
    host=next(r['pc'] for r in rows if r['host'])
    _job.update(completion_path='objective_graph',target=host._path_name(),
                completion_context=begin(rows,host._path_name()))
    _preview=None;_save(dict(event='started'))
    return status()

def status():
    if not _job:return dict(ok=True,state='idle',message='No replay jump is running.')
    return {k:v for k,v in _job.items() if k not in ('events','binding','roster','issued')}

def _teleport(rows):
    if _job['anchor'].get('recorded'):
        from .mission_recorded_placement import start
        start(_job,rows,_save)
        return
    from .mission_practice_placement import start
    start(_job,rows,_save)


def _track(rows,engine,row):
    """Request the chosen mission on the host HUD once; verify shared tracking."""
    if not _job.get('tracking_issued'):
        import unrealsdk
        token=unrealsdk.make_struct('/Script/CoreUObject.SToken',
            Hash=struct.unpack('<i',bytes.fromhex(row['token'])[:4])[0],Name=_job['name'])
        if engine.read(token._get_address(),12).hex()!=row['token']:
            raise RuntimeError('Replay tracking token differs; no tracking request issued')
        host=next(r['pc'] for r in rows if r['host'])
        _job.update(tracking_issued=True,tracking_since=time.monotonic(),state='uncertain',ok=False)
        _save(dict(event='replay_tracking_issued'))
        host.ServerRequestTrackMission(token,int(host.PlayerState.StableIndex))
        _job.update(state='running',ok=True);_save(dict(event='replay_tracking_returned'))
    if row['token'] not in engine.snapshot()['tracked']:
        if time.monotonic()-_job['tracking_since']>10:
            raise RuntimeError('Replay tracking was not confirmed; no request repeated')
        _job['message']='Waiting for the selected mission to appear in tracking.';return False
    return True

def _step():
    m=_progress()
    if _job['pid']!=os.getpid():raise RuntimeError('Game process changed')
    from . import mission_completion_context as context
    owner=_CompletionOwner()
    if not context.observe(owner):return
    w=_world()
    _job['world']=_job['completion_context']['world']
    engine=m._engine();rows=m._party()
    if engine.world_address!=_job['world'] or m._binding(rows)!=_job['binding']:raise RuntimeError('World or players changed during replay preparation')
    if _job['phase']=='placement':
        from .mission_practice_placement import tick
        tick()
        return
    if _job['phase'].startswith('checkpoint_'):
        definition=DATA[_job['name']];row=m._row(engine.snapshot(),_job['name'])
        if row['token']!=_job['token']:raise RuntimeError('Mission identity changed during direct replay setup')
        if _job['phase']=='checkpoint_unload':
            selected=next((o for g in definition['groups'] if g['index']==_job['checkpoint'] for o in g['objectives'] if
                           o['name'].casefold()==_job['selected_objective'].casefold()),None)
            if selected is None:raise RuntimeError('Selected main objective is unavailable; no replay reset issued')
            _job['return_map']=_return_map(definition,selected,_job['checkpoint'],_job['anchor'])
            if not context.prepare_reset(owner,_job['name'],row,definition):return
            _job['phase']='checkpoint_stage';_save(dict(event='checkpoint_area_unloaded'));return
        if _job['phase']=='checkpoint_reopen_wait':
            result=m.poll(_job['mission_job'])
            if result['state']=='running':return
            if result['state']!='completed':raise RuntimeError(result['message'])
            _job.update(phase='checkpoint_stage',checkpoint_runtime_since=time.monotonic())
            _save(dict(event='checkpoint_runtime_initialized'));return
        from .mission_execution import objectives
        selected=next((o for o in objectives(engine,row,definition) if
                       o['name'].casefold()==_job['selected_objective'].casefold()),None)
        if selected is None and _job['phase']=='checkpoint_stage' and not _job.get('mission_job'):
            if m._state(row) not in ('completed','accepted','active'):
                raise RuntimeError('Selected main objective is unavailable; mission initialization requires a started mission')
            _job.update(phase='checkpoint_reopen_wait',state='uncertain',ok=False)
            _save(dict(event='checkpoint_initialize_pending'))
            result=m.start(dict(scope='named',missions=[_job['name']],mode='reopen',reset_completed=True,
                                target_scope='local',acknowledge_shared_progress=True),manage_replay_travel=False)
            if not result.get('id'):raise RuntimeError(result.get('message','Mission initialization failed'))
            _job.update(mission_job=result['id'],state='running',ok=True)
            _save(dict(event='checkpoint_initialize_started'));return
        if selected is None:
            if _job['phase']=='checkpoint_stage' and time.monotonic()-_job.get('checkpoint_runtime_since',0)<10:
                _job['message']='Waiting for normal mission initialization to create the selected objective.';return
            raise RuntimeError('Selected main objective is unavailable; earlier objectives will not be replayed')
        if selected.get('optional'):raise RuntimeError('Selected replay checkpoint must be a required main objective')
        if _job['phase']=='checkpoint_stage':
            _job.update(phase='checkpoint_return',state='uncertain',ok=False)
            _save(dict(event='direct_checkpoint_pending'))
            from .mission_reset import stage_checkpoint
            earlier=[o for o in objectives(engine,row,definition) if o.get('group',_job['checkpoint'])<_job['checkpoint']]
            stage_checkpoint(engine,row,selected,_job['checkpoint'],_save,earlier=earlier)
            _job.update(state='running',ok=True);_save(dict(event='direct_checkpoint_returned'));return
        if _job['phase']=='checkpoint_return':
            destination=_job['return_map']
            station=(_job['anchor'].get('checkpoint') if _job['anchor'] and _job['anchor'].get('recorded') else None)
            if not context.travel_to(owner,_job['name'],row,definition['title'],destination,**({'station':station} if station else {})):return
            _job.update(phase='checkpoint_settle',checkpoint_settle_since=time.monotonic());return
        if m._state(row)!='active' or selected['state']!=4:
            if time.monotonic()-_job['checkpoint_settle_since']>120:
                raise RuntimeError('Selected section did not initialize after reload; no earlier mission progression issued')
            _job['message']='Waiting for the selected main objective to initialize after map reload.';return
        active_before=[o for o in objectives(engine,row,definition) if o['state'] in (4,10,11,12) and o.get('group',_job['checkpoint'])<_job['checkpoint']]
        if active_before:raise RuntimeError('An earlier objective remained active; direct replay stopped instead of progressing the mission')
        if not _track(rows,engine,row):return
        _job['phase']='teleport' if _job['anchor'] else 'replay_scene'
        _save(dict(event='direct_checkpoint_ready'));return
    if _job['phase']=='prepare':
        row=m._row(engine.snapshot(),_job['name']);state=m._state(row)
        definition=DATA[_job['name']]
        if state in ('active','accepted','completed'):
            if not context.prepare_reset(owner,_job['name'],row,definition):return
            _job['token']=row['token']
            _job.update(phase='reopen_wait',state='uncertain',ok=False)
            _save(dict(event='reopen_issued'))
            result=m.start(dict(scope='named',missions=[_job['name']],mode='reopen',reset_completed=True,
                                target_scope='local',acknowledge_shared_progress=True),manage_replay_travel=False)
            _job.update(mission_job=result['id'],state='running',ok=True)
            _save(dict(event='reopen_started'));return
        if state=='available':
            if not context.travel_to(owner,_job['name'],row,definition['title'],definition.get('execution_map')):return
            _job['token']=row['token']
            import unrealsdk
            token=unrealsdk.make_struct('/Script/CoreUObject.SToken',Hash=struct.unpack('<i',bytes.fromhex(row['token'])[:4])[0],Name=_job['name'])
            if engine.read(token._get_address(),12).hex()!=row['token']:raise RuntimeError('Mission token differs')
            host=next(r['pc'] for r in rows if r['host'])
            _job.update(phase='activate_wait',state='uncertain',ok=False);_save(dict(event='accept_issued'))
            host.ServerActivateMission(token,1,True,int(host.PlayerState.StableIndex))
            _job.update(state='running',ok=True);_save(dict(event='accept_returned'));return
        raise RuntimeError('Mission prerequisites became unavailable')
    if _job['phase']=='reopen_wait':
        result=m.poll(_job['mission_job'])
        if result['state']=='running':return
        if result['state']!='completed':raise RuntimeError(result['message'])
        _job['phase']='activate_wait'
    row=m._row(engine.snapshot(),_job['name'])
    if row['token']!=_job['token']:raise RuntimeError('Mission instance changed')
    if _job['phase']=='activate_wait' and not _job.get('objective_run') and not _job['issued']:
        definition=DATA[_job['name']]
        if not context.travel_to(owner,_job['name'],row,definition['title'],definition.get('execution_map')):return
    if m._state(row)=='accepted':
        _job['message']='Waiting for the mission opening actions to activate.';return
    if m._state(row)!='active':raise RuntimeError('Mission is not active at its replay checkpoint')
    if _job['checkpoint']==0 and not _track(rows,engine,row):return
    if _job['phase']=='recorded_verify':
        from .mission_recorded_placement import verify
        if verify(_job,rows):_job['phase']='world_ready'
        return
    if _job['checkpoint']==0 and not (_job['anchor'] and _job['anchor'].get('recorded')):
        _job.update(state='completed',ok=True,message=DATA[_job['name']]['title']+
                    ': mission opening is active. Play the mission again; character rewards are retained.')
        _save(dict(event='completed'))
        return
    if _job['phase']=='world_ready':
        from .mission_practice_world import ready
        if ready(_job,_save):
            _job.update(state='completed',ok=True,message=DATA[_job['name']]['title']+
                        (': selected objective is active at its recorded beginning. Experimental: verify normal gameplay.' if _job['anchor'] and _job['anchor'].get('recorded') else
                         ': selected objective is ready; everyone moved to the preceding completion location.' if _job['anchor'] else
                         ': selected objective is ready. Follow its mission waypoint to play it again.'))
            _save(dict(event='completed'))
        return
    if _job['phase']=='replay_scene':
        from .mission_execution import objectives
        targets=[o for o in objectives(engine,row,DATA[_job['name']]) if o.get('group')==_job['checkpoint'] and
                 o['state']==4 and not o['optional']]
        if not targets:raise RuntimeError('The selected replay objective is no longer active')
        if targets[0].get('travel_map') or targets[0].get('activation_by_arrival'):
            # Going to its completion waypoint would consume an arrival step.
            # Leave the player on the approach side for normal gameplay.
            _job['phase']='world_ready'
            return
        if context.objective_ready(owner,_job['name'],row,DATA[_job['name']],targets[0]):
            _job['phase']='world_ready'
        return
    if _job['phase']=='teleport':
        if not context.travel_to(owner,_job['name'],row,DATA[_job['name']]['title'],_job['anchor']['map'].casefold()):return
        if _job['anchor'].get('recorded'):
            from .mission_execution import objectives
            selected=[o for o in objectives(engine,row,DATA[_job['name']]) if
                      o['name'].casefold()==_job['selected_objective'].casefold() and o['state']==4]
            if len(selected)!=1:raise RuntimeError('Selected main objective is not active after map reload; no placement issued')
        _teleport(rows);return
    if _job['checkpoint']>0:
        raise RuntimeError('Direct checkpoint state is invalid; earlier objectives will not be replayed')
    # The mission opening already used the unload/reset/return protocol above.
    # Its recorded start needs placement only, never prefix outcome traversal.
    _job['phase']='teleport'
    if context.travel_to(owner,_job['name'],row,DATA[_job['name']]['title'],_job['anchor']['map'].casefold()):_teleport(rows)

def _progress_signature():
    ctx=_job.get('completion_context',{})
    return (_job['phase'],len(_job['issued']),len(_job.get('teleported',[])),
            ctx.get('world'),_job.get('objective_run',{}).get('progress_at'))


def step(payload):
    if not _job or payload.get('job_id')!=_job['id']:raise ValueError('Replay jump identifier changed')
    if _job['state']!='running':return status()
    try:
        if time.monotonic()-_job.setdefault('progress_at',time.monotonic())>STALL_TIMEOUT:
            ctx=_job.get('completion_context',{})
            if 'arrival_wait_since' not in ctx:
                raise RuntimeError('Replay preparation stopped making progress; stop and inspect it')
            # Revalidate the live world/party/native arrival before granting a
            # longer wait. observe retains both absolute and settling bounds.
            from .mission_completion_context import observe
            if not observe(_CompletionOwner()):return status()
            _job['progress_at']=time.monotonic()
        # Dialogue completion can release an authored scene's next action.
        # Interrupting its audio is not proof that the scene has completed.
        deadline=time.monotonic()+0.020
        for _ in range(16):
            before=_progress_signature()
            _step()
            after=_progress_signature()
            if before!=after:_job['progress_at']=time.monotonic()
            if _job['state']!='running' or before==after or time.monotonic()>=deadline:break
    except Exception as exc:
        if _job.get('completion_context',{}).get('placement'):
            from .mission_completion_placement import stop
            stop(_CompletionOwner(),str(exc),'stopped')
            return status()
        from .mission_practice_placement import cancel
        if not cancel(str(exc),'stopped'):
            _job.update(state='uncertain' if _job['state']=='uncertain' else 'stopped',ok=False,message=str(exc));_save(dict(event='stopped'))
    return status()

def dispatch(action,payload):
    try:
        if action=='mission_practice_preview':return preview(payload)
        if action=='mission_practice_start':return start(payload)
        if action=='mission_practice_step':return step(payload)
        if action=='mission_practice_cancel':
            if _job and payload.get('job_id')==_job['id'] and _job['state'] in ('running','stopped','uncertain'):
                if _job.get('completion_context',{}).get('placement'):
                    from .mission_completion_placement import stop
                    stop(_CompletionOwner(),retry=True)
                    return status()
                m=_progress()
                if _job.get('mission_job') and m._job and m._job['state']=='running':m.cancel(_job['mission_job'])
                from .mission_practice_placement import cancel,retry_cleanup
                if cancel():return status()
                if retry_cleanup(_job,_save):return status()
                if any(r.get('cleanup_error') or r.get('restore_pending') or r.get('held') for r in _job.get('placement',[])):
                    raise RuntimeError('Player placement cleanup needs inspection before starting another replay jump')
                _job.update(state='cancelled',message='Replay preparation stopped. Applied mission changes remain.');_save(dict(event='cancelled'))
            return status()
        return status()
    except Exception as exc:return dict(ok=False,message=str(exc))
