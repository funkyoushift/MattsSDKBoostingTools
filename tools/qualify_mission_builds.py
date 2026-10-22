"""Recover mission Steam/Epic correspondence from read-only installed PE files.

Complete exception-table function bodies must match instruction layouts; only
relative branches and RIP displacements are normalized. Ambiguous matches are
reported and never treated as an address. This tool never opens a game process.
"""
import argparse
import bisect
import hashlib
import json
import re
import struct
from pathlib import Path

import pefile
from compare_native_card_builds import decode

CODE = (0xf19ee4, 0xd80660, 0xd82e30, 0x5f7dac, 0xd83366,
        0x3a18c8, 0x6bbfa4, 0x3d32a5c, 0x89062d0, 0x61aaf4a,
        0xce3150, 0x3df18e0, 0x3df1dfe, 0x188573c, 0x891216a,
        0xd17c02, 0x89068f2, 0x156a95a, 0x125f73e, 0x141b6f0,
        0x419fefa, 0x8d09f1a, 0x8905d9e, 0x89069ca,
        0xdcb1dc, 0x105bc10, 0xce3c18)
VTABLES = (0xb752920, 0xb7dc120, 0xb975980, 0xb973820,
           0xb973940, 0xb973a20, 0xb3f6810)
TOKENS = (0xcb80808, 0xcb80830, 0xcb80870, 0xcb80898,
          0xcb808a8, 0xcb808a0, 0xcb808b0)


def qualify(steam_path, epic_path, *, expected=None, code=None, vtables=None, tokens=None):
    CODE = tuple(code) if code is not None else globals()['CODE']
    VTABLES = tuple(vtables) if vtables is not None else globals()['VTABLES']
    TOKENS = tuple(tokens) if tokens is not None else globals()['TOKENS']
    paths = [steam_path, epic_path]
    expected = expected or ('9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0',
                '764a4bb5403a2619a0be627de5a738e23ea021e8672f7f0e7a536697d4a06719')
    digests = []
    for path, known in zip(paths, expected):
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != known:
            raise ValueError('Executable differs from the qualified source build: '+str(path))
        digests.append(digest)
    pes = [pefile.PE(str(p), fast_load=True) for p in paths]
    directory = pes[0].OPTIONAL_HEADER.DATA_DIRECTORY[3]
    functions = list(struct.iter_unpack('<III', pes[0].get_data(directory.VirtualAddress, directory.Size)))
    starts = [r[0] for r in functions]
    sections = [(s.VirtualAddress, s.get_data()) for s in pes[1].sections if s.Characteristics & 0x20000000]
    cache = {}
    references = {}

    def function(rva):
        row = functions[bisect.bisect_right(starts, rva)-1]
        if not row[0] <= rva < row[1]:
            # Leaf routines have no unwind entry. Decode through their first ret.
            import capstone as cs
            md = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_64)
            end = next(i.address+i.size for i in md.disasm(pes[0].get_data(rva, 1024), rva) if i.mnemonic == 'ret')
            return rva, end
        return row[0], row[1]

    def match(rva):
        start, end = function(rva)
        if start in cache:
            return cache[start]
        raw = pes[0].get_data(start, end-start)
        normalized, masked, refs, count = decode(raw, start)
        runs, begin = [], 0
        for pos in range(len(raw)+1):
            if pos == len(raw) or pos in masked:
                if pos > begin:
                    runs.append((begin, raw[begin:pos]))
                begin = pos+1
        offset, anchor = max(runs, key=lambda r: len(r[1]))
        candidates = []
        for section_rva, blob in sections:
            pos = blob.find(anchor)
            while pos >= 0:
                at = pos-offset
                if 0 <= at and at+len(raw) <= len(blob):
                    target = section_rva+at
                    other = blob[at:at+len(raw)]
                    try:
                        norm, _, orefs, n = decode(other, target)
                        if norm == normalized and n == count and all(
                            not start <= a['target'] < end or b['target']-target == a['target']-start
                            for a, b in zip(refs, orefs) if a['kind'] == 'branch'):
                            candidates.append(dict(rva=target, references=orefs,
                                                   sha256=hashlib.sha256(other).hexdigest()))
                    except ValueError:
                        pass
                pos = blob.find(anchor, pos+1)
        result = dict(steam_rva=start, size=len(raw), steam_sha256=hashlib.sha256(raw).hexdigest(),
                      instructions=count, references=refs, candidates=candidates)
        cache[start] = result
        if len(candidates) == 1:
            references.setdefault(start, set()).add(candidates[0]['rva'])
            for a, b in zip(refs, candidates[0]['references']):
                references.setdefault(a['target'], set()).add(b['target'])
        print(hex(start), len(raw), 'candidates', len(candidates), flush=True)
        return result

    for rva in CODE:
        match(rva)

    # Constructor/destructor RIP references independently identify vtable/data.
    needed = set(VTABLES+TOKENS)
    source_sections = [(s.VirtualAddress, s.get_data()) for s in pes[0].sections if s.Characteristics & 0x20000000]
    ref_functions = {rva: set() for rva in needed}
    for section_rva, blob in source_sections:
        for m in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....', blob, re.DOTALL):
            at = section_rva+m.start()
            target = at+7+struct.unpack('<i', m.group()[3:])[0]
            if target in needed:
                ref_functions[target].add(function(at)[0])
    for target, users in ref_functions.items():
        for start in sorted(users):
            if target in references and len(references[target]) == 1:
                break
            match(start)

    mapping = {}
    for source in CODE+VTABLES+TOKENS:
        if source in references and len(references[source]) == 1:
            mapping[source] = next(iter(references[source]))
            continue
        start, end = function(source) if source in CODE else (source, source)
        row = cache.get(start)
        if row and len(row['candidates']) == 1:
            mapping[source] = row['candidates'][0]['rva']+source-start

    # A recovered vtable slot resolves generic leaf callbacks only after the
    # corresponding body has been independently found among its candidates.
    for source in CODE:
        if source in mapping:
            continue
        start, _ = function(source)
        row = cache[start]
        found = set()
        for sv in VTABLES:
            if sv not in mapping:
                continue
            for slot in range(40):
                sa = struct.unpack('<Q', pes[0].get_data(sv+slot*8, 8))[0]-pes[0].OPTIONAL_HEADER.ImageBase
                if sa != source:
                    continue
                ea = struct.unpack('<Q', pes[1].get_data(mapping[sv]+slot*8, 8))[0]-pes[1].OPTIONAL_HEADER.ImageBase
                if any(c['rva']+source-start == ea for c in row['candidates']):
                    found.add(ea)
        if len(found) == 1:
            mapping[source] = found.pop()

    # Verify every selected complete body, including correspondences resolved
    # through callers or vtable slots rather than the first search candidate.
    spans = []
    for source in CODE:
        if source not in mapping:
            continue
        start, end = function(source)
        target = mapping[source]-(source-start)
        a = pes[0].get_data(start, end-start)
        b = pes[1].get_data(target, end-start)
        an, _, ar, ac = decode(a, start)
        bn, _, br, bc = decode(b, target)
        if an != bn or ac != bc or any(
                start <= x['target'] < end and y['target']-target != x['target']-start
                for x, y in zip(ar, br) if x['kind'] == 'branch'):
            raise ValueError('Selected complete body differs: '+hex(source))
        spans.append(dict(steam_rva=start, epic_rva=target, size=end-start,
                          steam_sha256=hashlib.sha256(a).hexdigest(),
                          epic_sha256=hashlib.sha256(b).hexdigest()))
    missing = [hex(rva) for rva in CODE+VTABLES+TOKENS if rva not in mapping]
    conflicts = {hex(rva): [hex(v) for v in sorted(values)] for rva, values in references.items() if len(values) != 1}
    sdu = json.loads((Path(__file__).parents[1]/'mod_extracted/MattsSDKBoostingTools/sdu_catalog.json').read_text())
    sizes = {int(sdu['native_reader_rva'], 16): len(bytes.fromhex(sdu['native_reader_fingerprint']))}
    fingerprints = {hex(rva): {'steam': pes[0].get_data(rva, sizes.get(rva, 32)).hex(),
                              'epic': pes[1].get_data(mapping[rva], sizes.get(rva, 32)).hex()} for rva in CODE if rva in mapping}
    return dict(schema=1, process_access='none', game_files_modified=False,
                live_epic=False, normalization='relative branches and RIP displacements only',
                files=[dict(path=str(p), sha256=digest) for p, digest in zip(paths, digests)],
                addresses={hex(k): hex(v) for k, v in sorted(mapping.items())},
                fingerprints=fingerprints, spans=spans, missing=missing, conflicts=conflicts,
                matches=list(cache.values()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steam', type=Path, required=True)
    parser.add_argument('--epic', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    receipt = qualify(args.steam, args.epic)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({'missing': receipt['missing'], 'conflicts': receipt['conflicts'], 'addresses': receipt['addresses']}))
