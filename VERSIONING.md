# Versioning and GitHub Releases

Matt's SDK Boosting Tools uses Semantic Versioning for public Electron releases.

## Public Version Format

- Stable: `vMAJOR.MINOR.PATCH`
- Beta: `vMAJOR.MINOR.PATCH-beta.N`
- Alpha: `vMAJOR.MINOR.PATCH-alpha.N`

Examples:

- `v1.0.0`
- `v1.1.0`
- `v1.1.1-beta.1`

Do not use dates, commit hashes, workflow run IDs, or build timestamps as the primary public release version.

## Source of Truth

The Electron app version in `electron_poc/package.json` is the authoritative version for public Electron builds.

**Lockstep:** keep these aligned to the same SemVer when cutting a public release:

- `electron_poc/package.json` (+ lockfile)
- `mod_extracted/MattsSDKBoostingTools/__init__.py` (`__version__`)
- `mod_extracted/MattsSDKBoostingTools/pyproject.toml` (`version` / `[tool.sdkmod].version`)
- `releases/latest.json`
- `external_app/v22_parts_codes_fixed/resources/version_info.json` (packaged helper metadata)

Release scripts derive these values from that package version:

- Git tag: `v<package version>`
- Release title
- Installer filename
- Portable ZIP filename
- Electron `latest.yml` version check
- Release notes version

Build timestamps and commit SHAs may appear only as secondary build information.

## Release Titles

Use these title patterns:

- Stable: `Matt's SDK Boosting Tools v1.0.0`
- Beta: `Matt's SDK Boosting Tools v1.1.1 Beta 1`
- Alpha: `Matt's SDK Boosting Tools v1.1.1 Alpha 1`

## Asset Names

Use these Windows asset names:

- Installer: `MSBT-Installer-v1.0.0.exe`
- Portable ZIP: `MSBT-Portable-v1.0.0-win-x64.zip`

Electron updater metadata may remain named `latest.yml`, because that filename is expected by Electron tooling, but its contained `version` must match `electron_poc/package.json`.

## Download count badges

README and generated release notes show shields.io download badges for the **installer** and **portable ZIP** only (not `latest.json` / `latest.yml` / `.blockmap`).

When bumping the public version, update the versioned installer/portable filenames in the README badge URLs. Generated release notes (manual publisher + CI) include matching badges for that tag automatically.

**Do not** replace a published release body with a notes-only file (`gh release edit --notes-file` without the badge footer). That wipe already happened once on v2.1.0 — always keep the publisher/CI badge block.

## Safe Release Flow

1. Update `electron_poc/package.json` and `electron_poc/package-lock.json`.
2. Commit the version change and related release notes.
3. Build the SDK mod, Electron installer, and Electron portable ZIP with `.\build_electron_beta.ps1 -Installer`.
4. Create the semantic tag, for example `v1.0.0`.
5. Push the tag.
6. Publish assets with `.\publish_github_release.ps1`.

Do **not** rewrite `releases/latest.json` `git_commit` / compared metadata after the installer is built unless you also rebuild and re-upload the installer. Installed apps compare their bundled manifest to the remote `latest.json`; a post-release stamp (`pending` → real SHA) looks like a same-version rebuild and triggers a false update prompt. The publisher uploads the packaged `latest.json` so the release asset matches what users install.

The publisher refuses to publish when:

- The tag does not match `electron_poc/package.json`.
- The version is not valid public SemVer.
- The release title contains timestamp, run ID, or commit-hash naming.
- The installer, portable ZIP, or `latest.yml` is missing.
- `latest.yml` reports a different version.

## Existing Legacy Releases

Older releases used tags such as `beta-<commit>` and `electron-beta-v0.2.1`. Those tags should remain in place unless a deliberate updater-compatibility review says they are safe to rename or delete.

For old releases, prefer editing the visible release title and release notes instead of deleting or retagging. Keep a note explaining that the legacy tag remains for compatibility.
