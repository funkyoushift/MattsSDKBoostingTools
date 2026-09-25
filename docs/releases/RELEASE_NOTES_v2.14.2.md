# AFK join readiness and SHiFT input restoration

AFK boosts now wait for the guest character's progression and experience containers to initialize, then allow 20 seconds of stable loading before sending boosts. A missing or replaced character, progression reset, disconnect, or world change resets readiness. This addresses boosts being sent to a loading character before their save data arrives. Selected boosts still run regardless of existing progress, and level readback/retries remain enabled.

Closing the F10 SHiFT menu now repeats input restoration briefly after the close request. Native Back/close transitions also trigger restoration. Pending restoration is cancelled when the player controller changes or the Quick Menu takes focus.

The installer retains the bundled SHiFT PAK and official SDK/mod manager and preserves existing SDK/manager installations. Close Borderlands 4 before installing.

**Validation:** offline AFK, input lifecycle, startup, import, and UI checks passed. The readiness change was prompted by live logs showing empty progression data; live guest validation of the final patch remains outstanding. Auto-accept still requires the SHiFT menu open and captures game controls. A completed queue does not prove guest save persistence or 100% challenge completion.
