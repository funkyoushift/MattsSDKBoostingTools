# Overnight test log — remote data catalogs

**How to test in 5 minutes (Matt, morning)**

1. Open Electron from this branch (`feature/remote-data-catalogs`) — `cd electron_poc && npm start`.
2. **Updates** tab → **Refresh Data Catalogs** (or BL4 Codes → **Refresh Catalogs**). Status should mention `data-v1.0.1` (or newer) and show updated/unchanged/failed counts + last check time.
3. Confirm **BL4 Codes** detail line also shows data version / cache counts.
4. **BL4 Codes** → **Load Catalog** — search **Raiden**; serial should be ~60 chars starting `@UgwSAs35E/...` (not a short truncated stub).
5. Open **Travel** / **Item pools** / **Dev Spawner** after a refresh — they should resolve from `userData/msbt_data/` when cached (status JSON lists sources).
6. Optional: toggle airplane mode / unplug network, click Refresh Catalogs again — should soft-fail and keep last-good cache (no wipe).
7. Confirm app SemVer is still **2.3.1** (data version is separate).

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

### `npm run test:data-catalogs` detail (latest)

```
[PASS] manifest sha256/bytes match docs/data — data-v1.0.1, 10 files
[PASS] Lootlemon Raiden serial full in seed — len=60
[PASS] offline load uses bundled seed (no cache) — lootlemon=330
[PASS] simulated refresh updates cache by sha256; offline keeps last good — data=data-v1.0.1
[PASS] getDataCatalogStatus reports bundled sources — data-v1.0.1
[PASS] Phase 2 catalogs resolve from msbt_data cache — travelstations,travelmaps,item_pools,gzo_parts_map,shiny_serials,challenge_catalog,dev_spawner_catalog
[PASS] hash mismatch fails soft without wiping sibling caches — failed=travelstations
[PASS] dev_spawner_catalog seeded in docs/data — bytes=1661775
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

- Manifest **data-v1.0.1** includes travelstations, travelmaps, item_pools, gzo_parts_map, shiny_serials, challenge_catalog, **dev_spawner_catalog**
- Electron loaders prefer `msbt_data` for all of the above (`readResourceJson`, `readDevSpawnerCatalog`, BL4 catalog map)
- Stronger UX: version + last check + updated/unchanged/failed on Updates + BL4; progress events; retries; refresh_state.json
- Publish path: `tools/publish_data_release.py` (prerelease data tags so app `/latest` is untouched)
- SDK: shiny/challenge prefer Electron APPDATA `msbt_data` when present (no fetch; bridge still delivery-only)
- Phase 3 sketch: `docs/HOTFIX_CHANNEL.md`

## Still TODO / follow-ups

- Merge PR so raw.githubusercontent `main/docs/data/...` also resolves
- Mobile runtime manifest fetch (documented only for now)
- Optional `tutorial_copy.json` hotfix pack (Phase 3)
- Packaged users need an Electron build that includes this branch’s `remote_data_catalogs.js` before remote refresh works on their machines

## Re-run locally

```bash
python tools/build_data_catalog_manifest.py --check
python tools/publish_data_release.py --bump patch --dry-run
cd electron_poc
npm run check
npm run test:data-catalogs
npm run smoke
```
