# BL4 September 10, 2026 catalog update

The local seeds now include data extracted from installed Steam build
**25234898**. This is a local update; app and data release versions remain
unchanged. The final local package loaded on the updated game and its bridge
reported the current parameters without BLImGui installed. Live spawning,
travel and save edits still need verification.

## Imported data

| Catalog | Before | After | Coverage |
| --- | ---: | ---: | --- |
| Inventory roots | 450 | 515 | Current root definitions and inherited builder relationships |
| Compact inventory parts | 6,648 | 7,417 | Current serial IDs, slot rules, tag rules and names |
| Part-map IDs | 6,916 | 7,592 | Existing labels retained, 676 missing IDs added |
| Loveless class-mod parts | 0 | 546 | Root `402`, `classmod_corpohacker`, `Char_CorpoHacker` |
| Dev Spawner actors | 5,263 | 6,682 | Current local actor definitions merged with existing curated entries |
| Item pools | 586 | 699 | Current named pools, including 155 shiny pools |
| Travel maps | 22 | 27 | Includes verified new game-map definitions |
| Travel stations | 940 | 1,231 | Current station definitions and coordinates |
| Challenge entries | 2,549 | 3,286 | 837 new definitions; 100 duplicate identifiers differing only in case removed |
| Shiny serial variants | 106 | 127 | 21 extracted customization definitions paired with existing canonical gear serials |

The importer refreshes 59 numbered Nexus table files, including the previously
missing `Nexus-Data-skilltrees_data0.json` containing
`corpohacker_skill_trees`. The full parser output is normalized by unwrapping
type metadata while retaining `__deps` and `__dep_entries`; minimal parser
output alone cannot supply the editor's item-part data.

The unnumbered `Nexus-Data-inv.json` hotfix layer contained 15 overrides. Each
has a matching current `(root, dependency table, part key, serial identity)` in
the installed game. Only those superseded overrides were omitted. The importer
preserves unmatched custom parts and non-null custom root records. The file
and its original notice remain as a compatible empty override layer.

Current source-file hashes, normalized-file hashes, all new composition IDs,
the hotfix comparison and challenge/shiny additions are recorded in
[`local_game_data_provenance.json`](../external_app/v22_parts_codes_fixed/matt_editor/LegitItems/local_game_data_provenance.json).
The data came from local game assets through a separate, unmodified NcsParser
utility. The parser's executable or source is not incorporated into these
catalogs.

## Newly available gear and character data

There are **97 newly indexed buildable gear compositions** relative to the
previous compact rules. This includes older recipes missing from that compact
catalog as well as content from the current update; it is not a claim that all
97 were first released today.

Examples include Honeymooner, Shield Overflow, Infection, Virtue, Critical
Decay, Enumeration, Wind Skimmer, Clarity, Hippo Gun, Hand Frag, Flash Fuel,
Little Sister and Over Swarm. Loveless entries include Devourer, Virophile,
Montage Maker, Memory Hoarder, Trackstar, Functional Human and Programmer.

These definitions are available through the existing legitimate item builder
and Matt Editor part menus. Loveless also has a native character section in
`game_data_export.json`. A generated local part supplement supplies the current
indexed part IDs without removing existing curated editor descriptions.
New gear can also use the verified item-pool picker.

All **130 native Loveless image references** now have matching exported PNGs,
including skill icons, tooltips and portrait art. Each image was decoded from
the installed game, re-decoded after export, and checked against its recorded
dimensions and SHA-256. Representative action-skill, passive and portrait images
were visually inspected. `uiresources/corpo_hacker_icons/native-assets-manifest.json`
records the original assets and build; `tools/game_icon_extract` documents the
repeatable export. These are original Gearbox / 2K assets.

The challenge catalog includes **338 VC5 identifiers**. Tier goals follow
parent inheritance: for example, `vc5_AcquireContract10` resolves to 10 instead
of defaulting to 1. Catalog generation does not grant or complete challenges.
The offline Character Challenges preset now uses all 42 verified counter paths
for six Vault Hunters, including the separate C4SH and Loveless DLC branches.
It preserves higher counters and can use newer loaded Nexus goals. Current
level-up challenge goals are 50 for the original four characters and C4SH, and
60 for Loveless; these challenge goals are distinct from the level-70 XP cap.

All 127 shiny serial variants are at level 70. The existing 106 variants retain
their item parts and customization values; only their level headers changed.
The 21 additional variants use unchanged Lootlemon item parts plus exact shiny
customization names found in the installed game. They passed serialization
round-trip checks, but have not been live-spawn tested. Two distinct extracted
customization definitions map to Cormano; their catalog IDs remain distinct.
Another 24 shiny definitions have no matching canonical base serial in the
available Lootlemon catalog. Those serials were not fabricated. The local
drop-all-shinies path now also includes all 155 verified shiny item pools.

## Online catalog check

The existing refresh pipeline was run with `--bump-data-version keep` and
backups before writes:

- Lootlemon: 330 entries, 330 live detail pages checked, no new or changed
  serials. Its current serial list still lacks the new Providence gear.
- GZO: 2,897 entries, no new serials; eight rows gained thumbnail metadata.
- GZO family data still reports generation on August 1, 2026; it supplied no
  new part IDs.
- The save-editor Nexus proxy returned 59 files identical to the old seeds;
  three known keys returned 404. The newer locally extracted tables supersede
  those older online copies.

The maintainer's Nexus refresh now preserves files recorded in local extraction
provenance, including subsequent local edits, without downloading replacements.
Replacing them requires `--replace-local-nexus`; that explicit override retains
backups and the original provenance hashes, and does not mark online bytes as
verified game data.

Sources: [Lootlemon weapon list](https://www.lootlemon.com/db/borderlands-4/weapons),
[Loveless skill calculator](https://www.lootlemon.com/class/loveless),
[GZO catalog](https://save-editor.be/GZO/Borderlands4/codes/api.php?action=catalog),
[GZO family data](https://save-editor.be/GZO/Borderlands4/family-data.js?v=master-parts).

The online refresh also exposed a Windows console-encoding failure after
manifest generation. Logging now safely escapes unsupported console characters,
and child Python tools use UTF-8 so a completed refresh can finish reporting.

## Rebuild and verification

```powershell
python -X utf8 tools/import_local_ncs_catalogs.py <full-decoded-json-directory> --game-build 25234898 --write
python -X utf8 tools/refresh_game_world_catalogs.py <full-decoded-json-directory> --game-build 25234898 --write
python -X utf8 tools/build_data_catalog_manifest.py
python -X utf8 tools/build_data_catalog_manifest.py --check
```

The inventory importer does not fetch, publish, bump versions, or overwrite
world/spawner catalogs. Those use the separate world refresh tool. Retain the
local-game imports when checking older online sources.
The world importer processes every numeric shard in numeric order, including
shard 1's HoldingStation and MainMenuStation metadata. Both actors were already
listed, so refreshing their definitions leaves the actor count unchanged.

Focused parser, override-preservation, challenge-inheritance, manifest-freshness
and Windows logging tests pass. The refreshed Python tools and generated
JavaScript pass syntax checks. A Loveless class mod with its body and two
matching passive-point parts validates and round-trips at level 70.

The data manifest remains **data-v1.0.3**. Fresh game-derived assets carry
`game_build: "25234898"` so the desktop cache can distinguish their freshness
from older hosted catalogs. All manifest hashes and bundled mirrors were
checked after regeneration. No release or installer was published.

## Application and local runtime checks

The SDK, Electron, embedded editor and Android controller use player/item cap
70, specialization cap 701 and five Vault Cards with card cap 9,999. Live XP
actions use the game's native setters; no new XP curve was guessed. Offline
Vault Card level edits preserve the separately entered XP points. Loveless's
save token, class-mod root, skill trees and cosmetic category are wired into
the existing editor.

The installed SDK package was backed up before replacement under
`_install_backups/bl4-build-25234898-20260910-132712`. BL4 launched on build
25234898 and loaded MSBT 2.10.1, unrealsdk 3.2.0 and pyunrealsdk 1.10.0.
The live `/status` response had `ok: true`, `started: true`,
`snapshot_ready: true`, `blimgui_available: false` and no bridge error.
This establishes bridge startup without BLImGui; it does not establish that
every extracted actor or station works in a live session.

That live check caught the bridge's status projection omitting the backend's
new `game_parameters` field. The final local package includes the correction
and tests for both the cached HTTP response and pre-tick status. It is built
as `MattsSDKBoostingTools.sdkmod` (964,903 bytes, SHA-256
`df2931924af021e5eb69a57bd67040a2b1bffa51f2701917bd3ab04592efabbc`).
After Matt approved the game restart, BL4 closed normally and the final
package was installed with matching hashes. The new game process owns the
bridge listener and `/status` reports build `25234898`, player/item cap 70,
specialization cap 701, card cap 9,999, all five Vault Card tokens/tracks,
`snapshot_ready: true`, `blimgui_available: false` and no bridge error.
Local evidence is retained in `_tmp_catalog_compare/runtime-verification-25234898.json`
and `unrealsdk-final-25234898.log` in the same directory.

Electron was restarted after the final editor assets were added. Its active
catalog cache matches all seven game-derived bundled catalog hashes, and a
second startup refresh reported all 11 entries unchanged. Python syntax and
package-integrity checks, isolated Quick Menu/bridge tests, builder serial
round trips, JavaScript game-update/counter/cache tests and the Android Java
compile passed. Quick Menu registry tests run separately because older bridge
tests leave module stubs in the shared Python interpreter. An unrelated
pre-existing ASD probe autorun assertion remains stale; no probe behavior was
changed for this update.
