"""Related world objectives must be queued without replaying completed work."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

PATH = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools/mission_effects.py'
spec = importlib.util.spec_from_file_location('completion_effects_test', PATH)
effects = importlib.util.module_from_spec(spec)
spec.loader.exec_module(effects)
CLAIM = effects._world_safehouse_claim_address(effects.SAFEHOUSE, PATH.parent)


def context(monkeypatch, child='locked', parent='completed'):
    import importlib.resources
    monkeypatch.setattr(importlib.resources, 'files', lambda package: PATH.parent)
    values, writes, journal = {}, [], []
    def write(**kw):
        writes.append(kw['AddressString'])
        values[kw['AddressString']] = kw['AsName']
    facts = NS(ReadFact=lambda **kw: (None, values.get(kw['AddressString'], 'None')),
               WriteFact=write)
    monkeypatch.setitem(sys.modules, 'unrealsdk', NS(find_object=lambda *args: facts,
                                                    find_all=lambda *args, **kw: []))
    owner = NS(_job=dict(names=[effects.BEACH], total=1, target='host'),
               _journal=journal.append, _state=lambda r: r,
               _row=lambda snap, name: parent if name == effects.BEACH else child)
    return owner, NS(snapshot=lambda: {}), [dict(pc=NS(_path_name=lambda: 'host'), host=True)], writes, values


def test_repairs_then_queues_external_objective_once(monkeypatch):
    owner, engine, party, writes, _ = context(monkeypatch)
    effects.complete_dependencies(owner, engine, party, effects.BEACH)
    effects.complete_dependencies(owner, engine, party, effects.BEACH)
    assert writes == list(effects.CHECKPOINTS)
    assert owner._job['names'] == [effects.BEACH, effects.SAFEHOUSE]
    assert owner._job['total'] == 2


def test_completed_safehouse_is_not_replayed(monkeypatch):
    owner, engine, party, _, _ = context(monkeypatch, child='completed')
    effects.complete_dependencies(owner, engine, party, effects.BEACH)
    assert owner._job['names'] == [effects.BEACH]


def test_fast_completion_claims_abandoned_post_world_state_once(monkeypatch):
    owner, engine, party, writes, values = context(monkeypatch, child='completed')
    owner._job['names'] = [effects.SAFEHOUSE]
    values[CLAIM] = 'Claimable'
    effects.complete_dependencies(owner, engine, party, effects.SAFEHOUSE)
    effects.complete_dependencies(owner, engine, party, effects.SAFEHOUSE)
    assert writes == [CLAIM]
    assert values[CLAIM] == 'Claimed'
    assert owner._job['names'] == [effects.SAFEHOUSE]
    assert any(event['event'] == 'safehouse_claim_verified' for event in owner._journal.__self__)


def test_fast_completion_claims_uninitialized_safehouse(monkeypatch):
    owner, engine, party, writes, values = context(monkeypatch, child='completed')
    owner._job['names'] = [effects.SAFEHOUSE]
    effects.complete_dependencies(owner, engine, party, effects.SAFEHOUSE)
    assert writes == [CLAIM]
    assert values[CLAIM] == 'Claimed'


def test_loaded_safehouse_actor_uses_native_state_machine(monkeypatch):
    import json
    owner, engine, party, writes, values = context(monkeypatch, child='completed')
    identity = json.loads((PATH.parent / 'mission_activity_actors.json').read_text())[
        effects.SAFEHOUSE]['actor']
    actor = NS(FactsConduit=NS(GroupName=NS(Name=identity['groupname']),
                                RegistryName=NS(Name=NS(Name=identity['registryname']))),
               state='Claimable')
    transitions = []
    def set_state(**kw):
        transitions.append(kw['StateValue'].Name)
        kw['OwnerContext'].state = kw['StateValue'].Name
    lib = NS(GetActorStateValue=lambda **kw: (kw['OwnerContext'].state,),
             GetActorStateMachineStates=lambda **kw: ([NS(Name='Initialization'), NS(Name='Claimed')],),
             SetActorStateValue=set_state)
    sdk = NS(find_all=lambda *args, **kw: [actor], find_object=lambda *args: lib,
             make_struct=lambda path, **kw: NS(**kw))
    monkeypatch.setitem(sys.modules, 'unrealsdk', sdk)
    effects.complete_dependencies(owner, engine, party, effects.SAFEHOUSE)
    effects.complete_dependencies(owner, engine, party, effects.SAFEHOUSE)
    assert transitions == ['Claimed'] and actor.state == 'Claimed'
    assert not writes and not values


def test_inspect_safehouse_claim_reads_loaded_actor_without_writing(monkeypatch):
    import json
    context(monkeypatch)
    identity = json.loads((PATH.parent / 'mission_activity_actors.json').read_text())[
        effects.SAFEHOUSE]['actor']
    actor = NS(FactsConduit=NS(GroupName=NS(Name=identity['groupname']),
                                RegistryName=NS(Name=NS(Name=identity['registryname']))),
               state='Claimable')
    writes = []
    lib = NS(GetActorStateValue=lambda **kw: (kw['OwnerContext'].state,),
             SetActorStateValue=lambda **kw: writes.append(kw))
    sdk = NS(find_all=lambda *args, **kw: [actor], find_object=lambda *args: lib,
             make_struct=lambda path, **kw: NS(**kw))
    monkeypatch.setitem(sys.modules, 'unrealsdk', sdk)
    result = effects.inspect_safehouse_claim(object(), effects.SAFEHOUSE, CLAIM)
    assert result == dict(mission=effects.SAFEHOUSE, address=CLAIM,
                          channel='loaded_actor', state='Claimable')
    assert actor.state == 'Claimable' and not writes


def test_inspect_safehouse_claim_reads_stored_fact_without_writing(monkeypatch):
    owner, _, _, writes, values = context(monkeypatch)
    values[CLAIM] = 'Discovered'
    result = effects.inspect_safehouse_claim(owner, effects.SAFEHOUSE, CLAIM)
    assert result == dict(mission=effects.SAFEHOUSE, address=CLAIM,
                          channel='stored_fact', state='Discovered')
    assert not writes and values[CLAIM] == 'Discovered'


def test_inspect_safehouse_claim_rejects_unreviewed_identity_before_reads(monkeypatch):
    owner, _, _, writes, _ = context(monkeypatch)
    reads = []
    sdk = sys.modules['unrealsdk']
    sdk.find_all = lambda *args, **kw: reads.append('actors') or []
    with pytest.raises(ValueError, match='address does not match'):
        effects.inspect_safehouse_claim(owner, effects.SAFEHOUSE, CLAIM + '.wrong')
    with pytest.raises(ValueError, match='not a reviewed'):
        effects.inspect_safehouse_claim(owner, 'ZoneActivity_Grasslands_SafehouseMadeUp', CLAIM)
    assert not reads and not writes


def test_safehouse_claim_read_failure_journals_bounded_underlying_error(monkeypatch):
    owner, _, _, writes, _ = context(monkeypatch, child='completed')
    owner._job['names'] = [effects.SAFEHOUSE]
    sdk = sys.modules['unrealsdk']
    sdk.find_all = lambda *args, **kw: []
    sdk.find_object = lambda *args: NS(ReadFact=lambda **kw: (_ for _ in ()).throw(
        OSError('readback transport unavailable')))
    with pytest.raises(OSError, match='readback transport unavailable'):
        effects.complete_dependencies(owner, NS(snapshot=lambda: {}),
            [dict(pc=object(), host=True)], effects.SAFEHOUSE)
    failure = next(event for event in reversed(owner._journal.__self__)
                   if event['event'] == 'safehouse_claim_error')
    assert failure['stage'] == 'before_read'
    assert failure['error'] == 'OSError: readback transport unavailable'
    assert not writes


def test_ambiguous_loaded_safehouse_aborts_without_write(monkeypatch):
    import json
    owner, engine, party, writes, _ = context(monkeypatch, child='completed')
    identity = json.loads((PATH.parent / 'mission_activity_actors.json').read_text())[
        effects.SAFEHOUSE]['actor']
    actor = NS(FactsConduit=NS(GroupName=NS(Name=identity['groupname']),
                                RegistryName=NS(Name=NS(Name=identity['registryname']))))
    sys.modules['unrealsdk'].find_all = lambda *args, **kw: [actor, actor]
    with pytest.raises(RuntimeError, match='ambiguous'):
        effects.complete_dependencies(owner, engine, party, effects.SAFEHOUSE)
    assert not writes


def test_party_safehouse_capture_uses_host_world_context(monkeypatch):
    owner, engine, party, _, values = context(monkeypatch, child='completed')
    owner._job.update(names=[effects.SAFEHOUSE], target='visitor')
    host = party[0]['pc']
    visitor = NS(_path_name=lambda: 'visitor')
    party.insert(0, dict(pc=visitor, host=False))
    contexts = []

    def write(**kw):
        contexts.append(kw['OwnerContext'])
        values[kw['AddressString']] = kw['AsName']

    sys.modules['unrealsdk'].find_object = lambda *args: NS(
        ReadFact=lambda **kw: (None, values.get(kw['AddressString'], 'None')),
        WriteFact=write)
    effects.complete_dependencies(owner, engine, party, effects.SAFEHOUSE)
    assert contexts == [host]


def test_safehouse_capture_requires_completed_mission_and_known_state(monkeypatch):
    owner, engine, party, writes, values = context(monkeypatch, child='active')
    owner._job['names'] = [effects.SAFEHOUSE]
    with pytest.raises(RuntimeError, match='Complete'):
        effects.complete_dependencies(owner, engine, party, effects.SAFEHOUSE)
    values[CLAIM] = 'Failed'
    owner._row = lambda snapshot, name: 'completed'
    with pytest.raises(RuntimeError, match='unknown'):
        effects.complete_dependencies(owner, engine, party, effects.SAFEHOUSE)
    assert not writes


def test_safehouse_claim_matches_authored_completion_action():
    import json
    source = PATH.parents[2] / 'external_app/v22_parts_codes_fixed/matt_editor/LegitItems/Nexus-Data-Mission4.json'
    entry = json.loads(source.read_text(encoding='utf-8'))['mission']['records'][2]['entries'][20]
    mission = entry['zoneactivity_grasslands_safehousemain']
    poa = next(row['poa']['aliasdata']['actor'] for row in mission['alias_nodes']['alias'] if 'poa' in row)
    action = next(row['data'] for row in mission['states']['completed']['actions']
                  if row['data'].get('alias') == 'PoA')
    assert mission['mission'] == effects.SAFEHOUSE
    assert action['factchange'] == {'fact': 'State', 'value': {'namevalue': 'Claimed'}}
    assert CLAIM == '.'.join((
        'registry', poa['map'], 'top', poa['groupname'], poa['registryname'], 'State'))


def test_all_base_safehouse_claims_match_authored_actions():
    import json
    source = PATH.parents[2] / 'external_app/v22_parts_codes_fixed/matt_editor/LegitItems/Nexus-Data-Mission4.json'
    records = json.loads(source.read_text(encoding='utf-8'))['mission']['records']
    missions = {item['mission']: item for record in records for entry in record.get('entries', [])
                for item in entry.values() if isinstance(item, dict) and 'mission' in item}
    actors = json.loads((PATH.parent / 'mission_activity_actors.json').read_text())
    base = {name: row for name, row in actors.items()
            if name.startswith('ZoneActivity_') and 'Safehouse' in name and row['actor']['map'] == 'World_P'}
    assert len(base) == 14
    for name, row in base.items():
        actions = missions[name]['states']['completed']['actions']
        assert any(action.get('data', {}).get('alias', '').casefold() == 'poa'
                   and action['data'].get('factchange') == {'fact': 'State', 'value': {'namevalue': 'Claimed'}}
                   for action in actions)
        actor = row['actor']
        assert effects._world_safehouse_claim_address(name, PATH.parent) == '.'.join((
            'registry', actor['map'], 'top', actor['groupname'], actor['registryname'], 'State'))


def test_subordinate_requirements_skip_completed_and_queued_work(monkeypatch):
    import importlib.resources
    monkeypatch.setattr(importlib.resources, 'files', lambda package: PATH.parent)
    owner, engine, party, writes, _ = context(monkeypatch)
    parent = 'Mission_Main_Harmonica3'
    owner._job['names'] = [parent, 'Mission_Main_Harmonica3_Lava']
    owner._row = lambda snapshot, name: 'completed' if name in (parent, 'Mission_Main_Harmonica3_Hotel') else 'available'
    effects.complete_dependencies(owner, engine, party, parent)
    effects.complete_dependencies(owner, engine, party, parent)
    assert owner._job['related_completion'] == ['Mission_Main_Harmonica3_Logistics',
        'Mission_Main_Harmonica3_Spa', 'Mission_Main_Harmonica3_Theatre']
    assert len(owner._job['names']) == 5 and owner._job['total'] == 5
    assert not writes  # No prerequisite facts are invented for these relationships.


def test_credit_repair_never_queues_related_missions(monkeypatch):
    owner, engine, party, writes, _ = context(monkeypatch)
    owner._job['selection_scope'] = 'challenge_credit'
    effects.complete_dependencies(owner, engine, party, effects.BEACH)
    effects.complete_dependencies(owner, engine, party, 'Mission_Main_Harmonica3')
    assert not writes and owner._job['names'] == [effects.BEACH]


def test_unfinished_parent_never_grants_prerequisite(monkeypatch):
    owner, engine, party, writes, _ = context(monkeypatch, parent='active')
    with pytest.raises(RuntimeError, match='Complete Recruitment Drive'):
        effects.complete_dependencies(owner, engine, party, effects.BEACH)
    assert not writes


def test_unexpected_fact_stops_before_write(monkeypatch):
    owner, engine, party, writes, values = context(monkeypatch)
    values[effects.CHECKPOINTS[0]] = 'Failed'
    with pytest.raises(RuntimeError, match='Unexpected'):
        effects.complete_dependencies(owner, engine, party, effects.BEACH)
    assert not writes


def test_individual_completion_applies_its_reviewed_travel_requirements_only(monkeypatch):
    import json
    owner, engine, party, writes, values = context(monkeypatch)
    parent = 'Mission_Main_SearchForLilith'
    owner._job['names'] = [parent]
    owner._row = lambda snapshot, name: 'completed' if name == parent else 'locked'
    checkpoints = json.loads((PATH.parent / 'travel_checkpoints.json').read_text())
    expected = {address for mission, address in checkpoints.values() if mission == parent}
    effects.complete_dependencies(owner, engine, party, parent)
    effects.complete_dependencies(owner, engine, party, parent)
    assert set(writes) == expected and len(writes) == len(expected)
    assert set(values.values()) == {'Completed'}
    assert set(owner._job['checked_prerequisites']) == {'travel_0', 'travel_1'}


def test_unfinished_parent_cannot_apply_travel_requirements(monkeypatch):
    owner, engine, party, writes, _ = context(monkeypatch)
    parent = 'Mission_Main_SearchForLilith'
    owner._row = lambda snapshot, name: 'active'
    with pytest.raises(RuntimeError, match='Complete'):
        effects.complete_dependencies(owner, engine, party, parent)
    assert not writes

def switch_context(monkeypatch, states=('TRUE', 'TRUE')):
    writes, events = [], []
    actors = [NS(FactsConduit=NS(RegistryName=NS(Name=NS(Name=name)),
                                  GroupName=NS(Name='Grasslands_ClaptrapSafeHouse')), state=state)
              for name, state in zip(effects.SAFEHOUSE_SWITCHES, states)]
    def write(**kw):
        actor = kw['OwnerContext']; writes.append(actor); actor.state = kw['StateValue'].Name
    lib = NS(GetActorStateValue=lambda **kw: (kw['OwnerContext'].state,),
             SetActorStateValue=write)
    monkeypatch.setitem(sys.modules, 'unrealsdk', NS(find_object=lambda *args: lib,
        find_all=lambda *args, **kw: actors, make_struct=lambda path, **kw: NS(**kw)))
    return actors, writes, events


def test_reopen_clears_both_retained_switches(monkeypatch):
    actors, writes, events = switch_context(monkeypatch)
    effects.reset_interactions(effects.SAFEHOUSE, events.append)
    assert writes == actors and [a.state for a in actors] == ['FALSE', 'FALSE']
    effects.reset_interactions(effects.SAFEHOUSE, events.append)
    assert len(writes) == 2


def test_console_replay_preserves_finished_datapad(monkeypatch):
    actors, writes, events = switch_context(monkeypatch)
    effects.reset_interactions(effects.SAFEHOUSE, events.append, 'claim_the_command_console')
    assert writes == actors[1:] and actors[0].state == 'TRUE'


def test_other_mission_leaves_switches_alone(monkeypatch):
    _, writes, events = switch_context(monkeypatch)
    effects.reset_interactions(effects.BEACH, events.append)
    assert not writes


def test_unknown_second_switch_aborts_before_first_write(monkeypatch):
    _, writes, events = switch_context(monkeypatch, ('TRUE', 'Unexpected'))
    with pytest.raises(RuntimeError, match='Unknown'):
        effects.reset_interactions(effects.SAFEHOUSE, events.append)
    assert not writes


def test_unloaded_switches_are_not_claimed_as_reset(monkeypatch):
    _, writes, events = switch_context(monkeypatch, ())
    sdk=sys.modules['unrealsdk']
    sdk.find_object=lambda *args: NS(ReadFact=lambda **kw:(None,'None'))
    monkeypatch.setitem(sys.modules,'mods_base',NS(get_pc=lambda:object()))
    effects.reset_interactions(effects.SAFEHOUSE, events.append)
    assert not writes and len(events) == 2
    assert all(e['event'] == 'stored_interaction_unchanged' for e in events)


def test_streamed_out_switches_reset_existing_facts(monkeypatch):
    _, _, events = switch_context(monkeypatch, ())
    values={f'registry.World_P.top.Grasslands_ClaptrapSafeHouse.{a}.Pressed':'TRUE'
            for a in effects.SAFEHOUSE_SWITCHES}
    writes=[]
    def write(**kw):
        writes.append(kw['AddressString']);values[kw['AddressString']]=kw['AsName']
    sdk=sys.modules['unrealsdk']
    sdk.find_object=lambda *args:NS(ReadFact=lambda **kw:(None,values[kw['AddressString']]),WriteFact=write)
    monkeypatch.setitem(sys.modules,'mods_base',NS(get_pc=lambda:object()))
    effects.reset_interactions(effects.SAFEHOUSE,events.append)
    assert set(values.values())=={'FALSE'} and len(writes)==2
    effects.reset_interactions(effects.SAFEHOUSE,events.append)
    assert len(writes)==2


def test_other_safehouse_console_replay_keeps_its_datapad(monkeypatch):
    import importlib.resources
    monkeypatch.setattr(importlib.resources, 'files', lambda package: PATH.parent)
    _, _, events = switch_context(monkeypatch, ())
    root = 'registry.World_P.top.City_MNT_Safehouse.'
    values = {root + 'CommandConsole_a.Pressed': 'TRUE', root + 'IO_Safehouse_DataLog.Pressed': 'TRUE'}
    writes = []
    def write(**kw):
        writes.append(kw['AddressString']); values[kw['AddressString']] = kw['AsName']
    sdk = sys.modules['unrealsdk']
    sdk.find_object = lambda *args: NS(ReadFact=lambda **kw: (None, values[kw['AddressString']]), WriteFact=write)
    monkeypatch.setitem(sys.modules, 'mods_base', NS(get_pc=lambda: object()))
    effects.reset_interactions('ZoneActivity_City_Safehouse2', events.append, 'claim_the_command_console')
    assert writes == [root + 'CommandConsole_a.Pressed']
    assert values[root + 'IO_Safehouse_DataLog.Pressed'] == 'TRUE'


def test_authored_interaction_and_completion_manifests_match_sources():
    import json, hashlib
    source_root = PATH.parents[2] / 'external_app/v22_parts_codes_fixed/matt_editor/LegitItems'
    cache = {}
    for filename in ('mission_replay_interactions.json', 'mission_completion_dependencies.json'):
        manifest = json.loads((PATH.parent / filename).read_text())
        for source, digest in manifest['source_sha256'].items():
            raw = (source_root / source).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == digest
            cache[source] = json.loads(raw)
        for name, definition in manifest['missions'].items():
            rows = definition['interactions'] if isinstance(definition, dict) else definition
            for row in rows:
                source = definition['source'] if isinstance(definition, dict) else row['source']
                value = cache[source]
                for key in row['pointer'].strip('/').split('/'):
                    value = value[int(key)] if isinstance(value, list) else value[key]
                if 'actor' in row:
                    assert value['subtype'] == 'Switch' and 'OakInteract' in value['structtype']
                else:
                    assert value['mission'] == "mission'" + row['mission'] + "'"
                    assert value.get('subtype') != 'ExternalObjective'

def test_activity_reset_uses_exact_alias_and_preserves_discovery(monkeypatch):
    import importlib.resources
    monkeypatch.setattr(importlib.resources, 'files', lambda package: PATH.parent)
    correct = NS(FactsConduit=NS(GroupName=NS(Name='P1_AugerMine'),
        RegistryName=NS(Name=NS(Name='P1_AugerMine'))), state='Claimed', discovered=True)
    other = NS(FactsConduit=NS(GroupName=NS(Name='OtherMine'),
        RegistryName=NS(Name=NS(Name='P1_AugerMine'))), state='Claimed', discovered=True)
    writes, events = [], []
    def write(**kw):
        writes.append(kw['OwnerContext']); kw['OwnerContext'].state=kw['StateValue'].Name
    lib = NS(GetActorStateMachineStates=lambda **kw: ([NS(Name='Initialization',Index=0),NS(Name='Claimed',Index=2)],),
             GetActorStateValue=lambda **kw: (kw['OwnerContext'].state,),SetActorStateValue=write)
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(find_all=lambda *args:[correct,other],
        find_object=lambda *args:lib,make_struct=lambda path,**kw:NS(**kw)))
    effects.reset_activity_state('ZoneActivity_Grasslands_Mine1',events.append)
    assert writes == [correct] and correct.state == 'Initialization'
    assert correct.discovered and other.discovered and other.state == 'Claimed'
    effects.reset_activity_state('ZoneActivity_Grasslands_Mine1',events.append)
    assert len(writes) == 1


def test_activity_catalog_has_no_templates_or_invented_actors():
    import json
    catalog=json.loads((PATH.parent/'mission_activity_actors.json').read_text())
    assert len(catalog)==63
    assert all('Template' not in name and row['actor']['map'] in ('World_P','Cowbell_P','Harmonica_P') for name,row in catalog.items())
    assert 'ZoneActivity_Shatteredlands_Crawler4' not in catalog  # source alias unresolved


@pytest.mark.parametrize('before',['Discovered','discovered','Claimed','claimable'])
def test_streamed_out_activity_preflight_is_read_only_and_reset_accepts_native_states(monkeypatch,before):
    import importlib.resources
    monkeypatch.setattr(importlib.resources,'files',lambda package:PATH.parent)
    value=[before];writes=[]
    def write(**kw):writes.append(kw);value[0]=kw['AsName'].lower()
    facts=NS(ReadFact=lambda **kw:(None,value[0]),WriteFact=write)
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(find_all=lambda *args:[],find_object=lambda *args:facts))
    monkeypatch.setitem(sys.modules,'mods_base',NS(get_pc=lambda:object()))
    effects.reset_activity_state('ZoneActivity_Grasslands_Silo1',lambda e:None,validate_only=True)
    assert value[0]==before and not writes
    effects.reset_activity_state('ZoneActivity_Grasslands_Silo1',lambda e:None)
    assert value[0]=='initialization' and len(writes)==1


def test_unknown_unloaded_second_switch_prevents_loaded_first_write(monkeypatch):
    actors,writes,events=switch_context(monkeypatch,('TRUE',))
    actor_lib=sys.modules['unrealsdk'].find_object('', '')
    sys.modules['unrealsdk'].find_object=lambda cls,*args: NS(ReadFact=lambda **kw:(None,'Unexpected')) if cls=='FactsBlueprintLibrary' else actor_lib
    monkeypatch.setitem(sys.modules,'mods_base',NS(get_pc=lambda:object()))
    with pytest.raises(RuntimeError,match='Unknown stored activity state'):
        effects.reset_interactions(effects.SAFEHOUSE,events.append)
    assert not writes and actors[0].state=='TRUE'


def test_campaign_checks_all_interactions_before_any_native_reset(monkeypatch):
    import importlib.resources
    monkeypatch.setattr(importlib.resources,'files',lambda _:PATH.parent)
    from types import ModuleType
    package=ModuleType('reset_preflight');package.__path__=[str(PATH.parent)]
    monkeypatch.setitem(sys.modules,'reset_preflight',package)
    spec=importlib.util.spec_from_file_location('reset_preflight.mission_reset',PATH.parent/'mission_reset.py')
    reset=importlib.util.module_from_spec(spec);spec.loader.exec_module(reset)
    calls=[];checked=[];memory={}
    engine=NS(profile='steam-25372571',base=0x100000000,ensure_world=lambda:None,check_build=lambda:None,u64=lambda p:memory[p])
    rows=[]
    for i,name in enumerate(['first','unsupported']):
        record=0x1000+i*0x1000;storage=record+0x300;fields=record+0x400;group=record+0x500
        memory.update({record:engine.base+0xb973820,record+0xa8:storage,storage+8:fields,
            fields:engine.base+0xb3f6810,engine.base+0xb3f6810+8:engine.base+0x61aaf4a,
            record+0x28:group,group:engine.base+0xb973a20})
        rows.append(dict(record=hex(record),storage=hex(storage),replication_type=0,source_identity=dict(name=name)))
    def validate(name,journal,*,validate_only=False):
        assert validate_only
        checked.append(name)
        if name=='unsupported':raise RuntimeError('Unknown activity')
    monkeypatch.setitem(sys.modules,'reset_preflight',NS())
    monkeypatch.setitem(sys.modules,'reset_preflight.mission_effects',NS(reset_activity_state=validate,reset_interactions=lambda *a,**kw:None))
    monkeypatch.setattr(reset.C,'WINFUNCTYPE',lambda *a:lambda address:lambda *args:calls.append((address,args)))
    with pytest.raises(RuntimeError,match='Unknown activity'):reset.reset_campaign(engine,rows,lambda e:None)
    assert checked==['first','unsupported'] and not calls
