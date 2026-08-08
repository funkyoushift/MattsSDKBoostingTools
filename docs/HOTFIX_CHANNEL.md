# Hotfix channel (Phase 3)

Goal: ship **copy / tutorial / JSON-only** asset packs without a full Electron installer or SDK SemVer bump, using the same trust model as remote data catalogs.

## Non-negotiables

- **No remote code execution.** No downloading `.js`, `.py`, `.exe`, `.dll`, `.sdkmod`, or any executable payload into a load path.
- **Allowlisted asset types only:** JSON, Markdown/plain text tutorial copy, static images already referenced by the app (optional later).
- **`min_app_version` gates:** packs that require newer UI/schema are ignored by older builds.
- **Offline last-good:** never wipe a working local pack on a failed refresh.
- Bridge stays **delivery-only** (no blimgui import; no remote fetch inside `external_bridge.py`).

## Manifest layout

`catalog_manifest.json` keeps Phase 1/2 catalogs under `files[]` and Phase 3 allowlisted packs under `assets[]` (alias: `packs[]`):

```json
{
  "id": "tutorial_copy",
  "path": "tutorial_copy.json",
  "kind": "json_copy",
  "sha256": "...",
  "bytes": 1234,
  "min_app_version": "2.3.0",
  "url": "https://github.com/.../releases/download/data-vX.Y.Z/tutorial_copy.json",
  "raw_url": "https://raw.githubusercontent.com/.../docs/data/tutorial_copy.json"
}
```

Allowed `kind` values (v1):

| kind | Consumer | Notes |
| --- | --- | --- |
| `catalog_json` | Electron + optional SDK cache read | Phase 1/2 data files |
| `json_copy` | Electron UI strings / walkthrough tips | Optional; title/body overlays only |
| `markdown_doc` | In-app help panes | Optional; render as text only |

Rejected always: `script`, `native`, `sdkmod`, `archive_exec`, anything with an executable extension (`.js`, `.py`, `.exe`, `.dll`, `.sdkmod`, …). Publisher and Electron both enforce this.

## Shipped starter: `tutorial_copy.json`

Present under [`docs/data/tutorial_copy.json`](./data/tutorial_copy.json) and published with the data channel (**data-v1.0.3+**).

High-value `main` tour overlays (title/body only): Welcome (0), Boosting (2), Serial Tools (3), Updates (7), Arrange layout (9). Bundled SDK download / Updates-tab **links** stay local.

Schema:

```json
{
  "schema_version": 1,
  "kind": "json_copy",
  "min_app_version": "2.3.0",
  "tours": {
    "main": [
      { "index": 0, "title": "...", "body": "..." }
    ]
  }
}
```

Electron behavior:

1. Data catalog refresh downloads allowlisted `assets[]` into `userData/msbt_data/` (same sha256 rules as catalogs).
2. Renderer calls `msbt.getTutorialCopy()` at startup and after refresh.
3. Only **title** / **body** patches apply. Targets, links, actions, and selectors stay bundled — remote JSON cannot retarget UI or inject URLs/actions.

## Electron flow

1. Fetch manifest (release asset → raw main fallback), same as data catalogs.
2. Download changed sha256 into `userData/msbt_data/` for `files[]` + allowlisted `assets[]`.
3. UI reads copy JSON if present; otherwise bundled defaults.

## What this is not

- Not an auto-updater replacement for Electron/SDK binaries.
- Not a vehicle for UE hooks, console commands lists that execute arbitrary strings from remote, or plugin sideloads.
- Not a mobile code OTA channel (mobile may refresh **catalog JSON** only).

## Publish

```bash
python tools/publish_data_release.py --bump patch --create-release
```

One command rebuilds hashes, bumps `data-vX.Y.Z`, rewrites preferred Electron/mobile manifest URLs, and creates a **prerelease** GitHub data tag (keeps app `/latest` intact).

## Related

- [`DATA_CATALOGS.md`](./DATA_CATALOGS.md) — Phase 1/2 data refresh
- `electron_poc/remote_data_catalogs.js` — shared fetch/hash/cache + tutorial copy loader
- `docs/data/tutorial_copy.json` — allowlisted starter pack
