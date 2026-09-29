"""Read-only validation against actual installed PE files. Requires pefile.

Usage: python tools/verify_inventory_profiles.py --steam EXE --epic EXE
Does not load or execute either game binary.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import pefile

parser = argparse.ArgumentParser()
parser.add_argument('--steam', required=True)
parser.add_argument('--epic', required=True)
args = parser.parse_args()
source = Path(__file__).resolve().parents[1] / 'mod_extracted/MattsSDKBoostingTools/direct_inventory.py'
spec = importlib.util.spec_from_file_location('native_profiles', source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
expected = {
    'steam': '9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0',
    'epic': '764a4bb5403a2619a0be627de5a738e23ea021e8672f7f0e7a536697d4a06719',
}
for store in ('steam', 'epic'):
    file = Path(getattr(args, store))
    digest = hashlib.file_digest(file.open('rb'), 'sha256').hexdigest()
    assert digest == expected[store], f'{store}: executable differs from researched build'
    pe = pefile.PE(str(file), fast_load=True)
    name, gates = mod.select_profile(pe.get_data)
    assert name.startswith(store + '-')
    # Reject every individually damaged gate, including Epic layout evidence.
    for broken_rva, _, _ in gates:
        def damaged(rva, size):
            value = pe.get_data(rva, size)
            return bytes([value[0] ^ 1]) + value[1:] if rva == broken_rva else value
        try:
            mod.select_profile(damaged)
        except RuntimeError:
            pass
        else:
            raise AssertionError(f'{store}: accepted damaged gate {broken_rva:x}')
    print(json.dumps({'profile': name, 'sha256': digest, 'gates': len(gates), 'all_damaged_gates_rejected': True}))
