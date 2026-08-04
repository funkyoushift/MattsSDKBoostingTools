# Release Metadata

This folder stores **small** release metadata tracked in source control — not installers.

## Keep in git

- `latest.json` — version manifest for the app updater
- `RELEASE_NOTES_v*.md` — human release notes (publisher/CI append download badges)
- `README.md` — this policy
- `discord_media/` — optional promo screenshots / Discord copy
- `QUICK_MENU_PREVIEW_NOTES.txt` — optional tester notes

## Do not commit here

- `MSBT-Installer-*.exe`
- `MSBT-Portable-*.zip`
- `*.blockmap`, packaged `latest.yml` copies
- Tester pack ZIPs / Electron-Patch staging (archive locally under `../_msbt_archive/` if needed)

Upload binaries to GitHub Releases only.

## Requirements

- Current builds need SDK 03 / [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3)
- Downloads: https://github.com/funkyoushift/MattsSDKBoostingTools/releases

## Badge warning

`publish_github_release.ps1` and CI inject installer/portable download badges into the release body.  
`gh release edit --notes-file …` with notes-only content **wipes** those badges — re-run the publisher or append the badge block again.

See [`VERSIONING.md`](../VERSIONING.md) and [`docs/BUILD_AND_PACKAGE.md`](../docs/BUILD_AND_PACKAGE.md).
