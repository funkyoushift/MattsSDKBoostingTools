import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import threading
import types
import unittest
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1] / 'afk_lobby'
pkg = types.ModuleType('storage_test_pkg'); pkg.__path__ = [str(ROOT)]; sys.modules[pkg.__name__] = pkg
peer_spec = importlib.util.spec_from_file_location('storage_test_pkg.shift_peer_process', ROOT / 'shift_peer_process.py')
peer = importlib.util.module_from_spec(peer_spec); peer_spec.loader.exec_module(peer)
sys.modules[peer_spec.name] = peer
base = types.ModuleType('mods_base')
base.CoopSupport = types.SimpleNamespace(Unknown=None); base.Game = types.SimpleNamespace(BL4=None)
base.SETTINGS_DIR = Path(tempfile.gettempdir()); base.build_mod = lambda **kwargs: None
base.hook = lambda *args, **kwargs: lambda fn: fn
sdk = types.ModuleType('unrealsdk'); sdk.logging = types.SimpleNamespace(warning=lambda *_: None)
hooks = types.ModuleType('unrealsdk.hooks'); hooks.Type = types.SimpleNamespace(POST=None)
saved = {n: sys.modules.get(n) for n in ('mods_base','unrealsdk','unrealsdk.hooks')}
sys.modules.update({'mods_base':base,'unrealsdk':sdk,'unrealsdk.hooks':hooks})
spec = importlib.util.spec_from_file_location('storage_test_pkg.companion', ROOT / 'shift_storage_companion.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
for name, value in saved.items():
    if value is None: sys.modules.pop(name, None)
    else: sys.modules[name] = value

class StorageHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        mod.CONFIG_DIR = Path(self.tmp.name); mod.CONFIG_PATH = mod.CONFIG_DIR / 'settings.json'
        mod._instance = 'a' * 32; mod._load(); mod.peer_is_game = lambda *_: True
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), mod._StorageHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.tmp.cleanup()
    def call(self, method='GET', data=None, headers=None):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        c.request(method, '/shift-settings', body=data, headers=headers or {})
        r = c.getresponse(); body = json.loads(r.read()); status = r.status; c.close(); return status, body
    def test_first_run_review_and_reopen(self):
        status, state = self.call(); self.assertEqual(200,status); self.assertEqual('missing',state['storageState'])
        self.assertFalse(mod.CONFIG_PATH.exists())
        headers={'X-MSBT-Shift-Instance':mod._instance}
        payload={'settings': {}, 'protectedPlayers': [], 'initialize': True}
        self.assertEqual(400,self.call('POST',json.dumps(payload),headers)[0])
        payload['reviewed']=True
        status,state=self.call('POST',json.dumps(payload),headers)
        self.assertEqual(200,status); self.assertTrue(state['saved']); self.assertTrue(state['reviewed'])
        mod._load(); status,state=self.call(); self.assertTrue(state['storageValid']); self.assertEqual([],state['protectedPlayers'])
        payload={'settings': {}, 'protectedPlayers':['example'], 'reviewed': True}
        self.assertEqual(200,self.call('POST',json.dumps(payload),headers)[0])
        self.assertEqual(['example'],self.call()[1]['protectedPlayers'])
    def test_invalid_and_changed_never_overwritten(self):
        mod.CONFIG_PATH.write_text('{bad', encoding='utf-8'); mod._load()
        original=mod.CONFIG_PATH.read_bytes()
        status,state=self.call();self.assertEqual('invalid',state['storageState'])
        data=json.dumps({'settings':{},'protectedPlayers':[],'reviewed':True,'initialize':True})
        self.assertEqual(400,self.call('POST',data,{'X-MSBT-Shift-Instance':mod._instance})[0])
        self.assertEqual(original,mod.CONFIG_PATH.read_bytes())
    def test_instance_and_body_limit(self):
        self.assertEqual(403,self.call('POST','{}',{'X-MSBT-Shift-Instance':'wrong'})[0])
        self.assertEqual(413,self.call('POST','x'*65537,{'X-MSBT-Shift-Instance':mod._instance})[0])
        self.assertEqual(200,self.call('OPTIONS')[0])
    def test_foreground_heartbeat_returns_verified_terminal_state(self):
        old=mod._background
        mod._background=types.SimpleNamespace(request=lambda request,ready:{'ok':False},
            status=lambda:{'available':True,'state':'foreground','reason':'','token':None})
        try:
            conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
            conn.request('POST','/shift-background',body=json.dumps({'mode':'heartbeat','token':'a'*32}),
                         headers={'X-MSBT-Shift-Instance':mod._instance})
            response=conn.getresponse();data=json.loads(response.read());conn.close()
            self.assertEqual(409,response.status);self.assertFalse(data['ok'])
            self.assertEqual('msbt-shift-storage',data['service']);self.assertEqual(1,data['protocol'])
            self.assertEqual(mod._instance,data['instance']);self.assertEqual('foreground',data['background']['state'])
        finally:mod._background=old

    def test_real_same_process_peer_is_allowed(self):
        mod.peer_is_game = peer.peer_is_game
        self.assertEqual(200, self.call()[0])

    def test_actual_child_with_valid_instance_cannot_create_file(self):
        mod.peer_is_game = peer.peer_is_game
        code = """import http.client,json,sys
c=http.client.HTTPConnection('127.0.0.1',int(sys.argv[1]),timeout=3)
p={'settings':{},'protectedPlayers':[],'reviewed':True,'initialize':True}
c.request('POST','/shift-settings',json.dumps(p),{'X-MSBT-Shift-Instance':sys.argv[2]})
r=c.getresponse();r.read();print(r.status);c.close()
"""
        status = subprocess.check_output([sys.executable, '-c', code, str(self.server.server_port), mod._instance], text=True).strip()
        self.assertEqual('403', status)
        self.assertFalse(mod.CONFIG_PATH.exists())

    def test_wrong_process_rejected_all_methods(self):
        mod.peer_is_game = lambda client, port: peer.peer_is_game(client, port, os.getpid()+1)
        for method in ('GET','POST','OPTIONS'):
            self.assertEqual(403,self.call(method,'{}' if method=='POST' else None)[0])
        self.assertFalse(mod.CONFIG_PATH.exists())

class StorageLifecycleTests(unittest.TestCase):
    def test_enable_is_idempotent_disable_and_reenable(self):
        with tempfile.TemporaryDirectory() as directory:
            mod.CONFIG_DIR = Path(directory); mod.CONFIG_PATH = mod.CONFIG_DIR / 'settings.json'
            original = mod.ThreadingHTTPServer
            mod.ThreadingHTTPServer = lambda address, handler: original(('127.0.0.1', 0), handler)
            try:
                mod._disable(); mod._enable()
                first = mod._server; token = mod._instance
                self.assertIsNotNone(first); self.assertEqual(32, len(token))
                mod._enable(); self.assertIs(first, mod._server)
                mod._disable(); self.assertIsNone(mod._server)
                mod._enable(); self.assertIsNotNone(mod._server)
                self.assertNotEqual(token, mod._instance)
                self.assertFalse(mod.CONFIG_PATH.exists())
            finally:
                mod._disable(); mod.ThreadingHTTPServer = original

if __name__ == '__main__': unittest.main()
