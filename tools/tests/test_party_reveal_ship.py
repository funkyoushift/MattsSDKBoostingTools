"""Party Reveal / Host Clear Fog are product buttons, not pyexec-only."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "mod_extracted" / "MattsSDKBoostingTools"
ELECTRON = ROOT / "electron_poc"


def test_party_hops_are_the_proven_663():
    hops = json.loads((SDK / "fod_party_hops.json").read_text(encoding="utf-8"))
    assert len(hops) == 663
    assert hops[0] == [-345876, -258568, 13152]


def test_party_reveal_uses_shared_camera_tick_and_standup():
    source = (SDK / "fod_party_reveal.py").read_text(encoding="utf-8")
    assert "camera_tick.set_needed" in source
    assert "BlueprintModifyCamera" not in source
    assert "LineTraceSingle" not in source
    assert "stood up at host" in source
    assert "Spectator" in source
    assert "def start(" in source
    assert "def abort(" in source


def test_host_clear_fog_does_not_hide_overlay():
    backend = (SDK / "backend_actions.py").read_text(encoding="utf-8")
    start = backend.index("def fog_of_war_clear")
    body = backend[start : backend.index("\ndef party_reveal_start")]
    assert "_nfow.clear_fog" not in body
    assert "_fod.reveal_live_map" in body
    assert "Host Clear Fog" in body


def test_three_fog_buttons_in_panel_and_handlers():
    html = (ELECTRON / "renderer.html").read_text(encoding="utf-8")
    backend = (SDK / "backend_actions.py").read_text(encoding="utf-8")
    registry = (SDK / "quick_menu_registry.py").read_text(encoding="utf-8")
    assert 'data-action="party_reveal_start"' in html
    assert 'data-action="party_reveal_abort"' in html
    assert 'data-action="fog_of_war_clear">Host Clear Fog' in html
    assert 'data-action="fog_of_war_on">Hide Fog' in html
    for key in (
        "party_reveal_start",
        "party_reveal_abort",
        "fog_of_war_clear",
        "fog_of_war_on",
    ):
        assert f'key == "{key}"' in backend
        assert f'"{key}"' in registry
