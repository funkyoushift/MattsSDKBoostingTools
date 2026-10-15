"""Native normal-performance completion; same path as provider audio/timer end.

3189a6 timer completion and 8877c80 audio completion pass completed=true to
31838e; StopDialog RPC passes false. Manager receives interrupted=!completed.
Exact Steam/Epic function comparisons are in dialogue_native_builds.json.
"""
import ctypes as C
import json
from importlib.resources import files

class FString(C.Structure):
    _fields_=[('data',C.c_void_p),('count',C.c_int32),('capacity',C.c_int32)]

def complete(provider,engine,expected_thread):
    if int(provider.CurrentPerformance.DialogThreadID)!=expected_thread or expected_thread<=0:
        return False
    spec=json.loads(files(__package__).joinpath('dialogue_native_builds.json').read_text())
    profile=spec['profiles'].get(engine.profile)
    if not profile:raise RuntimeError('Dialogue completion is unavailable for this executable')
    address=engine.base+int(profile['rva'],16)
    if engine.read(address,32).hex()!=profile['fingerprint']:
        raise RuntimeError('Native dialogue completion fingerprint differs')
    reason=FString()
    C.WINFUNCTYPE(None,C.c_void_p,C.c_ubyte,C.c_void_p,C.c_float)(address)(
        provider._get_address(),1,C.byref(reason),0.)
    return True
