"""Port of the native integer fact getter (Steam f494f8-f49532).

Executable SHA256 9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0.
The game can retain an empty/name variant instead of an absent zero cursor.
This uses the same conversions as that getter; no native mutation is issued.
"""
import struct


def value(fact):
    if fact is None:
        return 0
    raw = bytes.fromhex(fact['raw'])
    if len(raw) != 16 or raw[0] != fact['tag']:
        raise RuntimeError('Mission cursor fact representation changed')
    if raw[0] == 2:
        return struct.unpack('<i', raw[12:16])[0]
    if raw[0] == 3:
        return int(any(raw[4:12]))
    if raw[0] == 1:
        return int(any(raw[12:16]))
    return 0
