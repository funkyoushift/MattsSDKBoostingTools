"""Bounded export of the recovered native model layout, not UI selection rules."""
import struct
from .native_attribute_values import definition_identity


def read_ui_rows(array, read):
    """E69A30 output: 70-byte records. No inferred filtering or formatting."""
    ptr, count, capacity = struct.unpack('<Qii', read(array, 16))
    if not 0 <= count <= capacity <= 8192 or count and not ptr:
        raise ValueError('UI row bounds')
    result = []
    for i in range(count):
        row = ptr + i * 0x70
        fields = {}
        for name, offset in (('label', 0), ('value', 0x10), ('description', 0x20),
                             ('image', 0x30), ('comparison', 0x40), ('ident', 0x58)):
            at, n, cap = struct.unpack('<Qii', read(row + offset, 16))
            if not 0 <= n <= cap <= 16384 or n and not at:
                raise ValueError('UI string bounds')
            fields[name] = read(at, n * 2).decode('utf-16-le').rstrip('\0') if n else ''
        fields['index'] = struct.unpack('<i', read(row + 0x50, 4))[0]
        fields['priority'] = struct.unpack('<f', read(row + 0x68, 4))[0]
        result.append(fields)
    return result


def read_model(model, read, base, project_array=None, *, verify_stable=False,
               include_widget_sources=False, project_single_row=None):
    original_read = read
    remaining = 16 * 1024 * 1024
    def read(at, size):
        nonlocal remaining
        if not 0 <= size <= remaining:
            raise ValueError('Model read budget')
        remaining -= size
        return original_read(at, size)
    def number(at, fmt='<Q'):
        return struct.unpack(fmt, read(at,struct.calcsize(fmt)))[0]

    def string(at):
        header=read(at,16)
        ptr,count,capacity=struct.unpack('<Qii',header)
        if not 0 <= count <= capacity <= 16384 or count and not ptr:
            raise ValueError('Model string bounds')
        value=read(ptr,count*2).decode('utf-16-le').rstrip('\0') if count else ''
        if verify_stable and read(at,16)!=header:
            raise ValueError('Model string changed during capture')
        return value

    # BAFB73..BAFCEE: map at +500, 40-byte entries, next at +32;
    # BB0AC0: E0-byte display rows. See capture_live_card_stat_groups.py.
    at=model+0x500
    header=read(at,80)
    ptr,count=struct.unpack_from('<Qi',header)
    free=struct.unpack_from('<i',header,52)[0]
    buckets=struct.unpack_from('<i',header,72)[0]
    external=struct.unpack_from('<Q',header,64)[0]
    if not 0 <= free <= count <= 4096 or not 0 <= buckets <= 8192:
        raise ValueError('Model map bounds')
    groups=[]
    total_rows=0
    if count!=free:
        if not buckets or buckets & (buckets-1):
            raise ValueError('Model map hash bounds')
        data=read(ptr,count*40)
        heads=read(external or at+56,buckets*4)
        seen=set()
        for bucket in range(buckets):
            i=struct.unpack_from('<i',heads,bucket*4)[0]
            while i!=-1:
                if not 0<=i<count or i in seen:
                    raise ValueError('Model map chain')
                seen.add(i)
                rows,n,cap=struct.unpack_from('<Qii',data,i*40+8)
                total_rows+=n
                if not 0<=n<=cap<=8192 or total_rows>8192 or n and not rows:
                    raise ValueError('Model row bounds')
                result=[]
                for j in range(n):
                    row=rows+j*0xe0
                    definition=number(row+0x88)
                    result.append(dict(definition=definition_identity(definition,read,base) if definition else None,
                        fields=[dict(offset=hex(offset),value=string(row+offset)) for offset in (8,0x38,0x68)],
                        flags=[number(row,'<B'),number(row+0x50,'<B')],priority=number(row+0x80,'<f')))
                group=dict(group_id=data[i*40],rows=result)
                if project_array is not None:
                    group['converted_ui_rows']=project_array(ptr+i*40+8)
                # 11FDE75..11FDE79 (headline) and 11FE83B..11FE842
                # (firmware) convert the first source row directly, without
                # E69A30's array visibility/empty filtering.
                if project_single_row is not None and group['group_id'] in (4,7) and n:
                    group['first_ui_row']=project_single_row(rows)
                if include_widget_sources and group['group_id']==4 and n:
                    # Opaque native key used at 11FF2CE..11FF34E. Do not
                    # interpret it as a pointer or persistent identity.
                    group['firmware_key_hex']=read(rows+0x58,8).hex()
                if verify_stable and read(ptr+i*40,40)!=data[i*40:(i+1)*40]:
                    raise ValueError('Model group changed during capture')
                groups.append(group)
                i=struct.unpack_from('<i',data,i*40+32)[0]
        if len(seen)!=count-free:
            raise ValueError('Model map incomplete')
    # Typed FString properties used by BAD682/BAC7D2/BAF88E. Keep offsets
    # explicit until the final consumer property names are independently bound.
    strings=[dict(offset=hex(offset),value=string(model+offset))
        for offset in (0x80,0xb8,0xd0,0xf0,0x1f0,0x468,0x480,0x498,0x550,0x568)]
    result=dict(display_groups=groups,strings=strings)
    if include_widget_sources:
        # Exact source offsets established by 11FC6BA and the game's reflected
        # OakWidgetData_ItemCard fields. See NATIVE_WIDGET_FIELD_BINDINGS.md.
        result['widget_sources']={
            name:string(model+offset) for name,offset in (
                ('Name',0xb8),('ItemType',0x468),('ItemBaseType',0xf0),
                ('RarityIdent',0x120),('RarityColor',0x498),
                ('ManufacturerName',0x140),('Manufacturer',0x170),
                ('Price',0x4b0),('DamageType1',0x190),('DamageType2',0x1a8),
                ('SecondElementText',0x568))}
        result['widget_sources']['level_raw']=number(model+0x44,'<i')
        result['widget_sources']['FirmwareTransfered']=bool(number(model+0x4d0,'<B'))
        result['firmware_context']=read_firmware_context(model,read,verify_stable=verify_stable)
    if verify_stable and read(at,80)!=header:
        raise ValueError('Model map changed during capture')
    return result


def read_firmware_context(model, read, *, verify_stable=False):
    """Export the +580 map consumed at 11FF2B8..11FF381, without counting items.

    Keys are capture-local opaque eight-byte values. An empty map alone does
    not prove that a live loadout was supplied to this model.
    """
    at=model+0x580
    header=read(at,80)
    ptr,count=struct.unpack_from('<Qi',header)
    free=struct.unpack_from('<i',header,52)[0]
    buckets=struct.unpack_from('<i',header,72)[0]
    external=struct.unpack_from('<Q',header,64)[0]
    if not 0<=free<=count<=4096 or not 0<=buckets<=8192:
        raise ValueError('Firmware map bounds')
    result=[]
    if count!=free:
        if not ptr or not buckets or buckets & (buckets-1):
            raise ValueError('Firmware map hash bounds')
        data=read(ptr,count*24)
        heads=read(external or at+56,buckets*4)
        seen=set()
        keys=set()
        for bucket in range(buckets):
            i=struct.unpack_from('<i',heads,bucket*4)[0]
            while i!=-1:
                if not 0<=i<count or i in seen:
                    raise ValueError('Firmware map chain')
                seen.add(i)
                row=data[i*24:(i+1)*24]
                key=row[:8].hex()
                if key in keys:raise ValueError('Firmware map duplicate key')
                keys.add(key)
                result.append(dict(key_hex=key,count=row[8]))
                if verify_stable and read(ptr+i*24,24)!=row:
                    raise ValueError('Firmware map entry changed during capture')
                i=struct.unpack_from('<i',row,16)[0]
        if len(seen)!=count-free:
            raise ValueError('Firmware map incomplete')
    if verify_stable and read(at,80)!=header:
        raise ValueError('Firmware map changed during capture')
    return result
