"""Live-mod HTTP requests must wait for game-thread dispatch, without losing OFF."""
import io
import json
import threading
from test_bridge_perf_bounds import _load_bridge


def test_live_mod_handler_does_not_execute_on_http_thread(monkeypatch):
    bridge = _load_bridge()
    body = json.dumps({'action': 'fog_of_war_on', 'timeout': 1}).encode()
    handler = object.__new__(bridge._Handler)
    handler.path = '/action'
    handler.headers = {'Content-Length': str(len(body))}
    handler.rfile = io.BytesIO(body)
    replies, calls = [], []
    handler._send = lambda *args: replies.append(args)
    monkeypatch.setattr(bridge, '_authorized_request', lambda _: (True, '127.0.0.1'))
    monkeypatch.setattr(bridge, '_handle_action', lambda *args: calls.append(threading.get_ident()) or {'ok': True})
    worker = threading.Thread(target=handler.do_POST)
    worker.start()
    worker.join(3)
    assert not worker.is_alive() and calls == []
    assert replies[0][0] == 202 and replies[0][1]['queued']
    bridge._process_pending_actions()
    assert calls == [threading.get_ident()]


def test_menu_intents_preserve_fifo_and_pending_delivery():
    bridge = _load_bridge()
    actions = ['give_serial_selected', 'fog_of_war_on', 'fog_of_war_off']
    for i, action in enumerate(actions):
        bridge._prepare_queue_for_enqueue_locked(action)
        bridge._queue.append({'id':str(i), 'action':action})
    assert [item['action'] for item in bridge._queue] == actions
    bridge._prepare_queue_for_enqueue_locked('give_serial_local')
    assert [item['action'] for item in bridge._queue] == actions[1:]
    bridge._prepare_queue_for_enqueue_locked('max_currency')
    assert [item['action'] for item in bridge._queue] == actions[1:]
