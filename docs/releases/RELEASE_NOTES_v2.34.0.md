# MSBT 2.34.0 — Epic farming and party controls

Farming controls now include qualified Epic Games support and independent player
targets in the regular desktop, Android workspace and SDK. No separate farming
add-on or console loader is required.

- Choose yourself, a named party member, Other Players or All Players in the
  weapon, survival/skill and glide panels. Target selections stay synchronized.
- Twelve character controls keep independent state for each player: God Mode,
  Infinite Ammo, No Reload, Instant Reload, No Recoil / Sway, Super Accuracy,
  Rapid Fire, Critical Hit Boost, Instant Skill Cooldown, Unlimited Skill
  Duration, Instant Grenade Cooldown and Unlimited Glide Duration.
- Readbacks identify affected players and mixed On/Off states. Missing or stale
  player selections return a clear error without redirecting the action to you.
- Vendor Refresh On Close, Weighted Loot High Roll and 100% Drop Rate are marked
  as whole-lobby controls. Weighted Loot High Roll remains experimental and does
  not guarantee legendary items. 100% Drop Rate affects eligible chance rolls;
  pool eligibility and exclusive item choices still apply.
- Epic native profiles cover the qualified installed build
  Oak2-RE_Games_Oak2_Patch_Epic-4845623; Steam build 25372571 remains supported.
  Unrecognized native contexts refuse activation.
- All 14 farming features remain individually searchable in both desktop
  layouts and the Android workspace. F7 actions use the selected player.

Controls start OFF and are not saved as active. All Off restores owned overrides;
travel, character replacement, disconnect and mod disable clean up affected state.
Completed refills and generated loot remain. Guest controls require lobby-host
authority; owning the app does not grant control of someone else's lobby.

Validation: 80 focused checks, both desktop search layouts, player-target UI and
all 14 local Steam HTTP On/Off/restoration checks passed. Epic support was checked
against the installed executable and native layouts. Epic live execution and
actual guest gameplay remain unverified. Prior host gameplay was confirmed by
the owner; these evidence levels are recorded separately.

Android 1.6.2 accompanies this release. Update the desktop, SDK and phone together.
Close Borderlands 4 before updating game files, then launch normally. If you used
the separate local Farming Lab, turn it OFF and disable/remove that test add-on
before the next game launch with the integrated SDK.
