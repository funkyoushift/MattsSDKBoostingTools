"""Bridge-safe Quick Menu registry validation and persistence."""

from __future__ import annotations

from tests.test_quick_menu_last_command import _load_backend_actions


def _registry():
    backend = _load_backend_actions()
    return backend.quick_menu_registry


def test_default_layout_is_five_pages_by_twelve_slots():
    registry = _registry()
    pages = registry.default_pages()
    assert len(pages) == 5
    assert all(len(page) == 12 for page in pages)
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


def test_registry_rejects_loot_pool_and_unknown_actions():
    registry = _registry()
    for action in ("spawn_itempool", "totally_unknown"):
        result = registry.assign_quick_menu_slot({"page": 0, "slot": 0, "action": action})
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


def test_snapshot_exposes_catalog_limits_and_layout():
    registry = _registry()
    snapshot = registry.get_quick_menu_snapshot()
    assert snapshot["ok"] is True
    assert snapshot["limits"] == {"max_pages": 5, "slots_per_page": 12}
    assert snapshot["catalog"]["max_all"]["assignable"] is True
    assert snapshot["catalog"]["max_all"]["needs_player"] is True
    assert snapshot["catalog"]["uvh_boost_tier_7"]["assignable"] is True
    assert snapshot["catalog"].get("spawn_itempool") is None
