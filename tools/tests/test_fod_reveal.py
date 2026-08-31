"""FoD reveal uses reflection offsets, not hardcoded Cheat Engine addresses."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FOD = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "fod_reveal.py"
BACKEND = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "backend_actions.py"
HTML = ROOT / "electron_poc" / "renderer.html"


def test_fod_reveal_has_memory_write_path():
    source = FOD.read_text(encoding="utf-8")
    assert "def reveal_live_map(" in source
    assert "def prop_offset(" in source
    assert "Offset_Internal" in source
    assert "def _write_f32(" in source
    assert "UnfogRadius" in source
    assert "ServerSetDiscoveryRegion" in source
    assert "_REGION_NAMES" in source
    assert "_LEVEL_NAMES" in source
    assert "_GS_DISC_BIT_ARRAY" in source
    assert "DiscoveryReplicatedBitArray" in source
    assert "blackmarket" in source
    assert "def _fill_gamestate_discovery_array(" in source
    assert "def _fill_fod_cpu_grids(" in source
    assert "def _widen_fod_unfog_radius(" in source
    assert "GbxDiscoveryFODManagerCPU" in source
    assert "_FOD_GRID_COUNT" in source
    assert "_FOD_UNFOG_OFFS" in source
    assert "0xDEAD" not in source
    assert "def _party_roots(" in source


def test_clear_fog_calls_fod_reveal():
    source = BACKEND.read_text(encoding="utf-8")
    assert "from . import fod_reveal as _fod" in source
    assert "_fod.reveal_live_map(pc)" in source
    assert "def _fog_status_dict(" in source


def test_map_travel_copy_mentions_three_fog_buttons():
    html = HTML.read_text(encoding="utf-8")
    assert "Party Reveal uncovers guest maps" in html
    assert "Host Clear Fog fills this machine" in html
    assert "Hide Fog is overlay-only" in html
    assert 'data-action="party_reveal_start">Party Reveal Map' in html
    assert 'data-action="fog_of_war_clear">Host Clear Fog' in html
    assert 'data-action="fog_of_war_on">Hide Fog' in html


if __name__ == "__main__":
    test_fod_reveal_has_memory_write_path()
    test_clear_fog_calls_fod_reveal()
    test_map_travel_copy_mentions_three_fog_buttons()
    print("ok")
