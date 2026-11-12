# MSBT v2.41.2 — SHiFT saving and menu repairs

- Save and reload the SHiFT do-not-delete list reliably. Atomic first saves and edits preserve the existing list if a write fails; stale reads cannot replace newer changes.
- Keep reviewed-list and matching save-acknowledgement safeguards before friend deletion.
- Add observed-menu suspension and restart handling to address background SHiFT pause-menu lockups, including longer menu sessions. Show, Stop and disconnect cancel automatic restart. The desktop distinguishes suspension and restart from confirmed active acceptance.
- Strengthen paired-phone authorization: shared IP addresses cannot select another phone's pairing, and paired phones cannot expand the desktop's trusted file paths. Existing token pairings survive address changes; legacy IP-only entries need pairing again. The Android APK is unchanged.

## Download and install

Choose one download for your platform:

- **Windows installer:** `MSBT-Installer-v2.41.2.exe` — run the installer to install or upgrade.
- **Windows portable:** `MSBT-Portable-v2.41.2-win-x64.zip` — extract into a folder and launch `MattsSDKBoostingTools.exe`.
- **Linux guided installer:** `MSBT-Installer-v2.41.2-linux-x64.AppImage` — make it executable and run it for per-user setup and optional game integration.
- **Linux portable:** `MSBT-Portable-v2.41.2-linux-x64.tar.gz` — extract and run the included `msbt` launcher.

Close BL4 before updating its game integration. Install the desktop and matching bundled game integration together, then restart BL4. GitHub's Source code ZIP/TAR downloads are source archives, not ready-to-run applications.

## Validation and limits

[Windows/Linux CI passed](https://github.com/funkyoushift/MattsSDKBoostingTools/actions/runs/43189250665), including actual Windows installation and the installed updater checks. The final Windows upgrade matched all 1,497 application files and preserved preferences and the complete user-data tree. The installed final native background service reached confirmed active state. Linux portable checks verified the final SDK sources, PAK, companion, desktop runtime and version metadata.

Physical Escape entry/exit, movement, mouse-look and the minimized SHiFT return passed on the v12 repair diagnostic; the requested 2.5-minute menu test was user-confirmed. The final production integration adds reviewed safeguards and passed its offline regressions plus live active/foreground checks. Its final physical Escape cycle was interrupted and is not claimed as passed; automated Escape was also unreliable with acceptance stopped.

Final physical gamepad and Linux live gameplay are not qualified. Travel coverage is not exhaustive; no blanket Epic or guest-save qualification is claimed. Linux packaging checks do not establish live gameplay behavior.

## SHA-256

```text
9136b3811a4316fe7c6f653e5cbd6229d3cc3b800b3cf2b320b9fb074d436bc1  MSBT-Installer-v2.41.2.exe
951b415a00630d0bff2feb18cfc1c8e6116ac3b85466df607aa407a0927ba1f4  MSBT-Portable-v2.41.2-win-x64.zip
4aff76ac8697b9612fdf8d2423a3a8887bfd6daf7873f6f1891e54d18359791e  MSBT-Installer-v2.41.2-linux-x64.AppImage
4881ec5bc42a6ba2bf52c4583e0c7340547c6af53c727b0cfcb3207955fd6f6a  MSBT-Portable-v2.41.2-linux-x64.tar.gz
```
