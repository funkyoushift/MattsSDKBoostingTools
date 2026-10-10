# Human-oriented desktop navigation — 2026-10-09

## Request and scope

Martin reported misplaced buttons, unclear categories and difficult navigation
throughout the desktop app. Reviewed the rendered control inventory for all 17
technical tabs in workspace and Classic, then reorganized the default workspace
into 40 task destinations. Work is in C:/src/MSBT-Workspace/product on
codex/clean-workspace, based on b0d3120; public version remains 2.34.0.
The pre-existing introspection-audit notes were preserved.

## Evidenced causes and changes

- Sidebar categories and section bars exposed technical tab ownership. Selecting
  weapons, camera or currency still presented a Boosting heading and a mixed
  strip of unrelated sections. Sidebar, page titles and search now use the same
  task destinations. Removed the redundant technical section strip; legacy
  section APIs remain usable for internal navigation and regression tests.
- Home is now a directory with six categories: Character & Progression, Items &
  Loot, Combat & Survival, Movement & World, Spawning & Encounters, App & Tools.
  It has navigation only, with three prominent links per category and expandable
  remaining tools. Sidebar expands the current category. Back returns from
  target selection, shortcuts and feature search without running an action.
- Skill reset moved beside XP/levels; Max All has a separate combined-boost
  panel there. Backpack/shiny drops and legendary/epic loot spawn belong with
  ground loot. Vendors have their own page. Kill All Enemies has an encounter
  page with links to spawned-actor cleanup and wave planning.
- Third Person moved to Camera. Instant Drops/Holds moved to World & Interaction.
  Flight/noclip and dash moved beside movement settings. Movement scope remains
  visible where used; teleport instead links to its actual named-player selector.
- Survival/action-skill toggles and numeric damage/ammo/repair-kit settings have
  distinct pages within Combat & Survival, preserving their different selectors.
- Map travel/favorites, saved XYZ locations, and reveal/fog controls are separate.
  Guest-grid diagnostics are expandable. Existing source warnings are retained.
- Common boost scope and named-player selection stay visible above applicable
  actions; detailed readback, spawn location and kick are expandable. Dedicated
  Players & Targets opens the details. Spawner, pools, teleport, map diagnostics
  and camera have explicit links to the canonical target controls.
- F7 slot grid and selected-slot editor precede pin/history and optional modules.
  Inventory's experimental-character link is under Related character tools.
  Catalog, saved/community items, serial converter/validator, embedded Matt
  Editor, item pools, spawner, hoard builder, activity, pairing, reports, updates
  and credits retain their existing specialized workflows and gain coherent
  navigation homes. Embedded editor internals were not rearranged.
- Header keeps search and status prominent. App contains language, walkthroughs,
  developer portal, updates, View and layout switch. Support links remain.
  Mobile installation notice belongs on pairing; update notice on updates.
- Single-tool pages use available width; long editor panels span the grid.
  Results have bounded scrolling. Populated F7 slots reflow at narrow widths.
  New labels and search entries are English; translation coverage for new copy
  is not claimed. Classic remains available with its existing saved layouts.

## Files and behavior boundaries

`electron_poc/workspace.js`, `workspace.css`, `renderer.js`, `panel_layout.js`;
`test_workspace_navigation.js` and updated AFK test navigation selector.
Original control nodes are moved before renderer binding; action IDs, payload
implementations, input values, backend/SDK and packaged resource paths remain.
The redundant no-ID dash shortcuts from the former Essentials home are removed;
the canonical dash controls remain. Existing identified controls are compared
against Classic in the new regression test. No saved-layout migration occurs.

## Validation and useful failures

- New real-Electron, preload-free navigation suite: 40 routes, matching active
  sidebar/title after painting, every identified original control retained,
  expected control homes, Back, no duplicate IDs and zero navigation-triggered
  game actions. Populated 21-slot F7 editor and App/View menu tested at 360,
  800 and 1360 pixels. Screenshots for every destination and receipt are under
  `output/testing/workspace-navigation/` (local ignored artifacts).
- Responsive suite: 588 measurements, 12 sizes, no failures, plus enlarged text,
  bounded challenge logs and stubbed currency/XP dispatch checks.
- Feature search: both workspace and Classic pass all 14 feature routes and
  13 legacy queries. Control-clarity and farming-party targeting suites pass.
- AFK suite passes start/stop payloads, validation, edit locks and bookmarks with
  a stub transport. Walkthrough audit passes 107 targets and 12 AFK steps.
- Tab workspace guards pass 15 tabs and Inventory-to-Editor/Spawner transitions.
- Required no-BLImGui tests: 5 passed. Python AST syntax checks passed for
  backend_actions, external_bridge, quick_menu and quick_menu_registry; JavaScript
  syntax and diff whitespace checks passed. No SDK sources were edited/packaged.
- Preservation test caught View initialization assuming Updates was a direct
  header child. Fixed insertion relative to the button's actual parent.
- Small-window menu test caught a popup extending left of the viewport. Position
  now clamps to the viewport; nested View content scrolls inside the menu.
- Existing AFK test used the removed section strip. Updated it to click the real
  sidebar route. Walkthrough copy updated to explain the new homes/hotkeys.
- Initial hidden-window captures painted stale sidebar frames. Extra capture
  warm-up plus delayed active-route assertions corrected the capture evidence.
- Preload-free fixtures report unavailable transport/resources; the expected
  missing bridgeRequest startup error is excluded specifically, not all errors.
  Fixture screenshots and stub tests are not live gameplay/guest-save proof.

## Deployment, rollback and limits

Stopped only the five processes at the installed MSBT executable path, then
started `npm start` from this checkout's electron_poc. Verified source Electron
main PID 28556, a responding native window titled Borderlands 4 Modding Tools —
Powered by Funk, and version 2.34.0 startup. Startup error log is empty; catalog
log reports data-v1.1.1 unchanged (11 catalogs). Borderlands was not terminated
or restarted. This proves preview startup, not live action correctness.
No version bump, release, tag, installer, APK or SDK installation. Roll back the
preview by closing it and reopening the installed MSBT executable. Source changes
are uncommitted and limited to the listed files plus this indexed note.
Live gameplay, Epic, actual phone installation, guest-save behavior and complete
embedded-editor interactions are not newly verified by this layout work.

## Follow-up: targets, AFK handoff and hover cards

Martin reported Party & Chaos under Spawning, distant target selectors,
unclear item-to-AFK transfers and hover cards intercepting the next item.
Source confirmed targeting differed between public scoped boosts, native
single-controller shortcuts, movement scopes and session controls. AFK append
already supported saved lists and edit locking, but only catalog exposed it.
The shared hover dialog accepted pointer events even when opened passively.

- `workspace.js`: seven categories now include Party & AFK (Players, AFK,
  Party & Chaos). Original selectors remain available on Players & Targets;
  broad shared targeting panels no longer appear beside unrelated controls.
- New `workspace_targets.js`, loaded after renderer: inline selectors mirror
  existing state and action contracts, including player refresh. Movement and
  numeric combat retain only their supported scopes. Native fixed-amount game
  shortcuts have their own named-player group; they are not presented as
  public all/other-player actions. Global/local controls have explicit notes.
  `renderer.js` broadcasts target changes; `workspace.css` styles selectors.
- New `afk_item_handoff.js`: consistent pool, guaranteed and review buttons
  in catalog, saved/community items, inventory, pasted serials and converter
  output. Reuses original catalog buttons and AFK append, preserving exact
  case/order/duplicates. Invalid pasted/selected entries reject the entire
  addition; running/busy AFK rejects edits. Review opens and focuses the
  destination. Preparing a list enables the existing loot option but never
  starts AFK or delivers items. Direct delivery settings remain together above
  the AFK block in the saved-items action rail.
- `item_card_preview.js`, `styles.css`: passive hover is inert and transparent
  to pointer hit testing, including descendants/backdrop. View card promotes
  it to an interactive pinned dialog with zoom, scroll, Close and Escape.
  Polling/layout removal still closes stale cards; existing image is reused.
- `renderer.html` loads both new modules. `afk_lobby.js` and walkthrough text
  use the current route and accurate auto-enable behavior.

Offline validation: new `test_workspace_handoffs.js` passes pasted/saved/
inventory/converter handoffs, duplicate/order preservation, atomic invalid-list
rejection, running lock, exact review destination, named target bridge payload,
movement payload and synchronized selectors. Existing AFK test covers catalog
handoff and persistence. Updated card test verifies actual underlying hit target,
hover-to-pinned promotion, scrolling/zoom, focus restoration, recycled hosts,
360px bounds and one render request. Its missing screenshot output directory
was fixed with recursive mkdir; the behavioral assertions had already passed.
Navigation passes all 40 routes and retains original IDs; responsive suite
passes 588 measurements. Farming party, control clarity (both modes), search
(both modes), walkthrough (107 steps + 12 AFK steps), five no-BLImGui tests,
four Python syntax checks and diff whitespace pass. Walkthrough audit caught
missing Classic panel naming in updated help; copy now names both layouts.
Screenshots regenerated under output/testing/workspace-navigation; reviewed
levels, saved items, chaos and inventory. Transport warnings in fixture captures
come from deliberate no-preload tests, not a connected runtime result.

No backend, SDK, game installation or public version was changed. Tests stub
action transport: no live gameplay, guest-save or delivery claim is made.
Follow-up preview: stopped only source Electron PIDs 28556/13216/44060/53648,
then restarted this checkout with npm start. New main PID 38008 responds with
the expected window title. Version remains 2.34.0; stderr empty, 11 catalogs
unchanged. Logs: output/testing/workspace-navigation/followup-start*.log.
Borderlands was left running untouched. Rollback remains the installed app.
