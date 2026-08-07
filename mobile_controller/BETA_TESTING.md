# MSBT Mobile Controller — Closed Android Beta

This is a **closed layout/function beta** for MSBT Mobile Controller. It is intentionally separate from the Windows MSBT installer.

## What testers receive

- `MSBT-Mobile-Controller-0.1.0-beta.1.apk` — Android app only.
- `MSBT-Mobile-Beta-Test-Kit-0.1.0-beta.1.zip` — this guide/checklist only.

Do **not** package the APK inside the Windows MSBT installer.

## Before installing

1. Confirm your phone make and model in Discord.
2. Note your Android version: **Settings → About phone → Android version**.
3. Keep your current desktop MSBT installation unchanged.
4. This first build can be reviewed offline. Live PC/game actions may remain unavailable until the connection gateway is enabled.

## Install the APK

1. Download the APK from the Discord post or linked GitHub Actions/Release page.
2. Open the downloaded APK.
3. Android may ask permission for your browser/Discord/file manager to install unknown apps. Allow it for the app you are using to open the APK.
4. Install **MSBT Mobile Controller**.
5. Open it and confirm the Home screen loads without crashing.

If Android refuses to install an update over an older mobile beta, report the exact message before uninstalling anything.

## What to test first

Test both **portrait** and **landscape** where it makes sense.

### 1. Home / navigation

- Home, Boost, Codes, Control, and More tabs are visible.
- Text is readable and not clipped.
- Bottom navigation is reachable above Android gesture controls.
- Rotate the phone and confirm the layout remains usable.

Take a full-screen screenshot in portrait.

### 2. BL4 Codes

- Bundled catalog loads.
- Search works.
- Source filter includes GZO, Lootlemon, and MSBT/custom data when present.
- Type, manufacturer, and rarity filters work.
- Multi-select works.
- **Select all filtered** selects the current filtered result set.
- **Clear** removes the selection.
- Item images that are available online display correctly; missing images should not break the list.
- Scroll a large result set and note any lag.

Take screenshots of:

- normal results;
- filters open/selected;
- multiple selected codes;
- any image/layout problem.

### 3. Boost

Check the layout for:

- target player area;
- Quick Max actions;
- Currency / XP fields;
- serial sender;
- copies / level options;
- Validate / Confirm;
- Selected / All / Non-Host delivery buttons;
- rarity presets.

Offline live actions should clearly say a PC connection is required rather than pretending they worked.

### 4. Serial Bookmarks

- Add a bookmark.
- Give it a name and group.
- Close and reopen the app.
- Confirm the bookmark is still there.
- Edit it.
- Delete it.

This mobile shape is intended to stay compatible with the desktop bookmark model.

### 5. Quick Menu

- Open the full Quick Menu.
- Verify the complete 3×7 layout is visible/usable.
- Switch pages.
- Rename several slots while offline.
- Close/reopen the app and confirm the changes remain.
- Rotate to landscape and take a screenshot.

**Important:** offline Quick Menu changes must never be silently deleted. Future PC sync will ask whether to merge, keep phone, or keep PC. Renamed commands should be preserved by command identity when possible; newly introduced commands should be appended into open/end slots during merge.

### 6. Movement

Check every visible field for clipping/usability:

- Speed Scale
- Walk Speed
- Jump Height
- Gravity Scale
- Step Height
- Floor Angle
- Glide Speed
- Glide Boost
- Glide Air Control
- Dash Speed
- Time Dilation
- Sprint Jump
- Double Jump
- Slide Jump
- Individual jump goals
- Zero vault on apply

Save a preset, close/reopen the app, and confirm the preset remains.

### 7. Connection Setup

- Open **More → Connection Settings**.
- Enter a test PC name, IP address, gateway port, and pairing code.
- Save setup.
- Close/reopen the app and confirm it remains.
- The first beta may report that the live gateway is not enabled yet; that is acceptable if the state is clear and the saved setup is not lost.

## Screenshots we need

Please send **full-screen** screenshots rather than cropping to one button whenever possible.

Required screenshots:

1. Home — portrait
2. BL4 Codes — results
3. BL4 Codes — multi-select
4. Quick Menu — portrait
5. Quick Menu — landscape
6. Movement
7. Connection Settings
8. Any broken/clipped screen

## How to give useful feedback

For this closed beta, send feedback **directly to FunkYouSHiFT in Discord DMs**.

Copy/paste this template:

```text
MSBT MOBILE BETA FEEDBACK

Phone make/model:
Android version:
MSBT Mobile version: 0.1.0-beta.1
Desktop MSBT version (if connected):

Screen/feature:
What I expected:
What happened:
Steps to reproduce:
Does it happen every time? Yes / No / Sometimes

Screenshots attached: Yes / No
Anything else:
```

Good feedback tells us **what you tapped, what happened, and what you expected**. A screenshot plus one sentence such as “the bottom Send button is behind the Android navigation bar after rotating to landscape” is much more useful than “movement is broken.”

## Known beta limitations

- The mobile-to-PC MSBT gateway may not be enabled yet in the first APK.
- Live game actions require desktop MSBT and the in-game bridge once connection support is enabled.
- Matt Editor, save editing, Legit Builder, and deep item-building tools are intentionally not part of the mobile controller.
- This is a controller beta; expect rough edges and send screenshots when you find them.
