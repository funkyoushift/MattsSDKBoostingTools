# Project map

What each **published** top-level folder is for (after nesting cleanup).

> **GitHub tip:** On the repo file browser, the grey text beside a folder is the *most recent commit message that touched that path* — not a folder description. After a large multi-folder commit those lines often look identical and unrelated to the folder’s purpose. Real descriptions live here and in the root [`README.md`](../README.md).

## GitHub root (what visitors see)

| Path | Purpose |
| --- | --- |
| [`README.md`](../README.md) / [`LICENSE`](../LICENSE) | Public entry + license |
| [`.github/workflows/`](../.github/workflows/) | CI (Electron release, Nexus sync helpers) |
| [`docs/`](./) | Human docs, screenshots, versioning, release metadata, reference archives |
| [`electron_poc/`](../electron_poc/) | **Shipping desktop UI** (Electron). Folder name is historical (“poc”). |
| [`external_app/v22_parts_codes_fixed/`](../external_app/v22_parts_codes_fixed/) | Packaged resources / Matt Editor host / serial helpers (not the main UI). Do not rearrange unless explicitly asked. |
| [`mod_extracted/MattsSDKBoostingTools/`](../mod_extracted/MattsSDKBoostingTools/) | **SDK mod source** — bridge, backend actions, Quick Menu, optional BLImGui |
| [`tools/`](../tools/) | Build/publish scripts, tests, NearbyDump, bundled third-party SDK mods |

Local-only / gitignored scratch (not on GitHub): `dist_electron/`, `build/`, `.venv/`, `AGENTS.md`, peek folders, etc.

## Inside `docs/`

| Path | Purpose |
| --- | --- |
| [`media/`](./media/) | README / Discord screenshots |
| [`releases/`](./releases/) | Tracked release metadata (`latest.json`, current notes, Discord promo media) — **not** installers |
| [`release-notes/`](./release-notes/) | Older historical release notes |
| [`reference/`](./reference/) | Look-back only (legacy Tkinter packagers, one-shot architecture reviews) |
| `VERSIONING.md`, `BUILD_AND_PACKAGE.md`, `ELECTRON_ROADMAP.md`, … | Maintainer docs |

## Inside `tools/`

| Path | Purpose |
| --- | --- |
| `build_electron_beta.ps1`, `build_sdkmod.ps1`, `publish_github_release.ps1`, … | Packaging / release |
| [`tests/`](../tools/tests/) | Python / wiring tests |
| [`third_party/sdk_mods/ActorScriptDeployer/`](../tools/third_party/sdk_mods/ActorScriptDeployer/) | Bundled Dev Spawner support mod (copied into Electron builds) |
| [`NearbyDump/`](../tools/NearbyDump/) | Optional folder-mod helper for live path dumps |

## Outside the working tree

| Path | Role |
| --- | --- |
| `../_msbt_archive/` | Bulk history: LOV/probe, peeks, build outputs, old packages, audit dumps |

## Runtime picture

```text
Electron (electron_poc)  ← primary desktop UI
  → HTTP :49774 → external_bridge → backend_actions → game helpers
  → also uses external_app helpers/resources (not Tkinter UI)

SDK __init__
  → starts bridge + Quick Menu (F7)
  → optional BLImGui panel (fallback only)
```

See [`ELECTRON_ROADMAP.md`](ELECTRON_ROADMAP.md). Maintainer AI notes live in local `AGENTS.md` (gitignored).
