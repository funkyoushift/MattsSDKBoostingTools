"""Offline manual clear/undo regressions. These do not verify guest save persistence."""
import ast
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'mod_extracted/MattsSDKBoostingTools/backend_actions.py'

def load():
    names = {'chaos_undo_empty_backpack', '_store_deleted_backpack_snapshot',
             '_capture_deleted_backpack_snapshot', '_serials_from_payload', 'chaos_empty_backpack'}
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    ns = {'_installation_authorized':lambda password=None:password=='funkyou', 'Any':object, '_BACKPACK_DELETE_CAP':2000, '_backpack_delete_memory':{},
          '_deleted_backpack_status':lambda:{}, '_backpack_snapshot_target':lambda pc:pc,
          '_chaos_selected_pc':lambda:('guest-a','Guest A'), 'refresh_players':lambda:None,
          'get_selected_player_index':lambda:1,'get_selected_player_name':lambda:'Guest A'}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(SOURCE),'exec'), ns)
    return ns

def test_password_retry_authorizes_bulk_undo_and_keeps_backup(tmp_path, monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path)); ns=load(); calls=[]
    snapshot={'index':1,'name':'A','target':'guest-a','serials':['@Ua']*71}
    ns['_store_deleted_backpack_snapshot'](snapshot)
    def send(serials,mode,bulk_authorized=False):
        calls.append((serials,bulk_authorized))
        return {'ok':bulk_authorized,'password_required':not bulk_authorized,'password_kind':'bulk_loot',
                'report_path':'own-report.jsonl'}
    ns['_deliver_serials_with_target']=send
    ns['serial_rewards']=NS(serial_delivery_progress=lambda:{'report_path':'report.jsonl'})
    assert ns['chaos_undo_empty_backpack']()['password_required']
    assert ns['chaos_undo_empty_backpack']({'bulk_loot_password':'wrong'})['password_required']
    assert ns['chaos_undo_empty_backpack']({'bulk_loot_password':'funkyou'})['ok']
    assert calls[-1]==(['@Ua']*71,True)
    assert ns['_backpack_delete_memory'][1]['serials']==['@Ua']*71
    assert ns['_backpack_delete_memory'][1]['restore_report']=='own-report.jsonl'
    assert json.loads(Path(snapshot['backup_path']).read_text())['serials']==['@Ua']*71
    assert not ns['chaos_undo_empty_backpack']({'bulk_loot_password':'funkyou'})['ok']
    assert len(calls)==3

def test_slot_replacement_cannot_receive_previous_players_undo(tmp_path, monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path)); ns=load()
    ns['_store_deleted_backpack_snapshot']({'index':1,'target':'guest-old','serials':['@Ua']})
    ns['_deliver_serials_with_target']=lambda *a,**k:(_ for _ in ()).throw(AssertionError('wrong player'))
    assert not ns['chaos_undo_empty_backpack']()['ok']

def test_capture_keeps_duplicates_and_does_not_use_stale_ui_rows(monkeypatch):
    ns=load();package=types.ModuleType('backpack_test');reader=NS()
    package.item_serial_reader=reader
    monkeypatch.setitem(sys.modules,'backpack_test',package);ns['__package__']='backpack_test'
    reader.read_inventory_for_party_index=lambda *a,**k:{'equipped':[], 'backpack':[{'serial':'@Ua'},{'serial':'@Ua'}]}
    assert ns['_capture_deleted_backpack_snapshot']()['serials']==['@Ua','@Ua']
    reader.read_inventory_for_party_index=lambda *a,**k:{'equipped':[],'backpack':[]}
    assert ns['_capture_deleted_backpack_snapshot']({'serials':['@Ustale']})['serials']==[]
    reader.read_inventory_for_party_index=lambda *a,**k:{'truncated':True,'backpack':[{'serial':'@Ua'}]}
    assert ns['_capture_deleted_backpack_snapshot']()['read_error']

def test_empty_persists_before_mutation_and_retains_backup_on_failure(tmp_path,monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path));ns=load();order=[]
    ns['_backpack_target_password_guard']=lambda *a:None
    ns['_capture_deleted_backpack_snapshot']=lambda *a:{'index':1,'target':'guest-a','serials':['@Ua','@Ua']}
    def clear(pc):
        assert len(list(tmp_path.rglob('*.json')))==1
        order.append(pc)
        raise RuntimeError('clear failed')
    ns['streamer_chaos']=NS(empty_backpack_for_pc=clear)
    assert not ns['chaos_empty_backpack']()['ok']
    assert order==['guest-a']
    assert ns['_backpack_delete_memory'][1]['serials']==['@Ua','@Ua']
    ns['_store_deleted_backpack_snapshot']({'index':1,'serials':[]})
    assert ns['_backpack_delete_memory'][1]['serials']==['@Ua','@Ua']
