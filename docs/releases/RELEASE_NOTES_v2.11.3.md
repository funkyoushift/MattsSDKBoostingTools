### What's fixed

- **XP / currency party targeting:** Give Cash / Eridium / Set Level / Max Player Level / Set Spec 701 / Max Cash / Max Eridium now resolve the boost-scope player the same way Max All does (party index first, name fallback) and fail closed when the grant does not apply.
- **BL4 Codes Send UX:** Confirm / Cancel stays in the panel (no `window.confirm`), Search keeps focus after confirm, and delivery is fire-and-forget so the Codes tab stays responsive.
- **Scoped boost soft-updates:** All / Other player loops avoid wiping Named Player dropdowns and BL4 Search focus mid-run (`pendingTarget` / `skipStatus`).

### Not in this release

MountGuard / spawn_track research, ASD hybrid combat unfinished work, guest-grid FoD experiments, and pending data-catalog scrapes.

### Upgrade notes

1. Install this desktop update (or extract the portable ZIP).
2. Open Updates → **Install / Update SDK Mod** (or copy `MattsSDKBoostingTools.sdkmod` into `sdk_mods`).
3. **Fully restart Borderlands 4** after replacing the `.sdkmod` — economy targeting lives in the SDK mod; BL4 Codes UX is in the desktop app.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).

### Download

- Windows installer: MSBT-Installer-v2.11.3.exe
- Windows portable: MSBT-Portable-v2.11.3-win-x64.zip
- SDK only: MattsSDKBoostingTools.sdkmod
- Android companion: MSBT-Mobile-Controller.apk (unchanged, v1.1.0)
