"""Export reflected widget fields after native execution. No presentation rules."""
import struct
from .native_card_model_read import read_ui_rows


def read_widget(widget, read, fields, text_to_string):
    source_read=read
    remaining=16*1024*1024
    def read(at,size):
        nonlocal remaining
        if not isinstance(size,int) or size<0 or size>remaining:
            raise ValueError('Widget export byte budget')
        remaining-=size
        data=source_read(at,size)
        if len(data)!=size:raise ValueError('Short widget memory read')
        return data
    def string(at):
        ptr,n,cap=struct.unpack('<Qii',read(at,16))
        if not 0<=n<=cap<=16384 or n and not ptr:
            raise ValueError('Widget string bounds')
        return read(ptr,n*2).decode('utf-16-le').rstrip('\0') if n else ''
    result={}
    for field in fields:
        name,kind=field['name'],field['type']
        offset=int(field['Offset_Internal'])
        if not 0<=offset<0x608:raise ValueError('Widget field offset')
        if name in result:raise ValueError('Duplicate widget field')
        span={'ZStrProperty':16,'ZTextProperty':16,'ZBoolProperty':1,
              'ZIntProperty':4,'ZUInt32Property':4,'ZFloatProperty':4,
              'ZArrayProperty':16,'ZStructProperty':0x70}.get(kind,1)
        if offset+span>0x608:raise ValueError('Widget field span')
        at=widget+offset
        if kind=='ZStrProperty':value=string(at)
        elif kind=='ZTextProperty':
            ptr=text_to_string(at)
            value=string(ptr) if ptr else ''
        elif kind=='ZBoolProperty':value=bool(read(at,1)[0])
        elif kind in ('ZIntProperty','ZUInt32Property','ZFloatProperty'):
            value=struct.unpack({'ZIntProperty':'<i','ZUInt32Property':'<I','ZFloatProperty':'<f'}[kind],read(at,4))[0]
        elif kind=='ZStructProperty' and field.get('Struct')=="ScriptStruct'/Script/OakGame.OakWidgetData_StatEntry'":
            # Use a synthetic header for the separately validated row reader.
            header=struct.pack('<Qii',at,1,1)
            value=read_ui_rows(-1,lambda p,n:header if p==-1 and n==16 else read(p,n))[0]
        elif kind=='ZArrayProperty' and name.endswith('_Stat_Entries'):
            value=read_ui_rows(at,read)
        else:
            # Glyphs and unrelated layout helpers are not item-stat arrays.
            value={'unexported_type':kind}
        result[name]=value
    return result
