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
from MattsSDKBoostingTools.native_card_builds import STEAM, EPIC, card_rva, card_gates


class ProbeTest(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.serial = '@U' + 'test' * 8
        self.text = C.create_string_buffer(self.serial.encode())
        self.party = [object()]
        self.thread = 123
        self.fill_error = False
        self.profile = STEAM
        self.storage = tempfile.TemporaryDirectory()
        self.output = Path(self.storage.name) / 'probe.json'
        test = self
        class FString(C.Structure):
            _fields_ = [('data', C.c_void_p), ('num', C.c_int32), ('max', C.c_int32)]
        class Native:
            base = 0
            @property
            def profile(self): return test.profile
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
        self.native_class = Native
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
                if address == card_rva(self.profile,0xBAF88E) and self.fill_error:
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

    def test_guests_allow_native_construction(self):
        self.party.append(object())
        result=self.run_probe()
        self.assertEqual(result['session_players'],2)
        self.assertEqual(result['inventory_insertions'],0)
        self.assertEqual(self.events[-2:],['0x8e1aa38','identity_destroy'])

    def test_epic_selects_only_epic_functions_and_cleans_up(self):
        self.profile = EPIC
        result = self.run_probe(export_model=False, compare_self=False)
        self.assertEqual(result['profile'], EPIC)
        for steam in (0x56D3CCA,0xBABBE2,0xBAF88E,0xB95EC6,0x8E1AA38):
            self.assertIn(hex(card_rva(EPIC,steam)),self.events)
            self.assertNotIn(hex(steam),self.events)
        self.assertEqual(self.events[-3:],['0x8e1fa60','identity_destroy','identity_destroy'])

    def test_epic_failure_retains_cleanup(self):
        self.profile = EPIC
        self.fill_error = True
        with self.assertRaisesRegex(RuntimeError,'simulated fill'):
            self.run_probe(export_model=False,compare_self=False)
        self.assertEqual(self.events[-3:],['0x8e1fa60','identity_destroy','identity_destroy'])

    def test_unknown_build_rejected_before_constructing(self):
        self.profile = 'epic-unknown'
        with self.assertRaisesRegex(RuntimeError,'not supported'):
            self.run_probe(export_model=False)
        self.assertEqual(self.events,['native_init'])

    def test_epic_research_model_does_not_use_steam_fname_pool(self):
        self.profile = EPIC
        with self.assertRaisesRegex(RuntimeError,'model export'):
            self.run_probe()
        self.assertEqual(self.events,['native_init'])

    def test_each_bad_gate_blocks_all_card_function_binding(self):
        from MattsSDKBoostingTools.native_sdk_widget_probe import WIDGET_GATES
        gates=probe.GATES+probe.PRICE_GATES+probe.EMPTY_COMPARISON_GATES+WIDGET_GATES
        for profile in (STEAM,EPIC):
            self.profile=profile
            for gate in gates:
                self.events.clear()
                with self.subTest(profile=profile,gate=hex(gate[0])), \
                     patch.object(C,'WinDLL',return_value=self.kernel), \
                     patch.object(C,'CFUNCTYPE') as bind, \
                     patch.object(probe,'GATES',(gate,)), \
                     patch.object(self.native_class,'read',side_effect=lambda at,n: bytes(n)):
                    with self.assertRaisesRegex(RuntimeError,'Native card function changed'):
                        probe.run(self.serial,None,expected_game_thread=123,export_model=False)
                    bind.assert_not_called()
                    self.assertEqual(self.events,['native_init'])

    def test_success_destroys_model_before_identity(self):
        result = self.run_probe()
        self.assertEqual(self.events[-2:], ['0x8e1aa38', 'identity_destroy'])
        self.assertEqual(result['stages'][-1], 'destroy_identity_complete')
        self.assertEqual(json.loads(self.output.read_text())['inventory_insertions'], 0)

    def test_full_party_retains_native_cleanup(self):
        self.party.extend([object(),object(),object()])
        result=self.run_probe(compare_self=False)
        self.assertEqual(result['session_players'],4)
        self.assertEqual(result['inventory_insertions'],0)
        self.assertEqual(self.events[-3:],['0x8e1aa38','identity_destroy','identity_destroy'])

    def test_no_world_prevents_construction(self):
        self.party.clear()
        with self.assertRaisesRegex(RuntimeError,'active game session'):
            self.run_probe()
        self.assertEqual(self.events,[])

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
        self.check_copy_failure(STEAM)

    def test_epic_copy_failure_uses_epic_text_vtable_and_cleanup(self):
        self.check_copy_failure(EPIC)

    def check_copy_failure(self, profile):
        identity=C.create_string_buffer(0xd8)
        container=C.create_string_buffer(0x200)
        text_object=C.create_string_buffer(16)
        C.c_uint64.from_buffer(identity,0x90).value=C.addressof(container)
        C.c_uint8.from_buffer(container,0x1f8).value=1
        C.c_uint32.from_buffer(container,0x40).value=0x80000000
        address=lambda rva:card_rva(profile,rva)
        C.c_uint64.from_buffer(text_object).value=address(0x9E12790)
        events=[]
        native=types.SimpleNamespace(base=0,profile=profile,read=C.string_at,
            u64=lambda at:C.c_uint64.from_address(at).value)
        def fake_type(*_):
            def bind(address):
                def call(*args):
                    events.append((address,args))
                    if address==card_rva(profile,0x5C4B4F8):
                        C.c_uint64.from_address(args[0]).value=C.addressof(text_object)
                    elif address==card_rva(profile,0x479623A):return 123
                    elif address==card_rva(profile,0x4994E1A):raise RuntimeError('copy failed')
                return call
            return bind
        with patch.object(C,'CFUNCTYPE',side_effect=fake_type):
            with self.assertRaisesRegex(RuntimeError,'copy failed'):
                probe.fill_default_price(native,C.addressof(identity),456,lambda _:None)
        self.assertEqual(events[0][1][1],2147483648)
        self.assertEqual(events[-1],(address(0x4774916),(C.addressof(text_object),)))

    def test_missing_price_cache_prevents_native_calls(self):
        native=types.SimpleNamespace(u64=lambda _:0)
        with patch.object(C,'CFUNCTYPE') as binding:
            with self.assertRaisesRegex(RuntimeError,'not initialized'):
                probe.fill_default_price(native,0,0,lambda _:None)
            binding.assert_not_called()


class WidgetProfileCleanupTest(unittest.TestCase):
    def check_widget(self,profile,fail):
        from MattsSDKBoostingTools.native_sdk_widget_probe import project_default_widget
        storage=C.create_string_buffer(0x608)
        fields=types.SimpleNamespace(PropertySize=0x608,_properties=lambda:[])
        widget=types.SimpleNamespace(_type=fields,_get_address=lambda:C.addressof(storage))
        sdk=types.ModuleType('unrealsdk')
        sdk.make_struct=lambda _:widget
        native=types.SimpleNamespace(profile=profile,base=0,read=C.string_at,
            u64=lambda at:C.c_uint64.from_address(at).value)
        calls=[]
        stages=[]
        address=lambda rva:card_rva(profile,rva)
        def fake_type(*_):
            def bind(rva):
                def invoke(*args):
                    calls.append(rva)
                    if rva==address(0x58CF8C4):
                        C.c_uint64.from_address(args[0]).value=address(0xB9B7700)
                    if rva==address(0x11FC6BA) and fail:
                        raise RuntimeError('simulated widget failure')
                return invoke
            return bind
        with patch.dict(sys.modules,{'unrealsdk':sdk}),patch.object(C,'CFUNCTYPE',side_effect=fake_type):
            if fail:
                with self.assertRaisesRegex(RuntimeError,'simulated widget'):
                    project_default_widget(native,123,stages.append)
            else:
                self.assertEqual(project_default_widget(native,123,stages.append),{})
        self.assertEqual(calls,[address(r) for r in (0x58CF8C4,0x167376E,0x11FC6BA,0x575204C)])
        self.assertEqual(stages[-2:],['widget_owner_destroy_complete','widget_sdk_release_complete'])

    def test_steam_widget_success(self): self.check_widget(STEAM,False)
    def test_steam_widget_failure_cleanup(self): self.check_widget(STEAM,True)
    def test_epic_widget_success(self): self.check_widget(EPIC,False)
    def test_epic_widget_failure_cleanup(self): self.check_widget(EPIC,True)


class PreviewBuildIdentityTest(unittest.TestCase):
    def test_profile_requires_successful_build_and_resets_with_session(self):
        from MattsSDKBoostingTools import native_preview_service as service
        with patch.object(service,'thread_id',return_value=123):
            service.enable(expected_game_thread=123)
            self.assertIsNone(service.status()['build_profile'])
            report={'profile':EPIC,'default_widget':{'Name':'Test'},'elapsed_ms':1}
            with patch.object(service,'run',return_value=report) as run:
                service.preview('@UTest')
                service.preview('@UTest')
                self.assertEqual(run.call_count,1)
            self.assertEqual(service.status()['build_profile'],EPIC)
            self.assertEqual(service.status()['builds'],1)
            service.enable(expected_game_thread=123)
            self.assertIsNone(service.status()['build_profile'])
            self.assertEqual(service.status()['builds'],0)

    def test_failed_build_does_not_claim_epic_success(self):
        from MattsSDKBoostingTools import native_preview_service as service
        with patch.object(service,'thread_id',return_value=123):
            service.enable(expected_game_thread=123)
            with patch.object(service,'run',side_effect=RuntimeError('unsupported')):
                with self.assertRaisesRegex(RuntimeError,'unsupported'):
                    service.preview('@UTest')
            self.assertIsNone(service.status()['build_profile'])
            self.assertEqual(service.status()['builds'],0)


if __name__ == '__main__': unittest.main()
