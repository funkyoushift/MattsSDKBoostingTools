# Borderlands 4 Modding Tools v2.39.1 — Powered by Funk

- Replay waits briefly when Windows locks the save during character reload, allowing verification to finish before map travel. Persistent locks still stop safely with the backup retained; game actions and save edits are not repeated.
- Replay selects one mission at a time. Changing campaigns or filters clears hidden replay selections, preventing the stuck “Choose one mission first” dropdown. Completion mode retains multiple selections.
- Replay requirements and failed-run recovery messages appear beside the Start control. Replay requires a solo lobby and a second existing loadable character in the same profile.
- Android **1.6.3 / build36** refreshes the shared mission interface, dialogue controls, replay and bookmarks. A paired phone can now control the Windows save-backed transaction; saves and backups remain on the PC. Update Windows to **2.39.1** too.
- Both Windows and Android update metadata point to these new versions. Steam and Epic support is retained.

Choose **MSBT-Installer-v2.39.1.exe** or the portable ZIP for Windows. Android users can use the in-app update check or install **MSBT-Mobile-Controller-1.6.3.apk** over their current app without clearing its data. Close Borderlands 4 before updating SDK components.

Mission replay, generated encounters and bookmarks remain experimental. Keep backups. Replay changes the mission timeline and clears dependent future progress while preserving current gear and levels. Missing or unsafe starting coordinates use a native respawn station. Some timed scenes still wait with dialogue skip enabled. Prior v2.39.0 mixed-DLC completion evidence remains applicable; this patch does not claim new guest-save persistence or exhaustive encounter testing.
