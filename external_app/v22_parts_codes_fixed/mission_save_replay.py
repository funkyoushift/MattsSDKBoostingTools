"""Pure desktop helpers. No filesystem mutation or game operations."""
from pathlib import Path
import hashlib
import re

import yaml
from mission_save_boundary import Boundary, BoundaryError, canonical, mapping, member, prepare, record


def identity(text):
    tree = yaml.compose(text)
    state = member(tree, 'state')
    guid = member(state, 'char_guid').value.replace('-', '').lower()
    if not re.fullmatch('[a-f0-9]{32}', guid):
        raise BoundaryError('Save has no valid character identity')
    return dict(guid=guid, name=member(state, 'char_name').value)


def edit(text, spec):
    if spec.get('kind') == 'selection':
        from mission_selection_state import edit as selection_edit
        return selection_edit(text, spec)
    if spec.get('kind') == 'bookmark':
        from mission_save_bookmarks import edit as bookmark_edit
        return bookmark_edit(text, spec)
    observed = Path(__file__).with_name('mission_save_observed.yaml').read_text(encoding='utf-8')
    if hashlib.sha256(observed.encode()).hexdigest() != spec['template_sha256']:
        raise BoundaryError('Mission reference data differs from this SDK build')
    section = spec['section']
    tree = yaml.compose(text)
    # This initial supported route has no reviewed descendants beyond SH3.
    # Preserve its parallel Mountains1 branch; do not treat chronology as ownership.
    allowed = {spec['mission_set'], *spec['parallel_mission_sets'],
               *(s for s, _ in spec['past_missions'])}
    sets = member(member(tree, 'missions'), 'local_sets')
    selected_missing = (spec['mission_set'] not in mapping(sets) or spec['saved_mission'] not in
        mapping(member(member(sets, spec['mission_set']), 'missions')))
    unreviewed = any(name.startswith('missionset_main_') and name not in allowed for name in mapping(sets))
    if (selected_missing or unreviewed) and spec.get('selection_fallback'):
        from mission_selection_state import edit as selection_edit
        return selection_edit(text, spec['selection_fallback'])
    for name in mapping(sets):
        if name.startswith('missionset_main_') and name not in allowed:
            raise BoundaryError('This character has other story progress without a reviewed reset rule; its save was not edited')
    boundary = Boundary(spec['mission_set'], spec['saved_mission'], section['checkpoint'],
                        section['station'], tuple(section['past_objectives']),
                        tuple(section['future_objectives']),
                        future_missions=tuple(tuple(v) for v in spec['future_missions']),
                        past_missions=tuple(tuple(v) for v in spec['past_missions']))
    candidate, receipt = prepare(text, observed, boundary)
    if identity(candidate) != identity(text):
        raise BoundaryError('Character identity changed')
    return dict(ok=True, yaml=candidate, receipt=receipt)


def inspect(text, spec):
    tree = yaml.compose(text)
    chosen = record(tree, spec['mission_set'], spec['saved_mission'])
    wanted = {n.casefold() for n in spec['section']['initial_objectives']}
    states = {k.casefold(): member(v, 'status').value
              for k, (_, v) in mapping(member(chosen, 'objectives')).items() if k.casefold() in wanted}
    cursor = mapping(chosen).get('cursorposition')
    # BL4 omits a zero cursor on native save. Its getter f494f8 returns zero
    # when the fact is absent; live Crystal Brawl opening confirmed the case.
    return dict(**identity(text), cursor=int(cursor[1].value) if cursor else 0,
                mission_status=member(chosen, 'status').value, objectives=states)


def dispatch(payload):
    action = payload['action']
    if action == 'bookmark_capture':
        from mission_save_bookmarks import capture
        return capture(payload['yaml'], payload['spec'])
    if action == 'identity':
        return dict(ok=True, **identity(payload['yaml']))
    if action == 'edit':
        return edit(payload['yaml'], payload['spec'])
    if action == 'inspect':
        return dict(ok=True, **inspect(payload['yaml'], payload['spec']))
    raise ValueError('Unsupported replay helper operation')
