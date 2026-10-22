# Full Game safehouse capture repair — 2026-10-22

Martin reported that Abandoned Post remained locked on the map/fast-travel list after a 100% Game run. Its green command console displayed no interaction prompt. The live `mission_preview` read `ZoneActivity_Grasslands_SafehouseMain` as `completed`, but that status does not read the physical safehouse capture state. The authored console interaction belongs to an active objective, so a missing prompt after mission completion is not itself proof of the unlock defect. The map lock is the player-facing result to verify. The live PoA state has not yet been read.

The fast Full Game path completes mission records through native callbacks and preserves already-completed solo records. It does not run each authored completion action. In the installed game-data extraction, all 14 base-game `World_P` safehouses have a `states.completed.actions` entry setting their `PoA` alias `State` to `Claimed`; Abandoned Post also declares that change at its mission exit. Source: `external_app/v22_parts_codes_fixed/matt_editor/LegitItems/Nexus-Data-Mission4.json`, `/mission/records/2/entries/20/zoneactivity_grasslands_safehousemain/states/completed/actions/0` and `/exit_points/exit_point/0/1/endstates/0`. Actor identities come from the existing `mission_activity_actors.json` extraction. This shows an omitted required effect in the fast path; it does not establish the reported console's current native state.

The Abandoned Post fast-travel station `World_P.FT_GRA_BeachTower` also has the authored Recruitment Drive activation dependency; the existing travel-checkpoint repair covers that separate requirement. Its discovery entry is a child of the safehouse PoA discovery. The Full Game stage order completes missions, then map discoveries, fast-travel discoveries, and travel requirements. These are distinct unlock conditions, so the added capture reconciliation does not claim the map is fixed without a live map check. Sources: `travelstations.json`, `discovery_catalog.json`, `full_progress.py`.

`mission_effects.complete_dependencies` now checks the exact PoA State after a safehouse mission reads completed. For a loaded PoA actor it uses the native actor state machine, resolves its authored `Claimed` state by name, sets that state, and reads it back. For an unloaded actor it uses the host's live `FactsBlueprintLibrary` context to read/write the stored State address and reads that back. Earlier live evidence showed that `ReadFactForObject` could return None for a loaded PoA even when its actor state was Claimed, so the loaded path must use the actor API. The change is limited to the 14 reviewed base-game safehouses and known unclaimed states. Already-claimed states perform no write. Unknown or ambiguous states stop before mutation. Issued/returned events retain the address, channel and readback; an uncertain write stops the run without automatic replay. This is live SDK world-state work, not save-file editing or map travel. Other activities and DLC horde safehouses are untouched.

Validation: 91 focused Python checks passed, including source-to-address checks for all 14 safehouses, loaded actor and unloaded stored-fact paths, no duplicate write, unknown/ambiguous-state refusal, incomplete-mission refusal, and host context in a mixed lobby. Python syntax passed. Installed v2.39.5 and the running game were not changed; no full run, map unlock, guest saved-character check, or reload persistence has been demonstrated. The BL4 external inspector failed against this game's current resolver, so it supplied no fact readback. The read-only installed mission preview confirmed the Abandoned Post mission record as completed only.

Deployment/rollback: candidate branch `codex/safehouse-full-progress` in an isolated worktree from v2.39.5. A local `.sdkmod` package was built and its ZIP integrity checked. The change was later integrated into the Steam 26007962 compatibility branch, with a byte-for-byte backup of the previous locally installed SDK package retained outside Git. No release has yet been published.

Steam 26007962 live follow-up: the authorized test character and profile were
backed up before a targeted solo check. The Abandoned Post mission read
completed. A named completion job reached completed; its journal reported
that the loaded PoA actor's State was already `Claimed`, so the repair issued
**no** state write. The safehouse discovery and its child fast-travel discovery
both read `2` (already discovered), and the authored Beach Tower travel
requirement read `Completed`; those targeted jobs also issued no write.
Martin then saw Abandoned Post unlocked in the map/fast-travel list, and it
remained unlocked after normal Save/Quit and reload. This confirms the current
player-facing state but does not establish that the repair caused it. No fast
Full Game run, unclaimed PoA write, or visitor-save result was tested. The
game was closed after this check.
