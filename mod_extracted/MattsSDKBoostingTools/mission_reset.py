"""Native mission teardown/reset, traced from ResetRepeatableMission.

This restarts mission-local state, not inventory, rewards, world unlocks or the
whole character. The game may immediately activate a mission whose prerequisites
are satisfied. See 2026-10-12-objective-advancement.md.
"""
from .mission_native import native_address, native_fingerprint
import ctypes as C


def stage_checkpoint(engine, row, objective, checkpoint, journal, *, earlier=()):
    """Select and reset the native objective set without preceding outcomes.

    Recovered BL4 8905d9e updates the saved set and broadcasts its change;
    89069ca resets objectives whose authored end set is at/after the target,
    then refreshes the native dependencies. See the checkpoint handler receipt.
    """
    engine.ensure_world()
    engine.check_build()
    record, pointer = int(row['record'],16), int(objective['pointer'],16)
    # Use exact bytes captured from the supported executable, not an inferred
    # layout or a raw write to the saved cursor.
    select_bytes=bytes.fromhex('56574883ec2889d64889cfe8863564f84885c074214889c189f2e86f50f3ff48')
    rewind_bytes=bytes.fromhex('4157415641554154565755534881eca80000000f29b4249000000089d74889ce')
    if (row.get('generated') or row.get('replication_type')!=0 or
            engine.u64(record)!=native_address(engine, 0xb973820) or engine.u64(pointer)!=native_address(engine, 0xb973940) or
            engine.u64(pointer+0x28)!=record or
            engine.read(native_address(engine, 0x8905d9e),len(select_bytes))!=native_fingerprint(engine, 0x8905d9e, select_bytes) or
            engine.read(native_address(engine, 0x89069ca),len(rewind_bytes))!=native_fingerprint(engine, 0x89069ca, rewind_bytes)):
        raise RuntimeError('Direct checkpoint setup differs from the reviewed game build')
    import struct
    start,end=struct.unpack('<ii',engine.read(engine.u64(pointer+0x40)+0x3c,8))
    if not start <= checkpoint <= end:
        raise RuntimeError('Selected objective does not span this native checkpoint')
    # The native rewind intentionally leaves earlier sets alone. An interrupted
    # previous replay can therefore leave a past objective active. Cancel only
    # those live actions and settle their native status without success outcomes
    # or finish-action traversal. Validate the complete candidate set first.
    cancel_bytes=bytes.fromhex('564883ec204889cee8650000004889f1e81f0000004889f1e84b020000b9d001')
    status_bytes=bytes.fromhex('56534883ec2889d34889cee8300000004885c074224889c189dae8c9da270048')
    candidates=[]
    for previous in earlier:
        address=int(previous['pointer'],16)
        if (engine.u64(address)!=native_address(engine, 0xb973940) or engine.u64(address+0x28)!=record or
                engine.u64(native_address(engine, 0xb973940)+0xd0)!=native_address(engine, 0xdcb1dc) or
                engine.u64(native_address(engine, 0xb973940)+0xc8)!=native_address(engine, 0x105bc10) or
                engine.read(native_address(engine, 0xce3c18),len(cancel_bytes))!=native_fingerprint(engine, 0xce3c18, cancel_bytes) or
                engine.read(native_address(engine, 0xdcb1dc),len(status_bytes))!=native_fingerprint(engine, 0xdcb1dc, status_bytes) or
                struct.unpack('<i',engine.read(engine.u64(address+0x40)+0x40,4))[0]>=checkpoint):
            raise RuntimeError('Earlier replay objective identity or cancellation handler changed; no reset issued')
        candidates.append((previous,address))
    from .mission_effects import reset_interactions
    name=row['source_identity']['name']
    reset_interactions(name,journal,objective['name'],validate_only=True)
    reset_interactions(name,journal,objective['name'])
    journal(dict(event='checkpoint_activate_issued',mission=name,checkpoint=checkpoint))
    C.WINFUNCTYPE(None,C.c_void_p,C.c_uint8,C.c_bool)(native_address(engine, 0xf19ee4))(record,4,False)
    journal(dict(event='checkpoint_activate_returned'))
    if (engine.fact(engine.u64(record+0xa8),0x20) or {}).get('known_status')!='active':
        raise RuntimeError('Mission activation was not confirmed; checkpoint reset was not issued')
    journal(dict(event='checkpoint_cursor_issued',checkpoint=checkpoint))
    C.WINFUNCTYPE(None,C.c_void_p,C.c_int32)(native_address(engine, 0x8905d9e))(record,checkpoint)
    journal(dict(event='checkpoint_cursor_returned'))
    def verify_cursor():
        value=engine.fact(engine.u64(record+0xa8),0x60)
        if not value or value['tag']!=2 or struct.unpack('<i',bytes.fromhex(value['raw'])[12:16])[0]!=checkpoint:
            raise RuntimeError('Native checkpoint cursor was not confirmed; no call repeated')
    verify_cursor()
    states={engine.read(native_address(engine, rva),8).hex() for rva in (0xcb80870,0xcb80898,0xcb808a8,0xcb808a0)}
    completed=engine.read(native_address(engine, 0xcb808b0),8).hex()
    for previous,address in candidates:
        if engine.u64(address+0x28)!=record:raise RuntimeError('Earlier replay objective changed during staging')
        fact=engine.fact(engine.u64(address+0x48),0x20) or {}
        if fact.get('fname') not in states:continue
        journal(dict(event='checkpoint_prior_cancel_issued',objective=previous['name']))
        C.WINFUNCTYPE(None,C.c_void_p)(native_address(engine, 0xce3c18))(address)
        C.WINFUNCTYPE(None,C.c_void_p,C.c_uint8)(native_address(engine, 0xdcb1dc))(address,13)
        actual=engine.fact(engine.u64(address+0x48),0x20) or {}
        if actual.get('fname')!=completed:
            raise RuntimeError('Earlier replay objective cancellation was not confirmed; no call repeated')
        journal(dict(event='checkpoint_prior_cancel_returned',objective=previous['name']))
    verify_cursor()
    journal(dict(event='checkpoint_reset_issued',checkpoint=checkpoint))
    C.WINFUNCTYPE(None,C.c_void_p,C.c_int32)(native_address(engine, 0x89069ca))(record,checkpoint)
    journal(dict(event='checkpoint_reset_returned'))
    verify_cursor()


def reopen(engine, row, journal):
    engine.ensure_world()
    engine.check_build()
    record, storage = int(row['record'], 16), int(row['storage'], 16)
    if row.get('generated') or row.get('replication_type') != 0:
        raise ValueError('Reopening generated or nonshared missions is not supported')
    if (row.get('status_fact') or {}).get('known_status') not in ('completed','active','accepted'):
        raise ValueError('Choose a started mission to reopen')
    fields = engine.u64(storage + 8)
    if (engine.u64(record) != native_address(engine, 0xb973820) or
            engine.u64(record + 0xa8) != storage or
            engine.u64(fields) != native_address(engine, 0xb3f6810) or
            engine.u64(engine.u64(fields) + 8) != native_address(engine, 0x61aaf4a)):
        raise RuntimeError('Mission reset layout changed')
    # Pinned executable hash is checked by MissionRuntime; these functions are
    # the exact sequence in eebb94 after its repeatable-definition eligibility.
    from .mission_effects import reset_interactions, reset_activity_state
    reset_activity_state(row['source_identity']['name'], journal, validate_only=True)
    reset_interactions(row['source_identity']['name'], journal, validate_only=True)
    reset_activity_state(row['source_identity']['name'], journal)
    reset_interactions(row['source_identity']['name'], journal)
    for rva, arg in ((0x89062d0, record), (0x61aaf4a, fields), (0xce3150, record)):
        journal(dict(event='reset_component_issued', rva=hex(rva)))
        C.WINFUNCTYPE(None, C.c_void_p)(native_address(engine, rva))(arg)
        journal(dict(event='reset_component_returned', rva=hex(rva)))
    C.WINFUNCTYPE(None, C.c_void_p, C.c_uint8, C.c_bool)(native_address(engine, 0xf19ee4))(record, 1, True)


def reset_campaign(engine, rows, journal):
    """Reset shared mission groups and records together, before another game tick.

    Unlike individual replay, state 0 waits for the authored MissionSet graph.
    State 1 would let every mission evaluate its own prerequisites independently.
    """
    engine.ensure_world()
    engine.check_build()
    records, groups = [], set()
    for row in rows:
        if row.get('generated') or row.get('replication_type') != 0:
            raise ValueError('Campaign reset requires ordinary shared missions')
        record, storage = int(row['record'], 16), int(row['storage'], 16)
        fields, group = engine.u64(storage + 8), engine.u64(record + 0x28)
        if (engine.u64(record) != native_address(engine, 0xb973820) or
                engine.u64(record + 0xa8) != storage or
                engine.u64(fields) != native_address(engine, 0xb3f6810) or
                engine.u64(engine.u64(fields) + 8) != native_address(engine, 0x61aaf4a) or
                engine.u64(group) != native_address(engine, 0xb973a20)):
            raise RuntimeError('Campaign reset layout changed before any calls')
        records.append((row, record, fields))
        groups.add(group)
    from .mission_effects import reset_interactions, reset_activity_state
    for row, _, _ in records:
        name = row['source_identity']['name']
        reset_activity_state(name, journal, validate_only=True)
        reset_interactions(name, journal, validate_only=True)
    for group in sorted(groups):
        journal(dict(event='campaign_group_issued', group=hex(group)))
        C.WINFUNCTYPE(None, C.c_void_p, C.c_uint8)(native_address(engine, 0x3df1dfe))(group, 0)
        journal(dict(event='campaign_group_returned', group=hex(group)))
    for row, record, fields in records:
        name = row['source_identity']['name']
        journal(dict(event='campaign_record_issued', mission=name))
        reset_activity_state(name, journal)
        reset_interactions(name, journal)
        if (row.get('status_fact') or {}).get('known_status') in ('accepted','active','completed','failed'):
            C.WINFUNCTYPE(None, C.c_void_p)(native_address(engine, 0x89062d0))(record)
        C.WINFUNCTYPE(None, C.c_void_p)(native_address(engine, 0x61aaf4a))(fields)
        C.WINFUNCTYPE(None, C.c_void_p)(native_address(engine, 0xce3150))(record)
        C.WINFUNCTYPE(None, C.c_void_p, C.c_uint8, C.c_bool)(native_address(engine, 0xf19ee4))(record, 0, True)
        journal(dict(event='campaign_record_returned', mission=name))
