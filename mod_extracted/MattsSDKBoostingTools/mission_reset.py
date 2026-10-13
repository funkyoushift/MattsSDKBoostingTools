"""Native mission teardown/reset, traced from ResetRepeatableMission.

This restarts mission-local state, not inventory, rewards, world unlocks or the
whole character. The game may immediately activate a mission whose prerequisites
are satisfied. See 2026-10-12-objective-advancement.md.
"""
import ctypes as C


def reopen(engine, row, journal):
    engine.ensure_world()
    engine.check_build()
    record, storage = int(row['record'], 16), int(row['storage'], 16)
    if row.get('generated') or row.get('replication_type') != 0:
        raise ValueError('Reopening generated or nonshared missions is not supported')
    if (row.get('status_fact') or {}).get('known_status') not in ('completed','active','accepted'):
        raise ValueError('Choose a started mission to reopen')
    fields = engine.u64(storage + 8)
    if (engine.u64(record) != engine.base + 0xb973820 or
            engine.u64(record + 0xa8) != storage or
            engine.u64(fields) != engine.base + 0xb3f6810 or
            engine.u64(engine.u64(fields) + 8) != engine.base + 0x61aaf4a):
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
        C.WINFUNCTYPE(None, C.c_void_p)(engine.base + rva)(arg)
        journal(dict(event='reset_component_returned', rva=hex(rva)))
    C.WINFUNCTYPE(None, C.c_void_p, C.c_uint8, C.c_bool)(engine.base + 0xf19ee4)(record, 1, True)


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
        if (engine.u64(record) != engine.base + 0xb973820 or
                engine.u64(record + 0xa8) != storage or
                engine.u64(fields) != engine.base + 0xb3f6810 or
                engine.u64(engine.u64(fields) + 8) != engine.base + 0x61aaf4a or
                engine.u64(group) != engine.base + 0xb973a20):
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
        C.WINFUNCTYPE(None, C.c_void_p, C.c_uint8)(engine.base + 0x3df1dfe)(group, 0)
        journal(dict(event='campaign_group_returned', group=hex(group)))
    for row, record, fields in records:
        name = row['source_identity']['name']
        journal(dict(event='campaign_record_issued', mission=name))
        reset_activity_state(name, journal)
        reset_interactions(name, journal)
        if (row.get('status_fact') or {}).get('known_status') in ('accepted','active','completed','failed'):
            C.WINFUNCTYPE(None, C.c_void_p)(engine.base + 0x89062d0)(record)
        C.WINFUNCTYPE(None, C.c_void_p)(engine.base + 0x61aaf4a)(fields)
        C.WINFUNCTYPE(None, C.c_void_p)(engine.base + 0xce3150)(record)
        C.WINFUNCTYPE(None, C.c_void_p, C.c_uint8, C.c_bool)(engine.base + 0xf19ee4)(record, 0, True)
        journal(dict(event='campaign_record_returned', mission=name))
