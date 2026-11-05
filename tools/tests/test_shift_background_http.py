import http.client
import json
import sys
import threading
import time
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from test_shift_storage_http import StorageHTTPTests, mod

class Controller:
    def __init__(self): self.calls=[]
    def status(self): return {'available':True,'state':'idle','reason':'','token':None}
    def request(self, payload, ready):
        self.calls.append((payload,ready,threading.get_ident()))
        if payload.get('mode') == 'start' and not ready: return {'ok':False}
        return {'ok':True}

class BackgroundHTTPTests(StorageHTTPTests):
    def setUp(self):
        super().setUp(); self.controller=Controller(); mod._background=self.controller; mod._page_command=None; mod._disabling=False
    def tearDown(self):
        mod._background=None;mod._page_command=None;super().tearDown()
    def route(self, path, method='GET', body=None, headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        c.request(method,path,body=body,headers=headers or {}); r=c.getresponse(); data=json.loads(r.read()); status=r.status;c.close();return status,data
    def test_background_paths_gating_and_instance(self):
        self.assertEqual(200,self.route('/shift-background','OPTIONS')[0])
        first=self.route('/shift-settings')[1]['background']
        self.assertTrue(first['available']); self.assertRegex(first['start_token'],r'^[0-9a-f]{32}$')
        self.assertNotEqual(first['start_token'],self.route('/shift-settings')[1]['background']['start_token'])
        self.assertEqual(200,self.route('/shift-background')[0])
        payload=json.dumps({'mode':'start','token':'a'*32}); headers={'X-MSBT-Shift-Instance':mod._instance}
        self.assertEqual(403,self.route('/shift-background','POST',payload,{'X-MSBT-Shift-Instance':'bad'})[0])
        self.assertEqual(400,self.route('/shift-background','POST',payload,headers)[0]); self.assertFalse(self.controller.calls[-1][1])
        mod._initialize({'settings':{},'protectedPlayers':[],'reviewed':True})
        mod._page_command={'id':'f'*32,'mode':'start','deadline':time.monotonic()+10}
        code,state=self.route('/shift-background','POST',payload,headers)
        self.assertEqual(200,code);self.assertTrue(self.controller.calls[-1][1]);self.assertNotIn('command',state['background'])
        self.assertNotEqual(self.controller.calls[-1][2],threading.get_ident())
    def test_command_expiry_and_peer_protection(self):
        mod._page_command={'id':'f'*32,'mode':'stop','deadline':time.monotonic()-1}
        self.assertNotIn('command',self.route('/shift-background')[1]['background'])
        mod.peer_is_game=lambda *_:False
        for method in ('GET','POST','OPTIONS'):
            self.assertEqual(403,self.route('/shift-background',method,'{}' if method=='POST' else None)[0])

if __name__ == '__main__': unittest.main()
