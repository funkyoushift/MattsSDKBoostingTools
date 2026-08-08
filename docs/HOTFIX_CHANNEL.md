# Hotfix channel (Phase 3 sketch)

Goal: ship **copy / tutorial / JSON-only** asset packs without a full Electron installer or SDK SemVer bump, using the same trust model as remote data catalogs.

## Non-negotiables

- **No remote code execution.** No downloading `.js`, `.py`, `.exe`, `.dll`, `.sdkmod`, or any executable payload into a load path.
- **Allowlisted asset types only:** JSON, Markdown/plain text tutorial copy, static images already referenced by the app (optional later).
- **`min_app_version` gates:** packs that require newer UI/schema are ignored by older builds.
- **Offline last-good:** never wipe a working local pack on a failed refresh.
- Bridge stays **delivery-only** (no blimgui import; no remote fetch inside `external_bridge.py`).

## Proposed layout

Extend `catalog_manifest.json` (or a sibling `hotfix_manifest.json`) with an `assets` / `packs` array:

```json
{
  "id": "tutorial_copy",
  "path": "tutorial_copy.json",
  "kind": "json_copy",
  "sha256": "...",
  "bytes": 1234,
  "min_app_version": "2.3.0",
  "url": "https://raw.githubusercontent.com/.../docs/data/tutorial_copy.json"
}
```

Allowed `kind` values (v1):

| kind | Consumer | Notes |
| --- | --- | --- |
| `catalog_json` | Electron + optional SDK cache read | Already shipped as Phase 1/2 data files |
| `json_copy` | Electron UI strings / walkthrough tips | Optional; ignore unknown keys |
| `markdown_doc` | In-app help panes | Optional; render as text only |

Rejected always: `script`, `native`, `sdkmod`, `archive_exec`, anything with an executable extension.

## Electron flow

1. Fetch manifest (release asset → raw main fallback), same as data catalogs.
2. Filter packs by `min_app_version` vs local `app.getVersion()`.
3. Download changed sha256 into `userData/msbt_data/` (or `userData/msbt_hotfix/`).
4. UI reads copy JSON if present; otherwise bundled defaults.

## What this is not

- Not an auto-updater replacement for Electron/SDK binaries.
- Not a vehicle for UE hooks, console commands lists that execute arbitrary strings from remote, or plugin sideloads.
- Not a mobile code OTA channel.

## Cheap Phase 3 starter (optional)

Add `docs/data/tutorial_copy.json` behind the existing manifest once copy authors want overnight text fixes. Until then, Phase 2 catalogs already provide the high-churn JSON path.

## Related

- [`DATA_CATALOGS.md`](./DATA_CATALOGS.md) — Phase 1/2 data refresh
- `electron_poc/remote_data_catalogs.js` — shared fetch/hash/cache machinery
