"""Build-pinned read-only DLC query recovered from DLCEntitlementValueResolver.

RVA 8d09f1a resolves a DLC reference via 156a95a and checks actor access via
125f73e. This uses the player's entitlement store, not shared world facts.
No entitlement flags or ownership records are assigned.
"""
from .mission_native import native_address, native_fingerprint
import ctypes as C
import json
from importlib.resources import files
DATA=json.loads(files(__package__).joinpath('full_progress_content.json').read_text())


def inspect(engine, rows):
    import unrealsdk
    engine.ensure_world()
    for rva,expected in DATA['fingerprints'].items():
        if engine.read(native_address(engine, int(rva,16)),32).hex()!=native_fingerprint(engine, int(rva,16), expected):
            raise RuntimeError('DLC access query differs from the reviewed game build')
    resolve=C.WINFUNCTYPE(C.c_void_p,C.c_void_p)(native_address(engine, 0x156a95a))
    query=C.WINFUNCTYPE(C.c_bool,C.c_void_p,C.c_void_p)(native_address(engine, 0x125f73e))
    result={}
    for key,definition in DATA['packs'].items():
        token=unrealsdk.make_struct('/Script/CoreUObject.SToken',Name=definition['definition'])
        ref=C.create_string_buffer(24)
        C.memmove(C.addressof(ref),token._get_address()+4,8)
        C.memmove(C.addressof(ref)+8,b'dlc\0\0\0\0\0',8)
        address=resolve(C.addressof(ref))
        players=[]
        for row in rows:
            pc=row['pc']
            if pc is None or pc.PlayerState._get_address()!=row['state']._get_address():
                raise RuntimeError('DLC query player identity changed')
            allowed=bool(query(pc._get_address(),address)) if address else None
            players.append(dict(player=row['label'],player_id=int(row['state'].PlayerId),access='enabled' if allowed else 'missing' if allowed is False else 'unknown'))
        blocked=[p['player'] for p in players if p['access']!='enabled']
        result[key]=dict(title=definition['title'],allowed=not blocked,players=players,
                         blocking_players=blocked,required=key not in ('raid1','raid2','tuba'),
                         reason='Access unavailable or unconfirmed: '+', '.join(blocked) if blocked else 'All players have access')
    return result
