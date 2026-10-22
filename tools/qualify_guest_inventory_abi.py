"""Read-only guest ABI recovery. This report does not enable native profiles.

All three EXEs must match exact source hashes. Known spans are compared in full,
including leaf validators absent from PE unwind tables. Address normalization
alone does not prove external callees, indirect dispatch, or live behavior.
"""
import argparse
import bisect
import re

import capstone
import hashlib
import json
from pathlib import Path
import struct

import pefile
from compare_native_card_builds import decode

HASHES = (
    '9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0',
    'ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a',
    '6d531d91011ae0d67ac461a3cacabc99993c279bf325dfe70ff1af00ec43c87e',
)
# name, old Steam RVA, current Steam RVA, current Epic RVA, old/current size
SPANS = (
    ('initialize', 0x5800cf4, 0x583e8ce, 0x584fca0, 176, 176),
    ('copy_identity', 0x6ffbee, 0x6fd608, 0x6ff7c8, 471, 471),
    ('destroy_identity', 0x369d14, 0x368b56, 0x36ad0e, 184, 184),
    ('destroy_transaction', 0x64e12d2, 0x64e9e1e, 0x64f20c6, 44, 44),
    ('validate_full_leaf', 0x5e09814, 0x5e36cac, 0x5e41d4c, 909, 909),
    ('insert_thunk', 0x12e8e74, 0x1337700, 0x1334974, 22, 22),
    ('cleanup_wrapper', 0x5da1344, 0x5daa0b8, 0x5db7312, 47, 47),
    ('op15', 0x3db6018, 0x3db9d60, 0x3daf3f8, 395, 395),
    ('serializer', 0x6231364, 0x623a918, 0x6242dfa, 2095, 2098),
    ('drop_body', 0x1570e22, 0x156f2ee, 0x156b226, 660, 660),
    ('rpc_executor', 0x62592e7, 0x6261f2f, 0x626a401, 765, 765),
    ('initialize_tail', 0x5e09686, 0x5e36b1e, 0x5e41bbe, 107, 107),
    ('operation_dispatch', 0x5e096f2, 0x5e36b8a, 0x5e41c2a, 290, 290),
)


def compare(a, b, ar, br, size):
    an, _, ax, ac = decode(a, ar)
    bn, _, bx, bc = decode(b, br)
    same = an == bn and ac == bc
    branches = same and all(y['target'] - br == x['target'] - ar
        for x, y in zip(ax, bx)
        if x['kind'] == 'branch' and ar <= x['target'] < ar + size)
    return {'normalized_bytes_equal': same, 'internal_branches_equal': branches,
            'source_references': ax, 'target_references': bx}


def control_flow(pe_a, pe_b, start_a, start_b, size_a, size_b):
    """Match reachable instructions by edges, so block order is immaterial."""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    a = {i.address: i for i in md.disasm(pe_a.get_data(start_a, size_a), start_a)}
    b = {i.address: i for i in md.disasm(pe_b.get_data(start_b, size_b), start_b)}
    if sum(i.size for i in a.values()) != size_a or sum(i.size for i in b.values()) != size_b:
        raise ValueError('Incomplete instruction decoding')
    def label(i):
        text = i.mnemonic + ' ' + i.op_str
        text = re.sub(r'\[rip [+-] 0x[0-9a-f]+\]', '[rip RELOC]', text)
        return re.sub(r'^(j\w+|call) 0x[0-9a-f]+$', r'\1 BRANCH', text)
    pending, mapping, calls = [(start_a, start_b)], {}, {}
    while pending:
        x, y = pending.pop()
        if x in mapping:
            if mapping[x] != y:
                raise ValueError('Inconsistent control-flow correspondence')
            continue
        i, j = a[x], b[y]
        if label(i) != label(j):
            raise ValueError('Changed instruction at ' + hex(x))
        mapping[x] = y
        if i.mnemonic.startswith('j') and i.op_str.startswith('0x'):
            at, bt = int(i.op_str, 16), int(j.op_str, 16)
            if at in a and bt in b:
                pending.append((at, bt))
            else:
                if (at in a) != (bt in b):
                    raise ValueError('Changed branch boundary')
                calls.setdefault(at, set()).add(bt)
        if i.mnemonic == 'call' and i.op_str.startswith('0x'):
            calls.setdefault(int(i.op_str, 16), set()).add(int(j.op_str, 16))
        if i.mnemonic not in ('ret', 'jmp', 'int3') and x + i.size in a:
            pending.append((x + i.size, y + j.size))
    if len(mapping) != len(a) or len(set(mapping.values())) != len(b):
        raise ValueError('Incomplete or non-bijective control-flow proof')
    if any(len(v) != 1 for v in calls.values()):
        raise ValueError('Inconsistent external call mapping')
    return {'instructions': len(mapping), 'complete_bijection': True,
            'external_calls': {hex(k): hex(next(iter(v))) for k, v in calls.items()}}


def callee_span(pe, address):
    """Resolve direct jump thunks and use complete unwind spans or known leaf."""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    chain = []
    for _ in range(4):
        i = next(md.disasm(pe.get_data(address, 16), address))
        if i.mnemonic != 'jmp' or not i.op_str.startswith('0x'):
            break
        chain.append(hex(address))
        address = int(i.op_str, 16)
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[3]
    functions = list(struct.iter_unpack('<III', pe.get_data(d.VirtualAddress, d.Size)))
    row = functions[bisect.bisect_right([x[0] for x in functions], address)-1]
    if row[0] <= address < row[1]:
        size = row[1] - address
    else:
        # This leaf is the serial-object lookup; full range ends at its only ret.
        if address not in (0x56c405c, 0x56cec3c, 0x56e03bc):
            raise ValueError('Unqualified leaf callee: ' + hex(address))
        size = 103
    return address, size, chain


def serializer_proof(pes):
    spans = ((0x6231364, 2095), (0x623a918, 2098), (0x6242dfa, 2098))
    graphs = [control_flow(pes[i], pes[i+1], spans[i][0], spans[i+1][0],
                          spans[i][1], spans[i+1][1]) for i in (0, 1)]
    callees = []
    for old, steam in graphs[0]['external_calls'].items():
        epic = graphs[1]['external_calls'][steam]
        bodies = [callee_span(pe, int(rva, 16)) for pe, rva in zip(pes, (old, steam, epic))]
        checks = []
        for i in (0, 1):
            a, n, _ = bodies[i]
            b, m, _ = bodies[i+1]
            checks.append(control_flow(pes[i], pes[i+1], a, b, n, m))
        callees.append({'entry_rvas': [old, steam, epic],
                        'resolved_spans': [{'rva':hex(a), 'size':n, 'thunks':t,
                            'sha256':hashlib.sha256(pe.get_data(a,n)).hexdigest()}
                            for pe,(a,n,t) in zip(pes,bodies)], 'comparisons': checks})
    return {'comparisons': graphs, 'direct_callees': callees,
            'limit': 'Direct callee bodies checked; their transitive external/indirect targets are not qualified.'}


def wrapper_dispatch(pes):
    # Identify slots immediately following the uniquely mapped cleanup callback.
    cleanups = (0x5da1344, 0x5daa0b8, 0x5db7312)
    expected = (0x5da1374, 0x5daa0e8, 0x5db7342)
    rows = []
    for pe, cleanup, wrapper in zip(pes, cleanups, expected):
        needle = struct.pack('<Q', pe.OPTIONAL_HEADER.ImageBase + cleanup)
        slots = []
        for section in pe.sections:
            if section.Characteristics & 0x20000000:
                continue
            blob, pos = section.get_data(), 0
            while (pos := blob.find(needle, pos)) >= 0:
                if pos % 8 == 0:
                    target = struct.unpack_from('<Q', blob, pos+8)[0] - pe.OPTIONAL_HEADER.ImageBase
                    if target != wrapper:
                        raise ValueError('Cleanup-adjacent wrapper changed')
                    slots.append(hex(section.VirtualAddress + pos + 8))
                pos += 1
        if len(slots) != 3:
            raise ValueError('Unexpected wrapper dispatch slot count')
        rows.append({'wrapper_rva':hex(wrapper), 'cleanup_rva':hex(cleanup), 'dispatch_slots':slots,
                     'sha256':hashlib.sha256(pe.get_data(wrapper,64)).hexdigest()})
    comparisons = [control_flow(pes[i],pes[i+1],expected[i],expected[i+1],64,64) for i in (0,1)]
    return {'builds':rows, 'comparisons':comparisons,
            'selection':'All three cleanup-adjacent virtual slots select the same wrapper; the duplicate occupies the slot two entries earlier.'}


def recover(paths):
    for path, expected in zip(paths, HASHES):
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
                raise ValueError('Unqualified executable: ' + str(path))
    pes = [pefile.PE(str(p), fast_load=True) for p in paths]
    try:
        rows = []
        for name, old, steam, epic, old_size, size in SPANS:
            raw = [p.get_data(rva, n) for p, rva, n in
                   zip(pes, (old, steam, epic), (old_size, size, size))]
            row = {'name': name, 'rvas': [hex(x) for x in (old, steam, epic)],
                   'sizes': [old_size, size, size],
                   'sha256': [hashlib.sha256(x).hexdigest() for x in raw],
                   'old_to_steam': compare(raw[0], raw[1], old, steam, old_size),
                   'steam_to_epic': compare(raw[1], raw[2], steam, epic, size)}
            if not row['steam_to_epic']['internal_branches_equal']:
                raise ValueError('Current platforms differ: ' + name)
            if name not in ('op15', 'serializer') and not row['old_to_steam']['internal_branches_equal']:
                raise ValueError('Previously unchanged body differs: ' + name)
            # Validator uses a relative 15-entry table for operation IDs 1..15.
            if name == 'validate_full_leaf':
                tables = []
                for pe, rva, blob in zip(pes, (old, steam, epic), raw):
                    refs = decode(blob, rva)[2]
                    table = next(x['target'] for x in refs if x['kind'] == 'rip')
                    targets = [table + x[0] - rva for x in
                               struct.iter_unpack('<i', pe.get_data(table, 15 * 4))]
                    tables.append({'rva': hex(table), 'body_offsets': targets,
                                   'sha256': hashlib.sha256(pe.get_data(table,60)).hexdigest()})
                assert tables[0]['body_offsets'] == tables[1]['body_offsets'] == tables[2]['body_offsets']
                row['operation_tables'] = tables
            rows.append(row)
        return {'schema': 1, 'process_access': 'none', 'game_files_modified': False,
                'serializer_proof': serializer_proof(pes), 'wrapper_dispatch': wrapper_dispatch(pes),
                'profile_enabled': False, 'executable_sha256': list(HASHES), 'spans': rows,
                'unresolved': ['Transitive external/indirect call closure and live joined-client receipt/save persistence remain unverified.'],
                'op15_change': 'Mask 0x97 becomes 0x93; existing request flag 0x08 does not set changed bit 0x04.'}
    finally:
        for pe in pes:
            pe.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('old-steam', 'steam', 'epic', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    report = recover([args.old_steam, args.steam, args.epic])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'spans': len(report['spans']), 'profile_enabled': False, 'output': str(args.output)}))
