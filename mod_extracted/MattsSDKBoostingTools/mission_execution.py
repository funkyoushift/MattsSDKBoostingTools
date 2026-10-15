"""Shared native objective processing for completion and practice.

The native successful-outcome handler executes success/finish graphs. A mission
status shortcut cannot stand in for those graphs. Calls are recorded before
issue and never repeated, including while finish actions wait on game ticks.
"""
from .mission_native import native_address, native_fingerprint
import ctypes as C
import json
import struct
import time
from importlib.resources import files

DATA = json.loads(files(__package__).joinpath('mission_practice_catalog.json').read_text(encoding='utf-8'))['missions']
OUTCOME_RVA = 0x3df18e0
OUTCOME_BYTES = '4157415641545657534883ec3889d3488b054ae090084831e04889442430488b'
# Native NPC travel and staged dialogue can take over two minutes even while
# functioning normally. Keep a bounded wait without interrupting/reissuing it.
FINISH_TIMEOUT = 360.


def coverage_error(name, checkpoint=None, definition=None):
    """Validate authored identity before any acceptance, reset or outcome.

    Missing coordinates only limit placement. Missing/ambiguous objective
    definitions limit execution, even when that objective is not active yet.
    """
    definition = DATA.get(name) if definition is None else definition
    if not definition or not definition.get('groups'):
        return 'Authored objective graph is unavailable for ' + name
    indexes = set()
    for group in definition['groups']:
        index = group['index']
        if index in indexes:
            return 'Duplicate authored objective group in ' + name
        indexes.add(index)
        if checkpoint is not None and index > checkpoint:
            continue
        declared = {}
        for obj in group['objectives']:
            key = str(obj.get('name', '')).casefold()
            if not key or obj.get('unresolved'):
                return 'Objective definition is unresolved: ' + str(obj.get('name', name))
            if key in declared and declared[key] != obj:
                return 'Ambiguous authored objective identity: ' + obj['name']
            declared[key] = obj
    if checkpoint is not None and checkpoint not in indexes:
        return 'Selected objective group is absent from authored data'
    return None


def require_coverage(name, checkpoint=None, definition=None):
    reason = coverage_error(name, checkpoint, definition)
    if reason:
        raise RuntimeError(reason)


def objectives(engine, row, definition):
    from .mission_objectives import read
    rows = read(engine, row)
    declared = {}
    for group in definition['groups']:
        for order, obj in enumerate(group['objectives']):
            key = obj['name'].casefold()
            memberships = declared.setdefault(key, [])
            # Authored groups may repeat the exact same definition reference.
            # Preserve the first order; conflicting definitions remain ambiguous.
            if not any(index == group['index'] and source == obj for index, _, source in memberships):
                memberships.append((group['index'], order, obj))
    for obj in rows:
        match = declared.get(obj['name'].casefold())
        if match is None:
            if obj['state'] in (4, 10, 11, 12):
                raise RuntimeError('Active objective is missing from authored data: ' + obj['name'])
            continue
        native = struct.unpack('<i', engine.read(engine.u64(int(obj['pointer'], 16) + 0x40) + 0x40, 4))[0]
        matches = [entry for entry in match if entry[0] == native]
        if not matches:
            raise RuntimeError('Authored objective groups differ from this game build')
        if len(matches) != 1:
            raise RuntimeError('Ambiguous authored objective identity; no outcome issued')
        group, order, source = matches[0]
        if source.get('unresolved') and obj['state'] in (4, 10, 11, 12):
            raise RuntimeError('Objective definition is unresolved: ' + obj['name'])
        obj.update(group=group, order=order, optional=bool(source.get('optional')),
                   completion_maps=source.get('completion_maps') or
                       ([source['scene_anchor']['map'].casefold()] if source.get('scene_anchor') else []),
                   travel_map=source.get('travel_map'),
                   activation_by_arrival=bool(source.get('activation_by_arrival')),
                   completion_anchor=source.get('completion_anchor'),scene_anchor=source.get('scene_anchor'),
                   encounter_scene=source.get('encounter_scene'),
                   wait_for_objectives=source.get('wait_for_objectives'),
                   interaction=source.get('interaction'))
    return rows


def required_tokens(rows, issued, checkpoint=None):
    """Include active trackers' explicit children, even if authored optional.

    Optional alternatives cease to be candidates when their native parent is
    deactivated. Already issued work still has to settle before moving on.
    """
    required={o['token'] for o in rows if 'group' in o and not o['optional']} | set(issued)
    by_name={o['name'].casefold():o for o in rows if 'group' in o}
    pending=[o for o in rows if o['token'] in required and o['state'] in (4,10,11,12)
             and (checkpoint is None or o.get('group',checkpoint)<checkpoint)]
    visited=set()
    while pending:
        parent=pending.pop()
        if parent['token'] in visited:continue
        visited.add(parent['token'])
        for name in parent.get('wait_for_objectives') or []:
            child=by_name.get(name.casefold())
            if child is None:raise RuntimeError('Required child objective is unavailable: '+name)
            required.add(child['token'])
            if child['state'] in (4,10,11,12):pending.append(child)
    return required


def advance(engine, row, name, receipt, journal, checkpoint=None, definition=None,
            current_map=None, before_outcome=None, selected_token=None):
    """Issue at most one outcome; return readiness and a user-facing message.

    checkpoint=None completes through normal mission activation. Otherwise the
    requested group remains active, and prior required finish work must settle.
    The receipt belongs to one mission token and retains all issued outcomes.
    """
    definition = DATA.get(name) if definition is None else definition
    require_coverage(name, checkpoint, definition)
    if receipt.get('token', row['token']) != row['token']:
        raise RuntimeError('Mission instance changed; no objective call repeated')
    receipt.setdefault('token', row['token'])
    issued = receipt.setdefault('issued', [])
    rows = objectives(engine, row, definition)
    required=required_tokens(rows,issued,checkpoint)
    selected_objective = None
    if selected_token is not None:
        selected_objective = next((o for o in rows if o['token']==selected_token and 'group' in o), None)
        if selected_objective is None:
            raise RuntimeError('Selected objective is unavailable; no other objective advanced')
        # A composite completes through its explicitly authored children. Limit
        # work to that dependency tree, never to unrelated siblings/later steps.
        required = {selected_token} | set(issued)
        by_name = {o['name'].casefold():o for o in rows if 'group' in o}
        # A composite definition can span authored sections while its native
        # group field names only the last one (Crystal Brawl's wildcat).
        # Include arrival setup from every section declaring this composite.
        # Retain these initializer outcomes; exclude optional and visible
        # siblings so selecting one objective never completes another section.
        memberships = {group['index'] for group in definition['groups']
                       if any(obj['name'].casefold() == selected_objective['name'].casefold()
                              for obj in group['objectives'])}
        initializers = [o for o in rows if selected_objective.get('wait_for_objectives')
                        and o.get('group') in memberships
                        and o['hidden'] and not o['optional'] and o.get('activation_by_arrival')]
        required.update(o['token'] for o in initializers)
        pending = [selected_objective] + initializers
        visited = set()
        while pending:
            parent = pending.pop()
            if parent['token'] in visited:continue
            visited.add(parent['token'])
            for child_name in parent.get('wait_for_objectives') or []:
                child = by_name.get(child_name.casefold())
                if child is None:raise RuntimeError('Required child objective is unavailable: '+child_name)
                required.add(child['token']);pending.append(child)
    active = [o for o in rows if o['state'] == 4 and 'group' in o and o['token'] in required]
    relevant = [o for o in rows if 'group' in o and o['token'] in required and
                (checkpoint is None or o['group'] < checkpoint)]
    # Even hidden required objectives and non-issued natural finish actions must
    # settle. An issued token disappearing is not success while its mission runs.
    present = {o['token']: o for o in rows}
    unsettled = [o for o in relevant if o['state'] in (10, 11, 12) or
                 (o['token'] in issued and o['state'] != 13)]
    missing_issued = any(token not in present for token in issued)
    waiting = bool(unsettled) or missing_issued
    if selected_objective is not None and selected_objective['state']==13 and not waiting:
        return dict(ready=True, message='Selected objective finished its normal actions; other objectives were left for gameplay.')
    if checkpoint is not None:
        # Mission stages can overlap. An authored hidden arrival trigger can
        # activate this stage's visible encounter while a later navigation
        # objective is already displayed. Leave that trigger for gameplay.
        reached = any(o['group'] == checkpoint for o in active)
        if not reached and any(o['group'] > checkpoint and not o['hidden'] for o in active):
            raise RuntimeError('The game advanced beyond the requested checkpoint')
        if reached and not waiting and not any(o['group'] < checkpoint for o in active):
            return dict(ready=True, message='Selected objective is active and prior finish actions settled.')
    candidates = [o for o in active if o['token'] not in issued and not o.get('wait_for_objectives') and
                  (checkpoint is None or o['group'] < checkpoint)]
    if waiting:
        # Native graphs can keep one objective finishing while activating a
        # sibling needed by that graph (for example the hidden console hits in
        # The Rescue). Advance those distinct active siblings, but never leave
        # their map or jump to a later group while prior work is unsettled.
        limit = min((o['group'] for o in unsettled), default=-1)
        candidates = [o for o in candidates if not missing_issued and not o['optional'] and o['group'] <= limit and
                      (not o.get('completion_maps') or current_map in o['completion_maps'])]
    if not candidates and not waiting and before_outcome:
        # A visible composite can stay active while its interaction child waits
        # for another map to load. It has no leaf outcome to reach the ordinary
        # before_outcome travel guard yet. Load only a source-declared child map;
        # never force its activation or complete the composite itself.
        child_names={n.casefold() for parent in active for n in parent.get('wait_for_objectives',[])}
        map_children=[o for o in rows if o['token'] in required and o['name'].casefold() in child_names and
                      o['state'] in (None,3,4) and o.get('completion_maps') and current_map and
                      current_map not in o['completion_maps'] and
                      (checkpoint is None or o['group']<checkpoint)]
        if map_children:
            child=min(map_children,key=lambda o:(o['group'],o['order']))
            before_outcome(child)
            return dict(ready=False,message='Loading the area needed by this objective.')
    if candidates:
        # An overarching map-arrival objective can coexist with work on the
        # current map. Settle that work before departing, within the same group.
        selected = min(candidates, key=lambda o: (o['group'],
                       bool(current_map and o.get('completion_maps') and current_map not in o['completion_maps']),
                       o['hidden'], o['order']))
        # Sibling finish dependencies may run in the existing scene; moving
        # away while an earlier finish graph owns it can strand that graph.
        selected['finish_actions_pending']=waiting
        if before_outcome is not None and not before_outcome(selected):
            return dict(ready=False,await_map=True,message='Preparing the mission scene for '+selected['name'].replace('_',' ')+'.')
        interaction=None
        if selected.get('interaction'):
            from .mission_interactions import prepare
            interaction=prepare(selected)
            if interaction is False:
                since=receipt.setdefault('progress_at',time.monotonic())
                if time.monotonic()-since>120:
                    raise RuntimeError('The required NPC interaction did not become available; no outcome forced')
                return dict(ready=False,message='Waiting for the required NPC interaction to load; no outcome forced.')
        if interaction is None and engine.read(native_address(engine, OUTCOME_RVA), 32).hex() != native_fingerprint(engine, OUTCOME_RVA, OUTCOME_BYTES):
            raise RuntimeError('Objective handler differs from the reviewed build')
        issued.append(selected['token'])
        receipt['pending'] = selected['token']
        journal(dict(event='issued', operation='objective_complete', mission=name,
                     before=row, objective=dict(selected),via='npc_use' if interaction else 'outcome'))
        try:
            if interaction:interaction()
            else:C.WINFUNCTYPE(None, C.c_void_p, C.c_uint8)(native_address(engine, OUTCOME_RVA))(int(selected['pointer'], 16), 1)
            journal(dict(event='returned', operation='objective_complete', mission=name,
                         token=row['token'], objective=dict(selected),via='npc_use' if interaction else 'outcome'))
        except Exception as exc:
            error = RuntimeError('Objective outcome is unconfirmed; inspect its receipt before continuing')
            error.issued = True
            raise error from exc
        receipt.pop('pending')
        receipt['progress_at'] = time.monotonic()
        return dict(ready=False, issued=True, message=('Used the required NPC interaction for ' if interaction else 'Advancing ')
                    + selected['name'].replace('_', ' ') + '; waiting for normal finish actions.')
    elif waiting:
        message = 'Waiting for objective finish actions; no outcome call repeated.'
    else:
        message = 'Waiting for normal mission/objective activation.'
    since = receipt.setdefault('progress_at', time.monotonic())
    if time.monotonic() - since > (FINISH_TIMEOUT if waiting else 120):
        raise RuntimeError(message + ' The mission needs inspection before this run continues.')
    return dict(ready=False, message=message)
