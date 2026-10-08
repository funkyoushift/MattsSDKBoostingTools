"""Activate via game-thread bridge; independently READ native bytes from Windows.

Run only during an authorized local lab trial. Always requests All Off on exit.
This proves activation/restoration, not execution of the gameplay routine.
"""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import runpy
from client import DATA, request

def main():
    pid=json.loads((DATA/'status.json').read_text())['pid']
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    psapi=ctypes.WinDLL('psapi',use_last_error=True)
    kernel.OpenProcess.argtypes=(wintypes.DWORD,wintypes.BOOL,wintypes.DWORD)
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=(wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t))
    kernel.CloseHandle.argtypes=(wintypes.HANDLE,)
    psapi.EnumProcessModulesEx.argtypes=(wintypes.HANDLE,ctypes.POINTER(ctypes.c_void_p),wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),wintypes.DWORD)
    psapi.GetModuleFileNameExW.argtypes=(wintypes.HANDLE,ctypes.c_void_p,wintypes.LPWSTR,wintypes.DWORD)
    handle=kernel.OpenProcess(0x410,False,pid) # QUERY_INFORMATION | VM_READ only
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    rows=[]
    try:
        modules=(ctypes.c_void_p*2048)();needed=wintypes.DWORD()
        if not psapi.EnumProcessModulesEx(handle,modules,ctypes.sizeof(modules),ctypes.byref(needed),3):raise ctypes.WinError()
        base=None
        for module in modules[:min(2048,needed.value//ctypes.sizeof(ctypes.c_void_p))]:
            name=ctypes.create_unicode_buffer(32768)
            if psapi.GetModuleFileNameExW(handle,module,name,len(name)) and Path(name.value).name.lower()=='borderlands4.exe':base=module;break
        if base is None:raise RuntimeError('Game executable module not found')
        def read(address,size):
            buffer=ctypes.create_string_buffer(size);count=ctypes.c_size_t()
            if not kernel.ReadProcessMemory(handle,address,buffer,size,ctypes.byref(count)) or count.value!=size:raise ctypes.WinError()
            return buffer.raw
        profiles=runpy.run_path(str(Path(__file__).parent/'MSBTFarmingLab/profiles.py'))['PROFILES']
        for feature,profile in profiles.items():
            if feature!='legendary_roll':continue # glide now uses a reflected movement attribute
            address=base+profile['rva'];original=profile['original']
            before=read(address,len(original));assert before==original,(feature,'not initially original')
            on=request({'op':'set','feature':feature,'enabled':True})
            assert on['ok'] and on['result']['ok'],on
            patched=read(address,len(original))
            assert patched[:6]==bytes.fromhex('ff 25 00 00 00 00') and patched!=before
            off=request({'op':'set','feature':feature,'enabled':False})
            restored=read(address,len(original))
            assert off['ok'] and off['result']['ok'] and restored==original
            rows.append(dict(feature=feature,rva=hex(profile['rva']),before=before.hex(),active=patched.hex(),restored=restored.hex(),ok=True))
    finally:
        cleanup=request({'op':'off'})
        kernel.CloseHandle(handle)
    result=dict(pid=pid,read_only_process_handle=True,features=rows,all_off=cleanup)
    output=Path('work/farming-native-independent-readback.json');output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'pid':pid,'verified_features':[r['feature'] for r in rows],'all_off':cleanup['result']['ok'],'receipt':str(output)}))

if __name__=='__main__':main()
