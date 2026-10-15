"""Compile experimental mission-selection edits from packaged game definitions.

This is a requested progress override, not a captured/native-playthrough snapshot.
Branches follow authored dependencies; numbering is a stable topological order.
"""
import hashlib
import json
import math
from pathlib import Path

from build_practice_catalog import ROOT, MOD, SOURCE, walk, resolve, reference


def start_waypoint(definition, group, previous, definitions, main_groups):
    """Use only a finished preceding main section, never this section's target."""
    anchor = None
    rule = None
    if previous:
        _, objective = previous
        last = max(g['index'] for g in definition['groups']
                   if any(o['name'].casefold() == objective['name'].casefold() for o in g['objectives']))
        if last < group['index']:
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
    stations = json.loads((MOD / 'travelstations.json').read_text(encoding='utf-8'))['stations']
    # Native station remains the initial arrival and safe placement fallback.
    stations = [s for s in stations if s['typedef'].casefold() in ('respawn', 'fast_travel', 'fast_travel_sendonly')]
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
        for group, primary in selector.main_groups(row['name'], definition):
            waypoint = start_waypoint(definition, group, previous, practice['missions'], selector.main_groups)
            previous = (group, primary)
            anchor = waypoint or group.get('start_anchor') or primary.get('completion_anchor')
            world = (anchor or {}).get('map') or definition.get('execution_map')
            candidates = [s for s in stations if s['world'].casefold() == str(world).casefold()]
            if not candidates:
                continue
            point = (anchor or {}).get('location')
            if point:
                candidates.sort(key=lambda s: sum((float(s[k]) - point[k]) ** 2 for k in ('x', 'y', 'z')))
            else:
                candidates.sort(key=lambda s: s['station'].casefold())
            station = candidates[0]
            earlier = {o['name'].casefold() for g in definition['groups'] if g['index'] < group['index'] for o in g['objectives']}
            later = {o['name'].casefold() for g in definition['groups'] if g['index'] >= group['index'] for o in g['objectives']}
            sections[str(group['index'])] = dict(checkpoint=group['index'], world=station['world'],
                station=station['station'], placement='native', initial_objectives=[primary['name'].casefold()],
                past_objectives=sorted(earlier-later), refresh_after_load=False,
                station_selection='nearest authored section anchor' if point else 'native map fallback')
            if waypoint:
                sections[str(group['index'])].update(placement='waypoint', location=waypoint['location'],
                    start_waypoint=waypoint, native_station_fallback=True)
        output[row['name']] = dict(kind='selection', mission=row['name'], saved_mission=key,
            mission_set=row['mission_set'], title=row['title'], campaign=campaign,
            playthrough=dict(rank=rank, number=number, label=f'{title} {number:02}',
                parallel=any(other != key and other not in ancestors_by_key[key] and key not in ancestors_by_key[other]
                    and rows[other]['campaign'] == campaign for other in rows)),
            past_missions=[[rows[n]['mission_set'], n] for n in ordered if n in ancestors_by_key[key]],
            future_missions=[[rows[n]['mission_set'], n] for n in ordered if key in ancestors_by_key[n]],
            sections=sections, source=row['source'], pointer=row['pointer'])
    data = dict(schema=1, catalog_sha256=hashlib.sha256((MOD/'mission_practice_catalog.json').read_bytes()).hexdigest(),
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
