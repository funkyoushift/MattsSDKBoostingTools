"""Purchase authored SDU ranks through the game's progression graph.

Private node identities/costs are read only, pinned by MissionRuntime's executable
hash and the native GetProgressGraphNodeTotalPoints code fingerprint. The native
reader matches FName at node+0x48 or its definition at node+0x50. Node order is
never inferred from the extracted JSON. See the completion/UI verification note.
"""
import json
import struct
import threading
import time
from importlib.resources import files

import unrealsdk

CATALOG = json.loads(files(__package__).joinpath('sdu_catalog.json').read_text())


def snapshot(pc, runtime):
    if threading.get_ident() != runtime.thread:
        raise RuntimeError('SDU work must run on the game thread')
    runtime.ensure_world()
    expected = bytes.fromhex(CATALOG['native_reader_fingerprint'])
    if runtime.read(runtime.base + int(CATALOG['native_reader_rva'], 16), len(expected)) != expected:
        raise RuntimeError('Unsupported SDU native reader')
    from . import player_economy
    character = player_economy._target_character_for_pc(pc)
    if character is None:
        raise RuntimeError('SDU target character is unavailable')
    graphs = [g for g in character.GbxProgressionManager.ProgressGraphs
              if str(g.ProgressGraphDef._name).casefold() == 'sdu_upgrades']
    if len(graphs) != 1:
        raise RuntimeError('Expected one SDU progression graph')
    graph = graphs[0]
    tokens = {}
    for item in CATALOG['nodes']:
        ref = unrealsdk.make_struct('/Script/GbxGame.GbxUnlockableNodeRef', NodeName=item['name'])
        tokens[runtime.read(ref._get_address() + 24, 8)] = item
    nodes = list(graph.nodes)
    if not 0 < len(nodes) <= 128:
        raise RuntimeError('Unexpected SDU node count')
    rows = {}
    for index, node in enumerate(nodes):
        address = node._get_address()
        definition = runtime.u64(address + 0x50)
        alias = runtime.read(address + 0x48, 8)
        key = runtime.read(definition, 8) if definition else None
        item = tokens.get(alias) or tokens.get(key)
        if item is None:
            continue
        if item['name'] in rows or not definition:
            raise RuntimeError('Ambiguous SDU node identity')
        # Native total-points reader checks this bool and signed cost at +8/+12.
        cost = struct.unpack('<i', runtime.read(definition + 12, 4))[0]
        if runtime.read(definition + 8, 1) != b'\x01' or cost != item['cost']:
            raise RuntimeError('SDU cost differs from authored data: ' + item['name'])
        spent = int(node.ProgressPointsSpent)
        if not 0 <= spent <= cost or int(node.BonusPoints) != 0:
            raise RuntimeError('Unsupported SDU point state: ' + item['name'])
        rows[item['name']] = dict(item, index=index, spent=spent,
                                 active=bool(node.bIsActivated), unlocked=bool(node.bIsUnlocked))
    if set(rows) != {n['name'] for n in CATALOG['nodes']}:
        raise RuntimeError('SDU graph does not match the authored paid ranks')
    return graph, rows


def advance(pc, runtime, state):
    """At most one purchase per call; wait for it before issuing another.

    Keep pending before dispatch, including on exceptions, so recovery never
    repeats a request whose outcome is uncertain. All state is serializable.
    """
    graph, rows = snapshot(pc, runtime)
    pending = state.get('pending')
    if pending:
        row = rows[pending['name']]
        if row['active'] and row['spent'] == row['cost']:
            state.pop('pending')
        elif time.time() - pending['issued_at'] > 10:
            raise RuntimeError('SDU purchase not confirmed: ' + row['name'] + '; request not repeated')
        else:
            return False
    remaining = [r for r in rows.values() if not r['active']]
    state.update(completed=len(rows) - len(remaining), total=len(rows))
    if not remaining:
        state['verified'] = True
        return True
    available = [r for r in remaining if r['unlocked'] and r['spent'] < r['cost']]
    if not available:
        raise RuntimeError('Remaining SDU ranks are locked; no forced activation attempted')
    row = available[0]
    state['pending'] = dict(name=row['name'], issued_at=time.time())
    graph.Server_SpendProgressPoints(InNodeIndex=row['index'], InPoints=row['cost'] - row['spent'])
    return False
