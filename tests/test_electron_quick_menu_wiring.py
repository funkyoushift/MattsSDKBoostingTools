"""Static regression checks for the Electron Quick Menu editor wiring."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
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
