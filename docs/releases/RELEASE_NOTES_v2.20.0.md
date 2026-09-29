# MSBT v2.20.0

- Import backpack and equipped items from character `.yaml` or `.sav` files into a new or existing Saved Items folder. Preview the character, level, and item counts before importing. Lost Loot is excluded; saves are read locally and left unchanged.
- Keep duplicate items or choose to skip codes already in the destination folder.
- Improve imported item-card loading. If an embedded card stalls, show readable item details instead of leaving a blank tile. Item details retain their existing validation limitations.
- Keep the developer portal signed in on trusted devices for up to 30 days, renewed while active. Users can opt out or sign out at any time.

Validation: local Steam/Epic save decoding round trips, real desktop import and reload, card rendering and failure recovery, responsive Saved Items layouts, and portal authentication/moderation checks. No game inventory behavior is changed by this update.
