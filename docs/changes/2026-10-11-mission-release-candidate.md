# Mission completion release candidate

Based on published v2.35.2; only mission-specific modules, routes, desktop controls
and tests integrated. Guest persistence confirmed by Martin for Rev and Bubbah
following the 200-mission run. Two unavailable definitions display separately;
three nonpersistent replayable entries excluded. Unsupported objective/undo/full
reset controls remain disabled. Map/station coverage has separate proof boundaries.

Validation: 35 focused Python checks, release SDK import test, JS coverage/step
checks, 41-route Electron navigation with zero game actions, offline SDK installation,
packaged dependency graph and packaged asset hashes. See mission-build-verification.json.
Initial build using a shared dependency junction omitted transitive libraries.
Resolved with a local npm ci and rebuilt; no dependency versions changed. Copied
vendor resources at their required roots; nested staging copy retained outside the
packaged app. Local worktree helper junction/copy are not source changes.

No public version bump, tag, upload or publication. Current candidate metadata is
2.35.2 for local validation only, not a replacement public release. New user-facing
mission capability calls for a minor release when explicitly authorized. Public
installer/portable packaging follows lockstep versioning. Preserve the active
product checkout and running discovery job. Rollback UI/code through published
version; completed gameplay progress is not undone by replacing the package.


## 2026-10-11 - Station claim gaps
Abandoned Post screenshot shows Claim Safehouse to unlock Fast Travel. Source audit: 82 fast_travel definitions, 53 with dependencies; 81 match discovery catalog records. Unmatched Raid2_P.BRP_Raid2_Exit is not proven to be a player destination. Receipt: ../local/mission-review-2026-10-11/station-coverage-audit.json. Source coverage is not live usability.
Added six source-exact positive checkpoint repairs covering Abandoned Post, Demonhold, Grey Havenage, Heritage Opus, Covered Charge, The Reliquary, Final Defiance, The Lockaway and Carcadia. Previously missing in product travel_checkpoints.json. Existing unique completed ordinary parent and None-to-Completed guards remain. Alternate/negative branches excluded; objective and alternate-route requirements remain unresolved.
Changed product/lab travel_checkpoints.json and test_mission_discovery.py; synchronized release worktree source. 27 offline discovery/full-run/startup checks and syntax passed. No new game mutations, package rebuild, installation or guest travel validation. Existing built candidate is stale for these repairs. Universal travel remains unverified. Rollback: remove six new named checkpoint entries; no runtime change to undo.


## Authorized v2.36.0 release
Martin explicitly requested publication. New user-facing mission capability advances Windows/SDK to 2.36.0 in lockstep; Android stays 1.6.2. Six new travel repairs included; installed review package live preview showed all 19 eligible requirements. Usable travel and guest-save proof for the added repairs remain unverified and are stated in public notes. 54 focused mission/discovery/startup/release-preflight checks plus isolated backend import passed. Initial Windows check caught a metadata encoding error introduced during versioning; original UTF-8 product identity restored and test passed. Full installer/portable build and publication checks in progress. No change to the running game or active product checkout.

Full Windows checks, installer/portable build, executable smoke and updater checks passed. Packaged dependency graph:48 packages; packaged assets:3258 matching hashes. Public upload pending; all ten deliverable hashes recorded in SHA256SUMS.txt.


### Published v2.36.0
Martin explicitly authorized release. Published latest stable v2.36.0 from isolated codex/missions-release-2.36.0, tag commit 6e643cec96f2c3702b90a917bc474025d7f441ee. Windows/SDK lockstep2.36.0; Android unchanged1.6.2. All11 GitHub asset digests matched local artifacts; unauthenticated latest/download/latest.json matched packaged bytes and2.36.0. Full Windows checks/build/smoke/updater passed;54 focused checks plus isolated import passed;48 packaged dependencies and3258 asset hashes passed. Six additional travel repairs included with honest unverified usable-travel/guest-save limitations. Known unavailable and unsupported objective/undo/reset controls disclosed. Release URL: https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/v2.36.0 . Running game and active app not restarted or replaced during publication.


## 2026-10-11 - Mission recovery and DLC access review
Implemented mission_recover and mission_dlc_status, desktop recovery/close/access controls, and source-mapped DLC checks before reset/accept/complete. Uses GbxAttributeBlueprintLibrary.GetValueOfAttributeAsInteger with each player controller and separate session attributes; shared entitlement facts returned identical FALSE and were rejected as per-player evidence. Source Nexus attribute/resident/mission hashes retained in mission_dlc_catalog.json (52 missions,9 packs). Never writes entitlement data or kicks players. Unknown access defers content without blaming a player. Deferred work is not counted as verified completion.
Recovery requires a durable returned call, settled matching mission identity and current state. Unchanged acceptance is deferred without retry; forward activation/completion can continue. Explicit close reconciles the receipt and permits a new job, including after restart; missing return or unresolved completion remains blocked. Changed parties require explicit recovery and fresh selected-player resolution.
49 offline tests and JS stop checks passed;41 page routes with zero game actions passed. Installed review SDK SHA2562d379e56e79a375eda1b8f2209eedd64146b5df9c02b7fad1a6c70422c38c9b0, version unchanged2.36.0, not published. Live read-only recovery of29109cbdc115401cbaaa7e469e168d4d confirmed An Invitation available;20 prior completions preserved and job still uncertain. Current live report identified Parzival_7 lacking Cowbell access. Earlier Criptyc_Gamer snapshot differed from later Criptyc; reports must always use fresh lobby identity. Native recovery continuation/skip batch remains untested.
First UI refresh was interrupted by user Escape; user then explicitly resumed. Closed only old desktop and launched updated isolated release-worktree source panel. Public v2.36.0 assets/tag unchanged; pending fixes require separate release authorization.
