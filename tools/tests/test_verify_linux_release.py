"""Offline verifier-helper checks; these do not qualify native Linux execution."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('verify_linux_release', Path(__file__).resolve().parents[1] / 'verify_linux_release.py')
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


class VerifierHelpers(unittest.TestCase):
    def test_packaged_smoke_rejects_top_level_success_with_broken_updater(self):
        row = {'ok': True, 'packaged': True, 'appVersion': '2.41.2'}
        for updater in ({'enabled': False, 'error': ''},
                        {'enabled': False, 'error': 'module missing'},
                        {'enabled': True, 'error': 'initialization failed'}, None):
            with self.subTest(updater=updater):
                with self.assertRaisesRegex(RuntimeError, 'enabled updater'):
                    verify.validate_packaged_smoke(json.dumps(dict(row, updater=updater)), '2.41.2')

    def test_packaged_smoke_accepts_enabled_updater_and_matching_version(self):
        row = {'ok': True, 'packaged': True, 'appVersion': '2.41.2',
               'updater': {'enabled': True, 'error': ''}}
        verify.validate_packaged_smoke('Electron log\n' + json.dumps(row) + '\n', '2.41.2')
        with self.assertRaises(RuntimeError):
            verify.validate_packaged_smoke(json.dumps(row), '2.41.3')

    def test_asar_reads_offset_and_rejects_truncated_payload(self):
        header = json.dumps({'files': {'package.json': {'size': 3, 'offset': '2'}}}).encode()
        padded = header + b'\0' * ((-len(header)) % 4)
        # Pickle header's size includes its size and string-length words.
        prefix = struct.pack('<IIII', 4, len(padded) + 8, len(padded) + 4, len(header))
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'app.asar'
            archive.write_bytes(prefix + padded + b'xxabc')
            self.assertEqual(verify.asar_read(archive, 'package.json'), b'abc')
            archive.write_bytes(prefix + padded + b'xxa')
            with self.assertRaisesRegex(RuntimeError, 'Truncated ASAR entry'):
                verify.asar_read(archive, 'package.json')

    def test_inventory_detects_changed_bytes_and_added_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'file').write_text('first')
            original = verify.inventory(root)
            (root / 'file').write_text('second')
            self.assertNotEqual(original, verify.inventory(root))
            (root / 'extra').write_text('extra')
            self.assertIn('extra', verify.inventory(root))

    def test_failed_requirement_is_fatal(self):
        with self.assertRaisesRegex(RuntimeError, 'missing required check'):
            verify.require(False, 'missing required check')


if __name__ == '__main__':
    unittest.main()
