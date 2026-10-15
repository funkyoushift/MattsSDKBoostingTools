"""Choose authored replay stations without alphabetical picks or future progress edits.

Waypoint destinations in this module are proximity evidence for a native station,
not claims that the destination is a verified objective beginning.
"""
import json
import math
import re

ARRIVAL_STATION_TYPES = frozenset(('respawn','fast_travel','destinationonly'))


def retain_native_boss_arrival(station, primary):
    """Keep a native cinematic/arena arrival instead of its approach trigger.

    A grounded approach marker can still be outside a closed arena barrier.
    This policy requires both an authored boss-fight objective and a native
    destination-only station; ordinary respawn stations keep waypoint placement.
    """
    scene = primary.get('scene_anchor') or {}
    return (str(station.get('typedef', '')).casefold() == 'destinationonly'
            and str(scene.get('gameplay_pointer', '')).endswith('/graph_data/gameplay/bossfight'))


def valid_anchor(anchor):
    point = (anchor or {}).get('location', {})
    return bool((anchor or {}).get('map') and set(point) == {'x', 'y', 'z'}
                and all(isinstance(v, (int, float)) and math.isfinite(v) and abs(v) < 1e9
                        for v in point.values()))


def anchors(group, definition=None):
    """Only required authored locations; optional objectives do not select a start."""
    result = {}
    for objective in group['objectives']:
        if objective.get('optional') or objective.get('optional_for_spawn'):
            continue
        if definition and any(g['index'] > group['index'] and any(o['name'].casefold() == objective['name'].casefold()
                for o in g['objectives']) for g in definition['groups']):
            continue
        anchor = objective.get('completion_anchor') or objective.get('scene_anchor')
        if valid_anchor(anchor):
            key = (anchor['map'].casefold(), tuple(anchor['location'][k] for k in ('x', 'y', 'z')))
            result.setdefault(key, anchor)
    return list(result.values())


def station_context(definition, group, primary, waypoint, next_index, map_defaults, *, first_section=False):
    """Keep exact prior completion first; derive station proximity from this section.

    A composite's required substeps supply location evidence, without becoming
    extra entries in the player-facing objective picker.
    """
    spanning = any(g['index'] > group['index'] and any(o['name'].casefold() == primary['name'].casefold()
        for o in g['objectives']) for g in definition['groups'])
    for anchor, rule in [(waypoint, 'authored mission entry' if (waypoint or {}).get('source_rule') == 'authored mission entry' else 'previous completion'),
                         (group.get('start_anchor'), 'previous authored group'),
                         (definition.get('entry_anchor') if first_section else None, 'authored mission entry'),
                         (None if spanning else primary.get('approach_anchor'), 'first authored route breadcrumb'),
                         (None if spanning else primary.get('completion_anchor') or primary.get('scene_anchor'), 'selected objective waypoint')]:
        if valid_anchor(anchor):
            return anchor['map'], [anchor], rule
    groups = sorted(definition['groups'], key=lambda g: g['index'])
    for candidate in groups:
        if group['index'] <= candidate['index'] < next_index:
            points = anchors(candidate, definition)
            maps = {p['map'].casefold() for p in points}
            if points and len(maps) == 1:
                return points[0]['map'], points, 'required section waypoints'
    expected = primary.get('travel_map')
    maps = primary.get('completion_maps') or []
    expected = expected or (maps[0] if len(maps) == 1 else definition.get('execution_map'))
    for candidate in reversed(groups):
        if candidate['index'] >= group['index']:
            continue
        points = [p for p in anchors(candidate, definition) if not expected or p['map'].casefold() == expected.casefold()]
        if points and len({p['map'].casefold() for p in points}) == 1:
            return points[0]['map'], points, 'last earlier authored waypoints'
    anchor = definition.get('start_anchor')
    if valid_anchor(anchor) and (not expected or anchor['map'].casefold() == expected.casefold()):
        return anchor['map'], [anchor], 'preceding mission location'
    # With no section location at all, an explicit authored map arrival is the
    # only supported baseline. Never silently substitute alphabetical station 1.
    anchor = map_defaults.get(str(expected).casefold())
    if valid_anchor(anchor):
        return anchor['map'], [anchor], 'authored map entry; section location unresolved'
    return expected, [], 'section location unresolved'


def station_requirements(station, current, earlier, past, rows, *, native_arrival=False):
    """Understand only explicit positive mission/objective completion conditions.

    Unknown conditions remain excluded. Native server-travel can reach a known
    same-campaign fast-travel station before its UI unlock (live checked at the
    Harmonica hub and FL4K fortress office). Do not complete its future objective.
    """
    raw = station.get('dependency')
    if not raw or str(raw).strip().casefold() == 'none':
        return []
    # Some native stations accept any of several completed entry routes. Only
    # resolve an OR of individually understood, owned positive conditions.
    # Keep authored branch order and supply no future/negative/unknown facts.
    if isinstance(raw,str) and '||' in raw and '&&' not in raw:
        branches=[station_requirements(dict(station,dependency=part.strip()),current,earlier,past,rows)
                  for part in raw.split('||')]
        return branches[0] if all(branch is not None for branch in branches) else None
    mission = objective = set_name = None
    try:
        condition = json.loads(raw)
    except (ValueError, TypeError):
        condition = None
    if isinstance(condition, dict) and condition.get('structtype') == "Asset'/Script/GbxGame.MissionDependencyCondition_Objective'":
        if set(condition) != {'structtype', 'mission', 'objective'}:
            return None
        match = re.fullmatch(r"mission'([^']+)'", str(condition['mission']), re.I)
        if not match:
            return None
        mission, objective = match[1].casefold(), str(condition['objective']).casefold()
    else:
        match = re.fullmatch(r'\s*\(\s*missions\.([\w]+)\.([\w]+)\.(?:final\.([\w]+)_endstate|status)\s*==\s*completed\s*\)\s*', str(raw), re.I)
        if not match:
            return None
        set_name, mission, objective = (v.casefold() if v else None for v in match.groups())
    row = rows.get(mission)
    if row is None or set_name and row['mission_set'].casefold() != set_name:
        return None
    if objective:
        owned = {o['name'].casefold() for g in row['definition']['groups'] for o in g['objectives']}
        if objective not in owned:
            return None
    future = (mission == current and (not objective or objective not in earlier)) or (mission != current and mission not in past)
    if future and native_arrival and station['typedef'].casefold() == 'fast_travel':
        campaign = rows.get(current, {}).get('campaign')
        if campaign and campaign == row.get('campaign'):
            return []  # Native arrival only. No future progress flag is supplied.
    if mission == current:
        if not objective or objective not in earlier:
            return None
    elif mission not in past:
        return None
    if objective:
        return [dict(mission_set=row['mission_set'], mission=mission, objective=objective)]
    return []  # The existing past-mission edit supplies this completed status.


def choose_station(stations, world, points, current, earlier, past, rows):
    candidates = []
    for row in stations:
        if row['world'].casefold() != str(world).casefold() or row['typedef'].casefold() not in ARRIVAL_STATION_TYPES:
            continue
        try:
            location = {k: float(row[k]) for k in ('x', 'y', 'z')}
        except (KeyError, ValueError, TypeError):
            continue
        if not valid_anchor(dict(map=world, location=location)):
            continue
        requirements = station_requirements(row, current, earlier, past, rows, native_arrival=True)
        if requirements is None:
            continue
        # Choose the native station with least total distance to the section's
        # authored locations. No synthetic coordinate is ever used for spawning.
        distance = sum(sum((location[k] - point['location'][k]) ** 2 for k in location) for point in points)
        candidates.append((distance, row['station'].casefold(), row, location, requirements))
    if not points or not candidates:
        return None
    _, _, row, location, requirements = min(candidates)
    return row, location, requirements
