# Matt's SDK Boosting Tools v2.17.1

AFK backpack cleanup and returning original items no longer require a password.
Starting AFK only requests the password when the selected new loot exceeds 70
items. Returning a guest's original inventory does not count toward that limit.

Desktop and Android wording and walkthrough guidance now match this behavior.
The separate manual Empty/Drop Backpack protections for other players remain.

Includes the v2.17.0 cleanup workflow: capture originals, apply boosts, open
reward packages, clear reward loot, send configured serial loot, return originals,
and verify item counts before auto-kick. Existing recovery safeguards and backup
records remain in place. Equipment slots and favorite/junk flags are not restored.

Validation: 105 Python checks, desktop/mobile AFK UI checks, password protection
checks, and release package checks. Desktop and SDK: **2.17.1**.
Android: **1.4.1 (28)**.
