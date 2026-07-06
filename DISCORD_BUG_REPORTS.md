# Discord Bug Reports Review

Source: attached tester/chat export from July 3-6, 2026. Quotes are lightly normalized for readability.

## Reported Issues

| ID | Quote/paraphrase | Feature area | Priority | Status | Suspected files/functions | Regression test |
|---|---|---|---:|---|---|---|
| D-001 | "When you paste the serials into the window in the boosting section and you press the clear serials button the serials still remain." | Boosting Serial Rewards | P0 | open/confirmed | `matts_external_app_v22.py:_clear_boosting_serials_local`, `ui_layout.json` `serial_text` field | Paste serials, click Clear Serials, verify visible widget and payload are empty. |
| D-002 | "You still have to manually raise backpack and bank levels." | Backpack/Bank | P0 | open/confirmed parity gap | `blimgui_panel.py:_draw_inventory_size_card`, external `backpack_bank` card, `backend_actions.py` | Join/rejoin party players and verify auto inventory behavior if enabled. |
| D-003 | "With the previous one you had a checkbox which you checked and as they spawned in it maxed them out." | Auto inventory apply | P0 | open/confirmed missing | BLImGui `_auto_inventory_sizes`, `inventory_capacity.auto_apply_inventory_sizes_if_needed` | Enable auto checkbox, have a new player join, expect sizes auto-applied. |
| D-004 | "External app doesn't launch when opening the file." | Packaging/launcher | P1 | fixed but verify | `build_external_exe.ps1`, `package_external_beta.ps1`, launchers | Fresh extraction, double-click launcher and EXE on a machine without Python. |
| D-005 | "It tried to open in Notepad... picked Python..." | Python dependency/file association | P1 | fixed by EXE packaging, verify | EXE package, README | Launch EXE only; no Python prompt. |
| D-006 | "It won't work if it's just on your desktop and not in a folder." | Packaging/resource path | P1 | likely fixed, verify | `external_app_paths.py`, package layout | Run from extracted folder; verify clear error if resources missing. |
| D-007 | "My max all buttons don't work." | Quick Max / Max All | P0 | open/needs live repro | `backend_actions.max_all`, `player_economy.py`, target selection | Select local and remote targets; click MAX ALL; verify each sub-action. |
| D-008 | "Cannot Delete or clear serials." | Serial Rewards / Serial Bookmarks / BL4 selected rows | P0 | partly confirmed | `_clear_boosting_serials_local`, bookmark delete/clear helpers | Test Boosting clear, Bookmark delete, Bookmark clear selected, BL4 clear selected. |
| D-009 | "Wasn't leveling up other players." | XP/player targeting | P0 | open/needs multiplayer repro | `backend_actions.give_experience`, `player_economy.py`, target row helpers | Select remote player; set player level/spec level. |
| D-010 | "Wasn't giving selected items." | Serial delivery | P0 | open/needs multiplayer repro | `serial_rewards.py`, `backend_actions.give_serials`, BL4/bookmark/legit delivery | Deliver selected BL4 code to remote target. |
| D-011 | "Testing on my own worked fine mostly but with other players it doesn't seem to." | Multiplayer | P0 | open/systemic risk | `party_helpers.py`, target mapping, host/non-host resolution | Full MP selected/all/non-host test matrix. |
| D-012 | "You have to do each thing separately, press SDU, press spec 701, press currency..." | Grouped boost workflow | P1 | open/depends on Max All | Quick Max and auto inventory workflow | Verify MAX ALL covers expected sequence and log each result. |
| D-013 | "I've had 1 or two crashes." | Stability/logging | P1 | open/needs more data | UI threads, bridge requests, live actions | Add crash capture instructions; test bridge failures and long validators. |
| D-014 | "It starts itself up." | Launch/reopen loop | P0 | fixed but verify | duplicate `__main__` removed, BAT one-shot, SDK launcher Popen guard | Launch/close direct EXE/BAT/SDK command; verify no reopen. |
| D-015 | "Joined a lobby... external mods not activated... I was not the host... then I ranked up." | Safety/unintended leveling | P0 | likely game glitch but must audit | startup actions, queued bridge actions, XP actions | Start app offline/online and verify no live boost actions fire without clicking. |
| D-016 | "Anybody else having any trouble leveling people up with the SDK and with spawning in items with it?" | Leveling/item spawn | P0 | open/needs live repro | XP backend, item pool backend, bridge payload | Level remote player and spawn item pool as host. |
| D-017 | Request for "drop loot lobby setup" / select all codes and drop many items | New workflow request | P3 | not a bug; future feature | BL4 Codes, serial delivery, item pool spawn | Defer until delivery and item pool are stable. |

## Priority Interpretation

- P0: blocks beta confidence or risks wrong player/item effects.
- P1: important beta regression or packaging/stability issue.
- P2: parity polish.
- P3: new feature request.

## Root Cause Clusters

### Cluster A - Visible UI state vs action payload

Reports D-001 and D-008 are classic state mismatch. The external app uses `StringVar` plus `tk.Text` widgets. Some actions update only the variable and not the actual widget. This can leave visible stale text and can also risk stale payloads.

Immediate fix: audit every multiline clear path and use a shared helper that clears both `field_vars[fid]` and `widgets[fid]` when the widget is `tk.Text`.

### Cluster B - Missing BLImGui convenience workflow

Reports D-002, D-003, and D-012 are not user error. BLImGui had automatic inventory apply and a more mature fast-boost workflow. The external app currently exposes manual apply buttons but not the old automatic checkbox.

Immediate fix: restore the automatic inventory checkbox before deeper UI polish.

### Cluster C - Multiplayer target and delivery reliability

Reports D-007, D-009, D-010, D-011, and D-016 all point at live target resolution and remote-party behavior.

Immediate fix: run a multiplayer test pass with logging that includes selected index/name, host index, target mode, resolved serial count, and backend result.

### Cluster D - Packaging confidence

Reports D-004, D-005, D-006, and D-014 were largely addressed by EXE packaging, one-shot launchers, resource path fixes, and duplicate startup removal.

Immediate fix: keep packaging tests in every release checklist and update README with extraction instructions.

### Cluster E - Safety concern

Report D-015 may be a known BL4 XP/bank glitch, but the beta must prove it does not auto-run level actions on startup or reconnect.

Immediate fix: add a regression test that app launch/reconnect/status never sends live mutation actions.

## Recommended Bug Triage Order

1. D-001 Boosting clear serial widget.
2. D-008 Delete/clear serials sweep.
3. D-003 restore automatic backpack/bank checkbox.
4. D-007 Max All live test and diagnostics.
5. D-009 leveling remote players.
6. D-010 giving selected items.
7. D-016 item pool spawn and leveling confirmation.
8. D-014 app reopen regression.
9. D-004/D-005/D-006 install/launcher documentation.
10. D-013 crash reporting process.

## Regression Test Scripts To Hand To Testers

### Tester Script 1 - Serial Clear

1. Open external app.
2. Go to Boosting.
3. Paste any serial text into Serial Rewards.
4. Click Clear Serials.
5. Confirm the box is blank.
6. Click Give Selected.
7. Expected: app says no serials or no valid serials, not delivery success.

### Tester Script 2 - Multiplayer Target

1. Host a lobby with one remote player.
2. Open app and click Refresh Players.
3. Select the remote player in Target Player.
4. Click Use Selected Target.
5. Click Set Player Level or Max Player Level.
6. Expected: remote player changes; host does not.

### Tester Script 3 - Give Selected

1. Host a lobby with one remote player.
2. Select a BL4 code.
3. Set BL4 Codes Target to the remote player.
4. Click Deliver Selected.
5. Expected: remote player receives item; host does not unless selected.

### Tester Script 4 - App Launch

1. Extract beta zip into a folder.
2. Run `Launch_MSBT_External_App.bat`.
3. Close app.
4. Wait 30 seconds.
5. Expected: app stays closed.

### Tester Script 5 - Auto Inventory Once Implemented

1. Enable automatic backpack/bank checkbox.
2. Set backpack and bank sizes.
3. Have a new player join or refresh party.
4. Expected: new player receives sizes automatically and status reports count.
