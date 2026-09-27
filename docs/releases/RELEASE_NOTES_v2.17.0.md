# Matt's SDK Boosting Tools v2.17.0

Optional AFK reward cleanup preserves guests' original items while removing
challenge and UVHM reward loot. Enable **Clean challenge / UVHM reward loot and
return original items** in the AFK settings, select challenges or UVHM, and enter
the backpack password once when starting the session.

The workflow captures and saves originals before boosts, opens reward packages,
clears the backpack, sends the configured serial loot when enabled, then returns
the originals. Random count, guaranteed items and class-mod filtering still apply
to the new loot. Returned originals are additional to the selected delivery size.

Duplicate copies and item quantities are checked before completion. Equipment
slots and favorite/junk flags are not restored. Backpacks containing stacked
entries are left untouched and their boost job is skipped. Incomplete captures,
delivery failures and failed verification keep the guest in the lobby. Unresolved
recovery records block a new AFK session after a restart rather than replaying
deletion or resending items automatically. Backups remain on the host PC.

The desktop and Android AFK controls include the new option. The built-in AFK
walkthrough explains the sequence. Cleanup is off by default and retains the
existing shared-connection kick barrier and settlement wait.

Validation includes a live 168-entry original-item round-trip, preserving all
duplicate serial counts, and automated combined-delivery tests. The full AFK
challenge/UVHM plus new-loot composition has not yet been independently confirmed
in a live guest save. The SDK manager and SHiFT PAK remain bundled; newer installed
SDK/manager versions retain the existing installer protections.

Desktop and SDK: **2.17.0**. Android: **1.4.0 (27)**.
