"""Grassroots and campaign unlock credit through the pinned mission callback.

Mission state and per-player once-only credit are separate native records.
See docs/changes/2026-10-11-grassroots-credit.md for recovered call/data evidence.
Never increment a counter directly or infer credit from the host's challenge.
"""
from .mission_native import native_address, native_fingerprint
import ctypes as C
import json
import struct
import time
from importlib.resources import files

DATA = json.loads(files(__package__).joinpath('mission_challenges.json').read_text())
MISSIONS = DATA['missions']
# Nexus-Data-challenge0.json: custom mission list, complete each mission once,
# one goal and exactly this mission. Runtime validates the actual definition,
# list ordering, once-only bits and native counter before issuing any event.
CAMPAIGN = DATA['campaign_unlock']
CREDIT_MISSIONS = (*MISSIONS, *CAMPAIGN['missions'])
MISSION_CREDIT_CATALOG = json.loads(files(__package__).joinpath('mission_credit_catalog.json').read_text())
MISSION_CREDIT_DEFINITIONS = {
    entry['challenge']:entry for entry in MISSION_CREDIT_CATALOG['entries']
}
MISSION_NAME_CANDIDATES = sorted({
    *(row['name'] for row in json.loads(files(__package__).joinpath('mission_catalog.json').read_text())),
    *(name for entry in MISSION_CREDIT_CATALOG['entries'] for name in entry['missions']),
})
# Steam 1.11 live readback found identical authored lists and coherent 7/15
# per-player counters/bitsets under these exact definition flags. The middle
# byte's meaning is not inferred. Each issued event still requires exact-bit
# and native-counter reconciliation before another can be sent.
CURRENT_HARMONICA_FLAGS = {
    'Challenges_Achievements_55_Harmonica_Activities',
    'Challenges_Achievements_56_Harmonica_SideMissions',
}
CALLBACK = 0xd17c02
FINGERPRINT = '4157415641554154565755534881ec280100004c89ce4c89c789d34989ce488b'


class CreditUncertain(RuntimeError):
    issued = True


class CreditReadbackMismatch(RuntimeError):
    """The existing credit records disagree before any new callback is issued."""


class CreditPending(RuntimeError):
    def __init__(self, receipt):
        super().__init__('Waiting for mission credit synchronization')
        self.receipt = receipt


def credit_definition(challenge):
    if challenge == DATA['challenge']:
        return DATA
    if challenge == CAMPAIGN['challenge']:
        return CAMPAIGN
    entry=MISSION_CREDIT_DEFINITIONS.get(challenge)
    if entry is None:
        raise ValueError('Unreviewed mission challenge definition')
    return dict(challenge=challenge,missions=entry['missions'])


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


def read_player(engine, pc, data=DATA):
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
    name = _name(engine, data['challenge'])
    definitions = [engine.u64(p+8) for p in sparse_entries(engine, manager+0x290,24,10000)
                   if engine.read(p,8)==name]
    if len(definitions)!=1:
        raise RuntimeError('Mission credit definition is missing or ambiguous')
    entry = definitions[0]
    definition = engine.u64(entry)
    mission_array,count = engine.array(definition+0x328,200)
    flags=engine.read(definition+0x320,3)
    accepted=(flags==b'\x01\x01\x01' or
              getattr(engine,'profile',None)=='steam-26007962' and
              data['challenge'] in CURRENT_HARMONICA_FLAGS and flags==b'\x01\x00\x01')
    if count!=len(data['missions']) or not accepted:
        raise RuntimeError('Mission credit counting rules changed')
    if any(engine.read(mission_array+i*24,8)!=_name(engine,n) for i,n in enumerate(data['missions'])):
        raise RuntimeError('Mission credit mission ordering changed')
    progress=[]
    for p in sparse_entries(engine,manager+0x3d8,96,16):
        if struct.unpack('<i',engine.read(p,4))[0]!=pid: continue
        progress.extend(engine.u64(q+8) for q in sparse_entries(engine,p+8,24,10000)
                        if engine.u64(q)==entry)
    if len(progress)!=1:
        raise RuntimeError('Mission credit player progress is missing or ambiguous')
    credits,n=engine.array(state+0x1300,10000)
    records=[credits+i*24 for i in range(n) if engine.read(credits+i*24,8)==name]
    if len(records)>1:
        raise RuntimeError('Duplicate mission credit records')
    credited=set()
    if records:
        words,nwords=engine.array(records[0]+8,64)
        values=struct.unpack('<'+'I'*nwords,engine.read(words,nwords*4)) if nwords else ()
        credited={i for i in range(len(data['missions'])) if i//32<len(values) and values[i//32] & (1 << (i%32))}
        if any(values[i//32] & (1 << (i%32)) for i in range(len(data['missions']), nwords*32)):
            raise RuntimeError('Mission credit includes an unknown mission')
    library=unrealsdk.find_object('OakChallengeBlueprintLibrary','/Script/OakGame.Default__OakChallengeBlueprintLibrary')
    count=int(library.GetChallengeProgressForPlayer(OakPC=pc,challenge=FGameDataHandle(16413,data['challenge'])))
    if count!=len(credited) or struct.unpack('<q',engine.read(progress[0],8))[0]!=count:
        raise CreditReadbackMismatch('Mission credit counter and per-mission credit disagree; wait for player synchronization')
    return dict(manager=manager,entry=entry,progress=progress[0],pid=pid,
                path=pc._path_name(),player=str(pc.PlayerState.PlayerNamePrivate),credited=credited,count=count)


def needs_credit(before, index):
    if before['count']!=len(before['credited']):
        raise RuntimeError('Challenge counter does not match mission credit')
    return index not in before['credited']


def verified(before, after, index):
    # Other missions can settle in the same game tick (including subordinate
    # authored completions). Preserve all prior credit and require this exact
    # mission's bit; a valid extra credit must not strand the shared batch.
    return (before['pid']==after['pid'] and before['path']==after['path']
            and after['credited'] >= before['credited'] | {index}
            and after['count']==len(after['credited'])
            and after['count']>before['count'])


def inspect_live_definition(engine, pc, challenge):
    """Read the loaded game's Mission list without inferring unknown FNames."""
    engine.ensure_world()
    if pc.OakChallengeManager is None or not pc.HasAuthority():
        raise RuntimeError('Authoritative challenge manager is not ready')
    manager=pc.OakChallengeManager._get_address()
    name=_name(engine,challenge)
    definitions=[engine.u64(p+8) for p in sparse_entries(engine,manager+0x290,24,10000)
                 if engine.read(p,8)==name]
    if len(definitions)!=1:
        raise RuntimeError('Mission credit definition is missing or ambiguous')
    definition=engine.u64(definitions[0])
    mission_array,count=engine.array(definition+0x328,200)
    flags=engine.read(definition+0x320,3)
    lookup={_name(engine,candidate):candidate for candidate in MISSION_NAME_CANDIDATES}
    names=[]
    for index in range(count):
        raw=engine.read(mission_array+index*24,8)
        names.append(lookup.get(raw) or dict(unresolved_fname=raw.hex()))
    return dict(count=count,flags=flags.hex(),missions=names,
                all_names_resolved=all(isinstance(item,str) for item in names))


def inspect_live_player_progress(engine, pc, challenge):
    """Read raw per-player Mission state even when its counting flags changed.

    These fields are diagnostic. In particular, set bits are not treated as
    once-only mission credit unless read_player has validated that rule.
    """
    import unrealsdk
    from unrealsdk.unreal import FGameDataHandle
    engine.ensure_world()
    if pc.PlayerState is None or pc.Pawn is None or pc.OakChallengeManager is None or not pc.HasAuthority():
        raise RuntimeError('Challenge player is not ready')
    manager=pc.OakChallengeManager._get_address()
    state=pc.PlayerState._get_address()
    pid=int(pc.PlayerState.PlayerId)
    if struct.unpack('<i',engine.read(state+0x394,4))[0]!=pid:
        raise RuntimeError('Challenge player identity differs from reflected identity')
    name=_name(engine,challenge)
    entries=[engine.u64(p+8) for p in sparse_entries(engine,manager+0x290,24,10000)
             if engine.read(p,8)==name]
    if len(entries)!=1:
        raise RuntimeError('Mission credit definition is missing or ambiguous')
    progress=[]
    for p in sparse_entries(engine,manager+0x3d8,96,16):
        if struct.unpack('<i',engine.read(p,4))[0]!=pid:continue
        progress.extend(engine.u64(q+8) for q in sparse_entries(engine,p+8,24,10000)
                        if engine.u64(q)==entries[0])
    if len(progress)!=1:
        raise RuntimeError('Mission credit player progress is missing or ambiguous')
    credits,n=engine.array(state+0x1300,10000)
    records=[credits+i*24 for i in range(n) if engine.read(credits+i*24,8)==name]
    if len(records)>1:
        raise RuntimeError('Duplicate mission credit records')
    words=[]
    if records:
        address,count=engine.array(records[0]+8,64)
        words=list(struct.unpack('<'+'I'*count,engine.read(address,count*4))) if count else []
    library=unrealsdk.find_object('OakChallengeBlueprintLibrary',
        '/Script/OakGame.Default__OakChallengeBlueprintLibrary')
    handle=FGameDataHandle(16413,challenge)
    return dict(player=str(pc.PlayerState.PlayerNamePrivate),player_id=pid,
                native_counter=int(library.GetChallengeProgressForPlayer(OakPC=pc,challenge=handle)),
                record_counter=struct.unpack('<q',engine.read(progress[0],8))[0],
                challenge_complete=bool(library.IsChallengeCompleteForPlayer(OakPC=pc,challenge=handle)),
                raw_record_present=bool(records),raw_bit_words=[hex(word) for word in words])


def inspect_mission_credit_catalog(engine, party, challenge_ids, definition_details=False):
    """Compare authored mission-credit lists with live per-player native records."""
    if not isinstance(challenge_ids,list) or not 1<=len(challenge_ids)<=8:
        raise ValueError('Inspect between one and eight mission challenge IDs')
    catalog=MISSION_CREDIT_CATALOG
    definitions=MISSION_CREDIT_DEFINITIONS
    results=[]
    for challenge in challenge_ids:
        if not isinstance(challenge,str) or challenge not in definitions:
            raise ValueError('Unknown authored mission challenge: '+str(challenge)[:80])
        entry=definitions[challenge]
        data=credit_definition(challenge)
        players=[]
        for row in party:
            try:
                native=read_player(engine,row['pc'],data)
            except (RuntimeError,ValueError) as exc:
                players.append(dict(player=row['label'],verified=False,error=str(exc)[:200]))
                continue
            players.append(dict(player=row['label'],verified=True,count=native['count'],
                                credited=[entry['missions'][i] for i in sorted(native['credited'])],
                                missing=[mission for i,mission in enumerate(entry['missions'])
                                         if i not in native['credited']]))
        result=dict(challenge=challenge,source_game_build=catalog['game_build'],
                    source=entry['source'],missions=entry['missions'],players=players)
        if definition_details:
            try:result['native_definition']=inspect_live_definition(engine,party[0]['pc'],challenge)
            except (RuntimeError,ValueError) as exc:
                result['native_definition']=dict(verified=False,error=str(exc)[:200])
            for index,row in enumerate(party):
                try:players[index]['raw_native_progress']=inspect_live_player_progress(
                    engine,row['pc'],challenge)
                except (RuntimeError,ValueError) as exc:
                    players[index]['raw_native_progress']=dict(verified=False,error=str(exc)[:200])
        results.append(result)
    return results


def reconcile(engine, party, receipt, journal):
    players=[r['pc'] for r in party if r['pc']._path_name()==receipt['player_path']
             and int(r['state'].PlayerId)==receipt['player_id']]
    if len(players)!=1:
        raise CreditUncertain('Challenge player changed before credit verification')
    try:
        try:data=credit_definition(receipt.get('challenge',DATA['challenge']))
        except ValueError as exc:raise CreditUncertain('Unreviewed mission challenge receipt') from exc
        after=read_player(engine,players[0]) if data is DATA else read_player(engine,players[0],data)
    except RuntimeError as exc:
        if time.time()-receipt['issued_at']<10:
            raise CreditPending(receipt) from exc
        raise CreditUncertain('Mission credit synchronization did not settle; inspect before retry') from exc
    before=dict(pid=receipt['player_id'],path=receipt['player_path'],
                count=receipt['before_count'],credited=set(receipt['before_credit']))
    if not verified(before,after,receipt['index']):
        if time.time()-receipt['issued_at']<10:
            raise CreditPending(receipt)
        raise CreditUncertain('Mission credit did not match the single missing mission')
    journal(dict(event='challenge_verified',**receipt,after_count=after['count']))
    return after


def credit_completed(engine, party, mission, journal, on_mismatch=None,challenge_id=None):
    data=credit_definition(challenge_id) if challenge_id else CAMPAIGN if mission in CAMPAIGN['missions'] else DATA
    if mission not in data['missions']:
        return []
    index=data['missions'].index(mission)
    receipts=[]
    for row in party:
        pc=row['pc']
        try:
            before=read_player(engine,pc) if data is DATA else read_player(engine,pc,data)
        except CreditReadbackMismatch as exc:
            if on_mismatch is None:
                raise
            item=dict(mission=mission,player_id=int(row['state'].PlayerId),
                      player_path=pc._path_name(),reason=str(exc))
            on_mismatch(item)
            receipts.append(dict(**item,unverified=True))
            continue
        if not needs_credit(before,index):
            receipts.append(dict(player=before['player'],count=before['count'],already_credited=True))
            continue
        if engine.read(native_address(engine, CALLBACK),32).hex()!=native_fingerprint(engine, CALLBACK, FINGERPRINT):
            raise RuntimeError('Mission credit native callback differs from supported build')
        # Native Mission event: type, mission FName, increment. The callback
        # sets the player's once-only bit and derives its total from those bits.
        event=C.create_string_buffer(0x400)
        event[0]=10
        struct.pack_into('<i',event,0x22c,1)
        C.memmove(C.addressof(event)+0x12c,_name(engine,mission),8)
        receipt=dict(operation='challenge_credit',mission=mission,player=before['player'],
                     challenge=data['challenge'],
                     player_id=before['pid'],player_path=before['path'],before_count=before['count'],
                     before_credit=sorted(before['credited']),issued_at=time.time(),index=index)
        journal(dict(event='issued',**receipt))
        try:
            C.WINFUNCTYPE(None,C.c_void_p,C.c_int,C.c_void_p,C.c_void_p,C.c_void_p)(native_address(engine, CALLBACK))(
                before['manager'],before['pid'],before['entry'],before['progress'],C.addressof(event))
            journal(dict(event='returned',**receipt,pending=True))
        except Exception as exc:
            raise CreditUncertain('Mission credit uncertain; inspect before retry: '+str(exc)) from exc
        # The native stat update is queued. Reconcile on a later game tick;
        # never issue the same callback while waiting for its count to settle.
        raise CreditPending(receipt)
    return receipts
