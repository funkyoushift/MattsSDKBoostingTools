# Bug Fix Plan

This plan is ordered for beta stability first, then BLImGui parity depth. Each item should be its own small commit unless explicitly bundled for the same feature.

## Top 10 Blockers

| Priority | Blocker | User impact | Likely files | Risk |
|---:|---|---|---|---|
| 1 | Boosting Clear Serials does not clear visible pasted serials | Users think clear/delete is broken and may deliver stale serials | `external_app/v22_parts_codes_fixed/matts_external_app_v22.py` | low |
| 2 | Missing automatic backpack/bank checkbox | Busy lobby workflow regression from BLImGui | `ui_layout.json`, `matts_external_app_v22.py`, `backend_actions.py`, `inventory_capacity.py` | medium |
| 3 | Max All reported not working | Core boosting workflow unreliable | `backend_actions.py`, `external_bridge.py`, external status/log UI | medium |
| 4 | Leveling other players reported not working | Multiplayer boosting core failure | `backend_actions.py`, `player_economy.py`, target selection UI | medium |
| 5 | Giving selected items reported not working | Main BL4/Bookmark/Builder delivery failure | `matts_external_app_v22.py`, `backend_actions.py`, `serial_rewards.py` | medium |
| 6 | Multiplayer selected/all/non-host behavior not fully verified | Solo works, lobbies fail | `party_helpers.py`, `backend_actions.py`, external target rows | high |
| 7 | BL4 Codes Mattmab validation button is pending | UI promises validation but does not fully execute | `external_validator.py`, `matts_external_app_v22.py` | medium |
| 8 | Legit Builder still needs exact slot/output parity | Codes may be invalid or incomplete for some item classes | `external_legit_builder.py`, `matts_external_app_v22.py` | high |
| 9 | Movement tab simplified vs BLImGui | Missing controls and ambiguous live effects | `matts_external_app_v22.py`, `ui_layout.json`, `backend_actions.py` | medium-high |
| 10 | Packaging/install instructions need regression coverage | Users may run wrong file or overwrite resources/bookmarks | `README_FIRST.txt`, scripts | low |

## Phase 0 - No-Code Verification Baseline

Before changing behavior, capture current state:

1. `python -m py_compile` for external app and SDK bridge files.
2. Launch source app and packaged EXE.
3. Verify app closes once and stays closed.
4. Verify bridge `/status` works with BLImGui unavailable.
5. Record single-player and multiplayer baseline for targeting, Max All, give selected, item spawn, and level.

## Phase 1 - Tiny Beta Blockers

### Fix 1.1 - Boosting Clear Serials visible widget

Problem: `_clear_boosting_serials_local` only sets `field_vars['serial_text']`. The Tk `Text` widget can keep visible pasted text.

Fix:

- Update `_clear_boosting_serials_local` to clear `self.widgets['serial_text']` if it is a `tk.Text`.
- Also clear `field_vars['serial_text']`.
- Log a short status only.

Validation:

- Paste serials into Boosting Serial Rewards.
- Click Clear Serials.
- Confirm visible text is gone.
- Click Give Selected and confirm empty serial payload is rejected.

Risk: low.

### Fix 1.2 - Clarify Delete/Clear semantics

Problem: Discord reports "cannot Delete or clear serials" may refer to multiple places.

Fix:

- After Fix 1.1, verify Serial Bookmarks Delete, Clear selected, Copy Selected, and BL4 Codes Clear selected.
- If any button only changes state but not list visuals, fix the exact widget refresh.

Risk: low.

## Phase 2 - Restore Auto Backpack/Bank Workflow

Original BLImGui behavior:

- `_draw_inventory_size_card` stores `_auto_inventory_sizes`.
- It exposes `Automatic Backpack and Bank Size for Party`.
- When enabled, it calls `auto_apply_inventory_sizes_if_needed(True, _backpack_size, _bank_size, source="ui-main-thread")` periodically.

Target external behavior:

- Add checkbox `auto_inventory_sizes`.
- Persist local setting beside other external state if needed.
- When enabled and app is connected, periodically call a bridge action such as `set_backpack_bank_all` or add a backend action that mirrors `auto_apply_inventory_sizes_if_needed`.
- It must apply only when explicitly enabled.
- It must not run on app startup unless the stored checkbox is enabled.

Recommended implementation:

1. Add field to `ui_layout.json` card `backpack_bank`.
2. Add external timer that watches checkbox and calls bridge at a conservative interval, only when connected.
3. Prefer adding backend wrapper around `inventory_capacity.auto_apply_inventory_sizes_if_needed` for exact BLImGui behavior.
4. Add status text: `Auto-applied inventory sizes to X party player(s)`.

Risk: medium because it affects live party players repeatedly.

## Phase 3 - Multiplayer Live Action Diagnostics

Add better messages before changing deeper logic.

Targets:

- `max_all`
- `set_level`
- `give_serial_selected`
- `give_serial_all`
- `give_serial_nonhost`
- `spawn_itempool`

Fix direction:

- Add action result messages that include selected player index/name and how many targets were patched.
- For failures, include whether no selected player, no party players, invalid serial, bridge offline, or backend exception.
- Do not spam logs with serial data.

Risk: medium.

## Phase 4 - BL4 Codes Mattmab Validation

Problem: external `_run_bl4_mattmab_validation_local` currently reports `Local Mattmab validation port pending.`

Fix:

- Reuse `external_validator.validate_serial_text` or `validate_many`.
- Iterate filtered or catalog entries, update `mattmab_validator` and `mattmab_validator_detail`.
- Refresh filters/details/count after completion.
- Avoid blocking UI; use a worker with progress.

Risk: medium for performance on large catalogs.

## Phase 5 - Legit Builder Parity Hardening

Do not redesign. Use BLImGui and `legit_builder_core.py` as source of truth.

Work items:

1. Add item-type test matrix for class mods, weapons, shields, repair kits, enhancements, gadgets/heavy.
2. Confirm selected compact parts are exactly the list passed to validate/build.
3. Confirm Base85 output changes when any selected part changes.
4. Confirm Add x Qty respects normal vs unlock mode.
5. Confirm Add All Max Passives selects valid `passive_points` only.
6. Confirm Give Selected/All uses generated Base85 and generic serial delivery actions.

Risk: high because invalid item generation is central to trust.

## Phase 6 - Item Pool And Travel Parity

Item Pool:

- Restore BLImGui search, category chips, pagination, favorites, favorite description, selected status, spawn button order.

Travel:

- Restore BLImGui map list, station list, search rows, show all stations, favorites, favorite descriptions, selected map/station status.

Risk: medium. Mostly local UI plus live spawn/travel actions.

## Phase 7 - Movement / Rarity Parity

Movement:

- Port auto apply saved preset checkbox.
- Port individual jump goals.
- Port per-live-player infinite jump display.
- Port players-only and teleport selected player if backend-safe.
- Verify payload field names for every movement control.

Rarity:

- Decide whether external should expose auto reapply on world change.
- Verify six sliders write correctly in a loaded world.

Risk: medium-high due live movement mutation.

## Do-Not-Touch Warnings

- Do not import SDK/live modules into the external app.
- Do not remove BLImGui UI.
- Do not route local-only catalog/validator/bookmark operations through the bridge.
- Do not auto-run live boost actions on startup.
- Do not overwrite user bookmarks during package updates without backup instructions.
- Do not make Max All or auto inventory run without explicit user action/checkbox.

## Suggested Commit Sequence

1. `beta-fix-boosting-clear-serials-widget`
2. `beta-verify-bookmark-clear-delete-state`
3. `beta-restore-auto-inventory-size-checkbox`
4. `beta-add-live-action-target-diagnostics`
5. `beta-fix-multiplayer-level-and-give-targeting`
6. `beta-port-bl4-mattmab-validation-local`
7. `beta-hardening-legit-builder-item-matrix`
8. `beta-port-itempool-browser-parity`
9. `beta-port-travel-browser-parity`
10. `beta-port-movement-blimgui-parity`
