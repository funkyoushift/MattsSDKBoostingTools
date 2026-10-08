"""Local-only farming experiments. File requests are serviced on the game thread."""
from __future__ import annotations
import importlib
import json
import os
from pathlib import Path
import time
import uuid
import mods_base
import unrealsdk
from mods_base import ButtonOption, CoopSupport, Game, build_mod, command
from . import engine

ROOT = next(p for p in Path(__file__).resolve().parents if p.name.lower() == 'sdk_mods')
DATA = ROOT / 'settings' / 'MSBTFarmingLab'
TICK = '/Script/Engine.CameraModifier:BlueprintModifyCamera'
TRAVEL = ('OakGame.OakPlayerController:ClientTravel', 'Engine.PlayerController:ClientTravel')
HOOK = 'MSBTFarmingLab'
session = ''
enabled = False
last_poll = 0.0
last_heartbeat = 0.0
hooks = []

def write(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=True, allow_nan=False), encoding='utf-8')
    os.replace(temp, path)

def status():
    return dict(session=session, pid=os.getpid(), enabled=enabled, heartbeat=time.time(), **engine.status())

def dispatch(r):
    op = r.get('op')
    if op == 'status': return status()
    if op == 'probe': return engine.probe(r)
    if op == 'set': return engine.set_feature(r['feature'], r['enabled'])
    if op == 'off': return engine.off()
    if op == 'reload':
        result = engine.off()
        if not result['ok']: return result
        importlib.invalidate_caches()
        importlib.reload(engine)
        return status()
    raise ValueError('Unknown local lab operation')

def pump(*_):
    global last_poll, last_heartbeat
    now = time.monotonic()
    if not enabled or now-last_poll < .1: return
    last_poll = now
    try:
        engine.tick()
        if now-last_heartbeat > 1:
            write(DATA/'status.json', status()); last_heartbeat = now
        path = next((DATA/'requests').glob('*.json'), None)
        if path is None: return
        claim = path.with_suffix('.processing'); os.replace(path, claim)
        response = dict(id=path.stem, session=session, time=time.time())
        try:
            if claim.stat().st_size > 65536: raise ValueError('Request too large')
            r = json.loads(claim.read_text(encoding='utf-8'))
            if r.get('session') != session or float(r.get('expires', 0)) <= time.time():
                raise ValueError('Stale or expired request')
            result = dispatch(r)
            if len(json.dumps(result)) > 250000: raise ValueError('Result too large')
            response.update(ok=True, result=result)
        except Exception as exc:
            import traceback
            response.update(ok=False, error=str(exc), traceback=traceback.format_exc()[-6000:])
        write(DATA/'responses'/path.name, response)
        claim.unlink()
        write(DATA/'status.json', status())
        with (DATA/'history.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(response)+'\n')
    except Exception as exc:
        unrealsdk.logging.error('[Farming Lab] '+str(exc))

def before_travel(*_):
    result = engine.off()
    if not result['ok']: unrealsdk.logging.error('[Farming Lab] '+str(result))

def on_enable():
    global enabled, session
    if enabled: return
    for p in (DATA, DATA/'requests', DATA/'responses'): p.mkdir(parents=True, exist_ok=True)
    session = uuid.uuid4().hex
    for path in TRAVEL:
        try:
            unrealsdk.hooks.add_hook(path, unrealsdk.hooks.Type.PRE, HOOK+'.travel', before_travel)
            if unrealsdk.hooks.has_hook(path, unrealsdk.hooks.Type.PRE, HOOK+'.travel'): hooks.append(path)
        except Exception: pass
    if not hooks: raise RuntimeError('Travel cleanup unavailable')
    unrealsdk.hooks.add_hook(TICK, unrealsdk.hooks.Type.POST, HOOK+'.pump', pump)
    if not unrealsdk.hooks.has_hook(TICK, unrealsdk.hooks.Type.POST, HOOK+'.pump'):
        raise RuntimeError('Lab game-thread tick unavailable')
    enabled = True
    engine.install_integration()
    write(DATA/'status.json', status())

def on_disable():
    global enabled
    result = engine.off()
    if not result['ok']: raise RuntimeError(str(result))
    engine.uninstall_integration()
    enabled = False
    for path in hooks: unrealsdk.hooks.remove_hook(path, unrealsdk.hooks.Type.PRE, HOOK+'.travel')
    hooks.clear()
    unrealsdk.hooks.remove_hook(TICK, unrealsdk.hooks.Type.POST, HOOK+'.pump')
    write(DATA/'status.json', status())

@command('msbt_farm', description='Local farming lab: status or off')
def farm(args):
    result = engine.off() if args.mode == 'off' else status()
    unrealsdk.logging.info('[Farming Lab] '+json.dumps(result))
farm.add_argument('mode', choices=('status', 'off'), nargs='?', default='status')

mod = build_mod(name='MSBT Farming Lab (local test)', version='local-test', author='Matt / MSBT',
    supported_games=Game.BL4, coop_support=CoopSupport.Unknown,
    description='Local farming experiments. All boosts start OFF and turn OFF on travel.',
    commands=[farm], on_enable=on_enable, on_disable=on_disable,
    options=[ButtonOption('Turn All Tests Off', on_press=lambda _: engine.off())])
