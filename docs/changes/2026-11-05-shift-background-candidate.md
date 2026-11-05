# SHiFT background accepting candidate — 2026-11-05

The open SHiFT overlay captures gameplay controls, and closing or blocking it had not provided a verified continuing auto-accept path. A native visibility and lease-based companion candidate was prepared on a clean v2.40.1 baseline; the prior isolated visibility experiment reverted while the overlay was open. The candidate adds foreground and desktop controls, authenticated same-process companion routing, protected-list readiness, and a fail-closed native profile tied to Steam executable SHA-256 `ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a`. Other builds are unsupported for this path.

The SDK, companion, PAK, Electron controls, and focused tests are changed. Packaging verifies archive contents; the candidate SDK differs from the previously installed trial in only afk_lobby.py, backend_actions.py, farming_controls.py and quick_menu_registry.py, preserving the newer mission/UVHM code. Offline validation includes Python source syntax, Quick Menu/bridge import tests, background routing and lifecycle, JavaScript lease tests, remote commands and companion installer rollback. One oversized HTTP test encountered a Windows connection-aborted error in the combined run and passed alone on retry.

The candidate has not been published. Supervised trials observed incoming friend acceptance and AFK God Mode behavior as detailed below; the two acceptance trials exceeded the combined limit of one and were disclosed. A compact visible view, not a fully invisible view, has now passed a bounded Steam-profile control and polling trial. No guest-save proof is claimed. Before any promotion, reconcile later source fixes, rebuild and verify package hashes, complete the relevant live tests, and follow the release authorization and version policy. Existing installed files should be restored from their recorded backups if a separately authorized trial is rolled back.


### 2026-11-05 — sustained polling and presentation limits

The earlier fully transparent/opacity approach did not demonstrate sustained polling; a trial lost its lease after about six seconds. The CSS integration appeared incompatible with the page API, but that explanation remains a hypothesis rather than a confirmed root cause. Do not describe that approach as successfully invisible.

In the later supervised production CSS-fallback run, the background observer recorded 20 polls, 42 responses, zero errors, and zero acceptance attempts after more than 60 seconds. The subsequently read dashboard receipt (`background-readonly-r4-counts.jsonl`) reached 29 polls, 64 responses, zero errors, and zero acceptance attempts at 85.7 seconds. Martin confirmed normal walking and mouse look. A cursor or a large, stale/unscaled SHiFT panel remained visible; compact presentation was not yet qualified by this evidence. The next candidate addresses pre-entry presentation and needs its own validation.

The earlier live acceptance trials exceeded the promised limit of one acceptance across the restart: `background-accept-counts.jsonl` and `background-accept-r2-counts.jsonl` each recorded a maximum of one attempt and one resolved acceptance, for two across the two runs. This was disclosed; no identities are recorded here. The later read-only observer blocked all social mutation and recorded zero acceptance attempts. No additional social mutation is authorized by this note.


### 2026-11-05 — compact background trial and desktop handoff

In the supervised r6 Steam-profile run, the SHiFT page remained visible as a small upper-left panel (approximately 100 by 60 pixels). Martin explicitly confirmed that walking and mouse look both worked normally and the cursor disappeared. The status receipt `background-readonly-r6-status.jsonl` recorded 31 active samples from 0 through 60 seconds. The observer file named `background-readonly-r5b-counts.jsonl` was still running for r6; it had no prior r5b rows. Its r6 dashboard data reached 27 polls and 49 responses over 79.4 seconds, with zero errors and zero accept attempts. This is bounded evidence for this Steam profile and session; the view is compact and visible, not invisible.

An earlier supervised God Mode-only AFK test confirmed host invulnerability while active and restoration to damageable on Stop, with no owned fields or pending restore afterward. Two earlier acceptances across a restart exceeded the promised combined limit of one and were disclosed; subsequent read-only observation blocked social mutations. The final desktop rebuild's source and hash were verified, but its last attempted launch was rejected by automatic approval policy; earlier desktop Start/Show/Stop controls were exercised on a prior snapshot. No publication or version bump occurred in this work.


### Release preparation — v2.41.0

The feature candidate is now versioned as v2.41.0 across the Electron package, SDK metadata and update manifest. The rebuilt standalone SDK archive contains the same 156 unique files as the v2.40.1 baseline; its SHA-256 is `536ff5e06acba0ceb31b7971c4b96cf2a8388f83e37597cc9debbcfb8440069d`. Martin installed the rebuilt SDK and confirmed its hash; the game remains closed. Focused offline release checks passed. Windows and Linux release artifacts and publication checks are pending.
