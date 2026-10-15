"""Packaged replay boundary editing. Never writes or loads a native save.

Restore earlier outcomes from an observed save, clear selected/later outcomes,
and leave every unowned field unchanged. This is not a save-cache unload API.
"""
from __future__ import annotations

from dataclasses import dataclass
import copy
import json
import yaml
from yaml.tokens import ScalarToken, FlowMappingStartToken, FlowMappingEndToken


class BoundaryError(ValueError):
    pass


@dataclass(frozen=True)
class Boundary:
    mission_set: str
    mission: str
    checkpoint: int
    station: str
    past_objectives: tuple[str, ...]
    future_objectives: tuple[str, ...]
    # Explicit reviewed records, including other story branches if requested.
    future_missions: tuple[tuple[str, str], ...] = ()
    past_missions: tuple[tuple[str, str], ...] = ()


def mapping(node):
    if not isinstance(node, yaml.MappingNode):
        raise BoundaryError('Expected a native mapping')
    result = {}
    for key, value in node.value:
        if not isinstance(key, yaml.ScalarNode) or key.value in result:
            raise BoundaryError('Non-scalar or duplicate save key')
        result[key.value] = (key, value)
    return result


def member(node, key):
    try:
        return mapping(node)[key][1]
    except KeyError as exc:
        raise BoundaryError('Missing observed save field: ' + key) from exc


def canonical(node):
    if isinstance(node, yaml.MappingNode):
        # Also reject duplicate keys in protected data.
        return (node.tag, {k: canonical(v) for k, (_, v) in mapping(node).items()})
    if isinstance(node, yaml.SequenceNode):
        return (node.tag, [canonical(v) for v in node.value])
    return (node.tag, node.value)


def span(text, key, value):
    start = text.rfind('\n', 0, key.start_mark.index) + 1
    end = value.end_mark.index
    line = text.rfind('\n', 0, end) + 1
    if not text[line:end].strip():
        end = line
    return start, end


def entry(text, key, value, indent):
    start, end = span(text, key, value)
    fragment = text[start:end]
    delta = indent - key.start_mark.column
    lines = fragment.splitlines(keepends=True)
    if delta >= 0:
        return ''.join(' ' * delta + line if line.strip() else line for line in lines)
    prefix = ' ' * -delta
    if any(line.strip() and not line.startswith(prefix) for line in lines):
        raise BoundaryError('Unsupported indentation in observed record')
    return ''.join(line[-delta:] if line.strip() else line for line in lines)


def record(tree, set_name, mission):
    sets = member(member(tree, 'missions'), 'local_sets')
    return member(member(member(sets, set_name), 'missions'), mission)


def rebuild(text, node, keep, additions):
    """Replace one mapping value, retaining original field spelling and tags."""
    values = mapping(node)
    if node.flow_style and values:
        raise BoundaryError('Nonempty flow records are not supported for editing')
    line = text[text.rfind('\n', 0, node.start_mark.index) + 1:node.start_mark.index]
    indent = next(iter(values.values()))[0].start_mark.column if values else len(line) - len(line.lstrip()) + 2
    fragments = [entry(text, key, value, indent)
                 for name, (key, value) in values.items() if name in keep]
    fragments.extend(entry(source, key, value, indent) for source, key, value in additions)
    result = ''.join(f if f.endswith('\n') else f + '\n' for f in fragments)
    if not values:
        tokens = list(yaml.scan(text[node.start_mark.index:node.end_mark.index]))
        opening = next(t for t in tokens if isinstance(t, FlowMappingStartToken))
        closing = next(t for t in tokens if isinstance(t, FlowMappingEndToken))
        replacement = '\n' + result.rstrip('\n') if result else '{}'
        return (node.start_mark.index + opening.start_mark.index,
                node.start_mark.index + closing.end_mark.index, replacement)
    first_key = next(iter(values.values()))[0]
    last_key, last_value = list(values.values())[-1]
    # Preserve a tag preceding the mapping's first key.
    return (first_key.start_mark.index, span(text, last_key, last_value)[1],
            result[indent:] if result else '{}\n')


def scalar_edit(text, node, replacement):
    if not isinstance(node, yaml.ScalarNode):
        raise BoundaryError('Expected a scalar checkpoint field')
    tokens = [t for t in yaml.scan(text[node.start_mark.index:node.end_mark.index])
              if isinstance(t, ScalarToken)]
    if len(tokens) != 1:
        raise BoundaryError('Ambiguous scalar representation')
    token = tokens[0]
    rendered = json.dumps(replacement) if token.style == '"' else "'" + replacement.replace("'", "''") + "'" if token.style == "'" else replacement
    return (node.start_mark.index + token.start_mark.index,
            node.start_mark.index + token.end_mark.index, rendered)


def prepare(current: str, observed: str, boundary: Boundary):
    """Return YAML plus a compact receipt; missing past evidence stops staging.

    Earlier composite children may be deactivated rather than completed. Their
    exact observed terminal outcomes are restored, never guessed from names.
    Future takes precedence for reused objectives spanning both sides.
    """
    if not isinstance(boundary.checkpoint, int) or isinstance(boundary.checkpoint, bool) or boundary.checkpoint < 0:
        raise BoundaryError('Invalid checkpoint')
    if not boundary.station or any(c in boundary.station for c in '\r\n:#{}[]'):
        raise BoundaryError('Invalid native station')
    past = {n.casefold() for n in boundary.past_objectives}
    future = {n.casefold() for n in boundary.future_objectives}
    past -= future
    selected = (boundary.mission_set, boundary.mission)
    if selected in boundary.future_missions or selected in boundary.past_missions:
        raise BoundaryError('Selected mission cannot be replaced wholesale')
    if set(boundary.future_missions) & set(boundary.past_missions):
        raise BoundaryError('Conflicting earlier/later mission ownership')
    tree, reference = yaml.compose(current), yaml.compose(observed)
    before = canonical(tree)
    rec, old = record(tree, *selected), record(reference, *selected)
    current_status = member(rec, 'status')
    if current_status.value not in ('Active', 'completed') or member(old, 'status').value != 'Active':
        raise BoundaryError('Selected mission needs observed active-state evidence')
    edits, repaired = [], []
    if current_status.value == 'completed':
        edits.append(scalar_edit(current, current_status, 'Active'))
    removed_fields = {}
    for field in ('objectives', 'final'):
        node, prior = member(rec, field), member(old, field)
        values, reference_values = mapping(node), mapping(prior)
        def objective(name):
            return name.casefold().removesuffix('_endstate') if field == 'final' else name.casefold()
        for collection in (values, reference_values):
            normalized = [objective(n) for n in collection]
            if len(set(normalized)) != len(normalized):
                raise BoundaryError('Conflicting case-insensitive objective evidence')
        keep = {n for n in values if objective(n) not in future | past}
        unknown = [n for n in values if objective(n) not in future | past]
        if unknown:
            raise BoundaryError('Objective has no reviewed boundary ownership: ' + unknown[0])
        removed_fields[field] = [n for n in values if objective(n) in future]
        additions = []
        evidence = {objective(n): (k, v) for n, (k, v) in reference_values.items()}
        for name in sorted(past):
            if field == 'final' and name not in evidence:
                # Not every authored objective remembers an end-state fact.
                continue
            if name not in evidence:
                raise BoundaryError('Missing earlier objective evidence: ' + name)
            key, value = evidence[name]
            status = member(value, 'status').value if field == 'objectives' else value.value
            terminal = ('Completed_PostFinished', 'Deactivated_PostFinished') if field == 'objectives' else ('completed', 'deactivated')
            if status not in terminal:
                raise BoundaryError('Earlier outcome is not observed terminal: ' + name)
            additions.append((observed, key, value))
            if key.value not in values or canonical(values[key.value][1]) != canonical(value):
                repaired.append(field + ':' + key.value)
        edits.append(rebuild(current, node, keep, additions))
    sets = member(member(tree, 'missions'), 'local_sets')
    owned_sets = {s for s, _ in boundary.future_missions + boundary.past_missions}
    if boundary.mission_set in owned_sets:
        raise BoundaryError('Other owned records in the selected set require a combined template')
    for set_name in sorted(owned_sets):
        earlier = {m for s, m in boundary.past_missions if s == set_name}
        later = {m for s, m in boundary.future_missions if s == set_name}
        if set_name not in mapping(sets):
            if earlier:
                source_sets = member(member(reference, 'missions'), 'local_sets')
                key, value = mapping(source_sets).get(set_name, (None, None))
                if key is None or set(mapping(member(value, 'missions'))) != earlier:
                    raise BoundaryError('Earlier mission-set template has unowned records: ' + set_name)
                for mission in earlier:
                    if member(record(reference, set_name, mission), 'status').value != 'completed':
                        raise BoundaryError('Earlier mission is not observed completed: ' + mission)
                last_key, last_value = list(mapping(sets).values())[-1]
                end = span(current, last_key, last_value)[1]
                fragment = entry(observed, key, value, last_key.start_mark.column)
                edits.append((end, end, fragment if fragment.endswith('\n') else fragment + '\n'))
            continue
        missions = member(member(sets, set_name), 'missions')
        values = mapping(missions)
        keep = set(values) - earlier - later
        additions = []
        for mission in sorted(earlier):
            prior = record(reference, set_name, mission)
            if member(prior, 'status').value != 'completed':
                raise BoundaryError('Earlier mission is not observed completed: ' + mission)
            prior_missions = member(member(member(member(reference, 'missions'), 'local_sets'), set_name), 'missions')
            prior_key, prior_value = mapping(prior_missions)[mission]
            additions.append((observed, prior_key, prior_value))
        if keep or additions:
            edits.append(rebuild(current, missions, keep, additions))
        else:
            key, value = mapping(sets)[set_name]
            if set(mapping(value)) == {'missions'}:
                start, end = span(current, key, value)
                edits.append((start, end, ''))
            else:
                edits.append(rebuild(current, missions, set(), []))
    cursor = member(rec, 'cursorposition')
    station = member(member(tree, 'state'), 'checkpoint_name')
    edits.extend([scalar_edit(current, cursor, str(boundary.checkpoint)),
                  scalar_edit(current, station, boundary.station)])
    patched, last = current, len(current) + 1
    for start, end, replacement in sorted(edits, reverse=True):
        if not 0 <= start <= end <= last:
            raise BoundaryError('Overlapping replay edits')
        last = start
        patched = patched[:start] + replacement + patched[end:]
    after = canonical(yaml.compose(patched))
    def protected(value):
        value = copy.deepcopy(value)
        del value[1]['state'][1]['checkpoint_name']
        local = value[1]['missions'][1]['local_sets'][1]
        chosen = local[boundary.mission_set][1]['missions'][1][boundary.mission][1]
        for field in ('objectives', 'final', 'cursorposition', 'status'):
            del chosen[field]
        for set_name, mission in boundary.future_missions + boundary.past_missions:
            if set_name in local:
                local[set_name][1]['missions'][1].pop(mission, None)
                if not local[set_name][1]['missions'][1] and set(local[set_name][1]) == {'missions'}:
                    del local[set_name]
        return value
    if protected(before) != protected(after):
        raise BoundaryError('Unowned character or world data changed')
    return patched, {'checkpoint': boundary.checkpoint, 'repaired_past_fields': repaired,
                     'cleared_objectives': sorted(future), 'preserved_unowned_data': True,
                     'removed_saved_fields': removed_fields,
                     'selected_mission_reopened': current_status.value == 'completed',
                     'world_effects_verified': False, 'installed': False}
