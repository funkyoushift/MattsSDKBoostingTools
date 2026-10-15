"""Actual Game/Lobby adapters must verify the full sequence for each guest."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
from test_afk_lobby import module,FakeGame,row,ticks


def test_each_guest_gets_every_private_step_and_native_verification(monkeypatch):
    path=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools/uvhm_progression.py'
    spec=importlib.util.spec_from_file_location('afk_private_native_steps',path)
    native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    sent={'a':[],'b':[]};complete={'a':set(),'b':set()};clock=[100.]
    monkeypatch.setattr(module.time,'monotonic',lambda:clock[0])
    monkeypatch.setattr(native,'_complete',lambda pc,name:name in complete[pc.label])
    def player(name,index):
        def grant(challenge,amount):
            sent[name].append((challenge,amount));complete[name].add(challenge)
        return NS(label=name,Pawn=object(),PlayerState=NS(_get_address=lambda:index+100),
                  HasAuthority=lambda:True,_get_address=lambda:index,
                  _path_name=lambda:'world:'+name,ServerIncrementChallengeForPlayer=grant)
    game=FakeGame();adapter=module.Game()
    adapter.backend=lambda:NS(uvh_boost_status=lambda:{'active':False},UVH_RANKS=[1,7],
        _uvh_build_plan=lambda _: [('UVH 1','first',.3),('UVH 7','final',.3)],
        _uvh_native_step=native.advance)
    original=game.step
    game.step=lambda step,job,config:adapter.step(step,job,config) if step=='uvhm' else original(step,job,config)
    game.rows=[dict(row(name,index),pc=player(name,index)) for index,name in enumerate(('a','b'),1)]
    lobby=module.Lobby(game);lobby.start({'uvhm':True})
    for _ in range(60):clock[0]+=1;ticks(lobby,1)
    assert sent=={'a':[('first',1),('final',1)],'b':[('first',1),('final',1)]}
    assert not any(entry['step']=='uvhm' for entry in lobby.shared_completed)
    assert len(lobby.history)==2
    for record in lobby.history:
        result=next(r for r in record['results'] if r['step']=='uvhm')
        assert result['native_completion_verified'] and not result['saved_progress_verified']
