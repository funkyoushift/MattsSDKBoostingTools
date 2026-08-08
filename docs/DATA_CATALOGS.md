# MSBT remote data catalogs

High-churn JSON (serials, travel, pools, etc.) can ship as a **data** release without bumping the public Electron/SDK SemVer (`2.x`).

## Layout

| Path | Role |
| --- | --- |
| [`docs/data/`](./data/) | GitHub-hosted catalog seeds + `catalog_manifest.json` |
| `userData/msbt_data/` | Per-user Electron cache (last-good copies) |
| `external_app/.../resources/` | Bundled offline seed (install-time) |

## Preference order (Electron)

1. **User cache** — `userData/msbt_data/<file>.json`
2. **Bundled seed** — packaged resources / `docs/data`
3. **GZO only** — live `save-editor.be` catalog API, then GitHub snapshot fallback

Offline never wipes a last-good cache. Refresh failures are soft.

## Publish a data fix (no app SemVer bump)

1. Update the JSON under `docs/data/` (or refresh sources, then mirror — see below).
2. Rebuild the manifest hashes:

```bash
python tools/build_data_catalog_manifest.py --bump patch
# or pin explicitly:
python tools/build_data_catalog_manifest.py --data-version 1.0.1
python tools/build_data_catalog_manifest.py --check
```

3. Commit + push to `main` (raw.githubusercontent URLs in the manifest point at `main/docs/data/...`).
4. Optional: attach `catalog_manifest.json` (and large JSON files if desired) to a GitHub Release so the app’s primary URL works:

   `https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/catalog_manifest.json`

   Until a release asset exists, Electron falls back to raw `main/docs/data/catalog_manifest.json`.

5. Do **not** bump `electron_poc/package.json` / SDK `__version__` for data-only fixes.

## How users refresh

- **BL4 Codes** tab → **Refresh Catalogs**, or
- **Updates** tab → **Refresh Data Catalogs**

On startup, Electron also attempts a soft background refresh.

**Refresh GZO** remains separate: it prefers live save-editor.be and writes `userData/bl4_gzo_codes.json`. GitHub’s GZO snapshot is a fallback / offline seed only.

## Maintainer refresh pipeline

`tools/refresh_matt_editor_catalogs.py` can mirror refreshed Lootlemon / GZO / parts map into `docs/data/` and rebuild the manifest (`--mirror-docs-data`, on by default when mirroring).

```bash
python tools/refresh_matt_editor_catalogs.py --skip-nexus --skip-audit
python tools/build_data_catalog_manifest.py --bump patch
```

## Bridge rule

The HTTP bridge stays **delivery-only**. Catalog scrape / GitHub fetch lives in Electron (and maintainer scripts), not in `external_bridge.py`.
