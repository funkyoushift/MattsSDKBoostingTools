"""Deterministic fake-WinAPI regression; never queries a real TCP table."""
import ctypes
import importlib.util
from pathlib import Path
import socket
import struct
import sys
import types
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / 'afk_lobby/shift_peer_process.py'
spec = importlib.util.spec_from_file_location('retry_peer_candidate', SOURCE)
peer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(peer)

PID, CLIENT, SERVER = 4242, 50001, 47991

def row(local, remote, owner=PID, state=5, local_addr=None):
    return (state, peer._LOOPBACK if local_addr is None else local_addr,
            socket.htons(local), peer._LOOPBACK, socket.htons(remote), owner)

def table(rows):
    return struct.pack('<I', len(rows)) + b''.join(peer._ROW.pack(*r) for r in rows)

GOOD_ROWS = [row(CLIENT, SERVER), row(SERVER, CLIENT)]

class TableAPI:
    """A sequence of `(is_size_query, return_code, returned_size, bytes)` calls."""
    def __init__(self, steps):
        self.steps = list(steps)
        self.calls = []
    def __call__(self, buffer, size, sort, family, klass, reserved):
        self.calls.append(buffer is None)
        if not self.steps:
            raise AssertionError('Unexpected WinAPI retry')
        query, code, value, body = self.steps.pop(0)
        assert query is (buffer is None)
        assert family == socket.AF_INET and klass == 5 and reserved == 0
        ctypes.cast(size, ctypes.POINTER(ctypes.c_ulong))[0] = value
        if body is not None:
            assert buffer is not None and len(body) <= len(buffer)
            ctypes.memmove(buffer, body, len(body))
        return code

def query(size):
    return (True, 122, size, None)

def fill(rows=GOOD_ROWS):
    body = table(rows)
    return (False, 0, len(body), body)

class TCPTableRetryTests(unittest.TestCase):
    def call(self, steps):
        api = TableAPI(steps)
        library = types.SimpleNamespace(GetExtendedTcpTable=api)
        with mock.patch.object(peer.sys, 'platform', 'win32'), mock.patch.object(
                peer.ctypes, 'WinDLL', return_value=library, create=True):
            result = peer.peer_is_game(('127.0.0.1', CLIENT), SERVER, PID)
        return result, api

    def test_stable_table_accepted_without_retry(self):
        result, api = self.call([query(len(table(GOOD_ROWS))), fill()])
        self.assertTrue(result)
        self.assertEqual([True, False], api.calls)

    def test_growth_between_size_and_fill_requeries_then_checks_identity(self):
        body = table(GOOD_ROWS)
        result, api = self.call([query(4), (False, 122, len(body), None), query(len(body)), fill()])
        self.assertTrue(result, 'A size/fill race must retry the unchanged peer authorization')
        self.assertEqual([True, False, True, False], api.calls)

    def test_two_growth_races_can_recover_on_third_attempt(self):
        body = table(GOOD_ROWS)
        result, api = self.call([query(4), (False, 122, 28, None),
                                 query(28), (False, 122, len(body), None),
                                 query(len(body)), fill()])
        self.assertTrue(result)
        self.assertEqual(6, len(api.calls))

    def test_repeated_growth_exhausts_exactly_three_attempts_fail_closed(self):
        result, api = self.call([query(4), (False, 122, 28, None),
                                 query(28), (False, 122, 52, None),
                                 query(52), (False, 122, 76, None)])
        self.assertFalse(result)
        self.assertEqual(6, len(api.calls))

    def test_other_size_query_error_not_retried(self):
        result, api = self.call([(True, 5, 4, None)])
        self.assertFalse(result)
        self.assertEqual(1, len(api.calls))

    def test_other_fill_error_not_retried(self):
        result, api = self.call([query(52), (False, 5, 52, None)])
        self.assertFalse(result)
        self.assertEqual(2, len(api.calls))

    def test_invalid_initial_sizes_fail_before_allocating(self):
        for size in (0, 3, peer._MAX_TABLE_BYTES + 1):
            with self.subTest(size=size):
                result, api = self.call([query(size)])
                self.assertFalse(result)
                self.assertEqual(1, len(api.calls))

    def test_invalid_growth_sizes_fail_without_further_queries(self):
        for size in (0, 3, peer._MAX_TABLE_BYTES + 1):
            with self.subTest(size=size):
                result, api = self.call([query(52), (False, 122, size, None)])
                self.assertFalse(result)
                self.assertEqual(2, len(api.calls))

    def test_invalid_success_size_or_count_fails_closed(self):
        for step in [(False, 0, 3, None), (False, 0, 53, None),
                     (False, 0, 52, struct.pack('<I', 3) + bytes(48))]:
            with self.subTest(step=step[:3]):
                result, api = self.call([query(52), step])
                self.assertFalse(result)
                self.assertEqual(2, len(api.calls))

    def test_successful_retry_does_not_relax_peer_matching(self):
        cases = {
            'wrong_client_owner': [row(CLIENT, SERVER, PID + 1), row(SERVER, CLIENT)],
            'wrong_server_owner': [row(CLIENT, SERVER), row(SERVER, CLIENT, PID + 1)],
            'missing_reverse': [row(CLIENT, SERVER)],
            'duplicate_client': GOOD_ROWS + [row(CLIENT, SERVER)],
            'duplicate_server': GOOD_ROWS + [row(SERVER, CLIENT)],
            'no_established_side': [row(CLIENT, SERVER, state=8), row(SERVER, CLIENT, state=8)],
            'wrong_address': [row(CLIENT, SERVER, local_addr=0), row(SERVER, CLIENT)],
            'wrong_endpoint': [row(CLIENT + 1, SERVER), row(SERVER, CLIENT)],
        }
        for name, rows in cases.items():
            with self.subTest(name=name):
                body = table(rows)
                result, api = self.call([query(4), (False, 122, len(body), None), query(len(body)), fill(rows)])
                self.assertFalse(result)
                self.assertEqual(4, len(api.calls), 'Authorization checks must run on the successful snapshot')

if __name__ == '__main__':
    unittest.main()
