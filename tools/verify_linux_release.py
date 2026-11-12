"""Verify built Linux artifacts without touching a real HOME or game installation.

Run after build_linux.py as a non-root Linux x86-64 desktop user. Requires
Python 3.12+, node, npm-ci dependencies and existing desktop libraries; headless
runners need xvfb-run. Never installs host packages. Failure receipts are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import tarfile
import tempfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory(root):
    """Include symlink targets and executable bits as well as file contents."""
    result = {}
    for file in sorted(Path(root).rglob('*')):
        key = file.relative_to(root).as_posix()
        if file.is_symlink():
            result[key] = {'link': os.readlink(file)}
        elif file.is_file():
            result[key] = {'sha256': sha256(file), 'executable': bool(file.stat().st_mode & 0o111)}
    return result


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def validate_packaged_smoke(output, version):
    rows = [json.loads(line) for line in output.splitlines() if line.strip().startswith('{')]
    require(any(isinstance(row, dict) and row.get('ok') is True
                and row.get('packaged') is True and row.get('appVersion') == version
                and isinstance(row.get('updater'), dict)
                and row['updater'].get('enabled') is True
                and not row['updater'].get('error') for row in rows),
            'Missing successful packaged smoke JSON with enabled updater')


def asar_read(archive, name):
    with Path(archive).open('rb') as stream:
        prefix = stream.read(16)
        require(len(prefix) == 16, 'Truncated ASAR header')
        header_size = struct.unpack_from('<I', prefix, 4)[0]
        json_size = struct.unpack_from('<I', prefix, 12)[0]
        require(json_size <= header_size <= 64 * 1024 * 1024, 'Invalid ASAR header')
        entry = json.loads(stream.read(json_size))
        for component in name.split('/'):
            entry = entry['files'][component]
        require(not entry.get('unpacked') and 'link' not in entry, 'Expected packed ASAR file: ' + name)
        stream.seek(8 + header_size + int(entry['offset']))
        data = stream.read(entry['size'])
        require(len(data) == entry['size'], 'Truncated ASAR entry: ' + name)
        return data


def verify_sdk_sources(archive, source, project_root):
    """Mirror build_linux.py's copytree followed by its two legal-file copies."""
    expected = {file.relative_to(source).as_posix(): file
                for file in source.rglob('*')
                if file.is_file() and '__pycache__' not in file.parts
                and file.suffix not in ('.pyc', '.pyo')}
    expected.update({'LICENSE': project_root / 'LICENSE',
                     'THIRD_PARTY_NOTICES.txt': project_root / 'docs/THIRD_PARTY_NOTICES.txt'})
    prefix = 'MattsSDKBoostingTools/'
    entries = [entry.filename for entry in archive.infolist() if not entry.is_dir()]
    require(len(entries) == len(set(entries)), 'Duplicate SDK ZIP entries')
    require(set(entries) == {prefix + name for name in expected}, 'SDK staged inventory mismatch')
    for name, file in expected.items():
        require(archive.read(prefix + name) == file.read_bytes(), 'SDK/staged-source mismatch: ' + name)


def verify_source(payload, version):
    resources = payload / 'resources'
    archive = resources / 'app.asar'
    require(json.loads(asar_read(archive, 'package.json'))['version'] == version, 'ASAR version mismatch')
    checked = 0
    for file in (ROOT / 'electron_poc').iterdir():
        if file.suffix in ('.js', '.html', '.css') and not file.name.startswith(('test_', '_tmp_')):
            require(asar_read(archive, file.name) == file.read_bytes(), 'ASAR/source mismatch: ' + file.name)
            checked += 1
    metadata = json.loads((resources / 'releases/latest.json').read_text())
    for key in ('package_version', 'app_version', 'sdkmod_version', 'electron_version', 'resources_version'):
        require(metadata[key] == version, 'Manifest version mismatch: ' + key)
    sdk = resources / 'sdkmod/MattsSDKBoostingTools.sdkmod'
    require(sha256(sdk) == sha256(ROOT / 'MattsSDKBoostingTools.sdkmod'), 'SDK artifact mismatch')
    with zipfile.ZipFile(sdk) as zf:
        require(zf.testzip() is None, 'SDK ZIP CRC failure')
        sdk_metadata = tomllib.loads(zf.read('MattsSDKBoostingTools/pyproject.toml').decode())
        require(sdk_metadata['project']['version'] == sdk_metadata['tool']['sdkmod']['version'] == version, 'SDK version mismatch')
        source = ROOT / 'mod_extracted/MattsSDKBoostingTools'
        verify_sdk_sources(zf, source, ROOT)
    for relative, source in [('sdkmods/ActorScriptDeployer', ROOT / 'tools/third_party/sdk_mods/ActorScriptDeployer'),
                             ('afk_shift', ROOT / 'tools/third_party/afk_shift')]:
        for file in source.rglob('*'):
            if file.is_file() and '__pycache__' not in file.parts and file.suffix not in ('.pyc', '.pyo'):
                require(sha256(resources / relative / file.relative_to(source)) == sha256(file), 'Companion/source mismatch: ' + str(file))
    manifest = json.loads((resources / 'afk_shift/manifest.json').read_text())
    require(sha256(resources / 'afk_shift/pakchunk90-Windows_90_P.pak') == manifest['sha256'], 'PAK manifest mismatch')
    require(sha256(resources / 'oak2/oak2-sdk.zip') == sha256(ROOT / 'electron_poc/vendor/oak2/oak2-sdk.zip'), 'Official SDK mismatch')
    require((resources / 'linux_bootstrap.py').read_bytes() == (ROOT / 'tools/linux_bootstrap.py').read_bytes(), 'Bootstrap/source mismatch')
    return {'electron_source_files': checked, 'version': version}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', '--receipt', dest='receipt', type=Path, default=ROOT / 'dist_linux/linux-platform-verification.json')
    parser.add_argument('--version', help='Require this exact public version')
    args = parser.parse_args()
    receipt = {'schema_version': 1, 'platform': 'linux', 'host': platform.platform(), 'checks': [], 'artifacts': [],
               'game_integration': {'kind': 'fixtures_only', 'live': 'NOT_TESTED'},
               'live_game': {'status': 'NOT_TESTED', 'reason': 'No actual BL4/Proton session or guest-save proof; fixtures are not gameplay.'}}
    def command(argv, *, env=None, cwd=ROOT, timeout=180):
        result = subprocess.run([str(a) for a in argv], cwd=cwd, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        require(result.returncode == 0, f'Command failed ({result.returncode}): {argv}\n{result.stdout[-6000:]}\n{result.stderr[-6000:]}')
        return result.stdout
    def check(name, action):
        record = {'name': name, 'status': 'FAIL', 'ok': False}
        receipt['checks'].append(record)
        record['evidence'] = action()
        record['status'] = 'PASS'
        record['ok'] = True
    try:
        receipt['source_commit'] = command(['git', 'rev-parse', 'HEAD']).strip()
        receipt['tree'] = command(['git', 'rev-parse', 'HEAD^{tree}']).strip()
        receipt['working_tree_status'] = command(['git', 'status', '--porcelain', '--untracked-files=normal'])
        check('native_linux_host', lambda: require(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64') and os.geteuid() != 0, 'Requires non-root Linux x86-64'))
        version = json.loads((ROOT / 'electron_poc/package.json').read_text())['version']
        receipt['version'] = version
        require(not args.version or args.version == version, 'Requested version does not match source')
        image = ROOT / f'dist_linux/MSBT-Installer-v{version}-linux-x64.AppImage'
        portable = ROOT / f'dist_linux/MSBT-Portable-v{version}-linux-x64.tar.gz'
        for file in (image, portable):
            receipt['artifacts'].append({'name': file.name, 'sha256': sha256(file), 'size': file.stat().st_size})
        with tempfile.TemporaryDirectory(prefix='msbt-linux-release-') as temporary:
            temp = Path(temporary)
            env = dict(os.environ)
            for key in ('APPIMAGE', 'APPDIR', 'MSBT_PYTHON', 'ELECTRON_RUN_AS_NODE', 'MSBT_SAVE_ROOT'):
                env.pop(key, None)
            for key, folder in [('HOME', 'home'), ('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')]:
                (temp / folder).mkdir()
                env[key] = str(temp / folder)
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            gui = [] if env.get('DISPLAY') else ['xvfb-run', '-a']
            if gui:
                require(shutil.which('xvfb-run'), 'Headless verification requires xvfb-run')
            extracted = temp / 'appimage'
            extracted.mkdir()
            check('appimage_extract', lambda: command([image, '--appimage-extract'], cwd=extracted, env=env)[-1000:])
            appdir = extracted / 'squashfs-root'
            with tarfile.open(portable) as tf:
                tf.extractall(temp / 'portable', filter='data')
            folders = list((temp / 'portable').iterdir())
            require(len(folders) == 1 and folders[0].is_dir(), 'Expected one portable root')
            moved = temp / "Relocated portable O'Brien & spaces"
            folders[0].rename(moved)
            staged = ROOT / 'dist_linux/linux-unpacked'
            def same_payload():
                baseline = inventory(staged)
                for target in (appdir, moved):
                    actual = inventory(target)
                    # AppImage adds its desktop integration files; every staged file must match.
                    for name, value in baseline.items():
                        require(actual.get(name) == value, 'Payload mismatch: ' + name)
                    if target == moved:
                        require(actual == baseline, 'Portable has unexpected files')
                return {'matched_staged_files': len(baseline)}
            check('appimage_portable_payload_parity', same_payload)
            check('portable_payload', lambda: verify_source(moved, version))
            check('appimage_payload', lambda: verify_source(appdir, version))
            python = moved / 'resources/python/bin/python3'
            check('bundled_python', lambda: command([python, '-I', '-c', 'import ssl,zlib,sqlite3,ctypes,yaml; assert yaml.__version__ == "6.0.3"; print(yaml.__version__)'], env=env))
            for label, target in [('appimage', appdir), ('portable', moved)]:
                check(label + '_desktop_requirements_probe', lambda target=target: command([target / 'resources/python/bin/python3', target / 'resources/linux_bootstrap.py', '--app-dir', target, '--probe-only'], env=env))
                def smoke(target=target):
                    output = command([*gui, target / ('AppRun' if target == appdir else 'msbt'), '--smoke'], env=env)
                    validate_packaged_smoke(output, version)
                    return output[-6000:]
                check(label + '_smoke', smoke)
            env['MSBT_PYTHON'] = str(python)
            def fixtures():
                return {script: command(['node', script], cwd=ROOT / 'electron_poc', env=env) for script in ('test_linux_runtime.js', 'test_linux_setup_service.js', 'test_linux_setup.js')}
            check('proton_integration_fixtures', fixtures)
            check('updater', lambda: command(['node', 'test_platform_release_updater.js'], cwd=ROOT / 'electron_poc', env=env))
            electron = ROOT / 'electron_poc/node_modules/.bin/electron'
            (ROOT / 'dist_unified').mkdir(exist_ok=True)
            check('per_user_install', lambda: command([*gui, electron, 'test_linux_setup_install_electron.js'], cwd=ROOT / 'electron_poc', env=env))
        receipt['status'] = 'PASS'
        return 0
    except Exception as error:
        receipt['status'] = 'FAIL'
        receipt['error'] = str(error)
        return 1
    finally:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({'status': receipt.get('status', 'FAIL'), 'receipt': str(args.receipt)}))


if __name__ == '__main__':
    raise SystemExit(main())
