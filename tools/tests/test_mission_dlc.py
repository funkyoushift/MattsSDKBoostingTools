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


def load_dlc(monkeypatch):
    monkeypatch.setattr(importlib.resources,'files',lambda _:ROOT)
    spec=importlib.util.spec_from_file_location('dlc_merge_test',ROOT/'mission_dlc.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_missing_report_and_mixed_case_mission_never_bypass_entitlement_gate(monkeypatch):
    m=load_dlc(monkeypatch)
    result=m.requirement('MISSION_MAIN_COWBELL0',{})
    assert result['allowed'] is False and 'unconfirmed' in result['reason']
    assert m.requirement('Mission_Main_Beach',{}) is None


def test_mixed_guest_access_and_conflicts_skip_only_affected_pack_without_changing_reports(monkeypatch):
    import copy
    m=load_dlc(monkeypatch)
    def pack(access):
        return dict(allowed=all(a=='enabled' for a in access),title='DLC',reason='Missing or unknown access',
                    players=[dict(player=f'Player{i}',player_id=i,access=a) for i,a in enumerate(access)])
    native={'cowbell':pack(['enabled','enabled','enabled']), 'harmonica':pack(['enabled']*3),
            'vaultcard2':pack(['enabled','missing','enabled'])}
    attrs={'cowbell':pack(['enabled','missing','unknown']), 'harmonica':pack(['enabled']*3)}
    before=copy.deepcopy((native,attrs));result=m.merge_reports(native,attrs)
    assert not result['cowbell']['allowed'] and result['cowbell']['access_checks_disagree']==['Player1','Player2']
    assert result['harmonica']['allowed'] and not result['vaultcard2']['allowed']
    assert result['vaultcard2']['players'][0]['access']=='enabled'
    assert (native,attrs)==before


def test_identity_based_merge_ignores_report_order_and_never_uses_host_access_for_guest(monkeypatch):
    m=load_dlc(monkeypatch)
    native={'cowbell':dict(allowed=True,players=[dict(player='Host',player_id=1,access='enabled'),dict(player='Guest',player_id=2,access='enabled')])}
    attrs={'cowbell':dict(allowed=False,reason='Guest missing',players=[dict(player='Guest',player_id=2,access='missing'),dict(player='Host',player_id=1,access='enabled')])}
    result=m.merge_reports(native,attrs)['cowbell']
    assert not result['allowed'] and result['blocking_players']==['Guest']


def test_every_catalogued_dlc_mission_has_an_access_gate_including_tuba(monkeypatch):
    m=load_dlc(monkeypatch)
    catalog=json.loads((ROOT/'mission_catalog.json').read_text(encoding='utf-8'))
    for row in catalog:
        if row['category']=='dlc':
            assert m.requirement(row['name'],{})['allowed'] is False, row['name']
    assert m.DATA['missions']['Mission_DLC_Tuba_Base']['pack']=='tuba'
    assert m.DATA['packs']['tuba']['native_definition']=='dlcdef_tuba'
    assert 'attribute' not in m.DATA['packs']['tuba']
