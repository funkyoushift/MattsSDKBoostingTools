### What's new

**v2.11.0** updates MSBT for Borderlands 4 v1.10 / installed build **25234898** and includes the completed license and attribution corrections.

- **Level 70 and Vault Card 5:** updated limits and selectors across the SDK, desktop panel, embedded editor, and Android companion. Native XP actions use the game's own level setters; offline Vault Card level edits preserve separately entered XP.
- **Loveless:** character/save identifiers, class mods, skill trees, cosmetic categories, and 130 native skill/tooltip/portrait images.
- **Current gear data:** 515 inventory roots and 7,417 compact parts, including 97 additional indexed gear compositions. This includes older recipes missing from the previous index as well as current update content.
- **Expanded world catalogs:** 6,682 actor entries, 699 item pools, 27 maps, and 1,231 travel stations. Existing curated entries are retained.
- **Challenges and shinies:** 3,286 challenge definitions, all six character challenge counter sets, 127 shiny serial variants, and 155 shiny item pools.
- **Catalog reliability:** older cached/online data cannot replace verified newer game catalogs. The first GZO refresh now displays the freshly downloaded results.
- **Runtime maintenance:** updated Electron and patched dependencies. The release dependency audit reports zero known vulnerabilities.

### License and credits

MSBT's original **MIT license** is restored, and the SDK metadata now agrees with it. Desktop, SDK, and Android packages carry the applicable full license texts and third-party notices, including the Mattmab/Galoob, Squ1ggs, Cr4nkSt4r, and glacierpiece contributions and bundled libraries.

Third-party code, catalog data, and game artwork retain their own licenses or permission terms. See [THIRD_PARTY_NOTICES.md](https://github.com/funkyoushift/MattsSDKBoostingTools/blob/v2.11.0/docs/THIRD_PARTY_NOTICES.md) for the source-to-file credits.

### Download and upgrade

- **Windows installer:** `MSBT-Installer-v2.11.0.exe`
- **Windows portable:** `MSBT-Portable-v2.11.0-win-x64.zip`
- **SDK only:** `MattsSDKBoostingTools.sdkmod`
- **Android companion 1.1.0:** `MSBT-Mobile-Controller.apk` (also supplied with a versioned filename)

1. Close Borderlands 4 before replacing the SDK mod.
2. Update the desktop app, then use **Updates → Install / Update SDK Mod**, or copy the SDK-only download into the game's `sdk_mods` directory.
3. Restart Borderlands 4. Phone users should install the new Android companion as well.
4. Requires [oak2 Mod Manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3). BLImGui remains optional; the native F7 Quick Menu and HTTP bridge are supported without it.

`latest.json`, `latest.yml`, `mobile-version.json`, and `.blockmap` files are updater metadata. `SHA256SUMS.txt` is provided for download verification.

### Verification and current limits

Game data was extracted from the installed update. Python/import checks, builder serialization checks, catalog hashes, Electron UI checks, Android compilation, and license-content checks accompany this release. The updated game loaded the SDK bridge without BLImGui and reported the new limits.

Individual actors, stations, and item combinations have not all been gameplay-tested. Some online GZO/Lootlemon preset serial lists still lag the game update; the newly imported gear definitions are available through the builder and item pools. Unfinished guest-grid, combat/aggro, and memory-spawning research is excluded from this release.
