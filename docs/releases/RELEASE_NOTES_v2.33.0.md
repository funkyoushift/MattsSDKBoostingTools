# MSBT 2.33.0 — Farming controls and searchable features

Fourteen farming controls now ship in the regular SDK and desktop/mobile
workspace, with individual On/Off buttons, game readbacks and F7 assignable
actions. No separate local add-on or console bootstrap is required.

- Weapons: Infinite Ammo, No Reload, Instant Reload, No Recoil / Sway,
  Super Accuracy, Rapid Fire and Critical Hit Boost.
- Survival and skills: God Mode, Instant Skill Cooldown, Unlimited Skill
  Duration and Instant Grenade Cooldown. Skill cooldown also refills validated
  owned action-skill charge pools. Repair-kit cooldown remains beside these
  controls in Combat / Resource Tuning.
- Movement: Unlimited Glide Duration removes glide power cost.
- Vendors: Vendor Refresh On Close.
- Loot: Weighted Loot High Roll remains a separate experimental weighted-roll
  control; it is not a guarantee of legendary items. The existing 100% Drop Rate
  control is retained and affects eligible drop-chance rolls, not pool eligibility.

Player/weapon controls apply to the hosting character and owned equipment.
Vendor/loot controls operate in the host process. Native weighted rolls and
skill-charge enumeration are qualified for Steam build 25372571 and refuse
unqualified contexts. These are not guest character controls.

All controls start OFF, are never saved as active, and turn OFF on travel,
world/pawn change or mod disable. Turn All Farming Controls Off is available
in the desktop and F7. Completed refills and generated loot are not undone.

Search now includes individual controls, all 14 farming features even before
game status arrives, and common aliases such as godmode, inf ammo and repkit
cooldown. Results open the right section, expand collapsed controls and highlight
the requested feature. Workspace and classic layouts are supported.

Matt confirmed all gameplay tests passed on October 8. Source, package and
publication checks are documented separately in the verification record.
No claim of every character/build or guest-save compatibility is implied.

Android 1.6.1 includes the updated workspace and search. Update the desktop,
SDK mod and Android APK together. Finish your current lobby, close Borderlands
4 before replacing game files, then launch it normally. Local Farming Lab users
should turn its controls OFF and disable/remove the separate test add-on before
using the integrated version.
