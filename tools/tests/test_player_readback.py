import importlib.util
from pathlib import Path
from types import SimpleNamespace as S
spec=importlib.util.spec_from_file_location('readback',Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools/player_readback.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_readback_preserves_inactive_keys_and_missing_values():
    ps=S(ExperienceState=[S(token='Character',bIsUnlocked=True),S(token='VaultCard01_Experience',bIsUnlocked=False)],BP_GetExperienceLevel=lambda t:70 if t=='Character' else 112)
    pc=S(PlayerState=ps,CurrencyManager=S(currencies=[S(type=S(Name='VaultCard01_Tokens'),Amount=2147483647),S(type=S(Name='Cash'),Amount=0)]))
    economy=S(_experience_state_token_name=lambda r:r.token,_make_experience_def_ptr=lambda t:t)
    d=m.read_player(pc,'Guest',lambda p:'Guest',economy)
    assert d['level']==70 and d['specialization'] is None
    assert d['currencies']=={'VaultCard01_Tokens':2147483647,'Cash':0}
    assert d['vault_cards']==[{'card':1,'rank':112,'active':False}]
    assert not m.read_player(pc,'Departed',lambda p:'Guest',economy)['available']
def test_absent_target_is_unavailable():
    assert not m.read_player(None,'',None,None)['available']
