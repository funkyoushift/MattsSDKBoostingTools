# StreamerChaos (Vault Surge / streamer-app feed)

Standalone BL4 SDK folder mod with **only verified** streamer-chaos hooks.
Self-contained — **not** required by MSBT. Feed this folder (or a zip of it) to the Vault Surge / streamer app project.

| Effect | API |
|---|---|
| Launch | `AddImpulse` (Velocity + Z boost) |
| Drop backpack | `SpillOutItemsInContainer` + `spawnpattern_default_loot` |
| Delete backpack | `EmptyContainer` + `FGbxDefPtr("Backpack")` |
| Kill | `StartDownState(True)` |
| FFYL | `StartDownState(False)` |
| Invert look | Negate `InputYawScale` / `InputPitchScale` (timed) |
| Lock look / move | `SetIgnoreLookInput` / `SetIgnoreMoveInput` (timed) |
| Unlock | `ResetIgnore*` |

## Install (for Vault Surge / standalone testing)

Copy this folder to:

`...\Borderlands 4\sdk_mods\StreamerChaos\`

Full game restart (folder mods do not hot-reload).

## Hotkeys / console

Assignable via oak2 / mods_base options. Defaults NumPad0–9 — see `WORKING.txt`.
Console: `sc_help`, `sc_launch`, `sc_drop_backpack`, …

Hotkeys always affect the **local** player.

## Relationship to MSBT

MSBT has the **same effects built in** (`streamer_chaos.py` → Dev Tools / Quick Menu / bridge `chaos_*` actions) with **host/party targeting**. You do **not** need this StreamerChaos folder mod installed to use MSBT chaos.

If both are installed, NumPad defaults can double-fire on the local player — disable one or the other when testing.
