"""Control-flow checks only; mocks do not establish native ABI or live parity."""
import ctypes as C
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

pkg=types.ModuleType('MattsSDKBoostingTools')
pkg.__path__=[str(Path(__file__).resolve().parents[2]/'mod_extracted/MattsSDKBoostingTools')]
sys.modules.setdefault('MattsSDKBoostingTools',pkg)
from MattsSDKBoostingTools import native_sdk_card_probe as probe


class ProbeTest(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.serial = '@U' + 'test' * 8
        self.text = C.create_string_buffer(self.serial.encode())
        self.party = [object()]
        self.thread = 123
        self.fill_error = False
        self.storage = tempfile.TemporaryDirectory()
        self.output = Path(self.storage.name) / 'probe.json'
        test = self
        class FString(C.Structure):
            _fields_ = [('data', C.c_void_p), ('num', C.c_int32), ('max', C.c_int32)]
        class Native:
            profile = 'steam-25372571'
            base = 0
            def __init__(self): test.events.append('native_init')
            def read(self, at, size): return C.string_at(at, size)
            def u64(self, at): return C.c_uint64.from_address(at).value
            def construct(self, at, value):
                test.events.append('construct')
                C.c_uint64.from_address(at + 0xA0).value = C.addressof(test.text)
                C.c_uint64.from_address(at + 0xB0).value = len(test.serial)
                C.c_uint64.from_address(at + 0xB8).value = len(test.serial)
                return True
            def destroy(self, at): test.events.append('identity_destroy')
            def insert(self, *args): raise AssertionError('Preview attempted insertion')
        direct = types.ModuleType('MattsSDKBoostingTools.direct_inventory')
        direct.NativeInventory, direct.FString = Native, FString
        party = types.ModuleType('MattsSDKBoostingTools.party_helpers')
        party._gbc_session_world_and_gamestate = lambda: (None, types.SimpleNamespace(PlayerArray=self.party))
        class ThreadFunction:
            def __call__(inner): return test.thread
        self.kernel = types.SimpleNamespace(GetCurrentThreadId=ThreadFunction())
        self.modules = patch.dict(sys.modules, {
            'MattsSDKBoostingTools.direct_inventory': direct,
            'MattsSDKBoostingTools.party_helpers': party,
        })
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.addCleanup(self.storage.cleanup)

    def fake_type(self, *signature):
        def bind(address):
            def call(*args):
                self.events.append(hex(address))
                if address == 0xBAF88E and self.fill_error:
                    raise RuntimeError('simulated fill failure')
            return call
        return bind

    def run_probe(self, **options):
        with patch.object(C, 'WinDLL', return_value=self.kernel), \
             patch.object(C, 'CFUNCTYPE', side_effect=self.fake_type), \
             patch.object(probe, 'GATES', ()), \
             patch.object(probe, 'EMPTY_COMPARISON_GATES', ()), \
             patch.object(probe, 'read_model', return_value={'display_groups': [], 'strings': []}):
            return probe.run(self.serial, self.output, expected_game_thread=123, **options)

    def test_wrong_thread_prevents_native_construction(self):
        self.thread = 456
        with self.assertRaisesRegex(RuntimeError, 'game thread'): self.run_probe()
        self.assertEqual(self.events, [])

    def test_guests_prevent_native_construction(self):
        self.party.append(object())
        with self.assertRaisesRegex(RuntimeError, 'solo session'): self.run_probe()
        self.assertEqual(self.events, [])

    def test_success_destroys_model_before_identity(self):
        result = self.run_probe()
        self.assertEqual(self.events[-2:], ['0x8e1aa38', 'identity_destroy'])
        self.assertEqual(result['stages'][-1], 'destroy_identity_complete')
        self.assertEqual(json.loads(self.output.read_text())['inventory_insertions'], 0)

    def test_fill_failure_still_destroys_both(self):
        self.fill_error = True
        with self.assertRaisesRegex(RuntimeError, 'simulated fill'): self.run_probe()
        self.assertEqual(self.events[-2:], ['0x8e1aa38', 'identity_destroy'])

    def test_journal_failure_does_not_skip_cleanup(self):
        with patch.object(Path, 'write_text', side_effect=OSError('disk error')):
            with self.assertRaisesRegex(RuntimeError, 'receipt'): self.run_probe()
        self.assertEqual(self.events[-2:], ['0x8e1aa38', 'identity_destroy'])

    def test_empty_comparison_is_destroyed_after_model_before_identity(self):
        result=self.run_probe(compare_self=False)
        self.assertIn('0xb95ec6',self.events)
        self.assertEqual(self.events[-3:],['0x8e1aa38','identity_destroy','identity_destroy'])
        self.assertEqual(result['stages'][-4:],['destroy_comparison_begin','destroy_comparison_complete',
                                              'destroy_identity_begin','destroy_identity_complete'])

    def test_fill_failure_cleans_up_empty_comparison(self):
        self.fill_error=True
        with self.assertRaisesRegex(RuntimeError,'simulated fill'):
            self.run_probe(compare_self=False)
        self.assertEqual(self.events[-3:],['0x8e1aa38','identity_destroy','identity_destroy'])


class PriceCleanupTest(unittest.TestCase):
    def test_copy_failure_releases_owned_text_and_preserves_unsigned_price(self):
        identity=C.create_string_buffer(0xd8)
        container=C.create_string_buffer(0x200)
        text_object=C.create_string_buffer(16)
        C.c_uint64.from_buffer(identity,0x90).value=C.addressof(container)
        C.c_uint8.from_buffer(container,0x1f8).value=1
        C.c_uint32.from_buffer(container,0x40).value=0x80000000
        C.c_uint64.from_buffer(text_object).value=0x9E12790
        events=[]
        native=types.SimpleNamespace(base=0,read=C.string_at,
            u64=lambda at:C.c_uint64.from_address(at).value)
        def fake_type(*_):
            def bind(address):
                def call(*args):
                    events.append((address,args))
                    if address==0x5C4B4F8:
                        C.c_uint64.from_address(args[0]).value=C.addressof(text_object)
                    elif address==0x479623A:return 123
                    elif address==0x4994E1A:raise RuntimeError('copy failed')
                return call
            return bind
        with patch.object(C,'CFUNCTYPE',side_effect=fake_type):
            with self.assertRaisesRegex(RuntimeError,'copy failed'):
                probe.fill_default_price(native,C.addressof(identity),456,lambda _:None)
        self.assertEqual(events[0][1][1],2147483648)
        self.assertEqual(events[-1],(0x4774916,(C.addressof(text_object),)))

    def test_missing_price_cache_prevents_native_calls(self):
        native=types.SimpleNamespace(u64=lambda _:0)
        with patch.object(C,'CFUNCTYPE') as binding:
            with self.assertRaisesRegex(RuntimeError,'not initialized'):
                probe.fill_default_price(native,0,0,lambda _:None)
            binding.assert_not_called()


if __name__ == '__main__': unittest.main()
