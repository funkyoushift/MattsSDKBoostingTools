# Movement hotfix notes (Infinite Jump + Super Dash)

Date: 2026-08-08  
Release: **v2.3.3** (follows v2.3.2 harden)

## What changed in 2.3.3 (FPS follow-up)

Matt still saw frame drops after 2.3.2. Root cause in the Electron/QM path:
camera ticks still entered `_force_infinite_jump_ready` every light interval
(move resolve + attr probes) even when jump counters were already idle.

### Infinite Jump (further lag cut)
- Camera interval **0.04s → 0.1s** (~10 Hz checks).
- Heavy `find_all` party scan **1.5s → 3.0s** (still immediate on world/controller/pawn change).
- **Read cheapest signal first:** `JumpCurrentCount` / `JumpMaxCount` / `JumpCurrentCountPreJump` — skip all writes and move-component resolve when idle.
- Solo/local-enabled path avoids party `PlayerArray` walks after local index is cached.
- Jump pre-hook no longer calls `live_player_pawns()` (`find_all`) as a fallback.
- Hot path uses address-only liveness (no per-tick `str(obj)` CDO probes).
- BLImGui duplicate camera hook aligned (0.1s + local-first idle skip). Jump/CanJump full prep unchanged so IJ still works (camera clears kept).

### Still true from 2.3.2
- Do **not** cache live UObject wrappers across ticks.
- Super Dash stays on the game-thread camera hook (no background `Thread`).

## In-game test steps (Matt)

1. Install **v2.3.3** `.sdkmod` (Updates → Install / Update SDK Mod, or copy packaged mod). **Fully restart BL4.**
2. Load into a character as listen host.
3. **Infinite Jump**
   - Note FPS with IJ OFF (baseline).
   - Enable IJ (Electron Player Movement or QM). Leave character standing / walking — FPS should stay close to OFF (idle path should not spam UE writes).
   - Hold jump / spam jump in air — should keep jumping.
   - Travel / die+respawn / reload with IJ ON — no ACCESS_VIOLATION; IJ keeps working.
4. **Super Dash** (smoke): MSBT **V** and Azzy **NumPad0** still fire on camera tick.
5. Optional: disable IJ and confirm FPS returns to baseline.

Reference fork patterns: https://github.com/funkyoushift/Bl4SDKmods (address-based liveness; no Name/Class probes on hot paths).
