"""Two build-guarded local experiments. No trainer execution or external writes.

Code allocations are intentionally retained until process exit after use: removing
the entry jump must never free code which another call could still be returning
through. This local prototype does not establish worker-thread quiescence.
"""
import ctypes
from ctypes import wintypes
import struct
from .farming_profiles import PROFILES
from .guaranteed_drops import NativeMemory
from .farming_builds import BUILDS
REVISION=2

class Region(ctypes.Structure):
    _fields_=[('BaseAddress',ctypes.c_void_p),('AllocationBase',ctypes.c_void_p),
        ('AllocationProtect',wintypes.DWORD),('padding',wintypes.DWORD),
        ('RegionSize',ctypes.c_size_t),('State',wintypes.DWORD),
        ('Protect',wintypes.DWORD),('Type',wintypes.DWORD),('padding2',wintypes.DWORD)]

def rel32(target, after):
    delta=target-after
    if not -(2**31)<=delta<2**31: raise ValueError('Native jump outside rel32 range')
    return struct.pack('<i',delta)

def make_code(name, code, data, site, original):
    result=bytearray(b'\x9c') # preserve flags around the added predicate
    if name=='glide_duration':
        result+=b'\x48\x3b\x3d'+rel32(data,code+len(result)+7) # cmp rdi, [owner]
        result+=b'\x0f\x85\0\0\0\0';branch=len(result)-4
        result+=bytes.fromhex('f3 0f 10 78 30') # timer maximum
        result+=bytes.fromhex('f3 0f 5c 3d')+rel32(data+8,code+len(result)+8)
        result+=bytes.fromhex('f3 0f 11 b8 c8 00 00 00')
    elif name=='legendary_roll':
        result+=bytes.fromhex('81 3f 00 00 b4 42') # exact trainer predicate: signed float bits >= 90
        result+=b'\x0f\x8c\0\0\0\0';branch=len(result)-4
        result+=bytes.fromhex('b8 fe 7f 00 00')
    else: raise ValueError('Unknown qualified hook')
    result[branch:branch+4]=rel32(code+len(result),code+branch+4)
    result+=b'\x9d'
    if name=='legendary_roll':
        # Relocate the original RIP-relative divisor without changing registers.
        divisor=site+len(original)+struct.unpack('<i',original[13:17])[0]
        result+=original[:9]+b'\x50\x48\xb8'+struct.pack('<Q',divisor)+bytes.fromhex('f3 0f 5e 00 58')
    else:result+=original
    result+=b'\xff\x25\0\0\0\0'+struct.pack('<Q',site+len(original))
    return bytes(result)

class NativeHook:
    def __init__(self,name,memory_factory=NativeMemory):
        self.name=name;self.profile=PROFILES[name];self.factory=memory_factory
        self.memory=None;self.owned=False;self.allocation=0;self.ready=False;self.patch=b'';self.error=''
    def allocate(self):
        api=self.memory.api
        api.VirtualAlloc.argtypes=(ctypes.c_void_p,ctypes.c_size_t,wintypes.DWORD,wintypes.DWORD)
        api.VirtualAlloc.restype=ctypes.c_void_p
        allocation=api.VirtualAlloc(None,0x2000,0x3000,0x04)
        if not allocation:raise RuntimeError('Native code allocation failed')
        return int(allocation)
    def check_context(self):
        p=self.profile;current=self.memory.read(self.memory.base+p['rva'],len(p['context']))
        expected=p['context']
        if self.owned:expected=self.patch+expected[len(self.patch):]
        if current!=expected:raise RuntimeError('Native context changed; refusing another mod\'s code')
    def enable(self,owner=0):
        try:
            if self.memory is None:self.memory=self.factory()
            self.memory.validate()
            if self.name=='legendary_roll':self.profile=BUILDS[getattr(self.memory,'build','steam-25372571')]['legendary_roll']
            self.check_context()
            if self.owned:return self.status()
            original=self.profile['original'];site=self.memory.base+self.profile['rva']
            if not self.allocation:
                self.allocation=self.allocate()
            if not self.ready:
                code=make_code(self.name,self.allocation,self.allocation+0x1000,site,original)
                self.memory.write(self.allocation,code)
                old=wintypes.DWORD()
                if not self.memory.api.VirtualProtect(self.allocation,0x1000,0x20,ctypes.byref(old)):
                    raise RuntimeError('Cannot protect lab code as execute/read')
                self.ready=True
            self.memory.write(self.allocation+0x1000,struct.pack('<Qf',owner,.5))
            self.patch=b'\xff\x25\0\0\0\0'+struct.pack('<Q',self.allocation)+b'\x90'*(len(original)-14)
            self.owned=True
            self.memory.write(site,self.patch)
            self.check_context();self.error=''
            return self.status()
        except Exception as exc:
            message=str(exc)
            if self.owned:
                result=self.disable()
                if not result['ok']:message+='; rollback: '+result['error']
            self.error=message
            return self.status(ok=False)
    def disable(self):
        try:
            if self.owned:
                p=self.profile;site=self.memory.base+p['rva'];current=self.memory.read(site,len(self.patch))
                if current not in (self.patch,p['original']):raise RuntimeError('Foreign native patch; restore refused')
                if current==self.patch:self.memory.write(site,p['original'])
                if self.memory.read(site,len(p['original']))!=p['original']:raise RuntimeError('Restore readback failed')
                self.memory.restore_protections();self.owned=False
            self.error='';return self.status()
        except Exception as exc:self.error=str(exc);return self.status(ok=False)
    def status(self,ok=True):
        active=False
        if self.owned:
            try:self.check_context();active=True
            except Exception as exc:self.error=str(exc);ok=False
        return dict(ok=ok,active=active,owned=self.owned,error=self.error,allocation_retained=bool(self.allocation),scope='host process' if self.name=='legendary_roll' else 'local movement component')

_hooks={}
def hook(name):
    if name not in _hooks:_hooks[name]=NativeHook(name)
    return _hooks[name]
