import importlib, json, sys, types
from pathlib import Path
import pytest
from test_farming_controls import modules, Obj, FakeMemory


class Player(Obj):
    def __init__(self,name,address):
        super().__init__();self.name=name;self.address=address;self.Pawn=self
        self.Controller=self;self.PlayerState=self;self.bCanBeDamaged=True;self.updates=0
        self.InfiniteAmmoLock=types.SimpleNamespace(bLocked=False)
        self.InfiniteClipLock=types.SimpleNamespace(bLocked=False)
    def _get_address(self):return self.address
    def _path_name(self):return 'World.'+self.name
    def GetLevel(self):return self
    def HasAuthority(self):return True
    def ForceNetUpdate(self):self.updates+=1


@pytest.fixture
def players(modules,monkeypatch):
    engine,native,mods,sdk=modules
    host,a,b=Player('Host',1),Player('Guest A',2),Player('Guest B',3)
    mods.get_pc=lambda:host
    objects={p._path_name():p for p in (host,a,b)}
    sdk.find_object=lambda cls,path:objects.get(path)
    helper=types.ModuleType('lab_test.party_helpers')
    states=[host,a,b]
    helper._gbc_session_world_and_gamestate=lambda:(host,types.SimpleNamespace(PlayerArray=states))
    helper._gbc_find_pc_for_player_state=lambda ps,w:ps
    helper._gbc_resolve_player_display_name=lambda ps:ps.name
    monkeypatch.setitem(sys.modules,'lab_test.party_helpers',helper)
    targets=importlib.import_module('lab_test.farming_targets')
    return engine,native,targets,host,a,b,states


def test_two_guests_keep_independent_state_and_off_restores_only_selected(players):
    e,_,t,host,a,b,_=players
    for guest in (a,b):
        target=t.resolve({'target_player':guest.name},(None,''))
        assert e.action({'op':'set','feature':'god_mode','enabled':True},target)['ok']
    assert host.bCanBeDamaged and not a.bCanBeDamaged and not b.bCanBeDamaged
    assert e.action({'op':'set','feature':'god_mode','enabled':False},t.resolve({'target_player':'Guest A'}))['ok']
    assert a.bCanBeDamaged and not b.bCanBeDamaged
    assert b.updates>0
    assert e.off()['ok'] and b.bCanBeDamaged and not e._snapshots


def test_targeting_does_not_fall_back_to_reused_index_or_change_host(players):
    _,_,t,host,_,b,states=players
    states.pop(1)
    with pytest.raises(RuntimeError,match='left'):t.resolve({'target_player':'1|Guest A'})
    assert t.resolve({'target_player':'1|Guest B'})[0]['pc'] is b
    assert host.bCanBeDamaged


def test_status_never_dereferences_departed_session_wrappers(players):
    e, _, _, _, guest, _, states = players
    e.session_for(guest, guest, 'Guest A', 1)
    session = next(iter(e._sessions.values()))
    class Expired:
        def __getattribute__(self, name):
            raise AssertionError('Stale wrapper accessed: ' + name)
    session['pc'] = session['pawn'] = Expired()
    states.remove(guest)
    result = e.status()
    for feature in ('god_mode', 'infinite_ammo', 'no_reload'):
        row = result['features'][feature]['targets'][0]
        assert row['live'] is False
        assert 'actual_invulnerable' not in row and 'actual_locked' not in row


@pytest.mark.parametrize('scope,names',[('local',['Host']),('all',['Host','Guest A','Guest B']),('nonhost',['Guest A','Guest B']),('selected',['Guest B'])])
def test_scopes_resolve_current_party(players,scope,names):
    _,_,t,_,_,_,_=players
    assert [r['label'] for r in t.resolve({'target_scope':scope},(2,'Guest B'))]==names


def test_missing_guest_controller_never_uses_local_player(players):
    _,_,t,_,a,_,_=players
    t.party_helpers._gbc_find_pc_for_player_state=lambda ps,w:None if ps is a else ps
    with pytest.raises(RuntimeError,match='not loaded'):t.resolve({'target_player':'Guest A'})


def test_guest_disconnect_restores_only_departed_guest(players):
    e,_,t,host,a,b,states=players
    for guest in (a,b):e.action({'op':'set','feature':'infinite_ammo','enabled':True},t.resolve({'target_player':guest.name}))
    states.remove(a);e._last_tick=0;e.tick()
    assert not a.InfiniteAmmoLock.bLocked and b.InfiniteAmmoLock.bLocked and not host.InfiniteAmmoLock.bLocked
    assert e.off()['ok'] and not b.InfiniteAmmoLock.bLocked


def test_guest_respawn_does_not_apply_to_replacement_pawn(players):
    e,_,t,_,a,_,_=players
    e.action({'op':'set','feature':'god_mode','enabled':True},t.resolve({'target_player':'Guest A'}))
    replacement=Player('Replacement',55);a.Pawn=replacement;e._last_tick=0;e.tick()
    assert a.bCanBeDamaged and replacement.bCanBeDamaged


def test_transferred_object_cannot_acquire_two_restoration_owners(players):
    e,_,_,_,a,b,_=players;obj=Obj()
    first=e.session_for(a,a,'Guest A');second=e.session_for(b,b,'Guest B')
    with e.using(first):e.edit('rapid_fire',obj,'value',99.0)
    with pytest.raises(RuntimeError,match='another farming target'):
        with e.using(second):e.edit('rapid_fire',obj,'value',99.0)
    assert next(iter(e._snapshots.values()))['owner']==first['key']


def test_status_identifies_each_player_without_merging_flags(players):
    e,_,t,host,a,b,_=players
    e.action({'op':'set','feature':'no_reload','enabled':True},t.resolve({'target_player':'Guest A'}))
    row=e.status()['features']['no_reload']
    assert row['targets'][0]['label']=='Guest A' and row['targets'][0]['actual_locked']
    assert not host.InfiniteClipLock.bLocked and not b.InfiniteClipLock.bLocked


def test_backend_and_f7_use_selected_player_without_changing_selection(monkeypatch):
    from tests.test_quick_menu_last_command import _load_backend_actions
    backend=_load_backend_actions();calls=[];resolved=[]
    helper=types.ModuleType('MattsSDKBoostingTools.farming_targets')
    guest={'pc':object(),'label':'Guest','index':1}
    helper.resolve=lambda payload,selected:resolved.append((dict(payload),selected)) or [guest]
    monkeypatch.setitem(sys.modules,'MattsSDKBoostingTools.farming_targets',helper)
    monkeypatch.setattr(backend,'get_selected_player_index',lambda:1)
    monkeypatch.setattr(backend,'get_selected_player_name',lambda:'Guest')
    monkeypatch.setattr(backend.farming_controls,'action',lambda payload,targets=None:calls.append((dict(payload),targets)) or {'ok':True})
    assert backend.run_quick_menu_action('farming_god_mode_on',{})['ok']
    assert calls[-1][1]==[guest] and resolved[-1][1]==(1,'Guest')
    assert calls[-1][0]['target_scope']=='selected'
    assert backend.farming_lab_action({'op':'set','feature':'god_mode','enabled':False,'target_scope':'nonhost'})['ok']
    assert resolved[-1][0]['target_scope']=='nonhost'
    previous=len(resolved)
    assert backend.farming_lab_action({'op':'off'})['ok']
    assert len(resolved)==previous and calls[-1][1] is None


def test_backend_rejected_target_never_applies_local_controls(monkeypatch):
    from tests.test_quick_menu_last_command import _load_backend_actions
    backend=_load_backend_actions()
    helper=types.ModuleType('MattsSDKBoostingTools.farming_targets')
    def reject(*args):raise RuntimeError('Guest left')
    helper.resolve=reject
    monkeypatch.setitem(sys.modules,'MattsSDKBoostingTools.farming_targets',helper)
    monkeypatch.setattr(backend,'get_selected_player_index',lambda:1)
    monkeypatch.setattr(backend,'get_selected_player_name',lambda:'Guest')
    monkeypatch.setattr(backend.farming_controls,'action',lambda *args:pytest.fail('must not fall back to host'))
    result=backend.farming_lab_action({'op':'set','feature':'god_mode','enabled':True})
    assert not result['ok'] and result['message']=='Guest left'


def test_epic_native_hook_uses_epic_site_and_roundtrips(modules):
    _,n,_,_=modules;p=n.BUILDS['epic-4845623']['legendary_roll']
    memory=FakeMemory(p);memory.build='epic-4845623'
    h=n.NativeHook('legendary_roll',lambda:memory);h.allocate=lambda:0x180000000
    assert h.enable()['active'] and h.profile['rva']==0x3d9e2d2
    assert h.disable()['ok'] and memory.read(memory.base+p['rva'],len(p['context']))==p['context']


def test_epic_site_corruption_fails_before_native_write(modules):
    _,n,_,_=modules;p=n.BUILDS['epic-4845623']['legendary_roll']
    memory=FakeMemory(p);memory.build='epic-4845623';memory.write(memory.base+p['rva']+20,b'\xcc')
    h=n.NativeHook('legendary_roll',lambda:memory);h.allocate=lambda:pytest.fail('must not allocate')
    assert not h.enable()['ok'] and not h.owned


def test_both_profiles_and_every_qualified_span_match_executable_files():
    import hashlib,pefile
    receipt=json.loads((Path(__file__).resolve().parents[2]/'docs/native-farming/EPIC_PROFILE.json').read_text())
    files=receipt['files']
    if not all(Path(f['path']).is_file() for f in files):pytest.skip('Qualified executables not installed on this test host')
    pes=[pefile.PE(f['path'],fast_load=True) for f in files]
    for file in files:
        with Path(file['path']).open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==file['sha256']
    for span in receipt['unique_matches']:
        for index,key in enumerate(('steam','epic')):
            assert hashlib.sha256(pes[index].get_data(span[key+'_rva'],span['size'])).hexdigest()==span[key+'_sha256']
    for table in receipt['vtables']:
        for span in table['methods']:
            assert hashlib.sha256(pes[1].get_data(span['epic_rva'],span['size'])).hexdigest()==span['epic_sha256']
