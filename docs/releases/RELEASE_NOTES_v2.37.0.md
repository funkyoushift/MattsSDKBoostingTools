# v2.37.0 â€” 100% game preset and mission recovery

- New **100% game** action under Missions runs supported missions, discoveries, travel requirements, levels, currencies, SDU points, vault-card progress, applicable unlocks, UVH, Mayhem and challenges.
- Host alone or host plus one guest can run available content. Larger lobbies require everyone to have the required DLC access. Unavailable content and affected players are reported.
- A final pass checks newly available missions and travel requirements without resetting or repeating verified work. A previously skipped Mayhem gate is rechecked too.
- Faster discovery batches, shorter app waits and smaller progress reports retain per-operation checks, guest mission-credit verification and durable recovery records.
- Inactive vault-card level requests are reported and skipped rather than stopping the entire run. Activate those cards individually to level them separately.
- Mission recovery, DLC access reporting and guest Grassroots challenge-credit repairs are included.

## What to expect
Check the lobby, review the shared-progress acknowledgement, then start the run. This changes the host and all participating characters; the initial mission pass can reset completed host missions for normal guest completion. Stop, status, continue and close-stopped-run controls are available. Uncertain mission results still stop instead of being blindly retried.

The nine-stage host-side run completed. The final pass repeated no completed work; no late-unlocked mission appeared in that test, so that pickup branch has offline coverage rather than a live example.

**Known guest-save issue:** The Chase remained active for one tested guest after saving and opening their own game, despite the host reporting completion. Retests with slower pacing, normal activation, DLC-map entry and a fresh host did not resolve it. A fast-forward prompt was also reported; its role and the cause remain unknown. This is not evidence of save corruption or universal failure. Other guest mission batches have passed own-game checks. A local completed count or finished preset is not a guarantee that every guest mission saved. Check guest saves and report the mission, objective and any fast-forward prompt.

The preset covers supported progression, not every possible item, statistic or achievement. Two known unavailable mission definitions and nonpersistent replayable variants remain excluded. Missing DLC, unmapped content, unconfirmed vehicle unlocks and inactive cards remain visible. SDU points do not automatically purchase upgrades. Verify each guest in their own game after saving and quitting. Generic objective completion, objective undo and resetting all progress remain unavailable.

Windows app and SDK: **2.37.0**. Android remains **1.6.2**; this release adds the preset to the desktop panel.
