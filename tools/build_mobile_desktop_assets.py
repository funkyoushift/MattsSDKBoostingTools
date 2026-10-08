"""Bundle the actual Windows workspace/editor for Android without copying Node code."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def contract():
    preload = (ROOT / 'electron_poc/preload.js').read_text(encoding='utf-8')
    methods = dict(re.findall(r'^\s*(\w+):[^\n]*?ipcRenderer\.invoke\(["\x27]([^"\x27]+)', preload, re.M))
    events = dict(re.findall(r'^\s*(on\w+):[\s\S]*?ipcRenderer\.on\(["\x27]([^"\x27]+)', preload, re.M))
    value = {'methods': methods, 'events': events}
    return '(function(r){const c=' + json.dumps(value, separators=(',', ':')) + ';if(typeof module==="object"&&module.exports)module.exports=c;else r.MsbtDesktopContract=c;})(globalThis);\n'


def build(destination):
    desktop = ROOT / 'electron_poc'
    destination.mkdir(parents=True, exist_ok=True)
    html = (desktop / 'renderer.html').read_text(encoding='utf-8')
    files = set(re.findall(r'(?:src|href)="([^"?#]+)"', html))
    copied = set()
    while files:
        name = files.pop()
        if name in copied or ':' in name or name.startswith(('#', '/')):
            continue
        source = desktop / name
        if not source.is_file():
            continue  # hyperlinks and generated runtime URLs are not assets
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.add(name)
        if source.suffix == '.css':
            for ref in re.findall(r'url\(["\x27]?([^\)"\x27]+)', source.read_text(encoding='utf-8')):
                if ':' not in ref and not ref.startswith('#'):
                    files.add(str((Path(name).parent / ref).as_posix()))
    html = html.replace('</head>', '<script src="desktop_contract.js"></script><script src="desktop_shim.js"></script><link rel="stylesheet" href="desktop_mobile.css">\n</head>', 1)
    (destination / 'renderer.html').write_text(html, encoding='utf-8')
    (destination / 'desktop_contract.js').write_text(contract(), encoding='utf-8')
    editor_source = ROOT / 'external_app/v22_parts_codes_fixed/matt_editor'
    editor_dest = destination / 'editor'
    shutil.copytree(editor_source, editor_dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git', 'node_modules'))
    editor_html = (editor_dest / 'index.html').read_text(encoding='utf-8')
    editor_html = editor_html.replace('</head>', '<script src="../mobile_editor_shim.js"></script>\n</head>', 1)
    editor_html = editor_html.replace('</body>', '<script src="matt_editor_adapter.js"></script>\n</body>', 1)
    (editor_dest / 'index.html').write_text(editor_html, encoding='utf-8')
    shutil.copy2(ROOT / 'external_app/v22_parts_codes_fixed/matt_editor_adapter.js', editor_dest / 'matt_editor_adapter.js')
    receipt = {'workspace_sha256': hashlib.sha256((desktop / 'renderer.html').read_bytes()).hexdigest(),
               'desktop_methods': len(json.loads(re.search(r'const c=(.*);if\(', contract()).group(1))['methods']),
               'workspace_assets': len(copied), 'editor_files': sum(p.is_file() for p in editor_dest.rglob('*'))}
    (destination / 'build-receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dest', type=Path)
    parser.add_argument('--write-contract', action='store_true')
    args = parser.parse_args()
    if args.write_contract:
        (ROOT / 'electron_poc/desktop_contract.js').write_text(contract(), encoding='utf-8')
    if args.dest:
        print(json.dumps(build(args.dest)))
