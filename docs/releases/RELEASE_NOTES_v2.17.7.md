# MSBT v2.17.7

- Fixed character filters losing class mods after Item Catalog cards load. Searches for "class mod" and "class mods" now include Classmod entries.
- Added **Test selected boosts on me** to AFK Lobby. Runs selected boosts, loot and cleanup once on the host, then stops. Auto-accept and auto-kick are disabled for this test; guest counters are unchanged. Challenge and UVHM actions retain their lobby-wide behavior.
- Guaranteed items now override the class filter, including class mods for other characters. The regular loot pool still excludes incompatible class mods. Guaranteed items still count toward the delivery size and existing password limits.

## Validation and known limitation

The host test and guaranteed-item override were tested in-game. Guest runs continued through reporting and auto-kick. Offline regression checks cover class selection, inventory recovery, host targeting and catalog filtering.

Some delivered modded items still produce inventory-verification warnings. Comparing saved codes found both equivalent serialization changes and removed part entries; the cause of the latter is not yet established. This release retains the reports and original-item backups and does not silently treat altered codes as verified. Alternative inventory delivery is not included.

## Installation

Use MSBT-Setup.exe for installation or updates, or the versioned installer/portable ZIP. Close Borderlands before updating its SDK mod. The Android APK remains v1.4.2, unchanged.
