# Experimental mission tools patch

The user authorized publishing the usable installed candidate with unfinished behavior clearly marked. This replaces the earlier requirement for universal mission/100% verification before release.

The SDK behavior matches the tested candidate, with a patch version update. Desktop mission views now use amber notices and explicit Experimental labels for later checkpoints; full-game wording reports supported progress rather than guaranteeing saved 100% completion. The separate direct-checkpoint shortcut is excluded.

Validation: 356 focused execution, selection, placement, objective, progression, context and full-progress checks passed; 14 release import/publisher checks passed. Bounded Bugbot found no release-blocking issue and independently passed 95 focused checks. Real-page mission views verified amber notices and responsive controls. Host live tests passed opening replay, selected NPC objective completion, objective rewind and precise checkpoint setup. Save comparisons preserved character progression and map discovery. Two later-checkpoint runs stopped safely; later stage playability, guest save persistence and universal 100% completion remain unverified.

Packaging completed: 31 installer checks, standard desktop checks, 600 responsive measurements, 48 packaged dependencies and 3260 packaged asset checks passed. SDK archive compilation and CRC passed. The release SDK differs from the tested installed candidate only in its two version metadata files. The unchanged published Android 1.6.2 APK accompanies the patch. Checksums are in SHA256SUMS.txt. Publication follows package verification; no universal completion claim is made.

Recovery: Stop preserves applied mission changes and restores owned movement changes. Reinstall the prior published v2.38.0 package to roll back the software; this does not undo saved progress.
