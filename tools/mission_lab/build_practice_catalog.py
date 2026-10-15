"""Extract checkpoint labels and preceding completion anchors from authored data.

No nearest-travel or coordinate inference. Ambiguous/missing anchors stay absent.
"""
import hashlib
import json
import math
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'external_app/v22_parts_codes_fixed/matt_editor/LegitItems'
MOD = ROOT / 'mod_extracted/MattsSDKBoostingTools'

def walk(value, path=''):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, path+'/'+key)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from walk(child, path+'/'+str(i))

def resolve(doc, path):
    for key in path.strip('/').split('/'):
        doc = doc[int(key)] if isinstance(doc,list) else doc[key]
    return doc

def reference(value):
    match = re.fullmatch(r"[^']+'([^']+)'", str(value))
    return match[1].casefold() if match else None

def group_objectives(group,definitions):
    """Include explicitly parented children for each parent group membership.

    Reused composites can list their children only in their first objective
    set. Their authored parent links still apply to every later membership.
    No generated-name inference or native identity check is relaxed here.
    """
    expanded=list(group.get('objectives',[]))
    seen={str(o.get('objective','')).casefold() for o in expanded}
    for objective in expanded:
        parent=str(objective.get('objective','')).casefold()
        if len(definitions.get(parent,[]))!=1:continue
        for matches in definitions.values():
            for _,child in matches:
                name=child.get('objective')
                if not name or str(child.get('parentobjective','')).casefold()!=parent or name.casefold() in seen:continue
                expanded.append({'objective':name});seen.add(name.casefold())
    return expanded

def scalar_order(row):
    order = (row.get('orderdata') or {}).get('order', {})
    if order.get('type') == 'Range' or 'end' in order or 'start' not in order:
        return None
    try:
        value = Decimal(str(order['start']))
        return value if value.is_finite() else None
    except InvalidOperation:
        return None

def ordered_predecessor(name, result, members):
    """Return only a uniquely ordered preceding member; missing order blocks proof."""
    names = members.get(result[name]['mission_set'], [])
    orders = {n: scalar_order(result[n]) for n in names}
    current = orders.get(name)
    if current is None or any(v is None for v in orders.values()):
        return None
    if sum(v == current for v in orders.values()) != 1:
        return None
    lower = [v for v in orders.values() if v < current]
    preceding = [n for n, v in orders.items() if lower and v == max(lower)]
    return preceding[0] if len(preceding) == 1 else None


def completion_fields(gameplay):
    """Use the authored completion target, including escort destinations."""
    kind=str(gameplay.get('structtype',''))
    if kind.endswith(".ObjectiveTypeSettings_EchoPanelHack'"):
        # A return trigger can differ from the panel. Retain both references;
        # the existing unique-location check rejects ambiguous completions.
        return ('echopanel', 'returntrigger')
    if kind.endswith(".ObjectiveTypeSettings_PlaceCarryable'"):return ('container',)
    if kind.endswith(".ObjectiveTypeSettings_EchoLog'"):return ('echologio',)
    if 'OakEscort' in kind:return ('endnode',)
    # An explicit conversation node locates the interaction. The moving NPC's
    # default registry waypoint can be elsewhere (Mr. Chew has several nodes).
    if 'Talk' in kind or 'OakExchangeItem' in kind:return ('node',) if gameplay.get('node') else ('node','npc')
    if 'ObjectiveTypeSettings_Encounter' in kind:return ('encounter',)
    return ('object','triggervolume','ainode','target')


def completion_dependencies(gameplay):
    """Explicit internal-objective trackers resolve from their native children.

    Only direct success-status watchers on Custom objectives are included;
    failure/deactivation/compound conditions are not reinterpreted here.
    """
    kind=str(gameplay.get('structtype',''))
    if ('ObjectiveTypeSettings_External' in kind and gameplay.get('subtype')=='InternalObjective'):
        target=gameplay.get('internalobjective')
        return [target] if isinstance(target,str) and target else []
    if 'ObjectiveTypeSettings_Custom' not in kind:return []
    dependencies=[]
    for aspect in gameplay.get('aspects',[]):
        data=aspect.get('data',{});condition=data.get('condition',{})
        if ('MissionObjectiveAspect_ResolveObjective' in data.get('structtype','') and
                'type' not in data and set(condition)=={'structtype','objective'} and
                'ObjectiveValueEvaluator_ObjectiveStatus' in condition['structtype'] and
                isinstance(condition['objective'],str) and condition['objective']):
            dependencies.append(condition['objective'])
    return sorted(set(dependencies))


def completion_aliases(gameplay):
    """Return explicit completion targets; dynamic pickup drops have no fixed anchor."""
    if str(gameplay.get('structtype','')).endswith(".ObjectiveTypeSettings_OakPickup'"):
        strategy=gameplay.get('pickupspawnstrategy') or {}
        if str(strategy.get('structtype','')).endswith(".GbxPickupObjectiveSpawnStrategy_Placed'"):
            return [('pickupspawnstrategy.pickupspawner',strategy.get('pickupspawner'))]
        return []
    return [(field,gameplay.get(field)) for field in completion_fields(gameplay)]


def actor_locations(actor, locations):
    """Resolve omitted groups only from a unique authored waypoint address.

    DLC actor aliases often omit groupname; their serialized waypoints retain it.
    Do not guess 'base' or choose between two groups sharing a registry name.
    """
    if not actor or not all(actor.get(k) for k in ('map','registryname')):return []
    # DLC discovery actors can live in an authored level instance, not Top.
    # The old Top-only prefix discarded their real serialized waypoints.
    scope=actor.get('submap') or 'top'
    prefix=f"registry.{actor['map']}.{scope}.".casefold()
    suffix=f".{actor['registryname']}.__nochannel".casefold()
    if actor.get('groupname'):
        addresses=[prefix+str(actor['groupname']).casefold()+suffix]
    else:
        addresses=[address for address in locations if address.startswith(prefix) and address.endswith(suffix)]
        if len(addresses)!=1:return []
    return [(address,point) for address in addresses for point in locations.get(address,[])]


def optional_for_spawn(value, definitions):
    """Optional parent branches must not choose a required replay start.

    Preserve the child's actual native optional flag for execution. This is
    ancestry metadata for spawn selection, derived only from explicit links.
    """
    seen=set()
    while value:
        if value.get('optional') == 'true':return True
        parent=str(value.get('parentobjective') or '').casefold()
        if not parent or parent in seen or len(definitions.get(parent,[]))!=1:return False
        seen.add(parent);value=definitions[parent][0][1]
    return False


def authored_scene_anchor(gameplay, aliases, locations):
    """Locate a declared scene target, never a moving enemy's completion.

    Static UI waypoints and spawner/boss origins are proximity evidence for
    station choice only. They do not become preceding-completion coordinates.
    """
    kind=str(gameplay.get('structtype',''))
    fields=()
    if kind.endswith(".ObjectiveTypeSettings_OakKill'"):fields=('spawner','targetorigin')
    elif kind.endswith(".ObjectiveTypeSettings_OakBoss'"):fields=('bossfight',)
    elif kind.endswith(".ObjectiveTypeSettings_OakDamage'"):fields=('targetorigin',)
    elif kind.endswith(".ObjectiveTypeSettings_OakInteract'"):fields=('spawner',)
    references=[(field,gameplay[field]) for field in fields if gameplay.get(field)]
    if not references:
        waypoints=gameplay.get('additionalwaypoints') or []
        if len(waypoints)==1 and set(waypoints[0]) <= {'runtimeactor','staticactor','settings'}:
            marker=waypoints[0];settings=marker.get('settings') or {}
            display_only=(not settings or (set(settings) <= {'structtype','bneverdisplayasoptional','waypointradius'}
                and settings.get('structtype')=="Asset'/Script/OakGame.OakObjectiveWaypointSettings'"))
            if settings.get('waypointradius') is not None:
                try:display_only=display_only and math.isfinite(float(settings['waypointradius'])) and float(settings['waypointradius'])>=0
                except (TypeError,ValueError):display_only=False
            field='staticactor' if marker.get('staticactor') else 'runtimeactor'
            if display_only and field and marker.get(field):references=[('additionalwaypoints/0/'+field,marker[field])]
    if not references and kind.endswith(".ObjectiveTypeSettings_OakTravel'") and gameplay.get('detectionmethod')=='Map' and gameplay.get('triggervolume'):
        references=[('triggervolume',gameplay['triggervolume'])]
    points={}
    for field,alias in references:
        actors=aliases.get(str(alias).casefold(),[])
        if len(actors)!=1:return None
        found=actor_locations(actors[0],locations)
        if len(found)!=1:return None
        address,point=found[0]
        try:location={k:float(point['location'][k]) for k in ('x','y','z')}
        except (KeyError,TypeError,ValueError):return None
        if not all(math.isfinite(v) for v in location.values()):return None
        key=(actors[0]['map'].casefold(),tuple(location.values()))
        points[key]=dict(map=actors[0]['map'],location=location,actor=address,
                         pointer=point['pointer'],gameplay_field=field,alias=alias)
    return next(iter(points.values())) if len(points)==1 else None


def authored_approach_anchor(gameplay, aliases, locations):
    """First native route breadcrumb, for nearby-station selection only."""
    candidates=[]
    for index,aspect in enumerate(gameplay.get('aspects',[])):
        data=aspect.get('data',{})
        if data.get('structtype')!="Asset'/Script/OakGame.MissionObjectiveAspect_Breadcrumbs'":continue
        crumbs=data.get('breadcrumbs') or []
        if not crumbs:continue
        crumb=crumbs[0]
        if set(crumb)-{'triggervolume','boverridewaypointlocation','waypointoverride'}:continue
        field='waypointoverride' if crumb.get('boverridewaypointlocation')=='true' else 'triggervolume'
        actors=aliases.get(str(crumb.get(field) or '').casefold(),[])
        if len(actors)!=1:continue
        found=actor_locations(actors[0],locations)
        if len(found)!=1:continue
        address,point=found[0]
        try:location={k:float(point['location'][k]) for k in ('x','y','z')}
        except (KeyError,TypeError,ValueError):continue
        if not all(math.isfinite(v) for v in location.values()):continue
        candidates.append(dict(map=actors[0]['map'],location=location,actor=address,pointer=point['pointer'],
            gameplay_field=f'aspects/{index}/data/breadcrumbs/0/{field}',alias=crumb[field]))
    return candidates[0] if len(candidates)==1 else None


def mission_entry_anchor(mission, aliases, locations, base_pointer):
    entries=[(pointer,value) for pointer,value in walk(mission.get('entry_points',{}),base_pointer+'/entry_points')
             if isinstance(value,dict) and value.get('structtype')=="Asset'/Script/GbxGame.MissionGiverType_Basic'"]
    if len(entries)>1:
        # Multiple native mission-giver routes are all valid beginnings. Use
        # the explicitly numbered entry 1, retaining its authored identity;
        # never sort actor/station names to manufacture an ordering.
        entries=[(pointer,giver) for pointer,giver in entries
                 if pointer.endswith('/1/missiongiver')]
    if len(entries)!=1:return None
    pointer,giver=entries[0];alias=giver.get('actoralias');actors=aliases.get(str(alias).casefold(),[])
    if len(actors)!=1 or not giver.get('waypoint'):return None
    points={}
    for address,point in actor_locations(actors[0],locations):
        try:location={k:float(point['location'][k]) for k in ('x','y','z')}
        except (KeyError,ValueError,TypeError):return None
        if not all(math.isfinite(v) for v in location.values()):return None
        points[(address,tuple(location.values()))]=dict(map=actors[0]['map'],location=location,actor=address,
            pointer=point['pointer'],entry_pointer=pointer,alias=alias,
            source_rule='authored mission giver; not previous completion')
    return next(iter(points.values())) if len(points)==1 else None


def dynamic_scene_anchor(gameplay, aliases, locations):
    """Resolve an authored static waypoint paired with a moving travel target.

    This loads the scene only; the moving actor's actual completion position is
    not proven by an additional waypoint and must not become a checkpoint.
    """
    if (gameplay.get('detectionmethod') != 'Dynamic' or
            'ObjectiveTypeSettings_OakTravel' not in gameplay.get('structtype', '')):
        return None
    target = str(gameplay.get('targetactor') or '').casefold()
    waypoints = gameplay.get('additionalwaypoints') or []
    if not target or len(waypoints) != 1:
        return None
    waypoint = waypoints[0]
    if str(waypoint.get('runtimeactor') or '').casefold() != target:
        return None
    actors = aliases.get(str(waypoint.get('staticactor') or '').casefold(), [])
    if len(actors) != 1:
        return None
    points = actor_locations(actors[0], locations)
    if len(points) != 1:
        return None
    address, point = points[0]
    try:
        location = {k: float(point['location'][k]) for k in ('x', 'y', 'z')}
    except (KeyError, TypeError, ValueError):
        return None
    if not all(math.isfinite(v) for v in location.values()):
        return None
    return dict(map=actors[0]['map'], location=location, actor=address,
                pointer=point['pointer'], alias=waypoint['staticactor'])


def encounter_staging(groups):
    """Use a declared preceding travel target inside an encounter's marker area.

    Encounter centres can sit over pits. The waypoint radius is used as our
    staging boundary, not as proof that the native encounter is completed.
    Practice completion anchors remain unchanged.
    """
    for group in groups:
        for objective in group['objectives']:
            scene = objective.get('encounter_scene')
            if not scene:
                continue
            previous = str(scene.get('previousobjective') or '').casefold()
            points = [o['completion_anchor'] for g in groups if g['index'] <= group['index']
                      for o in g['objectives'] if o.get('completion_anchor') and
                      str(o['name']).casefold() == previous]
            unique = {(p['map'].casefold(), tuple(p['location'][k] for k in ('x','y','z'))): p for p in points}
            if len(unique) != 1:
                continue
            anchor = next(iter(unique.values()))
            if (anchor['map'].casefold() == scene['actor']['map'].casefold() and
                    sum((anchor['location'][k]-scene['center'][k])**2 for k in ('x','y','z')) <= scene['radius']**2):
                objective['scene_anchor'] = anchor

def same_native_timeline(before, after):
    """Metadata repairs may expose existing implicit composite children.

    Require identical native source bytes, missions, identities and checkpoint
    order. An expanded group may only add objective IDs already in that same
    mission; removing a prior membership or adding a new ID requires review.
    """
    if before['source_hashes']!=after['source_hashes'] or set(before['missions'])!=set(after['missions']):return False
    for name,old in before['missions'].items():
        new=after['missions'][name]
        if old['mission_set']!=new['mission_set'] or [g['index'] for g in old['groups']]!=[g['index'] for g in new['groups']]:return False
        def names(m):return {o['name'] for g in m['groups'] for o in g['objectives']}
        if names(old)!=names(new):return False
        for left,right in zip(old['groups'],new['groups']):
            if not {o['name'] for o in left['objectives']} <= {o['name'] for o in right['objectives']}:return False
    return True


def build():
    output=MOD/'mission_practice_catalog.json'
    previous_bytes=output.read_bytes() if output.exists() else None
    previous_catalog=json.loads(previous_bytes) if previous_bytes else None
    catalog = json.loads((MOD/'mission_catalog.json').read_bytes())
    docs, hashes = {}, {}
    for filename in {r['source'] for r in catalog}:
        raw = (SOURCE/filename).read_bytes()
        docs[filename] = json.loads(raw)
        hashes[filename] = hashlib.sha256(raw).hexdigest()
    sets = {}
    for source in sorted(SOURCE.glob('Nexus-Data-missionset*.json')):
        raw=source.read_bytes();hashes[source.name]=hashlib.sha256(raw).hexdigest()
        for path,value in walk(json.loads(raw)):
            if isinstance(value,dict) and isinstance(value.get('missionset'),str):
                deps=[reference(v['completed']) for _,v in walk(value.get('generateddependencies',{}))
                      if isinstance(v,dict) and 'completed' in v]
                sets[value['missionset'].casefold()]=dict(dependencies=[d for d in deps if d],source=source.name,pointer=path)
    result, members = {}, {}
    for row in catalog:
        doc=docs[row['source']];mission=resolve(doc,row['pointer'])
        parent=resolve(doc,row['pointer'].rsplit('/',1)[0])
        aliases={}
        for _,value in walk(mission.get('alias_nodes',{})):
            if isinstance(value,dict) and isinstance(value.get('alias'),dict):
                for name in value['alias'].values():
                    if isinstance(name,str):aliases.setdefault(name.casefold(),[]).append(value.get('aliasdata',{}).get('actor'))
        locations={}
        definitions={}
        for path,value in walk(parent.get('__dep_entries',[]),row['pointer'].rsplit('/',1)[0]+'/__dep_entries'):
            if not isinstance(value,dict):continue
            if value.get('staticaddress') and value.get('loc'):
                locations.setdefault(value['staticaddress'].casefold(),[]).append(dict(location=value['loc'],pointer=path))
            if isinstance(value.get('objective'),str) and 'graph_data' in value:
                definitions.setdefault(value['objective'].casefold(),[]).append((path,value))
        groups=[]
        for index,group in enumerate(mission.get('objective_sets',[])):
            objectives=[]; anchors=[]; unresolved=[]; mandatory=0
            for objective in group_objectives(group,definitions):
                name=objective.get('objective');matches=definitions.get(str(name).casefold(),[])
                if len(matches)!=1:
                    reason='missing_definition' if not matches else 'ambiguous_definition'
                    objectives.append(dict(name=name,title=name,hidden=None,optional=None,pointer=None,unresolved=reason))
                    unresolved.append(dict(objective=name,reason=reason))
                    continue
                path,value=matches[0]
                hidden=value.get('ux_hidden')=='true';optional=value.get('optional')=='true'
                title=value.get('ux_display',{}).get('text','').split(', ',2)[-1] or name
                objectives.append(dict(name=name,title=title,hidden=hidden,optional=optional,pointer=path))
                spawn_optional=optional_for_spawn(value,definitions)
                if spawn_optional and not optional:objectives[-1]['optional_for_spawn']=True
                if not spawn_optional:mandatory+=1
                objective_issues=[]
                gameplay=value.get('graph_data',{}).get('gameplay',{})
                if 'ObjectiveTypeSettings_OakTravel' in gameplay.get('structtype',''):
                    objectives[-1]['activation_by_arrival']=True
                dependencies=completion_dependencies(gameplay)
                if 'ObjectiveTypeSettings_Composite' in gameplay.get('structtype',''):
                    # Use explicit parent links; generated naming conventions
                    # do not establish a dependency. The game decides whether
                    # all/any children satisfy its authored composite mode.
                    children=[child['objective'] for matches in definitions.values() for _,child in matches
                              if str(child.get('parentobjective','')).casefold()==name.casefold()]
                    if (children and len(set(c.casefold() for c in children))==len(children)
                            and str(len(children))==gameplay.get('numsubobjectives')):
                        dependencies=sorted(children)
                    else:
                        objectives[-1]['unresolved']='composite_children_unresolved'
                if dependencies:objectives[-1]['wait_for_objectives']=dependencies
                approach=authored_approach_anchor(gameplay,aliases,locations)
                if approach:
                    field=approach.pop('gameplay_field')
                    objectives[-1]['approach_anchor']=dict(approach,mission=row['name'],objective=name,
                        source=row['source'],gameplay_pointer=path+'/graph_data/gameplay/'+field,
                        source_rule='first authored route breadcrumb; station proximity only')
                scene = dynamic_scene_anchor(gameplay, aliases, locations)
                if scene:
                    objectives[-1]['scene_anchor'] = dict(scene, mission=row['name'],
                        objective=name, source=row['source'],
                        gameplay_pointer=path+'/graph_data/gameplay/additionalwaypoints/0')
                else:
                    scene=authored_scene_anchor(gameplay,aliases,locations)
                    if scene:
                        field=scene.pop('gameplay_field')
                        objectives[-1]['scene_anchor']=dict(scene,mission=row['name'],objective=name,
                            source=row['source'],gameplay_pointer=path+'/graph_data/gameplay/'+field,
                            source_rule='authored scene reference; completion unresolved')
                if gameplay.get('structtype')=="Asset'/Script/GbxGame.ObjectiveTypeSettings_Talk'":
                    actors=aliases.get(str(gameplay.get('npc') or '').casefold(),[])
                    objectives[-1]['interaction']=dict(kind='talk',
                        actor=actors[0] if len(actors)==1 else None,
                        alias=gameplay.get('npc'),source=row['source'],pointer=path+'/graph_data/gameplay')
                # Only Map detection makes this a cross-map arrival objective.
                # Other travel objectives can carry unused/default map fields.
                if (gameplay.get('detectionmethod')=='Map' and
                        'ObjectiveTypeSettings_OakTravel' in gameplay.get('structtype','')):
                    objectives[-1]['travel_map']=reference(gameplay.get('map'))
                # Only explicit objective completion interaction locations.
                candidates=[];target_maps=set()
                for field,alias in completion_aliases(gameplay):
                    actors=aliases.get(str(alias or '').casefold(),[])
                    if len(actors)>1:
                        objective_issues.append(dict(objective=name,reason='ambiguous_completion_alias',field=field))
                    if len(actors)!=1:continue
                    actor=actors[0]
                    if actor and actor.get('map'):target_maps.add(str(actor['map']).casefold())
                    for address,point in actor_locations(actor,locations):
                        try:
                            location={k:float(point['location'][k]) for k in ('x','y','z')}
                        except (KeyError,TypeError,ValueError):
                            objective_issues.append(dict(objective=name,reason='invalid_completion_location',pointer=point['pointer']))
                            continue
                        if all(math.isfinite(v) for v in location.values()):
                            candidates.append(dict(map=actor['map'],location=location,
                                                   actor=address,objective=name,pointer=point['pointer'],source=row['source']))
                        else:objective_issues.append(dict(objective=name,reason='invalid_completion_location',pointer=point['pointer']))
                if objectives[-1].get('travel_map'):
                    target_maps={objectives[-1]['travel_map']}
                objectives[-1]['completion_maps']=sorted(target_maps)
                unique={(p['map'],tuple(p['location'].values())):p for p in candidates}
                if len(unique)==1:
                    anchor=next(iter(unique.values()))
                    if not spawn_optional:anchors.append(anchor)
                    # Keep each proven target even when other objectives in
                    # this group finish elsewhere. Group checkpoint placement
                    # still requires one common, unambiguous destination.
                    if (not objective_issues
                            and not objectives[-1].get('travel_map')):
                        objectives[-1]['completion_anchor']=dict(anchor,mission=row['name'])
                        if 'ObjectiveTypeSettings_Encounter' in gameplay.get('structtype',''):
                            actors=aliases.get(str(gameplay.get('encounter') or '').casefold(),[])
                            try:radius=float((gameplay.get('primarywaypointsettings') or {}).get('waypointradius',0))
                            except (TypeError,ValueError):radius=0
                            if len(actors)==1 and actors[0] and math.isfinite(radius) and radius>0:
                                objectives[-1]['encounter_scene']=dict(actor=actors[0],center=anchor['location'],radius=radius,
                                    previousobjective=value.get('previousobjective'),source=row['source'],pointer=path+'/graph_data/gameplay')
                else:objective_issues.append(dict(objective=name,reason='missing_completion_location' if not unique else 'ambiguous_completion_location'))
                if not spawn_optional:unresolved.extend(objective_issues)
            unique={(p['map'],tuple(p['location'].values())):p for p in anchors}
            if len(unique)>1:unresolved.append(dict(reason='conflicting_required_completion_locations'))
            groups.append(dict(index=index,objectives=objectives,unresolved=unresolved,
                               completion_anchor=next(iter(unique.values())) if not unresolved and mandatory and len(anchors)==mandatory and len(unique)==1 else None))
        encounter_staging(groups)
        set_name=reference(mission.get('missionset'))
        if set_name:members.setdefault(set_name,[]).append(row['name'])
        raw_zone=mission.get('zone')
        zone=reference(raw_zone.get('def') if isinstance(raw_zone,dict) else raw_zone)
        alias_maps={str(actor['map']).casefold() for actors in aliases.values() for actor in actors if actor and actor.get('map')}
        target_maps={m for g in groups for o in g['objectives'] for m in o.get('completion_maps',[])}
        target_maps.update(o['scene_anchor']['map'].casefold() for g in groups for o in g['objectives'] if o.get('scene_anchor'))
        execution_map=next(iter(target_maps)) if len(target_maps)==1 else zone.split('.',1)[0] if zone else (next(iter(alias_maps)) if len(alias_maps)==1 else None)
        entry=mission_entry_anchor(mission,aliases,locations,row['pointer'])
        if entry:entry=dict(entry,source=row['source'],mission=row['name'])
        result[row['name']]=dict(title=row['title'],source=row['source'],pointer=row['pointer'],mission_set=set_name,
                                 entry_anchor=entry,
                                 execution_map=execution_map,execution_map_source='unique_completion_map' if len(target_maps)==1 else 'zone' if zone else 'unique_actor_map' if execution_map else None,
                                 execution_maps=sorted((target_maps or ({execution_map} if execution_map else set())) | ({entry['map'].casefold()} if entry else set())),
                                 replay_station=reference(mission.get('replaytravelstation')),orderdata=mission.get('orderdata'),groups=groups)
    for name,row in result.items():
        dependencies=sets.get(row['mission_set'],{}).get('dependencies',[])
        preceding=ordered_predecessor(name,result,members)
        same_set=members.get(row['mission_set'],[])
        orders=[scalar_order(result[n]) for n in same_set]
        first_member=len(same_set)==1 or (bool(orders) and all(v is not None for v in orders) and scalar_order(row)==min(orders))
        if preceding is None and first_member:
            previous=members.get(dependencies[0],[]) if len(dependencies)==1 else []
            if len(previous)==1:preceding=previous[0]
            elif previous:
                previous_orders={n:scalar_order(result[n]) for n in previous}
                if all(v is not None for v in previous_orders.values()):
                    final=[n for n,v in previous_orders.items() if v==max(previous_orders.values())]
                    if len(final)==1:preceding=final[0]
        row['predecessor']=preceding
        row['start_anchor']=result[preceding]['groups'][-1]['completion_anchor'] if preceding and result[preceding]['groups'] else None
        if row['start_anchor']:
            row['start_anchor']=dict(row['start_anchor'],mission=preceding)
    for name,row in result.items():
        row['successor_maps']=sorted({r['execution_map'] for r in result.values() if r['predecessor']==name and r['execution_map']})
        for i,group in enumerate(row['groups']):
            anchor=row['start_anchor'] if i==0 else row['groups'][i-1]['completion_anchor']
            group['start_anchor']=dict(anchor,mission=anchor.get('mission',name)) if anchor else None
        for group in row['groups']:
            group.pop('completion_anchor')
    payload=dict(version=1,policy='Preceding mission or objective completion location; no nearest station fallback.',
                 source_hashes=hashes,missions=result)
    def timeline(data):
        return {name:(m['mission_set'],[(g['index'],[o['name'] for o in g['objectives']]) for g in m['groups']])
                for name,m in data['missions'].items()}
    compatible=[]
    if previous_catalog and same_native_timeline(previous_catalog,payload):
        compatible=list(previous_catalog.get('bookmark_compatible_catalog_sha256',[]))
        core={k:v for k,v in previous_catalog.items() if k!='bookmark_compatible_catalog_sha256'}
        if core!=payload:compatible.append(hashlib.sha256(previous_bytes).hexdigest())
    if compatible:payload['bookmark_compatible_catalog_sha256']=sorted(set(compatible))
    encoded=(json.dumps(payload,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    digest=hashlib.sha256(encoded).hexdigest()
    legacy_path=MOD/'mission_save_replay.json'
    legacy=json.loads(legacy_path.read_bytes())
    if legacy['catalog_sha256'] not in [digest,*compatible]:
        changed=[k for k in set(hashes)|set(previous_catalog['source_hashes'] if previous_catalog else {})
                 if hashes.get(k)!=(previous_catalog or {}).get('source_hashes',{}).get(k)]
        changed_timelines=[k for k,v in timeline(payload).items() if not previous_catalog or timeline(previous_catalog).get(k)!=v]
        raise RuntimeError('Review legacy replay boundaries before rebuilding: '+json.dumps(dict(changed_sources=changed,changed_timelines=changed_timelines[:10],changed_timeline_count=len(changed_timelines))))
    legacy['catalog_sha256']=digest
    output.write_bytes(encoded)
    legacy_path.write_text(json.dumps(legacy,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(missions=len(result),mission_starts=sum(bool(r['start_anchor']) for r in result.values()),
                         checkpoints=sum(bool(g['start_anchor']) for r in result.values() for g in r['groups']))))

if __name__=='__main__':build()
