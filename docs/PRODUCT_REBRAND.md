# Product branding and compatibility

Public identity: **Borderlands 4 Modding Tools — Powered by Funk**.
Original project and editor: **Mattmab (Matt)**. FunkYouSHiFT maintains this project.

This change continues the six public-branding commits ending at `1480604`.
The initial local review used desktop/SDK `2.20.0` and Android `1.4.2` (29).
The approved public release is desktop/SDK `2.21.0` and Android `1.4.3` (30);
the release asset contract is unchanged.

## Display changes

- Electron product metadata, window/document title, About metadata, header, sidebar,
  support/onboarding/mobile instructions, and selected dialogs use the new name.
  The desktop header retains the existing Powered by Funk mark and now explicitly
  credits Mattmab. Compact labels may use Borderlands 4 Modding Tools.
- Android launcher label, header, About copy, update/pairing instructions and support
  copy are branded; the header wraps on narrow screens and keeps Powered by Funk visible.
- NSIS product/shortcut names and installer messages are branded. The reusable
  setup window, status text, product metadata and uninstall DisplayName are branded.
- Persistent setup creates the new shortcut and removes a legacy shortcut only if
  its target matches this installation's executable. Uninstall checks both names
  using the same ownership check. Links targeting other installations survive cleanup.
- SDK mod-manager display name, author credit, description, Quick Menu heading and
  keybind display labels are branded. Keybind identifiers and command names are stable.
- The hosted mobile install page source is branded without changing its address.

## Identifiers deliberately retained

| Area | Retained contract |
| --- | --- |
| GitHub | `funkyoushift/MattsSDKBoostingTools`, all updater repository targets |
| Electron | package name `matts-sdk-boosting-tools`, app ID `com.funkyoushift.msbt`, `MattsSDKBoostingTools.exe` |
| Desktop data | Existing `userData` and `sessionData`, saved JSON filenames, localStorage keys, cached catalogs, pairing secrets and `persist:msbt-developer-portal` |
| NSIS | Existing app-ID-derived GUID/registry identity, per-machine behavior and installation directory |
| Persistent installer | `%LOCALAPPDATA%/Programs/MSBT`, `MSBTPersistent` uninstall key, `.msbt-managed`, setup/cache/state filenames |
| Downloads | `MSBT-Setup.exe`, `MSBT-Installer-v<VERSION>.exe`, `MSBT-Portable-v<VERSION>-win-x64.zip`, APK names and `latest.yml` contract |
| Android | `com.funkyoushift.msbt.mobile`, Java namespace, SharedPreferences, WebView storage, JavaScript bridge and file-provider authority |
| SDK | `MattsSDKBoostingTools` project/module/folder, `MattsSDKBoostingTools.sdkmod`, settings filenames, keybind identifiers and `msbt_*` commands |
| Network | Ports, routes, `X-MSBT-*` headers, QR formats, protocol fields, User-Agent values and environment-variable names |
| Web | Existing `/MattsSDKBoostingTools/` paths, download URLs, image filenames and analytics keys |
| Diagnostics/history | MSBT log tags, diagnostic fields, backup/report filenames, historical release notes, licenses and original-project attribution |

Diagnostic and SDK-identifier references to MSBT remain in some technical UI copy.
The optional in-game logo's existing MSBT default, older screenshots, archived legacy
Tkinter UI and optional legacy BLImGui UI are not broadly rewritten by this change.
These are separate from the current desktop/mobile product title.

## Why existing data survives

Electron's runtime package name is unchanged. `product_identity.js` captures the
existing userData and sessionData paths before setting the display name, then pins
those same paths. Explicit caller/test profile overrides are respected. No data is
copied, moved, reset or migrated to a new namespace.

The installed electron-builder 26.15.3 implementation was inspected and exercised:
both old and new product names resolve to the same Windows installation-directory
name, `matts-sdk-boosting-tools`. The app ID is unchanged, so the NSIS GUID stays stable.
NSIS already records the prior shortcut name and handles renamed shortcuts on update;
the separate persistent installer needs its explicit target-checked legacy cleanup.

The actual bundled oak2 v0.3 `mods_base.sdkmod` was inspected: default settings paths
derive from `module.__name__`, not the display name. That module name is unchanged.

Old cached/remote tutorial overlays still contain `Welcome to MSBT`. The overlay
adapters translate that known heading at display time. The published data-channel
manifest, hashes, URLs and payload remain untouched.

## Validation and release boundary

Run `npm run check`, `npm run test:settings`, `npm run test:persistent-updater` and
`npm run test:mobile-parity` in electron_poc. The product-identity regression checks
are part of `npm run check`. The mobile parity screenshot test expects
`output/reported-issues` to exist in a fresh checkout.

`tools/build_electron_beta.ps1 -Installer` builds the SDK archive, persistent setup,
NSIS installer and portable package without publishing. `installer/Tests.cs` includes
real disposable Windows shell-link ownership tests without touching desktop shortcuts
or registry entries. Android builds through Gradle `:app:assembleDebug`.

Before shipping, Martin should validate old-to-new NSIS and persistent installs
separately on a disposable Windows account/VM; confirm the existing install directory,
one uninstall entry, renamed shortcuts, settings/bookmarks/pairing/portal storage and
uninstall preservation. Check 100%, 150% and 200% display scaling.

Install the Android candidate over the prior APK using the **same signing certificate**;
verify pairing, bookmarks, WebView data, launcher label and About view. A local debug
build alone does not prove release signing or upgrade continuity.

With game backups and the game closed, install the candidate SDK archive, then verify
mod-manager branding, F7 title/layout, retained binds/settings, desktop connection,
mobile pairing and representative bridge actions in Borderlands 4.

Local same-version builds are validation artifacts. The reusable setup still fetches
the currently published stable release, so running it does not select unpublished local
rebrand artifacts. End-to-end updater delivery needs an approved release with a new
version and matching assets/hashes; no such release is made by this source change.
