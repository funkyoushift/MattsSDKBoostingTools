"""Fail-closed desktop release gate. Receipts qualify packaging, not live gameplay."""
import argparse
import hashlib
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess

REQUIRED_CHECKS = {
    'win32': ('installed_payload', 'portable_payload', 'bundled_python', 'installed_smoke', 'updater'),
    'linux': ('appimage_payload', 'portable_payload', 'bundled_python', 'appimage_smoke',
              'portable_smoke', 'per_user_install', 'proton_integration_fixtures', 'updater'),
}


def expected_artifacts(version):
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('version must be a numeric public SemVer')
    return {
        'win32': [f'MSBT-Installer-v{version}.exe', f'MSBT-Portable-v{version}-win-x64.zip'],
        'linux': [f'MSBT-Installer-v{version}-linux-x64.AppImage',
                  f'MSBT-Portable-v{version}-linux-x64.tar.gz'],
    }


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _checks(platform, checks):
    if not isinstance(checks, list) or not checks:
        raise ValueError(f'{platform}: checks must be a nonempty list')
    names = []
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get('name'), str) or check.get('ok') is not True:
            raise ValueError(f'{platform}: failed or invalid check')
        names.append(check['name'])
    if len(names) != len(set(names)) or not set(REQUIRED_CHECKS[platform]).issubset(names):
        raise ValueError(f'{platform}: duplicate or missing mandatory checks')


def _integration(value):
    if not isinstance(value, dict) or value.get('kind') not in ('live', 'fixtures_only', 'not_tested'):
        raise ValueError('game_integration must explicitly qualify live coverage')
    return value


def create_platform_receipt(source_root, platform, version, checks, paths, game_integration):
    """Record successful native verification; the verifier owns executing checks."""
    if platform not in REQUIRED_CHECKS:
        raise ValueError('unsupported platform')
    _checks(platform, checks)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source_root, text=True).strip()
    artifacts = [{'name': Path(p).name, 'size': Path(p).stat().st_size,
                  'sha256': sha256_file(p)} for p in paths]
    receipt = dict(schema_version=1, platform=platform, version=version, source_commit=commit,
                   status='PASS', checks=checks, artifacts=artifacts,
                   game_integration=_integration(game_integration))
    _validate_receipt(receipt, platform, version, commit)
    return receipt


def _validate_receipt(receipt, platform, version, commit):
    if not isinstance(receipt, dict):
        raise ValueError(f'{platform}: invalid receipt')
    for key, expected in dict(schema_version=1, platform=platform, version=version,
                              source_commit=commit, status='PASS').items():
        if receipt.get(key) != expected:
            raise ValueError(f'{platform}: mismatched {key}')
    _checks(platform, receipt.get('checks'))
    _integration(receipt.get('game_integration'))
    artifacts = receipt.get('artifacts')
    if not isinstance(artifacts, list):
        raise ValueError(f'{platform}: missing artifacts')
    names = []
    for item in artifacts:
        if not isinstance(item, dict):
            raise ValueError('invalid artifact entry')
        name = item.get('name')
        if not isinstance(name, str) or not name or '/' in name or '\\' in name or ':' in name or name in ('.', '..'):
            raise ValueError('artifact names must be filenames only')
        if type(item.get('size')) is not int or item['size'] <= 0:
            raise ValueError(f'{name}: empty or invalid size')
        if not isinstance(item.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', item['sha256']):
            raise ValueError(f'{name}: invalid SHA256')
        names.append(name)
    if len(names) != len(set(names)) or set(names) != set(expected_artifacts(version)[platform]):
        raise ValueError(f'{platform}: duplicate, missing or extra artifact names')


def _live_evidence(path, version, commit, records):
    evidence = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(evidence, dict) or any(evidence.get(k) != v for k, v in
            dict(schema_version=1, version=version, source_commit=commit).items()):
        raise ValueError('live evidence does not match candidate')
    platforms = evidence.get('platforms')
    if not isinstance(platforms, dict) or set(platforms) != set(REQUIRED_CHECKS):
        raise ValueError('live evidence requires both native platforms')
    for platform, entry in platforms.items():
        if not isinstance(entry, dict) or entry.get('status') != 'PASS' or entry.get('kind') != 'live':
            raise ValueError(f'{platform}: native live evidence required')
        if not isinstance(entry.get('evidence'), str) or not entry['evidence'].strip():
            raise ValueError(f'{platform}: missing evidence reference')
        try:
            stamp = datetime.fromisoformat(entry.get('tested_at', '').replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                raise ValueError('timezone required')
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError(f'{platform}: tested_at must be timezone-qualified ISO time') from exc
        expected = {r['name']: r['sha256'] for r in records if r['platform'] == platform}
        if entry.get('artifact_sha256') != expected:
            raise ValueError(f'{platform}: live evidence artifact hashes do not match candidate')
    return evidence


def validate_gate(version, source_commit, artifacts_dir, windows_receipt, linux_receipt,
                  live_evidence=None, require_live=False):
    expected_artifacts(version)
    if not re.fullmatch('[0-9a-f]{40}', source_commit):
        raise ValueError('source commit must be a full lowercase 40-hex commit')
    records = []
    coverage = {}
    for platform, receipt_path in [('win32', windows_receipt), ('linux', linux_receipt)]:
        receipt = json.loads(Path(receipt_path).read_text(encoding='utf-8-sig'))
        _validate_receipt(receipt, platform, version, source_commit)
        coverage[platform] = receipt['game_integration']
        for item in receipt['artifacts']:
            path = Path(artifacts_dir) / item['name']
            if not path.is_file() or path.is_symlink():
                raise ValueError(f'missing or symlink artifact: {item["name"]}')
            if path.stat().st_size != item['size'] or sha256_file(path) != item['sha256']:
                raise ValueError(f'artifact size or SHA256 mismatch: {item["name"]}')
            with path.open('rb') as stream:
                magic = stream.read(4)
            signature = (b'MZ' if path.suffix == '.exe' else b'PK\x03\x04' if path.suffix == '.zip'
                         else b'\x7fELF' if path.suffix == '.AppImage' else b'\x1f\x8b')
            if not magic.startswith(signature):
                raise ValueError(f'invalid artifact format: {item["name"]}')
            records.append(dict(item, platform=platform))
    live = _live_evidence(live_evidence, version, source_commit, records) if live_evidence else None
    if require_live and live is None:
        raise ValueError('publication requires matching native live evidence for Windows and Linux')
    return dict(schema_version=1, status='PASS', version=version, source_commit=source_commit,
                artifacts=records, game_integration=coverage, publication_ready=live is not None,
                live_evidence=live,
                qualification='Both desktop platforms verified. Fixture checks do not establish live game coverage.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('version', 'source-commit', 'artifacts-dir', 'windows-receipt', 'linux-receipt', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--live-evidence')
    parser.add_argument('--require-live', action='store_true')
    args = parser.parse_args()
    output = Path(args.output)
    # Never leave a stale PASS record after a failed rerun.
    output.unlink(missing_ok=True)
    try:
        record = validate_gate(args.version, args.source_commit, args.artifacts_dir,
                               args.windows_receipt, args.linux_receipt, args.live_evidence, args.require_live)
    except (ValueError, OSError, TypeError) as exc:
        parser.exit(1, f'Release gate FAILED: {exc}\n')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print('Release gate PASS: Windows and Linux packaging verified; see live coverage qualification.')


if __name__ == '__main__':
    main()
