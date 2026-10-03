# Borderlands 4 Modding Tools v2.27.0

- Guest backpack dropping accepts valid signed item handles and reports an error when no eligible items are found, instead of claiming a zero-item drop succeeded. Added local backpack diagnostics.
- AFK can target vault card levels for cards 1–5 separately from keys, with an adjustable amount. Higher existing levels are preserved.
- AFK can save SHiFT names that receive boosts but are exempt from automatic kicking. Shared connections are protected together.
- Sending from the editor refreshes the generated code on each send, preventing the first code from sticking. Missing or ambiguous editor output stops the send.

Guest self-delivery and backpack dropping, plus the AFK and editor changes, passed the owner's live testing. Automated regression coverage includes the original successful guest transaction, AFK settings persistence, and website editor/admin code-edit permissions.

Close Borderlands 4 before installing so the bundled SDK mod can be replaced. Restart the game after installation. Android controller version remains 1.5.0.
