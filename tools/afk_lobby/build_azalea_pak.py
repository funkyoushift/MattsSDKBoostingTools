"""Build reviewed v4.4 UX source as a v3 PAK with MSBT additions. No game writes."""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
import struct
import zipfile
import zlib

from pak_v3 import parse_pak, extract_payload

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = 'js/dashboard/dashboard_controller.js'
PREFIX = 'pakchunk90-Windows_90_P/OakGame/Content/UX/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def controller_patch(data):
    text = data.decode('utf-8-sig')
    changes = {
        'if (automationSettings.friendRequestMode === "accept")':
            'if (msbtAfkManaged || automationSettings.friendRequestMode === "accept")',
        'if (automationSettings.gameInviteMode === "decline")':
            'if (msbtAfkManaged || automationSettings.gameInviteMode === "decline")',
        '    function onAutoAcceptRequestList(response)':
            '    var msbtAfkManaged = false;\n    function onAutoAcceptRequestList(response)',
        '        registerAutoAcceptResponse: function ()':
            '        setAfkManaged: function (value) { msbtAfkManaged = value === true; },\n        registerAutoAcceptResponse: function ()',
    }
    for before, after in changes.items():
        assert text.count(before) == 1, before
        text = text.replace(before, after)
    assert 'window.MsbtAfkShiftLink' not in text
    return text.encode('utf-8') + b'\n' + (ROOT / 'tools/afk_lobby/shift_link.js').read_bytes() + b'\n' + (ROOT / 'tools/afk_lobby/shift_float.js').read_bytes()


def fstring(value):
    raw = value.encode('utf-8') + b'\0'
    return struct.pack('<i', len(raw)) + raw


def build(archive, output):
    with zipfile.ZipFile(archive) as z:
        files = {}
        for info in z.infolist():
            if info.is_dir() or not info.filename.startswith(PREFIX):
                continue
            name = info.filename[len(PREFIX):]
            assert '..' not in PurePosixPath(name).parts and '\\' not in name
            assert name not in files
            files[name] = z.read(info)
    assert CONTROLLER in files and files
    source_hashes = {name: sha(data) for name, data in files.items()}
    # Supplied archive truncated this filename although dashboard.html uses the full one.
    assert 'libs/jquery-3.4.1.min.js' not in files
    assert files['libs/jquery-3.4'].startswith(b'/*! jQuery v3.4.1')
    files['libs/jquery-3.4.1.min.js'] = files.pop('libs/jquery-3.4')
    for ref in re.findall(r'<(?:script|link)\b[^>]*(?:src|href)="([^"]+)"', files['dashboard.html'].decode('utf-8-sig')):
        assert ref in files, f'Missing dashboard dependency: {ref}'
    files[CONTROLLER] = controller_patch(files[CONTROLLER])
    notification = 'NotificationWidget/js/notification_widget_controller.js'
    assert files[notification].count(b'            ShiftAutoAcceptBackground.init()') == 1
    files[notification] = files[notification].replace(
        b'            ShiftAutoAcceptBackground.init()',
        b'            // MSBT: dashboard owns automation; experimental second poller disabled.')
    payload = bytearray()
    index_entries = []
    for name, data in sorted(files.items()):
        offset = len(payload)
        chunks = [zlib.compress(data[i:i+65536]) for i in range(0, len(data), 65536)] or [zlib.compress(b'')]
        compressed = b''.join(chunks)
        cursor = offset + 57 + 16 * len(chunks)
        blocks = []
        for chunk in chunks:
            blocks.append((cursor, cursor + len(chunk)))
            cursor += len(chunk)
        def fields(entry_offset):
            return (struct.pack('<qqqi', entry_offset, len(compressed), len(data), 1)
                    + hashlib.sha1(compressed).digest() + struct.pack('<i', len(blocks))
                    + b''.join(struct.pack('<qq', a, b) for a, b in blocks)
                    + struct.pack('<BI', 0, 65536))
        index_entries.append(fstring(name) + fields(offset))
        payload.extend(fields(0) + compressed)
    index = fstring('../../../OakGame/Content/UX/') + struct.pack('<i', len(files)) + b''.join(index_entries)
    result = bytes(payload) + index + struct.pack('<IIQQ', 0x5A6F12E1, 3, len(payload), len(index)) + hashlib.sha1(index).digest()
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'pakchunk90-Windows_90_P.pak'
    target.write_bytes(result)
    check = parse_pak(target)
    assert check['index_left'] == 0 and len(check['files']) == len(files)
    for entry in check['files']:
        assert extract_payload(result, entry) == files[entry['name']], entry['name']
        packed = b''.join(result[a:b] for a, b in entry['blocks'])
        assert hashlib.sha1(packed).hexdigest() == entry['hash']
    (output / 'dashboard_controller.js').write_bytes(files[CONTROLLER])
    receipt = {'sha256': sha(result), 'source': 'Azalea SHiFT v4.4 UX source with MSBT AFK policy and floating controls',
               'source_archive_sha256': sha(archive.read_bytes()), 'entries_verified': len(files),
               'source_payload_sha256': source_hashes, 'modified_entries': [CONTROLLER, notification],
               'renamed_entries': {'libs/jquery-3.4': 'libs/jquery-3.4.1.min.js'},
               'optional_sdk_installed': False, 'validation': 'Offline payload round-trip; live game pending'}
    (output / 'manifest.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'source_payload_sha256'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(args.archive, args.output)
