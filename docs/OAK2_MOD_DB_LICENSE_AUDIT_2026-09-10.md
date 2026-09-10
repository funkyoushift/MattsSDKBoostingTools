# oak2 Mod Database License Cross-Check

Date: 2026-09-10

Scope: all 34 entries published in the BL4
[oak2 Mod Database](https://bl-sdk.github.io/oak2-mod-db/) at site commit
`eaf46a8796b16a6f96d1637cba796c1ddd986216`, their linked `pyproject.toml`
metadata, and the linked source repositories available on the audit date.

This is an engineering provenance review, not legal advice. A source comparison
can detect copied text/code, but cannot prove that independently written code
never used the same ideas.

## Result

- MSBT contains substantial copied or adapted material from Squ1ggs' MIT
  sources. Earlier MSBT notices understated that scope and earlier planning
  documents incorrectly called the whole `Squ1ggsBoostingTools` package GPL.
  The upstream repository has carried a root MIT license since its initial
  commit; Challenge Ticker is the separately marked GPL exception.
- MSBT now ships Squ1ggs' exact MIT text, including
  `Copyright (c) 2026 Squ1ggs`, in the SDK mod, desktop package, external-app
  tree, and Android assets that carry derived catalog data.
- No material copied source block was detected from the GPL-listed mod
  repositories. Those projects remain reference-only.
- The oak2 mod manager is a separately downloaded LGPL-3.0 runtime dependency;
  it is not vendored or relicensed by MSBT.

## Used, adapted, or required

| Database entry / source | Listed license | MSBT relationship | Compliance action |
| --- | --- | --- | --- |
| BL4 Player Movement | MIT | Movement implementation and shared helpers adapted | Squ1ggs MIT notice shipped |
| Borderlands Mob Spawner | MIT | Spawner behavior/helpers and catalog lineage | Squ1ggs MIT notice shipped |
| Damage & More | MIT | Combat-tuning patterns/helpers | Squ1ggs MIT notice shipped |
| P2P Teleporter | MIT | Party/player targeting and teleport helpers | Squ1ggs MIT notice shipped |
| Resources & Cooldowns | MIT | Resource/cooldown patterns/helpers | Squ1ggs MIT notice shipped |
| Vehicle Movement | MIT | Vehicle movement/spawn patterns/helpers | Squ1ggs MIT notice shipped |
| World Travel | MIT | Travel implementation and data lineage | Squ1ggs MIT notice shipped |
| `Squ1ggsBoostingTools` (same linked repository; not a separate DB entry) | MIT | Substantial SDK, external-helper, and catalog material | Squ1ggs MIT notice shipped; detailed scope in `THIRD_PARTY_NOTICES.md` |
| MattsBL4ModsMenu | MIT | Mattmab project lineage; no material exact block found against its current repository | Mattmab/Galoob credit, MIT project license, and direct permission recorded |
| oak2 Mod Manager | LGPL3 | Required game-side runtime, downloaded unmodified rather than bundled | Identified as a downloaded dependency; upstream release retains its LGPL files |

## GPL entries: not incorporated

The following database entries are GPL-licensed (the two Last1SiN entries also
declare additional GPL section 7 terms). MSBT does not bundle them and the
normalized source comparison found no matching contiguous block of 12 or more
nonblank, noncomment lines against their current linked repositories.

| Author | Database entries |
| --- | --- |
| Squ1ggs | Challenge Ticker |
| Yeti | Better World Boss Domes; command_history; Crystals Are Bad; Dialog Skipper; Dump Ping; Encore Tweaks; Falling Menus; Grapple Anywhere; Ground Loot Helpers; Modifier Eater; No More Barrels; Player Scaled Enemies; Rarity Remover; Separate Melee/Grapple Keys; Time & Weather Controls; TPS Style Slams |
| FreepDryer | Better Vehicle Jump; Trash Seller |
| apple1417 | obj_dump |
| Lango | Autordonite |
| Last1SiN | BL4 Auto Reload; BL4 Super Dash |

One eight-line generic authority-check sequence in MSBT movement code also
appears in Challenge Ticker. The same sequence appears in Squ1ggs'
MIT-licensed `Squ1ggsBoostingTools/movement_adjustments.py`, which is the
identified source for MSBT's movement module. It is therefore covered by the
retained Squ1ggs MIT notice and is not evidence of Challenge Ticker copying.

## Other MIT entries: no use detected

No material exact source match or named runtime dependency was found for:

- BonkUtilities (Pyrex)
- modthatclosesthegamewhenitopens (Pyrex)

They require no MSBT distribution notice while they remain neither copied nor
bundled.

## Squ1ggs-derived scope observed

The comparison found substantial exact or near-exact lineage in these shipped
areas:

- SDK: `legit_builder_core.py`, `serial_converter.py`,
  `movement_adjustments.py`, `serial_rewards.py`, `party_helpers.py`,
  `travel.py`, `blimgui_panel.py`, `player_economy.py`,
  `inventory_capacity.py`, `dev_tools.py`, `shinies.py`,
  `vault_card_boost.py`, `golden_chest_keybinds.py`, and related helpers.
- External helper tree: `external_legit_builder.py`,
  `external_serial_tools.py`, `resources/gzo_parts_map.json`, and
  `resources/item_pools.json`.
- Desktop/mobile catalog path: `dev_spawner_catalog.json` and downstream copies
  of applicable catalog data.

MIT does not require every adapted file to use the upstream project's license
as its sole license. It does require the upstream copyright and permission
notice to be retained in copies or substantial portions, which the packaging
changes in this audit implement.

## Audit method and limitations

1. Read every `_oak2_mods` entry and fetched its linked project metadata.
2. Compared shipped Python, JavaScript, HTML, and CSS against the linked
   Squ1ggs, Yeti, FreepDryer, Pyrex, Last1SiN, Lango, Mattmab, and apple1417
   repositories after normalizing whitespace and removing blank/comment-only
   lines.
3. Compared same-content data files and inspected high-confidence matching
   modules manually.
4. Distinguished bundled/adapted code from optional imports, separately
   downloaded runtimes, project lineage, and behavioral references.

Re-run this check before a release whenever a new community mod is copied,
vendored, or used to generate shipped data. Record the exact upstream revision
and add its full license text before distributing the artifact.
