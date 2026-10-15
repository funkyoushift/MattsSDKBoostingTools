"""Captured mission/world timelines, retaining current character equipment."""
import copy
import hashlib
import re
import yaml
from mission_save_boundary import BoundaryError, canonical, entry, mapping, member, record, scalar_edit, span

FIELDS = ('missions', 'world_state', 'timed_facts')


def capture(text, spec):
    tree = yaml.compose(text)
    state = member(tree, 'state')
    if member(state, 'char_guid').value.replace('-', '').lower() != spec['guid']:
        raise BoundaryError('The saved character differs from the loaded character')
    chosen = []
    sets = member(member(tree, 'missions'), 'local_sets')
    for set_name, (_, value) in mapping(sets).items():
        if spec['mission'].casefold() in mapping(member(value, 'missions')):
            chosen.append(set_name)
    if len(chosen) != 1:
        raise BoundaryError('The tracked mission save is missing or ambiguous')
    spec = copy.deepcopy(spec)
    spec.update(mission_set=chosen[0], saved_mission=spec['mission'].casefold())
    station = member(state, 'checkpoint_name').value
    if not re.fullmatch(r'[A-Za-z0-9_]+\.[A-Za-z0-9_]+', station) or station.split('.')[0].casefold() != spec['section']['world'].casefold():
        raise BoundaryError('Wait until the game saves a respawn station on this map')
    spec['section']['station'] = station
    rec = record(tree, spec['mission_set'], spec['saved_mission'])
    cursor = mapping(rec).get('cursorposition')
    if member(rec, 'status').value != 'Active' or (int(cursor[1].value) if cursor else 0) != spec['section']['checkpoint']:
        raise BoundaryError('The mission has not saved this point yet; let autosave finish and try again')
    saved = mapping(member(rec, 'objectives'))
    if any(n.casefold() not in saved or member(saved[n.casefold()][1], 'status').value != 'Active'
           for n in spec['section']['initial_objectives']):
        raise BoundaryError('The saved objectives have not caught up with gameplay yet')
    roots = mapping(tree)
    fragments = {name: entry(text, *roots[name], 0) for name in FIELDS if name in roots}
    spec['captured_fields'] = list(fragments)
    snapshot = ''.join(f if f.endswith('\n') else f+'\n' for f in fragments.values())
    spec['snapshot_sha256'] = hashlib.sha256(snapshot.encode()).hexdigest()
    return dict(ok=True, spec=spec, snapshot=snapshot)


def edit(text, spec):
    snapshot = spec['bookmark_snapshot']
    if hashlib.sha256(snapshot.encode()).hexdigest() != spec['snapshot_sha256']:
        raise BoundaryError('Bookmark snapshot changed; no save edited')
    old, captured = yaml.compose(text), yaml.compose(snapshot)
    state = member(old, 'state')
    if member(state, 'char_guid').value.replace('-', '').lower() != spec['guid']:
        raise BoundaryError('This bookmark belongs to a different character')
    roots, reference = mapping(old), mapping(captured)
    if not reference or 'missions' not in reference or set(reference)-set(FIELDS) or spec.get('captured_fields') != list(reference):
        raise BoundaryError('Bookmark contains unsupported fields')
    rec = record(captured, spec['mission_set'], spec['saved_mission'])
    cursor = mapping(rec).get('cursorposition')
    if member(rec, 'status').value != 'Active' or (int(cursor[1].value) if cursor else 0) != spec['section']['checkpoint']:
        raise BoundaryError('Bookmark mission state differs from its selected objective')
    saved = mapping(member(rec, 'objectives'))
    if any(n.casefold() not in saved or member(saved[n.casefold()][1], 'status').value != 'Active'
           for n in spec['section']['initial_objectives']):
        raise BoundaryError('Bookmark active objectives differ from its selected objective')
    edits = []
    cleared = []
    for name in FIELDS:
        if name in roots and name not in reference:
            start, end = span(text, *roots[name])
            edits.append((start, end, ''))
            cleared.append(name)
    for name, pair in reference.items():
        if name not in roots:
            raise BoundaryError('The current save has no matching world field: '+name)
        start, end = span(text, *roots[name])
        fragment = entry(snapshot, *pair, 0)
        edits.append((start, end, fragment if fragment.endswith('\n') else fragment+'\n'))
    edits.append(scalar_edit(text, member(state, 'checkpoint_name'), spec['section']['station']))
    result = text
    for start, end, fragment in sorted(edits, reverse=True):
        result = result[:start]+fragment+result[end:]
    before, after = canonical(old), canonical(yaml.compose(result))
    def protected(value):
        value = copy.deepcopy(value)
        for name in FIELDS:
            value[1].pop(name, None)
        value[1]['state'][1].pop('checkpoint_name')
        return value
    if protected(before) != protected(after):
        raise BoundaryError('Bookmark would change character data')
    return dict(ok=True, yaml=result, receipt=dict(preserved_unowned_data=True,
                restored_fields=list(reference), cleared_fields=cleared, bookmark=True, world_effects_verified=False))
