"""No remote mutations are executed by these tests."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import publish_verified_release as publish


class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.notes = self.root / 'notes.txt'
        self.notes.write_text('Verified release notes')
        self.args = SimpleNamespace(version='2.41.2', source_commit='a' * 40,
            artifacts_dir=self.root, windows_receipt='windows.json', linux_receipt='linux.json',
            live_evidence='live.json', notes=self.notes, build_run='123', repository='owner/repo', publish=False)
        self.item = dict(name='asset.zip', size=4, sha256=publish.sha256_file(self.notes))
        self.record = dict(artifacts=[self.item])

    def api(self, repo, endpoint):
        if endpoint.startswith('git/ref/'):
            return dict(object=dict(type='commit', sha=self.args.source_commit))
        if endpoint.endswith('/jobs?per_page=100'):
            return dict(jobs=[dict(name=n, status='completed', conclusion='success')
                for n in ('windows', 'linux', 'Required Windows and Linux release gate')])
        return dict(status='completed', conclusion='success', head_sha=self.args.source_commit,
                    path='.github/workflows/unified-build.yml')

    def command(self, *args):
        return self.args.source_commit if args[0] == 'git' else '[[]]'

    def test_check_only_does_not_mutate(self):
        with patch.object(publish, 'validate_gate', return_value=self.record) as gate, \
             patch.object(publish, 'verify_ci_artifacts') as ci, \
             patch.object(publish, 'api', side_effect=self.api), \
             patch.object(publish, 'command', side_effect=self.command) as command:
            self.assertFalse(publish.execute(self.args)['published'])
            self.assertTrue(gate.call_args.kwargs['require_live'])
            self.assertFalse(any(c.args[:2] == ('gh', 'release') for c in command.call_args_list))

    def test_gate_failure_prevents_any_remote_access(self):
        with patch.object(publish, 'validate_gate', side_effect=ValueError('tampered artifact')), \
             patch.object(publish, 'command') as command, patch.object(publish, 'api') as api:
            with self.assertRaises(ValueError):
                publish.execute(self.args)
            command.assert_not_called()
            api.assert_not_called()

    def test_failed_build_job_blocks(self):
        original = self.api
        def bad_api(repo, endpoint):
            value = original(repo, endpoint)
            if '/jobs?' in endpoint:
                value['jobs'][0]['conclusion'] = 'failure'
            return value
        with patch.object(publish, 'validate_gate', return_value=self.record), \
             patch.object(publish, 'command', side_effect=self.command), \
             patch.object(publish, 'api', side_effect=bad_api):
            with self.assertRaises(ValueError):
                publish.execute(self.args)

    def test_ci_receipt_binds_exact_four_artifact_hashes(self):
        artifacts = [dict(platform=platform, name=str(index), size=4, sha256='a' * 64)
                     for index, platform in enumerate(('win32', 'win32', 'linux', 'linux'))]
        record = dict(artifacts=artifacts)
        evidence = dict(schema_version=1, status='PASS', version=self.args.version,
                        source_commit=self.args.source_commit, artifacts=artifacts)
        def download(*args):
            self.assertEqual(args[:4], ('gh', 'run', 'download', '123'))
            destination = Path(args[args.index('--dir') + 1])
            (destination / 'release-verification.json').write_text(json.dumps(evidence))
            return ''
        with patch.object(publish, 'command', side_effect=download):
            publish.verify_ci_artifacts(self.args, record)
            original = json.dumps(evidence)
            mutations = [lambda e: e.update(status='FAIL'),
                         lambda e: e.update(source_commit='b' * 40),
                         lambda e: e.update(version='2.41.1'),
                         lambda e: e['artifacts'][0].update(sha256='b' * 64),
                         lambda e: e['artifacts'][0].update(size=5),
                         lambda e: e['artifacts'].pop(),
                         lambda e: e['artifacts'].append(e['artifacts'][0])]
            for index, mutate in enumerate(mutations):
                with self.subTest(case=index):
                    evidence = json.loads(original)
                    mutate(evidence)
                    with self.assertRaises(ValueError):
                        publish.verify_ci_artifacts(self.args, record)

    def test_ci_receipt_failure_blocks_release_checks_and_mutation(self):
        with patch.object(publish, 'validate_gate', return_value=self.record), \
             patch.object(publish, 'api', side_effect=self.api), \
             patch.object(publish, 'command', side_effect=self.command) as calls, \
             patch.object(publish, 'verify_ci_artifacts', side_effect=ValueError('CI hashes differ')):
            with self.assertRaisesRegex(ValueError, 'CI hashes differ'):
                publish.execute(self.args)
            self.assertEqual(len(calls.call_args_list), 1)  # local tag read only

    def test_failed_upload_keeps_draft_unpublished(self):
        self.args.publish = True
        path = self.root / self.item['name']
        path.write_bytes(b'data')
        self.item['sha256'] = publish.sha256_file(path)
        def command(*args):
            if args[:3] == ('gh', 'release', 'upload'):
                raise RuntimeError('upload interrupted')
            return '[[{"id":42,"draft":true,"tag_name":"v2.41.2"}]]'
        with patch.object(publish, 'prepare', return_value=self.record), \
             patch.object(publish, 'api', return_value=dict(id=42, draft=True)), \
             patch.object(publish, 'command', side_effect=command) as calls:
            with self.assertRaisesRegex(RuntimeError, 'draft 42 retained'):
                publish.execute(self.args)
            self.assertFalse(any('--method' in c.args for c in calls.call_args_list))

    def test_draft_lookup_uses_listing_and_checks_publication_response(self):
        self.args.publish = True
        path = self.root / self.item['name']
        path.write_bytes(b'data')
        self.item['sha256'] = publish.sha256_file(path)
        def api(repo, endpoint):
            self.assertNotIn('releases/tags/', endpoint)
            return [dict(self.item, digest='sha256:' + self.item['sha256'])]
        def command(*args):
            if '--paginate' in args:
                return '[[{"id":42,"draft":true,"tag_name":"v2.41.2"}]]'
            if '--method' in args:
                return '{"id":42,"tag_name":"v2.41.2","draft":false,"prerelease":false}'
            return ''
        with patch.object(publish, 'prepare', return_value=self.record), \
             patch.object(publish, 'api', side_effect=api), \
             patch.object(publish, 'command', side_effect=command):
            self.assertTrue(publish.execute(self.args)['published'])
        def unconfirmed(*args):
            if '--method' in args:
                return '{"id":42,"tag_name":"v2.41.2","draft":true,"prerelease":false}'
            return command(*args)
        with patch.object(publish, 'prepare', return_value=self.record), \
             patch.object(publish, 'api', side_effect=api), \
             patch.object(publish, 'command', side_effect=unconfirmed):
            with self.assertRaisesRegex(RuntimeError, 'publication outcome uncertain'):
                publish.execute(self.args)

    def test_missing_draft_reports_tag_and_uncertainty(self):
        self.args.publish = True
        with patch.object(publish, 'prepare', return_value=self.record), \
             patch.object(publish, 'command', return_value='[[]]'):
            with self.assertRaisesRegex(RuntimeError, 'v2.41.2.*draft may exist'):
                publish.execute(self.args)

    def test_tampered_after_gate_stops_upload(self):
        self.args.publish = True
        (self.root / self.item['name']).write_bytes(b'changed')
        with patch.object(publish, 'prepare', return_value=self.record), \
             patch.object(publish, 'api', return_value=dict(id=42, draft=True)), \
             patch.object(publish, 'command', return_value='[[{"id":42,"draft":true,"tag_name":"v2.41.2"}]]') as calls:
            with self.assertRaisesRegex(RuntimeError, 'artifact changed'):
                publish.execute(self.args)
            self.assertEqual(calls.call_count, 2)  # draft creation and read-only listing


if __name__ == '__main__':
    unittest.main()
