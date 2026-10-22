"""Exercise the offline proof's ability to reject changed native control flow."""
import importlib.util
from pathlib import Path
import sys

import pytest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location('guest_abi_qualification', TOOLS / 'qualify_guest_inventory_abi.py')
qualification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualification)


class Image:
    def __init__(self, data):
        self.data = bytes.fromhex(data)

    def get_data(self, rva, size):
        return self.data[rva - 0x1000:rva - 0x1000 + size]


def proof(a, b):
    a, b = Image(a), Image(b)
    return qualification.control_flow(a, b, 0x1000, 0x1000, len(a.data), len(b.data))


def test_reordered_blocks_preserve_edge_identity():
    # Conditional target and fallthrough retain their own effects after a
    # terminal block moves; explicit jumps preserve the same graph.
    result = proof('85c0 7402 eb06 b801000000 c3 b802000000 c3',
                   '85c0 7408 eb00 b802000000 c3 b801000000 c3')
    assert result['complete_bijection']


def test_reject_changed_branch_target_with_same_normalized_instructions():
    with pytest.raises(ValueError):
        proof('85c0 7406 b801000000 c3 b802000000 c3',
              '85c0 7405 b801000000 c3 b802000000 c3')


def test_reject_changed_field_offset():
    with pytest.raises(ValueError, match='Changed instruction'):
        proof('8b4110 c3', '8b4114 c3')


def test_reject_undecodable_trailing_byte():
    with pytest.raises(ValueError, match='Incomplete instruction decoding'):
        proof('c3 0f', 'c3 0f')
