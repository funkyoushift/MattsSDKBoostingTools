# Full Software Parity Audit Report

Audit date: 2026-07-06

Scope: compare the original BLImGui implementation against the current standalone Tkinter/exe beta and SDK bridge. This is an audit only; no source behavior was changed.

Source of truth:

- `mod_extracted/MattsSDKBoostingTools/blimgui_panel.py`
- `mod_extracted/MattsSDKBoostingTools/legit_builder_core.py`
- original packaged `originalMattsSDKBoostingTools.sdkmod`
- local SDK bridge/backend modules and resources

Current beta:

- `external_app/v22_parts_codes_fixed/matts_external_app_v22.py`
- `external_app/v22_parts_codes_fixed/matts_external_core_v20.py`
- `external_app/v22_parts_codes_fixed/external_serial_tools.py`
- `external_app/v22_parts_codes_fixed/external_validator.py`
- `external_app/v22_parts_codes_fixed/external_legit_builder.py`
- `external_app/v22_parts_codes_fixed/resources/`
- `MSBT_External_Beta.zip`

## Executive Summary

The current beta is much closer to the BLImGui product than the early external app: Serial Tools, Serial Bookmarks, BL4 Codes, Validator, packaging, support links, rarity sliders, and several live bridge actions have been ported or repaired. The biggest remaining gaps are now concentrated in live multiplayer workflow parity and the heavier tools that still differ from BLImGui behavior.

The highest-risk parity failures are:

1. Boosting Serial Rewards `Clear Serials` clears only the backing string variable, not the visible multiline widget.
2. The BLImGui automatic backpack/bank apply checkbox is missing from the external Boosting tab.
3. Multiplayer target-dependent actions need a focused live test pass: level other players, give selected items, non-host delivery, item pool spawning, and Max All.
4. Movement tab is still a simplified layout compared with BLImGui and lacks several controls/status flows.
5. Legit Builder is improved but still needs exact slot-card and output parity verification across item classes.
6. BL4 Codes Mattmab validation button is currently a local placeholder/pending path in the external app.
7. Some bridge fallback branches after `_panel()` still exist and should remain out of the external app path or be removed once proven unused.
8. Favorites for item pools/travel exist in BLImGui but are not fully matched by external app persistence/workflow.
9. Activity/logging is simpler externally and needs crash/error capture instructions.
10. Packaging is good now, but install/extract/resource-path regression tests must stay mandatory.

## Architecture Boundary

External app must remain standalone:

- No runtime imports of `blimgui`, `blimgui_panel`, `unrealsdk`, `mods_base`, `backend_actions`, `external_bridge`, or live SDK modules were found in `external_app/v22_parts_codes_fixed/`.
- Found references are names/comments/function names such as `_tab_serial_tools_blimgui`, not runtime imports.
- Live game mutation correctly belongs in the SDK bridge/backend.
- Local catalog, conversion, validation, bookmarks, filtering, and builder logic belong in the external app.

## Tab Inventory

| Original BLImGui tab/card/tool | Original source | External equivalent | External source | Status | Notes |
|---|---:|---|---:|---|---|
| Tabs row | `_draw_tabs` at `blimgui_panel.py:8046` | Tk notebook tabs from `ui_layout.json` | `matts_external_core_v20.py:_tab` | mostly parity | Same major tabs present. External has native Tk tab styling. |
| Boosting layout | `_draw_three_column_boosting` at `blimgui_panel.py:7982` | `_tab_boosting` | `matts_external_core_v20.py` | partial | Layout is close but several state flows differ. |
| Target Player | inline selector and party helpers | `target_player` card | `ui_layout.json`, `matts_external_core_v20.py` | mostly parity | External uses `index | name` display and bridge `set_target_player`. Needs multiplayer verification. |
| Quick Max | `_max_all_selected`, currency/level helpers | `quick_max` card | `ui_layout.json`, `backend_actions.py` | action mismatch risk | `max_all` is headless now, but Discord says Max All sometimes fails. Needs live target test. |
| Serial Rewards | `_draw_serial_card` at `blimgui_panel.py:3708` | `serial_rewards` card | `ui_layout.json`, `run_action` | broken | Clear Serials does not clear visible pasted text widget. |
| Experience | `_draw_experience_card` at `blimgui_panel.py:3759` | `experience` card | `ui_layout.json`, `backend_actions.give_experience` | needs live test | User reports leveling other players fails. |
| Currency | `_draw_currency_card` at `blimgui_panel.py:3732` | `currency` card | `ui_layout.json`, `backend_actions.give_currency` | mostly parity | Currency kinds present, including vault cards. |
| Backpack / Bank Size | `_draw_inventory_size_card` at `blimgui_panel.py:3789` | `backpack_bank` card | `ui_layout.json` | partial | Missing `Automatic Backpack and Bank Size for Party`. |
| Rarity Drop Weights | `_draw_rarity_disabler_card` at `blimgui_panel.py:1270` | `rarity_weights` card | `ui_layout.json`, `backend_actions.rarity_apply` | mostly parity | Six sliders restored. Need live GameState test and auto reapply parity review. |
| Cheats / Debug Cam | `_draw_dev_tools_card` at `blimgui_panel.py:5025` | `cheats_debug` card | `ui_layout.json`, `backend_actions` | partial | External card omits some devperk labels/actions visible in BLImGui. |
| SDU / Chest / Shinies | `_draw_sdu_card` at `blimgui_panel.py:3831` | `sdu_shinies` card | `ui_layout.json`, `backend_actions` | mostly parity | Live verification needed for multiplayer target. |
| Serial Tools | `_draw_serial_tools_tab` at `blimgui_panel.py:7719` | `_tab_serial_tools_blimgui` | `matts_external_app_v22.py:1155` | mostly parity | Local conversion/breakdown/copy implemented. |
| Serial Bookmarks | `_draw_serial_store_tab` at `blimgui_panel.py:7607` | `_tab_serial_bookmarks_local` | `matts_external_app_v22.py:1012` | mostly parity | Local browser/details/delivery split exists. Row click toggles checked; BLImGui selectable behavior is similar. |
| BL4 Codes | `_draw_gzo_codes_tab` at `blimgui_panel.py:7486` | `_tab_bl4_codes_v13` | `matts_external_app_v22.py:1307` | mostly parity | Catalog/filter/details/bookmark/delivery ported. Mattmab validation is pending locally. |
| Legit Builder | `_draw_legit_builder_tab` at `blimgui_panel.py:9673` | `_tab_legit_builder_v9` | `matts_external_app_v22.py:156` | partial | Core logic copied, but exact slot workflow still needs full parity verification. |
| Validator | `_draw_validator_tab` at `blimgui_panel.py:9580` | `_tab_validator_blimgui` | `matts_external_app_v22.py:894` | mostly parity | Local worker/progress/basic/bulk/cancel exists. |
| Item Pool Spawning | `_draw_item_pool_tab` at `blimgui_panel.py:9815` | generic/resource tab | `ui_layout.json`, `matts_external_core_v20.py` | partial | External is simplified and lacks BLImGui paging/category/favorite detail workflow. |
| Map Travel | `_draw_travel_tab` at `blimgui_panel.py:10017` | generic/resource tab | `ui_layout.json`, `matts_external_core_v20.py` | partial | External two-list layout exists but does not fully match BLImGui search/favorite/show-all flow. |
| Player Movement | `_draw_movement_tab` at `blimgui_panel.py:4754` | `_tab_movement` | `matts_external_app_v22.py:58` | partial | Missing several BLImGui controls and auto/debounce status details. |
| Activity Log | `_draw_log_card` at `blimgui_panel.py:7759` | Activity Log tab | `ui_layout.json`, core output | mostly parity | External log is simpler; needs crash/error visibility policy. |
| Support/follow/credits | BLImGui header/support controls | external header buttons | `matts_external_core_v20.py` | mostly parity | Ko-fi, Twitch, YouTube links present. |

## Button And Action Parity Matrix

| Feature | Original behavior | External behavior | Status | Fix recommendation |
|---|---|---|---|---|
| Refresh Players | Refresh/select live party | `/action refresh_players` | mostly parity | Live test with 1, 2, 3, 4 players. |
| Use Selected Target | Select party index/name | `/action set_target_player` with raw index/name | mostly parity | Verify all target rows map displayed `index | name` to raw index. |
| Kick Player | Live kick selected player | `backend_actions.kick_selected_player` | mostly parity | Verify host-only behavior/errors. |
| MAX ALL | Player level, spec, currency, eridium, SDU | `backend_actions.max_all` | reported broken | Add live diagnostic output per sub-action and test selected/all expectation. |
| MAX CASH/ERIDIUM | Max selected wallet | `backend_actions.max_currency/max_eridium` | mostly parity | Live test selected target. |
| MAX PLAYER/SPEC | Max selected XP track | `backend_actions.max_player_level/max_spec_level` | reported risk | Live test non-host target. |
| Serial Rewards Give Selected | Parse serials, patch selected target | `give_serial_selected` | reported broken | Verify target is set before delivery and serial text visible state matches payload. |
| Serial Rewards Give All | Patch all party | `give_serial_all` | needs live test | Test with host + joined clients. |
| Serial Rewards Give Non-Host | Patch non-host party indices | `give_serial_nonhost` | needs live test | Verify host index detection in remote sessions. |
| Clear Serials | Clear text input and state | `_clear_boosting_serials_local` only sets var | broken | Clear the actual `tk.Text` widget for `serial_text`. |
| Set Player Level | Selected target track/level | `set_level` -> `give_experience` | reported broken | Verify payload `xp_track`, `level`, selected target name. |
| Give Currency | Currency kind/amount selected target | `give_currency` | needs live test | Verify vault card currency strings. |
| Backpack/Bank Selected/All | Manual apply plus BLImGui auto checkbox | Manual selected/all only | missing workflow | Restore automatic inventory checkbox/state and repeated apply behavior. |
| Rarity Apply | Six weights + auto reapply option | Six sliders -> `rarity_apply` | mostly parity | Consider exposing `Auto reapply on world change`. |
| Dev perks | Multiple devperk buttons | subset of devperk buttons | partial | Restore missing devperk 6/7 if intended. |
| Open Bank/Chest/Shinies | Live actions | backend direct actions | mostly parity | Live host/session test. |
| Serial Tools Convert/Clear/Copy | Local convert, auto-convert, outputs, copy | local helper/output boxes | mostly parity | Regression test no bridge post. |
| Serial Bookmarks CRUD | Local JSON load/save/browser/details | local JSON load/save/browser/details | mostly parity | Verify Delete, Clear selected, Copy selected in package. |
| Serial Bookmarks delivery | Bridge give serial selected/all/non-host | generic bridge delivery | mostly parity | Live target tests. |
| BL4 Codes load/cache/filter/details | Local cache/catalog | local cache/catalog | mostly parity | Verify selected rows/check state and resource freshness. |
| BL4 Codes Mattmab Validation | Catalog validation worker | status says pending | partial | Port local catalog validation over `external_validator`. |
| BL4 Codes delivery | Bridge give serial selected/all/non-host | generic bridge delivery | mostly parity | Live target tests. |
| Validator basic/bulk/clear/cancel | Local pure validation worker | local worker | mostly parity | Test large paste/cancel. |
| Legit Builder Validate/Build | Local core validation/build | local helper | partial | Compare every slot and output against BLImGui. |
| Legit Builder Give Selected/All | Generate final serial, bridge deliver | local generated serial then bridge | needs verification | Do not call old `legit_*` bridge actions. |
| Item Pool Spawn/Favorite | Search/category/page/favorites/spawn | simplified resource selector/spawn | partial | Port BLImGui browser/favorites. |
| Travel map/station/favorite | Search maps, stations, show-all, favorites | simplified two-list | partial | Port exact BLImGui flow. |
| Movement apply/reset/presets | Debounced sliders, saved presets, per-player infinite jump | simplified bridge buttons/fields | partial | Rebuild from BLImGui tab after higher blockers. |
| Activity Log Clear | Clear log lines | local clear plus bridge status clear | mostly parity | Add crash/error reporting policy. |

## Dropdown, List, And State Findings

| State/control | Original state/source | External state/source | Status | Issue |
|---|---|---|---|---|
| Target player choices | live party contexts/player array | bridge `/status` players, `index | name` | mostly parity | Needs stale list and join-after-start tests. |
| Serial Rewards input | `_serial_text` string tied to visible input | `field_vars['serial_text']` plus `tk.Text` widget | broken | Clear action updates var only; widget can stay stale. |
| Inventory auto checkbox | `_auto_inventory_sizes` persisted in settings | missing | missing | Directly matches Discord request. |
| BL4 selected rows | `_gzo_selected_ids` | `bl4_selected_ids` | mostly parity | Single click toggles selection; verify not surprising. |
| Bookmark selected rows | `_serial_store_selected_ids` | `checked_bookmark_ids` | mostly parity | Single click toggles, double click currently does not toggle separately. |
| Legit selected parts | `_legit_selected_parts_text` and core lines | canonical list helpers and text | partial | Recently repaired, but class mod/weapon test matrix still needed. |
| Movement values | many globals with sliders/debounce | simplified fields and direct apply | partial | Missing individual jump goals, auto apply saved preset, players-only, teleport buttons in UI. |
| Rarity weights | `_rarity_weights`, persisted, auto reapply | slider fields and backend memory | mostly parity | Auto reapply world-change UI not exposed externally. |
| Item pools | filtered list, category buttons, page, favorites | resource choice/search simplified | partial | BLImGui pagination/favorite descriptions missing. |
| Travel | map list/station list, show all, favorites | local two-list simplified | partial | Need show-all stations and favorites parity. |
| Validator progress | worker state/progress/cancel | local thread/progress | mostly parity | Need large bulk stress tests. |

## Local Vs Bridge Routing

Local-only actions in current app:

- `serial_convert`, `serial_breakdown`, `clear_serial_tools`
- Serial Bookmarks CRUD/copy/import/filter
- BL4 Codes load cache, reload local Lootlemon cache, search/filter/details/bookmark/import, parts breakdown
- `validator_basic`, `validator_bulk`, `validator_clear`
- Legit Builder local validate/build/max passives/clear parts
- local logs and local copy operations

Bridge-only/live actions:

- `/status`, `refresh_players`, `set_target_player`
- `give_serial_selected`, `give_serial_all`, `give_serial_nonhost`
- `give_currency`, `set_level`, max level/spec/currency/eridium/SDU/all
- bank/chest/shiny/kick
- item pool spawn
- map/station travel
- movement, infinite jump, no target/noclip/time/delete ground items
- rarity GameState writes
- debug/dev perks

Routing issues or risks:

- `clear_serials` is local in external app and backend, but external local path does not clear the widget.
- `codes_mattmab_validation` is intentionally external-owned in bridge but not fully implemented locally.
- Old bridge fallback branches after `p = _panel()` still exist for many actions. They should not be hit by the external app after local/headless routing, but they remain a BLImGui dependency risk if a missed action routes there.
- External `run_action` still contains a compatibility fallback for `legit_validate_build`, `legit_give_selected`, `legit_give_all` before calling `super()`, but the intended current path is local validate/build and generic serial delivery.

Forbidden reference search:

- No runtime imports of forbidden modules were found in the external app.
- Text mentions in docstrings/function names are harmless naming/comment references.

## Legit Builder Deep Audit

Original BLImGui functions:

- `_draw_legit_builder_tab` at `blimgui_panel.py:9673`
- root/type/manufacturer helpers at `blimgui_panel.py:8236-8330`
- slot/part helpers at `blimgui_panel.py:8366-8612`
- max passive helpers at `blimgui_panel.py:8817-8858`
- validation/build at `blimgui_panel.py:8881`
- give/copy output helpers at `blimgui_panel.py:9624-9656`

Current external functions:

- `_tab_legit_builder_v9` at `matts_external_app_v22.py:156`
- state/filter/build helpers at `matts_external_app_v22.py:212-548`
- `external_legit_builder.py` mirrors major core functions such as `roots`, `slots`, `slot_counts`, `is_part_allowed`, `search_parts`, `describe_part`, `validate_build`, and `build_base85`.

Matches:

- Pure builder core is local.
- Type/manufacturer/root flow exists.
- Class mod detection was repaired to accept `item_type == "class_mod"` and `classmod_` roots.
- Selected parts are intended to feed both visible active build and Base85 output.
- Local give should deliver generated Base85 through generic serial bridge actions.

Mismatches/risks:

- External helper begins with a note that it is conservative and does not emulate every UI quirk.
- Full BLImGui slot-card behavior still needs item-type matrix testing.
- Add/Replace, Add x Qty, duplicate preservation, and exact-one replacement need repeated verification for weapons, shields, class mods, gadgets, enhancements, and repair kits.
- Max passives was recently fixed for class mods, but should be validated against every class mod root, not only `classmod_robodealer`.
- User-visible status/debug should remain until the builder is stable.

## Movement / Infinite Jump Deep Audit

Original BLImGui movement has:

- Presets / Save / Apply card
- Apply Now, Save Preset, Load Saved, Reset Defaults
- Auto apply saved preset on game load
- Fast, Very Fast, Moon, Wall Walk, Fast Glide presets
- Speed, Jump/Gravity, Wall/Step, Glide/Dash/Vault cards
- Individual jump goals
- Infinite Jump per live party player plus All ON/OFF
- World/Utility: time dilation, players only, no target, delete ground items, noclip
- Teleport selected player to P1/P2/P3/P4
- debounced slider apply behavior

Current external movement has:

- simplified speed/jump/wall/glide/utility/infinite jump cards
- bridge routes for apply/reset/presets/no target/noclip/time/infinite jump
- several controls missing or differently grouped

Status: partial. The backend is much better than the UI parity. This should be a later focused port.

## Rarity Deep Audit

Original BLImGui rarity has:

- six rarity rows
- Apply, Reset All, Only Legendary, Only Pearlescent
- auto reapply on world change
- persisted rarity settings
- GameState discovery/reapply logic

Current external:

- six slider fields now exist in `ui_layout.json`
- bridge/backend accepts `rarity_common_percent`, `rarity_uncommon_percent`, `rarity_rare_percent`, `rarity_epic_percent`, `rarity_legendary_percent`, `rarity_pearlescent_percent`
- package scripts copy current source resources into packaged resources

Status: mostly parity for visible sliders and direct actions. Missing or unverified: auto reapply setting visibility and live world-change reapply behavior.

## Persistence And Resource Audit

| File/resource | Source path | Packaged path | Purpose | Writable? | Notes |
|---|---|---|---|---|---|
| `ui_layout.json` | `external_app/.../resources/ui_layout.json` | `MattsSDKBoostingTools_external/resources/ui_layout.json` | external layout/actions | yes, but treat as app resource | Package now overwrites stale resource. |
| `user_serial_bookmarks.json` | external resources | packaged resources | Serial Bookmarks store | yes | User data should be backed up before replacing resources. |
| `MattsSDKBoostingTools_gzo_codes.json` | external resources | packaged resources | BL4/GZO catalog cache | yes/cache-like | App reads local cache. |
| `MattsSDKBoostingTools_lootlemon_codes.json` | external resources | packaged resources | Lootlemon local code/link cache | yes/cache-like | No website scraping in external app. |
| `gzo_parts_map.json` | external resources | packaged resources | serial parts breakdown map | app resource | Required for breakdown. |
| `legit_rules_flat.json` | external resources | packaged resources | Legit Builder/Validator rules | app resource | Must stay in sync with SDK source of truth. |
| `item_pools.json` | external resources | packaged resources | item pool browser | app resource | Favorites not fully externalized. |
| `travelmaps_flat.json` | external resources | packaged resources | map browser | app resource | Used locally. |
| `travelstations.json` | external resources | packaged resources | station browser | app resource | Used locally. |
| `app_icon.ico` | external resources | packaged resources | EXE icon | app resource | Present. |

## Packaging / EXE Audit

Current beta zip contains:

- `MSBT_External_Beta/Launch_MSBT_External_App.bat`
- `MSBT_External_Beta/MattsSDKBoostingTools.sdkmod`
- `MSBT_External_Beta/README_FIRST.txt`
- `MSBT_External_Beta/MattsSDKBoostingTools_external/MattsBoostingToolsExternal.exe`
- `_internal/` PyInstaller runtime
- `resources/` beside the EXE
- root and legacy launcher BAT files

Packaging scripts:

- `build_external_exe.ps1` builds onedir EXE and copies current resources beside the EXE.
- `package_external_beta.ps1` creates a fresh package folder, copies dist, deletes stale package resources, copies current source resources, writes README, removes `__pycache__`, and zips the package.

Packaging status:

- Python is not required for beta users when using `MattsBoostingToolsExternal.exe`.
- Resource path helper uses `sys.executable` parent when frozen and source file parent when running from source.
- Old auto-reopen cause was fixed by removing duplicate startup; launchers use one-shot `start`.

Remaining packaging risks:

- Users must extract the zip folder, not run files directly from inside the archive.
- Replacing the whole resources folder can overwrite user bookmarks unless instructions warn users to preserve `user_serial_bookmarks.json`.
- Keep a regression test that packaged `ui_layout.json` contains current rarity sliders and no stale placeholder text.

## Most Important Open Parity Gaps

1. Fix Boosting `Clear Serials` visible widget/state mismatch.
2. Restore automatic backpack/bank apply checkbox and behavior.
3. Live-test Max All with selected remote players.
4. Live-test level/give selected/non-host in multiplayer.
5. Finish BL4 Codes Mattmab validation local implementation.
6. Fully port Movement UI parity.
7. Fully port Item Pool browser/category/favorites parity.
8. Fully port Map Travel search/favorite/show-all parity.
9. Continue Legit Builder item-type matrix parity testing.
10. Add crash/log collection guidance and more user-facing failure messages.
