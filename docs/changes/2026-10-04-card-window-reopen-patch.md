# Item-card helper window reopening fix — v2.29.1

The final v2.29.0 handoff using Matt's regular profile exposed a window ownership bug: the tray and second-instance action chose the first Electron BrowserWindow, which could be a hidden native card capture. It displayed that helper instead of the control panel.

`remote_background.js` now remembers the main window passed to `bind()`. Showing the app restores and focuses only that window; a closed or destroyed main window never falls back to a helper. The regression test supplies the offscreen window first and fails if it is shown or focused.

Validation:

- Regression test and six SDK identity/startup checks passed. Full installer build passed source checks, 48 packaged runtime checks, 3,242 asset comparisons, catalog image audit and packaged smoke/updater checks.
- Installed the exact portable payload using the normal installer Engine, retaining the previous app. The matching game SDK was already installed with BL4 closed. Normal game startup reports 2.29.1 and SHA256 `4fad86dcf5d06f3bcc9c87219fb265a8457ff56d888e13398c4eccd7448f67dc`, matching source, packaged and installed SDK.
- Actual installed app, regular profile: 1,805 saved bookmarks present. Shared Community Folder test view displayed a matching GZO image and an 819x897 game card. Repeat native request reused identical cached pixels. Current refreshed catalog matched 508 of 818 unique codes; the prior isolated profile matched 503.
- A second app launch after creating the hidden card window showed only the main control panel. Visually verified the panel and both cards; normal close succeeded, followed by a clean restart without the diagnostic listener.
- All nine equipped and 865 backpack exact serials remained unchanged across the patch restart. AFK restored with every prior configuration field equal, without replaying deliveries.

Private receipts are in `output/native-release-checks/`. Native limitations documented in the shared-card release note still apply. No website deployment, NCS rendering requests, or new multiplayer-delivery proof is included. Android remains the unchanged 1.5.0 APK.
