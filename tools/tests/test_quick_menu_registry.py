"""Bridge-safe Quick Menu registry validation and persistence."""

from __future__ import annotations

from tests.test_quick_menu_last_command import _load_backend_actions


def _registry():
    backend = _load_backend_actions()
    return backend.quick_menu_registry


def test_default_layout_matches_registry_grid():
    registry = _registry()
    pages = registry.default_pages()
    assert len(pages) == registry.MAX_PAGES
    assert all(len(page) == registry.SLOTS_PER_PAGE for page in pages)
    assert pages[0][0]["action"] == "max_all"


def test_assign_slot_roundtrip_and_clear():
    registry = _registry()
    assigned = registry.assign_quick_menu_slot({
        "page": 2,
        "slot": 4,
        "action": "max_currency",
        "custom_label": "Money",
        "label_mode": "custom",
    })
    assert assigned["ok"] is True
    assert assigned["layout"]["pages"][2][4]["custom_label"] == "Money"
    cleared = registry.assign_quick_menu_slot({"page": 2, "slot": 4, "action": ""})
    assert cleared["ok"] is True
    assert cleared["layout"]["pages"][2][4] is None


def test_clear_page_preserves_other_pages():
    registry = _registry()
    registry.assign_quick_menu_slot({"page": 1, "slot": 0, "action": "max_all"})
    registry.assign_quick_menu_slot({"page": 2, "slot": 0, "action": "max_currency"})
    cleared = registry.clear_quick_menu_page({"page": 1})
    assert cleared["ok"] is True
    assert all(slot is None for slot in cleared["layout"]["pages"][1])
    assert cleared["layout"]["pages"][2][0]["action"] == "max_currency"


def test_registry_rejects_unknown_actions():
    registry = _registry()
    result = registry.assign_quick_menu_slot({"page": 0, "slot": 0, "action": "totally_unknown"})
    assert result["ok"] is False


def test_registry_sanitizes_payload_and_label():
    registry = _registry()
    source_payload = {"backpack_size": 777, "bank_size": 888, "danger": "drop table"}
    result = registry.assign_quick_menu_slot({
        "page": 0,
        "slot": 0,
        "action": "set_backpack_bank_selected",
        "label_mode": "custom",
        "custom_label": "X" * 100,
        "command_payload": source_payload,
    })
    assert result["ok"] is True
    stored = result["slot"]
    assert len(stored["custom_label"]) == registry.MAX_CUSTOM_LABEL_LEN
    assert stored["payload"] == {"backpack_size": 777, "bank_size": 888}
    source_payload["backpack_size"] = 1
    assert stored["payload"]["backpack_size"] == 777


def test_registry_sanitizes_parameterized_msbt_commands():
    registry = _registry()
    currency = registry.assign_quick_menu_slot({
        "page": 1,
        "slot": 0,
        "action": "give_currency",
        "command_payload": {
            "currency_kind": "eridium",
            "amount": 9999999999,
            "unexpected": "removed",
        },
    })
    assert currency["ok"] is True
    assert currency["slot"]["payload"] == {
        "currency_kind": "eridium",
        "amount": 2147483647,
    }
    level = registry.assign_quick_menu_slot({
        "page": 1,
        "slot": 1,
        "action": "set_level",
        "command_payload": {"xp_track": "specialization", "level": 701},
    })
    assert level["ok"] is True
    assert level["slot"]["payload"] == {"xp_track": "specialization", "level": 701}
    spawn = registry.assign_quick_menu_slot({
        "page": 1,
        "slot": 2,
        "action": "spawn_itempool",
        "custom_label": "Lumberjack",
        "label_mode": "custom",
        "command_payload": {
            "itempool_name": "itempool_dad_ar_05_legendary_Lumberjack_shiny",
            "itempool_count": 3,
            "itempool_level": 60,
            "danger": "drop",
        },
    })
    assert spawn["ok"] is True
    assert spawn["slot"]["payload"] == {
        "itempool_name": "itempool_dad_ar_05_legendary_Lumberjack_shiny",
        "itempool_count": 3,
        "itempool_level": 60,
    }
    travel = registry.assign_quick_menu_slot({
        "page": 1,
        "slot": 3,
        "action": "travel_to_station",
        "command_payload": {"travel_station": "Banjo_P.FT_BanjoStart", "noise": 1},
    })
    assert travel["ok"] is True
    assert travel["slot"]["payload"] == {"travel_station": "Banjo_P.FT_BanjoStart"}
    spawn_ai = registry.assign_quick_menu_slot({
        "page": 1,
        "slot": 4,
        "action": "dev_spawner_spawnai",
        "custom_label": "Boss Pin",
        "label_mode": "custom",
        "command_payload": {
            "dev_ai_name": "Char_BogTitan",
            "dev_ai_count": 2,
            "dev_ai_distance": 400,
            "danger": "nope",
        },
    })
    assert spawn_ai["ok"] is True
    assert spawn_ai["slot"]["payload"]["dev_ai_name"] == "Char_BogTitan"
    assert spawn_ai["slot"]["payload"]["dev_ai_count"] == 2
    assert "danger" not in spawn_ai["slot"]["payload"]


def test_snapshot_exposes_catalog_limits_and_layout():
    registry = _registry()
    snapshot = registry.get_quick_menu_snapshot()
    assert snapshot["ok"] is True
    assert snapshot["limits"]["max_pages"] == registry.MAX_PAGES
    assert snapshot["limits"]["slots_per_page"] == registry.SLOTS_PER_PAGE
    assert snapshot["catalog"]["max_all"]["assignable"] is True
    assert snapshot["catalog"]["max_all"]["needs_player"] is True
    assert snapshot["catalog"]["uvh_boost_tier_7"]["assignable"] is True
    assert snapshot["catalog"]["spawn_itempool"]["assignable"] is True
    assert snapshot["catalog"]["travel_to_map"]["assignable"] is True
    assert snapshot["catalog"]["devperk_7"]["assignable"] is True
    assert "itempool_name" in snapshot["catalog"]["spawn_itempool"]["payload_keys"]


def test_give_serial_local_is_assignable_without_player():
    registry = _registry()
    assert "give_serial_local" in registry.ACTION_CATALOG
    assert "give_serial_local" not in registry.NEEDS_PLAYER_ACTIONS
    assert "give_serial_local" in registry.ALLOWED_PAYLOAD_KEYS
    snapshot = registry.get_quick_menu_snapshot()
    local = snapshot["catalog"]["give_serial_local"]
    named = snapshot["catalog"]["give_serial_selected"]
    assert local["assignable"] is True
    assert local["needs_player"] is False
    assert local["basic"] == "Give Serials: Local"
    assert named["basic"] == "Give Serials: Named Player"
    assert named["needs_player"] is True
    pin = registry.assign_quick_menu_slot({
        "page": 0,
        "slot": 12,
        "action": "give_serial_local",
        "command_payload": {
            "serial_text": "@Uabc",
            "serial_override_level": True,
            "serial_level": 50,
            "danger": "drop",
        },
    })
    assert pin["ok"] is True
    assert pin["slot"]["payload"] == {
        "serial_text": "@Uabc",
        "serial_override_level": True,
        "serial_level": 50,
    }


def test_native_picker_actions_exist_in_catalog():
    registry = _registry()
    missing = [
        action
        for action in registry.NATIVE_PICKER_ACTIONS
        if action not in registry.ACTION_CATALOG
    ]
    assert missing == []
    assert "give_serial_local" not in registry.NATIVE_PICKER_ACTIONS
    assert "location_bookmark_go" not in registry.NATIVE_PICKER_ACTIONS
    assert "location_bookmark_save" in registry.NATIVE_PICKER_ACTIONS
    assert "hoard_start" in registry.NATIVE_PICKER_ACTIONS
    assert "third_person_toggle" in registry.NATIVE_PICKER_ACTIONS


def test_uvh_label_and_targeted_backpack_catalog():
    registry = _registry()
    assert registry.ACTION_CATALOG["uvh_boost_tier_7"]["basic"] == "UVH 7"
    assert "chaos_drop_backpack_targeted" in registry.ACTION_CATALOG
    assert "chaos_drop_backpack_targeted" in registry.NEEDS_PLAYER_ACTIONS
