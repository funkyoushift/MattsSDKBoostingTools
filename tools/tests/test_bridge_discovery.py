"""Real-socket regression tests for reserved ports and endpoint publication."""
import json
import socket
import urllib.request
import urllib.error
import pytest
from test_bridge_perf_bounds import _load_bridge

def test_reserved_port_fallback_identity_and_cleanup(monkeypatch,tmp_path):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    bridge=_load_bridge()
    original=bridge.ThreadingHTTPServer
    attempts=[]
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1',0));free=reserve.getsockname()[1]
    def bind(address,handler):
        attempts.append(address[1])
        if address[1]==49774:raise PermissionError(10013,'Windows reserved port')
        return original(address,handler)
    monkeypatch.setattr(bridge,'ThreadingHTTPServer',bind)
    monkeypatch.setattr(bridge,'BRIDGE_PORTS',(49774,free))
    monkeypatch.setattr(bridge,'_listen_host',lambda:'127.0.0.1')
    try:
        bridge._start_http_listen()
        assert attempts==[49774,free]
        record=json.loads(bridge._endpoint_file().read_text(encoding='utf-8'))
        assert record['port']==free and bridge.mobile_lan._PORT==free
        url=f'http://127.0.0.1:{free}'
        with urllib.request.urlopen(url+'/bridge-info') as response:
            info=json.load(response)
        assert info['started'] and info['instance']==record['instance']
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(urllib.request.Request(url+'/status',headers={'X-MSBT-Instance':'stale'}))
        assert error.value.code==401
    finally:bridge._stop_http_listen()
    assert not bridge._endpoint_file().exists()

def test_all_reserved_ports_report_failure(monkeypatch,tmp_path):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    bridge=_load_bridge()
    def denied(*args):raise PermissionError(10013,'reserved')
    monkeypatch.setattr(bridge,'ThreadingHTTPServer',denied)
    with pytest.raises(OSError,match='No bridge port available'):
        bridge._start_http_listen()
    assert not bridge._started and not bridge._endpoint_file().exists()
