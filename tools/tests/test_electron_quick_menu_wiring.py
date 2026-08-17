"""Static regression checks for the Electron Quick Menu editor wiring."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
ELECTRON = ROOT / "electron_poc"


def test_quick_menu_editor_ids_are_unique_and_wired():
    html = (ELECTRON / "renderer.html").read_text(encoding="utf-8")
    js = (ELECTRON / "renderer.js").read_text(encoding="utf-8")
    ids = (
        "tab-quick-menu",
        "quickMenuSlotGrid",
        "quickMenuActionSelect",
        "quickMenuSaveSlotBtn",
        "quickMenuAddModal",
        "quickMenuAddConfirmBtn",
    )
    for element_id in ids:
        assert len(re.findall(rf'id="{re.escape(element_id)}"', html)) == 1
        assert element_id in js


def test_editor_uses_bridge_registry_and_validated_mutations():
    js = (ELECTRON / "renderer.js").read_text(encoding="utf-8")
    assert 'path: "/quick_menu"' in js
    assert '"quick_menu_assign_slot"' in js
    assert '"quick_menu_clear_page"' in js
    assert "installQuickMenuAddButtons" in js
    assert 'add.textContent = "+ QM"' in js
    assert 'quickMenuNode("giveCurrencyBtn")' in js
    assert 'quickMenuNode("setLevelBtn")' in js
    assert 'document.querySelectorAll("[data-movement-action]")' in js


def test_instant_actions_have_qm_pins_and_rebindable_sdk_hotkeys():
    js = (ELECTRON / "renderer.js").read_text(encoding="utf-8")
    assert 'decorateQuickMenuActionButton(els.instantDropsToggleBtn, "instant_drops_toggle")' in js
    assert 'decorateQuickMenuActionButton(els.instantHoldsToggleBtn, "instant_holds_toggle")' in js

    registry = (
        ROOT
        / "mod_extracted"
        / "MattsSDKBoostingTools"
        / "quick_menu_registry.py"
    ).read_text(encoding="utf-8")
    assert '"instant_drops_toggle": {"basic": "Instant Drops"' in registry
    assert '"instant_holds_toggle": {"basic": "Instant Holds"' in registry

    sdk = (
        ROOT
        / "mod_extracted"
        / "MattsSDKBoostingTools"
        / "instant_click_holds.py"
    ).read_text(encoding="utf-8")
    assert '"MSBT Toggle Instant Drops"' in sdk
    assert '"MSBT Toggle Instant Holds"' in sdk
    assert "kb_toggle_drops" in sdk
    assert "kb_toggle_holds" in sdk


def test_spawnables_and_travel_are_assignable_and_wired():
    registry = (
        ROOT
        / "mod_extracted"
        / "MattsSDKBoostingTools"
        / "quick_menu_registry.py"
    ).read_text(encoding="utf-8")
    assert '"spawn_itempool"' in registry
    assert '"travel_to_map"' in registry
    assert '"give_serial_selected"' in registry
    js = (ELECTRON / "renderer.js").read_text(encoding="utf-8")
    assert 'decorateQuickMenuActionButton(\n    document.getElementById("spawnItempoolBtn")' in js or (
        'getElementById("spawnItempoolBtn")' in js and '"spawn_itempool"' in js
    )
    assert '"travel_to_map"' in js
    assert '"travel_to_station"' in js
    assert "quickMenuItemPoolPayload" in js
    assert "quickMenuSerialPayload" in js


def test_electron_pin_last_controls_are_wired():
    html = (ELECTRON / "renderer.html").read_text(encoding="utf-8")
    js = (ELECTRON / "renderer.js").read_text(encoding="utf-8")
    for element_id in (
        "quickMenuPinLastBtn",
        "quickMenuRepeatDropBtn",
        "quickMenuLockToggleBtn",
        "quickMenuLastCommand",
    ):
        assert f'id="{element_id}"' in html
        assert element_id in js
    assert "pinLastCommandToSelectedSlot" in js
    assert "repeatLastDropFromQuickMenu" in js
    assert '"repeat_last_drop"' in js
    assert '"set_drop_player_lock"' in js


def test_dev_spawner_targets_are_quick_menu_assignable():
    registry = (
        ROOT
        / "mod_extracted"
        / "MattsSDKBoostingTools"
        / "quick_menu_registry.py"
    ).read_text(encoding="utf-8")
    assert '"dev_spawner_spawnai"' in registry
    assert '"dev_ai_name"' in registry
    js = (ELECTRON / "renderer.js").read_text(encoding="utf-8")
    assert "quickMenuDevSpawnerPayload" in js
    assert 'data-dev-spawner-action' in js or "[data-dev-spawner-action]" in js
    assert '"dev_spawner_spawnai"' in js


def test_bl4_and_bookmark_serials_have_quick_menu_wiring():
    html = (ELECTRON / "renderer.html").read_text(encoding="utf-8")
    js = (ELECTRON / "renderer.js").read_text(encoding="utf-8")
    assert 'id="bookmarkQmSelectedBtn"' in html
    assert 'id="bl4QmSelectedBtn"' in html
    assert 'data-qm-serial-source="bookmark"' in html
    assert 'data-qm-serial-source="bl4"' in html
    assert "quickMenuBookmarkSerialPayload" in js
    assert "quickMenuBl4SerialPayload" in js
    assert "openSerialQuickMenuPin" in js
    assert "[data-qm-serial-source]" in js
    qm = (
        ROOT
        / "mod_extracted"
        / "MattsSDKBoostingTools"
        / "quick_menu.py"
    ).read_text(encoding="utf-8")
    assert "DOCK_X" in qm
    assert "C_BTN_GOLD" in qm
    assert "panel_opacity" in qm
    assert "poll_sliders" in qm
