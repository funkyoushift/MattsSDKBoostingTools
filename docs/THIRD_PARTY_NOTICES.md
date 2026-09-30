# Third-Party Notices

MSBT's original code is licensed under the repository's MIT `LICENSE`. That
license does not replace the licenses or permission grants below and does not
claim ownership of third-party code, data, artwork, names, or trademarks.

## Source and permission map

| Material in MSBT | Source / author | Governing terms retained by MSBT |
| --- | --- | --- |
| Original MSBT toolset and `external_app/v22_parts_codes_fixed/matt_editor/` | Mattmab, also known as Galoob; [original MSBT source](https://github.com/mattmab/MattsSDKBoostingTools) | Incorporated, modified, and redistributed with the author's direct permission. The reviewed upstream package also declared ISC; its notice is preserved as `LICENSE_MATTMAB_ISC.txt`. Mattmab has requested that the MSBT project itself use MIT. |
| Previously supplied Nexus JSON data and retained overrides | Dominic (Cr4nkSt4r), [Borderlands-4.NcsParser](https://github.com/Cr4nkSt4r/Borderlands-4.NcsParser) | The previously received copies carried the MIT notice `Copyright (c) 2026 Dominic (Cr4nkSt4r)`. That notice remains in `LICENSE_CR4NKST4R.txt` and in retained source material. |
| Current game-derived Nexus tables, world definitions and part supplements | Gearbox / 2K game data, extracted locally from installed BL4 build 25234898 | These game data are not claimed as original MSBT code or relicensed as MIT. Extraction provenance and hashes are recorded in `external_app/v22_parts_codes_fixed/matt_editor/LegitItems/local_game_data_provenance.json`. The unmodified NcsParser CLI is a separate local maintainer tool and is not shipped or linked into MSBT. |
| Loveless skill, tooltip and portrait PNGs in `matt_editor/uiresources/corpo_hacker_icons/` | Gearbox / 2K artwork, extracted locally from installed BL4 build 25234898 | Native game artwork, not original MSBT artwork or relicensed as MIT. The adjacent `native-assets-manifest.json` records source paths and hashes. CUE4Parse and CUE4Parse-Conversion are external maintainer extraction dependencies; they are not shipped as MSBT runtime components. |
| GZO-derived catalogs, part maps, and linked images | Ynot / GZO, [GZO BL4 Codes](https://save-editor.be/GZO/Borderlands4/Codes.html) | Used and redistributed with the site owner's direct permission. These data are not relicensed as MIT by MSBT. |
| Lootlemon-derived catalog records and links | Levin / Lootlemon, [Lootlemon](https://www.lootlemon.com/) | Used and redistributed with the site owner's direct permission. These data are not relicensed as MIT by MSBT. |
| Challenge-path discoveries | Mattmab / Matt; credited from maintainer-provided project history | Discovery credit, separate from authorship of later implementations. [Original MSBT](https://github.com/mattmab/MattsSDKBoostingTools). |
| UVHM path discoveries and tier workflow in `backend_actions.py` | PyrexBLJ discovered earlier UVHM paths; Azalea Asvail developed the Azzy UVH Booster workflow with help from FunkYouSHiFT | The reviewed Azzy source metadata declares MIT. [Azzy UVH Booster](https://github.com/AzaleaAsvailAMW/amw-Uvhbooster); [PyrexBLJ public profile](https://github.com/PyrexBLJ). Discovery and assistance credits follow maintainer-provided history; the profile link is not proof of particular path discoveries. |
| Documented adaptations and references for movement/teleport, combat/resource/vehicle tuning, location bookmarks, and compact Dev Spawner layout; see scope clarification below | RDP / Squ1ggs, [Bl4SDKmods](https://github.com/Squ1ggs/Bl4SDKmods) | MIT, `Copyright (c) 2026 Squ1ggs`. The exact notice is stored as `LICENSE_SQU1GGS_MIT.txt` in both the SDK source and packaged external-app tree. |
| [`tools/third_party/sdk_mods/ActorScriptDeployer/`](https://github.com/funkyoushift/MattsSDKBoostingTools/tree/main/tools/third_party/sdk_mods/ActorScriptDeployer) — standard Dev Spawner backend | Matt, as named in the bundled author metadata | MIT, as declared by its `pyproject.toml`; a full MIT notice is stored in that directory. |
| `mod_extracted/MattsSDKBoostingTools/bl4_tpc/` | Renil; distributed archive also credits Epilow | Used under the author's public permission allowing modification and redistribution. Source page: [Third Person Camera SDK](https://www.nexusmods.com/borderlands4/mods/259). This component is not represented as MIT. |
| Save/profile encryption wrapper adapted through Mattmab's editor | glacierpiece, [borderlands-4-save-utility](https://github.com/glacierpiece/borderlands-4-save-utility) | MIT, `Copyright (c) 2025 glacierpiece`. The exact upstream notice is preserved beside the wrapper as `LICENSE_GLACIERPIECE_MIT.txt`. |
| `electron_poc/vendor/gridstack/` | GridStack 11.5.1, Alain Dumesny | MIT; full notice stored beside the vendored files. |
| `matt_editor/js/vendor/js-yaml-4.3.2.js` | js-yaml 4.3.2, pako 2.1.0, and the Microsoft Monaco AMD loader | MIT; pako also identifies zlib-licensed portions. Full notices are stored beside the bundle in `THIRD_PARTY_LICENSES.txt`. |

The permission confirmations for Mattmab/Galoob, GZO, and Lootlemon are held
by the MSBT maintainer. They are described here so that downstream recipients
do not mistake permission-only data or assets for MIT-licensed MSBT code.

### Attribution scope clarification (2026-09-30)

The earlier overlap audit did not separate code already in MSBT's July baseline
from later adaptations. Its blanket attribution of legit-building, serial,
economy, inventory, and other whole modules to Squ1ggs is withdrawn as an
unsupported provenance conclusion. Matching code alone does not establish its
original author or the direction of reuse. Catalog/data origins still require
source-specific tracing; retained notices are not proof of exclusive authorship.

The documented August work credits Squ1ggs code/patterns for movement/teleport
and combat/resource/vehicle tuning, and inspiration for location bookmarks and
the compact Dev Spawner layout. This does not credit Squ1ggs with Actor Script
Deployer, the original challenge-path discoveries, or the earlier UVHM paths.
Actor Script Deployer's metadata names Matt; MSBT's standard spawning route
calls its `_cmd_spawnai`, with MSBT-side integration and runtime fixes.

Existing copyright and license texts remain intact. This correction narrows
claims of provenance; it does not remove notices or relicense any material.
See [Attribution review](https://github.com/funkyoushift/MattsSDKBoostingTools/blob/main/docs/ATTRIBUTION_REVIEW_2026-09-30.md)
for evidence, maintainer-provided history, and unresolved boundaries. No claim
about the origin of another developer's entire project is intended.

## Desktop runtime and npm packages

Electron and Chromium notices are emitted next to the packaged executable as
`LICENSE.electron.txt` and `LICENSES.chromium.html`. Production npm package
license files remain inside `app.asar`. The embedded CPython runtime retains
its own `LICENSE.txt`. MSBT additionally packages its root `LICENSE` and this
notice as top-level resources.

The separately vendored GridStack copy and the editor browser bundle are
covered by the adjacent notices identified in the table above.

## Android controller

The Android app directly uses AndroidX Core 1.13.1, AndroidX WebKit 1.12.1,
and JourneyApps ZXing Android Embedded 4.3.0 (including ZXing Core transitively).
Those dependencies use Apache License 2.0. The APK build copies MSBT's license,
this notice, and the complete Apache 2.0 text into its `assets/licenses/`
directory.

## Bundled SDK and AFK SHiFT menu

The installer includes the unmodified official oak2-mod-manager v0.3 release
archive (SDK, Python runtime, and mod manager). Existing SDK installations are
preserved, including beta and nightly builds. Full license texts and pinned
upstream source links are included in resources/oak2/NOTICE.txt and adjacent
license files. These components are not relicensed as MIT.

The AFK SHiFT PAK is the maintainer-provided pakchunk90 menu mod with the MSBT
AFK bridge and floating controls appended. Its source hash is recorded in
resources/afk_shift/manifest.json. Game-owned SHiFT resources are not MSBT code
and are not relicensed as MIT.

## Reference-only projects

The GPL projects listed in `docs/REFERENCE_MOD_NOTES.md` were reviewed for behavior.
Reviewing a project does not mean its implementation was copied. In particular,
GPL-licensed reference implementations must remain reference-only unless MSBT
is deliberately made compliant with their copyleft terms.

The complete 2026-09-10 comparison against the oak2 Mod Database is recorded in
`docs/OAK2_MOD_DB_LICENSE_AUDIT_2026-09-10.md`.

## Game and community content

Borderlands, Gearbox, 2K, and related names and assets belong to their respective
owners. MSBT is an unofficial fan project and no affiliation or endorsement is
claimed. Permission from a community source owner covers that source owner's
contribution; it does not purport to grant rights owned by Gearbox, 2K, or any
other third party.
