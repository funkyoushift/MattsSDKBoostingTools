# Movement hotfix notes (Infinite Jump + Super Dash)

Date: 2026-08-08  
Branch: `feature/remote-data-catalogs`  
Based on Discord analysis from Tobgun1 (FPS + ACCESS_VIOLATION).

## What changed

### Infinite Jump (lag)
- Camera tick still runs often (`~0.04s`) but **writes only when needed** (`JumpCurrentCount > 0` or `JumpMaxCount < 999`).
- Heavy `find_all` party/pawn discovery is throttled to **~1.5s** (or immediately on world/controller/pawn/player-state address change).
- Between heavy scans, IJ reacquires the **local pawn via `get_pc()` only**.
- Jump / CanJump hooks still do a full prep when the player actually jumps.

### Infinite Jump (crashes)
- Do **not** cache live UObject wrappers across ticks (`_jump_cache` / context caches).
- Liveness uses `_get_address()` only — never `.Name` / `.Class` on possibly-stale pointers.
- Clear IJ runtime caches on disable and when world identity changes.
- BLImGui duplicate IJ path aligned with the same rules (Electron/QM uses `movement_adjustments.py`).

### Super Dash
- No background `Thread` for UE work (already removed earlier; kept on camera tick).
- Bridge/HTTP callers **queue** a dash; impulse + delayed `StopJumping` run on the game-thread camera hook.
- Cooldown prevents command stacking spam.

## In-game test steps (Matt)

1. Install/rebuild this branch’s `.sdkmod` into `sdk_mods` (Updates → Install / Update SDK Mod, or copy packaged mod). **Fully restart BL4.**
2. Load into a character as listen host.
3. **Infinite Jump**
   - Note FPS with IJ OFF (rough baseline).
   - Enable IJ (Electron Player Movement or QM / BLImGui).
   - Hold jump / spam jump in air — should keep jumping.
   - FPS with IJ ON should be much closer to OFF than the old ~76 vs ~122 gap.
   - Travel to another map / die+respawn / reload save with IJ still ON — should not ACCESS_VIOLATE; IJ should keep working after reacquire.
4. **Super Dash**
   - Enable MSBT Super Dash; press **V** — impulse on game thread, no crash.
   - Enable Azzy Super Dash; press **NumPad0**.
   - Spam the key / queue from Electron repeatedly — cooldown should prevent stacking crashes.
5. Optional: disable IJ and confirm no leftover per-tick work (FPS returns).

Reference fork for Squ1ggs patterns (not vendored): https://github.com/funkyoushift/Bl4SDKmods — their movement path also uses `_get_address` for live pawn identity rather than Name/Class probes.

