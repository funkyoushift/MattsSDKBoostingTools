#!/bin/sh
# This prepackaged AppRun replaces electron-builder's generated entry point.
# Requirements run in bundled stdlib Python before Electron needs GTK/NSS.
set -eu
if [ -z "${APPDIR:-}" ]; then
    APPDIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
    export APPDIR
fi
export PATH="$APPDIR:$APPDIR/usr/sbin${PATH:+:$PATH}"
export XDG_DATA_DIRS="$APPDIR/usr/share${XDG_DATA_DIRS:+:$XDG_DATA_DIRS}:/usr/local/share:/usr/share"
export LD_LIBRARY_PATH="$APPDIR/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$APPDIR/resources/python/bin/python3" "$APPDIR/resources/linux_bootstrap.py" --app-dir "$APPDIR" -- "$@"
