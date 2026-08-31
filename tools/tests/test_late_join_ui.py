"""Late-join character UI (990 path) is console stateadd, not a pak."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "mod_extracted" / "MattsSDKBoostingTools"
ELECTRON = ROOT / "electron_poc"

ACTIONS = {
    "load_character_late_join": "MENU_LOAD_CHARACTER_LATE_JOIN",
    "select_character_late_join": "MENU_SELECT_CHARACTER_LATE_JOIN",
    "open_firmware_transfer": "MENU_FIRMWARETRANSFER",
}


def test_late_join_console_states_and_panel_buttons():
    backend = (SDK / "backend_actions.py").read_text(encoding="utf-8")
    registry = (SDK / "quick_menu_registry.py").read_text(encoding="utf-8")
    html = (ELECTRON / "renderer.html").read_text(encoding="utf-8")
    assert "gbx.ui.view.stateadd" in backend
    assert '"MENU_BANK"' in backend
    assert "def open_ui_view_state" in backend
    assert "def reset_gravity_default" in backend
    assert 'sections={"gravity"}' in backend
    travel_start = html.index('data-msbt-panel="travel-main"')
    travel_end = html.index("</section>", travel_start)
    travel = html[travel_start:travel_end]
    assert "load_character_late_join" not in travel
    assert "select_character_late_join" not in travel
    for key, tag in ACTIONS.items():
        assert f'gbx.ui.view.stateadd {tag}' in backend or f'"{tag}"' in backend
        assert f'key == "{key}"' in backend
        assert f'"{key}"' in registry
        assert f'data-action="{key}"' in html
    assert 'data-action="reset_gravity_default"' in html
    assert "def open_late_join_ui" in backend
    assert "host_picker" in backend
    assert "Event_AttemptAction" in backend
    assert "MENU_PAUSE" in backend
    assert "did not open" not in backend
    assert "is an online guest" not in backend
    js = (ELECTRON / "renderer.js").read_text(encoding="utf-8")
    assert "LATE_JOIN_CHARACTER_ACTIONS" in js
    assert "load_character_late_join" in js
    assert "target_player: state.selectedTarget" in js
    assert 'id="lateJoinHint"' in html
    assert "your screen" in html.lower()
    assert "experimental" in html.lower()
    assert "host picker" in html.lower()
    assert "not confirmed" in html.lower()
    assert "azalea" in html.lower()
    assert "sets gravity to 0" in html.lower() or "gravity to 0" in html.lower()


def test_late_join_is_not_a_pak_loader():
    backend = (SDK / "backend_actions.py").read_text(encoding="utf-8")
    html = (ELECTRON / "renderer.html").read_text(encoding="utf-8")
    blob = backend + html
    assert "pakchunk990" not in blob
    assert "hot-pak" not in blob.lower()
    assert "hot_pak" not in blob
