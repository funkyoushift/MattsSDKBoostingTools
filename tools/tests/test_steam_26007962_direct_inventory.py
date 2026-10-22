"""Current host delivery gates and executable-derived ABI; no live game calls."""
import hashlib
import importlib.util
from pathlib import Path

import capstone
import pefile
import pytest

from tools.compare_native_card_builds import decode

ROOT = Path(__file__).parents[2]
SDK = ROOT / 'mod_extracted/MattsSDKBoostingTools'


def module(name):
    spec = importlib.util.spec_from_file_location(name, SDK / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture(scope='module')
def profiles():
    direct = module('direct_inventory')
    paths = [Path('C:/Program Files (x86)/Steam/steamapps/common/Borderlands 4/OakGame/Binaries/Win64/Borderlands4.exe'),
             Path('C:/Program Files/Epic Games/Venus/OakGame/Binaries/Win64/Borderlands4.exe')]
    if not all(p.is_file() for p in paths):
        pytest.skip('Current qualified executable pair is not installed')
    images = []
    for path, (_, digest, _) in zip(paths, direct.CURRENT_PROFILES):
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest
        images.append(pefile.PE(str(path), fast_load=True))
    return direct, images


def test_current_hash_required_and_each_damaged_gate_rejected(profiles):
    direct, images = profiles
    for (name, digest, gates), image in zip(direct.CURRENT_PROFILES, images):
        assert direct.select_profile(image.get_data, digest) == (name, gates)
        with pytest.raises(RuntimeError, match='not supported'):
            direct.select_profile(image.get_data)
        with pytest.raises(RuntimeError, match='not supported'):
            direct.select_profile(image.get_data, '0' * 64)
        for damaged, _, _ in gates:
            def read(rva, size):
                raw = image.get_data(rva, size)
                return bytes([raw[0] ^ 1]) + raw[1:] if rva == damaged else raw
            with pytest.raises(RuntimeError, match='not supported'):
                direct.select_profile(read, digest)
        assert name not in module('guest_inventory').PROFILES
        assert name not in ('steam-25372571', 'epic-4845623')


def test_complete_current_store_bodies_and_internal_branches_match(profiles):
    direct, images = profiles
    for a, b in zip(direct.CURRENT_PROFILES[0][2][:6], direct.CURRENT_PROFILES[1][2][:6]):
        old, new = images[0].get_data(a[0], a[1]), images[1].get_data(b[0], b[1])
        an, _, ar, ac = decode(old, a[0])
        bn, _, br, bc = decode(new, b[0])
        assert an == bn and ac == bc and len(ar) == len(br)
        for x, y in zip(ar, br):
            assert (x['kind'], x['offset']) == (y['kind'], y['offset'])
            if x['kind'] == 'branch' and a[0] <= x['target'] < a[0] + a[1]:
                assert y['target'] - b[0] == x['target'] - a[0]


def test_native_stack_identity_insert_abi_and_cleanup(profiles):
    direct, images = profiles
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    for (_, _, gates), image in zip(direct.CURRENT_PROFILES, images):
        def instructions(index):
            rva, size, _ = gates[index]
            return [i.mnemonic + ' ' + i.op_str for i in md.disasm(image.get_data(rva, size), rva)]
        thunk = instructions(2)
        assert thunk[0] == 'cmp byte ptr [rcx - 0xcc0], 3'
        assert thunk[2] == 'add rcx, -0xe38'
        assert thunk[3] == 'jmp ' + hex(gates[3][0])
        caller = instructions(4)
        construct, destroy = 'call ' + hex(gates[0][0]), 'call ' + hex(gates[1][0])
        assert caller.index(construct) < caller.index('call qword ptr [rax + 0x30]') < caller.index(destroy)
        for expected in ('or r8d, 8', 'mov r9d, 0xffffffff', 'mov dword ptr [rsp + 0x20], 0',
                         'mov rcx, r14', 'mov rdx, r15'):
            assert expected in caller
        initializer = instructions(5)
        assert 'mov qword ptr [rcx + 0xb8], 0xf' in initializer
        assert 'mov word ptr [rcx + 0xc0], 1' in initializer
        assert 'movups xmmword ptr [rcx + 0xc4], xmm0' in initializer
        assert construct in initializer and destroy in initializer
        assert image.get_data(gates[6][0], 16).hex() == '0000000080000000ffffffff00000000'
