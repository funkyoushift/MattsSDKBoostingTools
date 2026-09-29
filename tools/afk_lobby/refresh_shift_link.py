"""Refresh only the source-backed AFK link in the bundled v3 PAK; no game writes."""
import hashlib
import json
import struct
import zlib
from pathlib import Path
from pak_v3 import parse_pak, extract_payload
from build_azalea_pak import fstring, CONTROLLER

ROOT = Path(__file__).resolve().parents[2]

def refresh():
    target = ROOT / 'tools/third_party/afk_shift/pakchunk90-Windows_90_P.pak'
    manifest = target.with_name('manifest.json')
    receipt = json.loads(manifest.read_text(encoding='utf-8'))
    original = target.read_bytes()
    assert hashlib.sha256(original).hexdigest() == receipt['sha256']
    pak = parse_pak(target)
    assert pak['version'] == 3 and pak['index_left'] == 0
    files = {e['name']: extract_payload(original, e) for e in pak['files']}
    controller = files[CONTROLLER]
    marker = b'/* MSBT AFK link. Appended to the existing SHiFT dashboard controller. */'
    assert controller.count(marker) == 1
    start = controller.index(marker)
    # Existing floating-controls source must remain byte-for-byte intact.
    floating = (ROOT / 'tools/afk_lobby/shift_float.js').read_bytes()
    assert controller.endswith(floating)
    files[CONTROLLER] = controller[:start] + (ROOT / 'tools/afk_lobby/shift_link.js').read_bytes() + b'\n' + floating
    payload, entries = bytearray(), []
    for name, data in sorted(files.items()):
        offset = len(payload)
        chunks = [zlib.compress(data[i:i+65536]) for i in range(0,len(data),65536)] or [zlib.compress(b'')]
        packed = b''.join(chunks)
        cursor = offset + 57 + 16*len(chunks)
        blocks=[]
        for chunk in chunks:
            blocks.append((cursor,cursor+len(chunk)));cursor+=len(chunk)
        def fields(position):
            return (struct.pack('<qqqi',position,len(packed),len(data),1)+hashlib.sha1(packed).digest()
                    +struct.pack('<i',len(blocks))+b''.join(struct.pack('<qq',a,b) for a,b in blocks)+struct.pack('<BI',0,65536))
        entries.append(fstring(name)+fields(offset));payload.extend(fields(0)+packed)
    index=fstring(pak['mount'])+struct.pack('<i',len(files))+b''.join(entries)
    result=bytes(payload)+index+struct.pack('<IIQQ',0x5A6F12E1,3,len(payload),len(index))+hashlib.sha1(index).digest()
    temporary=target.with_suffix('.pak.tmp');temporary.write_bytes(result)
    check=parse_pak(temporary)
    assert len(check['files'])==len(files) and check['index_left']==0
    for entry in check['files']:
        assert extract_payload(result,entry)==files[entry['name']]
        assert hashlib.sha1(b''.join(result[a:b] for a,b in entry['blocks'])).hexdigest()==entry['hash']
    temporary.replace(target)
    receipt['sha256']=hashlib.sha256(result).hexdigest()
    receipt['bridge_ports']=[49774,27874,27875,27876]
    manifest.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(f'PASS: {len(files)} PAK payloads verified; only AFK link replaced; '+receipt['sha256'])

if __name__=='__main__':
    refresh()
