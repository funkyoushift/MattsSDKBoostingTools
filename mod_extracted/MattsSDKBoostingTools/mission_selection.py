"""Player-facing sections; execution keeps the complete authored graph."""


def main_groups(name, definition):
    groups = definition['groups']
    # Martin confirmed the vehicle sequence is one replay section. Check the
    # source boundaries so an updated catalog cannot silently reuse this range.
    vehicle = name == 'Mission_Main_Shatteredlands3'
    if vehicle:
        by_index = {g['index']: g for g in groups}
        vehicle = (any(o['name'] == 'GetOnDrill' for o in by_index.get(12, {}).get('objectives', [])) and
                   any(o['name'] == 'ReturnRamp' for o in by_index.get(22, {}).get('objectives', [])))
    seen = set()
    mountain_office = name == 'Mission_Main_Mountains1' and any(
        g['index'] == 12 and any(o['name'] == 'MTN1_Reach_Calders_Office' for o in g['objectives']) for g in groups) and any(
        g['index'] == 24 and any(o['name'] == 'Office_Reached_Breadcrumb' for o in g['objectives']) for g in groups)
    for group in groups:
        visible = [o for o in group['objectives'] if not o.get('hidden') and not o.get('optional')]
        children = {n.casefold() for o in visible for n in o.get('wait_for_objectives') or []}
        roots = [o for o in visible if o['name'].casefold() not in children]
        if not roots:
            continue
        repeated = any(o['name'].casefold() in seen for o in roots)
        seen.update(o['name'].casefold() for o in roots)
        if repeated or (vehicle and 13 <= group['index'] <= 21) or (mountain_office and 13 <= group['index'] <= 24):
            continue
        # A persistent player-facing tracker defines the larger section when
        # it shares a group with its internal tasks. Never collapse by title.
        counts = {o['name']: sum(any(p['name'].casefold() == o['name'].casefold()
                                    for p in g['objectives']) for g in groups) for o in roots}
        primary = max(roots, key=lambda o: counts[o['name']])
        yield group, primary
