# `docs/data/`

GitHub-hosted MSBT data catalogs. See [`../DATA_CATALOGS.md`](../DATA_CATALOGS.md) and [`../HOTFIX_CHANNEL.md`](../HOTFIX_CHANNEL.md).

- `catalog_manifest.json` — data SemVer + sha256 index (`data-vX.Y.Z`); catalogs in `files[]`, Phase 3 packs in `assets[]`
- JSON seeds listed in the manifest (Lootlemon, custom codes, GZO snapshot, travel, pools, …)
- `tutorial_copy.json` — allowlisted walkthrough title/body overlays (no remote code)

One-command publish (rebuild + optional GitHub prerelease):

```bash
python tools/publish_data_release.py --bump patch --dry-run
python tools/publish_data_release.py --bump patch --create-release
python tools/build_data_catalog_manifest.py --check
```
