"""Read-only checks against installed Steam/Epic files; no process execution."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

import pefile
from compare_native_card_builds import decode, gates_from

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('card_builds', ROOT / 'mod_extracted/MattsSDKBoostingTools/native_card_builds.py')
builds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builds)


def verify(steam_path, epic_path, profile=builds.EPIC):
    expected = {
        'steam': '9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0',
        'epic': '764a4bb5403a2619a0be627de5a738e23ea021e8672f7f0e7a536697d4a06719',
    }
    if profile in builds.CURRENT_FUNCTIONS:
        expected['epic'] = {'steam-26007962': 'ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a',
                            'epic-6d531d91': '6d531d91011ae0d67ac461a3cacabc99993c279bf325dfe70ff1af00ec43c87e'}[profile]
    elif profile != builds.EPIC:
        raise ValueError('Unsupported comparison profile')
    functions = builds.CURRENT_FUNCTIONS.get(profile, builds.EPIC_FUNCTIONS)
    data = builds.CURRENT_DATA.get(profile, builds.EPIC_DATA)
    files = {'steam': steam_path, 'epic': epic_path}
    images = {}
    for store, path in files.items():
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != expected[store]:
            raise ValueError(f'{store}: executable differs from analyzed build ({digest})')
        images[store] = pefile.PE(str(path), fast_load=True)
    gates = sum((gates_from(ROOT / 'mod_extracted/MattsSDKBoostingTools' / name) for name in
                 ('native_sdk_card_probe.py','native_sdk_widget_probe.py')), [])
    mapped = builds.card_gates(profile, gates)
    if len(gates) != len(functions):
        raise ValueError('Incomplete profile')
    reference_map = {}
    normalized_instructions = 0
    for source, target in zip(gates, mapped):
        s, end, sh = source
        e, eend, eh = target
        sb, eb = images['steam'].get_data(s,end-s), images['epic'].get_data(e,eend-e)
        if hashlib.sha256(sb).hexdigest()!=sh or hashlib.sha256(eb).hexdigest()!=eh:
            raise ValueError(f'Function hash mismatch at {s:x}/{e:x}')
        sn, _, sr, sc = decode(sb,s)
        en, _, er, ec = decode(eb,e)
        if sn != en or sc != ec or len(sr) != len(er):
            raise ValueError(f'Instruction mismatch at {s:x}/{e:x}')
        normalized_instructions += sc
        for a,b in zip(sr,er):
            if a['offset']!=b['offset'] or a['kind']!=b['kind']:
                raise ValueError('Reference instruction mismatch')
            reference_map.setdefault(a['target'],set()).add(b['target'])
            if a['kind']=='branch' and s<=a['target']<end and a['target']-s != b['target']-e:
                raise ValueError('Internal control flow mismatch')
        # Every individually modified gate must fail its exact runtime digest.
        for raw, digest in ((sb,sh),(eb,eh)):
            changed=bytes([raw[0]^1])+raw[1:]
            assert hashlib.sha256(changed).hexdigest()!=digest
    if any(len(v)!=1 for v in reference_map.values()):
        raise ValueError('Conflicting shared address correspondence')
    for source,(target,*_) in functions.items():
        if source in reference_map and reference_map[source]!={target}:
            raise ValueError(f'Call target mismatch {source:x}')
    for source,target in data.items():
        if reference_map.get(source)!={target}:
            raise ValueError(f'Vtable reference mismatch {source:x}')
    for sv,ev,sd in ((0xB99E210,0xB98A050,0x8E1AA38),(0xB9B7700,0xB9A3530,0x575204C)):
        if profile in builds.CURRENT_FUNCTIONS:
            mapped_vtables = reference_map.get(sv, set())
            if len(mapped_vtables) != 1:
                raise ValueError('Constructor vtable has no unique reference')
            ev = next(iter(mapped_vtables))
        if reference_map.get(sv)!={ev}:
            raise ValueError('Constructor vtable reference mismatch')
        for store,vtable,dtor in [('steam',sv,sd),('epic',ev,builds.card_rva(profile,sd))]:
            pe=images[store]
            if struct.unpack('<Q',pe.get_data(vtable,8))[0]-pe.OPTIONAL_HEADER.ImageBase!=dtor:
                raise ValueError('Destructor vtable slot mismatch')
    return dict(ok=True, executable_sha256=expected, functions=len(gates),
                normalized_instructions=normalized_instructions,
                shared_reference_targets=len(reference_map), damaged_gate_checks=2*len(gates),
                constructor_vtable_checks=4, process_access='none', live_verified=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steam',type=Path,required=True)
    parser.add_argument('--epic',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--profile',default=builds.EPIC,choices=[builds.EPIC,*builds.CURRENT_FUNCTIONS])
    args=parser.parse_args()
    result=verify(args.steam,args.epic,args.profile)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
