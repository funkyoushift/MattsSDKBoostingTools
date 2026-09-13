### What's new

- **Live player roster:** Boosting / inventory Named Player dropdowns refresh on join, leave, slot change, and reconnect without wiping BL4 Search focus; connection failures surface instead of a stale roster.
- **Inventory selection:** Highlights, counts, and details update without rebuilding item cards; multi-select / Select All / paging behavior is unchanged.
- **Native item cards:** Offline card layouts for weapons, shields, ordnance, repkits, enhancements, and class mods (saved inventory included). Class-mod skill ranks sum across repeated parts; oversized modded lists wrap inside the card.
- **Max All party indices:** Local / Named / Other / All send explicit player indices through Electron, bridge, and SDK; session fog runs once per batch.

### Limits

Exact in-game card parity is still incomplete (mixed-part names, some perk/red-text and numeric displays). Missing shield augment / grenade modifier values show a dash. Live multiplayer Max All unlock completion was not re-validated in this cut.

### Not in this release

MountGuard / spawn_track / bl4_mcp research, ASD hybrid combat unfinished work, and guest-grid FoD experiments.

### Upgrade notes

1. Install this desktop update (or extract the portable ZIP).
2. Open Updates → **Install / Update SDK Mod** (or copy `MattsSDKBoostingTools.sdkmod` into `sdk_mods`).
3. **Fully restart Borderlands 4** after replacing the `.sdkmod` — Max All routing lives in the SDK mod; inventory cards and roster UX are in the desktop app.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).

### Download

- Windows installer: MSBT-Installer-v2.11.4.exe
- Windows portable: MSBT-Portable-v2.11.4-win-x64.zip
- SDK only: MattsSDKBoostingTools.sdkmod
- Android companion: MSBT-Mobile-Controller.apk (unchanged, v1.1.0)
