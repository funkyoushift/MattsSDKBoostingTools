"""Native integer fact getter conversions, including empty zero variants."""
import importlib.util
from pathlib import Path
import struct
import pytest

p=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools/mission_cursor.py'
s=importlib.util.spec_from_file_location('cursor_test',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


@pytest.mark.parametrize('tag,data,expected',[(2,struct.pack('<i',32),32),(2,struct.pack('<i',-1),-1),
    (1,b'\x01\0\0\0',1),(1,b'\0'*4,0),(0,b'\0'*4,0),(7,b'\x01\0\0\0',0)])
def test_integer_and_bool_and_unset_variants(tag,data,expected):
    raw=bytes([tag])+b'\0'*11+data
    assert m.value(dict(tag=tag,raw=raw.hex()))==expected


def test_missing_and_name_none_are_zero_but_nonempty_name_is_one():
    assert m.value(None)==0
    assert m.value(dict(tag=3,raw=(b'\x03'+b'\0'*15).hex()))==0
    raw=b'\x03'+b'\0'*3+b'\x01'+b'\0'*11
    assert m.value(dict(tag=3,raw=raw.hex()))==1


def test_malformed_fact_is_not_silently_accepted():
    with pytest.raises(RuntimeError):m.value(dict(tag=2,raw='00'))
