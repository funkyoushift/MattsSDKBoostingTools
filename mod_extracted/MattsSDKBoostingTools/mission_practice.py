"""Lobby-wide replay jumps using authored preceding completion anchors."""
import json
import os
import struct
import time
import uuid
from importlib.resources import files
from pathlib import Path

DATA = json.loads(files(__package__).joinpath('mission_practice_catalog.json').read_text(encoding='utf-8'))['missions']
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
    name=names[0];row=m._row(snapshot,name);state=m._state(row)
    from .mission_dlc import inspect,requirement
    rows=m._party();access=requirement(name,inspect(rows))
    reason=(access['reason'] if access and not access['allowed'] else
            'Mission prerequisites are not available' if state not in ('active','accepted','completed','available') else None)
    choices=[]
    from .mission_execution import coverage_error
    for g in DATA[name]['groups']:
        visible=[o for o in g['objectives'] if not o['hidden'] and not o.get('optional')]
        if not visible:continue
        anchor=g['start_anchor']
        beginning=g['index']==0
        choices.append(dict(index=g['index'],title='Mission beginning' if beginning else ' / '.join(o['title'] for o in visible),
                            objectives=[o['name'] for o in visible],anchor=anchor,
                            beginning=beginning,
                            blocked_reason=reason or coverage_error(name,g['index']) or
                            (None if DATA[name].get('execution_map') else 'Mission opening map is not resolved'),
                            placement='mission_opening' if beginning else 'preceding_completion' if anchor else 'objective_scene'))
    ident=uuid.uuid4().hex
    _preview=dict(id=ident,name=name,token=row['token'],world=engine.world_address,
                  binding=m._binding(rows),choices=choices,pid=os.getpid())
    return dict(ok=True,preview_id=ident,mission=name,title=DATA[name]['title'],choices=choices,
                message='Moves everyone together. Start points use preceding completion locations. Character rewards are retained.')

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
    _job=dict(id=uuid.uuid4().hex,state='running',ok=True,phase='prepare',name=_preview['name'],
              checkpoint=choice['index'],anchor=choice['anchor'],roster=_roster(rows),binding=m._binding(rows),
              world=engine.world_address,pid=os.getpid(),started=time.time(),progress_at=time.monotonic(),issued=[],teleported=[],events=[],
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
    from .mission_practice_placement import start
    start(_job,rows,_save)

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
    if _job['checkpoint']==0:
        _job.update(state='completed',ok=True,message=DATA[_job['name']]['title']+
                    ': mission opening is active. Play the mission again; character rewards are retained.')
        _save(dict(event='completed'))
        return
    if _job['phase']=='world_ready':
        from .mission_practice_world import ready
        if ready(_job,_save):
            _job.update(state='completed',ok=True,message=DATA[_job['name']]['title']+
                        (': selected objective is ready; everyone moved to the preceding completion location.' if _job['anchor'] else
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
        _teleport(rows);return
    from .mission_execution import advance
    receipt=_job.setdefault('objective_run',dict(issued=_job['issued']))
    _job.setdefault('objective_runs',{})[_job['name']]=receipt
    def journal(event):
        _job.update(state='uncertain' if event['event']=='issued' else 'running',
                    ok=event['event']!='issued')
        _save(event)
    result=advance(engine,row,_job['name'],receipt,journal,
                   checkpoint=_job['checkpoint'],definition=DATA[_job['name']],current_map=_map(w),
                   before_outcome=lambda objective:context.objective_ready(owner,_job['name'],row,DATA[_job['name']],objective))
    if result['ready']:
        if _job['anchor'] is None:
            _job['phase']='replay_scene'
            _job['message']='Selected objective is active; preparing its authored scene for gameplay.'
            return
        _job['phase']='teleport'
        if context.travel_to(owner,_job['name'],row,DATA[_job['name']]['title'],_job['anchor']['map'].casefold()):_teleport(rows)
        return
    _job['message']=result['message']

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
