# SQBT-inspired QoL — local test notes (not released)

Branch: `feature/sqbt-inspired-qol`  
**Nothing was pushed to origin. SemVer was not bumped. No GitHub Release.**

Inspired by Squ1ggs / Bl4SDKmods SQBT patterns (MIT modules reimplemented; challenge confirm is behavior-only — no GPL `challenge_ticker` imports).

## How to run locally

### Electron

```powershell
cd C:\Users\mwenn\Desktop\MSBT_Codex_Work\working\electron_poc
npm start
```

### SDK

Copy/rebuild the mod package into your `sdk_mods` folder from:

`mod_extracted/MattsSDKBoostingTools/`

(or your usual local `.sdkmod` packaging script). Do **not** publish.

Optional Steam path if you use it:

`c:\Program Files (x86)\Steam\steamapps\common\Borderlands 4\sdk_mods\`

## Smoke checklist

### 1. XYZ location bookmarks (Map Travel)

- [ ] Open **Map Travel** → **XYZ Location Bookmarks**
- [ ] Stand somewhere → name it → **Save Here**
- [ ] Move away → select bookmark → **Go Selected**
- [ ] Confirm teleport works without map travel
- [ ] **Delete Selected** removes the entry

### 2. Dev Spawner UX (fixed composition — no GridStack on this tab)

- [ ] Tab is **one fixed layout** (no Compact/Reset/Panels dock toolbar)
- [ ] Top **status strip**: warning + ASD autoclear timer + expandable **Last result**
- [ ] **Favorite strip** spawn-on-click; ☆/★ on actor rows; no My Favorites list column
- [ ] Left: search + chips (**Boss** / ★ Favorites / All / …) + **one** actor list + selection/spawn
- [ ] Right: aggro/anchor/dist/count + Spawn/Re-Aggro/Clear; Setup/Barrel/Advanced collapsed
- [ ] Boss chip filters the same list (not a second list)
- [ ] Spawn / Clear / favorites store still work (ASD_spawnai backend)
- [ ] Walkthrough copy matches pick→spawn (no “stack panels” tip)
- [ ] Other tabs still have docking unchanged

### 3. Movement scope

- [ ] Player Movement → scope **Local / All / Others**
- [ ] Apply movement; verify only intended players change
- [ ] **Infinite Jump** + **Super Dash** still behave as before (Tobgun-hardened paths untouched)

### 4. P2P teleport

- [ ] Movement → **Selected → Me** / **Me → Selected** / **All → Me**
- [ ] Existing **To P1–P4** slot teleports still work
- [ ] QM can pin the new teleport actions

### 5. Combat / Vehicle tab

- [ ] Curated sliders: damage dealt/taken, repair kit, ammo regen
- [ ] **Apply Once** (sticky checkbox stays **off** unless you opt in)
- [ ] After travel, **Reapply After Travel** restores last values
- [ ] Vehicle presets apply while in/near a vehicle
- [ ] Vehicle catalog spawn requests a personal vehicle (host/solo most reliable)

### 6. Challenge confirm

- [ ] First `complete_challenges_all` arms a 10s confirm (does not start yet)
- [ ] Second press within 10s starts the queue
- [ ] Changing party/target cancels pending confirm

## Partial / skipped

| Item | Status |
|------|--------|
| IO / world-prop picker | **Skipped** this pass (time) — ASD template/Lost Loot still available |
| Full SQBT aggro fidelity | **Partial** — thin SetEnemy/focus reaggro, not full combat-wake matrix |
| Vehicle spawn unlock/discovery | **Partial** — curated catalog + RPC summon, not full offline mesh scan |
| Sticky combat tick hooks | **Intentionally off** by default (apply-once + manual reapply) |

## Reminder for Matt

Test on this branch first. When happy, say the word to push / bump / release — agents will not ship until you ask.
