# AFK boosting lobbies and bundled game installation

Choose automatic boosts for each guest who joins: player level, specialization rank, currencies and keys, SDUs (3225), non-UVH challenges, and selected loot. Add loot from Item Catalog or bookmarks, or paste item codes with no overall line limit. Rejoining starts another run.

Optional auto-kick waits until the selected operations finish, including a 15-second settling period after loot delivery. Failed boosts are reported and prevent automatic kicking. Guest save persistence is not independently verified.

The Windows installer now includes the AFK SHiFT PAK and the official stable SDK/mod manager. A fresh game installation requires no separate SDK download. Existing SDK and manager files are preserved, including newer, beta, nightly, and unrecognized versions. Incomplete existing SDK installations are reported rather than overwritten. An existing PAK at the same filename is backed up under the game's MSBT-backups folder before replacement. Close the game before installation.

**AFK limitation:** auto-accept requires the SHiFT menu to stay open and captures gameplay input. This release does not provide background acceptance while playing. Use Close SHiFT / restore controls to return to the game. Screen capture with the floating menu was verified locally.

Challenge handling retries failures per player and sends smaller batches. Queue completion does not prove a guest has 100% completion; UVH challenges are separate.
