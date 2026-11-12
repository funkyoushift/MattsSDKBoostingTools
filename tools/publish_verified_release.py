"""Check a fully qualified release; publish only with explicit --publish authorization."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

from release_gate import validate_gate, sha256_file


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def api(repository, endpoint):
    return json.loads(command('gh', 'api', f'repos/{repository}/{endpoint}'))


def list_releases(repository):
    pages = json.loads(command('gh', 'api', '--paginate', '--slurp',
                               f'repos/{repository}/releases?per_page=100'))
    return [release for page in pages for release in page]


def prepare(args):
    record = validate_gate(args.version, args.source_commit, args.artifacts_dir,
                           args.windows_receipt, args.linux_receipt, args.live_evidence, require_live=True)
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repository):
        raise ValueError('invalid repository')
    if not str(args.build_run).isdigit():
        raise ValueError('build run must be a numeric run ID')
    if not Path(args.notes).read_text(encoding='utf-8-sig').strip():
        raise ValueError('release notes are empty')
    tag = 'v' + args.version
    if command('git', 'rev-parse', f'{tag}^{{commit}}') != args.source_commit:
        raise ValueError('local tag must resolve to the verified source commit')
    remote = api(args.repository, f'git/ref/tags/{tag}')['object']
    if remote.get('type') == 'tag':
        remote = api(args.repository, 'git/tags/' + remote['sha'])['object']
    if remote.get('type') != 'commit' or remote.get('sha') != args.source_commit:
        raise ValueError('remote tag does not resolve to verified source commit')
    run = api(args.repository, f'actions/runs/{args.build_run}')
    if (run.get('status') != 'completed' or run.get('conclusion') != 'success'
            or run.get('head_sha') != args.source_commit
            or run.get('path') != '.github/workflows/unified-build.yml'):
        raise ValueError('build run must be successful unified-build at the exact source commit')
    jobs = api(args.repository, f'actions/runs/{args.build_run}/jobs?per_page=100')
    required = {'windows', 'linux', 'Required Windows and Linux release gate'}
    found = {job['name'] for job in jobs.get('jobs', [])
             if job.get('status') == 'completed' and job.get('conclusion') == 'success'}
    if not required.issubset(found):
        raise ValueError('both platform jobs and release gate must pass')
    # A successful listing is required: authentication/network errors must not mean absent.
    if any(release.get('tag_name') == tag for release in list_releases(args.repository)):
        raise ValueError('release already exists; refusing to overwrite it')
    return record


def execute(args):
    record = prepare(args)
    if not args.publish:
        return dict(status='PASS', published=False, publication_ready=True)
    tag = 'v' + args.version
    release_id = None
    stage = 'creating draft (creation outcome uncertain)'
    try:
        command('gh', 'release', 'create', tag, '--repo', args.repository, '--draft', '--verify-tag',
                '--title', tag, '--notes-file', str(args.notes))
        stage = 'locating created draft (draft may exist)'
        matches = [r for r in list_releases(args.repository) if r.get('tag_name') == tag]
        if len(matches) != 1 or matches[0].get('draft') is not True:
            raise ValueError('expected exactly one matching draft in release listing')
        release_id = matches[0]['id']
        stage = f'draft {release_id} retained; publication stopped'
        # Rehash immediately before upload; never silently upload changed local files.
        for item in record['artifacts']:
            path = Path(args.artifacts_dir) / item['name']
            if path.stat().st_size != item['size'] or sha256_file(path) != item['sha256']:
                raise ValueError('artifact changed after verification: ' + item['name'])
        command('gh', 'release', 'upload', tag, '--repo', args.repository,
                *[str(Path(args.artifacts_dir) / item['name']) for item in record['artifacts']])
        assets = api(args.repository, f'releases/{release_id}/assets?per_page=100')
        expected = {item['name']: item for item in record['artifacts']}
        if len(assets) != len(expected) or {a['name'] for a in assets} != set(expected):
            raise ValueError('remote asset set differs from verified four artifacts')
        for asset in assets:
            item = expected[asset['name']]
            if asset.get('size') != item['size'] or asset.get('digest') != 'sha256:' + item['sha256']:
                raise ValueError('remote digest/size mismatch: ' + asset['name'])
        stage = f'release {release_id} publication outcome uncertain; inspect release before retrying'
        result = json.loads(command('gh', 'api', '--method', 'PATCH',
                f'repos/{args.repository}/releases/{release_id}',
                '-F', 'draft=false', '-F', 'prerelease=false', '-f', 'make_latest=true'))
        if (result.get('id') != release_id or result.get('tag_name') != tag
                or result.get('draft') is not False or result.get('prerelease') is not False):
            raise ValueError('publication response did not confirm expected stable public release')
    except Exception as exc:
        raise RuntimeError(f'Release {tag}: {stage}: {exc}') from exc
    return dict(status='PASS', published=True, release_id=release_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('version', 'source-commit', 'artifacts-dir', 'windows-receipt', 'linux-receipt',
                 'live-evidence', 'notes', 'build-run'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--repository', default='funkyoushift/MattsSDKBoostingTools')
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(execute(args), indent=2))
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError, KeyError) as exc:
        parser.exit(1, f'Publication stopped: {exc}\n')


if __name__ == '__main__':
    main()
