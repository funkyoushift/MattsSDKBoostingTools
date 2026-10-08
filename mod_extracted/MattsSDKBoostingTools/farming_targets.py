"""Resolve current party identities without changing the shared selected player."""
import mods_base
from . import party_helpers


def same(a, b):
    return a is not None and b is not None and a._get_address() == b._get_address()


def party():
    host = mods_base.get_pc()
    if host is None or host.Pawn is None or not host.HasAuthority():
        raise RuntimeError('Load a character into your hosted world first')
    world, gs = party_helpers._gbc_session_world_and_gamestate()
    states = list(gs.PlayerArray) if gs is not None else []
    rows = []
    for index, ps in enumerate(states):
        if ps is None:continue
        pc = host if same(ps, host.PlayerState) else party_helpers._gbc_find_pc_for_player_state(ps, world)
        label = party_helpers._gbc_resolve_player_display_name(ps)
        if pc is not None and not same(pc.PlayerState, ps):pc = None
        rows.append(dict(index=index, label=label, pc=pc, host=same(ps, host.PlayerState), state=ps))
    if not rows:
        raise RuntimeError('Current party list is unavailable; refresh status')
    return rows


def resolve(payload, selected=(None, '')):
    scope = payload.get('target_scope', 'selected')
    if scope not in ('local', 'selected', 'all', 'nonhost'):
        raise ValueError('Unknown farming target scope')
    rows = party()
    if scope == 'local':wanted = [r for r in rows if r['host']]
    elif scope == 'all':wanted = rows
    elif scope == 'nonhost':wanted = [r for r in rows if not r['host']]
    else:
        raw = payload.get('target_player')
        if raw is None or str(raw).strip() == '':
            index, name = selected
            if index is None and not name:
                raise RuntimeError('Choose a named player or Local before enabling a farming control')
        else:
            value = str(raw).strip()
            token, separator, name = value.partition('|')
            try:index = int(token)
            except ValueError:index = None;name = value
        wanted = [r for r in rows if (name and r['label'].casefold() == name.casefold()) or
                  (not name and index is not None and r['index'] == index)]
        # A name-bearing request never falls back to an index occupied by someone else.
        if len(wanted) != 1:
            raise RuntimeError('Selected farming player left or is ambiguous; refresh players')
    if not wanted:raise RuntimeError('No players match the farming target scope')
    for row in wanted:
        pc = row['pc']
        if pc is None or pc.Pawn is None or not pc.HasAuthority():
            raise RuntimeError('Farming target is not loaded: ' + row['label'])
        if not same(pc.Pawn.Controller, pc):
            raise RuntimeError('Farming pawn ownership changed: ' + row['label'])
    return wanted


def current(pc, pawn):
    if not same(pc.Pawn, pawn):return False
    return any(same(row['pc'], pc) and same(row['state'], pc.PlayerState) for row in party())
