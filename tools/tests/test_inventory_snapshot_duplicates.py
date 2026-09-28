"""Inventory snapshots count physical rows, not unique item-code strings."""
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FILE=ROOT/'mod_extracted/MattsSDKBoostingTools/item_serial_reader.py'

def reader(rows, active=None):
    names={'read_inventory_for_player_state','read_equipped_serials_for_player_state','_append_active_weapon'}
    tree=ast.parse(FILE.read_text(encoding='utf-8'))
    def entry(row,**kw):
        if row is None:return None
        return dict(row,label=kw.get('label_hint',''),summary='Test item',level=70)
    ns={'Any':object,'_INVENTORY_READ_CAP':2000,'_last_read_diag':{},'_log':lambda s:None,
        '_backpack_items_for_player_state':lambda ps:rows,'_equip_slot_of':lambda row:row['slot'],
        '_is_equipped_slot':lambda slot:slot>=0,'_entry_from_source':entry,
        'equip_slot_label':str,'_scan_row_stats':lambda rows:{},'empty_read_reason':lambda *a,**k:'',
        '_pawn_for_player_state':lambda ps:type('Pawn',(),{'weapon':active})(),
        '_live':lambda pawn:True,'_ACTIVE_WEAPON_ATTRS':['weapon']}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(FILE),'exec'),ns)
    return ns['read_inventory_for_player_state']

def test_identical_equipped_and_backpack_copies_all_survive_snapshot():
    rows=[{'slot':0,'serial':'@Ua'},{'slot':1,'serial':'@Ua'},
          {'slot':-1,'serial':'@Ua'},{'slot':-1,'serial':'@Ua'}]
    result=reader(rows,active=rows[0])(object())
    assert result['equipped_count']==2 and result['backpack_count']==2
    assert [r['serial'] for r in result['equipped']+result['backpack']]==['@Ua']*4
    assert not result['truncated']

def test_duplicate_rows_still_count_against_capture_cap():
    rows=[{'slot':-1,'serial':'@Ua'} for _ in range(3)]
    result=reader(rows)(object(),backpack_limit=2)
    assert result['backpack_count']==2 and result['truncated']

def test_active_weapon_already_in_equipment_is_not_added_twice():
    rows=[{'slot':0,'serial':'@Ua'},{'slot':-1,'serial':'@Ub'}]
    result=reader(rows,active=rows[0])(object())
    assert result['equipped_count']==1 and result['backpack_count']==1
