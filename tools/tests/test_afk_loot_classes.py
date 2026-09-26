import importlib.util,json,random
from pathlib import Path
from types import SimpleNamespace
import pytest
ROOT=Path(__file__).resolve().parents[2]/'mod_extracted/MattsSDKBoostingTools'
spec=importlib.util.spec_from_file_location('afk_loot_test',ROOT/'afk_loot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m._roots=json.loads((ROOT/'afk_loot_classes.json').read_text())['roots']
CLASSES=['Char_DarkSiren','Char_Paladin','Char_ExoSoldier','Char_Gravitar','Char_CorpoHacker','Char_RoboDealer']
@pytest.mark.parametrize('character',CLASSES)
def test_only_matching_class_mods_and_guaranteed_slot(character):
 pool=[f'gun{i}' for i in range(956)]+CLASSES
 classes=[None]*956+CLASSES
 for seed in range(15):
  selected,excluded=m.select_loot(pool,classes,character,True,random.Random(seed))
  assert len(selected)==70 and character in selected
  assert not set(selected).intersection(set(CLASSES)-{character})
  assert excluded==5
 selected,excluded=m.select_loot(pool,classes,character,False,random.Random(0))
 assert len(selected)==957 and selected[-1]==character
 assert excluded==5

def test_small_pool_unknown_and_absent_match():
 pool=['gun','siren','unknown','unknownclass']
 classes=[None,'Char_DarkSiren','unknown_item','unknown_class']
 selected,excluded=m.select_loot(pool,classes,'Char_Gravitar',True,random.Random(0))
 assert selected==['gun'] and excluded==3
 with pytest.raises(ValueError,match='Waiting'):
  m.select_loot(pool,classes,None,True,random.Random())
 with pytest.raises(ValueError,match='No compatible'):
  m.select_loot(['siren'],['Char_DarkSiren'],'Char_Gravitar',True,random.Random())

def test_repeated_copies_remain_separate_entries():
 selected,_=m.select_loot(['gun','gun','mod'],[None,None,'Char_DarkSiren'],'Char_DarkSiren',True,random.Random())
 assert sorted(selected)==['gun','gun','mod']

def test_native_character_field_only_no_name_guessing():
 for character in CLASSES:
  assert m.player_class(None,SimpleNamespace(ReplicatedCharacterDef=character),None)==character
 assert m.player_class(None,SimpleNamespace(ReplicatedCharacterDef='new_unknown_class'),None) is None
 assert m.player_class(None,SimpleNamespace(),SimpleNamespace(Name='Char_DarkSiren')) is None

def test_packaged_class_restrictions_match_extracted_native_definitions():
 for root,character in {'254':'Char_DarkSiren','255':'Char_Paladin','256':'Char_ExoSoldier','259':'Char_Gravitar','402':'Char_CorpoHacker','404':'Char_RoboDealer'}.items():
  assert m.roots()[root]['class']==character
 assert m.roots()['234']['class']=='unknown_class'


def test_two_guaranteed_items_plus_sixty_eight_random():
 pool=['gun','shield']+[f'other{i}' for i in range(956)]
 selected,_=m.select_loot(pool,[None]*len(pool),'Char_DarkSiren',True,random.Random(2),['gun','shield'],[None,None])
 assert len(selected)==70 and selected[:2]==['gun','shield']
 assert selected.count('gun')==selected.count('shield')==1
 assert len(set(selected[2:]))==68


def test_guaranteed_class_mod_counts_toward_class_rule_and_total():
 pool=['siren','exo']+[f'gun{i}' for i in range(100)]
 classes=['Char_DarkSiren','Char_ExoSoldier']+[None]*100
 fixed=['siren','exo','shield']
 fixed_classes=['Char_DarkSiren','Char_ExoSoldier',None]
 selected,_=m.select_loot(pool,classes,'Char_DarkSiren',True,random.Random(3),fixed,fixed_classes)
 assert len(selected)==70 and selected[:2]==['siren','shield']
 assert selected.count('siren')==1 and 'exo' not in selected
 selected,_=m.select_loot(pool,classes,'Char_DarkSiren',False,random.Random(3),fixed,fixed_classes)
 assert len(selected)==102 and selected.count('siren')==1 and 'exo' not in selected


def test_guaranteed_only_and_short_pool_do_not_invent_filler():
 assert m.select_loot([],[],None,True,random.Random(),['gun','gun'],[None,None])[0]==['gun','gun']
 selected,_=m.select_loot(['shield'],[None],None,True,random.Random(),['gun'],[None])
 assert selected==['gun','shield']
 fixed=[f'fixed{i}' for i in range(70)]
 assert m.select_loot(['shield'],[None],None,True,random.Random(),fixed,[None]*70)[0]==fixed


def test_class_guarantee_uses_remaining_slot_and_conflict_is_explicit():
 fixed=[f'fixed{i}' for i in range(69)]
 selected,_=m.select_loot(['siren','gun'],['Char_DarkSiren',None],'Char_DarkSiren',True,random.Random(),fixed,[None]*69)
 assert len(selected)==70 and selected[-1]=='siren'
 with pytest.raises(ValueError,match='no slot'):
  m.select_loot(['siren'],['Char_DarkSiren'],'Char_DarkSiren',True,random.Random(),fixed+['last'],[None]*70)

def test_catalog_codes_with_unsupported_payloads_classify_by_header(monkeypatch):
 import sys, types
 package=types.ModuleType('afk_header_regression'); package.__path__=[str(ROOT)]
 monkeypatch.setitem(sys.modules,package.__name__,package)
 spec=importlib.util.spec_from_file_location(package.__name__+'.afk_loot',ROOT/'afk_loot.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module._roots=m.roots()
 from afk_header_regression import serial_converter as converter
 catalog=ROOT.parents[1]/'external_app/v22_parts_codes_fixed/resources/MattsSDKBoostingTools_gzo_codes.json'
 def strings(value):
  if isinstance(value,str):yield value
  elif isinstance(value,dict):
   for child in value.values():yield from strings(child)
  elif isinstance(value,list):
   for child in value:yield from strings(child)
 checked=0
 for code in set(strings(json.loads(catalog.read_text(encoding='utf-8-sig')))):
  if not code.startswith('@U'):continue
  try:converter.serial_to_human(code)
  except EOFError:
   numbers,_=converter._read_header_numbers(code)
   assert module.classify_serials([code])==[m.roots().get(str(numbers[0]),{'class':'unknown_item'})['class']]
   checked+=1
  except ValueError:
   with pytest.raises(ValueError,match="AFK item code 1"):
    module.classify_serials([code])
 assert checked>0
 with pytest.raises(ValueError,match='AFK item code 1'):
  module.classify_serials(['@U'])
