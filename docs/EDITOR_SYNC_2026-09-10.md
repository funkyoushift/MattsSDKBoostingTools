# September 10 editor update

This change updates the embedded editor for BL4 v1.10, using installed game build `25234898`. It is prepared on a review branch. It does not change public versions, tags, releases, or updater manifests.

| Area | Coverage and behavior |
| --- | --- |
| Characters | All six Vault Hunters, including Loveless (`Char_CorpoHacker`, class-mod root 402) and C4SH (root 404). |
| Levels | Player/items 70, specialization 701, Vault Card levels 9999; Black Market defaults and controls now use the item cap. Explicit lower item levels remain intact. |
| Vault Cards | Five card tracks and currencies; explicit XP is preserved when changing a level. |
| Cosmetics | Canonical Resident parents resolve all 127 Loveless cosmetic IDs. The nine previously misclassified heads/skins are included without removing Vex equivalents. |
| Skills | Initial and supplemental loaders normalize graph/node keys. Identical native skill references can share tooltip metadata. The current data resolves 565 passive references; 47 native empty positions retain the existing fallback instead of receiving invented skills. |
| Item selectors | Class-mod roots 402/404 and metadata-identified class mods stay out of unlocked weapon/grenade body categories. |
| Gear data | Current tables retain 515 inventory roots and 7,417 compact parts. Existing native gear and artwork are preserved. |
| NEW badges | All part and type views use one generated catalog diff: 774 added serial IDs and 202 part keys. NEW means added to this catalog refresh, including previously unindexed older content. It does not claim every addition is newly released game loot. |
| Missions | Providence/Harmonica and Bounty Pack 5/Viola have current labels, grouping, completion/reset selection, and area controls. All 19 Harmonica set definitions are recognized; 16 have static completion templates. |
| Save XP | Character/specialization level edits and max presets preserve existing XP. Separate point fields allow deliberate edits; fitted curves and hardcoded XP amounts are no longer silently written. |
| Browser dependencies | js-yaml 4.3.2 replaces the older parser. Existing pako and Monaco companion code is preserved byte-for-byte, with provenance hashes and complete notices. |

## Verification

Run from `electron_poc`:

```powershell
npm run test:editor-update
npm run test:game-update
npm run check
```

The focused tests execute real browser helpers against the native data, exercise synthetic save/profile round trips, verify level/XP preservation and region scoping, check ordinary YAML parsing/compression, and verify local script references and badge membership. A hidden Electron window also loads the full page with external requests blocked, then exercises the Loveless selector, level/XP inputs and Providence/BP5 buttons. They do not modify player saves.

Generated native tables and vendor files use canonical LF line endings so their provenance hashes survive Windows and fresh Git checkouts. The importer writes LF explicitly; source hashes still describe the original parser output bytes. The browser checks verify all 59 imported table hashes and the vendored bundle.

Regenerate or verify badges from the previous published catalog:

```powershell
python tools/build_editor_release_badges.py --baseline-ref v2.10.1
python tools/build_editor_release_badges.py --baseline-ref v2.10.1 --check
```

## Data limits

`missionset_dlc2_npcmoments`, `missionset_micro_harmonica3`, and `missionset_side_harmonica4` have no statically assigned Mission rows in the current bundled exports. Grouping and reset support them, but completion does not invent their dynamic mission trees. Existing save data outside the chosen scope is preserved.

The native XP definitions contain curve parameters but do not establish the game's evaluation and rounding rules. Offline editors therefore preserve XP instead of presenting an estimated threshold as exact. The SDK's live native level setters are a separate path.

Catalog and serialization checks do not prove every item combination, mission progression transition, or actor spawn in gameplay. The native F7 menu, optional BLImGui fallback, SDK bridge, and Electron integration remain in their established roles.

## Sources

- [Official BL4 v1.10 update notes](https://borderlands.2k.com/borderlands-4/update-notes/)
- Native data provenance: `external_app/v22_parts_codes_fixed/matt_editor/LegitItems/local_game_data_provenance.json`
- Native artwork provenance: `external_app/v22_parts_codes_fixed/matt_editor/uiresources/corpo_hacker_icons/native-assets-manifest.json`
- [js-yaml ordered-map advisory](https://github.com/nodeca/js-yaml/security/advisories/GHSA-5p4m-2wfm-xmqj) and [empty-merge advisory](https://github.com/nodeca/js-yaml/security/advisories/GHSA-2883-xcg3-v3hh)
