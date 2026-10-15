"""Compile experimental mission-selection edits from packaged game definitions.

This is a requested progress override, not a captured/native-playthrough snapshot.
Branches follow authored dependencies; numbering is a stable topological order.
"""
import hashlib
import json
import math
from pathlib import Path

from build_practice_catalog import ROOT, MOD, SOURCE, walk, resolve, reference
from replay_spawn_rules import station_context, choose_station, valid_anchor, retain_native_boss_arrival


def preceding_required_anchor(definition, first_index, end_index):
    """Last unambiguous required completion in the preceding main section.

    A summary/escort/talk tracker can lack its own static end, while its last
    required completed trigger has a real point. Do not use optional branches,
    still-active trackers, enemy spawn origins, or points before a map crossing.
    """
    groups=definition['groups']
    for group in sorted(groups,key=lambda g:g['index'],reverse=True):
        if not first_index <= group['index'] < end_index:continue
        if any(o.get('travel_map') for g in groups if group['index'] <= g['index'] < end_index for o in g['objectives']):
            return None
        anchors={}
        for objective in group['objectives']:
            if objective.get('optional') or objective.get('optional_for_spawn'):continue
            if any(g['index'] >= end_index and any(o['name'].casefold()==objective['name'].casefold() for o in g['objectives']) for g in groups):continue
            anchor=objective.get('completion_anchor')
            if valid_anchor(anchor):
                key=(anchor['map'].casefold(),tuple(anchor['location'][k] for k in ('x','y','z')))
                anchors[key]=anchor
        if len(anchors)==1:return next(iter(anchors.values()))
        # A later group with conflicting completed points cannot establish
        # where its parallel tasks ended; do not fall farther back through it.
        if anchors:return None
    return None


def start_waypoint(definition, group, previous, definitions, main_groups):
    """Use the mission's entry, or a finished preceding section for later starts."""
    if previous is None and valid_anchor(definition.get('entry_anchor')):
        # A prerequisite can end far from this mission's actual giver, especially
        # on parallel story/DLC routes. Its completion point is not this entry.
        return dict(definition['entry_anchor'], source_rule='authored mission entry')
    anchor = None
    rule = None
    if previous:
        _, objective = previous
        section_end = previous[0].get('replay_end_anchor')
        if section_end and previous[0].get('replay_end_index', group['index']) < group['index']:
            anchor, rule = section_end, 'previous main section completion area'
        elif 'replay_end_index' in previous[0]:
            anchor = group.get('start_anchor') or preceding_required_anchor(definition, previous[0]['index'], group['index'])
            rule = 'previous main section final required completion'
        else:
            last = max(g['index'] for g in definition['groups']
                       if any(o['name'].casefold() == objective['name'].casefold() for o in g['objectives']))
            if not anchor and last < group['index']:
                anchor = objective.get('completion_anchor')
                rule = 'previous main objective completion'
    elif definition.get('predecessor'):
        prior = next((n for n in definitions if n.casefold() == definition['predecessor'].casefold()), None)
        groups = list(main_groups(prior, definitions[prior])) if prior else []
        if groups:
            anchor = groups[-1][1].get('completion_anchor')
            rule = 'previous mission final main objective completion'
    if not anchor:
        anchor = group.get('start_anchor')
        rule = 'previous authored group completion'
    if not anchor and previous:
        anchor=preceding_required_anchor(definition,previous[0]['index'],group['index'])
        rule='last required completion in preceding main section'
    if not anchor and previous and len(previous[1].get('wait_for_objectives', [])) > 1:
        # Parallel collection has no unique last pickup. A following task may
        # return to the same small area where that collection section began.
        # Keep that authored past point instead of a nearby station across a door.
        candidate = previous[0].get('start_anchor')
        targets = [o.get('completion_anchor') for o in group['objectives']
                   if not o.get('optional') and not o.get('optional_for_spawn')]
        past = {o['name'].casefold() for g in definition['groups'] if g['index'] < group['index']
                for o in g['objectives']}
        future = {o['name'].casefold() for g in definition['groups'] if g['index'] >= group['index']
                  for o in g['objectives']}
        # Fifteen metres is an operational area-match bound, not a native rule.
        if (valid_anchor(candidate) and candidate.get('objective', '').casefold() in past - future
                and targets and all(valid_anchor(p) and p['map'].casefold() == candidate['map'].casefold()
                    and math.dist([p['location'][k] for k in ('x','y','z')],
                                  [candidate['location'][k] for k in ('x','y','z')]) <= 1500
                    for p in targets)
                and not any(o.get('travel_map') for g in definition['groups']
                    if previous[0]['index'] <= g['index'] < group['index'] for o in g['objectives'])):
            anchor, rule = candidate, 'return to preceding collection section start'
    point = (anchor or {}).get('location', {})
    if (not (anchor or {}).get('map') or set(point) != {'x', 'y', 'z'}
            or not all(isinstance(v, (int, float)) and math.isfinite(v) and abs(v) < 1e9 for v in point.values())):
        return None
    return dict(anchor, source_rule=rule)


def build():
    practice = json.loads((MOD / 'mission_practice_catalog.json').read_text(encoding='utf-8'))
    public = json.loads((MOD / 'mission_catalog.json').read_text(encoding='utf-8'))
    dlc = json.loads((MOD / 'mission_dlc_catalog.json').read_text(encoding='utf-8'))
    docs = {}
    sets = {}
    hashes = dict(practice['source_hashes'])
    for p in sorted(SOURCE.glob('Nexus-Data-missionset*.json')):
        hashes[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
        for pointer, value in walk(json.loads(p.read_text(encoding='utf-8'))):
            if isinstance(value, dict) and isinstance(value.get('missionset'), str):
                sets[value['missionset'].casefold()] = value
    rows = {}
    for row in public:
        if row['source'] not in docs:
            docs[row['source']] = json.loads((SOURCE / row['source']).read_text(encoding='utf-8'))
        raw = resolve(docs[row['source']], row['pointer'])
        if row['category'] != 'story' and raw.get('missiontype') != 'DLC_MainStory':
            continue
        definition = practice['missions'].get(row['name'])
        if not definition or not definition.get('mission_set'):
            continue
        rows[row['name'].casefold()] = dict(name=row['name'], title=row['title'],
            mission_set=definition['mission_set'], definition=definition, raw=raw,
            campaign=dlc['missions'].get(row['name'], {}).get('pack', 'story'),
            source=row['source'], pointer=row['pointer'])
    members = {}
    for key, row in rows.items():
        members.setdefault(row['mission_set'], []).append(key)

    def dependencies(value):
        result = set()
        for _, node in walk(value):
            if isinstance(node, dict) and 'completed' in node:
                ref = reference(node['completed'])
                if not ref:
                    raise ValueError('Unresolved completed dependency')
                if str(node['completed']).casefold().startswith("missionset'"):
                    if ref not in members:
                        raise ValueError('Uncatalogued prerequisite set: ' + ref)
                    result.update(members[ref])
                elif ref in rows:
                    result.add(ref)
                else:
                    raise ValueError('Uncatalogued prerequisite mission: ' + ref)
        return result

    edges = {}
    for key, row in rows.items():
        group = sets.get(row['mission_set'], {})
        edges[key] = dependencies(group.get('generateddependencies', {})) | dependencies(row['raw'].get('dependencies', {}))
        edges[key].discard(key)
    ordered = []
    pending = list(rows)
    while pending:
        ready = [n for n in pending if edges[n].issubset(ordered)]
        if not ready:
            raise ValueError('Story dependency cycle or missing prerequisite')
        # Stable source catalog order chooses a display order for parallel routes.
        for n in ready:
            ordered.append(n)
            pending.remove(n)

    def ancestors(key):
        result = set(edges[key])
        todo = list(result)
        while todo:
            for dep in edges[todo.pop()]:
                if dep not in result:
                    result.add(dep)
                    todo.append(dep)
        return result

    ancestors_by_key = {key: ancestors(key) for key in rows}
    station_bytes = (MOD / 'travelstations.json').read_bytes()
    stations = json.loads(station_bytes)['stations']
    by_station = {s['station'].casefold(): s for s in stations}
    map_defaults = {}
    for row in json.loads((MOD / 'travelmaps_flat.json').read_text(encoding='utf-8'))['maps']:
        station = by_station.get(str(row.get('defaultstation')).casefold())
        if station:
            try:
                map_defaults[row['map'].casefold()] = dict(map=station['world'],
                    location={k: float(station[k]) for k in ('x', 'y', 'z')},
                    station=station['station'], source=station.get('source_file'))
            except (KeyError, ValueError, TypeError):
                pass
    counts = {}
    output = {}
    for rank, key in enumerate(ordered):
        row = rows[key]
        campaign = row['campaign']
        counts[campaign] = counts.get(campaign, 0) + 1
        number = counts[campaign]
        title = 'Story' if campaign == 'story' else dlc['packs'][campaign]['title']
        definition = row['definition']
        sections = {}
        # Import only the player-facing main sections; hidden tasks stay in edits.
        import importlib.util
        module_spec = importlib.util.spec_from_file_location('selection_groups', MOD / 'mission_selection.py')
        selector = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(selector)
        previous = None
        main = list(selector.main_groups(row['name'], definition))
        for position, (group, primary) in enumerate(main):
            waypoint = start_waypoint(definition, group, previous, practice['missions'], selector.main_groups)
            previous = (group, primary)
            earlier = {o['name'].casefold() for g in definition['groups'] if g['index'] < group['index'] for o in g['objectives']}
            later = {o['name'].casefold() for g in definition['groups'] if g['index'] >= group['index'] for o in g['objectives']}
            next_index = main[position + 1][0]['index'] if position + 1 < len(main) else float('inf')
            world, points, basis = station_context(definition, group, primary, waypoint, next_index, map_defaults, first_section=position==0)
            chosen = choose_station(stations, world, points, key, earlier-later, ancestors_by_key[key], rows)
            if chosen:
                station, station_location, requirements = chosen
            else:
                station = dict(world=world, station=None)
                station_location, requirements = None, []
            sections[str(group['index'])] = dict(checkpoint=group['index'], world=station['world'],
                station=station['station'], placement='native', initial_objectives=[primary['name'].casefold()],
                past_objectives=sorted(earlier-later), refresh_after_load=False,
                station_selection=basis, station_anchors=points, station_location=station_location,
                station_prerequisites=requirements, station_source=station.get('source_file'),
                station_dependency=station.get('dependency'),
                station_type=station.get('typedef'),
                station_arrival_policy='native server travel; future objectives unchanged')
            # Cross-map DLC travel openings need their objective restored on
            # the source map. Ordinary entries initialize during native travel;
            # a second character refresh can send them to the opposite route.
            if group['index'] == 0 and basis == 'authored mission entry' and primary.get('travel_map'):
                sections[str(group['index'])]['restore_active_objectives'] = [primary['name'].casefold()]
            if not chosen:
                sections[str(group['index'])]['spawn_issue'] = 'No source-resolved, accessible respawn station near this section'
            if chosen and retain_native_boss_arrival(station, primary):
                sections[str(group['index'])]['station_arrival_policy'] = 'native boss arena arrival; retain instead of preceding approach trigger'
            elif waypoint:
                sections[str(group['index'])].update(placement='waypoint', location=waypoint['location'],
                    start_waypoint=waypoint,
                    native_station_fallback=waypoint.get('source_rule') not in (
                        'return to preceding collection section start', 'previous main section completion area'))
        output[row['name']] = dict(kind='selection', mission=row['name'], saved_mission=key,
            mission_set=row['mission_set'], title=row['title'], campaign=campaign,
            playthrough=dict(rank=rank, number=number, label=f'{title} {number:02}',
                parallel=any(other != key and other not in ancestors_by_key[key] and key not in ancestors_by_key[other]
                    and rows[other]['campaign'] == campaign for other in rows)),
            past_missions=[[rows[n]['mission_set'], n] for n in ordered if n in ancestors_by_key[key]],
            future_missions=[[rows[n]['mission_set'], n] for n in ordered if key in ancestors_by_key[n]],
            sections=sections, source=row['source'], pointer=row['pointer'])
    data = dict(schema=1, catalog_sha256=hashlib.sha256((MOD/'mission_practice_catalog.json').read_bytes()).hexdigest(),
        travel_stations_sha256=hashlib.sha256(station_bytes).hexdigest(),
        policy='Experimental progress override: authored ancestors completed; descendants cleared; earlier selected objectives completed. Not captured gameplay.',
        source_hashes=hashes, missions=output)
    (MOD/'mission_selection_states.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    # Desktop ordering uses the same generated identities; independent of save progress.
    order = {name: dict(row['playthrough'], campaign=row['campaign']) for name, row in output.items()}
    (ROOT/'electron_poc/mission_playthrough.js').write_text(
        '(function(root){const data='+json.dumps(order, separators=(',', ':'))+';\n'
        'root.MsbtMissionPlaythrough=data;if(typeof module!=="undefined")module.exports=data;\n'
        '})(typeof window==="undefined"?globalThis:window);\n', encoding='utf-8')
    print(json.dumps(dict(missions=len(output), sections=sum(len(v['sections']) for v in output.values()), campaigns=counts)))


if __name__ == '__main__':
    build()
