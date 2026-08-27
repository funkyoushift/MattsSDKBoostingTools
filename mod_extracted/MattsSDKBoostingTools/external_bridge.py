"""Local external-control bridge for Matt's SDK Boosting Tools.

Runs inside the BL4 SDK mod.  External tools call http://127.0.0.1:49774
and the bridge queues actions onto a lightweight Unreal tick hook so the actual
SDK/game calls still happen from the loaded mod runtime instead of the external app.
"""
from __future__ import annotations

import copy
import json
import threading
import time
import uuid
import pkgutil
from collections import OrderedDict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from . import backend_actions, mobile_lan, perf_profile, quick_menu_registry

try:
    from mods_base import hook
except Exception:  # pragma: no cover - only available in-game
    hook = None  # type: ignore

_HOST = "127.0.0.1"
_PORT = 49774
_LAN_ROUTES_DENIED = ("/layout", "/resource/")
_DEVICE_HEADER = "x-msbt-device"
MAX_QUEUE_DEPTH = 64
MAX_RESULTS = 128
RESULT_TTL_SECONDS = 60.0
MAX_BODY_BYTES = 2 * 1024 * 1024
MAX_CLIENT_TIMEOUT_SECONDS = 30.0
MIN_CLIENT_TIMEOUT_SECONDS = 1.0
STATUS_REFRESH_SECONDS = 0.5
STOP_JOIN_TIMEOUT_SECONDS = 3.0
_server: ThreadingHTTPServer | None = None
_thread: threading.Thread | None = None
_started = False
_http_lock = threading.Lock()
_lock = threading.RLock()
_queue: deque[dict[str, Any]] = deque()
_results: OrderedDict[str, dict[str, Any]] = OrderedDict()
_waiters: dict[str, threading.Event] = {}
# Request IDs whose HTTP waiters already timed out / disconnected.  Those actions
# may still run if the game later ticks with an empty new-command stream, but a
# *new* /action must drop them so stale serials/spawns cannot re-fire mid-flight.
_abandoned_rids: set[str] = set()
# RID currently executing on the game tick (popped from queue, result not written yet).
_executing_rid: str | None = None
_last_action: str = ""
_last_error: str = ""
_tick_registered = False
_tick_registration: Any = None
_generation = 0
_status_snapshot: dict[str, Any] | None = None
_status_snapshot_at = 0.0
# GbxUIUMGTickWidget:BP_TickWidget fires once per widget, many times a frame.
_BRIDGE_TICK_MIN_INTERVAL_S = 1.0 / 60.0
_bridge_tick_last_at = 0.0
_bridge_tick_in_flight = False


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


def _record_sizes_locked() -> None:
    perf_profile.record_bridge_sizes(len(_queue), len(_results))


def _prune_results_locked(now: float | None = None) -> int:
    """Expire old results and enforce the bounded result cache."""
    current = _now() if now is None else float(now)
    removed = 0
    for rid, entry in list(_results.items()):
        completed_at = float(entry.get("completed_at", current))
        if current - completed_at <= RESULT_TTL_SECONDS:
            continue
        _results.pop(rid, None)
        removed += 1
    while len(_results) > MAX_RESULTS:
        _results.popitem(last=False)
        removed += 1
    _record_sizes_locked()
    return removed


def _store_result_locked(rid: str, result: dict[str, Any], now: float | None = None) -> bool:
    """Store a completed result unless its HTTP waiter has abandoned it."""
    if not rid or rid in _abandoned_rids:
        return False
    _results[rid] = {
        "result": result,
        "completed_at": _now() if now is None else float(now),
    }
    _results.move_to_end(rid)
    _prune_results_locked(now)
    return True


def _pop_result_locked(rid: str, now: float | None = None) -> dict[str, Any] | None:
    _prune_results_locked(now)
    entry = _results.pop(rid, None)
    _record_sizes_locked()
    if entry is None:
        return None
    # Tolerate direct legacy/test insertion of a raw result mapping.
    value = entry.get("result") if "result" in entry else entry
    return value if isinstance(value, dict) else None


def _signal_waiter_locked(rid: str) -> None:
    waiter = _waiters.get(rid)
    if waiter is not None:
        waiter.set()


def _copy_payload(payload: Any) -> dict[str, Any]:
    """Snapshot request payloads so later requests cannot mutate queued work."""
    if not isinstance(payload, dict):
        return {}
    try:
        return copy.deepcopy(payload)
    except Exception:
        try:
            return dict(payload)
        except Exception:
            return {}


# Background / read-mostly actions must not wipe a waiting spawn or serial send.
_QUEUE_PRESERVING_ACTIONS = frozenset({
    "auto_inventory_sizes",
    "status",
    "clear_external_log",
    "dev_spawner_status",
    "dev_spawner_cache_status",
    "dev_spawner_logo_options",
    "quick_menu_get_layout",
    "quick_menu_set_layout",
    "quick_menu_assign_slot",
    "quick_menu_clear_page",
    "read_equipped_serials",
    "read_backpack_serials",
    "read_inventory",
    "copy_read_serial",
    "copy_all_read_serials",
    # Live Boost Mods status polls must not cancel a pending enable/disable.
    "cxp_status",
    "instant_drops_status",
    "instant_holds_status",
    "fog_of_war_status",
    "third_person_status",
    # Hoard Builder status poll must not cancel an in-flight Start/Clear.
    "hoard_status",
})

_QUICK_MENU_LAYOUT_MUTATIONS = frozenset({
    "quick_menu_set_layout",
    "quick_menu_assign_slot",
    "quick_menu_clear_page",
})

# Initial Give_Serial bridge actions. After they run, multi-chunk delivery continues
# on the serial-rewards tick (outside this HTTP queue). Only a newer Give_Serial
# should replace that in-flight chunk work — see serial_rewards.py.
_SERIAL_DELIVERY_ACTIONS = frozenset({
    "give_serial_local",
    "give_serial_selected",
    "give_serial_all",
    "give_serial_nonhost",
})

# Flag-only / menu-safe live mods: run on the HTTP thread so title-menu toggles
# work before GbxUIUMGTickWidget is ticking in-world.
_IMMEDIATE_LIVE_MOD_ACTIONS = frozenset({
    "cxp_on",
    "cxp_off",
    "cxp_toggle",
    "cxp_set_mult",
    "cxp_status",
    "instant_drops_on",
    "instant_drops_off",
    "instant_drops_toggle",
    "instant_drops_status",
    "instant_holds_on",
    "instant_holds_off",
    "instant_holds_toggle",
    "instant_holds_status",
    "third_person_on",
    "third_person_off",
    "third_person_toggle",
    "third_person_status",
})


def _clear_pending_matching_locked(should_drop: Callable[[dict[str, Any]], bool]) -> int:
    """Drop queued actions matching should_drop; keep the rest in order."""
    dropped = 0
    kept: deque[dict[str, Any]] = deque()
    while _queue:
        item = _queue.popleft()
        if should_drop(item):
            rid = str(item.get("id") or "")
            if rid:
                _abandoned_rids.add(rid)
                _signal_waiter_locked(rid)
            dropped += 1
            continue
        kept.append(item)
    _queue.extend(kept)
    if len(_abandoned_rids) > 256:
        _abandoned_rids.clear()
    _record_sizes_locked()
    return dropped


def _clear_pending_queue_locked() -> int:
    """Drop every not-yet-executed bridge action."""
    return _clear_pending_matching_locked(lambda _item: True)


def _prepare_queue_for_enqueue_locked(action: str) -> int:
    """Prune stale waiting work before enqueueing a user-facing command.

    Policy:
    - Read-only / background actions: leave the queue alone.
    - New Give_Serial: clear the whole pending queue so an older waiting serial
      list or spawn cannot fire on the same tick. In-progress chunked delivery
      (already started) is replaced inside serial_rewards when this action runs.
    - Any other command (max cash, travel, spawn, etc.): drop stale waiting
      spawns/other actions so bosses do not re-fire, but **keep** pending
      Give_Serial entries so a large delivery that has not started yet is not
      cancelled. Chunk sequences already running are outside this queue and are
      never cleared here.
    """
    if action in _QUEUE_PRESERVING_ACTIONS:
        return 0
    if action in _SERIAL_DELIVERY_ACTIONS:
        return _clear_pending_matching_locked(
            lambda item: str(item.get("action") or "") not in _QUICK_MENU_LAYOUT_MUTATIONS
        )
    return _clear_pending_matching_locked(
        lambda item: str(item.get("action") or "") not in (
            _SERIAL_DELIVERY_ACTIONS | _QUICK_MENU_LAYOUT_MUTATIONS
        )
    )


def _request_was_superseded_locked(rid: str) -> bool:
    """True when a newer /action cleared this id before the game tick ran it."""
    if not rid or rid not in _abandoned_rids:
        return False
    if rid in _results:
        return False
    if _executing_rid == rid:
        return False
    for item in _queue:
        if str(item.get("id") or "") == rid:
            return False
    return True


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
                {"id":"max_player_level","label":"MAX PLAYER 70","accent":"cyan"},
                {"id":"max_spec_level","label":"MAX SPEC 701","accent":"purple"}
            ]},
            {"id":"serial_rewards","label":"SERIAL REWARDS","accent":"purple","text":"Paste one or more serials below, or Read Equipped / Backpack from the selected party target (P1–P4). Host can read a guest's equipped gear. Rewards use GiveRewardAllPlayers then patch serials onto target packages. Ground/dropped serials are not supported.","fields":[
                {"id":"serial_text","label":"Serial Input","type":"multiline","default":""},
                {"id":"serial_override_level","label":"Override delivery level?","type":"choice","choices":["false","true"],"default":"false"},
                {"id":"serial_level","label":"Level","type":"int","default":70}
            ],"actions":[
                {"id":"read_equipped_serials","label":"Read Equipped","accent":"cyan"},
                {"id":"read_backpack_serials","label":"Read Backpack","accent":"cyan"},
                {"id":"give_serial_local","label":"Give Local","accent":"cyan","uses_fields":["serial_text","serial_override_level","serial_level"]},
                {"id":"give_serial_selected","label":"Give Named Player","accent":"purple","uses_fields":["serial_text","serial_override_level","serial_level"]},
                {"id":"give_serial_all","label":"Give All","accent":"gold","uses_fields":["serial_text","serial_override_level","serial_level"]},
                {"id":"give_serial_nonhost","label":"Give Non-Host","accent":"cyan","uses_fields":["serial_text","serial_override_level","serial_level"]},
                {"id":"clear_serials","label":"Clear Serials","accent":"red"}
            ]},
            {"id":"experience","label":"EXPERIENCE","accent":"cyan","fields":[
                {"id":"xp_track","label":"XP Track","type":"choice","choices":["player","specialization"],"default":"player"},
                {"id":"level","label":"Target Level","type":"int","default":70}
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
                {"id":"disable_debug_cam","label":"Disable Debug Cam","accent":"red"},
                {"id":"teleport_debug_cam","label":"Teleport Pawn to Debug Cam","accent":"cyan"},
                {"id":"debug_cam_to_target","label":"Pull Cam to Target","accent":"gold"},
                {"id":"debug_cam_copy_location","label":"Copy Cam Location","accent":"purple"}
            ]},
            {"id":"sdu_shinies","label":"SDU / GOLDEN CHEST / SHINIES","accent":"gold","actions":[
                {"id":"max_sdu","label":"Max SDU for Selected","accent":"cyan"},
                {"id":"open_golden_chest","label":"Open Golden Chest","accent":"gold"},
                {"id":"close_golden_chest","label":"Close Golden Chest","accent":"red"},
                {"id":"spawn_golden_chest","label":"Spawn Golden Chest","accent":"gold"},
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
                {"id":"give_serial_local","label":"Deliver Local","accent":"green","uses_fields":["bookmark_serial"]},
                {"id":"give_serial_selected","label":"Deliver Named Player","accent":"purple","uses_fields":["bookmark_serial"]},
                {"id":"give_serial_all","label":"Deliver All","accent":"gold","uses_fields":["bookmark_serial"]},
                {"id":"give_serial_nonhost","label":"Deliver Non-Host","accent":"cyan","uses_fields":["bookmark_serial"]}
            ]}
        ]},
        {"id":"bl4_codes","label":"BL4 Codes","cards":[
            {"id":"bl4_codes_catalog","label":"BL4 CODES","accent":"gold","text":"Merged BL4 codes catalog. The external app can use the local Lootlemon/cache JSON without the game; delivery still goes through the bridge.","fields":[
                {"id":"code_search","label":"Search","type":"text","default":""},
                {"id":"code_serial","label":"Serial","type":"multiline","default":""},
                {"id":"serial_override_level","label":"Override delivery level?","type":"choice","choices":["false","true"],"default":"false"},
                {"id":"code_delivery_level","label":"Delivery Level","type":"int","default":70}
            ],"actions":[
                {"id":"codes_load_cache","label":"Load Cache","accent":"cyan"},
                {"id":"codes_refresh_gzo","label":"Refresh GZO","accent":"gold"},
                {"id":"codes_reload_lootlemon","label":"Reload Lootlemon Cache","accent":"gold"},
                {"id":"codes_mattmab_validation","label":"Mattmab Validation","accent":"green"},
                {"id":"codes_import_bookmarks","label":"Import Selected To Bookmarks","accent":"purple"},
                {"id":"give_serial_local","label":"Deliver Local","accent":"green","uses_fields":["code_serial","serial_override_level","code_delivery_level"]},
                {"id":"give_serial_selected","label":"Deliver Named Player","accent":"purple","uses_fields":["code_serial","serial_override_level","code_delivery_level"]},
                {"id":"give_serial_all","label":"Deliver All","accent":"gold","uses_fields":["code_serial","serial_override_level","code_delivery_level"]},
                {"id":"give_serial_nonhost","label":"Deliver Non-Host","accent":"cyan","uses_fields":["code_serial","serial_override_level","code_delivery_level"]}
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
                {"id":"itempool_level","label":"Level","type":"int","default":70},
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
                {"id":"movement_delete_ground_items","label":"Clear Ground Loot (Destroy)","accent":"red"},
                {"id":"movement_hide_ground_loot","label":"Clear Loot (Hide)","accent":"orange"},
                {"id":"movement_pull_ground_loot","label":"Pull Loot Here","accent":"gold"},
                {"id":"movement_super_dash","label":"Super Dash (MSBT)","accent":"cyan"},
                {"id":"movement_super_dash_toggle","label":"Super Dash Toggle (MSBT)","accent":"cyan"},
                {"id":"movement_azzy_super_dash","label":"Super Dash Fire (Azzy)","accent":"purple"},
                {"id":"movement_azzy_super_dash_toggle","label":"Super Dash Toggle (Azzy)","accent":"purple"},
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
                    {"id":"serial_override_level","label":"Override delivery level?","type":"choice","choices":["false","true"],"default":"false"},
                    {"id":"code_delivery_level","label":"Delivery Level","type":"int","default":70},
                ]
            elif tid == "item_pool_spawning" and cid == "item_pool_main":
                card["fields"] = [
                    {"id":"itempool_name","label":"Selected Item Pool","type":"resource_choice","source":"item_pools","default":""},
                    {"id":"itempool_search","label":"Search Item Pools","type":"text","default":""},
                    {"id":"itempool_level","label":"Level","type":"int","default":70},
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


def _normalize_quick_menu_bridge_payload(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Map Electron/bridge field aliases into Quick Menu runner payloads."""
    out = dict(payload or {})
    if action == "give_currency" and "currency_kind" not in out and "currency_index" in out:
        out["currency_kind"] = out.get("currency_index")
    if action == "set_level" and "xp_track" not in out and "xp_track_index" in out:
        out["xp_track"] = out.get("xp_track_index")
    if action.startswith("give_serial_"):
        text = _payload_serial_text(out)
        if text:
            out["serial_text"] = text
        raw_override = out.get("serial_override_level")
        if isinstance(raw_override, str):
            out["serial_override_level"] = raw_override.strip().lower() in ("1", "true", "yes", "on")
        if "serial_level" not in out and "code_delivery_level" in out:
            out["serial_level"] = out.get("code_delivery_level")
    if action == "movement_set_time" and "movement_time_dilation" not in out:
        out["movement_time_dilation"] = (
            out.get("time_dilation") or out.get("time") or 1.0
        )
    return out


def _handle_action(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if action == "status":
        return _status()
    # Assignable Quick Menu actions go through the shared runner so MSBT buttons
    # also populate last_command / last_drop for Pin Last Command.
    # refresh_players stays below because Electron expects an enriched status blob.
    if (
        action in quick_menu_registry.ASSIGNABLE_ACTIONS
        and action != "refresh_players"
    ):
        return backend_actions.run_quick_menu_action(
            action,
            _normalize_quick_menu_bridge_payload(action, payload),
            record=True,
        )
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
    if action == "spawn_golden_chest":
        return backend_actions.spawn_golden_chest()
    if action == "spawn_black_market":
        return backend_actions.spawn_black_market()
    if action == "black_market_clear_cooldown":
        return backend_actions.black_market_clear_cooldown()
    if action == "black_market_status":
        return backend_actions.black_market_status()
    if action == "rewards_open_everyone":
        return backend_actions.rewards_open_everyone()
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
    if action.startswith("uvh_boost_tier_"):
        return backend_actions.uvh_boost_tier(action.rsplit("_", 1)[-1])
    if action == "uvh_boost_all":
        return backend_actions.uvh_boost_all()
    if action == "uvh_boost_cancel":
        return backend_actions.uvh_boost_cancel()
    if action == "uvh_boost_resume":
        return backend_actions.uvh_boost_resume()
    if action == "uvh_boost_status":
        return backend_actions.uvh_boost_status()
    if action == "hoard_set_plan":
        return backend_actions.hoard_set_plan(payload)
    if action == "hoard_status":
        return backend_actions.hoard_status()
    if action == "hoard_start":
        return backend_actions.hoard_start()
    if action == "hoard_stop":
        return backend_actions.hoard_stop()
    if action == "hoard_clear":
        return backend_actions.hoard_clear(payload)
    if action == "complete_challenges_all":
        return backend_actions.complete_challenges_all(payload)
    if action == "complete_challenges":
        return backend_actions.complete_challenges(payload)
    if action == "challenge_catalog_list":
        return backend_actions.challenge_catalog_list(payload)
    if action == "complete_challenges_cancel":
        return backend_actions.complete_challenges_cancel()
    if action == "complete_challenges_status":
        return backend_actions.complete_challenges_status()
    if action == "probe_challenge_apis":
        if not backend_actions.challenge_api_probe_enabled():
            return {
                "ok": False,
                "message": (
                    "Challenge API probe is disabled in shipping builds. "
                    "Set MSBT_DEBUG_PROBES=1 to enable."
                ),
            }
        return backend_actions.probe_challenge_apis()
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
            payload.get("itempool_level") or 70,
        )
    if action == "spawn_itempool_all":
        return backend_actions.spawn_itempool_all(payload)
    if action == "spawn_itempool_cancel":
        return backend_actions.spawn_itempool_cancel()
    if action == "spawn_itempool_status":
        return backend_actions.spawn_itempool_status()
    if action.startswith("dev_spawner_"):
        return backend_actions.run_dev_spawner_action(action, payload)
    if action == "travel_to_map":
        return backend_actions.travel_to_map(payload.get("travel_map"))
    if action == "travel_to_station":
        return backend_actions.travel_to_station(payload.get("travel_station"))
    if action == "location_bookmark_save":
        return backend_actions.location_bookmark_save(payload.get("bookmark_name") or payload.get("name"))
    if action == "location_bookmark_go":
        return backend_actions.location_bookmark_go(payload.get("bookmark_name") or payload.get("name"))
    if action == "location_bookmark_list":
        return backend_actions.location_bookmark_list()
    if action == "location_bookmark_delete":
        return backend_actions.location_bookmark_delete(payload.get("bookmark_name") or payload.get("name"))
    if action == "combat_tuning_apply":
        return backend_actions.combat_tuning_apply(payload)
    if action == "combat_tuning_reapply":
        return backend_actions.combat_tuning_reapply()
    if action == "combat_tuning_reset":
        return backend_actions.combat_tuning_reset(payload.get("scope") or "local")
    if action == "vehicle_preset_apply":
        return backend_actions.vehicle_preset_apply(
            payload.get("vehicle_preset") or payload.get("preset") or payload.get("name"),
            payload.get("scope") or payload.get("vehicle_scope") or "local",
        )
    if action == "vehicle_spawn":
        return backend_actions.vehicle_spawn(
            payload.get("vehicle_id") or payload.get("name") or payload.get("alias"),
            payload.get("scope") or payload.get("vehicle_scope") or "local",
        )
    if action == "vehicle_catalog":
        return backend_actions.vehicle_catalog()
    if action == "movement_teleport_selected_to_me":
        return backend_actions.movement_teleport_selected_to_me()
    if action == "movement_teleport_me_to_selected":
        return backend_actions.movement_teleport_me_to_selected()
    if action == "movement_teleport_all_to_me":
        return backend_actions.movement_teleport_all_to_me()
    if action == "movement_delete_ground_items":
        return backend_actions.movement_delete_ground_items(payload)
    if action == "movement_hide_ground_loot":
        return backend_actions.movement_hide_ground_loot(payload)
    if action == "movement_pull_ground_loot":
        return backend_actions.movement_pull_ground_loot(payload)
    if action == "movement_super_dash":
        return backend_actions.movement_super_dash(payload.get("dash_strength"))
    if action == "movement_super_dash_toggle":
        return backend_actions.movement_super_dash_toggle()
    if action == "movement_azzy_super_dash":
        return backend_actions.movement_azzy_super_dash(payload.get("dash_strength"))
    if action == "movement_azzy_super_dash_toggle":
        return backend_actions.movement_azzy_super_dash_toggle()
    if action == "movement_zero_vault":
        return backend_actions.movement_zero_vault()
    if action == "movement_apply_all":
        return backend_actions.movement_apply_all(payload)
    if action == "movement_reset_all":
        return backend_actions.movement_reset_all()
    if action == "movement_toggle_no_target":
        return backend_actions.movement_toggle_no_target()
    if action == "movement_toggle_noclip":
        return backend_actions.movement_toggle_noclip(payload)
    if action == "movement_toggle_force_fly":
        return backend_actions.movement_toggle_force_fly(payload)
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
    if action == "movement_infinite_jump_toggle":
        return backend_actions.movement_infinite_jump_toggle(payload)
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
            "message": f"{action} should generate a serial locally, then call give_serial_local/give_serial_selected/give_serial_all/give_serial_nonhost.",
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
    if action == "give_serial_local":
        override_level = str(payload.get("serial_override_level") or "false").lower() in ("1", "true", "yes", "on")
        return backend_actions.give_serials(
            _payload_serial_text(payload),
            "local",
            override_level,
            payload.get("serial_level") or payload.get("code_delivery_level") or 70,
        )
    if action in ("give_serial_selected", "give_serial_all"):
        override_level = str(payload.get("serial_override_level") or "false").lower() in ("1", "true", "yes", "on")
        return backend_actions.give_serials(
            _payload_serial_text(payload),
            "all" if action.endswith("all") else "selected",
            override_level,
            payload.get("serial_level") or payload.get("code_delivery_level") or 70,
        )
    if action == "give_serial_nonhost":
        override_level = str(payload.get("serial_override_level") or "false").lower() in ("1", "true", "yes", "on")
        return backend_actions.give_serials(
            _payload_serial_text(payload),
            "nonhost",
            override_level,
            payload.get("serial_level") or payload.get("code_delivery_level") or 70,
        )
    if action == "read_equipped_serials":
        return backend_actions.read_equipped_serials(payload.get("target_player"))
    if action == "read_backpack_serials":
        return backend_actions.read_backpack_serials(payload.get("target_player"))
    if action == "read_inventory":
        return backend_actions.read_inventory(payload.get("target_player"))
    if action == "copy_read_serial":
        return backend_actions.copy_read_serial(
            payload.get("index") if "index" in payload else payload.get("serial_index")
        )
    if action == "copy_all_read_serials":
        return backend_actions.copy_all_read_serials()
    if action == "repeat_last_drop":
        return backend_actions.repeat_last_drop(payload.get("target_player"))
    if action == "set_drop_player_lock":
        return backend_actions.set_drop_player_lock(
            payload.get("enabled", True),
            payload.get("target_player"),
        )
    if action == "quick_menu_action":
        return backend_actions.run_quick_menu_action(
            str(payload.get("action") or payload.get("quick_action") or ""),
            payload,
            record=True,
        )
    if action == "quick_menu_get_layout":
        return backend_actions.get_quick_menu_layout()
    if action == "quick_menu_set_layout":
        return backend_actions.set_quick_menu_layout(_copy_payload(payload))
    if action == "quick_menu_assign_slot":
        return backend_actions.assign_quick_menu_slot(_copy_payload(payload))
    if action == "quick_menu_clear_page":
        return backend_actions.clear_quick_menu_page(_copy_payload(payload))
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
        "host_player_index": backend_status.get("host_player_index"),
        "last_command": backend_status.get("last_command"),
        "last_drop": backend_status.get("last_drop"),
        "drop_player_lock": backend_status.get("drop_player_lock") or {"enabled": False},
        "serial_delivery": backend_status.get("serial_delivery", {}),
        "challenge_bulk": backend_status.get("challenge_bulk") or {},
        "itempool_bulk": backend_status.get("itempool_bulk") or {},
        "uvh_boost": backend_status.get("uvh_boost") or {},
        "serial_text": backend_status.get("serial_text") or "",
        "read_serials": backend_status.get("read_serials") or {},
        "rarity_weights": backend_status.get("rarity_weights") or {},
        "rarity_revision": int(backend_status.get("rarity_revision") or 0),
        "cxp": backend_status.get("cxp") or {},
        "instant_drops": backend_status.get("instant_drops") or {},
        "instant_holds": backend_status.get("instant_holds") or {},
        "fog_of_war": backend_status.get("fog_of_war") or {},
        "third_person": backend_status.get("third_person") or {},
        "mobile_lan": mobile_lan.status_dict(),
        "diagnostics": diagnostics,
        "last_action": _last_action,
        "last_error": last_error,
    }


def _safe_status_stub() -> dict[str, Any]:
    return {
        "ok": True,
        "name": "MattsSDKBoostingTools external bridge",
        "host": _HOST,
        "port": _PORT,
        "started": _started,
        "queue": len(_queue),
        "players": [],
        "selected_player": "",
        "serial_delivery": {},
        "diagnostics": {"external_bridge_started": _started},
        "last_action": _last_action,
        "last_error": _last_error,
        "snapshot_ready": False,
    }


def _get_status_snapshot() -> dict[str, Any]:
    with _lock:
        snapshot = _status_snapshot
        if snapshot is None:
            return _safe_status_stub()
        result = _copy_payload(snapshot)
        result["started"] = _started
        result["queue"] = len(_queue)
        return result


def _refresh_status_snapshot(*, force: bool = False) -> None:
    global _status_snapshot, _status_snapshot_at, _last_error
    now = _now()
    if not force and now - _status_snapshot_at < STATUS_REFRESH_SECONDS:
        return
    try:
        snapshot = _status()
        snapshot["snapshot_ready"] = True
        with _lock:
            _status_snapshot = snapshot
            _status_snapshot_at = now
    except Exception as exc:
        _last_error = repr(exc)


def _process_pending_actions(
    *_args: Any,
    _callback_generation: int | None = None,
    **_kwargs: Any,
) -> None:
    global _last_error, _executing_rid
    started_at = _now()
    if _callback_generation is not None and _callback_generation != _generation:
        return
    try:
        backend_actions.uvh_boost_tick()
    except Exception as exc:
        _last_error = repr(exc)
    try:
        backend_actions.complete_challenges_tick()
    except Exception as exc:
        _last_error = repr(exc)
    try:
        backend_actions.spawn_itempool_tick()
    except Exception as exc:
        _last_error = repr(exc)
    try:
        backend_actions.hoard_tick()
    except Exception as exc:
        _last_error = repr(exc)
    if _callback_generation is not None and _callback_generation != _generation:
        return
    _refresh_status_snapshot()
    for _ in range(8):
        if _callback_generation is not None and _callback_generation != _generation:
            break
        with _lock:
            _prune_results_locked()
            if not _queue:
                break
            item = _queue.popleft()
            rid = str(item.get("id") or "")
            # Do not skip abandoned ids here: a timed-out waiter still wants the
            # action to run on the next idle game tick.  Abandoned ids are only
            # cancelled when a newer /action prunes the queue.
            if rid:
                _executing_rid = rid
            _record_sizes_locked()
        action = item.get("action")
        payload = item.get("payload") or {}
        action_started_at = _now()
        try:
            result = _handle_action(str(action), _copy_payload(payload))
        except Exception as exc:
            message = _format_action_exception(exc)
            _last_error = "" if _is_optional_ui_dependency_error(repr(exc)) else repr(exc)
            result = {"ok": False, "message": message}
        perf_profile.record_call(f"bridge.action.{action}", (_now() - action_started_at) * 1000.0)
        with _lock:
            if _callback_generation is None or _callback_generation == _generation:
                _store_result_locked(rid, result)
                _signal_waiter_locked(rid)
            if _executing_rid == rid:
                _executing_rid = None
            _record_sizes_locked()
    perf_profile.record_call("bridge.tick", (_now() - started_at) * 1000.0)
    return None


def _register_tick_hook() -> None:
    global _tick_registered, _tick_registration
    if _tick_registered or hook is None:
        return
    try:
        token = _generation

        def _generation_tick(*args: Any, **kwargs: Any) -> None:
            global _bridge_tick_last_at, _bridge_tick_in_flight
            if _bridge_tick_in_flight:
                return None
            now = _now()
            if now - _bridge_tick_last_at < _BRIDGE_TICK_MIN_INTERVAL_S:
                return None
            _bridge_tick_last_at = now
            _bridge_tick_in_flight = True
            try:
                _process_pending_actions(*args, _callback_generation=token, **kwargs)
            finally:
                _bridge_tick_in_flight = False
            return None

        _tick_registration = hook(
            "/Script/GbxUIUMG.GbxUIUMGTickWidget:BP_TickWidget",
            immediately_enable=True,
            hook_identifier="matts_sdk_boosting_tools_external_bridge_tick_v1",
        )(_generation_tick)
        _tick_registered = True
    except Exception as exc:
        global _last_error
        _last_error = f"bridge tick hook failed: {exc!r}"


def _unregister_tick_hook() -> None:
    """Best-effort unregister across mods_base hook API versions."""
    global _tick_registered, _tick_registration
    registration = _tick_registration
    for target in (registration, hook):
        if target is None:
            continue
        for name in ("disable", "unregister", "remove"):
            method = getattr(target, name, None)
            if not callable(method):
                continue
            try:
                if target is hook:
                    method("matts_sdk_boosting_tools_external_bridge_tick_v1")
                else:
                    method()
                break
            except Exception:
                continue
    _tick_registration = None
    _tick_registered = False


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

def _request_ip(handler: Any) -> str:
    addr = getattr(handler, "client_address", None)
    if not addr:
        return "127.0.0.1"
    try:
        return str(addr[0] or "127.0.0.1")
    except Exception:
        return "127.0.0.1"


def _request_path(handler: Any) -> str:
    raw = str(getattr(handler, "path", "") or "/")
    return raw.split("?", 1)[0]


def _request_header(handler: Any, name: str) -> str:
    headers = getattr(handler, "headers", None)
    if headers is None:
        return ""
    try:
        return str(headers.get(name) or "").strip()
    except Exception:
        return ""


def _is_loopback_ip(ip: str) -> bool:
    value = str(ip or "").strip().lower()
    return value in {"127.0.0.1", "::1", "localhost", ""}


def _lan_route_denied(path: str) -> bool:
    route = str(path or "")
    return any(route.startswith(prefix) for prefix in _LAN_ROUTES_DENIED)


def _authorized_request(handler: Any) -> tuple[bool, str]:
    ip = _request_ip(handler)
    path = _request_path(handler)
    if _is_loopback_ip(ip):
        return True, ip
    if path.startswith("/mobile/ping"):
        return True, ip
    if path.startswith("/mobile/enroll"):
        if not mobile_lan.enroll_open():
            return False, ip
        return True, ip
    if _lan_route_denied(path):
        return False, ip
    token = _request_header(handler, _DEVICE_HEADER)
    if mobile_lan.is_allowed(ip, token):
        if token:
            try:
                mobile_lan.remember_phone(ip=ip, token=token, name="")
            except Exception:
                pass
        return True, ip
    return False, ip


class _Handler(BaseHTTPRequestHandler):
    server_version = "MSBTBridge/2.0"

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _cors_origin(self) -> str:
        ip = _request_ip(self)
        if _is_loopback_ip(ip):
            return "http://127.0.0.1"
        return "*"

    def _send(self, status: int, data: Any) -> None:
        pretty = "?pretty=1" in self.path or "&pretty=1" in self.path
        body = json.dumps(
            data,
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        ).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", self._cors_origin())
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header(
                "Access-Control-Allow-Headers",
                "Content-Type, X-MSBT-Device, X-MSBT-Pairing-Code, X-MSBT-Enroll",
            )
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
        path = _request_path(self)
        allowed, _ip = _authorized_request(self)
        if path.startswith("/mobile/ping"):
            self._send(200, {
                "ok": True,
                "name": "MattsSDKBoostingTools external bridge",
                "port": _PORT,
                "lan_enabled": mobile_lan.lan_enabled(),
                "direct": True,
            })
            return
        if not allowed:
            if _lan_route_denied(path):
                self._send(404, {"ok": False, "message": "Not found"})
            else:
                self._send(401, {
                    "ok": False,
                    "message": "Phone not paired. Open in-game Phone Pairing and scan the QR.",
                })
            return
        if path.startswith("/status"):
            self._send(200, _get_status_snapshot())
        elif path.startswith("/quick_menu"):
            data = backend_actions.get_quick_menu_layout()
            self._send(200 if data.get("ok") else 500, data)
        elif path.startswith("/layout"):
            if not _is_loopback_ip(_request_ip(self)):
                self._send(404, {"ok": False, "message": "Not found"})
                return
            self._send(200, UI_LAYOUT)
        elif path.startswith("/resource/"):
            if not _is_loopback_ip(_request_ip(self)):
                self._send(404, {"ok": False, "message": "Not found"})
                return
            name = path.split("/resource/", 1)[1].split("?", 1)[0].strip("/")
            data = _load_resource(name)
            self._send(200 if data.get("ok") else 404, data)
        else:
            self._send(404, {"ok": False, "message": "Not found"})

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError(f"Request body exceeds {MAX_BODY_BYTES} byte limit.")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        data = json.loads(raw or "{}")
        return data if isinstance(data, dict) else {}

    def _handle_enroll(self) -> None:
        allowed, ip = _authorized_request(self)
        if not allowed:
            self._send(401, {
                "ok": False,
                "message": "Open the in-game Phone Pairing overlay to enroll this phone.",
            })
            return
        try:
            data = self._read_json_body()
        except ValueError as exc:
            self._send(413, {"ok": False, "message": str(exc)})
            return
        except Exception as exc:
            self._send(400, {"ok": False, "message": repr(exc)})
            return
        token = str(data.get("device") or data.get("token") or _request_header(self, _DEVICE_HEADER) or "").strip()
        if not token:
            token = uuid.uuid4().hex
        result = mobile_lan.enroll(
            str(data.get("nonce") or data.get("n") or ""),
            ip=ip,
            token=token,
            name=str(data.get("name") or "Phone"),
        )
        if result.get("ok"):
            result["device"] = token
        self._send(200 if result.get("ok") else 401, result)

    def do_POST(self) -> None:
        path = _request_path(self)
        if path.startswith("/mobile/enroll"):
            self._handle_enroll()
            return
        if not path.startswith("/action"):
            self._send(404, {"ok": False, "message": "Not found"})
            return
        allowed, _ip = _authorized_request(self)
        if not allowed:
            self._send(401, {
                "ok": False,
                "message": "Phone not paired. Open in-game Phone Pairing and scan the QR.",
            })
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length < 0 or length > MAX_BODY_BYTES:
                self._send(413, {
                    "ok": False,
                    "message": f"Request body exceeds {MAX_BODY_BYTES} byte limit.",
                })
                return
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(raw or "{}")
            action = str(data.get("action") or "")
            payload = _copy_payload(data.get("payload"))
            if not action:
                self._send(400, {"ok": False, "message": "Missing action"})
                return
            # Title/main menu often has no UMG bridge tick — arm live mods immediately.
            if action in _IMMEDIATE_LIVE_MOD_ACTIONS:
                try:
                    result = _handle_action(action, payload)
                except Exception as exc:
                    message = _format_action_exception(exc)
                    result = {"ok": False, "message": message}
                self._send(200, result)
                return
            rid = uuid.uuid4().hex
            wait_timeout = max(
                MIN_CLIENT_TIMEOUT_SECONDS,
                min(MAX_CLIENT_TIMEOUT_SECONDS, float(data.get("timeout", 5.0) or 5.0)),
            )
            enqueued_at = _now()
            waiter = threading.Event()
            with _lock:
                dropped = _prepare_queue_for_enqueue_locked(action)
                if len(_queue) >= MAX_QUEUE_DEPTH:
                    self._send(429, {
                        "ok": False,
                        "message": f"Bridge queue is full ({MAX_QUEUE_DEPTH} actions).",
                    })
                    return
                _waiters[rid] = waiter
                _queue.append({
                    "id": rid,
                    "action": action,
                    "payload": payload,
                    "enqueued_at": enqueued_at,
                    "waiter_deadline": enqueued_at + wait_timeout,
                })
                _record_sizes_locked()
            if dropped:
                _log(f"Cleared {dropped} pending bridge action(s) before enqueueing {action}.")
            deadline = enqueued_at + wait_timeout
            try:
                waiter.wait(wait_timeout)
                with _lock:
                    if _request_was_superseded_locked(rid):
                        _abandoned_rids.discard(rid)
                        self._send(409, {
                            "ok": False,
                            "cancelled": True,
                            "message": "Action was cancelled because a newer bridge command replaced the pending queue.",
                        })
                        return
                    result = _pop_result_locked(rid)
                if result is not None:
                    # Handled action failures are still useful JSON responses for
                    # the external app. Reserve HTTP 500 for bridge/server errors.
                    self._send(200, result)
                    return
                # Waiter gave up. Keep the item queued for an idle in-game tick,
                # but discard any eventual result because no client can consume it.
                with _lock:
                    still_queued = any(str(item.get("id") or "") == rid for item in _queue)
                    result = _pop_result_locked(rid)
                    in_flight = _executing_rid == rid
                    if result is not None:
                        self._send(200, result)
                        return
                    if not still_queued and not in_flight:
                        _abandoned_rids.discard(rid)
                        self._send(409, {
                            "ok": False,
                            "cancelled": True,
                            "message": "Action was cancelled because a newer bridge command replaced the pending queue.",
                        })
                        return
                    _abandoned_rids.add(rid)
                self._send(202, {
                    "ok": True,
                    "queued": True,
                    "message": (
                        "Action is queued or still running in-game. Keep the game unpaused; "
                        "it will apply when the SDK tick finishes."
                    ),
                })
            finally:
                with _lock:
                    _waiters.pop(rid, None)
        except Exception as exc:
            self._send(500, {"ok": False, "message": repr(exc)})


def _listen_host() -> str:
    try:
        return mobile_lan.bind_host()
    except Exception:
        return "127.0.0.1"


def _stop_http_listen(*, join: bool = True) -> None:
    global _server, _thread, _started
    server = _server
    thread = _thread
    _started = False
    try:
        if server is not None:
            if thread is not None and thread.is_alive():
                server.shutdown()
            server.server_close()
    except Exception:
        pass
    if join and thread is not None and thread is not threading.current_thread():
        try:
            thread.join(STOP_JOIN_TIMEOUT_SECONDS)
        except Exception:
            pass
    _server = None
    _thread = None


def _start_http_listen() -> None:
    global _server, _thread, _started, _last_error, _HOST
    host = _listen_host()
    _HOST = host
    server = ThreadingHTTPServer((host, _PORT), _Handler)
    server.allow_reuse_address = True
    thread = threading.Thread(target=server.serve_forever, name="MSBTExternalBridge", daemon=True)
    thread.start()
    _server = server
    _thread = thread
    _started = True
    _log(f"external bridge listening on http://{host}:{_PORT}")
    if host == "0.0.0.0":
        _log(
            "LAN listen on. Windows Firewall may prompt on first bind; "
            "allow private networks for Borderlands 4."
        )


def rebind_http() -> None:
    """Restart the HTTP socket if LAN bind host changed. Never called from tests on 0.0.0.0."""

    def _run() -> None:
        global _last_error
        time.sleep(0.12)
        with _http_lock:
            want = _listen_host()
            bound = str(_HOST or "")
            if _started and bound == want:
                return
            try:
                _stop_http_listen()
                _start_http_listen()
                _refresh_status_snapshot(force=True)
            except Exception as exc:
                _last_error = repr(exc)
                _log(f"bridge rebind failed: {exc!r}")

    threading.Thread(target=_run, daemon=True, name="MSBTBridgeRebind").start()


def start_bridge() -> None:
    global _last_error, _generation, _started
    if _started:
        return
    try:
        mobile_lan.load()
        mobile_lan.set_rebind_callback(rebind_http)
    except Exception:
        pass
    _generation += 1
    _register_tick_hook()
    try:
        with _http_lock:
            _start_http_listen()
        _refresh_status_snapshot(force=True)
    except OSError as exc:
        # Port already open usually means another copy/reload already started it.
        _last_error = repr(exc)
        _started = False
        _unregister_tick_hook()
        _stop_http_listen()
    except Exception as exc:
        _last_error = repr(exc)
        _started = False
        _unregister_tick_hook()
        _stop_http_listen()


def stop_bridge() -> None:
    global _executing_rid, _generation
    global _status_snapshot, _status_snapshot_at
    _generation += 1
    try:
        mobile_lan.set_rebind_callback(None)
    except Exception:
        pass
    with _http_lock:
        _stop_http_listen()
    _unregister_tick_hook()
    with _lock:
        for waiter in _waiters.values():
            waiter.set()
        _queue.clear()
        _results.clear()
        _abandoned_rids.clear()
        _waiters.clear()
        _executing_rid = None
        _status_snapshot = None
        _status_snapshot_at = 0.0
        _record_sizes_locked()
