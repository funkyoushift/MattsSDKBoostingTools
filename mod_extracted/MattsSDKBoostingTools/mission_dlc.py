"""Read-only DLC entitlement attributes; never grant or alter access.

Source DLCEntitlementValueResolver attributes distinguish actor, local and session
contexts. Actor and session results were compared in a mixed-access live lobby.
"""
import json
from importlib.resources import files

DATA = json.loads(files(__package__).joinpath('mission_dlc_catalog.json').read_text())


def inspect(rows):
    import unrealsdk
    try:
        library = unrealsdk.find_object('GbxAttributeBlueprintLibrary', '/Script/GbxEngine.Default__GbxAttributeBlueprintLibrary')
    except Exception:
        library = None
    result = {}
    for pack, definition in DATA['packs'].items():
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
    return result


def requirement(name, report):
    mapping = DATA['missions'].get(name)
    return report.get(mapping['pack']) if mapping else None
