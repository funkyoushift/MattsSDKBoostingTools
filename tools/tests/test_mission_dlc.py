"""DLC reads must use each controller, distinguish unknown and never grant access."""
import importlib.util
import importlib.resources
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'

def test_dlc_uses_player_context_not_local_or_shared_facts(monkeypatch):
    monkeypatch.setattr(importlib.resources,'files',lambda package:ROOT)
    spec=importlib.util.spec_from_file_location('dlc_test',ROOT/'mission_dlc.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.DATA={'packs':{'cowbell':{'title':'Vault','attribute':'Entitlement_Cowbell'}},'missions':{'test':{'pack':'cowbell'}}}
    calls=[]
    def read(**kw):
        calls.append(kw)
        return 0 if kw['AttributeDef'].endswith('_Session') or kw['ContextSource']=='guest' else 1
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(find_object=lambda *a:NS(GetValueOfAttributeAsInteger=read)))
    rows=[dict(pc='host',label='Host',state=NS(PlayerId=1)),dict(pc='guest',label='Guest',state=NS(PlayerId=2))]
    r=m.inspect(rows)['cowbell']
    assert not r['allowed'] and r['blocking_players']==['Guest']
    assert {c['ContextSource'] for c in calls}=={'host','guest'}
    assert all('_Local' not in c['AttributeDef'] for c in calls)
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(find_object=lambda *a:NS(GetValueOfAttributeAsInteger=lambda **kw:-99)))
    r=m.inspect(rows)['cowbell']
    assert not r['allowed'] and r['blocking_players']==[]
    assert all(p['access']=='unknown' for p in r['players'])

def test_dlc_catalog_pins_sources_and_maps_invitation():
    data=json.loads((ROOT/'mission_dlc_catalog.json').read_text())
    assert data['missions']['mission_main_cowbell0']['pack']=='cowbell'
    assert data['missions']['Mission_Side_Invasive1']['pack']=='cowbell'
    assert data['source_sha256'] and all(len(h)==64 for h in data['source_sha256'].values())
    assert 'Mission_Main_Beach' not in data['missions']

def test_playable_dlc_activity_coverage_is_entitlement_gated():
    data=json.loads((ROOT/'mission_dlc_catalog.json').read_text())
    catalog={row['name']:row for row in json.loads((ROOT/'mission_catalog.json').read_text())}
    expected={
        'harmonica':('ZoneActivity_Grotto_Jungle','ZoneActivity_Grotto_Lava',
                    'ZoneActivity_Lockdown_Jungle','ZoneActivity_Lockdown_Lava',
                    'ZoneActivity_Intro_Safehouse_Horde','ZoneActivity_Jungle_Safehouse_Horde',
                    'ZoneActivity_Lava_Safehouse_Horde'),
        'cowbell':('ZoneActivity_DLC1_Bunker','ZoneActivity_DLC1_FuelSiphon1','ZoneActivity_DLC1_FuelSiphon2'),
    }
    for pack,names in expected.items():
        for name in names:
            assert catalog[name]['category']=='activities'
            assert data['missions'][name]['pack']==pack
    assert not any('Template' in name for name in catalog)
