import ctypes
import importlib.util
from pathlib import Path
import threading
import types
import unittest
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / 'afk_lobby/shift_background_native.py'
spec = importlib.util.spec_from_file_location('shift_background_native', PATH)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class NativeTests(unittest.TestCase):
    def setUp(self):
        self.view = m.NativeShiftView.__new__(m.NativeShiftView)
        self.view._thread = None; self.view._owner = None; self.view.base = 0x10000000
        self.ident = (10,20,30,100,200,300); self.values = [25,25,25]; self.canvas=2; self.calls=[]
        self.view._inspect = lambda:(self.ident, tuple(self.values), self.canvas, self.values[2] == 25)
        def setter(widget, value):
            self.calls.append((widget,value)); self.values[self.ident[3:].index(widget)] = value
        self.view._set=setter
    def test_order_visibility_and_restoration(self):
        self.view.bind_thread(); result=self.view.enter()
        self.assertEqual([1,1,1],result['visibility']); self.assertFalse(result['visible']); self.assertTrue(result['owned'])
        self.assertEqual([(300,1),(100,1),(200,1)],self.calls)
        self.canvas=19
        self.assertEqual(19,self.view.inspect()['canvas_visibility'])
        self.assertTrue(self.view.restore()['restored'])
        self.assertEqual([(100,25),(200,25),(300,25)],self.calls[-3:]);self.assertFalse(self.view.owned)
    def test_entry_requires_canvas_visible_and_thread(self):
        with self.assertRaises(RuntimeError):self.view.enter()
        self.view.bind_thread();self.canvas=25
        with self.assertRaises(RuntimeError):self.view.enter()
        self.assertFalse(self.view.owned)
        self.canvas=2;self.view._thread=-1
        with self.assertRaises(RuntimeError):self.view.enter()
    def test_partial_failure_retains_ownership_for_retry(self):
        self.view.bind_thread();orig=self.view._set
        def fail(widget,value):
            if widget==200 and value==1:raise OSError('failed')
            orig(widget,value)
        self.view._set=fail
        with self.assertRaises(OSError):self.view.enter()
        self.assertTrue(self.view.owned);self.assertEqual([1,25,1],self.values)
        self.view._set=orig;self.view.restore();self.assertEqual([25,25,25],self.values)
    def test_restore_failure_keeps_ownership_then_retry(self):
        self.view.bind_thread();self.view.enter();orig=self.view._set
        def fail(widget,value):
            if widget==200 and value==25:raise OSError('failed')
            orig(widget,value)
        self.view._set=fail
        with self.assertRaises(OSError):self.view.restore()
        self.assertTrue(self.view.owned);self.assertEqual([25,1,1],self.values)
        self.view._set=orig;self.view.restore();self.assertFalse(self.view.owned)
    def test_close_and_identity_change_never_use_stale_widgets(self):
        self.view.bind_thread();self.view.enter();self.values=[2,2,2];self.calls=[]
        self.assertTrue(self.view.restore()['released_closed']);self.assertEqual([],self.calls)
        self.values=[25,25,25];self.view.enter();self.calls=[];self.ident=(11,20,30,100,200,300)
        with self.assertRaises(m.IdentityChanged):self.view.restore()
        self.assertFalse(self.view.owned);self.assertEqual([],self.calls)
    def test_canvas_change_does_not_block_restore_and_bad_value_does(self):
        self.view.bind_thread();self.view.enter();self.canvas=0;self.values[0]=4
        with self.assertRaises(RuntimeError):self.view.restore()
        self.assertTrue(self.view.owned);self.values[0]=1;self.view.restore()
    def test_constructor_verifies_hash_without_uobject_access(self):
        class Function:
            def __init__(self, fn): self.fn=fn
            def __call__(self,*args): return self.fn(*args)
        def filename(handle, buf, size): buf.value='game.exe'; return len(buf.value)
        fake = types.SimpleNamespace(GetModuleHandleW=Function(lambda _:0x10000000),
            GetModuleFileNameW=Function(filename),GetCurrentProcess=Function(lambda:1),
            ReadProcessMemory=Function(lambda *args:0))
        digest=types.SimpleNamespace(update=lambda _:None,hexdigest=lambda:m.EXPECTED_HASH)
        sdk=types.SimpleNamespace(find_object=lambda *args: (_ for _ in ()).throw(AssertionError('unexpected UObject access')))
        with mock.patch.object(ctypes,'WinDLL',return_value=fake,create=True), mock.patch.object(m.hashlib,'sha256',return_value=digest), mock.patch('builtins.open',mock.mock_open(read_data=b'game')):
            instance=m.NativeShiftView(sdk)
        self.assertEqual(0x10000000,instance.base);self.assertFalse(instance.owned)
        digest.hexdigest=lambda:'0'*64
        with mock.patch.object(ctypes,'WinDLL',return_value=fake,create=True), mock.patch.object(m.hashlib,'sha256',return_value=digest), mock.patch('builtins.open',mock.mock_open(read_data=b'game')):
            with self.assertRaises(RuntimeError):m.NativeShiftView(sdk)
    def test_bind_thread_rejects_different_thread(self):
        self.view.bind_thread();self.view._thread=-1
        with self.assertRaises(RuntimeError):self.view.bind_thread()
    def test_native_attribute_alignment_and_thread(self):
        self.view._set = m.NativeShiftView._set.__get__(self.view)
        with self.assertRaises(RuntimeError):self.view._set(100,1)
        self.view.bind_thread();seen=[]
        def factory(*args):
            def bind(addr):
                def invoke(widget,ptr):
                    self.assertEqual(0,ptr.value%8);seen.append(ctypes.string_at(ptr,24))
                return invoke
            return bind
        with mock.patch.object(ctypes,'WINFUNCTYPE',factory,create=True):self.view._set(100,1);self.view._set(100,25)
        self.assertEqual(bytes([1,1])+bytes(22),seen[0]);self.assertEqual(bytes([25,1])+bytes(22),seen[1])
    def test_fingerprint_layout_and_snapshot_checks(self):
        self.assertEqual(32,len(m.SETTER_BYTES));self.assertEqual(0xfe254e,m.SETTER)
        base=self.view.base
        pointers={base+0xcb98ab0:10,10+0x28:20,20:base+m.OWNER_VTABLE,20+0x188:40,
                  40:base+m.LISTENER_VTABLE,40+0x50:500,500:base+m.CANVAS_VTABLE,
                  40+0x60:300,300:base+m.BACKGROUND_VTABLE,20+0x1a8:100,100:base+m.SAFE_VTABLE,
                  20+0x1b8:200,200:base+m.OVERLAY_VTABLE,
                  base+m.SAFE_VTABLE+0x1c0:base+m.SETTER,base+m.OVERLAY_VTABLE+0x1c0:base+m.SETTER,
                  base+m.BACKGROUND_VTABLE+0x1c0:base+m.SETTER}
        constants=dict(m.VISIBILITY_CONSTANTS)
        def read(addr,length):
            if addr==base+m.SETTER:return m.SETTER_BYTES
            if addr==557:return bytes([2])
            if addr in (157,257,357):return bytes([25])
            return bytes([constants[addr-base]])
        self.view._read=read;self.view._u64=lambda addr:pointers[addr]
        self.view.sdk=types.SimpleNamespace(find_object=lambda cls,path:types.SimpleNamespace(_get_address=lambda:20) if cls=='ShiftUI' else types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(IsVisible=lambda:True)))
        self.view._inspect=m.NativeShiftView._inspect.__get__(self.view)
        self.assertEqual([25,25,25],self.view.inspect()['visibility'])
        constants[0xc96b23a]=99
        with self.assertRaises(RuntimeError):self.view.inspect()

if __name__=='__main__':unittest.main()
