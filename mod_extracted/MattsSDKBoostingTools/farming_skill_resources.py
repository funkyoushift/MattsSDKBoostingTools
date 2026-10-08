"""Read-only enumeration of owned charge components; mutations use native SDK APIs.

Qualified Steam 25372571 only. GbxSkill's component list is not reflected. Its
entry/instance pointers are read through ReadProcessMemory, then the native
charge getter and live ScriptStruct identity validate each SDK reference.
"""
import struct
import unrealsdk
from .guaranteed_drops import NativeMemory

CHARGES_VTABLE=0xB6379C0
CHARGES_GETTER=0x8BAE2AE
CHARGES_STRUCT_GLOBAL=0xCB9A960
ENTRY_VTABLE=0xB423B10
GETTER_CONTEXT=bytes.fromhex('48 83 ec 28 48 8b 05 a7 c6 fe 03 48 85 c0 74 05 48 83 c4 28 c3')
_memory=None

def library():
    return unrealsdk.find_object('GbxSkillComponentFunctions_Charges','/Script/OakGame.Default__GbxSkillComponentFunctions_Charges')

def references(pawn):
    global _memory
    if _memory is None:_memory=NativeMemory()
    m=_memory;m.validate()
    q=lambda address:struct.unpack('<Q',m.read(address,8))[0]
    if m.read(m.base+CHARGES_GETTER,len(GETTER_CONTEXT))!=GETTER_CONTEXT:
        raise RuntimeError('Unqualified skill-charge getter')
    cls=unrealsdk.find_object('ScriptStruct','/Script/OakGame.GbxSkillComponent_Charges')
    if q(m.base+CHARGES_STRUCT_GLOBAL)!=cls._get_address() or q(m.base+CHARGES_VTABLE+8)!=m.base+CHARGES_GETTER:
        raise RuntimeError('Skill-charge type identity changed')
    offsets={str(p.Name):int(p.Offset_Internal) for p in cls._properties()}
    attribute=unrealsdk.find_object('ScriptStruct','/Script/GbxCore.GbxAttributeInteger')
    value_offset=next(int(p.Offset_Internal) for p in attribute._properties() if str(p.Name)=='Value')
    lib=library()
    for skill in pawn.OakSkillContainer.skills:
        if skill.SkillOwner!=pawn:continue
        scripts=[s for s in skill.SkillScripts if s is not None and 'ActionSkill' in str(s.Class.Name)]
        if not scripts:continue
        array,count,capacity=struct.unpack('<QII',m.read(skill._get_address()+0x28,16))
        if count>256 or capacity<count or capacity>4096:raise RuntimeError('Invalid owned skill component list')
        for index in range(count):
            entry=q(array+index*16)
            if q(entry)!=m.base+ENTRY_VTABLE:continue
            component=q(entry+0x18)
            if q(component)!=m.base+CHARGES_VTABLE:continue
            guid=struct.unpack('<4i',m.read(component+8,16))
            reference=unrealsdk.make_struct('GbxSkillComponentReference',Context=scripts[0],
                ComponentID=unrealsdk.make_struct('Guid',**dict(zip(('A','B','C','D'),guid))))
            maximum=int(lib.GetMaxCharges(reference));current=int(lib.GetCharges(reference))
            native_max=struct.unpack('<i',m.read(component+offsets['MaxCharges']+value_offset,4))[0]
            native_current=struct.unpack('<i',m.read(component+offsets['Charges'],4))[0]
            if (maximum,current)!=(native_max,native_current) or not 0<=current<=maximum<=999:
                raise RuntimeError(f'Skill charge reference failed native/SDK readback: {skill.Name} SDK={(maximum,current)} native={(native_max,native_current)} guid={guid}')
            yield reference,dict(skill=skill._path_name(),guid=list(guid),charges=current,max_charges=maximum)

def stats(pawn):
    return [row for _,row in references(pawn)]
