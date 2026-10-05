"""Decode captured definition identities and preserve native value variants.

No inferred labels, fallback values, card formatting, or arithmetic.
"""
import struct


def definition_identity(at, read, base):
    header=read(at,64)
    identity=struct.unpack_from('<Q',header,8)[0]
    result=dict(definition_header_hex=header.hex(), identifier_components=None)
    if not identity: return result
    raw=read(identity,40)
    count=struct.unpack_from('<i',raw,4)[0]
    capacity=struct.unpack_from('<i',raw,36)[0]
    if not 0<count<=64 or capacity<0:
        raise ValueError('Invalid native definition identity')
    ptr=struct.unpack_from('<Q',raw,24)[0] if count>1 or capacity>0 else identity+8
    components=read(ptr,count*12)
    names=[]
    for i in range(count):
        index,number=struct.unpack_from('<II',components,i*12+4)
        pool=base+0xC876B00
        last=struct.unpack('<I',read(pool+8,4))[0]
        if not 0<=index>>16<=last<4096: raise ValueError('FName outside pool')
        block=struct.unpack('<Q',read(pool+16+(index>>16)*8,8))[0]
        address=block+(index&65535)*2
        flags=struct.unpack('<H',read(address,2))[0]
        length=flags>>6
        if not 0<length<=1024: raise ValueError('Invalid FName length')
        name=read(address+2,length*(2 if flags&1 else 1)).decode('utf-16-le' if flags&1 else 'ascii')
        names.append(name+('_'+str(number-1) if number else ''))
    result.update(identifier_header_hex=raw.hex(),identifier_components_hex=components.hex(),identifier_components=names)
    return result


def value_variant(raw):
    if len(raw)!=40: raise ValueError('Expected 40-byte native value variant')
    kind=raw[32]
    data_type=struct.unpack_from('<H',raw,24)[0]
    result=dict(raw_hex=raw.hex(),storage_kind=kind,data_type=data_type)
    if kind==3 and data_type==4:
        result['float_bits']=f'{struct.unpack_from("<I",raw)[0]:08x}'
    return result
