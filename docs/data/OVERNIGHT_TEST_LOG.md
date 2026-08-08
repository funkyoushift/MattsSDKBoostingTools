# Overnight test log — remote data catalogs

## READY FOR MATT

Remote data catalogs + Phase 3 tutorial overlays are merge-ready on PR #11. **Also packed on this branch (2026-08-08):** Infinite Jump / Super Dash Tobgun harden (sdkmod code), hotfix-channel honesty doc, Layout Builder QM export.

- **PR:** https://github.com/funkyoushift/MattsSDKBoostingTools/pull/11 *(do not merge from automation — Matt merges)*
- **Data tag (live prerelease):** [`data-v1.0.3`](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/data-v1.0.3)
- **App SemVer:** still **2.3.1** (not bumped) — IJ/Super Dash need a **rebuilt `.sdkmod`** at Matt’s release cut
- **Movement notes:** [`docs/MOVEMENT_HOTFIX_NOTES.md`](../MOVEMENT_HOTFIX_NOTES.md)
- **Layout Builder QM:** [`docs/layout_builder/README.md`](../layout_builder/README.md)
- **Automated:** `npm run test:data-catalogs` **11/11**, `npm run check`, `npm run smoke` PASS; Python `py_compile` on movement + export script PASS
- **Matt ship steps:** merge PR → ship Electron build that includes this branch’s `remote_data_catalogs.js` → rebuild/install `.sdkmod` for IJ/SD → optional mobile APK rebuild (no `gradlew` in tree; see command below)

---

**How to test in 5 minutes (Matt, morning)**

1. Open Electron from this branch (`feature/remote-data-catalogs`) — `cd electron_poc && npm start`.
2. **Updates** tab → **Refresh Data Catalogs** (or BL4 Codes → **Refresh Catalogs**). Status should mention `data-v1.0.3` (or newer) and show updated/unchanged/failed counts + last check time.
3. Confirm **BL4 Codes** detail line also shows data version / cache counts.
4. **BL4 Codes** → **Load Catalog** — search **Raiden**; serial should be ~60 chars starting `@UgwSAs35E/...` (not a short truncated stub).
5. Open **Travel** / **Item pools** / **Dev Spawner** after a refresh — they should resolve from `userData/msbt_data/` when cached (status JSON lists sources).
6. Replay **App Walkthrough** — Welcome / Boosting / Serial Tools / Updates / Arrange layout steps should show overlay copy from `tutorial_copy.json` (Welcome still has bundled SDK download / Updates-tab links).
7. Optional: toggle airplane mode / unplug network, click Refresh Catalogs again — should soft-fail and keep last-good cache (no wipe).
8. Confirm app SemVer is still **2.3.1** (data version is separate).
9. Mobile (if APK rebuilt from this branch): Codes → **Refresh** should fetch data catalogs into `filesDir/msbt_data/` and soft-fail offline.

---

## Automated results

| When (UTC) | Check | Result |
| --- | --- | --- |
| 2026-08-08T08:33:46Z | `python tools/build_data_catalog_manifest.py --check` | PASS — 9 files, sha256+bytes match |
| 2026-08-08T08:33:46Z | `npm run check` (Electron syntax) | PASS — includes `remote_data_catalogs.js` |
| 2026-08-08T08:33:46Z | `npm run test:data-catalogs` | **5/5 PASS** |
| 2026-08-08T08:33:46Z | `npm run smoke` | PASS — appVersion 2.3.1 |
| 2026-08-08T08:33:46Z | Raiden serial in `docs/data` lootlemon seed | PASS — length 60, valid `@U…` |
| 2026-08-08T08:33:46Z | Offline bundled load (empty cache) | PASS — lootlemon 330 entries from seed |
| 2026-08-08T08:33:46Z | Simulated refresh by sha256 + offline keep-cache | PASS |
| 2026-08-08T08:40:38Z | `python tools/publish_data_release.py --bump patch --dry-run` | PASS — wrote **data-v1.0.1** (10 files, +dev_spawner) |
| 2026-08-08T08:40:38Z | `npm run check` | PASS |
| 2026-08-08T08:40:38Z | `npm run test:data-catalogs` | **8/8 PASS** |
| 2026-08-08T08:40:38Z | `npm run smoke` | PASS — appVersion 2.3.1 |
| 2026-08-08T08:40:38Z | Phase 2 cache preference (travel/maps/pools/parts/shiny/challenge/dev_spawner) | PASS |
| 2026-08-08T08:40:38Z | Hash mismatch soft-fail keeps sibling caches | PASS |
| 2026-08-08T08:40:38Z | Raiden still valid after Phase 2 rewrites | PASS — len=60 |
| 2026-08-08T08:42:00Z | `gh release create data-v1.0.1` (prerelease) | PASS — https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/data-v1.0.1 |
| 2026-08-08T08:47:24Z | `python tools/publish_data_release.py --bump patch --dry-run` | PASS — **data-v1.0.2** (10 files + tutorial_copy asset) |
| 2026-08-08T08:47:24Z | `npm run check` | PASS |
| 2026-08-08T08:47:24Z | `npm run test:data-catalogs` | **11/11 PASS** |
| 2026-08-08T08:47:24Z | `npm run smoke` | PASS — appVersion 2.3.1 |
| 2026-08-08T08:47:24Z | tutorial_copy overlay allowlist (title/body only) | PASS |
| 2026-08-08T08:47:24Z | executable `.exe` / `script` kinds rejected | PASS |
| 2026-08-08T08:48:00Z | `gh release create data-v1.0.2` (prerelease) | PASS — https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/data-v1.0.2 |
| 2026-08-08T08:49:40Z | Expanded tutorial_copy overlays (Welcome/Boosting/Serial/Updates/Layout) | PASS — indexes 0,2,3,7,9 |
| 2026-08-08T08:49:40Z | `python tools/publish_data_release.py --bump patch --create-release` | PASS — **data-v1.0.3** prerelease |
| 2026-08-08T08:49:40Z | `npm run check` | PASS |
| 2026-08-08T08:49:40Z | `npm run test:data-catalogs` | **11/11 PASS** |
| 2026-08-08T08:49:40Z | `npm run smoke` | PASS — appVersion 2.3.1 |
| 2026-08-08T08:49:40Z | Mobile APK build | **SKIPPED** — no `gradlew` / Gradle on PATH |

### `npm run test:data-catalogs` detail (latest)

```
[PASS] manifest sha256/bytes match docs/data — data-v1.0.3, 10 files
[PASS] Lootlemon Raiden serial full in seed — len=60
[PASS] offline load uses bundled seed (no cache) — lootlemon=330
[PASS] simulated refresh updates cache by sha256; offline keeps last good — data=data-v1.0.3
[PASS] getDataCatalogStatus reports bundled sources — data-v1.0.3
[PASS] Phase 2 catalogs resolve from msbt_data cache — travelstations,travelmaps,item_pools,gzo_parts_map,shiny_serials,challenge_catalog,dev_spawner_catalog
[PASS] hash mismatch fails soft without wiping sibling caches — failed=travelstations
[PASS] dev_spawner_catalog seeded in docs/data — bytes=1661775
[PASS] tutorial_copy asset + overlay allowlist — applied=10, indexes=0,2,3,7,9
[PASS] tutorial_copy refreshes into msbt_data cache — 2.3.0
[PASS] executable extensions rejected from downloadables
```

## Phase coverage

### Phase 1 — done

- `docs/data/catalog_manifest.json` + Lootlemon / custom / GZO snapshot seeds
- Electron: soft start refresh, **Refresh Catalogs** UI, cache under `userData/msbt_data/`
- Preference: cache → bundled → (GZO) live save-editor.be then GitHub
- Maintainer: `tools/build_data_catalog_manifest.py`; refresh script mirrors to `docs/data/`
- Docs: `docs/DATA_CATALOGS.md`
- App SemVer **not** bumped

### Phase 2 — solid

- Manifest **data-v1.0.1+** includes travelstations, travelmaps, item_pools, gzo_parts_map, shiny_serials, challenge_catalog, **dev_spawner_catalog**
- Electron loaders prefer `msbt_data` for all of the above
- Publish path: `tools/publish_data_release.py` (prerelease data tags so app `/latest` is untouched)
- SDK: shiny/challenge prefer Electron APPDATA `msbt_data` when present (no fetch; bridge still delivery-only)

### Phase 3 light — done this overnight

- `docs/data/tutorial_copy.json` on manifest `assets[]` (`kind: json_copy`)
- Electron downloads allowlisted assets with catalogs; renderer applies **title/body only**
- Expanded overlays: Welcome (0), Boosting (2), Serial Tools (3), Updates (7), Arrange layout (9)
- Bundled Welcome SDK links / actions remain local (overlays never ship `links` / `url` / `target`)
- `HOTFIX_CHANNEL.md` updated from sketch → implemented starter
- Publisher rejects executable kinds/extensions; Electron normalize rejects them too
- **data-v1.0.3** prerelease published

### Mobile runtime refresh — done (max practical)

- Gradle `syncMobileCatalogAssets` prefers `docs/data/` seeds (+ `catalog_manifest.json`)
- Native `filesDir/msbt_data/` cache + sha256 refresh from data-v tag URLs
- WebView intercept prefers cache over APK assets; Codes **Refresh** triggers refresh
- Soft-fail offline; no remote code / no tutorial OTA on mobile

## Mobile APK build (exact command — wrapper missing)

No `mobile_controller/gradlew` (or `gradlew.bat`) and no `gradle` on PATH in this overnight environment.

When Android SDK / Android Studio is available:

```bash
# Option A — Android Studio
# File → Open → mobile_controller/
# Build → Build Bundle(s) / APK(s) → Build APK(s)
# Debug APK lands under mobile_controller/app/build/outputs/apk/debug/

# Option B — generate wrapper once, then assemble
cd mobile_controller
gradle wrapper --gradle-version 8.7
# Windows:
.\gradlew.bat :app:assembleDebug
# macOS/Linux:
./gradlew :app:assembleDebug
```

`syncMobileCatalogAssets` runs as part of the Android asset pipeline and prefers `docs/data/` seeds (including `catalog_manifest.json` pointing at **data-v1.0.3**).

## Still TODO / follow-ups (Matt)

- Merge PR #11 so raw.githubusercontent `main/docs/data/...` also resolves
- Ship an Electron installer/build that includes this branch’s `remote_data_catalogs.js`
- Rebuild/ship a mobile APK that includes this branch’s Java/JS refresh (commands above)
- No further high-value overnight automation left without merge / installer / Android SDK

## Re-run locally

```bash
python tools/build_data_catalog_manifest.py --check
python tools/publish_data_release.py --bump patch --dry-run
cd electron_poc
npm run check
npm run test:data-catalogs
npm run smoke
```
