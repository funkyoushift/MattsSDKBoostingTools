# SDK 03 Migration Audit

## Priority

All feature work is paused for this pass. Dev Spawner UI polish, Matt editor work,
Electron experiments, installer work, packaging polish, and new item-making/debug
features stay on hold until the SDK-facing MSBT code is clean on SDK 03 /
oak2-mod-manager v0.3.

SDK 03 is the forward target. SDK 02 compatibility is acceptable only when it does
not add complexity or preserve a deprecated pattern.

## Reference Stack

- oak2-mod-manager v0.3 / Whiskey Foxtrot
- Python 3.14 target
- Mods Base v1.12
- pyunrealsdk v1.10.0
- unrealsdk v3.2.0

Upstream `funkyoushift/oak2-mod-manager` was checked for the current Python target;
its `pyproject.toml` targets Python 3.14.

## Files Audited

SDK-facing production modules:

- `mod_extracted/MattsSDKBoostingTools/__init__.py`
- `mod_extracted/MattsSDKBoostingTools/backend_actions.py`
- `mod_extracted/MattsSDKBoostingTools/external_bridge.py`
- `mod_extracted/MattsSDKBoostingTools/external_app_launcher.py`
- `mod_extracted/MattsSDKBoostingTools/dev_tools.py`
- `mod_extracted/MattsSDKBoostingTools/golden_chest_keybinds.py`
- `mod_extracted/MattsSDKBoostingTools/inventory_capacity.py`
- `mod_extracted/MattsSDKBoostingTools/item_pool_spawning.py`
- `mod_extracted/MattsSDKBoostingTools/movement_adjustments.py`
- `mod_extracted/MattsSDKBoostingTools/party_helpers.py`
- `mod_extracted/MattsSDKBoostingTools/player_economy.py`
- `mod_extracted/MattsSDKBoostingTools/serial_rewards.py`
- `mod_extracted/MattsSDKBoostingTools/shinies.py`
- `mod_extracted/MattsSDKBoostingTools/travel.py`
- `mod_extracted/MattsSDKBoostingTools/blimgui_panel.py` as optional UI fallback only

## Deprecated API Sweep

No production MSBT usage was found for:

- `ValueOption`
- deprecated `on_change` callback patterns
- callback via option `__call__`
- `prevent_hooking_direct_calls`
- `HookType`
- `FGameDataHandle`
- `FGbxInlineStruct`

Existing hooks use the `mods_base.hook(...)` decorator path in:

- `external_bridge.py` for queued bridge actions
- `serial_rewards.py` for queued serial delivery
- `movement_adjustments.py` for infinite jump hooks
- `blimgui_panel.py` for optional UI behavior

No hook migration was required in this pass.

## SDK 03 Fixes Applied

### FGbxDefPtr field names

Old SDK fallback code wrote both the SDK 03 fields and older experimental fields:

- `_experimental_name`
- `_experimental_ref`

These were removed from:

- `player_economy.py`
- `serial_rewards.py`

MSBT now writes `FGbxDefPtr.name` and `FGbxDefPtr.ref`, which matches the SDK 03
field shape.

### FGbxDefPtr resolved instance

Old movement code tried `FGbxDefPtr._experimental_instance` as a fallback when
editing jump-goal definitions. That fallback was removed.

MSBT now reads only `FGbxDefPtr.instance` in:

- `movement_adjustments.py`

### Bridge diagnostics

`backend_actions.get_status()` now reports a best-effort diagnostics object:

- MSBT loaded flag
- Python version
- `mods_base` version if exposed
- `unrealsdk` version if exposed
- `pyunrealsdk` version if exposed
- BLImGui availability
- ActorScriptDeployer availability

`external_bridge._status()` includes those diagnostics and adds the external
bridge started flag.

This lets the external app or a direct `/status` check confirm the SDK 03 runtime
without importing BLImGui or optional UI code.

## BLImGui Optional Status

`__init__.py` still treats BLImGui as optional. If BLImGui or `blimgui_panel.py`
cannot import, the mod logs a warning, keeps command registration where possible,
starts auto-inventory support, and starts the external bridge.

`external_bridge.py` still filters optional BLImGui import errors out of `/status`
so headless use does not look broken just because the optional in-game panel is
missing.

No new BLImGui dependency was introduced.

## ActorScriptDeployer / Dev Spawner Compatibility

`backend_actions.py` routes Dev Spawner actions to ActorScriptDeployer command
objects when available. The audited path does not require BLImGui and does not use
the old panel fallback for Dev Spawner actions.

The SDK 03 migration did not change Dev Spawner features or UI.

## Python 3.14 Readiness

The SDK-facing modules use standard library APIs that remain available on Python
3.14, including:

- `http.server`
- `threading`
- `queue`
- `json`
- `pkgutil`
- `importlib`
- `subprocess`

No removed Python 3.14 APIs were identified in the audited SDK-facing files.

## Remaining Live Verification Needed

These actions should be tested in-game on SDK 03:

1. Mod load without BLImGui installed.
2. External bridge `/status`.
3. Player refresh and selected player targeting.
4. Give serial selected/all/non-host.
5. Currency, XP, max player/spec/currency/eridium/SDU.
6. Inventory selected/all and automatic inventory.
7. Movement apply/reset/infinite jump.
8. Golden chest, bank, shinies.
9. Item pool spawn and travel.
10. Dev Spawner status/cache/targets if ActorScriptDeployer is installed.

## Optional Follow-Up Opportunities

- Add deeper diagnostics for enabled hook state and ActorScriptDeployer command
  availability.
- Revisit `FGameDataHandle` if future SDK 03 APIs expose a cleaner path for
  challenge/unlock or game-data handle operations.
- Consider `HookType.pause` only after live SDK 03 testing shows a real need for
  pausing specific hooks during bulk writes.

## Result

The static SDK 03 migration sweep is clean for the known deprecated patterns, and
the concrete old experimental field accesses were removed. The bridge remains
headless-safe and BLImGui remains optional.
