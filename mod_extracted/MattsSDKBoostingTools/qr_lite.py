"""Minimal QR encoder (byte mode, ECC M) for in-game pairing overlays.

No third-party packages. Returns a square matrix of 0/1 modules (1 = dark).
"""
from __future__ import annotations

from typing import Sequence

# GF(256) for QR, primitive polynomial 0x11d
_EXP = [0] * 512
_LOG = [0] * 256


def _init_gf() -> None:
    value = 1
    for i in range(255):
        _EXP[i] = value
        _LOG[value] = i
        value <<= 1
        if value & 0x100:
            value ^= 0x11D
    for i in range(255, 512):
        _EXP[i] = _EXP[i - 255]


_init_gf()


def _gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _rs_generator(degree: int) -> list[int]:
    poly = [1]
    for i in range(degree):
        nxt = [0] * (len(poly) + 1)
        for idx, coeff in enumerate(poly):
            nxt[idx] ^= _gf_mul(coeff, _EXP[i])
            nxt[idx + 1] ^= coeff
        poly = nxt
    return poly


def _rs_encode(data: Sequence[int], ecc_len: int) -> list[int]:
    # Generator is built low-degree-first; the shift register wants highest degree first.
    gen = list(reversed(_rs_generator(ecc_len)))
    ecc = [0] * ecc_len
    for byte in data:
        factor = byte ^ ecc[0]
        ecc = ecc[1:] + [0]
        for i, coeff in enumerate(gen[1:]):
            ecc[i] ^= _gf_mul(coeff, factor)
    return ecc


# version -> (data_codewords, ecc_per_block, blocks1, data1, blocks2, data2)
# ECC level M tables from ISO/IEC 18004.
_M_BLOCKS: dict[int, tuple[int, int, int, int, int, int]] = {
    1: (16, 10, 1, 16, 0, 0),
    2: (28, 16, 1, 28, 0, 0),
    3: (44, 26, 1, 44, 0, 0),
    4: (64, 18, 2, 32, 0, 0),
    5: (86, 24, 2, 43, 0, 0),
    6: (108, 16, 4, 27, 0, 0),
    7: (124, 18, 4, 31, 0, 0),
    8: (154, 22, 2, 38, 2, 39),
    9: (182, 22, 3, 36, 2, 37),
    10: (216, 26, 4, 43, 1, 44),
}

_ALIGN: dict[int, tuple[int, ...]] = {
    1: (),
    2: (6, 18),
    3: (6, 22),
    4: (6, 26),
    5: (6, 30),
    6: (6, 34),
    7: (6, 22, 38),
    8: (6, 24, 42),
    9: (6, 26, 46),
    10: (6, 28, 50),
}


def _size_for(version: int) -> int:
    return 21 + 4 * (version - 1)


def _choose_version(data_len: int) -> int:
    # mode(4) + length(8 or 16) + data + terminator, then pad to codewords
    for version in range(1, 11):
        length_bits = 8 if version < 10 else 16
        bits = 4 + length_bits + data_len * 8 + 4
        need = (bits + 7) // 8
        if need <= _M_BLOCKS[version][0]:
            return version
    raise ValueError("QR payload too large for versions 1-10")


def _add_bits(bits: list[int], value: int, count: int) -> None:
    for i in range(count - 1, -1, -1):
        bits.append((value >> i) & 1)


def _bits_to_bytes(bits: list[int]) -> list[int]:
    padded = list(bits)
    while len(padded) % 8:
        padded.append(0)
    out: list[int] = []
    for i in range(0, len(padded), 8):
        byte = 0
        for bit in padded[i:i + 8]:
            byte = (byte << 1) | bit
        out.append(byte)
    return out


def _encode_bytes(payload: bytes, version: int) -> list[int]:
    data_cw = _M_BLOCKS[version][0]
    bits: list[int] = []
    _add_bits(bits, 0b0100, 4)
    _add_bits(bits, len(payload), 8 if version < 10 else 16)
    for byte in payload:
        _add_bits(bits, byte, 8)
    remain = data_cw * 8 - len(bits)
    _add_bits(bits, 0, min(4, remain))
    # Pad to the next codeword boundary. Already-aligned streams stay aligned.
    if len(bits) % 8:
        _add_bits(bits, 0, 8 - (len(bits) % 8))
    raw = _bits_to_bytes(bits)
    pad = (0xEC, 0x11)
    idx = 0
    while len(raw) < data_cw:
        raw.append(pad[idx % 2])
        idx += 1
    return raw[:data_cw]


def _ecc_blocks(data: list[int], version: int) -> list[int]:
    _total, ecc_len, b1, d1, b2, d2 = _M_BLOCKS[version]
    blocks: list[tuple[list[int], list[int]]] = []
    offset = 0
    for _ in range(b1):
        chunk = data[offset:offset + d1]
        offset += d1
        blocks.append((chunk, _rs_encode(chunk, ecc_len)))
    for _ in range(b2):
        chunk = data[offset:offset + d2]
        offset += d2
        blocks.append((chunk, _rs_encode(chunk, ecc_len)))
    interleaved: list[int] = []
    max_data = max(len(block[0]) for block in blocks)
    for i in range(max_data):
        for chunk, _ecc in blocks:
            if i < len(chunk):
                interleaved.append(chunk[i])
    for i in range(ecc_len):
        for _chunk, ecc in blocks:
            interleaved.append(ecc[i])
    return interleaved


def _in_finder(row: int, col: int, size: int) -> bool:
    return (
        (row < 9 and col < 9)
        or (row < 9 and col >= size - 8)
        or (row >= size - 8 and col < 9)
    )


def _in_timing(row: int, col: int) -> bool:
    return row == 6 or col == 6


def _alignment_centers(version: int) -> tuple[int, ...]:
    return _ALIGN.get(version, ())


def _in_alignment(row: int, col: int, version: int, size: int) -> bool:
    centers = _alignment_centers(version)
    for r in centers:
        for c in centers:
            if r < 9 and c < 9:
                continue
            if r < 9 and c > size - 10:
                continue
            if r > size - 10 and c < 9:
                continue
            if abs(row - r) <= 2 and abs(col - c) <= 2:
                return True
    return False


def _reserved(row: int, col: int, version: int, size: int) -> bool:
    if _in_finder(row, col, size):
        return True
    if _in_timing(row, col):
        return True
    if _in_alignment(row, col, version, size):
        return True
    if row == 8 and (col < 9 or col >= size - 8):
        return True
    if col == 8 and (row < 9 or row >= size - 8):
        return True
    if version >= 7 and row < 6 and col >= size - 11:
        return True
    if version >= 7 and col < 6 and row >= size - 11:
        return True
    return False


def _draw_finder(matrix: list[list[int]], row: int, col: int) -> None:
    for r in range(-1, 8):
        for c in range(-1, 8):
            rr, cc = row + r, col + c
            if not (0 <= rr < len(matrix) and 0 <= cc < len(matrix)):
                continue
            dark = (
                (0 <= r <= 6 and 0 <= c <= 6 and (r in (0, 6) or c in (0, 6)))
                or (2 <= r <= 4 and 2 <= c <= 4)
            )
            if 0 <= r <= 6 and 0 <= c <= 6:
                matrix[rr][cc] = 1 if dark else 0


def _draw_alignment(matrix: list[list[int]], row: int, col: int) -> None:
    for r in range(-2, 3):
        for c in range(-2, 3):
            matrix[row + r][col + c] = 1 if max(abs(r), abs(c)) != 1 else 0


def _place_function(matrix: list[list[int]], version: int) -> None:
    size = len(matrix)
    _draw_finder(matrix, 0, 0)
    _draw_finder(matrix, 0, size - 7)
    _draw_finder(matrix, size - 7, 0)
    for i in range(8):
        if i < 7:
            matrix[i][7] = 0
            matrix[7][i] = 0
            matrix[i][size - 8] = 0
            matrix[7][size - 7 + i] = 0 if i else matrix[7][size - 7]
            matrix[size - 8][i] = 0
            matrix[size - 7 + i][7] = 0 if i else matrix[size - 7][7]
        matrix[8][size - 8] = 1
    for i in range(size):
        if not _in_finder(i, 6, size):
            matrix[i][6] = 1 if i % 2 == 0 else 0
        if not _in_finder(6, i, size):
            matrix[6][i] = 1 if i % 2 == 0 else 0
    centers = _alignment_centers(version)
    for r in centers:
        for c in centers:
            if r < 9 and c < 9:
                continue
            if r < 9 and c > size - 10:
                continue
            if r > size - 10 and c < 9:
                continue
            _draw_alignment(matrix, r, c)


def _mask_fn(mask: int, row: int, col: int) -> bool:
    if mask == 0:
        return (row + col) % 2 == 0
    if mask == 1:
        return row % 2 == 0
    if mask == 2:
        return col % 3 == 0
    if mask == 3:
        return (row + col) % 3 == 0
    if mask == 4:
        return (row // 2 + col // 3) % 2 == 0
    if mask == 5:
        return (row * col) % 2 + (row * col) % 3 == 0
    if mask == 6:
        return ((row * col) % 2 + (row * col) % 3) % 2 == 0
    return ((row + col) % 2 + (row * col) % 3) % 2 == 0


def _place_data(matrix: list[list[int]], data: list[int], version: int, mask: int) -> None:
    size = len(matrix)
    bits: list[int] = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    idx = 0
    going_up = True
    col = size - 1
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(size - 1, -1, -1) if going_up else range(size)
        for row in rows:
            for c in (col, col - 1):
                if _reserved(row, c, version, size):
                    continue
                bit = bits[idx] if idx < len(bits) else 0
                if _mask_fn(mask, row, c):
                    bit ^= 1
                matrix[row][c] = bit
                idx += 1
        going_up = not going_up
        col -= 2


def _bch_format(value: int) -> int:
    data = value << 10
    poly = 0x537
    for i in range(14, 9, -1):
        if data & (1 << i):
            data ^= poly << (i - 10)
    return ((value << 10) | data) ^ 0x5412


def _bch_version(version: int) -> int:
    data = version << 12
    poly = 0x1F25
    for i in range(17, 11, -1):
        if data & (1 << i):
            data ^= poly << (i - 12)
    return (version << 12) | data


def _draw_version(matrix: list[list[int]], version: int) -> None:
    if version < 7:
        return
    bits = _bch_version(version)
    size = len(matrix)
    for i in range(18):
        bit = (bits >> i) & 1
        row = size - 11 + (i % 3)
        col = i // 3
        matrix[row][col] = bit
        matrix[col][row] = bit


def _draw_format(matrix: list[list[int]], mask: int) -> None:
    # ECC M = 00. Format bits are placed MSB-first at (8,0).
    fmt = _bch_format((0b00 << 3) | mask)
    size = len(matrix)
    bits = [(fmt >> i) & 1 for i in range(14, -1, -1)]
    positions_a = [
        (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 7), (8, 8),
        (7, 8), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8),
    ]
    positions_b = [
        (size - 1, 8), (size - 2, 8), (size - 3, 8), (size - 4, 8), (size - 5, 8),
        (size - 6, 8), (size - 7, 8),
        (8, size - 8), (8, size - 7), (8, size - 6), (8, size - 5), (8, size - 4),
        (8, size - 3), (8, size - 2), (8, size - 1),
    ]
    for bit, (r, c) in zip(bits, positions_a):
        matrix[r][c] = bit
    for bit, (r, c) in zip(bits, positions_b):
        matrix[r][c] = bit
    matrix[size - 8][8] = 1


def _penalty(matrix: list[list[int]]) -> int:
    size = len(matrix)
    score = 0
    for row in range(size):
        run = 1
        for col in range(1, size):
            if matrix[row][col] == matrix[row][col - 1]:
                run += 1
            else:
                if run >= 5:
                    score += 3 + (run - 5)
                run = 1
        if run >= 5:
            score += 3 + (run - 5)
    for col in range(size):
        run = 1
        for row in range(1, size):
            if matrix[row][col] == matrix[row - 1][col]:
                run += 1
            else:
                if run >= 5:
                    score += 3 + (run - 5)
                run = 1
        if run >= 5:
            score += 3 + (run - 5)
    for row in range(size - 1):
        for col in range(size - 1):
            if matrix[row][col] == matrix[row][col + 1] == matrix[row + 1][col] == matrix[row + 1][col + 1]:
                score += 3
    dark = sum(sum(row) for row in matrix)
    percent = abs(int(dark * 100 / (size * size)) - 50) // 5
    score += percent * 10
    return score


def encode(text: str) -> list[list[int]]:
    payload = str(text or "").encode("utf-8")
    version = _choose_version(len(payload))
    data = _ecc_blocks(_encode_bytes(payload, version), version)
    size = _size_for(version)
    best: list[list[int]] | None = None
    best_score = 10 ** 9
    for mask in range(8):
        matrix = [[0] * size for _ in range(size)]
        _place_function(matrix, version)
        _place_data(matrix, data, version, mask)
        _draw_format(matrix, mask)
        _draw_version(matrix, version)
        score = _penalty(matrix)
        if score < best_score:
            best_score = score
            best = matrix
    assert best is not None
    return best
