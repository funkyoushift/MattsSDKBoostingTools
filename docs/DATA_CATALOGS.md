# MSBT remote data catalogs

High-churn JSON (serials, travel, pools, etc.) can ship as a **data** release without bumping the public Electron/SDK SemVer (`2.x`).

## Layout

| Path | Role |
| --- | --- |
| [`docs/data/`](./data/) | GitHub-hosted catalog seeds + `catalog_manifest.json` |
| `userData/msbt_data/` | Per-user Electron cache (last-good copies) |
| `external_app/.../resources/` | Bundled offline seed (install-time) |
| `electron_poc/dev_spawner_catalog.json` | Bundled Dev Spawner seed (also mirrored into `docs/data/`) |

## Preference order (Electron)

1. **User cache** — `userData/msbt_data/<file>.json`
2. **Bundled seed** — packaged resources / `docs/data` / Electron app dir (Dev Spawner)
3. **GZO only** — live `save-editor.be` catalog API, then GitHub snapshot fallback

Offline never wipes a last-good cache. Refresh failures are soft (partial success keeps good files; hash mismatches retry then skip that file).

## Phase 2 catalogs (loaded from cache when present)

| id | Consumer |
| --- | --- |
| lootlemon / custom_bl4_codes / gzo_codes | BL4 Codes tab |
| travelstations / travelmaps | Travel UI (`readResourceJson`) |
| item_pools | Item pool spawn UI |
| gzo_parts_map | Parts labels |
| shiny_serials / challenge_catalog | Hosted for publish; SDK prefers Electron `msbt_data` cache if discoverable, else packaged seed |
| dev_spawner_catalog | Dev Spawner (`readDevSpawnerCatalog`) |

## Publish a data fix (no app SemVer bump)

```bash
# Rebuild hashes + bump data SemVer
python tools/publish_data_release.py --bump patch --dry-run

# Or create a real GitHub data-vX release (requires gh auth)
python tools/publish_data_release.py --bump patch --create-release
```

Lower-level:

```bash
python tools/build_data_catalog_manifest.py --bump patch
python tools/build_data_catalog_manifest.py --check
```

Do **not** bump `electron_poc/package.json` / SDK `__version__` for data-only fixes.

URLs:

- Release asset (preferred when published): `…/releases/download/data-vX.Y.Z/catalog_manifest.json`
- Durable fallback: `raw.githubusercontent.com/.../main/docs/data/catalog_manifest.json`

Until `main` contains `docs/data/`, packaged clients still use the release asset + local bundled seeds.

## How users refresh

- **BL4 Codes** → **Refresh Catalogs**, or
- **Updates** → **Refresh Data Catalogs**

Status lines show **data version**, **last check time**, and **updated / unchanged / failed** counts. Startup runs a quiet auto-check and updates those lines when finished.

**Refresh GZO** remains separate (live save-editor.be → `userData/bl4_gzo_codes.json`).

## Maintainer refresh pipeline

```bash
python tools/refresh_matt_editor_catalogs.py --skip-nexus --skip-audit
python tools/publish_data_release.py --bump patch --create-release
```

## SDK / bridge

- HTTP bridge stays **delivery-only** (no catalog scrape in `external_bridge.py`, no blimgui import).
- `backend_actions` may **read** Electron's `APPDATA/.../msbt_data/` for shiny/challenge when present; it never fetches.
- Override cache dir with env `MSBT_DATA_CACHE`.

## Mobile

Mobile controller can refresh catalog JSON at runtime:

1. APK build syncs seeds from `docs/data/` (fallback: packaged resources) including `catalog_manifest.json`.
2. Codes → **Refresh** fetches the data-channel `catalog_manifest.json` (data-v tag URLs), verifies sha256, and writes into app `filesDir/msbt_data/`.
3. WebView asset loads prefer cache over APK bundled seeds.
4. Offline / failed refresh soft-fails and never wipes last-good cache.

Mobile does **not** load remote tutorial copy or any executable payloads.

## Phase 3

See [`HOTFIX_CHANNEL.md`](./HOTFIX_CHANNEL.md). `tutorial_copy.json` ships on the data manifest `assets[]` list; Electron applies title/body overlays only.
