"""Reproduce current store correspondence without executing either game."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import pefile
import qualify_mission_builds as q


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('direct_inventory', root / 'mod_extracted/MattsSDKBoostingTools/direct_inventory.py')
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    steam, epic = native.CURRENT_PROFILES
    paths = [Path('C:/Program Files (x86)/Steam/steamapps/common/Borderlands 4/OakGame/Binaries/Win64/Borderlands4.exe'),
             Path('C:/Program Files/Epic Games/Venus/OakGame/Binaries/Win64/Borderlands4.exe')]
    receipt = q.qualify(*paths, expected=(steam[1], epic[1]),
                        code=tuple(g[0] for g in steam[2][:6]), vtables=(), tokens=())
    assert not receipt['missing'] and not receipt['conflicts']
    for a, b in zip(steam[2][:6], epic[2][:6]):
        assert receipt['addresses'][hex(a[0])] == hex(b[0])
    for path, (name, digest, gates) in zip(paths, native.CURRENT_PROFILES):
        image = pefile.PE(str(path), fast_load=True)
        assert native.select_profile(image.get_data, digest) == (name, gates)
        for rva, size, expected in gates:
            assert hashlib.sha256(image.get_data(rva, size)).hexdigest() == expected
    receipt['scope'] = 'Host direct inventory only; guest transactions and card mappings remain gated'
    receipt['abi_evidence'] = {
        'steam_identity_initializer': '0x8dc76ec',
        'steam_construct_insert_destroy_caller': '0x3db5c0a',
        'steam_authority_thunk': '0x1337700',
        'steam_insert_body': '0x1337716',
        'identity_size': '0xd8', 'owner_interface': '0xe38',
        'interface_vtable_slot': '0x30',
        'arguments': 'interface, identity, flags|8, slot=-1, final=0',
        'lifetime': 'Native caller destroys stack identity immediately after insertion returns',
        'qualification': 'Current executable-derived ABI, not unchanged implementation from game 1.10',
        'live_execution': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('Six complete store-matched bodies and all 14 runtime gates verified; no live execution')


if __name__ == '__main__':
    main()
