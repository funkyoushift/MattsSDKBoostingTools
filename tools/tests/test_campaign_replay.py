"""Travel sequencing and failure recovery for the campaign replay reset."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import pytest


@pytest.fixture
def rig(monkeypatch):
    root = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools'
    pkg = NS()
    monkeypatch.setitem(sys.modules, 'replay_test', pkg)
    spec = importlib.util.spec_from_file_location('replay_test.campaign_replay', root / 'campaign_replay.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    current = [NS(_path_name=lambda: module.WORLD, _get_address=lambda: 1)]
    monkeypatch.setattr(module, 'world', lambda: current[0])
    pc = NS(Pawn=object(), _path_name=lambda: current[0]._path_name() + ':PC', PlayerState=NS(StableIndex=0))
    party = [dict(label='Host', state=NS(PlayerId=0), host=True, pc=pc)]
    states = {module.FIRST:'completed', 'activity':'completed', 'later':'completed'}
    def snapshot():
        return dict(missions=[dict(source_identity=dict(name=n), status_fact=dict(known_status=s), token='01'*12) for n,s in states.items()])
    engine = NS(snapshot=snapshot, world_address=1, ensure_world=lambda: None)
    calls=[]; events=[]
    def reset(engine, rows, journal):
        calls.append([r['source_identity']['name'] for r in rows])
        for r in rows:states[r['source_identity']['name']]='None'
    travels=[]
    pkg.mission_reset=NS(reset_campaign=reset)
    pkg.travel=NS(travel_to_station=travels.append)
    job=dict(phase='prepare', names=list(states), binding=['host'], state='running', index=0)
    owner=NS(_job=job, _runtime=engine, _engine=lambda: engine, _party=lambda:party,
             _binding=lambda rows:['host'], _journal=events.append,
             _row=lambda snap,n:next(r for r in snap['missions'] if r['source_identity']['name']==n),
             _state=lambda r:r['status_fact']['known_status'], CATALOG={'later':dict(category='story')},
             status=lambda:dict(job))
    monkeypatch.setitem(sys.modules,'mods_base',NS(get_pc=lambda:pc))
    return NS(m=module, owner=owner, current=current, states=states, calls=calls, events=events, travels=travels, party=party)


def test_residue_reset_after_unload_and_no_completed_work_repeated(rig):
    r=rig; m=r.m
    m.step(r.owner)
    assert r.calls==[[m.FIRST,'activity','later']]
    m.step(r.owner)
    assert r.travels==['Intro_P.Respawn']
    m.step(r.owner)  # Still on original map: no reset or travel repeated.
    assert len(r.calls)==1 and len(r.travels)==1
    r.current[0]=NS(_path_name=lambda:m.INTRO,_get_address=lambda:2)
    r.states.update({m.FIRST:'active','activity':'completed'})
    m.step(r.owner)
    assert r.calls[-1]==['activity']
    m.step(r.owner)
    assert r.owner._job['state']=='completed'
    assert r.states[m.FIRST]=='active' and r.states['later']=='None'


def test_existing_intro_is_unloaded_before_reset(rig):
    r=rig; r.current[0]=NS(_path_name=lambda:r.m.INTRO,_get_address=lambda:4)
    r.m.step(r.owner)
    assert r.travels==['World_P.Game_Start'] and not r.calls


def test_changed_roster_stops_travel_rebinding(rig):
    r=rig; r.m.step(r.owner);r.m.step(r.owner)
    r.current[0]=NS(_path_name=lambda:r.m.INTRO,_get_address=lambda:2)
    r.party[0]['label']='Different player'
    with pytest.raises(RuntimeError,match='Players changed'):
        r.m.step(r.owner)
    assert len(r.calls)==1


def test_unknown_reset_return_cannot_be_repeated_by_recovery(rig):
    r=rig
    with pytest.raises(ValueError,match='no return receipt'):
        r.m.recover(r.owner,dict(mode='continue',acknowledge_shared_progress=True),
                    [dict(event='campaign_reset_issued')],True,None)
    assert not r.calls


def test_interrupted_campaign_can_be_closed_without_game_calls(rig, tmp_path):
    r=rig; path=tmp_path/'job.jsonl';path.write_text('')
    result=r.m.recover(r.owner,dict(mode='close',job_id='a'*32,acknowledge_shared_progress=True),
                       [dict(event='campaign_reset_issued')],False,path)
    assert result['closed'] and not r.calls and not r.travels
    assert '"state": "stopped"' in path.read_text()
