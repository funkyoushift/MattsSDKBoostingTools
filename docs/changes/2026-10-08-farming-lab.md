# 2026-10-08: Local Farming Lab

## Request and isolation

Matt authorized setting up all previously proposed FLiNG candidates for local
testing, full PC control, and API-first game operation. This change does not
publish a release or change version 2.32.0. Work is isolated in
`C:/Users/mwenn/.codex/worktrees/farming-lab/working`, based on 4251178.
The dirty primary checkout and installed production desktop/SDK are preserved.

The existing controls did not expose the complete candidate set or distinguish
requested state from the game's ammo/clip locks. A separate addon now provides
13 individually reversible controls through MSBT's existing game-thread backend
dispatch, desktop Rarity panel, native Mods options, and F7 assignable actions.
The API bootstrap was completed through the SDK console after Matt authorized
computer control; subsequent game operations used the bridges.

## Source and behavioral evidence

The supplied trainer was inspected statically and was never executed.
Trainer SHA256:
`420880557e744cddf90256a0ccceeb977a95056d6940cf434e87c62ee4fd6012`.
Game: Steam build 25372571, PE timestamp 1789399121, image size 834191360,
EXE SHA256 `9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.
Read-only qualification used the current executable's exception-directory
function boundaries and disassembly, plus live SDK reflected fields/signatures.
The trainer is a research lead, not proof of gameplay or guest behavior.

- Infinite Ammo / No Reload set `OakPlayerController.InfiniteAmmoLock.bLocked`
  and `InfiniteClipLock.bLocked`; the UI also displays the actual lock state.
- Instant Reload sets owned reload behavior time values to 0.05 seconds.
  Recoil/sway and accuracy controls set the corresponding owned weapon scalar
  values to zero. Rapid Fire requests 99 shots/sec and a 0.01 positive burst delay.
- Critical Hit Boost sets `DamageCauserData.DefaultCriticalHitChance.Value` to
  the trainer's 1,000,000 amplitude. Guaranteed critical hits are unverified.
- Skill cooldown/duration call the live-qualified
  `GbxSkillComponentFunctions_ActionSkill.RefillCooldown/RefillDuration` methods
  with `(pawn, 1.0, Normal)`. Duration refill runs only with positive duration.
- Grenade cooldown sets the owned gadget's `CooldownTime.Value` to 0.1 seconds;
  an already running cooldown is not proven affected.
- Vendor refresh sets host vendors' `bShuffleCalledWhileInUse` while used.
  Live reflection confirms offset 0x2ae0, corresponding to the trainer's
  `rsi+0x1048` with rsi at object+0x1a98. Actual stock refresh remains untested.
- Glide native site RVA 0x4fb57e, function 0x4fb50c..0x4fb840, covers 16 whole
  bytes. The added predicate restricts timer writes to the local movement
  component address. It writes maximum minus 0.5, then executes the originals.
- Weighted roll native site RVA 0x3da8c3a, function 0x3da8c1e..0x3da8e0d,
  covers 17 whole bytes. It reproduces the trainer's signed bit comparison at
  `[rdi] >= 0x42b40000` and sets EAX to 0x7ffe before the original normalization.
  The original RIP-relative divisor is relocated explicitly. This routine's
  complete callers/loot scope and legendary outcome are unverified.

`tools/farming_lab/MSBTFarmingLab/profiles.py` preserves exact 64-byte contexts
and original bytes. Both native sites require PE identity, unchanged context,
and ownership checks. The code is independently authored. These experiments
do not establish worker-thread quiescence for patch installation/removal and
must not be described as production-qualified native features.

## Components and restoration

- `tools/farming_lab/MSBTFarmingLab/{__init__,engine,native,profiles}.py` and
  local pyproject: addon, game-thread pump, scoped scalar snapshots, probes,
  native ownership, backend/status/F7 integration and lifecycle cleanup.
- `tools/farming_lab/{client,qualify,verify_live_native,test_lab}.py`: expiring
  session-scoped file requests, read-only EXE research, independent live byte
  verification using a read-only process handle, and focused regressions.
- `electron_poc/renderer.html`, `renderer.js`, `test_farming_lab_ui.js`: 13
  API-driven rows under Rarity, real lock status, errors, All Off, no selected
  guest payload, and no persistence of activation.
- `tools/farming_lab/README.md`: local activation, gameplay comparisons and rollback.

Scalar snapshots retain original values and path/address identity, not live
UObjects. Restore only overwrites a field still equal to the last lab write;
expired/replaced objects or externally changed values are skipped. Failed
restoration retains its snapshot for retry. BaseValue is preserved. Native
restore refuses foreign bytes and verifies originals/protection restoration.
Code allocations remain until process exit to avoid freeing in-flight code.
Travel PRE hooks, pawn/world identity checks, All Off and addon disable request
cleanup. Completed shots/refills/generated loot cannot be reversed by Off.
Registry cleanup preserves unrelated addon entries added during the trial.

## Validation completed

Offline: Python syntax checks passed; 14 focused lab tests passed, including
snapshot restoration/conflicts, object replacement, readback failure, world
change, registry ownership, native conflicts/context checks and four x64
emulation cases for predicate/register/flags/divisor behavior. The required
Quick Menu/no-BLImGui regression suite passed (5 tests). Renderer syntax and
actual Electron test-button suites for Farming Lab and existing 100% Drop Rate
passed. Hidden renderer shutdown produced nonfatal GPU diagnostic messages.

Live game PID 5604: all 11 reflected controls completed On/Off requests and
readbacks. Both native experiments completed activation/restoration. A separate
Windows VM_READ-only observer verified original → absolute jump → identical
original bytes for both sites. Actual desktop No Reload On/Off clicks were
followed by API readbacks confirming the real clip lock changed and restored.
API lifecycle testing confirmed backend bindings disappear while disabled,
re-enable reconnects, and all 13 features start OFF. Final status: zero active
features, zero errors, no owned native patches; game remains running.

Evidence receipts in this checkout's ignored `work/`: `farming-reflected-roundtrip.json`,
`farming-native-absolute-roundtrip.json`, `farming-native-independent-readback.json`,
`farming-final-lifecycle.json`, and `farming-qualification/instructions.json`.
The research script regenerates the last receipt against the installed EXE and
the primary checkout's `output/trainer-feature-audit/extracted.json`.

Not yet proven: real firing/reload/crit effects, active skill refill behavior,
grenade reuse, sustained glide, changed vendor stock, comparative loot quality,
guest replication or guest-save persistence. Initial skill readbacks were idle
and no vendor instance was loaded. Activation is not full gameplay proof.

## Useful failures and deployment

Near rel32 allocation failed safely because no suitable nearby address range
was available; original game bytes remained intact. The final experiment uses
a 14-byte absolute indirect jump padded to the qualified 16/17-byte spans, with
separate RX code and RW data pages. Hot reload initially retained an older
backend callback; rebinding it and live disable/enable tests fixed that path.
Atomic status replacement occasionally encountered a reader's Windows sharing
lock; the pump logged it and retried next tick, without failing the game session.

Addon source/loader installed only in the game's `sdk_mods/MSBTFarmingLab` and
`sdk_mods/msbt_farming_lab_load.py`. The local desktop was restarted using
`npm start` from this worktree; Borderlands was not terminated. No SDK package,
installer, tag, public upload or SemVer change was produced.

Rollback: All Off, disable **MSBT Farming Lab (local test)**, then with game closed
remove only its folder/loader if desired. Exit source Electron and reopen the
installed production app. Keep source/receipts for further local comparisons.

## Follow-up: organization, God Mode, skill charges and glide (2026-10-08)

Matt reported that unrelated controls were crowded into Rarity, requested true
God Mode, and reported failures with long-press cooldown and glide duration.
He subsequently confirmed ammo behavior works with a different gun and asked
that investigation to stop. Ammo implementation is unchanged.

### Changes and evidence

- The 14 controls now occupy fitting sections: weapon controls in Boosting /
  Combat; God Mode, skill duration/cooldown and grenades in Party & Combat /
  Combat Tuning; glide in Movement; vendor refresh in Loot & Vendors. Only
  Weighted Loot High Roll remains in Rarity. `renderer.html`, `renderer.js`
  and `workspace.js` route the groups; shared All Off stops the entire lab.
- Added God Mode through the live character's `bCanBeDamaged=False`. Bonk
  Utilities uses the same game property. This is a game flag exposed through
  the SDK, not a newly discovered built-in SDK God Mode menu. Original flag
  state is restored with the existing ownership checks. Live True -> False ->
  True and actual desktop On/Off requests passed. Normal combat damage and
  scripted/environmental death behavior were not separately reproduced.
- The old cooldown handler refilled only the primary action-skill resource.
  Added read-only enumeration of owned action-skill charge components in
  `skill_resources.py`, then SDK `RefillCooldown` and `RefillVirtualCooldown`
  calls for validated references. No native skill state is written directly.
  Context is limited to owned scripts whose class contains ActionSkill.
- Native list layout is qualified for the same Steam build 25372571 / EXE
  SHA256 recorded above: GbxSkill TArray at +0x28, 16-byte entries, entry
  vtable RVA 0xb423b10, component pointer +0x18. Charge component vtable RVA
  0xb6379c0 / slot 1 getter RVA 0x8bae2ae, 21-byte context, and getter's cached
  ScriptStruct global RVA 0xcb9a960 must match live SDK type identity. GUID
  at component+8 is marshalled as four signed int32 fields. Reflected Charges
  and MaxCharges.Value offsets and SDK getters must agree before mutation.
  The array is bounded, foreign owners/types skipped, and mismatch fails shut.
  `work/farming-native-component-identities.json` retains getter disassembly /
  live type mapping; `work/farming-skill-charge-trial.json` records the owned
  Contagion charge 1 -> ConsumeCharges -> 0 -> new cooldown handler -> 1.
  Continuous On/Off passed with no error. Actual long-press activation/reuse
  remains unconfirmed; a question identifying the failing skill is pending.
- Replaced the ineffective glide timer hook with owned
  `VaultPowerCost_Glide.Value=0`. The old hook is disabled first and during
  cleanup. Other vault costs and BaseValue are untouched. Live Value 7.5 -> 0
  -> 7.5, BaseValue 15 unchanged, passed. Sustained gliding remains unverified.
  Combined scalar/native cleanup now preserves either failure instead of
  hiding a failed scalar restore behind successful native cleanup.
- Repair-kit cooldown already exists in Combat / Resource Tuning, in seconds,
  with Apply Once / reapply options. The current pawn has native
  HealthState.RepairKitCooldown; no duplicate control was added. Trainer's
  health-kit scripts also touch stack count; those are not equivalent to this
  existing cooldown setting and were not silently substituted.

### Validation, failures, deployment and limits

Python syntax passed. 27 tests passed: 22 lab regressions plus 5 required
Quick Menu/no-BLImGui tests. New checks cover God Mode restoration, glide cost
restoration and cleanup failure, signed charge GUIDs / attribute Value offset,
foreign owners, invalid array bounds, changed getter bytes and SDK/native
mismatch. Renderer/workspace syntax and actual Electron group/button suite
passed (nonfatal GPU shutdown diagnostics). The source desktop was restarted
without stopping BL4 and opened to Combat Tuning; screenshot verifies the new
God Mode / skill panel beside the existing repair-kit control. God Mode UI
activation was independently confirmed through the live bridge. All Off and
addon disable/enable binding cleanup passed. Current native weighted-roll
original -> jump -> original readback passed independently; the verifier now
excludes the retired glide patch.

Useful rejected approaches: do not force ammo locks false or disable unrelated
ammo perks after Matt's different-gun test. Initial charge GUID construction
used unsigned values, which the SDK's signed fields rejected. Initial raw
MaxCharges check read the attribute handle rather than Value; live reflection
proved Value is +4 and BaseValue +8, then SDK/native equality passed. Neither
failed probe changed charges. No assumptions from the failed probes remain.

Source/installed addon files are hash-compared after deployment. This remains
an isolated local test addon and source desktop; no production SDK package,
installer, public upload, tag or version bump. Rollback remains All Off and
addon disable, then close the source desktop and use the installed app.
Long-press gameplay, sustained glide, actual combat invulnerability, other
characters/builds and guest replication/save proof remain separate checks.

Final follow-up receipt: `work/farming-organized-final.json` records live PID
5604, 14 features OFF, zero errors, zero owned scalar fields, normal damage
restored, successful repeated charge depletion/refill trial and SHA256 equality
for all six installed addon source/metadata files. Final 27-test run and syntax
checks passed; desktop remains open at Combat Tuning for local testing.


## Release integration and owner confirmation

Matt requested publication and then explicitly confirmed that everything had
been tested and works, including the previously pending gameplay checks. This
is owner gameplay evidence; prior independent readbacks remain distinct. The
approved controls are integrated into SDK farming_controls, farming_definitions,
farming_native, farming_profiles and farming_skill_resources, with explicit
backend/HTTP/status/F7 routing, the existing game-thread tick, PRE-travel and
mod-disable cleanup. The release has no dependency on the separate local addon
or its file bridge, probes, monkey-patched bindings or console bootstrap.

Public version 2.33.0 and Android 1.6.1/code34 are coordinated. See
../releases/VERIFICATION_v2.33.0.txt for current packaging/public evidence.
Useful test corrections: the new PRE hook needed SDK test stubs to expose PRE
and hook decorators; cached registry functions retained an earlier fake settings
store, so each fake backend now reloads its registry. Production settings behavior
was unchanged. The 67 focused production tests and full SDK syntax passed.
