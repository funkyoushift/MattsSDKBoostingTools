"""Pre-Electron requirements check for the MSBT AppImage (Python stdlib only).

Only distro package managers are elevated, after visible user confirmation.
The application and this helper never run with administrator privileges.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

# SONAME -> Debian/Ubuntu candidates (t64 first), Fedora/RHEL package.
PACKAGES = {
    'libgtk-3.so.0': (('libgtk-3-0t64', 'libgtk-3-0'), 'gtk3'),
    'libgdk-3.so.0': (('libgtk-3-0t64', 'libgtk-3-0'), 'gtk3'),
    'libnss3.so': (('libnss3',), 'nss'),
    'libnssutil3.so': (('libnss3',), 'nss-util'),
    'libsmime3.so': (('libnss3',), 'nss'),
    'libnspr4.so': (('libnspr4',), 'nspr'),
    'libplc4.so': (('libnspr4',), 'nspr'),
    'libplds4.so': (('libnspr4',), 'nspr'),
    'libatk-1.0.so.0': (('libatk1.0-0t64', 'libatk1.0-0'), 'atk'),
    'libatk-bridge-2.0.so.0': (('libatk-bridge2.0-0t64', 'libatk-bridge2.0-0'), 'at-spi2-atk'),
    'libatspi.so.0': (('libatspi2.0-0t64', 'libatspi2.0-0'), 'at-spi2-core'),
    'libdrm.so.2': (('libdrm2',), 'libdrm'),
    'libX11.so.6': (('libx11-6',), 'libX11'),
    'libX11-xcb.so.1': (('libx11-xcb1',), 'libX11-xcb'),
    'libxcb.so.1': (('libxcb1',), 'libxcb'),
    'libXcomposite.so.1': (('libxcomposite1',), 'libXcomposite'),
    'libXdamage.so.1': (('libxdamage1',), 'libXdamage'),
    'libXext.so.6': (('libxext6',), 'libXext'),
    'libXfixes.so.3': (('libxfixes3',), 'libXfixes'),
    'libXrandr.so.2': (('libxrandr2',), 'libXrandr'),
    'libgbm.so.1': (('libgbm1',), 'mesa-libgbm'),
    'libxkbcommon.so.0': (('libxkbcommon0',), 'libxkbcommon'),
    'libcups.so.2': (('libcups2t64', 'libcups2'), 'cups-libs'),
    'libasound.so.2': (('libasound2t64', 'libasound2'), 'alsa-lib'),
    'libpango-1.0.so.0': (('libpango-1.0-0',), 'pango'),
    'libpangocairo-1.0.so.0': (('libpangocairo-1.0-0',), 'pango'),
    'libcairo.so.2': (('libcairo2',), 'cairo'),
    'libdbus-1.so.3': (('libdbus-1-3',), 'dbus-libs'),
    'libglib-2.0.so.0': (('libglib2.0-0t64', 'libglib2.0-0'), 'glib2'),
    'libgobject-2.0.so.0': (('libglib2.0-0t64', 'libglib2.0-0'), 'glib2'),
    'libgio-2.0.so.0': (('libglib2.0-0t64', 'libglib2.0-0'), 'glib2'),
}
MANAGERS = {'apt': '/usr/bin/apt-get', 'dnf': '/usr/bin/dnf'}


class PackageIndexMissing(RuntimeError):
    pass


def run(args, **kwargs):
    return subprocess.run(args, check=False, text=True, **kwargs)


def distro_family(text):
    fields = {}
    for line in text.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            fields[key] = value.strip().strip('"\'')
    names = set((fields.get('ID', '') + ' ' + fields.get('ID_LIKE', '')).split())
    if names & {'debian', 'ubuntu', 'linuxmint'}:
        return 'apt'
    if names & {'fedora', 'rhel', 'centos', 'rocky', 'almalinux'}:
        return 'dnf'
    return None


def parse_ldd(text, returncode):
    missing = sorted(set(re.findall(r'^\s*(\S+)\s+=>\s+not found\s*$', text, re.MULTILINE)))
    # A newer glibc/libstdc++ ABI is a distro compatibility boundary, not a
    # library-install invitation. Never attempt a system libc upgrade here.
    if re.search(r'(GLIBC|GLIBCXX|CXXABI)_[0-9.]+.*not found', text):
        raise RuntimeError('This Linux version has an unsupported glibc/C++ runtime. Use a supported newer distribution; Setup will not upgrade system libc.')
    if returncode or (not missing and '=>' not in text):
        raise RuntimeError('Could not inspect application libraries with ldd. ' + text.strip()[:1000])
    return missing


def probe(app_dir):
    binary = app_dir / 'MattsSDKBoostingTools'
    if not binary.is_file():
        raise RuntimeError('The MSBT package is incomplete: application executable is missing.')
    if not Path('/usr/bin/ldd').is_file():
        raise RuntimeError('The system ldd tool is unavailable. Setup cannot verify desktop libraries.')
    result = run(['/usr/bin/ldd', str(binary)], capture_output=True)
    return parse_ldd(result.stdout + result.stderr, result.returncode)


def apt_available(name):
    result = run(['/usr/bin/apt-cache', 'show', name], capture_output=True)
    return result.returncode == 0 and f'Package: {name}\n' in result.stdout


def package_plan(missing, family, available=None):
    available = available or apt_available
    if family not in MANAGERS:
        raise RuntimeError('Automatic requirements repair supports Debian/Ubuntu/Mint and Fedora/RHEL-like distributions only. Install these desktop libraries with your distribution tools: ' + ', '.join(missing))
    unknown = sorted(set(missing) - PACKAGES.keys())
    if unknown:
        raise RuntimeError('Setup cannot safely map this missing library to a supported package: ' + ', '.join(unknown))
    packages = set()
    for soname in missing:
        row = PACKAGES.get(soname)
        if row is None:
            raise RuntimeError('Setup cannot safely map this missing library to a supported package: ' + soname)
        if family == 'apt':
            candidate = next((name for name in row[0] if available(name)), None)
            if candidate is None:
                raise PackageIndexMissing('No supported package is available for ' + soname + '. Refresh your distribution package lists or install the library with its package manager.')
        else:
            candidate = row[1]
        packages.add(candidate)
    return sorted(packages)


def package_command(family, packages):
    allowed = {name for row in PACKAGES.values() for name in (row[0] if family == 'apt' else [row[1]])}
    allowed.add('protontricks')
    if family not in MANAGERS or not packages or not set(packages) <= allowed:
        raise RuntimeError('Refusing an unrecognized package-manager request.')
    if not Path(MANAGERS[family]).is_file():
        raise RuntimeError('Supported package manager is unavailable: ' + MANAGERS[family])
    if family == 'apt':
        return [MANAGERS[family], 'install', '--no-install-recommends', '-y', *packages]
    return [MANAGERS[family], 'install', '-y', *packages]


def dialog(message, question=False):
    env = os.environ.copy()
    env.pop('LD_LIBRARY_PATH', None)
    if Path('/usr/bin/zenity').is_file():
        args = ['/usr/bin/zenity', '--question' if question else '--error', '--no-markup', '--title=MSBT Setup', '--text=' + message, '--width=540']
    elif Path('/usr/bin/kdialog').is_file():
        args = ['/usr/bin/kdialog', '--title', 'MSBT Setup', '--yesno' if question else '--error', message]
    else:
        return None
    try:
        result = run(args, env=env, capture_output=True)
    except OSError:
        return None
    if result.returncode in (0, 1):
        return result.returncode == 0
    return None


def terminal_command(python, script, app_dir, ensure_protontricks=False, refresh_apt=False):
    command = [str(python), str(script), '--app-dir', str(app_dir), '--repair-terminal']
    if ensure_protontricks:
        command.append('--ensure-protontricks')
    if refresh_apt:
        command.append('--refresh-apt-index-terminal')
    for terminal, flags in [('/usr/bin/gnome-terminal', ['--wait', '--']), ('/usr/bin/konsole', ['--nofork', '-e']), ('/usr/bin/xfce4-terminal', ['--disable-server', '-x']), ('/usr/bin/xterm', ['-e']), ('/usr/bin/x-terminal-emulator', ['-e'])]:
        if Path(terminal).is_file():
            return [terminal, *flags, *command]
    raise RuntimeError('No graphical confirmation tool or visible terminal is available. Install the listed libraries with your distribution package manager and reopen Setup.')


def repair(app_dir, family, packages, terminal=False):
    command = package_command(family, packages)
    message = ('MSBT Setup needs these system packages:\n\n' + ', '.join(packages) + '\n\nInstall them using your distribution package manager? Administrator authentication may be requested. Only these packages and their dependencies will be installed; MSBT itself runs as your normal user.')
    if terminal:
        print(message, flush=True)
        if input('Install these packages? [y/N] ').strip().lower() not in ('y', 'yes'):
            return False
        if not Path('/usr/bin/sudo').is_file():
            raise RuntimeError('sudo is unavailable in this terminal. Install the listed packages with your distribution tools.')
        return run(['/usr/bin/sudo', *command]).returncode == 0
    if Path('/usr/bin/pkexec').is_file():
        accepted = dialog(message, question=True)
        if accepted is False:
            return False
        if accepted is True:
            result = run(['/usr/bin/pkexec', *command], capture_output=True)
            if result.returncode:
                raise RuntimeError('Package installation was cancelled or failed. Reopen Setup to retry.\n' + result.stderr.strip()[-1800:])
            return True
    result = run(terminal_command(sys.executable, Path(__file__).resolve(), app_dir, packages == ['protontricks']))
    return result.returncode == 0



def refresh_apt_index(app_dir, terminal=False):
    """Refresh only distro package indexes after consent; never installs packages."""
    command = ['/usr/bin/apt-get', 'update']
    if not Path(command[0]).is_file():
        raise RuntimeError('The apt-get package manager is unavailable.')
    message = ('MSBT could not find required packages in the local package lists. '
               'Refresh the distribution package lists now? This runs apt-get update; '
               'it does not install or upgrade packages. Administrator authentication may be requested.')
    if terminal:
        print(message, flush=True)
        if input('Refresh package lists? [y/N] ').strip().lower() not in ('y', 'yes'):
            return False
        if not Path('/usr/bin/sudo').is_file():
            raise RuntimeError('sudo is unavailable. Package lists could not be refreshed.')
        result = run(['/usr/bin/sudo', *command])
    elif Path('/usr/bin/pkexec').is_file():
        accepted = dialog(message, question=True)
        if accepted is False:
            return False
        if accepted is True:
            result = run(['/usr/bin/pkexec', *command], capture_output=True)
        else:
            result = run(terminal_command(sys.executable, Path(__file__).resolve(), app_dir, refresh_apt=True))
    else:
        result = run(terminal_command(sys.executable, Path(__file__).resolve(), app_dir, refresh_apt=True))
    if result.returncode == 3:
        return False
    if result.returncode:
        raise RuntimeError('Package-list refresh was cancelled or failed. Check your network/repository settings and reopen Setup.')
    return True


def plan_with_refresh(missing, family, app_dir, terminal=False):
    try:
        return package_plan(missing, family)
    except PackageIndexMissing:
        if family != 'apt' or not refresh_apt_index(app_dir, terminal=terminal):
            return None
        # Exactly one refresh attempt. Missing packages after this are an
        # unsupported repository state, not a reason to loop or guess names.
        return package_plan(missing, family)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-dir', type=Path, required=True)
    parser.add_argument('--probe-only', action='store_true')
    parser.add_argument('--repair-terminal', action='store_true')
    parser.add_argument('--ensure-protontricks', action='store_true')
    parser.add_argument('--refresh-apt-index-terminal', action='store_true')
    parser.add_argument('electron_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    app_dir = args.app_dir.resolve()
    try:
        missing = [] if (args.ensure_protontricks or args.refresh_apt_index_terminal) else probe(app_dir)
        family = distro_family(Path('/etc/os-release').read_text())
        if args.probe_only:
            print(json.dumps({'ok': not missing, 'missing': missing, 'family': family}))
            return 0 if not missing else 2
        if os.geteuid() == 0:
            raise RuntimeError('Run MSBT Setup as your normal desktop user. Only the package-manager operation requests administrator access.')
        if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
            raise RuntimeError('MSBT Setup requires a graphical desktop session. Reopen it after signing into your desktop.')
        if args.refresh_apt_index_terminal:
            if family != 'apt':
                raise RuntimeError('APT index refresh is only supported on Debian-family systems.')
            return 0 if refresh_apt_index(app_dir, terminal=True) else 3
        if args.ensure_protontricks:
            if not Path('/usr/bin/protontricks').is_file():
                if family == 'apt' and not apt_available('protontricks'):
                    if not refresh_apt_index(app_dir, terminal=args.repair_terminal):
                        return 3
                if family == 'apt' and not apt_available('protontricks'):
                    raise RuntimeError('protontricks is not available in configured distribution repositories. Enable the supported distribution repository, then retry game setup.')
                if not repair(app_dir, family, ['protontricks'], terminal=args.repair_terminal):
                    return 3
                if not Path('/usr/bin/protontricks').is_file():
                    raise RuntimeError('protontricks is still unavailable after installation.')
            print(json.dumps({'ok': True, 'protontricks': '/usr/bin/protontricks'}))
            return 0
        if missing:
            packages = plan_with_refresh(missing, family, app_dir, terminal=args.repair_terminal)
            if packages is None:
                return 3
            if not repair(app_dir, family, packages, terminal=args.repair_terminal):
                return 3
            remaining = probe(app_dir)
            if remaining:
                raise RuntimeError('Desktop requirements are still missing after installation: ' + ', '.join(remaining))
        if args.repair_terminal:
            return 0
        electron_args = args.electron_args
        if electron_args[:1] == ['--']:
            electron_args = electron_args[1:]
        os.execv(str(app_dir / 'MattsSDKBoostingTools'), [str(app_dir / 'MattsSDKBoostingTools'), *electron_args])
    except (OSError, RuntimeError, EOFError) as error:
        message = str(error)
        print('MSBT Setup: ' + message, file=sys.stderr)
        if args.probe_only:
            print(json.dumps({'ok': False, 'missing': [], 'family': None, 'error': message}))
        if not args.probe_only:
            dialog(message)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
