### What's fixed

- **Safe self item delivery:** sending serial items to yourself now uses the local reward route instead of GiveRewardAllPlayers. This prevents the Borderlands 4 v1.10 loyalty-reward side effects that could add XP, cash, and unrelated rewards during a self-send.
- **Non-combat XP protection:** item delivery and currency grants update the Combat XP baseline, so they cannot be multiplied when Combat XP is enabled.
- **Idle performance cleanup:** camera dispatch and bridge discovery no longer run continuously while unused.

### Upgrade notes

Close Borderlands 4 before replacing the SDK mod, then restart the game. Self-sends should show GiveReward OK in the SDK log; remote and party delivery continue to use the all-player route required for replication.

### Download

- Windows installer: MSBT-Installer-v2.11.2.exe
- Windows portable: MSBT-Portable-v2.11.2-win-x64.zip
- SDK only: MattsSDKBoostingTools.sdkmod
- Android companion: MSBT-Mobile-Controller.apk (unchanged, v1.1.0)

Requires [oak2 Mod Manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
