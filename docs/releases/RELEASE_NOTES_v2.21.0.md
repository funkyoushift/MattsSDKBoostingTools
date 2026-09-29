# Borderlands 4 Modding Tools v2.21.0 — Powered by Funk

## What changed

- New public desktop, installer, SDK and Android branding, with Mattmab retained as the original project's creator. Existing settings and update/install identities stay compatible.
- Remote AFK restores the existing pairing at startup, reconnects after interruptions, and renews its relay registration. Closing the window keeps enabled access in the tray; Windows sign-in restores it. The PC and game must stay running. Android retries status without replaying uncertain actions.
- Windows-reserved or occupied bridge ports now fall back automatically. Desktop, phone, LAN gateway and SHiFT AFK controls discover the endpoint and verify it before sending actions.
- Repairs missing packaged QR/updater dependencies from v2.20.0. Builds now verify the dependency graph and bundled assets inside the actual package.
- Android v1.4.3 (code 30), installed over the existing app with the same signing identity and data.

## Install or update

Use **MSBT-Setup.exe** for the reusable setup, **MSBT-Installer-v2.21.0.exe** for the Windows installer, or **MSBT-Portable-v2.21.0-win-x64.zip** for portable use. Choose one Windows installation method.

Android: install **MSBT-Mobile-Controller.apk** over the existing app. The versioned APK contains the same build. No uninstall is needed.

Fully exit Borderlands 4 before updating the SDK/SHiFT files, then launch it normally. Keep oak2-mod-manager v0.3 installed. Existing remote pairing should continue working; full phone controls use LAN, while Remote AFK works over cellular or another network.

The historical MSBT repository/asset names, app IDs, SDK module, bridge commands, settings, and website paths remain stable for compatibility. Original project: **Mattmab**; maintained by **FunkYouSHiFT**.

## Validation

Martin confirmed the locally installed desktop, Android and game candidate works. Automated bridge/reconnect/security-scope checks, settings restart tests, mobile UI checks, Windows/Android builds, and packaged dependency/asset audits passed. Live hosted relay tests used a simulated bridge; no broader gameplay compatibility is implied.
