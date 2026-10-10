"""Specific action outcomes must survive the generic lifecycle status merge."""
import ast
from pathlib import Path
from typing import Any

SOURCE = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/fod_party_reveal.py'


def load_actions(points):
    tree = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in ('start', 'abort')]
    calls = []
    env = dict(Any=Any, _state={}, _load_pts=lambda: points,
               last_status=lambda: dict(message='Party Reveal idle.', running=False, hop=0),
               _set_needed=lambda value: calls.append(value), _ensure_registered=lambda: None,
               get_pc=lambda: None, _pawn_of=lambda *args: None, _loc=lambda obj: None,
               _xyz=lambda obj: (0, 0, 0), _refresh_pawns=lambda: None,
               _pull_home=lambda: calls.append('pull'), _log=lambda text: None)
    exec(compile(tree, str(SOURCE), 'exec'), env)
    return env, calls


def test_missing_hops_keeps_specific_error():
    env, _ = load_actions([])
    result = env['start']()
    assert result['ok'] is False
    assert result['message'] == 'Party Reveal hops file is missing.'
    assert result['running'] is False


def test_missing_guest_keeps_specific_error():
    env, _ = load_actions([(0, 0, 0)])
    result = env['start']()
    assert result['ok'] is False
    assert result['message'] == 'Party Reveal needs a live guest in this session.'


def test_abort_keeps_action_message_and_pull():
    env, calls = load_actions([])
    result = env['abort']()
    assert result['ok'] is True
    assert 'aborted' in result['message']
    assert result['running'] is False
    assert calls == [False, 'pull']
