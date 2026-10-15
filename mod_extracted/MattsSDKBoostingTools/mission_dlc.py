"""Read-only DLC entitlement attributes; never grant or alter access.

Source DLCEntitlementValueResolver attributes distinguish actor, local and session
contexts. Actor and session results were compared in a mixed-access live lobby.
"""
import json
from importlib.resources import files

DATA = json.loads(files(__package__).joinpath('mission_dlc_catalog.json').read_text())


def merge_reports(native, attributes):
    """Require agreement per player/pack; an unavailable pack is not a run failure."""
    result = {}
    for key, source in native.items():
        report = dict(source, players=[dict(p) for p in source['players']])
        established = attributes.get(key)
        if established is not None:
            by_id = {p['player_id']: p['access'] for p in established['players']}
            disagreements = []
            for player in report['players']:
                other = by_id.get(player['player_id'], 'unknown')
                if player['access'] != other:
                    disagreements.append(player['player'])
                player['access'] = ('missing' if 'missing' in (player['access'], other) else
                                    'enabled' if player['access'] == other == 'enabled' else 'unknown')
            report['allowed'] = bool(report['players']) and source['allowed'] and established['allowed']
            report['access_checks_disagree'] = disagreements
            report['blocking_players'] = [p['player'] for p in report['players'] if p['access'] != 'enabled']
            if not report['allowed']:
                report['reason'] = ('DLC access checks disagree for ' + ', '.join(disagreements)
                                    if disagreements else established['reason'] if not established['allowed'] else source['reason'])
        result[key] = report
    # An attribute-only pack has no independently qualified native definition.
    for key, source in attributes.items():
        if key not in result:
            result[key] = dict(source, allowed=False, reason='Native DLC access is unconfirmed')
    return result


def inspect(rows, *, engine=None):
    import unrealsdk
    try:
        library = unrealsdk.find_object('GbxAttributeBlueprintLibrary', '/Script/GbxEngine.Default__GbxAttributeBlueprintLibrary')
    except Exception:
        library = None
    result = {}
    for pack, definition in DATA['packs'].items():
        # Some content (Tuba) has a qualified native definition but no
        # recovered actor/session attribute. Do not invent an attribute name.
        if not definition.get('attribute'):
            continue
        players = []
        sessions = []
        for row in rows:
            try:
                value = library.GetValueOfAttributeAsInteger(AttributeDef=definition['attribute'], ContextSource=row['pc'], DefaultValue=-99)
                session = library.GetValueOfAttributeAsInteger(AttributeDef=definition['attribute'] + '_Session', ContextSource=row['pc'], DefaultValue=-99)
            except Exception:
                value = session = -99
            players.append(dict(player=row['label'], player_id=int(row['state'].PlayerId),
                                access='enabled' if value == 1 else 'missing' if value == 0 else 'unknown'))
            sessions.append(session)
        missing = [p['player'] for p in players if p['access'] == 'missing']
        unknown = any(p['access'] == 'unknown' for p in players)
        allowed = bool(players) and not missing and not unknown and all(v == 1 for v in sessions)
        result[pack] = dict(pack=pack, title=definition['title'], allowed=allowed, players=players,
                            blocking_players=missing, reason=(('Game reports no access: ' + ', '.join(missing)) if missing else
                            'DLC access not confirmed for the whole lobby' if not allowed else 'All players have access'))
    if engine is not None:
        from . import progress_access
        return merge_reports(progress_access.inspect(engine, rows), result)
    return result


def requirement(name, report):
    mapping = next((v for n, v in DATA['missions'].items() if n.casefold() == name.casefold()), None)
    if mapping is None:
        return None
    pack = mapping['pack']
    return report.get(pack) or dict(pack=pack, title=DATA['packs'][pack]['title'], allowed=False,
                                   blocking_players=[], reason='DLC access is unconfirmed')
