# QA Test Plan

This checklist is intended to be rerun after every beta change. Tests are grouped by offline, live game, multiplayer, and packaging.

## Offline Tests

| ID | Feature | Steps | Expected result | Failure symptoms | Likely files |
|---|---|---|---|---|---|
| OFF-001 | Source app import | Run external app import check without game. | Import succeeds. | Import error, forbidden SDK import. | `matts_external_app_v22.py`, helper modules |
| OFF-002 | EXE launch | Open `MattsBoostingToolsExternal.exe` directly. | App opens without Python. | Missing DLL/resource, app does not open. | packaging scripts, `external_app_paths.py` |
| OFF-003 | EXE close | Close the EXE. | App exits and stays closed. | App reopens or remains in Task Manager. | launchers, `matts_external_app_v22.py` |
| OFF-004 | Root BAT launch | Run `Launch_MSBT_External_App.bat`. | Starts app once, BAT exits. | Loop/reopen, wrong path, console stuck. | root BAT |
| OFF-005 | Legacy BAT launch | Run `MattsSDKBoostingTools_external/Launch_MattsBoostingTools_External.bat`. | Starts app once, BAT exits. | Loop/reopen. | legacy BAT |
| OFF-006 | Resources load | Start app with bridge offline. | Tabs render, resources loaded, offline message visible. | Missing layout/resource errors. | `external_app_paths.py`, resources |
| OFF-007 | Rarity sliders visible | Open Boosting. | Six rarity sliders visible. | Placeholder text or missing sliders. | `ui_layout.json`, package resources |
| OFF-008 | Serial Tools convert @U | Paste known @U serial and Convert. | Human output, @U output, parts breakdown populated. | Bridge call, empty output, error. | `external_serial_tools.py` |
| OFF-009 | Serial Tools convert human | Paste human readable serial and Convert. | @U output generated. | Serialization fails. | `external_serial_tools.py` |
| OFF-010 | Serial Tools clear | Convert, then Clear. | Input and all outputs cleared. | Any old output remains. | `matts_external_app_v22.py` |
| OFF-011 | Serial Tools copy buttons | Copy each output. | Clipboard receives selected output; short log only. | Empty copy or huge global log spam. | `matts_external_app_v22.py` |
| OFF-012 | Serial Bookmarks save | Create bookmark, Save. | Row appears with name/group. | Row missing, JSON unchanged. | bookmark helpers |
| OFF-013 | Serial Bookmarks delete | Select active bookmark, Delete. | Row removed, fields cleared. | Row remains, stale details. | bookmark helpers |
| OFF-014 | Serial Bookmarks clear selected | Check rows, Clear. | Checked markers cleared, rows remain saved. | Deletes bookmarks or markers remain. | bookmark helpers |
| OFF-015 | Serial Bookmarks copy selected | Check two rows, Copy Selected Serials. | Clipboard gets one serial per line. | Empty/wrong clipboard. | bookmark helpers |
| OFF-016 | BL4 Codes load cache | Open BL4 Codes. | Rows load from local resources. | Empty catalog with resource present. | BL4 local helpers/resources |
| OFF-017 | BL4 Codes filters | Search/filter listing/type/rarity. | Count/list/details update. | Stale rows or wrong filters. | `_populate_bl4_codes_v13` |
| OFF-018 | BL4 Codes bookmark | Bookmark active code. | Serial Bookmarks receives entry. | Bookmark saved elsewhere or not visible. | BL4 + bookmark helpers |
| OFF-019 | BL4 Codes parts breakdown | Select code, Run/copy breakdown. | Local breakdown generated. | Bridge call or missing map error. | `external_serial_tools.py`, `gzo_parts_map.json` |
| OFF-020 | Validator basic | Paste known serial, Validate Basic. | Result classified LEGIT/MODDED/ERROR with details. | Bridge call, no result. | `external_validator.py` |
| OFF-021 | Validator bulk | Paste multiple serials, Validate Bulk. | Progress/result list updates. | UI freezes, wrong count. | validator worker |
| OFF-022 | Validator cancel | Start large bulk, Cancel. | Worker stops cleanly and status updates. | UI freeze or partial exception. | validator worker |
| OFF-023 | Legit class mod build | Select class mod root, inv_comp/body/firmware/passives, Build Base85. | Human and Base85 include selected parts. | Base85 empty or missing selected parts. | `external_legit_builder.py`, legit UI |
| OFF-024 | Add All Max Passives | Select `classmod_robodealer`, unlock if required, Add All Max Passives. | Passive rows selected, output cleared for rebuild. | "only for class mod roots" error. | legit UI |
| OFF-025 | Legit root change clearing | Build one item, change root variant. | selected parts and outputs clear. | stale parts remain. | legit UI |

## Live Game Single-Player Tests

| ID | Feature | Steps | Expected result | Failure symptoms | Likely files |
|---|---|---|---|---|---|
| LIVE-001 | Bridge status | Load game with SDK mod, click Status. | Player list appears, selected index/name valid. | Bridge offline or empty list. | `external_bridge.py`, `backend_actions.py` |
| LIVE-002 | Set target | Select local player, Set Target. | Bridge status selected player updates. | Wrong index/name. | target row helpers |
| LIVE-003 | Max currency | Click Max Cash. | Selected wallet set. | No effect/error. | `player_economy.py`, backend |
| LIVE-004 | Max eridium | Click Max Eridium. | Selected eridium set. | No effect/error. | `player_economy.py`, backend |
| LIVE-005 | Set player level | XP track player, level 60. | Selected player reaches level 60. | Wrong player or no change. | `give_experience` |
| LIVE-006 | Spec level | Set Spec 701. | Spec level updated. | No change. | `give_experience` |
| LIVE-007 | Max All | Click MAX ALL. | Level/spec/currency/eridium/SDU updated. | partial success or no effect. | `backend_actions.max_all` |
| LIVE-008 | Backpack/bank selected | Set sizes and apply selected. | Selected containers update. | no effect. | `inventory_capacity.py` |
| LIVE-009 | Open bank | Click Open Bank Anywhere. | Bank UI opens. | no UI/open error. | `travel._exec_console` |
| LIVE-010 | Golden chest | Open then Close Golden Chest. | Chest opens/closes. | no effect. | chest helpers |
| LIVE-011 | Drop shinies | Click Drop All Shinies. | Shinies drop for selected. | no effect/error. | `shinies.py` |
| LIVE-012 | Item pool spawn | Spawn selected item pool level/count. | Pool spawns near local player. | no spawn or crash. | `item_pool_spawning.py` |
| LIVE-013 | Map travel | Select map, travel. | Map travel command executes. | no travel/error. | `travel.py` |
| LIVE-014 | Station travel | Select station, travel. | Station travel command executes. | wrong station/no travel. | `travel.py` |
| LIVE-015 | Movement apply/reset | Change speed/jump, Apply, Reset. | Movement changes then resets. | no effect or bad values. | `movement_adjustments.py` |
| LIVE-016 | Infinite jump selected | Select player, toggle infinite jump. | Selected pawn gets repeated jump behavior. | wrong/no player. | movement backend |
| LIVE-017 | Rarity apply/reset | Change sliders, Apply, Reset. | GameState weights change, message includes writes. | no GameState found or no effect. | rarity backend |

## Multiplayer Tests

| ID | Feature | Steps | Expected result | Failure symptoms | Likely files |
|---|---|---|---|---|---|
| MP-001 | Player refresh after join | Start host, have client join, click Refresh Players. | All party players listed in order. | joined player missing/stale. | `party_helpers.py` |
| MP-002 | Target selected remote | Choose remote player and Set Target. | selected name/index matches remote. | selected host/local instead. | target helpers |
| MP-003 | Give serial selected | Deliver one known serial to remote selected. | only selected target receives patched item. | host/all/no one receives. | `serial_rewards.py` |
| MP-004 | Give serial all | Deliver one known serial all. | all party players receive item. | host only or selected only. | `serial_rewards.py` |
| MP-005 | Give serial non-host | Deliver one known serial non-host. | all non-host players receive item, host does not. | host receives or no remote receives. | host index detection |
| MP-006 | Level selected remote | Select remote, Set Player Level. | remote levels, host unchanged. | host levels or no effect. | `player_economy.py` |
| MP-007 | Max All selected remote | Select remote, MAX ALL. | remote receives all selected boosts. | partial or wrong player. | `backend_actions.max_all` |
| MP-008 | Backpack/bank all | Apply to all party. | every party player gets sizes. | only host/selected updated. | inventory backend |
| MP-009 | Auto backpack/bank if restored | Enable checkbox, new player joins. | new player auto-applied within interval. | no auto apply or repeated spam. | inventory auto logic |
| MP-010 | Item pool spawn in lobby | Spawn item pool as host. | items spawn safely near host/local. | crash/no spawn. | item pool backend |
| MP-011 | Joined client safety | Use app as non-host where supported. | unsupported actions fail clearly. | silent wrong action/crash. | backend live checks |

## Packaging Tests

| ID | Feature | Steps | Expected result | Failure symptoms | Likely files |
|---|---|---|---|---|---|
| PKG-001 | Fresh build | Run `build_external_exe.ps1`. | EXE built, resources copied beside EXE. | stale/missing resources. | build script |
| PKG-002 | Fresh package | Run `package_external_beta.ps1`. | Package folder and zip created. | old resources copied. | package script |
| PKG-003 | Zip contents | Inspect zip. | EXE, `_internal`, resources, SDK mod, launchers, README. | source-only app or missing EXE. | package script |
| PKG-004 | No junk | Inspect package. | no `__pycache__`, `.git`, `.venv`, old zips. | junk included. | scripts |
| PKG-005 | Resource freshness | Search packaged `ui_layout.json` for rarity fields and stale placeholder text. | rarity field found, stale text absent. | old placeholder appears. | package script |
| PKG-006 | Extracted-folder run | Extract zip to fresh folder and launch EXE. | App runs from extracted folder. | resource path errors. | `external_app_paths.py` |
| PKG-007 | No Python requirement | On a system without Python association, launch EXE. | App opens. | prompts for app to open `.py`. | packaging |
| PKG-008 | User bookmark preservation | Update package over existing user folder. | User warned/preserves bookmarks. | bookmarks overwritten. | release process |

## Known Bug Regression Tests

| ID | Bug | Steps | Expected result |
|---|---|---|---|
| REG-001 | Boosting clear serials | Paste in Boosting serial box, click Clear Serials. | Visible box and payload clear. |
| REG-002 | Delete/clear serials | Create bookmark, delete it; select rows, clear selected. | Delete removes active row; Clear only unchecks. |
| REG-003 | Auto backpack/bank missing | Inspect Boosting inventory card. | If implemented, checkbox present and safe; if not, test is expected fail/open. |
| REG-004 | Max All buttons | Select target, click MAX ALL. | All sub-actions succeed or identify failing sub-action. |
| REG-005 | Leveling others | Select remote player, level to 60. | Remote player changes. |
| REG-006 | Giving selected items | Deliver selected from BL4 Codes and Bookmarks. | Selected target receives item. |
| REG-007 | App auto-start/reopen | Launch, close, wait 30 seconds. | App remains closed. |
| REG-008 | Crash report | Trigger bridge offline/live error. | App displays useful error and stays open. |
| REG-009 | Rarity resource stale | Open packaged Boosting. | Six sliders visible. |
| REG-010 | Legit Base85 selected parts | Build class mod after selecting parts. | Base85 output changes and validates. |

## Recommended Release Gate

Do not send a new beta zip unless all of these are green or explicitly marked as known open issues:

- OFF-001 through OFF-023
- LIVE-001 through LIVE-008
- MP-001 through MP-007
- PKG-001 through PKG-007
- REG-001 through REG-009
