"""Validate source-identical additions reached through existing wait links."""
def review_reused_memberships(original,candidate):
    """Allow only unchanged children reached from existing explicit wait links."""
    if original.keys()!=candidate.keys() or any(original[k]!=candidate[k] for k in original if k!='groups'):raise ValueError('Mission metadata changed')
    if len(original['groups'])!=len(candidate['groups']):raise ValueError('Group count changed')
    definitions={}
    for group in original['groups']:
        for obj in group['objectives']:
            key=obj['name'].casefold()
            if key in definitions and definitions[key]!=obj:raise ValueError('Original child definition is ambiguous')
            definitions[key]=obj
    additions=[]
    for old,new in zip(original['groups'],candidate['groups']):
        if old.keys()!=new.keys() or any(old[k]!=new[k] for k in old if k not in ('objectives','unresolved')):raise ValueError('Group metadata changed')
        if [o for o in new['objectives'] if o in old['objectives']]!=old['objectives']:raise ValueError('Original objectives changed or reordered')
        old_warnings=old.get('unresolved',[]);new_warnings=new.get('unresolved',[])
        if [w for w in new_warnings if w in old_warnings]!=old_warnings:raise ValueError('Existing unresolved evidence changed')
        missing_children={o['name'] for o in new['objectives'] if o not in old['objectives'] and not o.get('completion_anchor')}
        if any(w not in old_warnings and (set(w)!= {'objective','reason'} or w['reason']!='missing_completion_location' or w['objective'] not in missing_children) for w in new_warnings):raise ValueError('Unreviewed unresolved evidence added')
        names=[o['name'].casefold() for o in new['objectives']]
        if len(names)!=len(set(names)):raise ValueError('Duplicate group objective')
        pending=[n.casefold() for o in old['objectives'] for n in o.get('wait_for_objectives') or []];reachable=set()
        while pending:
            key=pending.pop()
            if key in reachable:continue
            reachable.add(key)
            pending.extend(n.casefold() for n in definitions.get(key,{}).get('wait_for_objectives') or [])
        for obj in new['objectives']:
            if obj in old['objectives']:continue
            key=obj['name'].casefold()
            if definitions.get(key)!=obj or key not in reachable:raise ValueError('Added child is changed, new or unrelated to existing wait links')
            additions.append((new['index'],obj['name']))
    return additions
