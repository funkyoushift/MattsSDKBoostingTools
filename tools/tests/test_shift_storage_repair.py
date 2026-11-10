"""Synthetic settings only; no game or private settings access."""
import json
import http.client
import os
from pathlib import Path
import sys
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
from test_shift_storage_http import StorageHTTPTests, mod


class StorageRepairTests(StorageHTTPTests):
    def test_flush_failure_never_publishes_or_replaces_settings(self):
        with mock.patch.object(mod.os, 'fsync', side_effect=OSError('injected flush failure')):
            self.assertFalse(mod._initialize({'settings': {}, 'protectedPlayers': ['Keep']}))
        self.assertFalse(mod.CONFIG_PATH.exists())
        self.assertTrue(mod._initialize({'settings': {}, 'protectedPlayers': ['Keep']}))
        before = mod.CONFIG_PATH.read_bytes()
        with mock.patch.object(mod.os, 'fsync', side_effect=OSError('injected flush failure')):
            with self.assertRaises(ValueError):
                mod._process_save({'settings': {}, 'protectedPlayers': []})
        self.assertEqual(before, mod.CONFIG_PATH.read_bytes())
        self.assertEqual(['Keep'], mod._data['protectedPlayers'])
        self.assertEqual([mod.CONFIG_PATH], list(mod.CONFIG_DIR.iterdir()))

    def test_failed_publication_leaves_no_file_and_allows_retry(self):
        operation = 'rename' if os.name == 'nt' else 'link'
        payload = {'settings': {}, 'protectedPlayers': ['Fixture'], 'reviewed': True, 'initialize': True}
        with mock.patch.object(mod.os, operation, side_effect=OSError('injected publication failure')):
            self.assertFalse(mod._initialize(payload))
        self.assertFalse(mod.CONFIG_PATH.exists())
        self.assertEqual([], list(mod.CONFIG_DIR.iterdir()))
        mod._load()
        self.assertTrue(mod._initialize(payload))
        mod._load()
        self.assertEqual(['Fixture'], mod._data['protectedPlayers'])

    def test_partial_temporary_write_never_publishes_partial_json(self):
        real = mod.os.fdopen
        class BrokenWrite:
            def __init__(self, *args): self.file = real(*args)
            def __enter__(self): return self
            def __exit__(self, *args): self.file.close()
            def write(self, data):
                self.file.write(data[:5])
                raise OSError('injected disk full')
        with mock.patch.object(mod.os, 'fdopen', BrokenWrite):
            self.assertFalse(mod._initialize({'settings': {}, 'protectedPlayers': []}))
        self.assertFalse(mod.CONFIG_PATH.exists())
        self.assertEqual([], list(mod.CONFIG_DIR.iterdir()))

    def test_late_destination_is_not_replaced(self):
        operation = 'rename' if os.name == 'nt' else 'link'
        original = getattr(mod.os, operation)
        def raced(source, target):
            mod.CONFIG_PATH.write_bytes(b'other writer')
            return original(source, target)
        with mock.patch.object(mod.os, operation, side_effect=raced):
            self.assertFalse(mod._initialize({'settings': {}, 'protectedPlayers': []}))
        self.assertEqual(b'other writer', mod.CONFIG_PATH.read_bytes())
        self.assertEqual([mod.CONFIG_PATH], list(mod.CONFIG_DIR.iterdir()))

    def test_failed_edit_preserves_previous_json(self):
        initial = {'settings': {}, 'protectedPlayers': ['Keep'], 'reviewed': True}
        self.assertTrue(mod._initialize(initial))
        before = mod.CONFIG_PATH.read_bytes()
        with mock.patch.object(mod.os, 'replace', side_effect=OSError('injected edit failure')):
            with self.assertRaises(ValueError):
                mod._process_save({'settings': {}, 'protectedPlayers': []})
        self.assertEqual(before, mod.CONFIG_PATH.read_bytes())
        self.assertEqual(['Keep'], mod._data['protectedPlayers'])
        self.assertEqual([mod.CONFIG_PATH], list(mod.CONFIG_DIR.iterdir()))

    def test_revision_and_foreground_stop_acknowledgement(self):
        self.assertEqual('msbt-shift-20261110', self.call()[1]['integration'])
        mod._page_command = {'id': 'b'*32, 'mode': 'stop', 'deadline': float('inf')}
        try:
            with self.assertRaises(ValueError):
                mod._ack_page_stop({'mode': 'ack_stop', 'command_id': 'c'*32})
            self.assertIsNotNone(mod._page_command)
            mod._ack_page_stop({'mode': 'ack_stop', 'command_id': 'b'*32})
            self.assertIsNone(mod._page_command)
            mod._ack_page_stop({'mode': 'ack_stop', 'command_id': 'b'*32})
        finally:
            mod._page_command = None

    def test_expired_command_reports_failure_without_claiming_applied(self):
        mod._page_command = {'id': 'b'*32, 'mode': 'start', 'deadline': 0}
        try:
            state = mod._background_status()
            self.assertNotIn('command', state)
            self.assertIn('did not confirm', state['command_error'])
        finally:
            mod._page_command = None
            mod._page_command_error = ''

    def test_stop_ack_http_requires_instance_and_exact_pending_command(self):
        def ack(identifier, instance):
            connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
            connection.request('POST', '/shift-background',
                               json.dumps({'mode': 'ack_stop', 'command_id': identifier}),
                               {'X-MSBT-Shift-Instance': instance})
            response = connection.getresponse()
            result = response.status, json.loads(response.read())
            connection.close()
            return result
        mod._page_command = {'id': 'b'*32, 'mode': 'stop', 'deadline': float('inf')}
        try:
            self.assertEqual(403, ack('b'*32, 'wrong')[0])
            self.assertEqual(400, ack('c'*32, mod._instance)[0])
            self.assertIsNotNone(mod._page_command)
            status, body = ack('b'*32, mod._instance)
            self.assertEqual(200, status)
            self.assertIsNone(mod._page_command)
            self.assertNotIn('command_pending', body['background'])
            self.assertFalse(mod.CONFIG_PATH.exists())
        finally:
            mod._page_command = None
