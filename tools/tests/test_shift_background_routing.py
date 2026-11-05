"""Offline SHiFT background action routing; no Unreal runtime."""
import ast
from pathlib import Path
import sys
import types

PATH = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/backend_actions.py'
tree = ast.parse(PATH.read_text(encoding='utf-8'))
fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'shift_overlay_control')
namespace = {'__package__': 'routing_test'}
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), str(PATH), 'exec'), namespace)
route = namespace['shift_overlay_control']


def test_background_routes_to_companion(monkeypatch):
    calls=[]
    companion=types.ModuleType('ShiftManagement')
    companion.background_control=lambda mode: calls.append(mode) or {'ok':True, 'mode':mode}
    monkeypatch.setitem(sys.modules,'ShiftManagement',companion)
    for source, target in (('background_start','start'),('background_stop','stop'),
                           ('background_show','show'),('background_status','status')):
        assert route({'mode':source}) == {'ok':True,'mode':target}
    assert calls == ['start','stop','show','status']


def test_missing_companion_fails_closed_and_legacy_remains_routed(monkeypatch):
    monkeypatch.setitem(sys.modules,'ShiftManagement',None)
    assert not route({'mode':'background_start'})['ok']
    package=types.ModuleType('routing_test');package.__path__=[]
    overlay=types.ModuleType('routing_test.shift_overlay');overlay.control=lambda mode:{'ok':True,'legacy':mode}
    package.shift_overlay=overlay
    monkeypatch.setitem(sys.modules,'routing_test',package)
    monkeypatch.setitem(sys.modules,'routing_test.shift_overlay',overlay)
    assert route({'mode':'close'}) == {'ok':True,'legacy':'close'}
