# MSBT v2.15.0

- Add guaranteed AFK items from the catalog, bookmarks, or pasted codes. Guaranteed items arrive first, with the remaining slots filled randomly up to 70. Duplicate codes across the two pools are not drawn twice.
- Draw a fresh random selection for each guest. Class mods are restricted to the guest character, with one matching class mod included when available and space permits. Unrecognized character classes wait rather than receiving another class mod.
- Retain password protection for deliveries above 70 and guest backpack actions.
- Fix AFK Start failing with “unexpected end of bitstream” by classifying item headers without decoding the full part payload.
- Apply SHiFT screen-capture support when the menu is opened normally as well as with F10, independently of gameplay input restoration. Native SHiFT still captures gameplay input.
- Include the new guaranteed-items tutorial and the SDK mod, SDK manager/runtime, and AFK PAK in the installer. Existing newer SDK/manager installations are preserved.

Validation: automated AFK, class filtering, recording lifecycle, password, startup, and release checks. Live guest delivery and recorder-specific compatibility still require user testing.
