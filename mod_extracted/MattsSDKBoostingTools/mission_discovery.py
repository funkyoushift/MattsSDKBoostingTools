"""Source-listed discovery RPCs and reviewed positive travel checkpoint repairs.

Called only inside mission_progression's pinned, journaled game-thread jobs.
Discovery does not imply every station is usable or every map tile revealed.
"""
import ctypes as C
import json
from importlib.resources import files

SCOPES = ('map_locations', 'travel_stations', 'travel_requirements')
CATALOG = json.loads(files(__package__).joinpath('discovery_catalog.json').read_text())
CHECKPOINTS = json.loads(files(__package__).joinpath('travel_checkpoints.json').read_text())


def plan(scope, snapshot, names=None):
    if scope not in SCOPES:
        raise ValueError('Unknown discovery scope')
    if scope == 'travel_requirements':
        entries = []
        for key, (parent, address) in CHECKPOINTS.items():
            rows = [r for r in snapshot['missions'] if (r['source_identity'] or {}).get('name') == parent]
            ready = len(rows) == 1 and not rows[0]['generated'] and rows[0]['replication_type'] == 0 and (rows[0]['status_fact'] or {}).get('known_status') == 'completed'
            entries.append(dict(name=key, title=address.rsplit('.', 1)[-1], category=scope,
                                state='parent completed' if ready else 'parent unfinished',
                                blocked_reason=None if ready else 'Complete ' + parent + ' first',
                                resets_host_completion=False, parent=parent, address=address))
    else:
        included = {r['gbx_discovery_location_meta_data'] for r in CATALOG
                    if scope == 'map_locations' or 'FastTravel' in r['locationtype']}
        by_name = {r['gbx_discovery_location_meta_data']: r for r in CATALOG}
        # Retain parent-before-child source ordering, including non-station parents.
        for name in list(included):
            parent = by_name[name]['parentlocation']
            visited = set()
            while parent not in (None, 'None', ''):
                if parent in visited or parent not in by_name:
                    raise ValueError('Invalid discovery parent chain')
                visited.add(parent); included.add(parent)
                parent = by_name[parent]['parentlocation']
        entries = [dict(name=r['gbx_discovery_location_meta_data'],
                        title=r['worldmapname'] + ' / ' + (r['travelstationdef'] if r['travelstationdef'] not in (None, 'None', '') else r['gbx_discovery_location_meta_data']),
                        category=scope, state='discover if needed', blocked_reason=None,
                        resets_host_completion=False) for r in CATALOG if r['gbx_discovery_location_meta_data'] in included]
    if names is not None:
        if not names or len(set(names)) != len(names) or set(names) - {r['name'] for r in entries}:
            raise ValueError('Unknown or duplicate discovery selection')
        entries = [r for r in entries if r['name'] in names]
        if scope != 'travel_requirements' and len(entries) != len(included):
            raise ValueError('Discovery requires the complete ordered parent chain')
    return entries


def operation(engine, scope, name, snapshot, target):
    """Prepare a checked call; caller journals before invoking mutate()."""
    import unrealsdk
    if scope == 'travel_requirements':
        row = next(r for r in plan(scope, snapshot, [name]) if r['name'] == name)
        if row['blocked_reason']:
            raise ValueError(row['blocked_reason'])
        facts = unrealsdk.find_object('FactsBlueprintLibrary', '/Script/GbxGame.Default__FactsBlueprintLibrary')
        def read():
            return str(facts.ReadFact(OwnerContext=target, AddressString=row['address'], AsName='None', AsInt=0, AsBool=False)[1]).casefold()
        before = read()
        if before not in ('none', 'completed'):
            raise ValueError('Unexpected existing travel checkpoint value')
        def mutate():
            if before != 'completed':
                facts.WriteFact(OwnerContext=target, AddressString=row['address'], AsName='Completed', AsInt=0, AsBool=False)
            return read()
        return before, mutate, lambda value: value == 'completed'
    from mods_base import get_pc
    pc = get_pc()
    cls = unrealsdk.find_object('ScriptStruct', '/Script/GbxGame.GbxDiscoveryLocationMetaData')
    enum = unrealsdk.find_enum('EGbxDiscoveryProximity').Discovered
    if int(enum) != 2:
        raise RuntimeError('Unexpected discovery enum')
    manager = engine.u64(pc._get_address() + 0x2200)
    if not manager:
        raise RuntimeError('Local discovery manager absent')
    key = unrealsdk.make_struct('/Script/GbxGame.GbxDiscoveryDiscoveredKey', AsMetaLocation=unrealsdk.unreal.FGbxDefPtr(name, cls))
    query = C.WINFUNCTYPE(C.c_int, C.c_void_p, C.c_void_p, C.c_int)(engine.base + 0x6bbfa4)
    before = query(manager, key._get_address(), 0)
    if before not in (0, 1, 2):
        raise RuntimeError('Unexpected discovery state')
    def mutate():
        if before < 2:
            pc.ServerDiscoveryMakeNonAuthoritativeDiscovery(key, enum)
        return query(manager, key._get_address(), 0)
    return before, mutate, lambda value: value == 2
