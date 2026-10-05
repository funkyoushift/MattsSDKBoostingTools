# Borderlands 4 Modding Tools

**Powered by Funk · Built on the work of the Borderlands modding community**

This project brings community mods, discoveries, editors, and game tools together in a desktop app and an in-game control panel. It began with **Mattmab’s Matt’s SDK Boosting Tools** and continues through **FunkYouSHiFT’s** integration, development, maintenance, and testing.

**The original creators deserve credit for their work wherever we use it.** Bringing a mod into a different interface, adapting it to a newer SDK, or connecting it to another workflow does not make its underlying work ours. Their research, code, discoveries, and time remain their contributions. This project would not exist in its present form without them.

[Download the current release](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest) · [Getting started](#getting-started) · [Report a problem or missing credit](https://github.com/funkyoushift/MattsSDKBoostingTools/issues)

[![Installer downloads](https://img.shields.io/github/downloads/funkyoushift/MattsSDKBoostingTools/latest/MSBT-Installer-v2.30.0.exe?label=Download%20Windows%20installer&color=2ea44f)](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/MSBT-Installer-v2.30.0.exe)
[![Portable downloads](https://img.shields.io/github/downloads/funkyoushift/MattsSDKBoostingTools/latest/MSBT-Portable-v2.30.0-win-x64.zip?label=Download%20portable%20ZIP&color=0969da)](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/MSBT-Portable-v2.30.0-win-x64.zip)
[![Android APK downloads](https://img.shields.io/github/downloads/funkyoushift/MattsSDKBoostingTools/latest/MSBT-Mobile-Controller.apk?label=Download%20Android%20APK&color=e8a23a)](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/MSBT-Mobile-Controller.apk)

These counters track the installer, portable ZIP, and Android APK on the latest release, excluding updater metadata.

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
