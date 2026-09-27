# Matt's SDK Boosting Tools v2.17.3

Reward cleanup now retries unstable backpack reads and repairs missing deliveries
automatically. It rechecks deficits after settling, then sends only the missing
copies of original items and selected new loot, with up to three repair attempts.
Interrupted original returns also proceed to verification and repair. The backpack
clear and boosts are not repeated. Late arrivals are rechecked to avoid duplicates.

Removed the remaining per-guest check that rejected cleanup because of an old
failed recovery record. Unresolved recoveries retain their saved item lists while
AFK continues serving other guests. Active returns still finish before a new
session starts; disconnected or unrecovered guests are not automatically kicked.

Includes the no-password cleanup behavior: only delivery above 70 new items needs
the AFK password. Original items do not count toward that limit. Equipment slots
and favorite/junk flags are not restored. Interrupted journals are not replayed
across process restarts.

Validation: 121 offline checks, including partial delivery, interrupted return,
late arrivals, duplicate preservation, retry limits, player replacement and old
recovery records, plus desktop packaging checks. Live guest recovery remains
unverified for this patch.

Desktop and SDK: **2.17.3**. Android remains **1.4.1 (28)**.
