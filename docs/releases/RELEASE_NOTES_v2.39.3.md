# v2.39.3 — Phone pairing repair

Android **1.6.5** fixes Save Setup discarding Remote AFK credentials and leaving the remote label as an invalid computer address.

- Saving a remote setup now keeps its credentials. Manual LAN fields stay disabled while remote pairing is active; scan a local pairing QR to switch connection type.
- If an older setup already lost its remote credentials, the phone asks you to scan the Remote AFK QR again instead of searching invalid addresses and ports. In Windows, open **App & Tools → Mobile Pairing** and scan the upper **Remote AFK** QR.
- The repaired local APK reconnected on Martin's phone after a fresh QR scan. Page tests cover saving, reloading and choosing the correct remote transport. Android build/lint and coordinated package checks are recorded in the verification receipt.

Windows/full SDK and standalone SDK are versioned **2.39.3** to keep release and update metadata aligned. Mission behavior is unchanged from [v2.39.2](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/v2.39.2): whole main-objective sections, exact-position bookmarks and the standalone console menu remain included. Generated mission encounters remain experimental.

## Downloads

- **Windows:** `MSBT-Installer-v2.39.3.exe`, or `MSBT-Portable-v2.39.3-win-x64.zip`. `MSBT-Setup.exe` is the reusable installer.
- **Android:** `MSBT-Mobile-Controller.apk` or the identical `MSBT-Mobile-Controller-1.6.5.apk`.
- **Standalone selector:** `BL4MissionSelector.sdkmod` and its included README. Use this instead of the full MSBT SDK, not alongside it; the standalone has no phone bridge.
- **Full app SDK:** `MattsSDKBoostingTools.sdkmod`, also bundled with Windows. Phone game controls require the full SDK and running game.

Existing damaged pairing needs a fresh QR scan once; an app update cannot reconstruct credentials already discarded. Updating in place preserves valid pairing. Close the game before replacing SDK files. See the README and previous release notes for mission requirements, contributor credits and limitations.
