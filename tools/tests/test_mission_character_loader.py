"""Selector navigation is bounded, journaled and stops before commit retries."""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType,SimpleNamespace as N
import pytest

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'

@pytest.fixture
def loader(monkeypatch):
    pkg=ModuleType('picker_test');pkg.__path__=[str(ROOT)]
    monkeypatch.setitem(sys.modules,pkg.__name__,pkg)
    spec=importlib.util.spec_from_file_location(pkg.__name__+'.mission_character_loader',ROOT/'mission_character_loader.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    state=dict(now=1.,index=0,guid='original',calls=[],receipts=[])
    m.time=N(monotonic=lambda:state['now'])
    m._collector=lambda *_:(N(),['original-slot','holding-slot','another-slot'][state['index']])
    def input_action(pc,engine,action):
        state['calls'].append(action)
        if action=='down':state['index']=(state['index']+1)%3
        if action=='up':state['index']=(state['index']-1)%3
        if action=='select':state['guid']='original' if state['index']==0 else 'holding'
    m.pulse=input_action
    monkeypatch.setitem(sys.modules,pkg.__name__+'.camera_tick',N(register=lambda *a,**k:None,set_needed=lambda *a:None))
    monkeypatch.setitem(sys.modules,pkg.__name__+'.mission_save_replay',N(_host=lambda:(N(),N(),state['guid'],'world')))
    lease=dict(original_guid='original',holding_guid='holding',closed=False)
    return m,state,lease


def test_other_and_original_are_selected_using_observed_focus(loader):
    m,s,lease=loader
    m.start(lease,'other',0,lambda:None);m._tick();s['now']+=.2;m._tick()
    assert s['calls']==['down','select'] and s['guid']=='holding' and m._task is None
    assert lease['loader']['0_other']['commit']=='returned'
    m.start(lease,'original',0,lambda:None);m._tick();s['now']+=.2;m._tick()
    assert s['calls']==['down','select','up','select'] and s['guid']=='original'
    assert lease['loader']['0_original']['commit']=='returned'


def test_failed_navigation_is_not_repeated(loader):
    m,s,lease=loader
    m.pulse=lambda *a:s['calls'].append(a[-1])
    m.start(lease,'other',0,lambda:None);m._tick();s['now']+=3.5;m._tick();m._tick()
    assert s['calls']==['down'] and m._task is None
    assert 'did not respond' in lease['loader']['0_other']['error']


def test_unknown_commit_is_journaled_and_never_retried(loader):
    m,s,lease=loader
    def fail(*args):s['calls'].append(args[-1]);raise RuntimeError('uncertain input result')
    lease['original_picker_focus']='original-slot';s['index']=1
    m.pulse=fail;m.start(lease,'other',0,lambda:None);m._tick();m._tick()
    assert s['calls']==['select']
    assert lease['loader']['0_other']['commit']=='issued' and m._task is None


def test_character_change_or_stop_blocks_inputs(loader):
    m,s,lease=loader
    m.start(lease,'other',0,lambda:None);s['guid']='unexpected';m._tick()
    assert not s['calls'] and 'changed' in lease['loader']['0_other']['error']
    s['guid']='original';m.start(lease,'other',1,lambda:None);m.stop();m._tick()
    assert not s['calls']


def test_diagnostic_does_not_advertise_unverified_automation(loader):
    m,s,lease=loader
    m._collector=lambda *_:(N(_get_address=lambda:200),'original-slot')
    pc=N(_get_address=lambda:100);engine=N(profile='test',u64=lambda *_:0,read=lambda *a:bytes(a[-1]))
    result=m.inspect(pc,engine)
    assert result['manual_input_required'] is True
    assert result['automatic_selection_verified'] is False
    assert result['focus_available'] is True
    m._collector=lambda *_:(N(_get_address=lambda:200),None)
    assert m.inspect(pc,engine)['focus_available'] is False


def test_direct_select_uses_native_slot_token_and_return_to_game(loader,monkeypatch):
    m,s,lease=loader
    calls=[]
    monkeypatch.setitem(sys.modules,'unrealsdk',N(make_struct=lambda path,**kw:N(_get_address=lambda:100)))
    m._collector=lambda *_:(N(_get_address=lambda:200),None)
    m._direct_function=lambda *args:lambda *values:calls.append((args[1],values))
    result=m.select_slot(N(),N(read=lambda *args:(123).to_bytes(8,'little')),'17')
    assert calls==[('select_slot',(200,123,1))]
    assert result['selection_requested'] and not result['verified']


def test_invalid_direct_slot_never_reaches_native_call(loader):
    m,s,lease=loader
    m._direct_function=lambda *args:pytest.fail('Invalid slot issued native call')
    for slot in ('../17','17.sav','',None):
        with pytest.raises(ValueError):m.select_slot(N(),N(),slot)
