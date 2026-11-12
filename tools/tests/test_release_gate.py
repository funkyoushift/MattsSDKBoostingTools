"""Release authorization evidence must cover both exact platform builds."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('release_gate', Path(__file__).parents[1] / 'release_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.version = '2.41.2'
        self.commit = 'a' * 40
        self.receipts = {}
        for platform, names in gate.expected_artifacts(self.version).items():
            artifacts = []
            for name in names:
                magic = b'MZ' if name.endswith('.exe') else b'PK\x03\x04' if name.endswith('.zip') else b'\x7fELF' if name.endswith('.AppImage') else b'\x1f\x8b'
                path = self.root / name
                path.write_bytes(magic + b'test payload')
                artifacts.append(dict(name=name, size=path.stat().st_size, sha256=gate.sha256_file(path)))
            self.receipts[platform] = dict(schema_version=1, platform=platform, version=self.version,
                source_commit=self.commit, status='PASS', checks=[dict(name=n, ok=True) for n in gate.REQUIRED_CHECKS[platform]],
                artifacts=artifacts, game_integration=dict(kind='fixtures_only'))
        self.save()

    def save(self):
        for platform, receipt in self.receipts.items():
            (self.root / (platform + '.json')).write_text(json.dumps(receipt), encoding='utf-8')

    def run_gate(self):
        return gate.validate_gate(self.version, self.commit, self.root,
                                  self.root / 'win32.json', self.root / 'linux.json')

    def test_valid_both_platforms_preserves_coverage(self):
        result = self.run_gate()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(len(result['artifacts']), 4)
        self.assertEqual(result['game_integration']['linux']['kind'], 'fixtures_only')

    def test_publication_requires_both_native_candidate_records(self):
        self.assertFalse(self.run_gate()['publication_ready'])
        args = (self.version, self.commit, self.root, self.root / 'win32.json', self.root / 'linux.json')
        with self.assertRaises(ValueError):
            gate.validate_gate(*args, require_live=True)
        evidence = dict(schema_version=1, version=self.version, source_commit=self.commit, platforms={})
        for platform, receipt in self.receipts.items():
            evidence['platforms'][platform] = dict(status='PASS', kind='live', tested_at='2026-11-12T15:00:00Z',
                evidence='Manual native verification receipt reference',
                artifact_sha256={a['name']: a['sha256'] for a in receipt['artifacts']})
        path = self.root / 'live.json'
        path.write_text(json.dumps(evidence))
        self.assertTrue(gate.validate_gate(*args, live_evidence=path, require_live=True)['publication_ready'])
        original = json.dumps(evidence)
        mutations = [lambda e: e.update(source_commit='b' * 40),
                     lambda e: e.update(version='2.41.1'),
                     lambda e: e['platforms'].pop('linux'),
                     lambda e: e['platforms']['linux'].update(kind='fixtures_only'),
                     lambda e: e['platforms']['linux'].update(status='FAIL'),
                     lambda e: e['platforms']['linux'].update(evidence='  '),
                     lambda e: e['platforms']['linux'].update(tested_at='yesterday'),
                     lambda e: e['platforms']['linux'].update(artifact_sha256={})]
        for index, mutate in enumerate(mutations):
            with self.subTest(case=index):
                candidate = json.loads(original)
                mutate(candidate)
                path.write_text(json.dumps(candidate))
                with self.assertRaises(ValueError):
                    gate.validate_gate(*args, live_evidence=path, require_live=True)

    def test_missing_linux_receipt(self):
        (self.root / 'linux.json').unlink()
        with self.assertRaises(OSError):
            self.run_gate()

    def test_receipt_failures(self):
        mutations = {
            'failed check': lambda r: r['checks'][0].update(ok=False),
            'missing check': lambda r: r['checks'].pop(),
            'stale commit': lambda r: r.update(source_commit='b' * 40),
            'wrong version': lambda r: r.update(version='2.41.1'),
            'wrong platform': lambda r: r.update(platform='win32'),
            'failed status': lambda r: r.update(status='FAIL'),
            'traversal': lambda r: r['artifacts'][0].update(name='../escape.AppImage'),
            'windows traversal': lambda r: r['artifacts'][0].update(name='..\\escape.AppImage'),
            'duplicate': lambda r: r['artifacts'].append(r['artifacts'][0].copy()),
            'extra artifact': lambda r: r['artifacts'][0].update(name='other.AppImage'),
            'unknown coverage': lambda r: r.update(game_integration={}),
        }
        original = json.dumps(self.receipts['linux'])
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                self.receipts['linux'] = json.loads(original)
                mutate(self.receipts['linux'])
                self.save()
                with self.assertRaises(ValueError):
                    self.run_gate()

    def test_missing_asset(self):
        (self.root / self.receipts['linux']['artifacts'][0]['name']).unlink()
        with self.assertRaises(ValueError):
            self.run_gate()

    def test_tampered_asset(self):
        path = self.root / self.receipts['linux']['artifacts'][0]['name']
        path.write_bytes(b'X' * path.stat().st_size)
        with self.assertRaises(ValueError):
            self.run_gate()

    def test_format_checked_even_with_matching_hash(self):
        item = self.receipts['linux']['artifacts'][0]
        path = self.root / item['name']
        path.write_bytes(b'bad image')
        item.update(size=path.stat().st_size, sha256=gate.sha256_file(path))
        self.save()
        with self.assertRaises(ValueError):
            self.run_gate()


if __name__ == '__main__':
    unittest.main()
