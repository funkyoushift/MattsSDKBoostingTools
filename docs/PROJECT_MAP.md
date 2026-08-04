# Project map

What lives where in the MSBT repo (after Phase 1–3 cleanup).

## Product (edit these)

| Path | Role |
| --- | --- |
| [`mod_extracted/MattsSDKBoostingTools/`](../mod_extracted/MattsSDKBoostingTools/) | **SDK mod source** — bridge, backend actions, Quick Menu, optional BLImGui |
| [`electron_poc/`](../electron_poc/) | **Desktop app** (Electron). Folder name is historical (“poc”); this is the shipping UI. Rename deferred until explicitly approved (touches packaging/CI/docs). |
| [`external_app/v22_parts_codes_fixed/`](../external_app/v22_parts_codes_fixed/) | **Runtime helpers + resources**, not the main UI. Electron packages this tree for catalogs, serial tools, and Matt Editor host. Tkinter shells inside are legacy rollback only — do not rearrange without an explicit ask. |
| [`third_party/sdk_mods/ActorScriptDeployer/`](../third_party/sdk_mods/ActorScriptDeployer/) | Bundled Dev Spawner support mod |
| [`docs/`](./) | Current human docs + README media |
| [`releases/`](../releases/) | `latest.json`, `RELEASE_NOTES_v*.md`, Discord promo media — **not** installers/ZIPs |
| [`tests/`](../tests/), [`tools/`](../tools/) | Tests and helper scripts |
| [`build_electron_beta.ps1`](../build_electron_beta.ps1), [`build_sdkmod.ps1`](../build_sdkmod.ps1), [`publish_github_release.ps1`](../publish_github_release.ps1) | Ship / package |
| [`.github/workflows/`](../.github/workflows/) | CI release |

## Reference (in-repo, not daily)

| Path | Role |
| --- | --- |
| [`_reference/legacy_tkinter/`](../_reference/legacy_tkinter/) | Old Tkinter packaging scripts |
| [`_reference/docs/`](../_reference/docs/) | Historical architecture / one-shot review docs |

## Outside the working tree

| Path | Role |
| --- | --- |
| `../_msbt_archive/` | Bulk history: LOV/probe, peeks, build outputs, old packages, audit dumps, tester packs |

## Runtime picture

```text
Electron (electron_poc)  ← primary desktop UI
  → HTTP :49774 → external_bridge → backend_actions → game helpers
  → also uses external_app helpers/resources (not Tkinter UI)

SDK __init__
  → starts bridge + Quick Menu (F7)
  → optional BLImGui panel (fallback only)
```

See [`AGENTS.md`](../AGENTS.md) and [`ELECTRON_ROADMAP.md`](ELECTRON_ROADMAP.md).
