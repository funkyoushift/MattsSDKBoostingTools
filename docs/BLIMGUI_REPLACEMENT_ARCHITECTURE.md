# BLImGui Replacement Architecture

This project started as an SDK mod with a working BLImGui panel. The public architecture keeps that panel available, but no longer makes it required for the external bridge or standalone app.

## Goals

- Preserve the original BLImGui workflows and behavior.
- Replace BLImGui rendering with a standalone Tkinter control panel.
- Keep the SDK mod focused on live game interaction.
- Keep the external app free of `blimgui`, `unrealsdk`, `mods_base`, and live game imports.
- Let other SDK developers reuse the bridge-safe pattern.

## Runtime Pieces

### SDK Mod

Path:

```text
mod_extracted/MattsSDKBoostingTools/
```

Responsibilities:

- start the HTTP external bridge
- expose live game actions through `backend_actions.py`
- keep BLImGui imports optional
- register SDK commands such as `msbt_external_app`
- run unrealsdk-only behavior inside the game process

Important modules:

- `__init__.py` - mod registration, optional BLImGui setup, bridge startup
- `external_bridge.py` - HTTP action/status bridge
- `backend_actions.py` - bridge-safe action wrappers
- `serial_rewards.py` - live serial reward package delivery
- `inventory_capacity.py` - backpack/bank helpers
- `movement_adjustments.py` - movement and infinite jump helpers
- `travel.py` - map and station travel helpers
- `item_pool_spawning.py` - item pool spawn helpers

### Optional BLImGui UI

Path:

```text
mod_extracted/MattsSDKBoostingTools/blimgui_panel.py
```

This remains the behavior and workflow reference for porting UI into the standalone app.

It should not be imported by the external app.

### Standalone External App

Path:

```text
external_app/v22_parts_codes_fixed/
```

Responsibilities:

- render the user interface with Tkinter
- run local serial conversion and parts breakdown
- search/filter local BL4 Codes resources
- manage local bookmarks
- validate serials locally
- build Legit Builder serials locally
- call the SDK bridge only for live game actions

Important modules:

- `matts_external_app_v22.py` - Tkinter app and tab rendering
- `external_serial_tools.py` - local serial conversion and parts breakdown helpers
- `external_validator.py` - local validation helpers
- `external_legit_builder.py` - local Legit Builder helper API
- `external_app_paths.py` - source/frozen resource path helpers

## Porting Pattern

When porting a BLImGui tab:

1. Read the BLImGui draw function in `blimgui_panel.py`.
2. Identify helper state, filtering, validation, outputs, and status behavior.
3. Move pure/local logic into an external app helper if needed.
4. Replace BLImGui draw calls with Tkinter widgets.
5. Keep labels, order, button behavior, and status messages close to the original.
6. Route live game actions through `external_bridge.py` action names.

## Local Logic

Local app logic includes:

- serial conversion
- parts breakdown
- catalog loading/search/filter/details
- bookmarks and favorites
- validator logic
- Legit Builder filtering, selected parts, validation, and serial generation
- item pool browser state
- travel browser state
- output/copy/status behavior

## Bridge-Only Actions

Bridge-only actions include:

- give serials selected/all/non-host
- give currency/XP
- max level/spec/currency/eridium/SDU
- inventory sizes
- open bank/chest
- drop shinies
- kick player
- spawn item pool
- travel to map/station
- movement/debug/dev commands
- rarity/live modifier commands

## Rule For Other Developers

If a feature can run without the game being open, it belongs in the standalone app. If it must touch `unrealsdk`, a live player, a controller, a world object, or a game reward manager, it belongs in the SDK mod bridge.
