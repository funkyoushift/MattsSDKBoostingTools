### What's new

**v2.9.1**

- **Matt Editor no longer collides with Mobile Gateway.** The editor host prefers port **49776** and never binds **49775**. Opening Mobile Gateway first used to leave Chromium’s Pretty-print JSON viewer in the Matt Editor iframe.
- Electron refuses to load a JSON URL into that iframe and shows a visible load-error status on the Matt Editor tab if the host is wrong.

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.9.1.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.9.1-win-x64.zip`

**Android (phone companion)**

Unchanged from v2.9.0. Same Mobile Controller **1.0.0** APK:

- Rolling APK: `MSBT-Mobile-Controller.apk`
- Versioned APK: `MSBT-Mobile-Controller-1.0.0.apk`
- Phone install page: https://www.funkyoushift.com/MattsSDKBoostingTools/mobile-install.html

**Do not manually download these unless you know why**

- `latest.json`, `latest.yml`, `mobile-version.json`, `*.blockmap`

### Upgrade notes

1. Install this desktop update (or extract the portable ZIP). You do **not** need a new phone APK.
2. Open Updates → **Install / Update SDK Mod** if you want the matching `.sdkmod`, or copy it into `sdk_mods`.
3. A full Borderlands 4 restart is only needed if you update the SDK mod.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
