#!/usr/bin/env python3
import argparse
import re

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{/}~"
REV = {c: i for i, c in enumerate(ALPHABET)}

TOK_SEP1 = 0   # 00 -> |
TOK_SEP2 = 1   # 01 -> ,
TOK_VARINT = 2 # 100
TOK_VARBIT = 3 # 110
TOK_PART = 4   # 101
TOK_STRING = 5 # 111

SUBTYPE_NONE = 0
SUBTYPE_INT = 1
SUBTYPE_LIST = 2


def mirror(value, width):
    out = 0
    for i in range(width):
        out = (out << 1) | ((value >> i) & 1)
    return out


def base85_decode(serial):
    serial = serial.strip()
    if not serial.startswith("@U"):
        raise ValueError("serial must start with @U")
    s = serial[2:]
    out = bytearray()
    i = 0
    while i < len(s):
        v = 0
        count = 0
        while i < len(s) and count < 5:
            ch = s[i]
            i += 1
            if ch in REV:
                v = v * 85 + REV[ch]
                count += 1
        if count == 0:
            break
        for _ in range(5 - count):
            v = v * 85 + 84
        byte_count = 4 if count == 5 else count - 1
        for shift in (24, 16, 8, 0)[:byte_count]:
            out.append((v >> shift) & 0xFF)
    return bytes(mirror(b, 8) for b in out)


def base85_encode(data):
    data = bytes(mirror(b, 8) for b in data)
    out = []
    i = 0
    full = len(data) // 4
    extra = len(data) % 4
    for _ in range(full):
        v = (data[i] << 24) | (data[i + 1] << 16) | (data[i + 2] << 8) | data[i + 3]
        i += 4
        chars = []
        for div in (85**4, 85**3, 85**2, 85, 1):
            chars.append(ALPHABET[v // div])
            v %= div
        out.extend(chars)
    if extra:
        v = data[i]
        if extra >= 2:
            v = (v << 8) | data[i + 1]
        if extra == 3:
            v = (v << 8) | data[i + 2]
        v <<= (4 - extra) * 8
        chars = []
        for div in (85**4, 85**3, 85**2, 85, 1):
            chars.append(ALPHABET[v // div])
            v %= div
        out.extend(chars[:extra + 1])
    return "@U" + "".join(out)


class BitReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.length = len(data) * 8

    def read(self):
        if self.pos >= self.length:
            raise EOFError("unexpected end of bitstream")
        b = self.data[self.pos // 8]
        bit = (b >> (7 - (self.pos % 8))) & 1
        self.pos += 1
        return bit

    def read_n(self, n):
        if n <= 0 or n > 32 or self.pos + n > self.length:
            raise EOFError("unexpected end of bitstream")
        v = 0
        for _ in range(n):
            v = (v << 1) | self.read()
        return v

    def expect(self, bits):
        for bit in bits:
            got = self.read()
            if got != bit:
                raise ValueError(f"bad magic/header bit at {self.pos - 1}: got {got}, expected {bit}")


class BitWriter:
    def __init__(self):
        self.bits = []

    def write_bit(self, bit):
        self.bits.append(bit & 1)

    def write_bits(self, *bits):
        for bit in bits:
            self.write_bit(bit)

    def write_n(self, value, n):
        for i in range(n - 1, -1, -1):
            self.write_bit((value >> i) & 1)

    def data(self):
        out = bytearray((len(self.bits) + 7) // 8)
        for i, bit in enumerate(self.bits):
            if bit:
                out[i // 8] |= 1 << (7 - (i % 8))
        return bytes(out)


def read_token(br):
    try:
        b1 = br.read()
    except EOFError:
        return None
    b2 = br.read()
    tok2 = (b1 << 1) | b2
    if tok2 == 0:
        return TOK_SEP1
    if tok2 == 1:
        return TOK_SEP2
    b3 = br.read()
    tok3 = (tok2 << 1) | b3
    if tok3 == 0b100:
        return TOK_VARINT
    if tok3 == 0b110:
        return TOK_VARBIT
    if tok3 == 0b101:
        return TOK_PART
    if tok3 == 0b111:
        return TOK_STRING
    raise ValueError("invalid token")


def write_token(bw, tok):
    if tok == TOK_SEP1:
        bw.write_bits(0, 0)
    elif tok == TOK_SEP2:
        bw.write_bits(0, 1)
    elif tok == TOK_VARINT:
        bw.write_bits(1, 0, 0)
    elif tok == TOK_VARBIT:
        bw.write_bits(1, 1, 0)
    elif tok == TOK_PART:
        bw.write_bits(1, 0, 1)
    elif tok == TOK_STRING:
        bw.write_bits(1, 1, 1)
    else:
        raise ValueError(f"bad token {tok}")


def read_varint(br):
    data_read = 0
    out = 0
    for _ in range(4):
        block = br.read_n(4)
        out |= mirror(block, 4) << data_read
        data_read += 4
        if br.read() == 0:
            break
    return out


def write_varint(bw, value):
    nbits = max(1, value.bit_length())
    nbits = min(nbits, 16)
    while nbits > 4:
        for _ in range(4):
            bw.write_bit(value & 1)
            value >>= 1
            nbits -= 1
        bw.write_bit(1)
    for _ in range(4):
        if nbits > 0:
            bw.write_bit(value & 1)
            value >>= 1
            nbits -= 1
        else:
            bw.write_bit(0)
    bw.write_bit(0)


def read_varbit(br):
    length = mirror(br.read_n(5), 5)
    v = 0
    for i in range(length):
        v |= br.read() << i
    return v


def write_varbit(bw, value):
    nbits = max(1, value.bit_length())
    nbits = min(nbits, 31)
    for _ in range(5):
        bw.write_bit(nbits & 1)
        nbits >>= 1
    nbits = max(1, value.bit_length())
    nbits = min(nbits, 31)
    for _ in range(nbits):
        bw.write_bit(value & 1)
        value >>= 1


def varint_len(value):
    tmp = BitWriter(); write_varint(tmp, value); return len(tmp.bits)


def varbit_len(value):
    tmp = BitWriter(); write_varbit(tmp, value); return len(tmp.bits)


def best_numeric_token(value):
    return TOK_VARBIT if varint_len(value) > varbit_len(value) else TOK_VARINT


def read_string(br):
    length = read_varint(br)
    chars = []
    for _ in range(length):
        chars.append(chr(mirror(br.read_n(7), 7)))
    return "".join(chars)


def write_string(bw, s):
    write_varint(bw, len(s))
    for ch in s:
        bw.write_n(mirror(ord(ch), 7), 7)


def read_part(br):
    index = read_varint(br)
    flag1 = br.read()
    if flag1 == 1:
        value = read_varint(br)
        if [br.read(), br.read(), br.read()] != [0, 0, 0]:
            raise ValueError("bad part int terminator")
        return {"index": index, "subtype": SUBTYPE_INT, "value": value}
    flag2 = br.read_n(2)
    if flag2 == 0b10:
        return {"index": index, "subtype": SUBTYPE_NONE}
    if flag2 == 0b01:
        tok = read_token(br)
        if tok != TOK_SEP2:
            raise ValueError("expected list opening separator")
        vals = []
        while True:
            tok = read_token(br)
            if tok == TOK_SEP1:
                break
            if tok == TOK_VARINT:
                vals.append(read_varint(br))
            elif tok == TOK_VARBIT:
                vals.append(read_varbit(br))
            else:
                raise ValueError("unexpected token in part list")
        return {"index": index, "subtype": SUBTYPE_LIST, "values": vals}
    raise ValueError("unknown part subtype")


def write_part(bw, part):
    write_varint(bw, part["index"])
    subtype = part.get("subtype", SUBTYPE_NONE)
    if subtype == SUBTYPE_NONE:
        bw.write_bits(0, 1, 0)
    elif subtype == SUBTYPE_INT:
        bw.write_bit(1)
        write_varint(bw, part["value"])
        bw.write_bits(0, 0, 0)
    elif subtype == SUBTYPE_LIST:
        bw.write_bits(0, 0, 1)
        write_token(bw, TOK_SEP2)
        for v in part.get("values", []):
            tok = best_numeric_token(v)
            write_token(bw, tok)
            (write_varbit if tok == TOK_VARBIT else write_varint)(bw, v)
        write_token(bw, TOK_SEP1)
    else:
        raise ValueError(f"bad part subtype {subtype}")


def part_to_str(p):
    if p["subtype"] == SUBTYPE_NONE:
        return f"{{{p['index']}}}"
    if p["subtype"] == SUBTYPE_INT:
        return f"{{{p['index']}:{p['value']}}}"
    return f"{{{p['index']}:[{' '.join(str(v) for v in p.get('values', []))}]}}"


def parse_serial_bytes(data):
    br = BitReader(data)
    br.expect([0, 0, 1, 0, 0, 0, 0])
    blocks = []
    trailing_terms = 0
    while True:
        try:
            tok = read_token(br)
        except EOFError:
            break
        if tok is None:
            break
        block = {"token": tok}
        trailing_terms = trailing_terms + 1 if tok == TOK_SEP1 else 0
        if tok == TOK_VARINT:
            block["value"] = read_varint(br)
        elif tok == TOK_VARBIT:
            block["value"] = read_varbit(br)
        elif tok == TOK_PART:
            block["part"] = read_part(br)
        elif tok == TOK_STRING:
            block["value"] = read_string(br)
        elif tok not in (TOK_SEP1, TOK_SEP2):
            raise ValueError(f"unknown token {tok}")
        blocks.append(block)
    if trailing_terms > 1:
        blocks = blocks[:-(trailing_terms - 1)]
    return blocks


def blocks_to_bytes(blocks):
    bw = BitWriter()
    bw.write_bits(0, 0, 1, 0, 0, 0, 0)
    for b in blocks:
        tok = b["token"]
        write_token(bw, tok)
        if tok == TOK_VARINT:
            write_varint(bw, b["value"])
        elif tok == TOK_VARBIT:
            write_varbit(bw, b["value"])
        elif tok == TOK_PART:
            write_part(bw, b["part"])
        elif tok == TOK_STRING:
            write_string(bw, b["value"])
    return bw.data()


def serial_to_human(serial):
    blocks = parse_serial_bytes(base85_decode(serial))
    out = []
    for i, b in enumerate(blocks):
        tok = b["token"]
        if tok == TOK_SEP1:
            out.append("|")
        elif tok == TOK_SEP2:
            out.append(",")
        elif tok in (TOK_VARINT, TOK_VARBIT):
            if i > 0:
                out.append(" ")
            out.append(str(b["value"]))
        elif tok == TOK_PART:
            if i > 0:
                out.append(" ")
            out.append(part_to_str(b["part"]))
        elif tok == TOK_STRING:
            if i > 0:
                out.append(" ")
            s = b["value"].replace("\\", "\\\\").replace('"', '\\"')
            out.append(f'"{s}"')
    return "".join(out)


def parse_part_text(token):
    body = token.strip()[1:-1].strip()
    if ":[" in body:
        idx_s, rest = body.split(":", 1)
        vals_s = rest.strip()[1:-1].strip()
        vals = [int(x) for x in vals_s.split()] if vals_s else []
        return {"index": int(idx_s.strip()), "subtype": SUBTYPE_LIST, "values": vals}
    if ":" in body:
        idx_s, val_s = body.split(":", 1)
        return {"index": int(idx_s.strip()), "subtype": SUBTYPE_INT, "value": int(val_s.strip())}
    return {"index": int(body), "subtype": SUBTYPE_NONE}


def tokenize_human(text):
    token_re = re.compile(r'\s*(?:(?P<sep>[|,])|(?P<part>\{[^}]*\})|(?P<string>"(?:\\.|[^"])*")|(?P<int>\d+))')
    pos = 0
    toks = []
    while pos < len(text):
        m = token_re.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError(f"cannot parse near: {text[pos:pos+40]!r}")
        pos = m.end()
        kind = m.lastgroup
        value = m.group(kind)
        toks.append((kind, value))
    return toks


def human_to_serial(text):
    import ast
    blocks = []
    for kind, value in tokenize_human(text.strip()):
        if kind == "sep":
            blocks.append({"token": TOK_SEP1 if value == "|" else TOK_SEP2})
        elif kind == "int":
            n = int(value)
            blocks.append({"token": best_numeric_token(n), "value": n})
        elif kind == "part":
            blocks.append({"token": TOK_PART, "part": parse_part_text(value)})
        elif kind == "string":
            blocks.append({"token": TOK_STRING, "value": ast.literal_eval(value)})
    return base85_encode(blocks_to_bytes(blocks))


def convert_opposing(text):
    text = text.strip()
    if not text:
        raise ValueError("empty input")
    return serial_to_human(text) if text.startswith("@U") else human_to_serial(text)


def main():
    ap = argparse.ArgumentParser(description="Convert BL4 @U Base85 serials to/from nicnl human-readable form.")
    ap.add_argument("--serial", required=True, help="@U serial or nicnl-style human-readable text")
    args = ap.parse_args()
    print("--serial")
    print(convert_opposing(args.serial))


if __name__ == "__main__":
    main()
