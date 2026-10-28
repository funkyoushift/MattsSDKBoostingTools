"""Build the Linux x86-64 portable desktop without Windows build tools.

Run with Python 3.12+ and Node 24/npm on PATH. Downloads are pinned and verified.
Nothing is installed into a game folder and electron-builder publishing is disabled.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PYTHON_URL = 'https://github.com/astral-sh/python-build-standalone/releases/download/20261026/cpython-3.12.16%2B20261026-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz'
PYTHON_SHA256 = 'ce4f6d0a6cfdb3bed6e44c2f9affd85943c76a42e25ad3a259002f31d6fb8a20'
PYYAML_URL = 'https://files.pythonhosted.org/packages/8b/9d/b3589d3877982d4f2329302ef98a8026e7f4443c765c46cfecc8858c6b4b/pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl'
PYYAML_SHA256 = 'ba1cc08a7ccde2d2ec775841541641e4548226580ab850948cbfda66a1befcdc'


def run(*args, cwd=ROOT):
    subprocess.run(args, cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-archive', type=Path, help='Use a cached pinned archive (hash still checked).')
    args = parser.parse_args()
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise SystemExit('This build targets Linux x86-64 only.')
    electron = ROOT / 'electron_poc'
    pkg = json.loads((electron / 'package.json').read_text())
    version = pkg['version']
    build = ROOT / 'build/linux'
    build.mkdir(parents=True, exist_ok=True)
    archive = args.python_archive or build / 'python.tar.gz'
    if not archive.exists():
        urllib.request.urlretrieve(PYTHON_URL, archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != PYTHON_SHA256:
        raise SystemExit('Pinned Linux Python archive checksum mismatch.')
    runtime = build / 'runtime'
    runtime.mkdir(exist_ok=True)
    with tarfile.open(archive) as tf:
        tf.extractall(runtime, filter='data')
    python = runtime / 'python/bin/python3'
    run(str(python), '-c', 'import ssl, zlib, sqlite3, ctypes; print("Bundled Python verified")')
    wheel = build / 'pyyaml.whl'
    if not wheel.exists():
        urllib.request.urlretrieve(PYYAML_URL, wheel)
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != PYYAML_SHA256:
        raise SystemExit('Pinned PyYAML wheel checksum mismatch.')
    with zipfile.ZipFile(wheel) as zf:
        zf.extractall(runtime / 'python/lib/python3.12/site-packages')
    run(str(python), '-c', 'import yaml; assert yaml.__version__ == "6.0.3"; print("Bundled PyYAML verified")')
    # Validate every source before staging the SDK archive; no bytecode in source.
    source = ROOT / 'mod_extracted/MattsSDKBoostingTools'
    for file in source.rglob('*.py'):
        ast.parse(file.read_bytes(), filename=str(file))
    stage = build / 'sdk-stage'
    package = stage / 'MattsSDKBoostingTools'
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(source, package, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
    shutil.copy2(ROOT / 'LICENSE', package / 'LICENSE')
    shutil.copy2(ROOT / 'docs/THIRD_PARTY_NOTICES.txt', package / 'THIRD_PARTY_NOTICES.txt')
    run(str(python), str(ROOT / 'tools/pack_sdkmod_zip.py'), str(stage), str(ROOT / 'MattsSDKBoostingTools.sdkmod'))
    run('node', 'tools/prepare_game_bundle.js')
    resources = [r for r in pkg['build']['extraResources'] if r['from'] not in ('vendor/python', 'vendor/setup/MSBT-Setup.exe')]
    resources.append({'from': str(runtime / 'python'), 'to': 'python'})
    # Full override keeps established resource paths while excluding Windows setup/Python.
    config = dict(pkg['build'])
    config['extraResources'] = resources
    config['directories'] = {'output': str(ROOT / 'dist_linux')}
    config['linux'] = {'target': ['dir'], 'category': 'Utility'}
    config['files'] = list(config['files']) + ['!vendor/linux-python/**']
    config_path = build / 'electron-builder.json'
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    run('npx', '--no-install', 'electron-builder', '--linux', '--x64', '--dir', '--publish', 'never', '--config', str(config_path), cwd=electron)
    unpacked = ROOT / 'dist_linux/linux-unpacked'
    launcher = unpacked / 'msbt'
    launcher.write_text('#!/bin/sh\nset -eu\nAPP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexport MSBT_PYTHON="$APP_DIR/resources/python/bin/python3"\nexec "$APP_DIR/MattsSDKBoostingTools" "$@"\n')
    launcher.chmod(0o755)
    shutil.copy2(ROOT / 'docs/LINUX.md', unpacked / 'LINUX-README.md')
    (unpacked / 'LINUX-PYTHON-PROVENANCE.json').write_text(json.dumps({'python': {'url': PYTHON_URL, 'sha256': PYTHON_SHA256}, 'pyyaml': {'url': PYYAML_URL, 'sha256': PYYAML_SHA256}}, indent=2) + '\n')
    # archive includes executable bits and native symlinks; ZIP would lose these.
    target = ROOT / f'dist_linux/MSBT-Portable-v{version}-linux-x64.tar.gz'
    with tarfile.open(target, 'w:gz') as tf:
        tf.add(unpacked, arcname=f'MSBT-Portable-v{version}-linux-x64')
    print(f'Built {target}\nSHA256 {hashlib.sha256(target.read_bytes()).hexdigest()}')


if __name__ == '__main__':
    main()
