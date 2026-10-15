"""Guard native completion before dispatch; cancellation must never be used."""
import importlib.util,json
from pathlib import Path
from types import SimpleNamespace as N
import pytest
ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'
def load():
 s=importlib.util.spec_from_file_location('dialogue_native_under_test',ROOT/'dialogue_native.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.files=lambda *_:ROOT;return m
def test_native_completion_uses_normal_end_flag_and_zero_fade(monkeypatch):
 m=load();spec=json.loads((ROOT/'dialogue_native_builds.json').read_text());profile=spec['profiles']['steam-25372571'];calls=[]
 monkeypatch.setattr(m.C,'WINFUNCTYPE',lambda *types:lambda address:lambda *args:calls.append((address,args)))
 p=N(CurrentPerformance=N(DialogThreadID=9),_get_address=lambda:200)
 e=N(profile='steam-25372571',base=1000,read=lambda *a:bytes.fromhex(profile['fingerprint']))
 assert m.complete(p,e,9)
 assert calls[0][0]==1000+int(profile['rva'],16)
 assert calls[0][1][0:2]==(200,1) and calls[0][1][3]==0.
 assert m.C.sizeof(m.FString)==16
def test_changed_thread_and_wrong_executable_do_not_dispatch(monkeypatch):
 m=load();monkeypatch.setattr(m.C,'WINFUNCTYPE',lambda *_:pytest.fail('Native call must be blocked'))
 p=N(CurrentPerformance=N(DialogThreadID=9))
 assert not m.complete(p,N(),8)
 with pytest.raises(RuntimeError):m.complete(p,N(profile='unknown'),9)
 with pytest.raises(RuntimeError):m.complete(p,N(profile='steam-25372571',base=1000,read=lambda *a:bytes(32)),9)
