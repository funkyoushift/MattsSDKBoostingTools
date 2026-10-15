"""Standalone package/transport checks; fake game, real bundled runtime and saves."""
import copy
import importlib
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import types
import urllib.error
import urllib.request
import zipfile

import pytest

ROOT=Path(__file__).parents[2]
ARTIFACT=ROOT/'output/standalone-mission-selector/BL4MissionSelector.sdkmod'
pytestmark=pytest.mark.skipif(not ARTIFACT.exists(),reason='Build the local standalone SDK first')


@pytest.fixture
def packaged(tmp_path,monkeypatch):
    sdk=types.ModuleType('mods_base');sdk.SETTINGS_DIR=tmp_path/'settings';sdk.SETTINGS_DIR.mkdir()
    def command(*_a,**_kw):
        def decorate(fn):fn.add_argument=lambda *_a,**_kw:None;return fn
        return decorate
    sdk.command=command;sdk.build_mod=lambda **kw:types.SimpleNamespace(is_enabled=True,**kw)
    sdk.ButtonOption=lambda identifier,**kw:types.SimpleNamespace(identifier=identifier,**kw)
    sdk.Game=types.SimpleNamespace(BL4=4);sdk.CoopSupport=types.SimpleNamespace(Unknown=0)
    sdk.ENGINE=types.SimpleNamespace();sdk.get_pc=lambda **_kw:None
    sdk.get_ordered_mod_list=lambda:[]
    unrealsdk=types.ModuleType('unrealsdk');unrealsdk.logging=types.SimpleNamespace(info=lambda *_:None)
    unrealsdk.find_class=lambda *_a,**_kw:None
    monkeypatch.setitem(sys.modules,'mods_base',sdk);monkeypatch.setitem(sys.modules,'unrealsdk',unrealsdk)
    monkeypatch.syspath_prepend(str(ARTIFACT))
    for name in list(sys.modules):
        if name=='BL4MissionSelector' or name.startswith('BL4MissionSelector.'):monkeypatch.delitem(sys.modules,name)
    console=importlib.import_module('BL4MissionSelector.console')
    yield console
    for name in list(sys.modules):
        if name=='BL4MissionSelector' or name.startswith('BL4MissionSelector.'):sys.modules.pop(name,None)


@pytest.fixture
def menu_ui(packaged, monkeypatch):
    stack=[];output=[]
    parent=types.ModuleType('console_mod_menu');parent.__path__=[]
    screens=types.ModuleType('console_mod_menu.screens')
    drawing=types.ModuleType('console_mod_menu.draw');drawing.draw=output.append
    class AbstractScreen:
        def __init__(self,name):self.name=name
    def standard(line):
        if line.lower() in ('q','quit'):
            stack.clear();return True
        if line.lower() in ('b','back'):
            if stack:stack.pop()
            return True
        return line=='?'
    screens.AbstractScreen=AbstractScreen;screens.screen_stack=stack
    screens.draw_stack_header=lambda:None;screens.draw_standard_commands=lambda:None
    screens.handle_standard_command_input=standard
    screens.pop_screen=stack.pop;screens.push_screen=stack.append
    screens.quit_interactive_menu=stack.clear
    for name,module in [('console_mod_menu',parent),('console_mod_menu.screens',screens),('console_mod_menu.draw',drawing)]:
        monkeypatch.setitem(sys.modules,name,module)
    menu=importlib.import_module('BL4MissionSelector.menu')
    return packaged,menu,stack,output


def test_menu_selects_a_main_objective_through_existing_replay_route(menu_ui,monkeypatch):
    c,menu,stack,output=menu_ui;calls=[]
    monkeypatch.setattr(c,'submit',lambda action,payload:calls.append((action,payload)))
    entry=importlib.import_module('BL4MissionSelector')
    assert entry.mod.options[0].display_name=='Mission replay'
    entry.mod.options[0].on_press(entry.mod.options[0])
    assert stack[-1].name=='Mission replay'
    assert stack[-1].handle_input('1')
    assert stack[-1].name=='Main story'
    assert stack[-1].handle_input('3')
    assert stack[-1].name=='Down and Outbound'
    assert stack[-1].handle_input('2')
    assert not calls
    assert stack[-1].name=='Go to the Order Surveillance Center'
    assert stack[-1].handle_input('1')
    assert not stack
    assert calls==[('start',dict(mission='Mission_Main_Grasslands1',checkpoint=5,automatic=True,acknowledge_shared_progress=True,fog_mode='leave'))]


def test_menu_pagination_rejects_zero_negative_and_off_page_choices(menu_ui):
    _,menu,_,output=menu_ui;selected=[]
    page=menu.Page('Test',[(str(i),lambda i=i:selected.append(i)) for i in range(1,22)])
    page.draw();assert '[10] 10' in output and '[11] 11' not in output
    for bad in ('0','-1','11','100','wrong','p'):assert not page.handle_input(bad)
    assert not selected
    assert page.handle_input('n') and page.handle_input('p')
    assert page.handle_input('n') and page.handle_input('n')
    assert not page.handle_input('n') and not page.handle_input('20')
    assert page.handle_input('21') and selected==[21]


def test_menu_bookmarks_use_selected_id_and_fog_with_confirmation(menu_ui,monkeypatch):
    c,menu,stack,_=menu_ui;calls=[]
    monkeypatch.setattr(c,'submit',lambda action,payload:calls.append((action,payload)))
    menu.open_menu();assert stack[-1].handle_input('7')
    assert stack[-1].handle_input('2') and menu._fog=='clear'
    assert stack[-1].handle_input('5') and stack[-1].handle_input('2')
    menu.on_worker_result({'bookmarks':[dict(id='a'*32,name='First',mission='One'),dict(id='b'*32,name='Second',mission='Two')]})
    assert stack[-1].handle_input('0') is False
    assert stack[-1].handle_input('2')
    assert calls==[('bookmark_list',{})]
    assert stack[-1].handle_input('1')
    action,payload=calls[-1]
    assert action=='bookmark_start' and payload['id']=='b'*32 and payload['fog_mode']=='clear'
    assert not stack


def test_menu_bookmark_name_and_disabled_mod_guard(menu_ui,monkeypatch):
    c,menu,stack,_=menu_ui;calls=[]
    monkeypatch.setattr(c,'submit',lambda action,payload:calls.append((action,payload)))
    menu.open_menu();assert stack[-1].handle_input('5') and stack[-1].handle_input('1')
    assert not stack[-1].handle_input('') and not stack[-1].handle_input('x'*81)
    assert stack[-1].handle_input('Before the boss')
    assert calls[-1][0]=='bookmark_save' and calls[-1][1]['name']=='Before the boss'
    entry=importlib.import_module('BL4MissionSelector');entry.mod.is_enabled=False
    calls.clear();menu.open_menu();assert not stack and not calls


def test_replay_hud_is_restored_once_after_map_change_without_touching_progress(packaged):
    tracking=importlib.import_module('BL4MissionSelector.tracking')
    follow=tracking.Selection('Mission_Test','original',1);requests=[]
    follow.update('original',2,True,False,lambda:requests.append('track'),0)
    assert requests==['track'] and not follow.released
    follow.update('original',2,True,False,lambda:requests.append('duplicate'),1)
    follow.update('original',2,True,True,lambda:requests.append('duplicate'),2)
    assert requests==['track']
    follow.update('original',2,True,False,lambda:requests.append('override user'),6)
    assert follow.released and requests==['track']


@pytest.mark.parametrize('guid,active',[('other',True),('original',False)])
def test_replay_hud_stops_on_character_change_or_mission_completion(packaged,guid,active):
    tracking=importlib.import_module('BL4MissionSelector.tracking')
    follow=tracking.Selection('Mission_Test','original',1);requests=[]
    follow.update(guid,2,active,False,lambda:requests.append('track'),0)
    assert follow.released and not requests


def test_replay_hud_does_not_repeat_an_uncertain_tracking_request(packaged):
    tracking=importlib.import_module('BL4MissionSelector.tracking')
    follow=tracking.Selection('Mission_Test','original',1);requests=[]
    def lost():requests.append('track');raise RuntimeError('return lost')
    with pytest.raises(RuntimeError):follow.update('original',2,True,False,lost,0)
    follow.update('original',2,True,False,lost,10)
    assert follow.released and requests==['track']


def test_hud_helper_failure_does_not_block_worker_requests(packaged,monkeypatch):
    c=packaged;tracking=importlib.import_module('BL4MissionSelector.tracking')
    requests=[];messages=[]
    def broken():raise AttributeError('world wrapper expired')
    monkeypatch.setattr(tracking,'tick',broken)
    monkeypatch.setattr(c,'log',messages.append)
    monkeypatch.setattr(c,'native_action',lambda action,payload:requests.append(action) or {'ok':True})
    ticket=dict(action='mission_save_replay_status',payload={},lock=threading.Lock(),cancelled=False,started=False,done=threading.Event())
    c._pending.put(ticket);c._tick()
    assert ticket['done'].is_set() and ticket['result']=={'ok':True}
    assert requests==['mission_save_replay_status'] and 'world wrapper expired' in messages[0]


def test_hud_arm_failure_preserves_successful_native_tracking(packaged,monkeypatch):
    c=packaged;tracking=importlib.import_module('BL4MissionSelector.tracking')
    core=importlib.import_module('BL4MissionSelector.core.mission_save_replay')
    monkeypatch.setattr(c,'log',lambda _:None)
    monkeypatch.setattr(core,'dispatch',lambda *args:{'ok':True,'tracked':True})
    monkeypatch.setattr(core,'_lease',{'spec':{'mission':'Mission_Test'}})
    def broken(_):raise RuntimeError('world changed')
    monkeypatch.setattr(tracking,'arm',broken)
    assert c.native_action('mission_save_replay_track',{})=={'ok':True,'tracked':True}


def test_catalogue_and_display_numbers_match_all_supported_main_sections(packaged):
    # The installed SDK's version parser accepts dotted integers only.
    entry=importlib.import_module('BL4MissionSelector')
    assert tuple(int(part) for part in entry.mod.version.split('.'))==(2,39,2)
    c=packaged;total=0
    for campaign,expected in [('story',21),('fl4k',11),('ellie',6),('moxxi',1)]:
        rows=c.campaign_rows(campaign);assert len(rows)==expected
        for number,(name,row) in enumerate(rows,1):
            assert c.choose(campaign,str(number))[0]==name
            objectives=c.objective_rows(name,row);assert len(objectives)==len(row['sections'])
            total+=len(objectives)
    assert total==126
    assert not any(n.endswith(('.external_bridge','.quick_menu','.mobile_pairing')) for n in sys.modules)


def test_bundled_yaml_and_save_editor_import_from_sdk_zip(packaged):
    helper=importlib.import_module('BL4MissionSelector.save_tools.mission_save_replay')
    source="state: {char_guid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, char_name: Test}\n"
    assert helper.dispatch(dict(action='identity',yaml=source))['guid']=='a'*32
    assert packaged.documents_path().is_dir()
    vendor=importlib.import_module('BL4MissionSelector.save_tools._vendor.yaml')
    assert not vendor.__with_libyaml__
    # Replay core and narrow host/travel adapters import without a full app.
    importlib.import_module('BL4MissionSelector.core.mission_save_replay')
    importlib.import_module('BL4MissionSelector.core.backend_actions')


def test_authenticated_transport_denies_foreign_and_unknown_requests(packaged):
    c=packaged;c._token='test-token'
    server=c.ThreadingHTTPServer(('127.0.0.1',0),c.Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        url='http://127.0.0.1:'+str(server.server_port)
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(urllib.request.Request(url+'/native',data=b'{}',method='POST'),timeout=3)
        assert exc.value.code==403
        request=urllib.request.Request(url+'/native',data=b'{"action":"arbitrary_code"}',
            headers={'Authorization':'Bearer test-token'},method='POST')
        with urllib.request.urlopen(request,timeout=3) as r:assert not json.load(r)['ok']
        assert c._pending.empty()
    finally:server.shutdown();server.server_close()


def test_play_routes_main_objective_numbers_and_requires_confirmation(packaged,monkeypatch):
    c=packaged;requests=[];messages=[]
    monkeypatch.setattr(c,'submit',lambda action,payload:requests.append((action,payload)))
    monkeypatch.setattr(c,'log',messages.append)
    args=types.SimpleNamespace(operation='play',campaign='fl4k',mission='3',objective=1,yes=False,fog='leave')
    c.run(args);assert not requests and '--yes' in messages[-1]
    args.yes=True;c.run(args)
    assert requests[0][0]=='start' and requests[0][1]['mission']=='Mission_Main_Harmonica2'
    assert requests[0][1]['checkpoint']==0 and requests[0][1]['automatic']
    args.objective=10000;c.run(args);assert len(requests)==1


def test_full_msbt_conflict_is_checked_before_starting_a_worker(packaged,monkeypatch):
    sdk=sys.modules['mods_base'];sdk.get_ordered_mod_list=lambda:[types.SimpleNamespace(is_enabled=True,settings_file=Path('MattsSDKBoostingTools.json'))]
    with pytest.raises(RuntimeError,match='Move the full'):packaged.submit('start',{})
    assert not packaged._starting and packaged._process is None
    sdk.get_ordered_mod_list=lambda:[]
    monkeypatch.setitem(sys.modules,'MattsSDKBoostingTools',types.ModuleType('MattsSDKBoostingTools'))
    with pytest.raises(RuntimeError,match='Move the full'):packaged.submit('start',{})
    assert not packaged._starting and packaged._process is None


def test_complete_hidden_worker_transaction_with_real_epic_codec_and_preserved_backup(packaged,tmp_path,monkeypatch):
    """A local transport integration check, not a native/gameplay test."""
    c=packaged;worker=c._worker_files();endpoint=None;process=None;server=None
    helper=importlib.import_module('BL4MissionSelector.save_tools.mission_save_replay')
    yaml=importlib.import_module('BL4MissionSelector.save_tools._vendor.yaml')
    boundary=importlib.import_module('BL4MissionSelector.save_tools.mission_save_boundary')
    account='0123456789abcdef0123456789abcdef';profile=tmp_path/'saves'/account/'Profiles'/'client';profile.mkdir(parents=True)
    guid='a'*32;other='c'*32
    text='''state:
  checkpoint_name: World_P.Before
  inventory: !native [{serial: AbC, count: 1}]
  experience: {level: 70, rank: 701}
  char_guid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
  char_name: Original
missions:
  local_sets:
    unrelated_set:
      missions:
        unrelated: {status: Active, objectives: {stay: {status: Active}}}
world_state: !nativeworld {unchanged: 42}
timed_facts: {unchanged: abc}
'''
    def codec(command,value):
        data=dict(command=command,steamid=account,**({'yaml_content':value} if command=='encrypt' else {'sav_data':__import__('base64').b64encode(value).decode()}))
        script="const c=require('./codec');process.stdout.write(JSON.stringify(c.run(JSON.parse(require('fs').readFileSync(0,'utf8')))));"
        result=json.loads(subprocess.check_output([str(worker/'node.exe'),'-e',script],input=json.dumps(data).encode(),cwd=worker))
        assert result['success'];return __import__('base64').b64decode(result['sav_data']) if command=='encrypt' else result['yaml_content']
    original=codec('encrypt',text);(profile/'17.sav').write_bytes(original)
    (profile/'15.sav').write_bytes(codec('encrypt',text.replace(guid,other)))
    row=copy.deepcopy(c.catalogue()['Mission_Main_Harmonica2']);row['section']=row.pop('sections')['16']
    row['catalog_sha256']='test';row['force_travel']=True
    state=dict(guid=guid,world='world_p',lease=None,calls={});selected=[]
    def native(action,payload):
        op=action.removeprefix('mission_save_replay_')
        if op=='status':return dict(ok=True,loaded=True,pid=123,session='test',background_loading=True,**state)
        if op=='begin':
            state['lease']=payload['id'];return dict(ok=True,id=payload['id'],guid=guid,pid=123,session='test',spec=row,background_loading=True)
        if op=='close':state['lease']=None;return dict(ok=True)
        if op=='loader_bind':return dict(ok=True)
        if op=='loader_select':
            selected.append(payload['slot']);state['guid']=other if payload['role']=='other' else guid
        if op=='travel':state['world']='harmonica_p'
        key=f"{op}_{payload['role']}_{payload['cycle']}" if op in ('loader_refresh','loader_select') else op
        result=dict(ok=True,at_station=True,boundary_ready=True,encounter_ready=True,tracked=True)
        state['calls'][key]=dict(state='returned',result=result)
        return result
    monkeypatch.setattr(c,'native_action',native)
    c._token='test-token';server=c.ThreadingHTTPServer(('127.0.0.1',0),c.Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    env=__import__('os').environ.copy();env.update(MSBT_SELECTOR_ENDPOINT='http://127.0.0.1:'+str(server.server_port),
        MSBT_SELECTOR_TOKEN=c._token,MSBT_SELECTOR_SAVE_ROOT=str(tmp_path/'saves'),MSBT_SELECTOR_STORAGE=str(tmp_path/'replay'))
    output=queue.Queue()
    try:
        process=subprocess.Popen([str(worker/'node.exe'),str(worker/'worker.cjs')],cwd=worker,env=env,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
        def read():
            for line in process.stdout:output.put(json.loads(line))
        threading.Thread(target=read,daemon=True).start()
        process.stdin.write(json.dumps(dict(action='start',payload=dict(mission=row['mission'],checkpoint=16,automatic=True,acknowledge_shared_progress=True)))+'\n');process.stdin.flush()
        result=None;deadline=time.monotonic()+80
        while time.monotonic()<deadline:
            c._tick()
            try:
                result=output.get_nowait()
                assert result.get('ok',True),result
                if result.get('state')=='ready':break
            except queue.Empty:pass
            time.sleep(.01)
        assert result and result.get('state')=='ready',result
        assert selected==['C_15','C_17'] and state['lease'] is None
        edited=codec('decrypt',(profile/'17.sav').read_bytes());before=yaml.compose(text);after=yaml.compose(edited)
        for field in ('inventory','experience'):
            assert boundary.canonical(boundary.member(boundary.member(before,'state'),field))==boundary.canonical(boundary.member(boundary.member(after,'state'),field))
        backups=list((tmp_path/'replay'/'runs').glob('*/before.sav'));assert len(backups)==1 and backups[0].read_bytes()==original
        assert helper.dispatch(dict(action='inspect',yaml=edited,spec=row))['cursor']==16
    finally:
        if process:
            process.stdin.close()
            try:process.wait(timeout=8)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
        if server:server.shutdown();server.server_close()
