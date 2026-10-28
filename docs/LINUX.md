# Linux desktop (x86-64)

Extract `MSBT-Portable-vVERSION-linux-x64.tar.gz` into a user-owned directory and
run `./msbt` inside it. The archive includes Electron and a pinned Python 3.12
runtime and PyYAML 6.0.3; no Python, Node.js or Wine installation is needed for the desktop app.
Install your distribution's normal Electron desktop libraries (GTK 3, NSS, ALSA,
X11/Wayland and Mesa). A working graphical session is required.

Borderlands 4 and its SDK runtime still run as Windows software under Steam
Proton/Wine. This package does not turn the game SDK into a native Linux library.
The [official BL4 SDK installation instructions](https://bl-sdk.github.io/oak2-mod-db/)
require the Proton launch options:

```text
WINEDLLOVERRIDES="dsound=n,b" %command% -pf_tricks=vcrun2022
```

Configure these in Steam when qualifying the game SDK; this archive does not
change your Steam launch options automatically. The SDK console must load
successfully before MSBT can connect to its game-side bridge.

Select the actual game's `sdk_mods` folder when automatic discovery cannot find
it. Close the game before installing or updating SDK files. Keep saves backed up.
For save-backed replay, set `MSBT_SAVE_ROOT` to the absolute Proton/Wine
`Saved/SaveGames` directory before starting `./msbt`. The app refuses to guess a
save directory on Linux.

Native item-card executable profiles retain their existing exact-build gates.

The Linux tarball is updated manually: download and extract the next version
alongside the old one. Windows updater executables must not run on Linux.
App settings remain under Electron's normal per-user Linux configuration folder.
The standalone Mission Selector is separate; do not install it alongside the full
MSBT SDK. Linux game/Proton compatibility and guest-save proof require separate
live qualification; desktop packaging and offline checks alone do not prove them.

## Build from source

Use Linux x86-64, Python 3.12 or later and Node.js 24/npm. From `electron_poc`, run
`npm ci`, then `npm run dist:linux`. Output is under `dist_linux/`. The script
checks Python syntax before packaging the SDK and verifies the official SDK and
pinned standalone Python SHA-256 hashes. It does not publish or install into a
game directory. Build products include Python's licenses inside `resources/python`;
`LINUX-PYTHON-PROVENANCE.json` records its upstream archive and checksum.

To roll back, close MSBT and run the preceding extracted version. SDK rollback is
a separate operation performed while the game is closed; retain the prior SDK
archive before replacement.
