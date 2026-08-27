from pathlib import Path
import json
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_qr():
    import importlib.util
    src = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "qr_lite.py"
    spec = importlib.util.spec_from_file_location("qr_lite_roundtrip", src)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_qr_lite_roundtrip_jsqr(tmp_path):
    node = subprocess.run(["node", "-v"], capture_output=True, text=True)
    if node.returncode != 0:
        pytest.skip("node is required for jsQR roundtrip")
    qr = _load_qr()
    payload = '{"v":2,"name":"MSBT","hosts":["192.168.1.10"],"port":49774,"n":"ABCD1234"}'
    matrix_path = tmp_path / "matrix.json"
    payload_path = tmp_path / "payload.txt"
    matrix_path.write_text(json.dumps(qr.encode(payload)), encoding="utf-8")
    payload_path.write_text(payload, encoding="utf-8")
    result = subprocess.run(
        ["node", str(ROOT / "tools" / "qr_jsqr_roundtrip.js"), str(matrix_path), str(payload_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "DECODE_OK" in result.stdout
