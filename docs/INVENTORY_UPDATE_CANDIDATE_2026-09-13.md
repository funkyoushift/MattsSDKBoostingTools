# Inventory update candidate

Prepared from published v2.11.3 (`92d03fb`) on `codex/inventory-update-20260913`. This is a local review build, still versioned 2.11.3. No release, tag, push or version bump has occurred. Proposed next patch: v2.11.4, subject to Matt's release approval.

## Changes prepared

- Refresh the player dropdowns when players join, leave, change slots or reconnect, including while a BL4 search/filter has focus. Retain existing option nodes and typing position. Apply a deferred selection after a focused dropdown is released. Display connection failures instead of retaining an obsolete roster.
- Inventory selections update highlights, counts and details without rebuilding item cards. Single, Ctrl/Cmd, Shift, multi-select, Select All, Clear Selection and paging retain their behavior.
- Original extracted game card layouts for weapons, shields, ordnance, repkits, enhancements and class mods, with offline calculations and saved inventory. Repeated class-mod parts contribute summed skill ranks; oversized modded lists wrap inside the card.
- Max All sends explicit player indices for all four scopes. SDK/bridge routing retains these indices; session fog runs once per batch. Only the Max All functions and two dispatch sites were ported into the release SDK. The release's existing status and tick optimizations remain intact.

## Limits to disclose

Exact card parity is still incomplete: mixed-part names, perk/red-text selection and some numeric displays remain unverified. Missing shield augment and grenade modifier-display values use a dash. Live Max All unlock completion and real multiplayer join/leave behavior were not exercised; tests use controlled inputs without gameplay mutations.

## Verification

- Player-roster integration passed in both source and packaged Electron renderer: seven real dropdowns, joins/departures/reindexing, Search/filter focus, independent inventory targets, pending target preservation, offline/reconnect periodic polling. No gameplay request was sent.
- Inventory selection integration passed with no tile mutations or iframe reloads, preserving focus and scroll. Saved-inventory tests passed.
- Native card input/naming tests, real item-card rendering and five equipment-card tests passed. The five equipment cards also resolved and painted using only the packaged ASAR/resources.
- Max All Electron click tests passed. Seven scoped Max All/bridge snapshot Python tests passed in this release tree. All 49 SDK Python modules compiled before SDK packaging.
- Existing editor browser-assets/native-lookups/save tests passed. Full editor-page integration passed when rerun alone after a timing failure under concurrent load. Existing window-state integration similarly passed on an isolated rerun after a concurrent-run failure. These reruns involved no changes to those tests or window/editor implementations.
- `npm run pack` succeeded after installing dependencies inside this worktree. The first build using a dependency junction omitted transitive packages and was replaced. Packaged `--smoke` returned `ok:true`, `packaged:true`, Electron 44.3.0. Runtime packaging excludes test scripts, fixtures and scratch files.
- Existing imported game tables were compared as parsed JSON and retained byte-for-byte from v2.11.3 where identical, preserving its provenance hashes and editor fixes.

Local unpacked build: `dist_electron/win-unpacked/MattsSDKBoostingTools.exe`. Installer/portable release artifacts must be rebuilt with approved lockstep version and manifest before publication; this review build must not be uploaded as v2.11.3.
