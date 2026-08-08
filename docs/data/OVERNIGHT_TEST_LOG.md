# Overnight test log — remote data catalogs

**How to test in 5 minutes (Matt, morning)**

1. Open Electron from this branch (`feature/remote-data-catalogs`) — `cd electron_poc && npm start`.
2. **Updates** tab → **Refresh Data Catalogs** (or BL4 Codes → **Refresh Catalogs**). Status should mention `data-v1.0.0` (or newer) and show updated/unchanged counts.
3. **BL4 Codes** → **Load Catalog** — search **Raiden**; serial should be ~60 chars starting `@UgwSAs35E/...` (not a short truncated stub).
4. Optional: toggle airplane mode / unplug network, click Refresh Catalogs again — should soft-fail and keep last-good cache (no wipe).
5. Confirm app SemVer is still **2.3.1** (data version is separate).

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

### `npm run test:data-catalogs` detail

```
[PASS] manifest sha256/bytes match docs/data — data-v1.0.0, 9 files
[PASS] Lootlemon Raiden serial full in seed — len=60
[PASS] offline load uses bundled seed (no cache) — lootlemon=330
[PASS] simulated refresh updates cache by sha256; offline keeps last good — data=data-v1.0.0
[PASS] getDataCatalogStatus reports bundled sources — data-v1.0.0
```

## Phase coverage

### Phase 1 — done

- `docs/data/catalog_manifest.json` (`data-v1.0.0`) + Lootlemon / custom / GZO snapshot seeds
- Electron: soft start refresh, **Refresh Catalogs** UI, cache under `userData/msbt_data/`
- Preference: cache → bundled → (GZO) live save-editor.be then GitHub
- Maintainer: `tools/build_data_catalog_manifest.py`; refresh script mirrors to `docs/data/`
- Docs: `docs/DATA_CATALOGS.md`
- App SemVer **not** bumped

### Phase 2 — seeded + Electron loaders wired where they exist

Manifest + seeds also include: travelstations, travelmaps, item_pools, gzo_parts_map, shiny_serials, challenge_catalog.

- Electron `readResourceJson` prefers `msbt_data` cache for travel / maps / pools / gzo_parts_map
- Shiny + challenge are hosted for data publish; SDK still packages its own copies (runtime SDK remote load = TODO if desired later)

## Still TODO / follow-ups

- Merge `feature/remote-data-catalogs` → `main` so raw.githubusercontent `main/docs/data/...` URLs resolve for packaged users
- Optionally attach `catalog_manifest.json` to a GitHub Release asset (primary URL)
- Packaged users on older builds without this code won’t refresh until they install an Electron build that includes `remote_data_catalogs.js` (data channel itself does not require a SemVer bump after that build ships once)
- SDK-side shiny/challenge hot-reload from Electron cache (optional; bridge stays delivery-only)

## Re-run locally

```bash
python tools/build_data_catalog_manifest.py --check
cd electron_poc
npm run check
npm run test:data-catalogs
npm run smoke
```
