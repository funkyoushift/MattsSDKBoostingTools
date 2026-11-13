#!/bin/bash
# Diagnostic only: never changes host policy, file permissions or verification receipts.
set -u
out="$PWD/dist_linux/sandbox-diagnostics"
mkdir -p "$out"
started=$(date --iso-8601=seconds)
{
  date --iso-8601=seconds
  cat /etc/os-release
  uname -a
  id
  cat /proc/self/attr/current
  sysctl kernel.apparmor_restrict_unprivileged_userns kernel.unprivileged_userns_clone user.max_user_namespaces
  printf 'CHROME_DEVEL_SANDBOX=%s\n' "${CHROME_DEVEL_SANDBOX-<unset>}"
  printf 'ELECTRON_DISABLE_SANDBOX=%s\n' "${ELECTRON_DISABLE_SANDBOX-<unset>}"
  sudo -n aa-status
} > "$out/host.txt" 2>&1
unshare -Ur true > "$out/unshare.txt" 2>&1
printf '%s\n' "$?" > "$out/unshare.exit"
image=$(find "$PWD/dist_linux" -maxdepth 1 -type f -name 'MSBT-Installer-v*-linux-x64.AppImage' -print -quit)
if [ -z "$image" ]; then printf 'No AppImage available\n' > "$out/no-image.txt"; exit 0; fi
scratch=$(mktemp -d /tmp/msbt-sandbox-diagnostic-XXXXXX)
printf '%s\n' "$scratch" > "$out/scratch-path.txt"
(cd "$scratch" && "$image" --appimage-extract) > "$out/extract.txt" 2>&1
printf '%s\n' "$?" > "$out/extract.exit"
target="$scratch/squashfs-root"
{
  stat -Lc '%n uid=%u gid=%g mode=%a' "$target/MattsSDKBoostingTools" "$target/chrome-sandbox"
  findmnt -T "$target" -o TARGET,SOURCE,FSTYPE,OPTIONS
  sha256sum "$image" "$target/MattsSDKBoostingTools" "$target/chrome-sandbox"
} > "$out/files.txt" 2>&1
mkdir -p "$scratch/home" "$scratch/config" "$scratch/data" "$scratch/cache"
env -u APPIMAGE -u APPDIR -u MSBT_PYTHON -u ELECTRON_RUN_AS_NODE -u MSBT_SAVE_ROOT \
  HOME="$scratch/home" XDG_CONFIG_HOME="$scratch/config" XDG_DATA_HOME="$scratch/data" XDG_CACHE_HOME="$scratch/cache" \
  PYTHONDONTWRITEBYTECODE=1 timeout 180 xvfb-run -a "$target/AppRun" --smoke > "$out/smoke.txt" 2>&1
printf '%s\n' "$?" > "$out/smoke.exit"
sudo -n journalctl -k --since "$started" --no-pager > "$out/kernel.txt" 2>&1
printf '%s\n' "$?" > "$out/kernel.exit"
# Keep the bounded CI-only scratch directory for inspection; runner disposal removes it.
exit 0
