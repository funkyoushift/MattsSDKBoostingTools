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
    with path.open('w', encoding='utf-8') as stream:
        json.dump(_last,stream,ensure_ascii=False,indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def complete(payload):
    global _last
    m = _progress()
    if payload.get('acknowledge_shared_progress') is not True:
        raise ValueError('Acknowledge shared host and party progress')
    if m._job and m._job['state'] in ('running','uncertain'):
        raise ValueError('Finish or reconcile the existing mission job first')
    if not _preview or _preview['id']!=payload.get('preview_id') or _preview['consumed']:
        raise ValueError('Refresh objectives before advancing another step')
    if _last and _last['state'] in ('uncertain', 'running'):
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
    expected='4157415641545657534883ec3889d3488b054ae090084831e04889442430488b'
    if engine.read(engine.base+0x3df18e0,32).hex()!=expected:
        raise RuntimeError('Objective outcome handler differs from the tested build')
    _preview['consumed']=True
    _last=dict(id=uuid.uuid4().hex, time=time.time(), state='uncertain',
               mission=_preview['name'], token=row['token'], objective=selected,
               pid=os.getpid(),world=engine.world_address,binding=_preview['binding'],
               before=objectives)
    _save()
    C.WINFUNCTYPE(None,C.c_void_p,C.c_uint8)(engine.base+0x3df18e0)(int(selected['pointer'],16),1)
    _last['returned']=True
    _save()
    return status()


def status():
    if not _last:
        return dict(ok=True,state='idle',message='No objective has been advanced in this session.')
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
        active = [o for o in after if o['state'] == 4 and not o['hidden']]
        confirmed = (m._state(row) == 'active' and selected is not None and
                     selected['state'] not in (10, 11, 12, 13) and bool(active))
        if confirmed:
            _last.update(state='replayed', after=after)
            _save()
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
    finishing=selected and selected['state'] in (10,11,12)
    if confirmed:
        _last.update(state='completed',after=after,mission_state=m._state(row))
        _save()
    elif finishing:
        _last.update(state='running',after=after)
        _save()
    return dict(ok=bool(confirmed),state=_last['state'],id=_last['id'],
                mission=_last['mission'], restart_supported=not _last['mission'].startswith('bounty:'),
                replay_supported=bool(confirmed) and m._state(row)=='active' and not _last['mission'].startswith('bounty:'),
                message=('Objective advanced; mission is '+str(m._state(row))+'.') if confirmed
                else 'Objective is finishing its authored actions. Refresh objective status; no completion call repeated.' if finishing
                else 'Objective call issued once; result not yet confirmed. Refresh objective status; no retry issued.')


def replay_last(payload):
    """Use the native objective checkpoint rewind, including authored reset actions.

    Recovered 89068f2 -> 89069ca -> objective teardown/reset actions, saved
    counters/end-state reset, group rewind, and normal objective activation.
    This intentionally preserves character rewards and progression outside the
    mission. A completed mission must be reopened through the mission action.
    """
    global _last, _preview
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
    _save()
    from .mission_effects import reset_interactions
    def journal(event):
        _last.setdefault('interaction_events', []).append(event)
        _save()
    reset_interactions(_last['mission'], journal, selected['name'])
    C.WINFUNCTYPE(None, C.c_void_p, C.c_void_p)(engine.base + 0x89068f2)(record, objective)
    _last['returned'] = True
    _save()
    return status()
