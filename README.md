<!-- v2.39.2 mission replay and exact bookmarks -->

> **v2.39.2 — Mission replay and exact bookmarks.** Choose whole main objectives, including their travel and internal steps: 65 sections across 21 story missions and 61 sections across 18 supported DLC missions. Save an exact-position bookmark for a smaller practice point. Windows and the standalone SDK share this behavior. [Release notes](docs/releases/RELEASE_NOTES_v2.39.2.md).

> **Android 1.6.4** includes the matching mission interface. Update Windows to **2.39.2** as well; save files and backups stay on your PC. Replay requires a solo lobby and a second existing character. Generated encounters remain experimental.

This release combines selection and replay under **Mission replay**: choose a campaign, a numbered mission in dependency order, and its beginning or a main objective. Experimental generated progress edits now cover 39 story/DLC missions and 126 main sections, including missions not yet reached by the current character. They create prerequisite records, clear dependent future mission records and reload the selected state. Parallel branches are retained; numbering gives a stable playable order, not a unique chronology for those branches. Mudmouth and Ripper Queen retain their narrower live-tested setup path. Other generated states are progress overrides, not captured gameplay snapshots; completing earlier objectives does not reproduce every authored branch outcome, and world facts/encounters may need further fixes. These wider states have offline checks and still need live gameplay tests.

Save-backed replay is solo-host only. It backs up and edits the inactive original save, preserving equipment, levels and unrelated save data, then automatically reloads the character and mission map using a second existing loadable character in the same profile. DLC ownership is checked before setup. Generated states automatically place the host below the preceding main objective’s completion waypoint when its source coordinates and loaded collision are usable (79 coordinate candidates across 126 main sections). Missing or unsafe points retain the native respawn/fast-travel station, which may be farther from the selected objective. Coordinates retain their authored map and source pointer; individual gameplay starts remain experimental. Stop retains the backup; restoring it requires the original character to be unloaded and replaces its entire save with that earlier backup. Older live replay controls are under **Advanced live replay tools**.

**Mission-state bookmarks — experimental.** Stand on foot at the point you want to practice and save a bookmark. New bookmarks store your exact XYZ position and saved mission/world state, including smaller internal steps. Loading restores that timeline and position while keeping your current equipment and levels. Older bookmarks marked “spawn station” retain their original loading behavior. Bookmarks stay on this PC and require matching game/catalog data.

> **Mission tools remain experimental in v2.39.2.** Amber labels identify mission selection and bulk progress that may stop or leave NPCs, doors or encounters unready. Mission opening, selected-objective completion and native objective rewind have host test evidence; all-mission playability and guest save persistence are not verified. A finished full-game run does not guarantee saved 100% completion.

Mission tools now support one-objective advancement, authored checkpoint replay, mission reopening and campaign reset that retains character equipment and progression. Host save retention and opening NPC behavior were verified; guest-save and exhaustive world-effect coverage remain limited. See [v2.38.0 release notes](docs/releases/RELEASE_NOTES_v2.38.0.md).

# Borderlands 4 Modding Tools

**Powered by Funk · Built on the work of the Borderlands modding community**

This project brings community mods, discoveries, editors, and game tools together in a desktop app and an in-game control panel. It began with **Mattmab’s Matt’s SDK Boosting Tools** and continues through **FunkYouSHiFT’s** integration, development, maintenance, and testing.

**The original creators deserve credit for their work wherever we use it.** Bringing a mod into a different interface, adapting it to a newer SDK, or connecting it to another workflow does not make its underlying work ours. Their research, code, discoveries, and time remain their contributions. This project would not exist in its present form without them.

[Download the current release](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest) · [Getting started](#getting-started) · [Report a problem or missing credit](https://github.com/funkyoushift/MattsSDKBoostingTools/issues)

[![Installer downloads](https://img.shields.io/github/downloads/funkyoushift/MattsSDKBoostingTools/latest/MSBT-Installer-v2.39.2.exe?label=Download%20Windows%20installer&color=2ea44f)](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/MSBT-Installer-v2.39.2.exe)
[![Portable downloads](https://img.shields.io/github/downloads/funkyoushift/MattsSDKBoostingTools/latest/MSBT-Portable-v2.39.2-win-x64.zip?label=Download%20portable%20ZIP&color=0969da)](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/MSBT-Portable-v2.39.2-win-x64.zip)
[![Android APK downloads](https://img.shields.io/github/downloads/funkyoushift/MattsSDKBoostingTools/latest/MSBT-Mobile-Controller.apk?label=Download%20Android%20APK&color=e8a23a)](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/MSBT-Mobile-Controller.apk)

[Download the standalone Mission Selector SDK](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/BL4MissionSelector.sdkmod) · [Console menu and installation](standalone_mission_selector/README.md)

The standalone mod runs without the desktop app. Use it instead of the full MSBT SDK: move the full mod out of `sdk_mods` before installing the selector.

These counters track the installer, portable ZIP, and Android APK on the latest release, excluding updater metadata.

Steam and Epic support are included, including Epic account save handling. Replay requires a supported game build, solo hosting and a second existing loadable character in the same profile. Close the game before updating SDK components.

## Full-game completion with different DLC access

The run refreshes visitors’ real game access before starting. It retains the original bulk mission callbacks, completes available work, and reports blocked content without stopping the rest of the run. It does not grant DLC ownership. The three-player test included a visitor with only bounty packs: all stages finished or reported their specific limits, all three had 59/59 SDU upgrades verified, and both visitors confirmed story completion and UVHM 7. Native challenge readback found 2,574 complete, zero incomplete and 261 unavailable definitions; 60 current vault-card challenges were verified. Own-game save/rejoin verification remains separate.

Blocked DLC, absent definitions and unsupported cosmetic/vehicle unlocks remain visible. The broken teleporting fog-reveal tour is excluded. “Run finished” does not guarantee every collectible, achievement or saved 100% character. Android 1.6.4 includes the current mission interface and paired-PC replay/bookmark controls. Update the Windows app to 2.39.2 as well; saves and backups remain on the PC. Solo replay still requires a second existing character.

Earlier v2.36.0 testing confirmed saved completion for both visitors after a 200-mission run; see its [release notes](docs/releases/RELEASE_NOTES_v2.36.0.md). That historical result does not replace verification for the new replay workflow.

## v2.38.0 progress repairs

Scoped mission and discovery controls now share the 100% Game processing loop and connection recovery. Mission runs use the same dialogue skipping and guest challenge-credit checks. Other app or companion requests no longer cancel queued progress steps. Repair and continue keeps applied work; inactive vault cards and failed vehicle unlocks remain visible without blocking later stages.

The full preset retains its final pass for later unlocks. Scope selection, acceptance player and reset options still apply to individual runs. The reported **The Chase** guest-save issue remains unresolved; verify saved progress in each player's own game. Objective completion and mission/campaign replay controls are available for experimental testing; exhaustive playability and saved guest progress remain unverified.

Dialogue native-call research credit: [Yeti's Dialog Skipper](https://github.com/RedxYeti/yeti-bl4-sdk). [Release notes](docs/releases/RELEASE_NOTES_v2.38.0.md).

### Earlier repairs and saved guest progress

The v2.37.1 serial repair honors the copies setting for readable numeric codes and Quick Menu shortcuts, including repeated pasted codes. Reconfigure older pinned serial shortcuts to capture the corrected quantity.

The reported **The Chase** guest-save issue remains unresolved: a guest still had it active in their own save after targeted retests, including a fresh host. Save corruption was not established. Other guest batches passed own-game checks. Save and quit normally, check progress in each guest’s own game, and include the mission, objective and any fast-forward prompt when reporting an issue.

## Credits

### Community Discords

- [Funk’s Borderlands Trading Hub — FunkYouSHiFT](https://discord.gg/funksbth)
- [GZO — Mattmab and Ynot](https://discord.gg/wgjX48bksj)
- [Scooter’s Garage — Squ1ggs](https://discord.gg/sMUtqZG8Gt)
- [Azalea Asvail’s Modding World — Azalea’s branch of GZO](https://discord.gg/CV8bc6z32E)

### Mattmab / Matt / Galoob — the original foundation and editor

Mattmab created the original MSBT toolset and its in-game menu. His code remains part of our player economy and boosting, serial conversion and reward delivery, movement, inventory capacity, party helpers, travel, item-pool spawning, shiny spawning, and developer tools. Our Python Legit Builder and external serial helpers also build on his implementations. This is a substantial part of the project's foundation: moving these tools into new interfaces would not have been possible in the same form without the systems Matt built and shared.

Matt’s save/item editor and portable Legit Builder supplied the editor foundation, including retained interface styles, item parsing, part selection, data loading, and editor tabs. We also credit his challenge-path discoveries. The external control app and game bridge were developed by FunkYouSHiFT’s project; we later adopted Electron to match Matt’s editor.

The **Actor Script Deployer** bundled with this project is **Matt’s spawning implementation**, including actor creation, spawn placement and spacing, actor tracking, and cleanup. Our Dev Spawner controls and subsequent fixes build around that work. Its contribution deserves explicit recognition alongside the visible interface.

**Explore his work:** [Original MSBT](https://github.com/mattmab/MattsSDKBoostingTools) · [Legit Builder](https://github.com/mattmab/legit-builder) · [Bundled Actor Script Deployer and author metadata](tools/third_party/sdk_mods/ActorScriptDeployer/pyproject.toml)

### RDP / Squ1ggs — targeting, teleport, tuning, and spawn-helper additions

Squ1ggs’ public mods and SDK research informed later additions for Local / All / Others player targeting, player-to-player teleport, combat/resource tuning, and vehicle tuning. His mob-spawner code also supplied references for the later nearest-NPC anchor selection and re-aggro controls around Matt’s ASD backend. This credit covers those additional helpers and references, not ASD’s spawning, placement, tracking, or cleanup. GZO, Lootlemon, and Nexus data retain their separate source credits.

Our challenge-category filtering and non-UVHM completion behavior also used SQBT as a reference. Squ1ggs’ published implementations gave us concrete examples for expanding these controls and working with the SDK. We value the research, testing, and shared code behind those contributions, and credit both adapted material and documented inspiration.

**Explore his work:** [Public mods and source](https://github.com/Squ1ggs/Bl4SDKmods) · [Player Movement](https://github.com/Squ1ggs/Bl4SDKmods/tree/main/bl4_player_movement) · [P2P Teleporter](https://github.com/Squ1ggs/Bl4SDKmods/tree/main/p2p_teleporter) · [Damage & More](https://github.com/Squ1ggs/Bl4SDKmods/tree/main/damage_and_more) · [Resources & Cooldowns](https://github.com/Squ1ggs/Bl4SDKmods/tree/main/resources_and_cooldowns) · [Vehicle Movement](https://github.com/Squ1ggs/Bl4SDKmods/tree/main/vehicle_movement) · [World Travel](https://github.com/Squ1ggs/Bl4SDKmods/tree/main/world_travel) · [Borderlands Mob Spawner](https://github.com/Squ1ggs/Bl4SDKmods/tree/main/mob_spawner)

**Implementation references:** [MSBT's later helper additions](https://github.com/funkyoushift/MattsSDKBoostingTools/commit/a956860) · [Challenge filtering](mod_extracted/MattsSDKBoostingTools/backend_actions.py)

### Azalea Asvail / Azzy — UVH boosting and native-menu inspiration

Azalea developed the **Azzy UVH Booster** workflow adapted into our boosting tools. Her native in-game interface also inspired the Quick Menu’s move, resize, and theme controls. Those are meaningful contributions to both what the tools do and how players use them.

FunkYouSHiFT assisted with the UVHM work, but Azalea’s workflow and interface contributions remain hers. Thank you for developing and sharing them.

**Explore her work:** [Azzy UVH Booster — project, source, and downloads](https://github.com/AzaleaAsvailAMW/amw-Uvhbooster)

**Documented in our source:** [UVH workflow credit](mod_extracted/MattsSDKBoostingTools/backend_actions.py) · [Quick Menu inspiration](mod_extracted/MattsSDKBoostingTools/quick_menu.py)

### PyrexBLJ / Pyrex — Bonk Utilities and UVHM discoveries

Pyrex created **Bonk Utilities**, a gameplay-utility reference for god/demigod mode, noclip, time controls, no-target, ground-item cleanup, and developer-perk actions. Publishing those controls made useful game and SDK behavior available for other modders to study. We acknowledge that utility work separately from his earlier UVHM-path discoveries used by the boosting workflow. Azalea’s public project also acknowledges Pyrex.

**Explore his work:** [Bonk Utilities — source](https://github.com/PyrexBLJ/BL4-SDK-Mods/tree/main/BonkUtilities) · [Bonk Utilities — mod listing](https://bl-sdk.github.io/oak2-mod-db/mods/bonkutilities/) · [Pyrex’s BL4 SDK mods](https://github.com/PyrexBLJ/BL4-SDK-Mods). These acknowledgments do not mean every mod in his repository is bundled here.

### apple1417, Faultz, and the BL SDK contributors — the runtime that makes this possible

The game-side tools depend on the **BL SDK ecosystem**, including oak2 Mod Manager, pyunrealsdk, and unrealsdk. apple1417’s work, alongside Faultz and the wider SDK contributors, makes it possible to load mods and interact with Borderlands 4 from Python. That infrastructure is a foundation of this project, not something MSBT created.

Thank you for the SDK, maintenance, documentation, and tools that make community modding possible.

**Explore their work:** [apple1417](https://github.com/apple1417) · [oak2 Mod Manager and contributors](https://github.com/bl-sdk/oak2-mod-manager) · [pyunrealsdk](https://github.com/bl-sdk/pyunrealsdk) · [unrealsdk](https://github.com/bl-sdk/unrealsdk) · [BL4 SDK Mod Database](https://bl-sdk.github.io/oak2-mod-db/)

### Renil / cnrenil — third-person camera

Our third-person camera integration includes Renil’s **Third Person Camera SDK** controller. The distributed archive used by the project also credits **Epilow**, whose credit we retain. The camera work belongs to its creators; MSBT provides the surrounding integration and controls.

**Explore the original mod:** [Third Person Camera SDK](https://www.nexusmods.com/borderlands4/mods/259)

### glacierpiece — save encryption and decryption

The save/profile encryption wrapper used through Mattmab’s editor was adapted from **glacierpiece’s Borderlands 4 Save Utility**. That work enables saves to be decoded and encoded for editing and belongs to its original author.

**Explore the project:** [Borderlands 4 Save Utility](https://github.com/glacierpiece/borderlands-4-save-utility)

### Cr4nkSt4r / Dominic — NCS tooling and supplied data

Cr4nkSt4r’s **NcsParser** work and previously supplied Nexus tables contributed to the editor’s data foundation. Retained supplied data and overrides keep their attribution. Current locally extracted game tables are separately identified as game-derived data; the extraction tool is not claimed as our work.

**Explore the project:** [Borderlands-4.NcsParser](https://github.com/Cr4nkSt4r/Borderlands-4.NcsParser)

### Ynot / GZO and Levin / Lootlemon — item knowledge and catalogs

**Ynot / GZO** supplies community item-code resources, catalogs, part maps, and linked images used by our browsing workflows. **Levin / Lootlemon** supplies item information, code references, and links used in the catalog. Their research and ongoing curation make those workflows useful. Displaying their information inside this app does not make it our data.

**Visit the original resources:** [GZO Borderlands 4 Codes](https://save-editor.be/GZO/Borderlands4/Codes.html) · [GZO hub](https://save-editor.be/GZO/) · [Lootlemon](https://www.lootlemon.com/)

### juso and smugg — BLImGui / Borderlands ImGui

**juso and smugg** created **BLImGui**, the framework used by the earlier in-game interface. Their work gave SDK modders a way to build graphical controls and is part of this project’s history. The current desktop app and native F7 Quick Menu do not require BLImGui, but moving to a new interface does not erase that contribution.

**Explore their work:** [BLImGui source](https://github.com/juso40/blimgui) · [Published BL4 listing and author credits](https://bl-sdk.github.io/oak2-mod-db/mods/blimgui/)

### Research references and the wider modding community

Our research notes acknowledge **Yeti’s** Dump Ping, Falling Menus, and Grapple Anywhere, **FreepDryer’s** Trash Seller, and **apple1417’s** obj_dump as references studied during development. We thank these authors for publishing their work. This acknowledgment describes research references; it does not claim that their implementations are bundled in MSBT.

**Explore their work:** [Yeti’s BL4 SDK mods](https://github.com/RedxYeti/yeti-bl4-sdk) · [FreepDryer’s BL4 SDK mods](https://github.com/FreepDryer/freepdryer-bl4-sdk-mods) · [apple1417’s SDK mods](https://github.com/apple1417/oak-sdk-mods) · [Browse the BL4 SDK Mod Database](https://bl-sdk.github.io/oak2-mod-db/)

### Framework maintainers, testers, and community creators

We also thank the maintainers of **Electron, Chromium, Python, GridStack, js-yaml, pako, Monaco, AndroidX, and ZXing**, whose software supports the desktop, editor, and mobile tools. Their notices remain separate from our project license.

**Azzarock, Frag Em All, Tobgun1, Crayons82.0**, and the wider testing community have contributed testing, reports, feedback, and item data. Save creators, build authors, item-code contributors, and community-library authors deserve credit for their individual submissions as well; sharing or importing their work does not transfer authorship to MSBT.

## Our role and our responsibility

To address frame drops with the original in-game menu, we moved the mod’s controls outside the game. We designed our own bridge and built an external app. We later moved that app to Electron to match Matt’s editor. That desktop interface and bridge were our development work.

FunkYouSHiFT maintains this version of the project. Our work includes bringing components together, building desktop and mobile workflows, updating integrations for SDK changes, improving reliability, testing, and packaging. That work sits alongside the original creators’ contributions. It does not replace them.

We aim to name the creator, explain the contribution, link to the original work, and preserve the applicable notices. Credit for a discovery, copied or adapted implementation, interface inspiration, and later integration should remain distinct. Where the history is unresolved, we should investigate it rather than assign ownership by assumption.

If we have missed you or described your contribution incorrectly, please [open an attribution issue](https://github.com/funkyoushift/MattsSDKBoostingTools/issues) with the relevant feature or source. We want the record to be accurate, useful, and respectful.

[Third-party notices and permissions](docs/THIRD_PARTY_NOTICES.txt)

## Getting started

1. Back up your saves before using save-editing or boosting tools.
2. Open the [latest release](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest) and choose the Windows installer or portable ZIP. The release page explains what changed and includes the download links. Files such as `latest.json`, `latest.yml`, and `.blockmap` are updater metadata.
3. Follow the release’s installation instructions. Close Borderlands 4 before installing or updating the game-side components.
4. Launch the game with the SDK loaded, then open the desktop app and connect to the game. **F7** opens the native in-game Quick Menu.

The toolkit includes boosting, item and serial workflows, save/editor tools, inventory browsing, movement, travel, spawning, AFK lobby controls, and an Android companion. Feature availability depends on the installed version and game compatibility.

## Development and license

[Desktop source](electron_poc/) · [SDK source](mod_extracted/MattsSDKBoostingTools/) · [Build tools](tools/)

Original project code is covered by [LICENSE](LICENSE). Bundled and adapted code, data, libraries, and artwork retain their respective licenses or permissions; see [Third-party notices](docs/THIRD_PARTY_NOTICES.txt). Credit is not a substitute for those terms.

Borderlands and its game assets belong to Gearbox / 2K and their respective owners. This is an unofficial community project and is not affiliated with or endorsed by them.


## Serial quantity repair — v2.38.0

Give Items by Serial now honors the copies setting for readable numeric codes and Quick Menu shortcuts. Repeated pasted codes retain their requested quantity.

## 100% game preset — v2.37.0
Open **Missions → 100% game** in the desktop app. Check lobby access, review the shared-progress acknowledgement, then run supported missions, discoveries/travel requirements, character levels, currencies, SDU points, applicable unlocks, UVH/Mayhem and challenges. Host plus one guest can use available content; larger lobbies require everyone to have the required DLC access.

The final prerequisite pass picks up newly available missions and travel requirements without resetting verified work. Missing DLC, unavailable definitions and inactive vault cards are reported separately. This preset purchases authored SDU ranks and verifies their native readback. It does not promise every item/statistic/achievement. Save and quit normally and verify guests in their own games. See [v2.37.0 release notes](docs/releases/RELEASE_NOTES_v2.37.0.md) for limitations and recovery controls.

### v2.37.0 guest mission persistence limitation

The 100% game preset can report shared-lobby completion while a guest still has a mission active in their own save. The Chase remained unfinished for one tested guest after several targeted retests, including a fresh host. The cause is unresolved; save corruption has not been established. Other guest batches have passed own-game checks. Save and quit, check each guest in their own game, and report the mission, objective and any fast-forward prompt.
