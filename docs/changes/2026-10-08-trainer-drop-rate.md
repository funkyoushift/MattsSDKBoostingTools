# Trainer drop-rate research and opt-in MSBT control — 2026-10-08

## Request and existing behavior

Matt supplied `Borderlands 4 v1.0-v1.9.1 Plus 45 Trainer.exe` and asked to
investigate its 100% Drop Rate option and add the behavior to MSBT. Existing
MSBT rarity weights change rarity multipliers; they do not implement this
chance-roll override. This entry records source implementation and read-only
qualification, not a deployed or gameplay-verified feature.

The workspace already contained extensive unrelated modifications. Those were
preserved. No SemVer changes, installer/SDK package, installation, tag, or release
was made. The workspace SDK version is older than the loaded public SDK; replacing
the installed package with a broad workspace build would also replace unrelated
code. The active lobby and game process were left running.

## Evidence recovered from the supplied file

- Trainer SHA256: `420880557e744cddf90256a0ccceeb977a95056d6940cf434e87c62ee4fd6012`.
- Embedded author/UI strings identify FLiNG and `Shift+F6 - 100% Drop Rate`.
- The actual ASCII auto-assembler scripts begin at file offsets `0x1079a0`
  and `0x108000`. Both zero `xmm0` and skip `cvtsi2ss xmm0,ebp` when the
  `drop_rate` flag is 1, then return to the original division/comparison logic.
- These are recovered embedded instructions, not a guess based on the label.
  The trainer was never executed, loaded as a table, or injected. Its embedded
  troubleshooting text was treated as data, not followed as instructions.
- A separate `drop_rarity` script exists; it is not used for this feature.

`tools/inspect_trainer_drop_rate.py` reproduces the read-only extraction and
executable match/disassembly. Development-only dependencies are pefile/capstone;
the shipped helper does not import them. Full research receipt is retained at
`output/trainer-drop-rate/inspection.json` outside the shipping SDK source.
The trainer and its injection scripts are not bundled with MSBT. Research lead
credit to FLiNG is recorded in `docs/THIRD_PARTY_NOTICES.md`.

## Installed-game and running-process qualification

Actual Steam manifest build: **25372571**. Game EXE:
`C:/Program Files (x86)/Steam/steamapps/common/Borderlands 4/OakGame/Binaries/Win64/Borderlands4.exe`.
SHA256: `9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.
PE timestamp: `1789399121`; image size: `834191360`.

The first trainer signature matches exactly once at RVA **0x372dcf**, file
offset **0x3723cf**. The second signature has no matches in this installed EXE.
The PE runtime-function record bounds the containing function at RVA
`0x372c45..0x373424`; a symbolic function name has not been recovered.

Relevant recovered instructions:

- `0x372d48`: zero `xmm7`.
- `0x372dc9`: mask `ebp` with `0x7fff`.
- `0x372dcf`: zero `xmm0`.
- `0x372dd2`: convert `ebp` to float in `xmm0`.
- `0x372dd6`: divide `xmm0` by `xmm6`.
- `0x372dda..0x372dde`: reject values in `xmm8` that are not above zero.
- `0x372de0..0x372de4`: compare `xmm8` against the roll; branch to append
  the entry when greater than or equal to it.

The trainer replaces the roll with zero; the positive-chance filter remains.
An independently written four-byte replacement at RVA `0x372dd2` implements the
same zero result (`0f 57 c0 90`) without the trainer's allocation/trampoline.
Original bytes are `f3 0f 2a c5`. The original division and branches remain.

Fresh external **read-only** access to running PID 79136 verified the header and
the entire 54-byte context beginning at RVA `0x372dc9`. Original instructions
remain present. No game memory writes, breakpoint, debugger attachment, restart,
enemy spawn/kill, inventory mutation, or drop-rate activation was performed.
Receipt: `output/trainer-drop-rate/runtime-readonly.json`. Addresses/PID describe
this observation only; shipping code resolves its own module base each activation.

The live bridge answered `/status`, but its `game_parameters.extracted_game_build`
was the older `25234898`. The actual manifest/header/hash above govern this
qualification. The connected SDK does not yet expose the new control.

## Source changes and exact behavior

- `guaranteed_drops.py`: lazy current-process Windows APIs; exact qualified
  PE profile plus all 54 context bytes required before writing. Starts off,
  never persists. Repeated On is idempotent. Off restores original instructions
  only when the current code is owned/expected; foreign edits are never replaced.
  Readback, cache flush, page-permission restoration, rollback, and visible error
  state are included. Failed page restoration retains the original protection
  for a recovery attempt.
- `backend_actions.py`: `drop_rate_on`, `drop_rate_off`, `drop_rate_status`;
  On requires an available GameState and positively verified host authority.
  Off remains available after loss of host/world. Status includes active,
  ownership, conflict, and error state.
- `external_bridge.py`: dispatch through backend handlers and cached HTTP status;
  schema exposes On/Off for connected clients. No HTTP-thread game mutation.
- `quick_menu_registry.py`: both actions can be assigned to native F7 slots.
- `runtime_cleanup.py` and `__init__.py`: restore on travel cleanup/mod disable.
- Electron `renderer.html`/`renderer.js`: separate On/Off controls alongside rarity
  weights and bridge-authoritative status. Old SDK connections report unavailable.

Changing rarity weights or clicking Reset Rarity does not enable/disable this
separate control. The override affects this native routine process-wide while
enabled; it is not scoped to the currently selected party player. Solo/host only.

## Validation and useful failed approaches

Final validation after the page-permission recovery refinement: **47 passed**,
run in separate interpreters with `PYTHONPATH=tools;tools/tests`:

- `test_guaranteed_drops.py`: 14 passed, including the actual Windows scratch-page test.
- `test_quick_menu_no_blimgui.py`: 7 passed.
- `test_quick_menu_registry.py` + `test_quick_menu_last_command.py`: 16 passed.
- `test_bridge_status_snapshot.py` + `test_bridge_perf_bounds.py`: 10 passed.
- Python syntax checks passed for all eight new/modified Python files.
- `node --check electron_poc/renderer.js` passed. No rendered/native Electron UI
  validation is claimed.

The feature tests exercise patch ownership, repeat actions, exact restore,
unknown builds/changed code, foreign patches, rollback before/after a failed
write, lazy APIs, host authorization, Quick Menu/HTTP dispatch, cached status,
and actual Windows write/flush/restore APIs on an isolated scratch allocation.
Scratch writes are not live-game activation evidence.

The combined Quick Menu startup/registry test invocation initially exposed shared
module-stub pollution (`test_clear_page_preserves_other_pages` failed). Each suite
passes in a separate interpreter; they are verified separately below rather than
changing unrelated test harnesses. Initial test helper function-name mistakes
were corrected before the successful runs.

Parsing every PE unwind record was unnecessarily slow. The extractor now reads
only the existing RUNTIME_FUNCTION triples to obtain function boundaries; the
completed extraction takes seconds and does not execute either EXE.

## Deployment, rollback, and remaining proof

Initial state: **source only; not installed, enabled, packaged, or published.** No Electron
restart was needed because no new running panel was presented for Matt to inspect.
Versions and installed game/SDK/app artifacts remain unchanged.

Once installed, Off, travel cleanup, or disabling MSBT restores owned original
code. A game process exit also discards this memory-only change. If another tool
changes the same site, MSBT reports the conflict and refuses destructive restore.

Still required before calling this gameplay-verified: a controlled known-enemy
comparison with the option Off/On/Off, actual loot counts/identities, and travel/
mod-disable restoration in the live game. The recovered patch proves zero-roll
behavior, **not every item in every possible nested or exclusive pool**. Pool
selection, eligibility, later limits, multiplayer visibility, and save persistence
remain unverified. No all-items-per-kill or universal-build support claim is made.

## Live local farming add-on — later October 8 validation

Matt clarified that the purpose is easier farming for guests, authorized disruption
of the current lobby, and selected nearby **Splash Zone** while finding a guest.
Fresh `/status` identified the active installed MSBT as **2.31.0**, with no
`drop_rate` control before this trial. The older workspace package was not used
to replace it.

Added `work/drop-rate-trial/MSBTFarmingDrops/{__init__.py,native.py}`, a small
local add-on using a byte-identical copy of `guaranteed_drops.py`. Added a loader
and an offline integration test in that same trial directory. The add-on installs
reversible wrappers for the loaded SDK's HTTP action dispatch, F7 dispatch, and
cached status; restores wrappers only if they still belong to this add-on. It
adds On/Off to the F7 assignable catalog and supplies native Mods menu buttons
plus `msbt_drops on`, `msbt_drops off`, and `msbt_drops status` console commands.
It starts OFF and registers ClientTravel PRE cleanup before permitting activation.
Disable restores the owned patch before removing recovery controls.

Local deployment: copied the add-on folder to the verified Steam installation's
`sdk_mods/MSBTFarmingDrops/`, and loader to
`sdk_mods/msbt_farming_drops_load.py`. No existing `.sdkmod`, installed Electron
files, shipping versions, or release assets were replaced. The standalone helper
copy SHA256 is `70a1fb48535330848346c57b50811082d3c0f8467248d7f7bb591ff730d49c83`.

The control-lab transport was stale/dead, and the active HTTP bridge had no
Python-loading route. The Computer Use skill was used only to enter
`pyexec msbt_farming_drops_load.py` in the existing in-game console. Overlapping
user input was detected once; input stopped, state was refreshed, and the console
was cleared before submission. No OS terminal/UI/security action was performed.
After bootstrap, all activation checks used the SDK HTTP bridge. Console closed
with Escape and game controls returned to Matt.

Validation: Python syntax checks passed for the trial files; **14 core feature
tests plus 1 trial integration test passed**. The integration test covers wrapper
passthrough/restoration, cached status, F7 dispatch, and travel callback cleanup.
The seven required no-BLImGui regressions were also rerun successfully.

**Live On -> Off -> On passed**, with independent external read-only reads after
each SDK action at RVA `0x372dd2`:

1. Baseline: `f3 0f 2a c5`.
2. On: `0f 57 c0 90`; active/owned true, no conflict/error.
3. Off: `f3 0f 2a c5`; active/owned false, no conflict/error.
4. On again: `0f 57 c0 90`; active/owned true, no conflict/error.

Receipt: `output/trainer-drop-rate/activation-roundtrip.json`. Running PID remained
79136. `sdk_mods/settings/MSBTFarmingDrops/{state.json,history.jsonl}` records
the native add-on's actions. **Left ON for Matt's Splash Zone guest test.** This
is native activation/restoration proof; it is not yet boss-loot, guest-loot,
actual-travel, mod-disable, or guest-save proof.

Guest model: the patch affects the native routine in the hosting process and is
not per selected party member. Test with an unmodified guest before claiming
host-only deployment benefits their instanced loot. A guest hosting their own
separate lobby would need the feature on their own compatible host. Giving one
selected guest the boost while leaving others vanilla would require a different,
player-context-aware implementation; this patch does not provide that.

For the trial, use the native Mods menu entry **MSBT Farming Drops (local test)**
or the three console commands above. Travel restores the patch by design, so
re-enable after travel/reset before the next comparison. If the add-on is not
loaded after a new game session, use `pyexec msbt_farming_drops_load.py` again.
To roll back, turn it Off/disable the add-on first; with the game closed, remove
only the newly added add-on folder/loader if desired. Keep evidence/source.
No public package or release was created.

## Release integration — v2.32.0

Matt confirmed "it works" after the local farming trial and explicitly requested
integration and release, suggesting the loot rarity panel. This is user-reported
live farming success. Exact boss drop counts, individual guest observations,
exclusive-pool enumeration and guest-save persistence were not supplied and are
not claimed independently verified.

Release source starts at the published v2.31.0 tag (3bcc1bee) in the isolated
`guaranteed-drops-release/working` checkout. Only this feature, focused tests,
attribution, notes and coordinated desktop/SDK version changes were transplanted.
The extensive unrelated primary checkout edits and the later unpublished phone
navigation fix were preserved outside this release.

The production Rarity Weights panel has separate On/Off controls. They use a
host-lobby action with no selected-player or rarity-weight payload, preserve
unsaved slider drafts, and display bridge-authoritative status even when rarity
revision is unchanged. Old SDK/empty state reports unavailable, conflicts remain
visible, and presets never persist activation. Both actions are assignable in F7.
The bridge refreshes its cached snapshot on these actions before HTTP completion.

Production travel restoration uses separate ClientTravel PRE hooks enabled
independently of pawn readiness/join hooks, plus deferred cleanup as a fallback.
They restore owned bytes without reading any UObjects during teardown. Mod-disable
uses the same restoring callback. A repeat On retries pending page-protection
restoration and cannot hide a failure. These are tested offline; actual travel and
production mod-disable have not been exercised in the running lobby.

Scope: Steam build 25372571 only, guarded by PE identity and all inspected context
bytes. Epic activation is explicitly unsupported; existing Epic item cards remain.
Android 1.6.0/code33 APKs are carried forward byte-for-byte from v2.31.0; no new
phone UI or device-install evidence is claimed. Desktop and F7 expose the feature.
The running game retains the local trial helper until a normal game restart;
source/installer verification does not imply an already reloaded production SDK.

Rollback: turn Off before replacing code; previous public v2.31.0 installer/SDK
remains available. A game exit discards the memory patch. The local trial helper
starts off after a new process and is not included in public packages. A foreign
patch is never overwritten. Build/package/public verification is recorded in
`docs/releases/VERIFICATION_v2.32.0.txt`.
