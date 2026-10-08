"""Profile selection/fail-closed checks. Native correctness needs binary/live proof."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('card_builds',ROOT/'mod_extracted/MattsSDKBoostingTools/native_card_builds.py')
builds=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builds)


class BuildProfileTest(unittest.TestCase):
    def test_steam_identity_and_epic_mapping_cover_every_function(self):
        for source,(target,size,steam_hash,epic_hash) in builds.EPIC_FUNCTIONS.items():
            with self.subTest(source=hex(source)):
                gate=((source,source+size,steam_hash),)
                self.assertEqual(builds.card_rva(builds.STEAM,source),source)
                self.assertEqual(builds.card_rva(builds.EPIC,source),target)
                self.assertEqual(builds.card_gates(builds.STEAM,gate),gate)
                self.assertEqual(builds.card_gates(builds.EPIC,gate),((target,target+size,epic_hash),))

    def test_changed_source_evidence_is_not_silently_translated(self):
        for source,(_,size,sh,_) in builds.EPIC_FUNCTIONS.items():
            for gate in ((source,source+size+1,sh),(source,source+size,'0'*64)):
                with self.subTest(gate=gate):
                    with self.assertRaisesRegex(RuntimeError,'evidence mismatch'):
                        builds.card_gates(builds.EPIC,(gate,))

    def test_unmapped_address_never_falls_back_to_steam(self):
        for profile in (builds.STEAM,builds.EPIC):
            with self.assertRaisesRegex(RuntimeError,'Unmapped'):
                builds.card_rva(profile,0x123456)

    def test_unknown_build_never_falls_back(self):
        with self.assertRaisesRegex(RuntimeError,'not supported'):
            builds.card_rva('epic-next',0x56D3CCA)
        with self.assertRaisesRegex(RuntimeError,'not supported'):
            builds.card_gates('epic-next',())

    def test_data_addresses_are_profile_specific(self):
        for source,target in builds.EPIC_DATA.items():
            self.assertEqual(builds.card_rva(builds.STEAM,source),source)
            self.assertEqual(builds.card_rva(builds.EPIC,source),target)


if __name__=='__main__':unittest.main()
