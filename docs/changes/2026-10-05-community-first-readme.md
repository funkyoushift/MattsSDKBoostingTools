# Community-first README and fresh Mod Database review — October 5, 2026

## Request and result

Matt requested a complete README replacement, removal of obsolete app screenshots,
and prominent acknowledgment of the people whose work the project uses. He also
explicitly requested a fresh scrape of the entire BL4 SDK Mod Database.
The README now leads with creator contributions and source links, followed by a
brief explanation of MSBT integration, installation, and licenses. Old screenshot
embeds, promotional blocks and stale feature walkthroughs were removed from the
README; image files themselves were not deleted.

## Evidence collected

- Fetched the live site index and all **34 visible mod pages**, without fetch errors.
- Read all **35 database metadata entries**, including the SDK manager, and fetched
  their linked current pyproject metadata. No metadata fetch errors.
- Enumerated **13 source repositories** at pinned revisions. Read **76 Python files**
  across the listed mod source paths, including .sdkmod archives and the nested
  Grapple Anywhere SDK archive. No upstream code was executed.
- Compared stripped nonblank/non-comment Python windows with SDK, packaged external
  Python helpers and bundled Actor Script Deployer. Initial 12-line loose-source
  scan was insufficient because several mods publish code only inside archives;
  final candidate scan includes archived source and uses eight-line windows.
- Reviewed existing attribution corrections, reference notes, local author metadata,
  source comments and relevant Git history. Also read current public projects for
  Mattmab, Squ1ggs, Azalea, Pyrex, apple1417, bl-sdk, glacierpiece, Cr4nkSt4r,
  Renil, GZO and Lootlemon, including sources not listed in the Mod Database.

Database tree revision: `b18cf6a0f930d03ccc297944ecb6c9c25512245d`.
[Machine-readable source revisions, hashes, fetch receipts and candidates](../attribution/2026-10-05-mod-database-snapshot.json).
The local scrape scripts and fetched source are retained under
`output/credit-review/`; third-party source is not added to the public repository.

## Important findings

- **juso and smugg** are BLImGui's declared authors. The earlier generic framework
  credit omitted their names. The README now names and links them.
- **Squ1ggs** deserves explicit spawn-anchor / re-aggro pattern credit in addition
  to interface inspiration. `spawn_helpers.py`'s module comment identifies SQBT
  pattern reimplementation, and `a956860` introduced the file. Current archive
  overlaps support investigating those helpers; the source/history documents the
  adaptation. Matt's Actor Script Deployer remains separately credited.
- **Azalea's** Quick Menu move/resize/theme inspiration is explicitly recorded in
  `quick_menu.py:36`, in addition to her UVH workflow credit.
- **apple1417 and Faultz** appear in the current oak2 manager contributor list.
  They are acknowledged with the wider SDK team, without assigning all SDK work
  to one person.
- Challenge Ticker currently declares **MIT**, unlike the historical September
  audit label. This review records today's declaration without retroactively
  changing the terms of previously obtained versions or claiming use of that mod.
- Small overlaps in generic authority checks, actor helpers and UI code do not
  establish origin. The September 30 correction remains applicable. World-travel
  helper lineage and exact catalog origins are not newly resolved by this scan.
- Yeti, FreepDryer and apple1417 are acknowledged for the research references
  actually recorded in project notes. Their implementations are not presented as
  bundled simply because we studied them.

## Coverage and limits

This is a current attribution review, not a proof of every line's original author.
The automated comparison covers Python source within the listed mod paths and
local roots. It does not establish absence of rewritten, short, older, native,
asset or data reuse. License labels reflect current metadata, not a legal audit.
Pyrex's specific path discovery and Matt's challenge discoveries remain credited
from maintainer-provided history; a profile link is not independent proof of a
particular discovery. Renil's source identifies him; Epilow credit is retained
from the incorporated archive's recorded attribution.

Each database entry is accounted for below. "No candidate" does not mean "never
used"; it means no additional incorporation was established by this bounded check.

| Published mod | Declared author(s) | Current metadata license | Public work | Attribution disposition |
| --- | --- | --- | --- | --- |
| BL4 2-Player Split-Screen Unlocked | TitanNav | GPL3 | [Source](https://github.com/TitanNav/bl4-2player-splitscreen) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| Autordonite | Lango | GPL3 | [Source](https://github.com/jlangowells/bl4_ordonite_helper) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| BL4 AutoReload | Sol / GPT-5.6 Sol | GPL3 + Section 7 terms | [Source](https://github.com/Last1SiN/BL4-AutoReload) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| BL4 Super Dash | Sol / GPT-5.6 Sol | GPL3 + Section 7 terms | [Source](https://github.com/Last1SiN/BL4-SuperDash) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| Better Vehicle Jump | FreepDryer | GPL3 | [Source](https://github.com/FreepDryer/freepdryer-bl4-sdk-mods) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| BL4 Player Movement | Squ1ggs | MIT | [Source](https://github.com/Squ1ggs/Bl4SDKmods) | Documented movement/teleport or combat/resource/vehicle adaptations; Squ1ggs credited. |
| Bonk Utilities | Pyrex | MIT | [Source](https://github.com/PyrexBLJ/BL4-SDK-Mods) | No named integration or eight-line candidate found for this mod; Pyrex credited separately for UVHM discoveries. |
| Borderlands Mob Spawner (BMS) | Squ1ggs | MIT | [Source](https://github.com/Squ1ggs/Bl4SDKmods) | Documented spawn-helper pattern adaptation and compact layout inspiration; ASD credited separately. |
| Challenge Ticker | Squ1ggs | MIT | [Source](https://github.com/Squ1ggs/Bl4SDKmods) | Behavior reference in implementation notes; generic authority-check overlap does not establish copied implementation. |
| Crystals are Bad | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| Damage & More | Squ1ggs | MIT | [Source](https://github.com/Squ1ggs/Bl4SDKmods) | Documented movement/teleport or combat/resource/vehicle adaptations; Squ1ggs credited. |
| Dialog Skipper | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| Encore Tweaks | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| Falling Menus | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | Documented research reference; author acknowledged separately from incorporated code. |
| Grapple Anywhere | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | Documented research reference; author acknowledged separately from incorporated code. |
| Ground Loot Helpers | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| MattsBL4ModsMenu | Mattmab | MIT | [Source](https://github.com/mattmab/MattsBL4ModsMenu) | Mattmab credited for original MSBT/editor. Small UI overlap is a lead, not proof this separate mod was copied. |
| Modifier Eater | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| No More Barrels | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| P2P Teleporter | Squ1ggs | MIT | [Source](https://github.com/Squ1ggs/Bl4SDKmods) | Documented movement/teleport or combat/resource/vehicle adaptations; Squ1ggs credited. |
| Player Scaled Enemies | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| Rarity Remover | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| Resources & Cooldowns | Squ1ggs | MIT | [Source](https://github.com/Squ1ggs/Bl4SDKmods) | Documented movement/teleport or combat/resource/vehicle adaptations; Squ1ggs credited. |
| Separate Melee/Grapple Keys | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| TPS Style Slams | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| Time and Weather Controls | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| Trash Seller | FreepDryer | GPL3 | [Source](https://github.com/FreepDryer/freepdryer-bl4-sdk-mods) | Documented research reference; author acknowledged separately from incorporated code. |
| Vehicle Movement | Squ1ggs | MIT | [Source](https://github.com/Squ1ggs/Bl4SDKmods) | Documented movement/teleport or combat/resource/vehicle adaptations; Squ1ggs credited. |
| World Travel | Squ1ggs | MIT | [Source](https://github.com/Squ1ggs/Bl4SDKmods) | Documented bookmark inspiration; older travel helper overlap remains origin-unresolved. |
| blimgui | juso, smugg | MIT | [Source](https://github.com/juso40/blimgui) | Historical UI foundation; juso and smugg now named prominently. |
| command_history | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | No named integration or eight-line Python candidate found in reviewed source; not proof of independent authorship. |
| dump_ping | Yeti | GPL3 | [Source](https://github.com/RedxYeti/yeti-bl4-sdk) | Documented research reference; author acknowledged separately from incorporated code. |
| modthatclosesthegamewhenitopens | Pyrex | MIT | [Source](https://github.com/PyrexBLJ/modthatclosesthegamewhenitopens-bl) | No named integration or eight-line candidate found for this mod; Pyrex credited separately for UVHM discoveries. |
| BL4 Mod Manager | bl-sdk | LGPL3 | [Source](https://github.com/bl-sdk/oak2-mod-manager) | Required bundled runtime; bl-sdk contributors credited. |
| obj_dump | apple1417 | GPL3 | [Source](https://github.com/apple1417/oak-sdk-mods) | Documented research reference; apple1417 also credited for SDK foundation. |

## Validation and deployment

README links to contributor projects, current releases, notices and developer
documents. The existing `#credits` anchor is preserved for published/in-app links.
Local validation passed: relative links, author coverage, preserved credits anchor,
absence of image embeds, GitHub Markdown rendering, and `git diff --check`. No SDK behavior or license text is changed. No version bump or release.

README, central notices, this review and its snapshot are the documentation change
published to GitHub main on October 5, 2026.
The earlier desktop attribution edits remain a separate local change; they are
not included in the documentation publication or an installed build.

Rollback: revert the documentation commit only. Preserve the earlier desktop edits
and other untracked work in the native-cards-release worktree.
