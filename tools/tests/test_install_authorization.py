import ast
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
SDK=ROOT/'mod_extracted/MattsSDKBoostingTools'

def load():
    spec=importlib.util.spec_from_file_location('authorization_test',SDK/'install_authorization.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

@pytest.fixture
def authorization(tmp_path,monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    return load()

def test_unlock_survives_fresh_module_without_storing_password(authorization):
    assert not authorization.authorized()
    assert not authorization.authorized('wrong')
    assert not authorization.authorized(True)
    assert not authorization._path().exists()
    assert authorization.authorized('funkyou')
    assert load().authorized()
    assert 'funkyou' not in authorization._path().read_text()
    assert list(authorization._path().parent.glob('*.tmp'))==[]

def test_other_install_and_corrupt_receipt_stay_locked(authorization,monkeypatch):
    assert authorization.authorized('funkyou')
    another=load();monkeypatch.setattr(another,'__file__',str(SDK/'different-install'/'mod'/'install_authorization.py'))
    assert not another.authorized()
    authorization._path().write_text('{broken')
    assert not load().authorized()

def test_backpack_unlock_allows_bulk_and_still_checks_expected_target(authorization):
    tree=ast.parse((SDK/'backend_actions.py').read_text(encoding='utf-8'))
    names={'_backpack_target_password_guard','_deliver_serials_with_target'}
    ns={'Any':object,'_installation_authorized':authorization.authorized,
        '_uvh_obj_addr':lambda pc:pc,'_uvh_obj_path':lambda pc:'pc',
        'get_pc':lambda:0,'_challenge_is_host':lambda:(True,'host'),
        '_serial_delivery_count_note':lambda *a:'','get_selected_player_index':lambda:1,
        'get_selected_player_name':lambda:'Guest'}
    calls=[]
    from types import SimpleNamespace
    ns['serial_rewards']=SimpleNamespace(_do_give_serial_to_player_indices=lambda *a,**k:calls.append(k))
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'guards','exec'),ns)
    guard=ns['_backpack_target_password_guard'];send=ns['_deliver_serials_with_target']
    assert guard(1)['password_required']
    assert send(['@Ua']*71,'selected')['password_required']
    assert guard(1,{'backpack_password':'funkyou'}) is None
    assert guard(1) is None
    assert send(['@Ua']*71,'selected')['ok']
    assert calls[-1]['bulk_authorized'] is True
    assert not guard(2,{'backpack_expected_target':'1:pc'})['ok']


def test_afk_restart_reuses_install_unlock(authorization):
    spec=importlib.util.spec_from_file_location('afk_authorization_test',SDK/'afk_lobby.py')
    lobby_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(lobby_module)
    from types import SimpleNamespace
    game=SimpleNamespace(prepare_loot=lambda p:['@Ua']*71, classify_loot=lambda s:[None]*len(s),
        authorize_bulk_loot=authorization.authorized, is_host=lambda:True)
    lobby=lobby_module.Lobby(game)
    assert lobby.start({'loot':True})['password_required']
    assert lobby.start({'loot':True,'bulk_loot_password':'funkyou'})['ok']
    lobby.stop()
    assert lobby.start({'loot':True})['ok']
    assert lobby.config['bulk_loot_authorized'] is True
