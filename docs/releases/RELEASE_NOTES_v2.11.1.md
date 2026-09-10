### What's new

**MSBT v2.11.1** completes the built-in editor update for Borderlands 4 v1.10 / game build **25234898**.

- **Loveless cosmetics and skills:** all 127 cosmetic IDs resolve to the correct character, including nine previously missed heads/skins. Skill lookups now resolve case differences and shared native references, covering 565 passive metadata entries.
- **Current gear selectors:** Loveless and C4SH class mods stay in class-mod categories. All item views use the current catalog badges for 774 newly indexed serial IDs; some entries are older content previously missing from the index.
- **Level 70 defaults:** Black Market fields use the current item cap while retaining explicitly chosen lower levels.
- **Save XP controls:** character/specialization level changes and max presets preserve saved XP. Separate point fields allow deliberate XP edits, including zero.
- **Providence and Bounty Pack 5:** updated mission grouping and dedicated completion/reset controls for the new regions.
- **Parser and package maintenance:** js-yaml 4.3.2, complete third-party notices, stable native-data/vendor hashes, and published catalog bytes that match their existing checksum manifest.

The six characters, five Vault Cards, 515 inventory roots, 7,417 parts, 130 Loveless images, and expanded world catalogs from v2.11.0 remain included. MSBT and SDK versions are aligned at 2.11.1; Android remains 1.1.0.

### Download and upgrade

- **Windows installer:** `MSBT-Installer-v2.11.1.exe`
- **Windows portable:** `MSBT-Portable-v2.11.1-win-x64.zip`
- **SDK only:** `MattsSDKBoostingTools.sdkmod`
- **Android companion:** `MSBT-Mobile-Controller.apk` (unchanged version 1.1.0)

Close MSBT before replacing a portable installation. Close Borderlands 4 before replacing the SDK mod, then restart the game. Requires [oak2 Mod Manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).

The **UVH 1–7** panel remains under **Boosting**, with **Run All 1–7**. If hidden by a saved layout, enable it from **View → Panels**. The native F7 Quick Menu and optional BLImGui fallback remain available.

### Verification and data limits

Editor regressions cover synthetic save/profile round trips, the full Electron editor page, native catalogs, all 130 icon hashes, level/XP preservation and scoped mission actions. Release checks cover Python imports, SDK packaging, Windows installer/portable contents, licenses and updater checksums.

Exact native XP threshold evaluation remains unverified, so the offline editor preserves XP instead of writing an estimated curve. All 19 Providence mission sets are recognized; 16 have static completion templates. The remaining three support grouping/reset without invented dynamic mission trees. Individual item combinations and mission transitions have not all been gameplay-tested.

MSBT's MIT license and the applicable third-party licenses and game-data credits are retained. See [THIRD_PARTY_NOTICES.md](https://github.com/funkyoushift/MattsSDKBoostingTools/blob/v2.11.1/docs/THIRD_PARTY_NOTICES.md). Matt's standalone editor repository remains on its separate approval path.

`latest.json`, `latest.yml`, `mobile-version.json`, and `.blockmap` files are updater metadata. `SHA256SUMS.txt` provides download checksums.
