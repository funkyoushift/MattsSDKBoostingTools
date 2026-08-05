# NearbyDump

Tiny BL4 folder mod to capture live object paths near the player or map-wide (e.g. floating DLC coins).

## Install

Copy this folder to:

`...\Borderlands 4\sdk_mods\NearbyDump\`

Layout must match other folder mods (`__init__.py` + `pyproject.toml` at the folder root). **Fully restart BL4** after copying or editing `.py` (folder mods do not hot-reload).

## Mandolin arcade coins (important)

The **15** Zane / arcade coins are **not** PersistentLevel UAID actors. Mission data wires them as:

- `OakSpawner_Token_1` … `OakSpawner_Token_15` → spawn `IO_BP3_CoinToken_Interactable`
- `bautoenablespawner: false` (mission graph enables them)
- Progress tracked as `Token_01.IsCollected` … `Token_15.IsCollected`

`find_dump CoinToken` matching only **4** hits is expected in free-roam after coins are collected / spawners idle:

- 3× `IO_RedChest_BP3_CoinToken_*` (chests that *spend* coins — always PersistentLevel)
- 1× `IO_BP3_CoinToken_Brain_*` (token brain / chest unlock tracker)

Those names contain `CoinToken` but they are **not** the 15 floating coins.

## Commands

```text
find_dump CoinToken
find_dump Interactable
find_dump_class LootableObject CoinToken
find_dump_class LootableObject
find_dump_class OakSpawner Token
find_dump_class OakSpawner
nearby_dump CoinToken 0
nearby_dump IO_BP3_CoinToken_Interactable 0
nearby_dump CoinToken 50000
nearby_dump coin 2500
nearby_dump_all 2500
```

- `find_dump [needle]` — map-wide: **no distance filter**; list all name matches sorted by distance from player.
- `find_dump_class <Class> [needle]` — `find_all` on **one** class only (e.g. `LootableObject`, `OakSpawner`). Empty needle lists all instances.
- `nearby_dump [needle] [radius]` — same scan; **radius `0`** means unlimited (same as `find_dump`).
- Prefer OakInteractiveObject / LootableObject / OakSpawner; skips `find_all(Actor)` when a needle is set or radius is unlimited.
- Output capped at 200 hits.

## Dump files

Writes to every writable path (logs each attempt):

- `sdk_mods\NearbyDump\dumps\nearby_dump_latest.txt` (may fail under Program Files)
- `%LOCALAPPDATA%\NearbyDump\dumps\nearby_dump_latest.txt` (fallback)
- Matching timestamped `nearby_dump_<stamp>.txt` beside each latest

Also mirrors lines to `unrealsdk.log`.
