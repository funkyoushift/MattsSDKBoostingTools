"""Grassroots credit through the build-pinned per-mission challenge callback.

Mission state and per-player once-only credit are separate native records.
See docs/changes/2026-10-11-grassroots-credit.md for recovered call/data evidence.
Never increment a counter directly or infer credit from the host's challenge.
"""
import ctypes as C
import json
import struct
import time
from importlib.resources import files

DATA = json.loads(files(__package__).joinpath('mission_challenges.json').read_text())
MISSIONS = DATA['missions']
CALLBACK = 0xd17c02
FINGERPRINT = '4157415641554154565755534881ec280100004c89ce4c89c789d34989ce488b'


class CreditUncertain(RuntimeError):
    issued = True


class CreditPending(RuntimeError):
    def __init__(self, receipt):
        super().__init__('Waiting for Grassroots credit synchronization')
        self.receipt = receipt


def sparse_entries(engine, address, stride, maximum):
    data, count = engine.array(address, maximum)
    bits, capacity = struct.unpack('<ii', engine.read(address + 0x28, 8))
    if bits != count or not 0 <= bits <= capacity <= max(128, maximum * 2):
        raise RuntimeError('Challenge map allocation layout changed')
    source = engine.u64(address + 0x20) or address + 0x10
    allocation = engine.read(source, ((count + 31)//32)*4) if count else b''
    return [data + i*stride for i in range(count) if allocation[i//8] & (1 << (i%8))]


def _name(engine, name):
    import unrealsdk
    token = unrealsdk.make_struct('/Script/CoreUObject.SToken', Name=name)
    return engine.read(token._get_address()+4, 8)


def read_player(engine, pc):
    import unrealsdk
    from unrealsdk.unreal import FGameDataHandle
    engine.ensure_world()
    if pc.PlayerState is None or pc.Pawn is None or pc.OakChallengeManager is None or not pc.HasAuthority():
        raise RuntimeError('Challenge player is not ready')
    manager = pc.OakChallengeManager._get_address()
    state = pc.PlayerState._get_address()
    pid = int(pc.PlayerState.PlayerId)
    if struct.unpack('<i', engine.read(state+0x394,4))[0] != pid:
        raise RuntimeError('Challenge player identity differs from reflected identity')
    name = _name(engine, DATA['challenge'])
    definitions = [engine.u64(p+8) for p in sparse_entries(engine, manager+0x290,24,10000)
                   if engine.read(p,8)==name]
    if len(definitions)!=1:
        raise RuntimeError('Grassroots definition is missing or ambiguous')
    entry = definitions[0]
    definition = engine.u64(entry)
    data,count = engine.array(definition+0x328,200)
    if count!=len(MISSIONS) or engine.read(definition+0x320,3)!=b'\x01\x01\x01':
        raise RuntimeError('Grassroots counting rules changed')
    if any(engine.read(data+i*24,8)!=_name(engine,n) for i,n in enumerate(MISSIONS)):
        raise RuntimeError('Grassroots mission ordering changed')
    progress=[]
    for p in sparse_entries(engine,manager+0x3d8,96,16):
        if struct.unpack('<i',engine.read(p,4))[0]!=pid: continue
        progress.extend(engine.u64(q+8) for q in sparse_entries(engine,p+8,24,10000)
                        if engine.u64(q)==entry)
    if len(progress)!=1:
        raise RuntimeError('Grassroots player progress is missing or ambiguous')
    credits,n=engine.array(state+0x1300,10000)
    records=[credits+i*24 for i in range(n) if engine.read(credits+i*24,8)==name]
    if len(records)>1:
        raise RuntimeError('Duplicate Grassroots credit records')
    credited=set()
    if records:
        words,nwords=engine.array(records[0]+8,64)
        values=struct.unpack('<'+'I'*nwords,engine.read(words,nwords*4)) if nwords else ()
        credited={i for i in range(len(MISSIONS)) if i//32<len(values) and values[i//32] & (1 << (i%32))}
        if any(values[i//32] & (1 << (i%32)) for i in range(len(MISSIONS), nwords*32)):
            raise RuntimeError('Grassroots credit includes an unknown mission')
    library=unrealsdk.find_object('OakChallengeBlueprintLibrary','/Script/OakGame.Default__OakChallengeBlueprintLibrary')
    count=int(library.GetChallengeProgressForPlayer(OakPC=pc,challenge=FGameDataHandle(16413,DATA['challenge'])))
    if count!=len(credited) or struct.unpack('<q',engine.read(progress[0],8))[0]!=count:
        raise RuntimeError('Grassroots counter and per-mission credit disagree; wait for player synchronization')
    return dict(manager=manager,entry=entry,progress=progress[0],pid=pid,
                path=pc._path_name(),player=str(pc.PlayerState.PlayerNamePrivate),credited=credited,count=count)


def needs_credit(before, index):
    if before['count']!=len(before['credited']):
        raise RuntimeError('Challenge counter does not match mission credit')
    return index not in before['credited']


def verified(before, after, index):
    return (before['pid']==after['pid'] and before['path']==after['path']
            and after['credited']==before['credited'] | {index}
            and after['count']==before['count']+1)


def reconcile(engine, party, receipt, journal):
    players=[r['pc'] for r in party if r['pc']._path_name()==receipt['player_path']
             and int(r['state'].PlayerId)==receipt['player_id']]
    if len(players)!=1:
        raise CreditUncertain('Challenge player changed before credit verification')
    try:
        after=read_player(engine,players[0])
    except RuntimeError as exc:
        if time.time()-receipt['issued_at']<10:
            raise CreditPending(receipt) from exc
        raise CreditUncertain('Grassroots synchronization did not settle; inspect before retry') from exc
    before=dict(pid=receipt['player_id'],path=receipt['player_path'],
                count=receipt['before_count'],credited=set(receipt['before_credit']))
    if not verified(before,after,receipt['index']):
        if time.time()-receipt['issued_at']<10:
            raise CreditPending(receipt)
        raise CreditUncertain('Grassroots credit did not match the single missing mission')
    journal(dict(event='challenge_verified',**receipt,after_count=after['count']))
    return after


def credit_completed(engine, party, mission, journal):
    if mission not in MISSIONS:
        return []
    index=MISSIONS.index(mission)
    receipts=[]
    for row in party:
        pc=row['pc']
        before=read_player(engine,pc)
        if not needs_credit(before,index):
            receipts.append(dict(player=before['player'],count=before['count'],already_credited=True))
            continue
        if engine.read(engine.base+CALLBACK,32).hex()!=FINGERPRINT:
            raise RuntimeError('Grassroots native callback differs from supported build')
        # Native Mission event: type, mission FName, increment. The callback
        # sets the player's once-only bit and derives its total from those bits.
        event=C.create_string_buffer(0x400)
        event[0]=10
        struct.pack_into('<i',event,0x22c,1)
        C.memmove(C.addressof(event)+0x12c,_name(engine,mission),8)
        receipt=dict(operation='challenge_credit',mission=mission,player=before['player'],
                     player_id=before['pid'],player_path=before['path'],before_count=before['count'],
                     before_credit=sorted(before['credited']),issued_at=time.time(),index=index)
        journal(dict(event='issued',**receipt))
        try:
            C.WINFUNCTYPE(None,C.c_void_p,C.c_int,C.c_void_p,C.c_void_p,C.c_void_p)(engine.base+CALLBACK)(
                before['manager'],before['pid'],before['entry'],before['progress'],C.addressof(event))
            journal(dict(event='returned',**receipt,pending=True))
        except Exception as exc:
            raise CreditUncertain('Grassroots credit uncertain; inspect before retry: '+str(exc)) from exc
        # The native stat update is queued. Reconcile on a later game tick;
        # never issue the same callback while waiting for its count to settle.
        raise CreditPending(receipt)
    return receipts
