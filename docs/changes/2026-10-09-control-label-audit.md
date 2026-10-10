# Desktop control naming and duplicate audit — 2026-10-09

## Request, scope and source

Matt reported overlapping controls and strange labels in Weapons/Ammo and
Combat Tuning, then requested the same review across the entire app.
Changes use the current v2.34.0 source in the farming-lab worktree, branch
`codex/epic-player-farming`, base 3dd59c0. The running installed app was identified
at `AppData/Local/Programs/MSBT/app/MattsSDKBoostingTools.exe`.
No version change or public release is authorized or performed.

The audit reads the rendered desktop UI without preload or a game transport,
in both workspace and classic modes. It inventories buttons, labels, headings,
routes and their locations; current receipts are in
`work/control-label-audit/inventory.json`. The initial inventory contained 783
workspace and 808 classic entries. Final inventory contains 783 and 804.
These are controls/headings, not unique gameplay features.

## Evidenced causes and corrections

- Two ammo controls were distinct implementations with indistinguishable names.
  `dev_tools.activate_devperk(5)` calls `ServerActivateDevPerk`; its cached toggle
  state cannot establish actual state. `farming_controls.apply('infinite_ammo')`
  owns and reads `InfiniteAmmoLock.bLocked`, while No Reload owns
  `InfiniteClipLock.bLocked`. Retain both methods. The main control is now
  Infinite Reserve Ammo; Game Ammo Toggle is in a collapsed advanced section
  with explicitly unverified state and its actual target behavior explained.
- Demigod is the separate native command (perk 6); God Mode owns the character
  `bCanBeDamaged` flag. No unsupported claim about Demigod's exact protection
  is introduced. Game Demigod is advanced and unverified; God Mode remains primary.
- Gameplay rows use frontend definitions rather than stale SDK display strings.
  Fast Reload describes the actual 0.05-second setting; Fast Grenade Cooldown
  describes the 0.1-second setting. Action-skill labels specify action skills.
  Accessible On/Off names and aligned rows improve clarity at narrow widths.
- Replace generic Farming/Combat Cheats headings with Weapons & Ammo,
  Survival & Action Skills, Combat & Character Actions, and Damage, Ammo & Repair
  Kits. Show the Party & Chaos target only in its workspace section or All Controls.
  Numeric tuning and vehicle targeting explicitly identify their own selectors.
- All Off retains its existing `farming_lab {op:'off'}` route. Its visible note
  states that it affects all players and lists the affected controls. Game commands,
  100% Drop Rate and numeric tuning are separate. Status now prints real errors
  and affected players instead of merely saying to check reported errors.
- `combat_tuning.reapply_combat_tuning()` is a manual action using the previous
  numeric payload on the local character. Rename the button accordingly.
  `_sticky_enabled` is retained but no running reapply handler references it;
  hide/disable that nonfunctional checkbox and send `sticky:false`. This does
  not add an automatic reapply function or alter numeric backend behavior.
- Remove duplicated max-cash, Eridium, character and specialization buttons
  from the mixed classic grid; their existing canonical buttons remain.
- Inventory repeated four experimental character actions and incorrectly
  asserted guest character/save success, conflicting with the canonical panel's
  unverified warning. Replace those copies with navigation to the one existing
  Experimental Character Tools panel. Navigation dispatches no game action.
- AFK local and community folder buttons now name their source. Dash Now and
  Toggle Dash Hotkey (V) distinguish a one-shot dash from enabling its handler.
  Players & Targets, Give Items by Serial, Backpack & Bank Capacity and the
  Item Catalog heading use the same names as their navigation homes.
- Desktop F7 editor metadata distinguishes native commands from the new controls.
  Action IDs, assignability, custom saved slot labels and layout data are preserved.
  Old search names remain aliases. Existing duplicate cleanup/dash shortcuts,
  updater entry points and contextual selection/delivery buttons were reviewed
  and retained because their locations or selected data are meaningful.

## Components

`electron_poc/renderer.html`, `renderer.js`, `styles.css`, `workspace.js`,
`community_folders_ui.js`; new `test_control_clarity.js` and developer-only
`tools/audit_control_labels.js`, `tools/capture_control_clarity.js`.
Walkthrough expectations follow the renamed panel. The community-folder test
uses the current saved-delivery confirmation boundary instead of window.confirm.

## Verification and useful failures

- Control-clarity regression passes in both layouts: no duplicate direct action
  IDs or DOM IDs; native commands separated and unverified; authoritative display
  names; F7 metadata identity; numeric payload; appropriate target visibility;
  safe Inventory navigation and legacy search aliases.
- Farming UI and party-target suites pass: real button clicks with stubbed
  transport, On/Off, global Off, mixed/individual target readbacks, local/all/
  other/named payloads and no activation persistence.
- Feature search passes in both layouts: all 14 controls and 13 legacy queries.
- Walkthrough audit passes 107 highlighted steps and all 12 AFK workspace steps.
- Community folder UI suite passes after replacing its outdated confirmation
  stub. The original failure was `delivery` undefined because its window.confirm
  stub did not resolve the current in-app delivery confirmation. No production
  confirmation or delivery code was changed to bypass this.
- Responsive workspace passes 480 measurements across 16 tabs and 12 sizes,
  with no reported overflow. Tab workspace guards pass 15 tabs and transitions
  between Inventory, Editor and Spawner.
- Required Quick Menu/no-BLImGui suite: `python -m pytest
  tools/tests/test_quick_menu_no_blimgui.py -q`: 5 passed.
- Changed JavaScript syntax and `git diff --check` pass. SDK Python source is
  unchanged; no SDK package is rebuilt for these desktop presentation changes.
- Hidden native captures initially showed stale prior frames/boot dialogs.
  The capture tool now waits for boot completion, suppresses only fixture modals,
  and warms the hidden renderer using capturePage stayHidden/stayAwake before
  taking the final image. Images in `output/testing/control-clarity` are fixture
  UI evidence, not live gameplay evidence. Numeric targeting uses a full-width
  selector to avoid truncating its destination label.

## Deployment, rollback and limits

Local source preview was reopened through `npm start` after stopping only
the four installed MSBT desktop processes. Borderlands is not restarted or terminated.
The installed public package, SDK, Android APK, saved settings and published
v2.34.0 assets are unchanged. Rollback is to close the source Electron preview
and reopen the installed MSBT executable.

This is a complete desktop UI naming/duplicate review, including its F7 editor,
not a new gameplay, Epic, guest-save or physical-phone proof. Android standalone
UI and the native in-game F7 renderer are not installed/rebuilt in this task.
Final startup verified: source Electron main PID 38520 has the window title
Borderlands 4 Modding Tools — Powered by Funk. Startup log identifies 2.34.0
and reports data catalog data-v1.1.1 unchanged (11 catalogs); no startup error
was recorded. Final search and responsive rechecks passed, including the
full-width numeric target selector. No live game action was used for validation.

## Follow-up: controls hard to find

Matt could not find the buttons after the local preview reopened. Source review
found that `syncFarmingLabStatus` returned before constructing any feature rows
without SDK status. Thus offline search could find a feature's container, but
the actual buttons did not exist until a successful connection. This is a
confirmed source defect; it does not establish the exact live connection state
at the time of Matt's report.

All 14 controls are now constructed from frontend definitions on startup and
remain visible across disconnects. Unsupported/missing features stay disabled
with a clear connection/unavailable explanation, rather than showing a false
OFF state. Partial SDK responses disable absent features instead of leaving
stale enabled buttons. Existing connected actions/readbacks are preserved.

Boosting Quick Actions now has direct navigation buttons for Weapons & Ammo,
God Mode & Skills and Damage & Repair Kits. The Party & Combat sidebar group
starts expanded, and its links name Weapons & Ammo and God Mode & Skills.
These are navigation shortcuts and dispatch no game action. Adding the God
Mode shortcut initially changed search tie ordering for `godmode`; a direct
legacy alias now keeps the actual God Mode control first.

Both-layout regression covers visible disconnected controls, partial feature
availability, and safe navigation through all three shortcuts. Existing farming
UI and search checks pass. Preview is restarted again after these fixes; public
versions/packages and the game remain unchanged.

Follow-up validation complete: final responsive suite again passed all 480
measurements with no failures. The updated source preview was restarted;
startup reported unchanged catalogs and no recorded error.
