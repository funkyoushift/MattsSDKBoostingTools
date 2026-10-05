"""Conservative image identity, using the existing serial decoder, never item names.

Only encoding choices are erased: numeric token format and scalar/list packing.
All values, separators, part order, duplicates and unvalued parts remain distinct.
This key is not a rewritten delivery serial or proof of native card arithmetic.
"""
import hashlib
import json
import external_serial_tools as serial


def image_identity(code):
    if not isinstance(code, str) or not code.startswith('@U') or len(code) > 8192:
        return None
    if any(c not in serial.ALPHABET for c in code[2:]):
        return None
    try:
        blocks = serial.parse_serial_bytes(serial.base85_decode(code))
        if not blocks or blocks[-1]['token'] != serial.TOK_SEP1:
            return None
        tokens = []
        for block in blocks:
            kind = block['token']
            if kind in (serial.TOK_VARINT, serial.TOK_VARBIT):
                tokens.append(['number', block['value']])
            elif kind == serial.TOK_PART:
                part = block['part']
                if part['subtype'] == serial.SUBTYPE_NONE:
                    tokens.append(['bare-part', part['index']])
                else:
                    values = part['values'] if part['subtype'] == serial.SUBTYPE_LIST else [part['value']]
                    if not values:
                        return None
                    tokens.extend(['part', part['index'], value] for value in values)
            else:
                tokens.append([kind, block.get('value')])
        data = json.dumps(tokens, ensure_ascii=True, separators=(',', ':')).encode('ascii')
        return 'serial-parts-v1:' + hashlib.sha256(data).hexdigest()
    except (ValueError, KeyError, IndexError, EOFError, OverflowError):
        return None


def image_identities(codes):
    return [image_identity(code) for code in codes]
