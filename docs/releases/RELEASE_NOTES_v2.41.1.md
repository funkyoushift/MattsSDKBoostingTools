# MSBT v2.41.1 — updater and SHiFT repairs

This patch combines three repairs:

- Electron updater checks use `original-fs` to verify the physical ASAR archive. In an Electron 44.3.0 fixture, `fs/promises.access(app.asar)` returned `ENOENT` while `original-fs.promises.access(app.asar)` succeeded. Existing v2.41.0 installs need one manual update to receive the fixed updater.
- SHiFT F10/F11 bindings register at SDK startup, with idempotent fallback and rollback if binding setup is partial. Martin confirmed F10 opens SHiFT in a fresh session.
- Ordinary incoming acceptance no longer waits for a reviewed protected-list prerequisite. The existing Remove All guard remains.

The native controller-input path is unchanged. Martin reported that Play while accepting blocked movement and mouse look from the pause menu; that live behavior remains unresolved and publication is held pending a supervised check. No social action was issued by tools.

The candidate PAK SHA-256 is `728165a795f7543b9a109604b60a8ae54f70de2c6cf92f4a37c231982a5e617f`; the companion SDK archive SHA-256 is `9fc2a823605f1035cf3df8b53ff20b753b2db8798d51b15fbe6fb00f941c8c02`. Android remains at 1.6.6/build 39 and is unchanged.

Validation recorded so far: 38 focused Python background/storage tests and JavaScript background/protection/automation checks passed; updater Electron ASAR source and synthetic-package regression passed. Windows installed-package CI, Windows/Linux artifact builds, full package hashes, and all release asset checks are pending. No live game/device qualification is claimed.
