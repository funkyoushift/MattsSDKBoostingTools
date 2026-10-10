"""Timeouts retain observable outcomes without repeating or cancelling actions."""
import io
import json
import threading
from test_bridge_perf_bounds import _load_bridge


def handler(bridge, path, body=None):
    value = object.__new__(bridge._Handler)
    value.path = path
    raw = json.dumps(body or {}).encode()
    value.headers = {'Content-Length': str(len(raw))}
    value.rfile = io.BytesIO(raw)
    value.replies = []
    value._send = lambda *args: value.replies.append(args)
    return value


def test_timeout_then_late_failure_is_retrievable_without_reexecution(monkeypatch):
    b = _load_bridge()
    monkeypatch.setattr(b, '_authorized_request', lambda _: (True, '127.0.0.1'))
    calls = []
    b._handle_action = lambda *args: calls.append(args) or {'ok': False, 'message': 'test failure'}
    h = handler(b, '/action', {'action': 'farming_lab', 'timeout': 1})
    worker = threading.Thread(target=h.do_POST)
    worker.start()
    worker.join(3)
    assert not worker.is_alive()
    code, pending = h.replies[0]
    assert code == 202 and pending['request_id']
    read = handler(b, pending['result_url'])
    read.do_GET()
    assert read.replies[-1][1]['state'] == 'queued'
    b._process_pending_actions()
    read.do_GET()
    receipt = read.replies[-1][1]
    assert receipt['state'] == 'completed'
    assert receipt['result'] == {'ok': False, 'message': 'test failure'}
    read.do_GET()
    assert len(calls) == 1
    assert not b._results


def test_receipts_are_authenticated_and_unknown_is_not_cancelled(monkeypatch):
    b = _load_bridge()
    monkeypatch.setattr(b, '_authorized_request', lambda _: (False, '192.168.1.2'))
    h = handler(b, '/action_result?id=unknown')
    h.do_GET()
    assert h.replies[-1][0] == 401
    monkeypatch.setattr(b, '_authorized_request', lambda _: (True, '127.0.0.1'))
    h.do_GET()
    assert h.replies[-1][0] == 404
    assert not h.replies[-1][1].get('cancelled')


def test_completion_snapshot_survives_waiter_consumption_and_is_bounded():
    b = _load_bridge()
    result = {'ok': True, 'nested': [1]}
    b._store_result_locked('one', result, now=100)
    b._pop_result_locked('one', now=100)
    result['nested'].append(2)
    assert b._action_receipts['one']['result']['nested'] == [1]
    for i in range(b.MAX_RESULTS + 1):
        b._store_result_locked(str(i), {'ok': True}, now=100)
    assert len(b._action_receipts) == b.MAX_RESULTS
    b._prune_action_receipts_locked(now=161)
    assert not b._action_receipts
    b._store_result_locked('big', {'ok': True, 'data': 'x' * b.MAX_RECEIPT_BYTES})
    assert b._action_receipts['big']['result_omitted']
    assert b._action_receipts['big']['action_ok'] is True


def test_queue_replacement_has_explicit_cancelled_receipt():
    b = _load_bridge()
    b._queue.append({'id': 'old', 'action': 'spawn'})
    b._prepare_queue_for_enqueue_locked('max_currency')
    assert b._get_action_receipt_locked('old')['state'] == 'cancelled'
    b._executing_rid = 'running'
    assert b._get_action_receipt_locked('running')['state'] == 'running'
