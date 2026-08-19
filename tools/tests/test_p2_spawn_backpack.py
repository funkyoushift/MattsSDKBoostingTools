"""P2 spawn-near / item-pool knobs / challenge multi / IO fold / backpack undo."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "backend_actions.py"
SPAWN_HELPERS = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "spawn_helpers.py"
ITEM_POOLS = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "item_pool_spawning.py"
REGISTRY = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "quick_menu_registry.py"
HTML = ROOT / "electron_poc" / "renderer.html"
JS = ROOT / "electron_poc" / "renderer.js"


def test_spawn_helpers_include_selected_anchor():
    source = SPAWN_HELPERS.read_text(encoding="utf-8")
    assert 'SPAWN_ANCHORS = ("local", "selected", "party", "npc_nearest")' in source
    assert 'if mode == "selected":' in source
    assert "def _selected_pawn" in source


def test_item_pool_spit_and_anchor_helpers_exist():
    source = ITEM_POOLS.read_text(encoding="utf-8")
    assert "ITEM_POOL_SPIT_DIRECTIONS" in source
    assert "def item_pool_spit_offsets" in source
    assert "def _anchor_player_pose" in source
    assert "direction: str = \"forward\"" in source


def test_backend_itempool_and_challenge_payloads():
    source = BACKEND.read_text(encoding="utf-8")
    assert "def _challenge_ids_from_payload" in source
    assert 'payload.get("challenge_ids")' in source
    assert "itempool_delay" in source
    assert "itempool_items_per_tick" in source
    assert "itempool_spit" in source
    assert "def chaos_undo_empty_backpack" in source
    assert "def chaos_clear_empty_backpack_memory" in source
    assert "elif key in (\"chaos_undo_empty_backpack\", \"backpack_undo_delete\"):" in source
    assert "elif key in (\"chaos_clear_empty_backpack_memory\", \"backpack_clear_deleted_memory\"):" in source
    assert "def _zipimport_reload_hint" in source
    assert "_WORLD_BM_PATH" in source
    assert "/Game/Maps/WorldLevels/World_P.World_P:PersistentLevel.IO_VendingMachine_BlackMarket" in source
    assert "from unrealsdk import find_object" in source
    assert "def _duplicate_world_black_market" in source
    assert "def _copy_bm_script_data" in source
    assert 'list(snapshot.get("equipped") or []) + list(snapshot.get("backpack") or [])' in source
    assert "camera_tick.register(\"black_market\"" in source
    assert "from Squ1ggsBoostingTools.bridge_actions_extended import black_market" in source
    assert "oak_dual IO_VendingMachine_BlackMarket" in source
    assert "_backpack_delete_memory.pop(key, None)" in source
    assert "_backpack_delete_memory.pop(int(idx), None)" in source


def test_quick_menu_registry_has_undo_and_pool_knobs():
    source = REGISTRY.read_text(encoding="utf-8")
    assert '"chaos_undo_empty_backpack"' in source
    assert '"chaos_clear_empty_backpack_memory"' in source
    assert '"itempool_delay"' in source
    assert '"itempool_spit"' in source


def test_electron_ui_wires_p2_controls():
    html = HTML.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    assert 'id="boostSpawnAnchor"' in html
    assert 'id="challengeListSelect" class="list-select" size="8" multiple' in html
    assert 'id="itempoolDelay"' in html
    assert 'id="itempoolItemsPerTick"' in html
    assert 'id="itempoolSpit"' in html
    assert 'data-dev-part="setup-io"' in html
    assert 'id="devShowIoCategoryBtn"' in html
    assert 'data-action="chaos_undo_empty_backpack"' in html
    assert 'data-action="chaos_clear_empty_backpack_memory"' in html
    assert 'id="deletedBackpackStatus"' in html
    assert "function selectedChallengeIds" in js
    assert "function setSpawnAnchor" in js
    assert "function itemPoolKnobPayload" in js
    assert "function applyDeletedBackpackFromStatus" in js
    assert "async function runEmptyBackpackWithCapture" in js
    assert "async function runUndoEmptyBackpack" in js
    assert "async function captureBackpackSerialsForCurrentTarget" in js
    assert "backpackSerialsFromRows([...(state.invEquipped || []), ...(state.invBackpack || [])])" in js
    assert '"chaos_undo_empty_backpack"' in js
    assert "Interactive Objects" in js
    assert 'Runs Squiggs\' oak_dual IO_VendingMachine_BlackMarket spawn twice' in html
