"""Local external-control bridge for Matt's SDK Boosting Tools.

Runs inside the BL4 SDK mod.  External tools call http://127.0.0.1:49774
and the bridge queues actions onto a lightweight Unreal tick hook so the actual
SDK/game calls still happen from the loaded mod runtime instead of the external app.
"""
from __future__ import annotations

import json
import threading
import time
import uuid
import pkgutil
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from . import backend_actions

try:
    from mods_base import hook
except Exception:  # pragma: no cover - only available in-game
    hook = None  # type: ignore

_HOST = "127.0.0.1"
_PORT = 49774
_server: ThreadingHTTPServer | None = None
_thread: threading.Thread | None = None
_started = False
_lock = threading.RLock()
_queue: deque[dict[str, Any]] = deque()
_results: dict[str, dict[str, Any]] = {}
_last_action: str = ""
_last_error: str = ""
_tick_registered = False


_OPTIONAL_UI_MODULE = "bl" + "imgui"


def _is_optional_ui_dependency_error(value: object) -> bool:
    text = str(value or "")
    return f"No module named '{_OPTIONAL_UI_MODULE}'" in text or f"No module named {_OPTIONAL_UI_MODULE}" in text


def _format_action_exception(exc: Exception) -> str:
    if _is_optional_ui_dependency_error(repr(exc)):
        return (
            "This optional in-game panel dependency is not installed. "
            "The headless external bridge is online; use the standalone external app workflow."
        )
    return repr(exc)


def _now() -> float:
    try:
        return time.monotonic()
    except Exception:
        return time.time()


# This is the shared UI description consumed by the external control panel.
# It intentionally mirrors the current Boosting tab layout first. More complex
# tabs can be added to this same registry without changing the external app.
UI_LAYOUT: dict[str, Any] = {
    "title": "Matt's SDK Boosting Tools - External Control",
    "version": 3,
    "notes": "External control layout. Static catalogs are served to the external app; game-touching actions run through the SDK bridge.",
    "tabs": [
        {"id":"boosting","label":"Boosting","cards":[
            {"id":"target_player","label":"TARGET PLAYER","accent":"cyan","actions":[
                {"id":"refresh_players","label":"Refresh Players","accent":"cyan"},
                {"id":"kick_player","label":"Kick Player","accent":"red"}
            ]},
            {"id":"quick_max","label":"QUICK MAX","accent":"gold","actions":[
                {"id":"max_all","label":"MAX ALL","accent":"gold"},
                {"id":"max_currency","label":"MAX CASH","accent":"green"},
                {"id":"max_eridium","label":"MAX ERIDIUM","accent":"purple"},
                {"id":"max_player_level","label":"MAX PLAYER 60","accent":"cyan"},
                {"id":"max_spec_level","label":"MAX SPEC 701","accent":"purple"}
            ]},
            {"id":"serial_rewards","label":"SERIAL REWARDS","accent":"purple","text":"Paste one or more serials below. Rewards are created with GiveRewardAllPlayers, then custom serials are patched onto the selected target packages.","fields":[
                {"id":"serial_text","label":"Serial Input","type":"multiline","default":""},
                {"id":"serial_override_level","label":"Override delivery level?","type":"choice","choices":["false","true"],"default":"false"},
                {"id":"serial_level","label":"Level","type":"int","default":60}
            ],"actions":[
                {"id":"give_serial_selected","label":"Give Selected","accent":"purple","uses_fields":["serial_text","serial_override_level","serial_level"]},
                {"id":"give_serial_all","label":"Give All","accent":"gold","uses_fields":["serial_text","serial_override_level","serial_level"]},
                {"id":"give_serial_nonhost","label":"Give Non-Host","accent":"cyan","uses_fields":["serial_text","serial_override_level","serial_level"]},
                {"id":"clear_serials","label":"Clear Serials","accent":"red"}
            ]},
            {"id":"experience","label":"EXPERIENCE","accent":"cyan","fields":[
                {"id":"xp_track","label":"XP Track","type":"choice","choices":["player","specialization"],"default":"player"},
                {"id":"level","label":"Target Level","type":"int","default":60}
            ],"actions":[
                {"id":"set_level","label":"Set Player Level","accent":"cyan","uses_fields":["xp_track","level"]},
                {"id":"max_player_level","label":"Max Player Level","accent":"cyan"},
                {"id":"max_spec_level","label":"Set Spec 701","accent":"purple"}
            ]},
            {"id":"currency","label":"CURRENCY","accent":"green","fields":[
                {"id":"currency_kind","label":"Currency Kind","type":"choice","choices":["cash","eridium"],"default":"cash"},
                {"id":"amount","label":"Currency Amount","type":"int","default":1000000}
            ],"actions":[
                {"id":"give_currency","label":"Give Currency","accent":"green","uses_fields":["currency_kind","amount"]},
                {"id":"max_currency","label":"Max Currency","accent":"green"},
                {"id":"max_eridium","label":"Max Eridium","accent":"purple"},
                {"id":"max_all","label":"Max All","accent":"gold"}
            ]},
            {"id":"backpack_bank","label":"BACKPACK / BANK SIZE","accent":"cyan","fields":[
                {"id":"backpack_size","label":"Backpack Size","type":"int","default":999},
                {"id":"bank_size","label":"Bank Size","type":"int","default":1500}
            ],"actions":[
                {"id":"set_backpack_bank_selected","label":"Set Backpack + Bank for Selected","accent":"cyan","uses_fields":["backpack_size","bank_size"]},
                {"id":"set_backpack_bank_all","label":"Apply to All Party","accent":"purple","uses_fields":["backpack_size","bank_size"]}
            ]},
            {"id":"rarity_weights","label":"RARITY DROP WEIGHTS","accent":"purple","text":"Rarity controls are driven by the headless SDK bridge. The standalone app owns the visible controls.","actions":[
                {"id":"rarity_apply","label":"Apply","accent":"purple"},
                {"id":"rarity_reset","label":"Reset All","accent":"gold"},
                {"id":"rarity_only_legendary","label":"Only Legendary","accent":"gold"},
                {"id":"rarity_only_pearlescent","label":"Only Pearlescent","accent":"purple"}
            ]},
            {"id":"cheats_debug","label":"CHEATS / DEBUG CAM","accent":"pink","actions":[
                {"id":"devperk_0","label":"Give Experience","accent":"cyan"},
                {"id":"devperk_1","label":"Give 1 Million Cash","accent":"gold"},
                {"id":"devperk_2","label":"Give 100k Eridium","accent":"purple"},
                {"id":"devperk_3","label":"Kill All Enemies","accent":"red"},
                {"id":"devperk_4","label":"All Customs + Hovers","accent":"pink"},
                {"id":"devperk_5","label":"Infinite Ammo [OFF]","accent":"cyan"},
                {"id":"open_bank","label":"Open Bank Anywhere","accent":"cyan"},
                {"id":"toggle_debug_cam","label":"Toggle Debug Cam","accent":"gold"},
                {"id":"teleport_debug_cam","label":"Teleport Pawn to Debug Cam","accent":"cyan"}
            ]},
            {"id":"sdu_shinies","label":"SDU / GOLDEN CHEST / SHINIES","accent":"gold","actions":[
                {"id":"max_sdu","label":"Max SDU for Selected","accent":"cyan"},
                {"id":"open_golden_chest","label":"Open Golden Chest","accent":"gold"},
                {"id":"close_golden_chest","label":"Close Golden Chest","accent":"red"},
                {"id":"drop_all_shinies","label":"Drop All Shinies","accent":"gold"},
                {"id":"shiny_selected","label":"Shiny Selected","accent":"purple"},
                {"id":"shiny_all","label":"Shiny All","accent":"gold"},
                {"id":"shiny_nonhost","label":"Shiny Non-Host","accent":"cyan"}
            ]}
        ]},
        {"id":"serial_tools","label":"Serial Tools","cards":[
            {"id":"serial_convert","label":"SERIAL TOOLS","accent":"cyan","text":"Paste a @U serialized value or deserialized human-readable serial below. The converter returns both formats.","fields":[
                {"id":"serial_input","label":"Input","type":"multiline","default":""}
            ],"actions":[
                {"id":"serial_convert","label":"Convert","accent":"cyan","uses_fields":["serial_input"]},
                {"id":"clear_serial_tools","label":"Clear","accent":"red"},
                {"id":"serial_breakdown","label":"Copy Parts Breakdown","accent":"purple","uses_fields":["serial_input"]}
            ]},
            {"id":"serial_output","label":"OUTPUTS","accent":"purple","text":"Deserialized Output / Parts Breakdown / @U Serialized Output are returned in the external activity output and mirrored into the in-game Serial Tools state."}
        ]},
        {"id":"serial_bookmarks","label":"Serial Bookmarks","cards":[
            {"id":"serial_bookmarks_main","label":"SERIAL BOOKMARKS","accent":"purple","text":"Browse saved serials, edit the active entry, then deliver checked items from the footer. Full bookmark list export is a V3 resource target.","fields":[
                {"id":"bookmark_search","label":"Search","type":"text","default":""},
                {"id":"bookmark_name","label":"Name","type":"text","default":"Default"},
                {"id":"bookmark_group","label":"Group","type":"text","default":"Default"},
                {"id":"bookmark_serial","label":"Serial","type":"multiline","default":""}
            ],"actions":[
                {"id":"serial_bookmark_new","label":"+ New Serial","accent":"cyan"},
                {"id":"serial_bookmark_import","label":"Import","accent":"gold"},
                {"id":"serial_bookmark_save","label":"Save","accent":"cyan"},
                {"id":"serial_bookmark_duplicate","label":"Duplicate","accent":"purple"},
                {"id":"serial_bookmark_delete","label":"Delete","accent":"red"},
                {"id":"serial_bookmark_copy","label":"Copy","accent":"gold"},
                {"id":"give_serial_selected","label":"Deliver Selected","accent":"purple","uses_fields":["bookmark_serial"]},
                {"id":"give_serial_all","label":"Deliver All","accent":"gold","uses_fields":["bookmark_serial"]},
                {"id":"give_serial_nonhost","label":"Deliver Non-Host","accent":"cyan","uses_fields":["bookmark_serial"]}
            ]}
        ]},
        {"id":"bl4_codes","label":"BL4 Codes","cards":[
            {"id":"bl4_codes_catalog","label":"BL4 CODES","accent":"gold","text":"Merged BL4 codes catalog. The external app can use the local Lootlemon/cache JSON without the game; delivery still goes through the bridge.","fields":[
                {"id":"code_search","label":"Search","type":"text","default":""},
                {"id":"code_serial","label":"Serial","type":"multiline","default":""},
                {"id":"code_delivery_level","label":"Delivery Level","type":"int","default":60}
            ],"actions":[
                {"id":"codes_load_cache","label":"Load Cache","accent":"cyan"},
                {"id":"codes_refresh_gzo","label":"Refresh GZO","accent":"gold"},
                {"id":"codes_reload_lootlemon","label":"Reload Lootlemon Cache","accent":"gold"},
                {"id":"codes_mattmab_validation","label":"Mattmab Validation","accent":"green"},
                {"id":"codes_import_bookmarks","label":"Import Selected To Bookmarks","accent":"purple"},
                {"id":"give_serial_selected","label":"Deliver Selected","accent":"purple","uses_fields":["code_serial","code_delivery_level"]},
                {"id":"give_serial_all","label":"Deliver All","accent":"gold","uses_fields":["code_serial","code_delivery_level"]},
                {"id":"give_serial_nonhost","label":"Deliver Non-Host","accent":"cyan","uses_fields":["code_serial","code_delivery_level"]}
            ]}
        ]},
        {"id":"legit_builder","label":"Legit Builder","cards":[
            {"id":"legit_builder_main","label":"STRIPPED LEGIT BUILDER","accent":"cyan","text":"Slot-first builder: choose Type first, then Manufacturer. V3 keeps using the loaded in-game builder state for exact validation while we move the rule/slot data into the external UI.","fields":[
                {"id":"legit_unlock_modded","label":"Unlock rules for modded gear","type":"choice","choices":["false","true"],"default":"false"},
                {"id":"legit_type","label":"Type","type":"text","default":"Pistol"},
                {"id":"legit_manufacturer","label":"Manufacturer","type":"text","default":"Daedalus"},
                {"id":"legit_root_filter","label":"Optional Root Filter","type":"text","default":""},
                {"id":"legit_part_filter","label":"Filter Available Parts","type":"text","default":""}
            ],"actions":[
                {"id":"legit_apply_max_passives","label":"Add All Max Passives","accent":"gold"},
                {"id":"legit_validate_build","label":"Validate / Build Active","accent":"cyan"},
                {"id":"legit_give_selected","label":"Give Active to Selected","accent":"gold"},
                {"id":"legit_give_all","label":"Give Active to All","accent":"purple"},
                {"id":"legit_clear_parts","label":"Clear Selected Parts","accent":"red"}
            ]},
            {"id":"legit_slot_grid","label":"SLOT GRID PLACEHOLDER","accent":"purple","text":"This is where the external app will render the same 3-column slot grid using legit_rules_flat.json and gzo_parts_map.json. Those resources do not require the game and can be cached locally."}
        ]},
        {"id":"validator","label":"Validator","cards":[
            {"id":"validator_basic","label":"VALIDATOR","accent":"cyan","text":"Validate one serial or a large pasted list. Validation can mostly run externally once the serial/rules code is moved into the app.","fields":[
                {"id":"validator_basic_input","label":"Basic validation input","type":"multiline","default":""},
                {"id":"validator_bulk_input","label":"Bulk validator input","type":"multiline","default":""}
            ],"actions":[
                {"id":"validator_basic","label":"Validate Basic","accent":"cyan"},
                {"id":"validator_clear","label":"Clear Validator","accent":"red"},
                {"id":"validator_bulk","label":"Validate Bulk","accent":"gold"}
            ]}
        ]},
        {"id":"item_pool_spawning","label":"Item Pool Spawning","cards":[
            {"id":"item_pool_main","label":"ITEM POOL SPAWNING","accent":"gold","text":"Filter item pools, then spawn the selected pool near the local player. Turrets, terminals, and cosmetics are intentionally excluded.","fields":[
                {"id":"itempool_search","label":"Search Item Pools","type":"text","default":""},
                {"id":"itempool_level","label":"Level","type":"int","default":60},
                {"id":"itempool_count","label":"Quantity","type":"int","default":1},
                {"id":"itempool_name","label":"Selected / exact pool name","type":"text","default":""}
            ],"actions":[
                {"id":"spawn_itempool","label":"Spawn Selected Item Pool","accent":"gold","uses_fields":["itempool_name","itempool_count","itempool_level"]},
                {"id":"toggle_itempool_favorite","label":"Favorite Selected","accent":"purple","uses_fields":["itempool_name"]}
            ]}
        ]},
        {"id":"map_travel","label":"Map Travel","cards":[
            {"id":"map_travel_main","label":"MAP TRAVEL","accent":"pink","text":"Select a map first, then choose a travel station on that map. Travel commands are host-side server travel helpers.","fields":[
                {"id":"travel_map","label":"Search Maps / Selected Map","type":"text","default":""},
                {"id":"travel_station","label":"Search Travel Stations / Selected Station","type":"text","default":""}
            ],"actions":[
                {"id":"toggle_map_favorite","label":"Favorite Map","accent":"purple","uses_fields":["travel_map"]},
                {"id":"travel_to_map","label":"Travel to Selected Map","accent":"cyan","uses_fields":["travel_map"]},
                {"id":"toggle_station_favorite","label":"Favorite Station","accent":"purple","uses_fields":["travel_station"]},
                {"id":"travel_to_station","label":"Travel to Selected Station","accent":"gold","uses_fields":["travel_station"]}
            ]}
        ]},
        {"id":"player_movement","label":"Player Movement","cards":[
            {"id":"movement_presets","label":"PRESETS / SAVE / APPLY","accent":"green","text":"UI-only controls. Slider changes are debounced and apply after you stop dragging.","actions":[
                {"id":"movement_apply_all","label":"Apply Now","accent":"green"},
                {"id":"movement_save_preset","label":"Save Preset","accent":"cyan"},
                {"id":"movement_load_saved","label":"Load Saved","accent":"purple"},
                {"id":"movement_reset_all","label":"Reset Defaults","accent":"gold"},
                {"id":"movement_preset_fast","label":"Fast","accent":"purple"},
                {"id":"movement_preset_veryfast","label":"Very Fast","accent":"purple"},
                {"id":"movement_preset_moon","label":"Moon","accent":"purple"},
                {"id":"movement_preset_wallwalk","label":"Wall Walk","accent":"green"},
                {"id":"movement_preset_fastglide","label":"Fast Glide","accent":"cyan"}
            ]},
            {"id":"movement_speed","label":"SPEED","accent":"cyan","fields":[
                {"id":"movement_speed_scale","label":"Speed Scale","type":"text","default":"1.00x"},
                {"id":"movement_walk_speed","label":"Walk / Ground Speed","type":"int","default":600}
            ],"actions":[{"id":"movement_apply_all","label":"Apply Movement Settings","accent":"cyan"}]},
            {"id":"movement_jump","label":"JUMP / GRAVITY","accent":"purple","fields":[
                {"id":"movement_jump_height","label":"Master JumpGoal Height","type":"int","default":198},
                {"id":"movement_gravity_scale","label":"Gravity Scale","type":"text","default":"1.00"}
            ],"actions":[
                {"id":"movement_toggle_no_target","label":"Toggle No Target","accent":"purple"},
                {"id":"movement_toggle_noclip","label":"Toggle Noclip","accent":"gold"}
            ]},
            {"id":"movement_utility","label":"WORLD / UTILITY","accent":"pink","actions":[
                {"id":"movement_set_time","label":"Set Time","accent":"gold"},
                {"id":"movement_reset_time","label":"Reset Time","accent":"purple"},
                {"id":"movement_delete_ground_items","label":"Delete Ground Items","accent":"red"},
                {"id":"movement_zero_vault","label":"Zero Vault Cooldown","accent":"cyan"}
            ]}
        ]},
        {"id":"activity_log","label":"Activity Log","cards":[
            {"id":"activity_log_main","label":"ACTIVITY LOG","accent":"purple","actions":[
                {"id":"status","label":"Refresh Status","accent":"cyan"},
                {"id":"clear_external_log","label":"Clear Log","accent":"red"}
            ]}
        ]}
    ],
    "resources": {
        "lootlemon_codes": "/resource/lootlemon_codes",
        "item_pools": "/resource/item_pools",
        "travel_maps": "/resource/travel_maps",
        "travel_stations": "/resource/travel_stations",
        "gzo_parts_map": "/resource/gzo_parts_map",
        "legit_rules": "/resource/legit_rules"
    }
}

# V4: resource-backed external dropdown metadata.  The external app uses these
# resources to render real combo boxes/lists instead of plain text placeholders.
UI_LAYOUT["version"] = 5
UI_LAYOUT["notes"] = "V5 bridge keeps action/status endpoints; external app now bundles static resources locally."

def _v4_patch_layout() -> None:
    for tab in UI_LAYOUT.get("tabs", []):
        tid = tab.get("id")
        for card in tab.get("cards", []):
            cid = card.get("id")
            if tid == "bl4_codes" and cid == "bl4_codes_catalog":
                card["fields"] = [
                    {"id":"code_entry","label":"Code / Item","type":"resource_choice","source":"lootlemon_codes","default":"","sets":{"code_serial":"serial"}},
                    {"id":"code_search","label":"Search","type":"text","default":""},
                    {"id":"code_serial","label":"Serial","type":"multiline","default":""},
                    {"id":"code_delivery_level","label":"Delivery Level","type":"int","default":60},
                ]
            elif tid == "item_pool_spawning" and cid == "item_pool_main":
                card["fields"] = [
                    {"id":"itempool_name","label":"Selected Item Pool","type":"resource_choice","source":"item_pools","default":""},
                    {"id":"itempool_search","label":"Search Item Pools","type":"text","default":""},
                    {"id":"itempool_level","label":"Level","type":"int","default":60},
                    {"id":"itempool_count","label":"Quantity","type":"int","default":1},
                ]
            elif tid == "map_travel" and cid == "map_travel_main":
                card["fields"] = [
                    {"id":"travel_map","label":"Selected Map","type":"resource_choice","source":"travel_maps","default":""},
                    {"id":"travel_station","label":"Selected Station","type":"resource_choice","source":"travel_stations","default":""},
                    {"id":"travel_map_search","label":"Search Maps","type":"text","default":""},
                    {"id":"travel_station_search","label":"Search Travel Stations","type":"text","default":""},
                ]
            elif tid == "legit_builder" and cid == "legit_builder_main":
                card["text"] = "External resource-backed Legit Builder. Pick Type → Manufacturer → Root → Parts outside the game; only final build/give is sent through the SDK bridge."
                card["fields"] = [
                    {"id":"legit_unlock_modded","label":"Unlock rules for modded gear","type":"choice","choices":["false","true"],"default":"false"},
                    {"id":"legit_type","label":"Type","type":"legit_type","default":"pistol"},
                    {"id":"legit_manufacturer","label":"Manufacturer","type":"legit_manufacturer","default":"Daedalus"},
                    {"id":"legit_root_serial","label":"Root Variant","type":"legit_root","default":""},
                    {"id":"legit_part_select","label":"Available Part","type":"legit_part","default":""},
                    {"id":"legit_selected_parts","label":"Selected Parts","type":"multiline","default":""},
                ]
                card["actions"] = [
                    {"id":"local_legit_add_part","label":"Add Selected Part","accent":"cyan"},
                    {"id":"legit_apply_max_passives","label":"Add All Max Passives","accent":"gold","uses_fields":["legit_root_serial","legit_selected_parts","legit_unlock_modded"]},
                    {"id":"legit_validate_build","label":"Validate / Build Active","accent":"cyan","uses_fields":["legit_root_serial","legit_selected_parts","legit_unlock_modded"]},
                    {"id":"legit_give_selected","label":"Give Active to Selected","accent":"gold","uses_fields":["legit_root_serial","legit_selected_parts","legit_unlock_modded"]},
                    {"id":"legit_give_all","label":"Give Active to All","accent":"purple","uses_fields":["legit_root_serial","legit_selected_parts","legit_unlock_modded"]},
                    {"id":"legit_clear_parts","label":"Clear Selected Parts","accent":"red"},
                ]
            elif tid == "legit_builder" and cid == "legit_slot_grid":
                card["label"] = "RESOURCE-BACKED PART PICKER"
                card["text"] = "V4 loads legit_rules_flat.json and gzo_parts_map.json in the external app. The current picker is a root-wide part dropdown plus Selected Parts text; the next pass can split it into Matt's exact 3-column slot cards."
_v4_patch_layout()

# V6: add target-player dropdown/action to the copied UI layout.
def _v6_patch_layout() -> None:
    UI_LAYOUT["version"] = 6
    UI_LAYOUT["notes"] = "V6 adds live player target selection for external boosting."
    try:
        for tab in UI_LAYOUT.get("tabs", []):
            if tab.get("id") != "boosting":
                continue
            for card in tab.get("cards", []):
                if card.get("id") == "target_player":
                    card["text"] = "Select which party player the boosting buttons should target. Refresh pulls the live party list from the SDK bridge."
                    card["fields"] = [{"id":"target_player","label":"Target Player","type":"player_choice","default":""}]
                    card["actions"] = [
                        {"id":"refresh_players","label":"Refresh Players","accent":"cyan"},
                        {"id":"set_target_player","label":"Use Selected Target","accent":"green","uses_fields":["target_player"]},
                        {"id":"kick_player","label":"Kick Player","accent":"red"},
                    ]
    except Exception:
        pass
_v6_patch_layout()

def _log(msg: str) -> None:
    global _last_action
    _last_action = str(msg)


def _set_selected_player_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = backend_actions.set_target_player(payload.get("target_player"))
    if result.get("ok"):
        _log(str(result.get("message") or "External target player updated."))
    return result


def _external_app_owned(action: str, feature: str) -> dict[str, Any]:
    return {
        "ok": False,
        "message": f"{action} is handled locally by the standalone external app ({feature}); no SDK bridge call is needed.",
    }


def _payload_serial_text(payload: dict[str, Any]) -> str:
    for key in ("serial_text", "bookmark_serial", "code_serial", "serial_input"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return ""


def _handle_action(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if action == "status":
        return _status()
    if action == "refresh_players":
        backend_actions.refresh_players()
        return {"ok": True, "message": "Refreshed party/player list.", "status": _status()}
    if action == "set_target_player":
        return _set_selected_player_from_payload(payload)
    if action == "kick_player":
        return backend_actions.kick_selected_player()
    if action == "open_bank":
        return backend_actions.open_bank_anywhere()
    if action == "open_golden_chest":
        return backend_actions.open_golden_chest()
    if action == "close_golden_chest":
        return backend_actions.close_golden_chest()
    if action == "drop_all_shinies":
        return backend_actions.drop_all_shinies_selected()
    if action == "shiny_selected":
        return backend_actions.deliver_shinies("selected")
    if action == "shiny_all":
        return backend_actions.deliver_shinies("all")
    if action == "shiny_nonhost":
        return backend_actions.deliver_shinies("nonhost")
    if action == "set_backpack_bank_selected":
        return backend_actions.set_inventory_sizes_selected(
            payload.get("backpack_size") or 1000,
            payload.get("bank_size") or 1000,
        )
    if action == "set_backpack_bank_all":
        return backend_actions.set_inventory_sizes_all_party(
            payload.get("backpack_size") or 1000,
            payload.get("bank_size") or 1000,
        )
    if action == "auto_inventory_sizes":
        return backend_actions.auto_apply_inventory_sizes(
            payload.get("backpack_size") or 1000,
            payload.get("bank_size") or 1000,
            payload.get("enabled", True),
        )
    if action == "max_currency":
        return backend_actions.max_currency()
    if action == "max_eridium":
        return backend_actions.max_eridium()
    if action == "max_player_level":
        return backend_actions.max_player_level()
    if action == "max_spec_level":
        return backend_actions.max_spec_level()
    if action == "max_sdu":
        return backend_actions.max_sdu()
    if action == "max_all":
        return backend_actions.max_all()
    if action == "give_currency":
        return backend_actions.give_currency(
            payload.get("currency_kind") if "currency_kind" in payload else payload.get("currency_index", "cash"),
            payload.get("amount") or 0,
        )
    if action == "set_level":
        return backend_actions.give_experience(
            payload.get("xp_track") if "xp_track" in payload else payload.get("xp_track_index", "player"),
            payload.get("level") or 0,
        )
    if action == "toggle_debug_cam":
        return backend_actions.toggle_debug_cam()
    if action == "teleport_debug_cam":
        return backend_actions.teleport_debug_cam()
    if action.startswith("devperk_"):
        return backend_actions.activate_devperk(action.split("_", 1)[1])
    if action == "spawn_itempool":
        return backend_actions.spawn_itempool(
            payload.get("itempool_name"),
            payload.get("itempool_count") or 1,
            payload.get("itempool_level") or 60,
        )
    if action.startswith("dev_spawner_"):
        return backend_actions.run_dev_spawner_action(action, payload)
    if action == "travel_to_map":
        return backend_actions.travel_to_map(payload.get("travel_map"))
    if action == "travel_to_station":
        return backend_actions.travel_to_station(payload.get("travel_station"))
    if action == "movement_delete_ground_items":
        return backend_actions.movement_delete_ground_items()
    if action == "movement_zero_vault":
        return backend_actions.movement_zero_vault()
    if action == "movement_apply_all":
        return backend_actions.movement_apply_all(payload)
    if action == "movement_reset_all":
        return backend_actions.movement_reset_all()
    if action == "movement_toggle_no_target":
        return backend_actions.movement_toggle_no_target()
    if action == "movement_toggle_noclip":
        return backend_actions.movement_toggle_noclip()
    if action == "movement_set_time":
        return backend_actions.movement_set_time(
            payload.get("movement_time_dilation") or payload.get("time_dilation") or payload.get("time") or 1.0
        )
    if action == "movement_reset_time":
        return backend_actions.movement_reset_time()
    if action == "movement_players_only":
        return backend_actions.movement_toggle_players_only()
    if action == "movement_teleport_to_slot":
        return backend_actions.movement_teleport_selected_to_slot(payload.get("slot", 0))
    if action == "movement_preset_fast":
        return backend_actions.movement_apply_preset("fast")
    if action == "movement_preset_veryfast":
        return backend_actions.movement_apply_preset("veryfast")
    if action == "movement_preset_moon":
        return backend_actions.movement_apply_preset("moon")
    if action == "movement_preset_wallwalk":
        return backend_actions.movement_apply_preset("wallwalk")
    if action == "movement_preset_fastglide":
        return backend_actions.movement_apply_preset("fastglide")
    if action == "movement_infinite_jump_all_on":
        return backend_actions.movement_infinite_jump_all(True)
    if action == "movement_infinite_jump_all_off":
        return backend_actions.movement_infinite_jump_all(False)
    if action == "movement_infinite_jump_toggle_selected":
        return backend_actions.movement_infinite_jump_selected(
            payload.get("infinite_jump_target") or payload.get("target_player")
        )
    if action == "movement_infinite_jump_selected_on":
        return backend_actions.movement_infinite_jump_set_selected(
            payload.get("infinite_jump_target") or payload.get("target_player"), True
        )
    if action == "movement_infinite_jump_selected_off":
        return backend_actions.movement_infinite_jump_set_selected(
            payload.get("infinite_jump_target") or payload.get("target_player"), False
        )
    if action in ("movement_save_preset", "movement_load_saved"):
        return {"ok": False, "message": f"{action} is local UI preset storage and is not handled by the SDK bridge."}
    if action == "rarity_apply":
        return backend_actions.rarity_apply(payload)
    if action == "rarity_reset":
        return backend_actions.rarity_reset()
    if action == "rarity_only_legendary":
        return backend_actions.rarity_only("legendary")
    if action == "rarity_only_pearlescent":
        return backend_actions.rarity_only("pearlescent")
    if action in ("codes_load_cache", "codes_refresh_gzo", "codes_reload_lootlemon"):
        return {"ok": True, "message": f"{action}: static code resources are bundled in the external app; use Reconnect/Reload in the app to refresh the local view."}
    if action == "codes_import_bookmarks":
        return {"ok": True, "message": "Import to bookmarks is handled locally by the external app."}
    if action == "codes_mattmab_validation":
        return _external_app_owned(action, "BL4 Codes validation")
    if action == "serial_breakdown":
        return _external_app_owned(action, "Serial Tools parts breakdown")
    if action in ("validator_basic", "validator_clear", "validator_bulk"):
        return _external_app_owned(action, "Validator")
    if action in (
        "legit_apply_max_passives",
        "legit_validate_build",
        "legit_clear_parts",
    ):
        return _external_app_owned(action, "Legit Builder")
    if action in ("legit_give_selected", "legit_give_all", "legit_give_nonhost"):
        return {
            "ok": False,
            "message": f"{action} should generate a serial locally, then call give_serial_selected/give_serial_all/give_serial_nonhost.",
        }
    if action in ("toggle_itempool_favorite", "toggle_map_favorite", "toggle_station_favorite"):
        return {"ok": True, "message": f"{action} is local favorite state in the external app."}
    if action == "clear_external_log":
        global _last_action, _last_error
        _last_action = ""
        _last_error = ""
        return {"ok": True, "message": "Cleared bridge status markers. The external app owns its local activity log."}
    if action in ("serial_bookmark_new", "serial_bookmark_import", "serial_bookmark_save", "serial_bookmark_duplicate", "serial_bookmark_delete", "serial_bookmark_copy"):
        return _external_app_owned(action, "Serial Bookmarks")
    if action == "clear_serials":
        return backend_actions.clear_serials()
    if action == "clear_serial_tools":
        return backend_actions.clear_serial_tools()
    if action == "serial_convert":
        return backend_actions.serial_convert(payload.get("serial_input") or "")
    if action in ("give_serial_selected", "give_serial_all"):
        override_level = str(payload.get("serial_override_level") or "false").lower() in ("1", "true", "yes", "on")
        return backend_actions.give_serials(
            _payload_serial_text(payload),
            "all" if action.endswith("all") else "selected",
            override_level,
            payload.get("serial_level") or payload.get("code_delivery_level") or 60,
        )
    if action == "give_serial_nonhost":
        override_level = str(payload.get("serial_override_level") or "false").lower() in ("1", "true", "yes", "on")
        return backend_actions.give_serials(
            _payload_serial_text(payload),
            "nonhost",
            override_level,
            payload.get("serial_level") or payload.get("code_delivery_level") or 60,
        )
    return {"ok": False, "message": f"Unknown action: {action}"}


def _status() -> dict[str, Any]:
    backend_status = backend_actions.get_status()
    diagnostics = dict(backend_status.get("diagnostics") or {})
    diagnostics.setdefault("external_bridge_started", _started)
    last_error = _last_error or backend_status.get("last_refresh_error", "")
    if _is_optional_ui_dependency_error(last_error):
        last_error = ""
    return {
        "ok": True,
        "name": "MattsSDKBoostingTools external bridge",
        "host": _HOST,
        "port": _PORT,
        "started": _started,
        "queue": len(_queue),
        "players": backend_status.get("players", []),
        "selected_player": backend_status.get("selected_player") or "",
        "selected_player_index": backend_status.get("selected_player_index"),
        "serial_delivery": backend_status.get("serial_delivery", {}),
        "diagnostics": diagnostics,
        "last_action": _last_action,
        "last_error": last_error,
    }


def _process_pending_actions(*_args: Any, **_kwargs: Any) -> None:
    for _ in range(8):
        with _lock:
            if not _queue:
                return None
            item = _queue.popleft()
        rid = item.get("id")
        action = item.get("action")
        payload = item.get("payload") or {}
        try:
            result = _handle_action(str(action), dict(payload))
        except Exception as exc:
            global _last_error
            message = _format_action_exception(exc)
            _last_error = "" if _is_optional_ui_dependency_error(repr(exc)) else repr(exc)
            result = {"ok": False, "message": message}
        with _lock:
            _results[str(rid)] = result
    return None


def _register_tick_hook() -> None:
    global _tick_registered
    if _tick_registered or hook is None:
        return
    try:
        hook(
            "/Script/GbxUIUMG.GbxUIUMGTickWidget:BP_TickWidget",
            immediately_enable=True,
            hook_identifier="matts_sdk_boosting_tools_external_bridge_tick_v1",
        )(_process_pending_actions)
        _tick_registered = True
    except Exception as exc:
        global _last_error
        _last_error = f"bridge tick hook failed: {exc!r}"


_RESOURCE_FILES = {
    "lootlemon_codes": "MattsSDKBoostingTools_lootlemon_codes.json",
    "item_pools": "item_pools.json",
    "travel_maps": "travelmaps_flat.json",
    "travel_stations": "travelstations.json",
    "gzo_parts_map": "gzo_parts_map.json",
    "legit_rules": "legit_rules_flat.json",
}


def _load_resource(name: str) -> dict[str, Any]:
    filename = _RESOURCE_FILES.get(name)
    if not filename:
        return {"ok": False, "message": f"Unknown resource: {name}"}
    try:
        package = __package__ or "MattsSDKBoostingTools"
        raw = pkgutil.get_data(package, filename)
        if raw is None:
            return {"ok": False, "message": f"Resource not found: {filename}"}
        return {"ok": True, "name": name, "data": json.loads(raw.decode("utf-8", errors="replace"))}
    except Exception as exc:
        return {"ok": False, "name": name, "message": repr(exc)}

class _Handler(BaseHTTPRequestHandler):
    server_version = "MSBTBridge/2.0"

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _send(self, status: int, data: Any) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)
        except OSError:
            # The external app may time out or close the request while the game
            # thread is busy. The action result is still stored/logged; avoid
            # noisy bridge tracebacks for a client-side disconnect.
            return

    def do_OPTIONS(self) -> None:
        self._send(200, {"ok": True})

    def do_GET(self) -> None:
        if self.path.startswith("/status"):
            self._send(200, _status())
        elif self.path.startswith("/layout"):
            self._send(200, UI_LAYOUT)
        elif self.path.startswith("/resource/"):
            name = self.path.split("/resource/", 1)[1].split("?", 1)[0].strip("/")
            data = _load_resource(name)
            self._send(200 if data.get("ok") else 404, data)
        else:
            self._send(404, {"ok": False, "message": "Not found"})

    def do_POST(self) -> None:
        if not self.path.startswith("/action"):
            self._send(404, {"ok": False, "message": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(raw or "{}")
            action = str(data.get("action") or "")
            payload = data.get("payload") or {}
            if not action:
                self._send(400, {"ok": False, "message": "Missing action"})
                return
            rid = uuid.uuid4().hex
            with _lock:
                _queue.append({"id": rid, "action": action, "payload": payload})
            deadline = _now() + float(data.get("timeout", 5.0) or 5.0)
            while _now() < deadline:
                with _lock:
                    result = _results.pop(rid, None)
                if result is not None:
                    # Handled action failures are still useful JSON responses for
                    # the external app. Reserve HTTP 500 for bridge/server errors.
                    self._send(200, result)
                    return
                time.sleep(0.05)
            self._send(202, {"ok": False, "queued": True, "message": "Action queued but not processed yet. Make sure the game is loaded and the SDK mod is active."})
        except Exception as exc:
            self._send(500, {"ok": False, "message": repr(exc)})


def start_bridge() -> None:
    global _server, _thread, _started, _last_error
    if _started:
        return
    _register_tick_hook()
    try:
        _server = ThreadingHTTPServer((_HOST, _PORT), _Handler)
        _thread = threading.Thread(target=_server.serve_forever, name="MSBTExternalBridge", daemon=True)
        _thread.start()
        _started = True
        _log(f"external bridge listening on http://{_HOST}:{_PORT}")
    except OSError as exc:
        # Port already open usually means another copy/reload already started it.
        _last_error = repr(exc)
        _started = False
    except Exception as exc:
        _last_error = repr(exc)
        _started = False


def stop_bridge() -> None:
    global _server, _thread, _started
    try:
        if _server is not None:
            _server.shutdown()
            _server.server_close()
    except Exception:
        pass
    _server = None
    _thread = None
    _started = False
