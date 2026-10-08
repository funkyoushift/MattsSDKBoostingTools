"""Read-only instruction comparison; never loads or executes either game.

Only relative control-flow and RIP-relative addresses are normalized. All other
instruction bytes (including field offsets, constants and registers) must match.
Candidate discovery is not authorization to call a function: inspect the report
and validate profile hashes before using the resulting addresses.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import struct

import capstone as cs
from capstone.x86_const import X86_OP_MEM, X86_REG_RIP
import pefile


def gates_from(path):
    result = []
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id.endswith('GATES') for t in node.targets):
            result.extend(ast.literal_eval(node.value))
    return result


def decode(data, rva):
    decoder = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_64)
    decoder.detail = True
    instructions = list(decoder.disasm(data, rva))
    if sum(i.size for i in instructions) != len(data):
        raise ValueError(f'Incomplete disassembly at {rva:x}')
    normalized = bytearray(data)
    masked = set()
    references = []
    for i in instructions:
        offset = i.address - rva
        if i.group(cs.CS_GRP_BRANCH_RELATIVE):
            start, size = i.imm_offset, i.imm_size
            target = i.operands[0].imm
            references.append(dict(offset=offset, kind='branch', target=target))
        elif any(o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP for o in i.operands):
            start, size = i.disp_offset, i.disp_size
            target = i.address + i.size + i.disp
            references.append(dict(offset=offset, kind='rip', target=target))
        else:
            continue
        for j in range(offset + start, offset + start + size):
            normalized[j] = 0
            masked.add(j)
    return bytes(normalized), masked, references, len(instructions)


def compare(steam_path, epic_path, root):
    steam = pefile.PE(str(steam_path), fast_load=True)
    epic = pefile.PE(str(epic_path), fast_load=True)
    files = [root / 'mod_extracted/MattsSDKBoostingTools' / name for name in
             ('native_sdk_card_probe.py', 'native_sdk_widget_probe.py')]
    gates = sum((gates_from(f) for f in files), [])
    sections = [(s.VirtualAddress, s.get_data()) for s in epic.sections if s.Characteristics & 0x20000000]
    matches = []
    for start, end, digest in gates:
        source = steam.get_data(start, end - start)
        if hashlib.sha256(source).hexdigest() != digest:
            raise ValueError(f'Steam source gate mismatch: {start:x}')
        normal, masked, refs, count = decode(source, start)
        runs = []
        run = 0
        for n in range(len(source) + 1):
            if n == len(source) or n in masked:
                if n > run:
                    runs.append((run, source[run:n]))
                run = n + 1
        anchor_offset, anchor = max(runs, key=lambda x: len(x[1]))
        candidates = []
        for section_rva, data in sections:
            pos = data.find(anchor)
            while pos >= 0:
                at = pos - anchor_offset
                if 0 <= at and at + len(source) <= len(data):
                    target = section_rva + at
                    raw = data[at:at + len(source)]
                    try:
                        other, _, other_refs, other_count = decode(raw, target)
                        if other == normal and other_count == count:
                            # Internal jumps must stay within the corresponding body.
                            same_branches = all(not start <= a['target'] < end or
                                b['target'] - target == a['target'] - start
                                for a, b in zip(refs, other_refs) if a['kind'] == 'branch')
                            if same_branches:
                                candidates.append(dict(rva=target, end=target + len(raw),
                                    sha256=hashlib.sha256(raw).hexdigest(), references=other_refs))
                    except ValueError:
                        pass
                pos = data.find(anchor, pos + 1)
        matches.append(dict(steam_rva=start, steam_end=end, steam_sha256=digest,
                            instructions=count, references=refs, candidates=candidates))
    # Constructor references independently identify model/owner vtables. Slot 0
    # identifies the deleting destructors; their tiny bodies are not unique.
    vtables = []
    known_vtables = {0x56D3CCA: 0xB99E210, 0x58CF8C4: 0xB9B7700}
    for entry in matches:
        vtable = known_vtables.get(entry['steam_rva'])
        if vtable is None or len(entry['candidates']) != 1:
            continue
        other = entry['candidates'][0]
        for a, b in zip(entry['references'], other['references']):
            if a['kind'] == 'rip' and a['target'] == vtable:
                sa = struct.unpack('<Q', steam.get_data(a['target'], 8))[0] - steam.OPTIONAL_HEADER.ImageBase
                ea = struct.unpack('<Q', epic.get_data(b['target'], 8))[0] - epic.OPTIONAL_HEADER.ImageBase
                vtables.append(dict(steam_vtable=vtable, epic_vtable=b['target'], steam_slot0=sa, epic_slot0=ea))
    for _ in range(len(matches)):
        resolved = {m['steam_rva']: m['candidates'][0]['rva'] for m in matches if len(m['candidates']) == 1}
        resolved.update({v['steam_slot0']: v['epic_slot0'] for v in vtables})
        changed = False
        for entry in matches:
            if len(entry['candidates']) <= 1:
                continue
            filtered = [c for c in entry['candidates']
                        if (entry['steam_rva'] not in resolved or c['rva'] == resolved[entry['steam_rva']])
                        and all(a['target'] not in resolved or b['target'] == resolved[a['target']]
                                for a, b in zip(entry['references'], c['references']))]
            changed |= len(filtered) != len(entry['candidates'])
            entry['candidates'] = filtered
        if not changed:
            break
    # Every shared external reference must map consistently across matched bodies.
    references = {}
    conflicts = []
    for entry in matches:
        if len(entry['candidates']) != 1:
            continue
        other = entry['candidates'][0]
        references.setdefault(entry['steam_rva'], set()).add(other['rva'])
        for a, b in zip(entry['references'], other['references']):
            references.setdefault(a['target'], set()).add(b['target'])
    for a, values in references.items():
        if len(values) != 1:
            conflicts.append(dict(steam=hex(a), epic=[hex(v) for v in sorted(values)]))
    return dict(schema=1, process_access='none', game_files_modified=False,
                normalization='relative branches and RIP-relative displacements only',
                executables={name: dict(path=str(path), sha256=hashlib.file_digest(path.open('rb'), 'sha256').hexdigest())
                             for name, path in [('steam', steam_path), ('epic', epic_path)]},
                matches=matches, vtables=vtables,
                reference_map={hex(k): [hex(v) for v in sorted(values)] for k, values in references.items()},
                reference_conflicts=conflicts, live_verified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steam', type=Path, required=True)
    parser.add_argument('--epic', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.steam, args.epic, Path(__file__).resolve().parents[1])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps({'matches': [{ 'steam': hex(m['steam_rva']), 'candidates': len(m['candidates']), 'epic': [hex(c['rva']) for c in m['candidates'][:2]]} for m in report['matches']],
                      'conflicts': report['reference_conflicts'], 'executables': report['executables']}))
