### What's new

**v2.10.0**

- **Party Reveal Map** (Map Travel) — host-run station hop sweep (663 hops) so **guest** fog-of-discovery paints, including console. Abort stops the sweep. This is not a guest-process grid fill.
- **Host Clear Fog** — fills this machine’s discovery tiles (`GbxDiscoveryFODManagerCPU + 0xB0`). Instant for the **host**. Does not paint guests.
- **Hide Fog** — session overlay hide on **this client** (`MI_BigMapFogRipple`). Same as before; each player still applies it locally.
- **Dev Spawner hybrid** — catalog-wide live pawns: clone a matching OakCharacter when one is already in the world, otherwise FGbxDefPtr + OakSpawner + PushActorDef. Success means a pawn exists. **Attack Me** arms after spawn, including a delayed pawn recover (up to 8s) so combat is not applied before the actor is alive. Replace the `.sdkmod` for this — an older zip can spawn without attacking.
- **Late Join Character** (Boosting) — **experimental.** Opens Gearbox’s late-join picker on the **host** screen (990 pause `stateadd`, no pak). Player-2 character swap / Azalea-style persist is **not** confirmed in this build.
- **Infinite Jump** apply now actually arms `CanJump` (Off unregisters cleanly).
- Serial delivery no longer resizes the backpack as a side effect.

Instant Holds, Extreme Combat XP, and third-person were already in earlier releases.

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.10.0.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.10.0-win-x64.zip`

**Android (phone companion)**

Unchanged from v2.9.0. Same Mobile Controller **1.0.0** APK:

- Rolling APK: `MSBT-Mobile-Controller.apk`
- Versioned APK: `MSBT-Mobile-Controller-1.0.0.apk`
- Phone install page: https://www.funkyoushift.com/MattsSDKBoostingTools/mobile-install.html

**Do not manually download these unless you know why**

- `latest.json`, `latest.yml`, `mobile-version.json`, `*.blockmap`

### Upgrade notes

1. Install this desktop update (or extract the portable ZIP). You do **not** need a new phone APK.
2. Open Updates → **Install / Update SDK Mod** (or copy `MattsSDKBoostingTools.sdkmod` into `sdk_mods`). Hybrid spawn, fog buttons, and Late Join live in the SDK mod.
3. **Fully restart Borderlands 4** after replacing the `.sdkmod`.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
