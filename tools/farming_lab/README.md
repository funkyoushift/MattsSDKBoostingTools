# Local Farming Lab

Open the running local desktop panel. Controls are grouped by purpose:

- **Boosting → Combat → Weapons & Ammo — Local Tests**: weapon controls.
- **Party & Combat → Combat Tuning → Survival & Skills — Local Tests**: God Mode and skills/grenades.
- **Movement & World → Movement → Glide / Dash**: Unlimited Glide Duration.
- **Boosting → Loot & Vendors → Chests & Vendors**: Vendor Refresh On Close.
- **Boosting → Rarity → Loot Rolls — Local Test**: Weighted Loot High Roll only.

Choose **On** beside one control. Choose **Off** to restore it, or **Turn All Local Tests Off**
to stop the entire lab. Test one control at a time so comparisons are meaningful.

The lab contains God Mode, Infinite Ammo, No Reload, Instant Reload, No Recoil / Sway,
Super Accuracy, Rapid Fire, Critical Hit Boost, Instant Skill Cooldown,
Unlimited Skill Duration, Instant Grenade Cooldown, Vendor Refresh On Close,
Unlimited Glide Duration, and Weighted Loot High Roll.

Player/weapon controls apply to the hosting character and owned equipment.
Vendor refresh affects host vendors being used. Weighted Loot High Roll changes
the qualified weighted-selection routine in the host process; it is not proven
to guarantee legendary items or outperform the existing rarity controls.
Guest combat effects and guest loot/save behavior require separate validation.

All controls start OFF. Travel, a different pawn/world, and disabling the add-on
request restoration. Completed shots, refills, purchases, and generated loot are
not undone. The weighted-roll native experiment and read-only skill-charge
enumeration support only the qualified Steam build 25372571.
Do not run another trainer over the same native routines.

God Mode uses the character's native damage-permission flag and restores its
original value. Glide now sets only glide power cost to zero; it preserves the
other movement costs. Skill cooldown refills the primary resource and validated
owned action-skill charge/virtual-cooldown pools. Actual long-press behavior and
sustained glide remain gameplay checks; successful API calls are not proof.
Repair-kit cooldown already exists in **Combat / Resource Tuning**, in seconds.

For gameplay comparisons:

1. Fire/reload the same weapon with a control OFF, then ON, then OFF again.
2. Activate a skill or grenade to test cooldown/duration; idle readbacks prove
   only that the API call works.
3. Compare vendor stock before opening, after closing, and after reopening.
4. Compare a sustained glide with the duration test OFF and ON.
5. Compare repeated kills of the same enemy with the same rarity settings;
   record actual drops and ask a guest to check their own items and persistence.

The addon is installed at the game's `sdk_mods/MSBTFarmingLab`. If needed after
loading a character, bootstrap it once in the SDK console with
`pyexec msbt_farming_lab_load.py`. Console fallback: `msbt_farm off`.
The local desktop is launched with `npm start` from this checkout's `electron_poc`.

API actions use the existing MSBT `/action` route with action `farming_lab` and
payload `{"op":"set","feature":"no_reload","enabled":true}` or `{"op":"off"}`.
F7 assignable actions appear with the `Lab:` prefix while the addon is enabled.
The file client is for bounded developer probes and requests, not a public API.

To roll back: first turn all tests OFF and disable **MSBT Farming Lab (local test)**.
With the game closed, remove only that addon folder and its loader if desired.
Close the local source desktop and reopen the installed MSBT desktop. Production
SDK/installer files and public version 2.32.0 were not replaced by this lab.

See [change record](../../docs/changes/2026-10-08-farming-lab.md) for provenance,
exact checks, limitations, and evidence paths. This is local test source only.
