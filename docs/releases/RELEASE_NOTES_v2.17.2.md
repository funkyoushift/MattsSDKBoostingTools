# Matt's SDK Boosting Tools v2.17.2

Unresolved backpack recoveries no longer lock AFK startup. Saved recovery records
remain available for support without preventing boosts for other guests.
An item return that is still running must finish before another AFK session starts.
Failed recovery still prevents that guest from being automatically kicked.

New recovery jobs save separate, paste-ready original-backpack and selected-new-loot
lists under %LOCALAPPDATA%/MattsSDKBoostingTools/inventory-recovery/saved-item-lists/.
Each folder includes the player name and item counts. Duplicate items and serial
case are preserved. Lists record intended items, not confirmation of delivery;
check with the player before resending. Recovery records are never replayed automatically.

Includes the v2.17.1 password correction: cleanup and returning original items need
no password; sending more than 70 new items still does. Equipment slots and
favorite/junk flags are not restored.

Desktop and SDK: **2.17.2**. Android controller remains **1.4.1 (28)**.
Validation: recovery, AFK, startup/import and desktop packaging checks.
This release does not claim a new live multiplayer recovery verification.
