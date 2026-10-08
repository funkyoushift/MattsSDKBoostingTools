# Project change notes — read first

Before re-researching a feature, read its entry below and any linked component notes. Confirm the current checkout, installed artifacts and runtime before reusing conclusions. Historical notes are evidence of that run, not current proof.

## Changes

- [2026-10-08: 100% Drop Rate farming control](changes/2026-10-08-trainer-drop-rate.md) — independent guarded native zero-roll override in Rarity Weights and F7; Matt confirmed the local farming trial works and requested release. Release validation follows below.

- [2026-10-08: Combined v2.31.0 release](../docs/releases/VERIFICATION_v2.31.0.txt) — Epic cards, full Android workspace, persistent phone data, AFK phone controls and Catalog focus; release verification in progress.

- [2026-10-08: Epic card implementation evidence](native-cards/EPIC_CARD_PROFILE.md) — exact executable mappings and offline tests; Matt explicitly authorized inclusion in the normal release with live confirmation pending.

- [2026-10-08: Repeated phone status downloads](changes/2026-10-08-phone-status-data-cache.md) — unchanged large item lists cached persistently on Android; live status remains fresh. Current snapshot reduced from 1.98 MB to 18 KB after synchronization. Installed locally; no release.

- [2026-10-08: Full Windows workspace in Android](changes/2026-10-08-android-windows-workspace.md) — actual Windows workspace/editor bundled in Android; paired companion API, native files and remote transfer handling. Local builds installed; final native checks recorded in the entry. No release.

- [2026-10-08: Phone commands during AFK](changes/2026-10-08-phone-commands-during-afk.md) — remote commands and player targeting enabled; native phone selection and UVH Status confirmed while AFK remained active. Desktop/Android installed locally; no release. Includes persistent host-test error handling and separate unresolved vault readback investigation.

- [2026-10-08: Item Catalog hidden-window focus](changes/2026-10-08-catalog-hidden-window-focus.md) - reproduced Catalog focus IPC exposing a hidden frameless card renderer; fix selects the requesting panel, actual Send/Confirm/Cancel IPC regression passes. Installed locally with the Android Windows workspace change; no release.

- [2026-10-08: Wolf surface from native triangles](changes/2026-10-08-wolf-native-triangles.md) — shipped triangle asset fitted to eight original animated ear faces using 32 native pieces; vanilla guest confirmed visible and moving. Host transforms, cleanup and respawn passed. Experiment closed at Matt's request; source wolf and triangles inactive after bounded runtime cleanup, evidence retained.

- [2026-10-08: Wolf visibility for ordinary BL4 guests](changes/2026-10-08-wolf-vanilla-visibility.md) — smooth procedural wolf failed the native replication comparison; a source-driven 37-piece native wolf was confirmed visible and animated by a vanilla guest. Owned cleanup/respawn checked; exact mesh and combat remain open.

- [2026-10-08: Wolf Lab and rigging research](changes/2026-10-08-wolf-lab.md) — 41-bone CC0 wolf, 12 converted clips; corrected BL4 face winding, live showcase/cleanup/respawn verified. GitHub tools checked; combat and guest rendering remain open.

- [2026-10-08: Dragon Rider Lab](changes/2026-10-08-dragon-rider-lab.md) — supplied flying-lizard animation attached to a native enemy; host visibility and damage/death confirmed, cleanup/restart readbacks recorded. Separate local experiment; body replacement and guest visibility remain unverified.

- [2026-10-06: Password popup fix and v2.30.2 release](changes/2026-10-06-password-popup-investigation.md) - Saved Items native confirmation replaced; shared password styling and Saved Items/Item Catalog checks pass. Published with all 11 public downloads hash-verified; original white-popup reproduction remains unconfirmed.

- [2026-10-05: BL4 master reference enrichment](changes/2026-10-05-master-reference-enrichment.md) — separate recipient JSON/ZIP with synchronized indexes, extracted source definitions, 97 restored dependencies and explicit evidence limits; offline checks passed, no game/app changes.

- [2026-10-05: v2.30.1 release](C:/Users/mwenn/Documents/MSBT-Private-Provenance/Repository-Cleanup-2026-10-05/RELEASE-2.30.1.txt) — Credits tab and maintenance patch published; Android 1.5.1; 11 public downloads verified by size/SHA256. Packaged checks passed; no live gameplay or phone validation.

- [2026-10-05: Dedicated Credits tab](C:/Users/mwenn/Documents/MSBT-Private-Provenance/Repository-Cleanup-2026-10-05/CREDITS-TAB.txt) — consolidated acknowledgments and offline notices; workspace/classic Electron checks passed; pending app release.

- [2026-10-05: Second repository cleanup](C:/Users/mwenn/Documents/MSBT-Private-Provenance/Repository-Cleanup-2026-10-05/second-pass/CHANGE-RECORD.txt) — archived old screenshots and layout captures, excluded development artifacts, preserved previous SDK builds on packaging failure; 11 focused tests and local SDK build passed. No release or live test.

- [2026-10-05: Repository cleanup](C:/Users/mwenn/Documents/MSBT-Private-Provenance/Repository-Cleanup-2026-10-05/CHANGE-RECORD.txt) — removed retired panel and obsolete project files; 10 offline tests passed; published fe18ce1. Local archives retained; no release or live validation.

- [2026-10-05: Mario arcade tests](changes/2026-10-05-mario-arcade-tests.md) — single-file Mario Arcade package delivered with selector integration, portable runtime and experimental party tunnel; frozen two-emulator proxy test passed; actual two-PC BL4 transport remains unverified.

- [2026-10-04: Scooby model upgrade and crew phases](changes/2026-10-04-scooby-model-upgrade.md) — staged gang mechanics; actual model download blocked on Sketchfab sign-in; import and live proof pending.

- [2026-10-04: Arcade ROM integration discovery](changes/2026-10-04-arcade-rom-discovery.md) — installed arcade/Doom notes inspected; local NES/SNES/Genesis/N64 library found; emulator integration not yet implemented.

- [2026-10-04: Updater selected wrong game installation](changes/2026-10-04-updater-game-target.md) — local checker/updater patched; Steam repaired to bundled v2.28.0; public release unchanged.

- [2026-10-04: Large native inventory trial](changes/2026-10-04-large-native-inventory.md) — 874 slots / 818 exact serials resolved and cached; queue, artwork and tall-capture fixes in local-native-cards. Local trial only, exact visual parity unfinished.

- [2026-10-04: Concurrent manual and AFK delivery methods](changes/2026-10-04-concurrent-delivery-methods.md) — implemented in codex/concurrent-delivery-methods in the isolated afk-concurrent-release worktree; offline/renderer checks passed, not installed or published.

- [2026-10-04: AFK concurrent release v2.28.0](changes/2026-10-04-afk-concurrent-release.md) — published; all 11 public asset hashes and public installer/reinstall/rollback checks passed. Permanent concurrent guest default, exclusive cleanup/host-test safeguards, desktop per-guest progress and authoritative count.

- [2026-10-04: Concurrent AFK pacing pilot](changes/2026-10-04-afk-concurrent-pacing.md) — two overlapping live deliveries completed 500 each; both guests confirmed counts and persistence via Matt. Three-guest live validation remains open; see entry for deployment and rollback.
- [2026-10-04: AFK shows 500 but sends 70](changes/2026-10-04-afk-delivery-count.md) — confirmed stale active-state display; desktop fixed and installed locally; active SDK configuration restored to 500 with persisted authorization. Includes data flow, tests, rollback and limits.

## Existing component context

- `AFK_NEXT_WORK.md`: original random-count, guaranteed-item and password requirements; dated historical implementation notes.
- `REMOTE_AFK_PERSISTENCE.md`: bridge discovery, remote action forwarding, pairing and desktop background behavior.
- `AFK_INVENTORY_CAPTURE.md`: inventory capture evidence and limits.
- `LOCAL_FIX_QUEUE_2026-10-02.md`: historical queue, superseded in part by v2.27.0; do not treat all pending entries as current.

## Required entry for every meaningful change

Record issue/symptoms; root cause with evidence (separate unknowns); checkout and relevant version; files/components; exact behavior before/after; validation commands and outcomes; failed/rejected approaches worth preserving; deployment state and rollback; unresolved follow-ups. Link the entry here. Never include passwords, tokens or full user inventories. Keep measured evidence separate from assumptions and offline tests separate from live proof.
