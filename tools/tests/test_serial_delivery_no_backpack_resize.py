"""Serial delivery must not rewrite backpack size, and must blank leftover reward rows."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERIAL = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "serial_rewards.py"
HOOK_GATE = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "hook_gate.py"


def test_serial_delivery_does_not_resize_backpack():
    source = SERIAL.read_text(encoding="utf-8")
    assert "_SERIAL_DELIVERY_BACKPACK_HEADROOM" not in source
    assert "_ensure_backpack_capacity_for_indices" not in source
    assert "set_backpack_size_for_player_state" not in source
    assert "Prepared backpack capacity" not in source


def test_apply_writes_full_chunk_then_clears_leftover_rows():
    source = SERIAL.read_text(encoding="utf-8")
    assert "def _write_serial_numbers(" in source
    assert "def _clear_serial_numbers(" in source
    assert "leftover reward content row" in source
    assert "list(contents)[1:]" in source


def test_hook_gate_keeps_serial_delivery_tick_alive():
    source = HOOK_GATE.read_text(encoding="utf-8")
    assert 'f"{_PACKAGE}.serial_rewards"' in source


if __name__ == "__main__":
    test_serial_delivery_does_not_resize_backpack()
    test_apply_writes_full_chunk_then_clears_leftover_rows()
    test_hook_gate_keeps_serial_delivery_tick_alive()
    print("ok")
