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

```powershell
# Local package + Steam copy (test only):
.\tools\build_sdkmod.ps1
.\tools\sync_test_sdkmods.ps1 -BuildSdkMod
```

## Smoke checklist

### 1. XYZ location bookmarks (Map Travel)

- [ ] Open **Map Travel** → **XYZ Location Bookmarks**
- [ ] Stand somewhere → name it → **Save Here**
- [ ] Move away → select bookmark → **Go Selected**
- [ ] Confirm teleport works without map travel
- [ ] **Delete Selected** removes the entry

### 2. Dev Spawner UX (Compact vs Panels)

- [ ] Header toggle **Compact | Panels** persists in `localStorage` key `msbt.devSpawner.layoutMode` (`fixed` / `docked`)
- [ ] **Compact** (default): fixed Squ1ggs-inspired composition — no GridStack toolbar; status strip + favorite strip + one actor list + right spawn controls
- [ ] **Panels**: multi-card GridStack with Search / Boss / Favorites / Characters / Details / Result + Standard Spawning / Setup / Barrel
- [ ] Shared widgets keep unique IDs (reparented between shells — no duplicate `id=`s)
- [ ] Compact: Boss chip filters the same list; Panels: Boss / My Favorites lists fill their own cards
- [ ] Spawn / Clear / favorites store still work in both modes (ASD_spawnai backend)
- [ ] Walkthrough covers Compact pick→spawn and mentions Panels mode
- [ ] Other tabs still have docking unchanged

### 3. Movement scope

- [ ] Player Movement → scope **Local / All / Others**
- [ ] Apply movement; verify only intended players change
- [ ] **Infinite Jump** + **Super Dash** still behave as before (Tobgun-hardened paths untouched)

### 4. P2P teleport

- [ ] Movement → **Selected → Me** / **Me → Selected** / **All → Me**
- [ ] Existing **To P1–P4** slot teleports still work
- [ ] QM can pin the new teleport actions

### 5. Dev Tools tab (WIP — hidden by default)

**Do not publish until Squ1ggs conversation (combat resource tuning) and vehicle data/credits are cleared.** No release until Matt says.

Unlock gate:

- [ ] Tab id remains `combat-vehicle` (WIP unlock storage still works)
- [ ] Nav label reads **Dev Tools**; tab is **hidden** in the main bar by default
- [ ] Normal **View** menu does **not** list it under Main tabs
- [ ] **Shift+click View** → **Development tabs** → enable **Dev Tools (WIP)**

#### Combat

- [ ] Description notes Squ1ggs-inspired Oak damage/ammo/repair tuning + ask before publishing
- [ ] Curated sliders: damage dealt/taken, repair kit, ammo regen
- [ ] **Apply Once** (sticky checkbox stays **off** unless you opt in)
- [ ] After travel, **Reapply After Travel** restores last values

#### Vehicle

- [ ] Description credits **mattmab** presets; catalog seeded for local test (unlock tokens / Proto / verified)
- [ ] Vehicle presets apply while in/near a vehicle
- [ ] Catalog option text shows unlock / unreleased flags
- [ ] Spawn Selected Vehicle best-effort unlocks then summons (host/solo most reliable)

#### Challenges (Boosting Essentials, under UVH — Phase 1)

- [ ] Challenges live on **Boosting** next to UVH 1–7 (not Dev Tools, no “(WIP)”)
- [ ] Category select + search filters the list (`challenge_catalog_list`)
- [ ] **Complete All / Category / Selected** show an explicit confirm dialog (save warning). No 10s double-press.
- [ ] Progress strip `#challengeBulkPanel` shows `done/total`, ok, fail while the queue runs
- [ ] **Cancel** stops a running queue
- [ ] Complete All grants full catalog amounts (chunk 250 only if the native RPC rejects the full value)
- [ ] After the queue, challenge UI state is maxed for **granted** tokens (not UVHM)
- [ ] Join client is refused with a host/listen error
- [ ] F7 Quick Menu can pin **Complete All Challenges** / **Cancel Challenges**

## Partial / skipped

| Item | Status |
|------|--------|
| IO / world-prop picker | **Skipped** this pass (time) — ASD template/Lost Loot still available |
| Full SQBT aggro fidelity | **Partial** — thin SetEnemy/focus reaggro, not full combat-wake matrix |
| Vehicle spawn unlock/discovery | **Partial** — full 15-row catalog + best-effort unlock RPC; not full offline mesh scan |
| Sticky combat tick hooks | **Intentionally off** by default (apply-once + manual reapply) |

## Reminder for Matt

Test on this branch first. When happy, say the word to push / bump / release — agents will not ship until you ask.
