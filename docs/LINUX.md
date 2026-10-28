# Linux desktop (x86-64)

Download `MSBT-Installer-vVERSION-linux-x64.AppImage`, mark it executable in
your file manager and open it. The first launch opens **MSBT Setup**. Install
for your account and optionally set up the SDK for
the detected Borderlands 4 installation. Setup never stops the game. If the game
or its Proton prefix is busy, desktop installation finishes and game setup stays
pending until you close it normally and rerun Setup.

The installed application lives at `~/.local/share/msbt/MSBT.AppImage`, with its
receipt beside it in `install.json`. The launcher is `~/.local/bin/msbt`; the
application-menu shortcut is `~/.local/share/applications/msbt.desktop`. After
installation, the installed shortcut opens the panel normally. Run the AppImage
with `--setup` to reopen Setup, or choose **MSBT Setup** from the installed
application menu to repair the installation. If your system blocks FUSE mounts, use
`--appimage-extract-and-run`.

For a portable folder, extract `MSBT-Portable-vVERSION-linux-x64.tar.gz` into a user-owned directory and
run `./msbt` inside it. The archive includes Electron and a pinned Python 3.12
runtime and PyYAML 6.0.3; no Python, Node.js or Wine installation is needed for the desktop app.
Before Electron starts, the AppImage checks its shared-library requirements.
On Debian/Ubuntu/Mint and Fedora/RHEL-like systems, it offers to install recognized
missing desktop packages through the distribution package manager. You see the
package list and must confirm; administrator authentication is requested only for
that package-manager command. MSBT itself runs as your normal user. A visible
terminal provides a fallback when graphical confirmation tools are unavailable.
If APT package lists are empty or stale, Setup offers a separate consented
package-list refresh before checking again. It never loops or invents package
names. No host packages are installed silently. Unsupported distributions, unknown
libraries, incompatible glibc and missing graphical sessions produce an error;
Setup does not upgrade system libc or bypass those requirements.

Borderlands 4 and its SDK runtime still run as Windows software under Steam
Proton/Wine. This package does not turn the game SDK into a native Linux library.
The [official BL4 SDK installation instructions](https://bl-sdk.github.io/oak2-mod-db/)
require the Proton launch options:

```text
WINEDLLOVERRIDES="dsound=n,b" %command% -pf_tricks=vcrun2022
```

Run Borderlands 4 once through Steam before optional game setup so its Proton
prefix exists, then close the game normally. Optional game setup applies the
scoped SDK/Proton configuration only while the game and prefix are idle. If the Visual C++ runtime is missing, Setup can offer
the distribution's `protontricks` package and then its interactive `vcrun2022`
installer under your normal user account. Cancellation leaves game setup pending.
For manual setup, use the official launch options above. The SDK console must
load successfully before MSBT can connect to its game-side bridge.

Select the actual game's `sdk_mods` folder when automatic discovery cannot find
it. Close the game before installing or updating SDK files. Keep saves backed up.
For save-backed replay, set `MSBT_SAVE_ROOT` to the absolute Proton/Wine
`Saved/SaveGames` directory before starting `./msbt`. The app refuses to guess a
save directory on Linux.

Native item-card executable profiles retain their existing exact-build gates.

Use the app update controls to download the matching Linux package. Keep the
previous package until the update succeeds. You can also replace an AppImage or
extract a new portable folder manually. Windows updater executables do not run
on Linux.
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
Both AppImage and portable TAR contain the same application and bundled
runtime. Only the two application packages are public Linux assets; build
metadata and development files remain local.

To roll back, close MSBT and run the preceding extracted version. SDK rollback is
a separate operation performed while the game is closed; retain the prior SDK
archive before replacement.

## Requirements references and checks

The repair allowlist uses the distribution package names, including
[Ubuntu's GTK t64 package](https://packages.ubuntu.com/noble/amd64/libgtk-3-0t64),
[Fedora GTK](https://packages.fedoraproject.org/pkgs/gtk3/gtk3/),
[Fedora ALSA](https://packages.fedoraproject.org/pkgs/alsa-lib/alsa-lib/) and
[Fedora protontricks](https://packages.fedoraproject.org/pkgs/protontricks/protontricks/).
Debian-family repairs use `apt-get`, as recommended for scripts by
[Ubuntu's package-management documentation](https://ubuntu.com/server/docs/package-management/).

`tools/linux_bootstrap.py --app-dir PATH --probe-only` performs a read-only library
probe and emits JSON. `python3 -m unittest tools.tests.test_linux_bootstrap` tests
missing-library and consent scenarios with fake commands; it never installs host
packages. Package installation and a live game are separate validation steps.
