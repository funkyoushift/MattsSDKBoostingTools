"""Offline SHiFT background action routing; no Unreal runtime."""
import ast
import io
import json
from pathlib import Path
import sys
import types

PATH = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/backend_actions.py'
tree = ast.parse(PATH.read_text(encoding='utf-8'))
fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'shift_overlay_control')
namespace = {'__package__': 'routing_test'}
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), str(PATH), 'exec'), namespace)
route = namespace['shift_overlay_control']

TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
from test_shift_storage_http import mod as storage_mod


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


def test_only_failed_lease_owner_receives_terminal_background_error(monkeypatch):
    owner_token, stale_token = 'a' * 32, 'b' * 32

    class Controller:
        state = 'idle'
        def status(self):
            return {'available':True, 'state':self.state,
                    'reason':'Close other menus and open SHiFT with F10 before starting.', 'token':None}
        def request(self, payload):
            if payload == {'mode':'start', 'token':owner_token}:
                self.state = 'pending'
                return {'ok':True}
            return {'ok':False}

    def post(payload, instance):
        body=json.dumps(payload).encode('utf-8')
        handler=object.__new__(storage_mod._StorageHandler)
        handler.client_address=('127.0.0.1',50000)
        handler.server=types.SimpleNamespace(server_port=47991)
        handler.path='/shift-background'
        handler.headers={'X-MSBT-Shift-Instance':instance,'Content-Length':str(len(body))}
        handler.rfile=io.BytesIO(body)
        handler.close_connection=False
        replies=[]
        handler._authorized=lambda:True
        handler._reply=lambda status,data:replies.append((status,data))
        handler.do_POST()
        assert len(replies)==1
        return replies[0]

    controller=Controller()
    monkeypatch.setattr(storage_mod, '_background', controller)
    monkeypatch.setattr(storage_mod, '_background_terminal_token', None)
    monkeypatch.setattr(storage_mod, '_instance', 'c' * 32)
    monkeypatch.setattr(storage_mod, '_page_command', None)
    monkeypatch.setattr(storage_mod, '_page_command_error', '')
    monkeypatch.setattr(storage_mod, 'peer_is_game', lambda *_:True)

    controller.state='error'
    status, body = post({'mode':'heartbeat'}, 'c' * 32)
    assert status == 400
    assert 'background' not in body
    controller.state='idle'

    status, _ = post({'mode':'start','token':owner_token}, 'c' * 32)
    assert status == 200
    controller.state='error'

    status, body = post({'mode':'heartbeat','token':stale_token}, 'c' * 32)
    assert status == 400
    assert 'background' not in body

    status, body = post({'mode':'heartbeat','token':owner_token}, 'wrong-instance')
    assert status == 403
    assert 'background' not in body

    status, body = post({'mode':'heartbeat','token':owner_token}, 'c' * 32)
    assert status == 409
    assert body['service'] == 'msbt-shift-storage'
    assert body['instance'] == 'c' * 32
    assert body['terminal'] == 'owned-error'
    assert body['background']['state'] == 'error'
    assert body['background']['reason'].startswith('Close other menus')
    assert body['background']['token'] is None
