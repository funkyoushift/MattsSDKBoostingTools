"""Actual dispatch/authorization/guard with isolated unlock storage and no game."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import pytest

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def delivery(tmp_path,monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    spec=importlib.util.spec_from_file_location('shiny_unlock',ROOT/'install_authorization.py')
    auth=importlib.util.module_from_spec(spec);spec.loader.exec_module(auth)
    source=(ROOT/'backend_actions.py').read_text(encoding='utf-8')
    names={'deliver_shinies','_deliver_serials_with_target','_serial_delivery_count_note','run_quick_menu_action'}
    nodes=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name in names]
    queued=[];converted=[]
    serials=['@U'+str(n) for n in range(127)]
    def enqueue(values,indices,**kwargs):
        queued.append((list(values),indices,kwargs));return {}
    rewards=NS(_resolve_give_serial_strings=lambda values:converted.append(list(values)) or values,
               _do_give_serial_to_player_indices=enqueue,
               _do_give_serial_to_selected_player=lambda values,**kw:enqueue(values,[1],**kw))
    env=dict(Any=object,_installation_authorized=auth.authorized,
             get_selected_player_index=lambda:1,get_selected_player_name=lambda:'Guest',
             _load_shiny_serials=lambda:serials,serial_rewards=rewards,
             _players=lambda:[(0,'Host'),(1,'Guest')],_non_host_party_player_indices=lambda:[1],
             note_last_command=lambda *a,**kw:None,_canonical_action_key=lambda key:key,
             full_progress_conflict=lambda key:False,sys=NS(modules={}))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<shiny-password>','exec'),env)
    return env,auth,queued,converted,serials


@pytest.mark.parametrize('action',['shiny_selected','shiny_all','shiny_nonhost',
                                   'deliver_shinies_selected','deliver_shinies_all','deliver_shinies_nonhost'])
def test_correct_password_unlocks_all_shared_action_routes(delivery,action):
    env,auth,queued,converted,serials=delivery
    run=env['run_quick_menu_action']
    for value in (None,'wrong',True):
        result=run(action,{'bulk_loot_password':value})
        assert result['password_required'] and not queued and not converted
    result=run(action,{'bulk_loot_password':'funkyou'})
    assert result['ok'],result
    assert len(queued)==1 and queued[0][0]==serials
    assert queued[0][2]['bulk_authorized'] is True
    assert 'funkyou' not in auth._path().read_text()
    assert run(action,{})['ok'] and len(queued)==2
    assert 'bulk_loot_password' not in queued[0][2]


@pytest.mark.parametrize('action,mode',[('shiny_selected','selected'),('shiny_all','all'),('shiny_nonhost','nonhost')])
@pytest.mark.parametrize('assignable',[False,True])
def test_http_handler_forwards_password_to_same_guard(delivery,action,mode,assignable):
    env,auth,queued,_,_=delivery
    tree=ast.parse((ROOT/'external_bridge.py').read_text(encoding='utf-8'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_handle_action','_normalize_quick_menu_bridge_payload')]
    bridge=dict(Any=object,quick_menu_registry=NS(ASSIGNABLE_ACTIONS=[action] if assignable else []),
                backend_actions=NS(deliver_shinies=env['deliver_shinies'],run_quick_menu_action=env['run_quick_menu_action'],full_progress_conflict=lambda _:False))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<bridge-shinies>','exec'),bridge)
    handle=bridge['_handle_action']
    assert handle(action,{})['password_required'] and not queued
    assert handle(action,{'bulk_loot_password':'funkyou'})['ok']
    assert auth.authorized() and len(queued)==1


def test_resolved_count_still_enforces_guard_when_small_input_expands(delivery):
    env,_,queued,converted,serials=delivery
    env['_load_shiny_serials']=lambda:serials[:1]
    env['serial_rewards']._resolve_give_serial_strings=lambda values:serials
    assert env['deliver_shinies']()['password_required'] and not queued
