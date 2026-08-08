# `docs/data/`

GitHub-hosted MSBT data catalogs. See [`../DATA_CATALOGS.md`](../DATA_CATALOGS.md).

- `catalog_manifest.json` — data SemVer + sha256 index (`data-vX.Y.Z`)
- JSON seeds listed in the manifest (Lootlemon, custom codes, GZO snapshot, travel, pools, …)

Rebuild hashes:

```bash
python tools/build_data_catalog_manifest.py --bump patch
python tools/build_data_catalog_manifest.py --check
```
