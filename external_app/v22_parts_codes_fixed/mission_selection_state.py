"""Experimental authored progress overrides, preserving unrelated save data.

Unlike bookmarks, these are requested edits, not captured playthrough states.
The game initializes the selected/current/future objectives after a fresh reload.
"""
import copy
import re
from pathlib import Path
import yaml
from mission_save_boundary import BoundaryError, canonical, mapping, member, rebuild, scalar_edit


def scalar(value):
    return yaml.ScalarNode('tag:yaml.org,2002:str', str(value))


def native_mapping(values=()):
    return yaml.MappingNode('tag:yaml.org,2002:map', [(scalar(k), v) for k, v in values])


def put(node, key, value):
    entries = mapping(node)
    if key in entries:
        old, _ = entries[key]
        node.value = [(k, value if k is old else v) for k, v in node.value]
    else:
        node.value.append((scalar(key), value))


def remove(node, key):
    node.value = [(k, v) for k, v in node.value if k.value != key]


def edit(text, spec):
    if spec.get('kind') != 'selection':
        raise BoundaryError('Not an authored mission selection')
    section = spec['section']
    checkpoint = section['checkpoint']
    if type(checkpoint) is not int or checkpoint < 0:
        raise BoundaryError('Invalid selected objective')
    active = section.get('restore_active_objectives', [])
    if (active and (checkpoint != 0 or section.get('station_selection') != 'authored mission entry'
            or not set(active).issubset(section.get('initial_objectives', []))
            or set(active) & set(section['past_objectives'])
            or any(not isinstance(n, str) or not re.fullmatch(r'[a-z0-9_]+', n) for n in active))):
        raise BoundaryError('Invalid initial travel-objective state')
    tree = yaml.compose(text)
    before = canonical(tree)
    missions = member(tree, 'missions')
    local = copy.deepcopy(member(missions, 'local_sets'))
    selected = (spec['mission_set'], spec['saved_mission'])
    past = {tuple(v) for v in spec['past_missions']}
    future = {tuple(v) for v in spec['future_missions']}
    if selected in past | future or past & future:
        raise BoundaryError('Conflicting story dependency ownership')
    station_flags = spec['section'].get('station_prerequisites', [])
    for flag in station_flags:
        owner = (flag['mission_set'], flag['mission'])
        if (owner not in past | {selected} or not re.fullmatch(r'[a-z0-9_]+', flag['objective'])
                or owner == selected and flag['objective'] not in section['past_objectives']):
            raise BoundaryError('Respawn station would require future or unrelated objective progress')
    observed = yaml.compose(Path(__file__).with_name('mission_save_observed.yaml').read_text(encoding='utf-8'))
    observed_sets = mapping(member(member(observed, 'missions'), 'local_sets'))
    observed_rec = None
    if selected[0] in observed_sets:
        observed_records = mapping(member(observed_sets[selected[0]][1], 'missions'))
        if selected[1] in observed_records:
            observed_rec = observed_records[selected[1]][1]
    for set_name, mission in sorted(future):
        if set_name not in mapping(local):
            continue
        group = member(local, set_name)
        remove(member(group, 'missions'), mission)
        remove(group, 'status')
        if not mapping(member(group, 'missions')):
            # A completed chained set can retain a cursor pointing at a
            # removed future mission. The game recreates that mission on load.
            remove(group, 'cursorposition')
        if not mapping(member(group, 'missions')) and set(mapping(group)) == {'missions'}:
            remove(local, set_name)
    for set_name, mission in [*sorted(past), selected]:
        if set_name not in mapping(local):
            put(local, set_name, native_mapping([('missions', native_mapping())]))
        group = member(local, set_name)
        records = member(group, 'missions')
        if mission not in mapping(records):
            put(records, mission, native_mapping())
        rec = member(records, mission)
        if (set_name, mission) == selected:
            remove(group, 'status')
            # A chained set can still point at the next mission even after
            # its selected mission's own cursor is rewound. Let the game
            # rebuild that set position from the edited mission records.
            remove(group, 'cursorposition')
            put(rec, 'status', scalar('Active'))
            put(rec, 'cursorposition', yaml.ScalarNode('tag:yaml.org,2002:int', str(checkpoint)))
            put(rec, 'final', native_mapping())
            # Intentional completion override for strictly earlier authored
            # objectives. Reused objectives stay unset for native initialization.
            put(rec, 'objectives', native_mapping((name, native_mapping([
                ('status', scalar('Completed_PostFinished'))])) for name in section['past_objectives']))
            for name in active:
                put(member(rec, 'objectives'), name, native_mapping([('status', scalar('Active'))]))
            if observed_rec is not None:
                observed_fields = mapping(observed_rec)
                for name, (_, value) in mapping(observed_fields.get('objectives', (None, native_mapping()))[1]).items():
                    if name in section['past_objectives'] and member(value, 'status').value in ('Completed_PostFinished', 'Deactivated_PostFinished'):
                        put(member(rec, 'objectives'), name, copy.deepcopy(value))
                for name, (_, value) in mapping(observed_fields.get('final', (None, native_mapping()))[1]).items():
                    if name.removesuffix('_endstate') in section['past_objectives']:
                        put(member(rec, 'final'), name, copy.deepcopy(value))
        else:
            put(rec, 'status', scalar('completed'))
            remove(rec, 'cursorposition')
            remove(rec, 'objectives')
            if 'final' not in mapping(rec):
                put(rec, 'final', native_mapping())
    # Some native travel destinations check an objective's completed flag even
    # when its mission is completed. Preserve only source-declared station gates
    # in the owned past timeline; never unlock future or parallel objectives.
    for flag in station_flags:
        rec = member(member(member(local, flag['mission_set']), 'missions'), flag['mission'])
        if 'objectives' not in mapping(rec):
            put(rec, 'objectives', native_mapping())
        objectives = member(rec, 'objectives')
        if flag['objective'] not in mapping(objectives):
            put(objectives, flag['objective'], native_mapping())
        put(member(objectives, flag['objective']), 'status', scalar('Completed_PostFinished'))
        if 'final' not in mapping(rec):
            put(rec, 'final', native_mapping())
        put(member(rec, 'final'), flag['objective'] + '_endstate', scalar('completed'))
    # A completed set is needed for authored MissionSet dependencies. Do not
    # mark a shared selected/future set completed just because a sibling is past.
    for set_name in {s for s, _ in past} - {selected[0]} - {s for s, _ in future}:
        group = member(local, set_name)
        if all(member(v, 'status').value == 'completed' for _, v in mapping(member(group, 'missions')).values()):
            put(group, 'status', scalar('completed'))
    old_local = member(missions, 'local_sets')
    # Serialize only the owned mapping; surrounding native tags/text are kept.
    fragment = yaml.serialize(local)
    fragment_tree = yaml.compose('local_sets:\n' + ''.join('  '+line+'\n' for line in fragment.splitlines()))
    fragment_node = member(fragment_tree, 'local_sets')
    additions = [('local_sets:\n' + ''.join('  '+line+'\n' for line in fragment.splitlines()), k, v)
                 for k, v in fragment_node.value]
    start, end, value = rebuild(text, old_local, set(), additions)
    station = member(member(tree, 'state'), 'checkpoint_name')
    edits = [(start, end, value), scalar_edit(text, station, section['station'])]
    result = text
    for start, end, value in sorted(edits, reverse=True):
        result = result[:start] + value + result[end:]
    after = canonical(yaml.compose(result))
    def protected(value):
        value = copy.deepcopy(value)
        value[1]['missions'][1].pop('local_sets')
        value[1]['state'][1].pop('checkpoint_name')
        return value
    if protected(before) != protected(after):
        raise BoundaryError('Selection would change protected character/world data')
    # Within local_sets, preserve every unowned mission and set metadata.
    future_sets = {set_name for set_name, _ in future}
    def unowned(value):
        value = copy.deepcopy(value)
        for set_name, mission in past | future | {selected}:
            if set_name in value[1]:
                group = value[1][set_name][1]
                group.pop('status', None)
                if set_name == selected[0]:
                    group.pop('cursorposition', None)
                group['missions'][1].pop(mission, None)
                if set_name in future_sets and not group['missions'][1]:
                    group.pop('cursorposition', None)
                if not group['missions'][1] and set(group) == {'missions'}:
                    del value[1][set_name]
        return value
    if unowned(canonical(old_local)) != unowned(canonical(member(member(yaml.compose(result), 'missions'), 'local_sets'))):
        raise BoundaryError('Selection would change an unrelated mission')
    return dict(ok=True, yaml=result, receipt=dict(preserved_unowned_data=True,
        filled_prerequisites=len(past), cleared_future_missions=len(future),
        filled_station_objectives=len(station_flags),
        authored_progress_override=True, world_effects_verified=False,
        warning='Experimental generated progress; world facts and encounter initialization need gameplay testing.'))
