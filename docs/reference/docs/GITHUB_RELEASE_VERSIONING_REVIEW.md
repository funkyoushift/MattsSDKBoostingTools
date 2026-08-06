# GitHub Release Versioning Review

Audit date: 2026-07-13

Repository: `funkyoushift/MattsSDKBoostingTools`

## Summary

The live GitHub Releases page currently mixes legacy commit-based tags with Electron package versions. The latest public Electron installer reports application version `0.2.2`, but its release tag and title use `beta-6489711`.

Because `0.2.2` has already shipped, the next SemVer beta must not be `0.2.2-beta.1`; that would be considered older than `0.2.2` by normal SemVer ordering. The next safe beta version is `0.2.3-beta.1`.

## Existing Releases

| Current tag | Current title | App version evidence | Assets | Commit | Type | Proposed title | Proposed tag action | Asset action | Updater risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `beta-6489711` | `MSBT External Beta beta-6489711` | Electron `latest.yml` says `0.2.2`; installer name says `0.2.2` | `MattsSDKBoostingTools-Electron-Beta-Installer-0.2.2-x64.exe`, blockmap, `latest.yml`, `MSBT_External_Beta.zip` | `768dc37` | Current Electron beta plus legacy ZIP | `Matt's SDK Boosting Tools v0.2.2 Beta 1` | Keep legacy tag for compatibility | Keep existing assets; future assets use SemVer names | High if tag or filenames are changed; existing downloads/updater may reference them |
| `electron-beta-v0.2.1` | `MSBT Electron Beta v0.2.1` | Electron package at tag says `0.2.1`; `latest.yml` says `0.2.1` | `MSBT-Electron-Beta-0.2.1-x64.exe`, blockmap, `latest.yml` | `2e8d4cd` | Electron beta | `Matt's SDK Boosting Tools v0.2.1 Beta 1` | Keep legacy tag | Keep existing assets | Medium if tag or filenames are changed |
| `beta-a5e02fc` | `MSBT External Beta beta-a5e02fc` | Electron package at tag says `0.1.0`; release asset is legacy ZIP only | `MSBT_External_Beta.zip` | `f37214e` | Legacy/Tkinter beta with Electron source present | `Matt's SDK Boosting Tools Legacy Tkinter Beta beta-a5e02fc` | Keep legacy tag | Keep existing asset | Low for Electron updater; medium for users with old links |
| `beta-6c35268` | `Release title: MSBT External Beta beta-6c35268` | Electron package at tag says `0.1.0`; release asset is legacy ZIP only | `MSBT_External_Beta.zip` | `43994d9` | Early Electron proof-of-concept source plus legacy ZIP | `Matt's SDK Boosting Tools Legacy Tkinter Beta beta-6c35268` | Keep legacy tag | Keep existing asset | Low for Electron updater; medium for users with old links |
| `beta-latest` | `MSBT External Beta` | No Electron package at tag | `MSBT_External_Beta.zip` | `4e23ced` | Old legacy/Tkinter beta | `Matt's SDK Boosting Tools Legacy Tkinter Beta beta-latest` | Keep legacy tag | Keep existing asset | Low for Electron updater; medium for old download links |

## Non-Destructive Corrections

Safe corrections:

- Update visible release titles.
- Update release notes/descriptions to explain legacy tags.
- Keep old tags and old asset names.
- Mark future public Electron builds with SemVer tags and clean asset names.

Applied on 2026-07-13:

- `beta-6489711` title changed to `Matt's SDK Boosting Tools v0.2.2 Beta 1`.
- `electron-beta-v0.2.1` title changed to `Matt's SDK Boosting Tools v0.2.1 Beta 1`.
- `beta-a5e02fc` title changed to `Matt's SDK Boosting Tools Legacy Tkinter Beta beta-a5e02fc`.
- `beta-6c35268` title changed to `Matt's SDK Boosting Tools Legacy Tkinter Beta beta-6c35268`.
- `beta-latest` title changed to `Matt's SDK Boosting Tools Legacy Tkinter Beta beta-latest`.
- Release descriptions were updated to explain which asset to download and why the legacy tags remain.
- No tags, assets, release flags, or binaries were renamed, deleted, or replaced.

Corrections requiring explicit approval:

- Delete old releases.
- Rename or delete old tags.
- Replace existing assets with differently named assets.
- Change prerelease/latest flags if doing so would break `/releases/latest/download/...` links or Electron updater behavior.

## Current Local Build Rule

The local Electron package has been moved forward to `0.2.3-beta.1` for the next public beta. This preserves update ordering after the already-shipped `0.2.2` build.
