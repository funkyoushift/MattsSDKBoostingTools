"""Player-facing sections; execution keeps the complete authored graph."""
import json
from functools import lru_cache
from importlib.resources import files
from pathlib import Path


@lru_cache(maxsize=1)
def replay_sections():
    source = files(__package__) if __package__ else Path(__file__).parent
    return json.loads(source.joinpath('mission_replay_sections.json').read_text(encoding='utf-8'))['missions']


def guide_groups(name, definition, rule):
    """Resolve reviewed guide boundaries without changing native execution."""
    groups = {g['index']: g for g in definition['groups']}
    sections = rule['sections']
    indices = [s['checkpoint'] for s in sections]
    first = rule.get('entry_checkpoint', min(groups))
    skipped = [g for i,g in groups.items() if i < first]
    if (not indices or indices != sorted(set(indices)) or indices[0] != first
            or any(not o.get('hidden') for g in skipped for o in g['objectives'])):
        raise ValueError('Replay section order differs from its reviewed mission')
    resolved = []
    for position, section in enumerate(sections):
        group = groups.get(section['checkpoint'])
        objective = next((o for o in (group or {}).get('objectives', [])
                          if o['name'] == section['objective']), None)
        if objective is None:
            raise ValueError('Replay section source changed: ' + name + ' / ' + section['objective'])
        end = indices[position + 1] - 1 if position + 1 < len(indices) else max(groups)
        for checkpoint, names in section.get('required_objectives', {}).items():
            step = groups.get(int(checkpoint), {})
            if not group['index'] <= step.get('index', -1) <= end or not set(names) <= {o['name'] for o in step.get('objectives', [])}:
                raise ValueError('Replay section source changed: ' + name)
        selected = dict(group, replay_end_index=end)
        if 'end_anchor_checkpoint' in section:
            anchor_group = groups.get(section['end_anchor_checkpoint'], {})
            anchor = anchor_group.get('start_anchor')
            if not group['index'] <= anchor_group.get('index', -1) <= end or not anchor:
                raise ValueError('Replay section return point changed: ' + name)
            selected['replay_end_anchor'] = anchor
        resolved.append((selected, dict(objective, title=section['title'])))
    return resolved


def main_groups(name, definition):
    groups = definition['groups']
    reviewed = replay_sections().get(name)
    if reviewed:
        yield from guide_groups(name, definition, reviewed)
        return
    seen = set()
    for group in groups:
        visible = [o for o in group['objectives'] if not o.get('hidden') and not o.get('optional')]
        children = {n.casefold() for o in visible for n in o.get('wait_for_objectives') or []}
        roots = [o for o in visible if o['name'].casefold() not in children]
        if not roots:
            continue
        repeated = any(o['name'].casefold() in seen for o in roots)
        seen.update(o['name'].casefold() for o in roots)
        if repeated:
            continue
        # A persistent player-facing tracker defines the larger section when
        # it shares a group with its internal tasks. Never collapse by title.
        counts = {o['name']: sum(any(p['name'].casefold() == o['name'].casefold()
                                    for p in g['objectives']) for g in groups) for o in roots}
        primary = max(roots, key=lambda o: counts[o['name']])
        yield group, primary
