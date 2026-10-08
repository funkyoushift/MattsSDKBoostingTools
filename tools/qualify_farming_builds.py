"""Read-only Steam/Epic instruction, constructor and vtable comparison.

Only RIP displacements and relative branches are normalized. No game function
is loaded/called and no executable or process memory is changed.
"""
from pathlib import Path
import argparse, bisect, hashlib, json, re, struct, sys, types
import pefile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from compare_native_card_builds import decode
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--steam',type=Path,required=True)
parser.add_argument('--epic',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
paths=[args.steam,args.epic]
pes=[pefile.PE(str(p),fast_load=True) for p in paths]
sections=[(s.VirtualAddress,s.get_data()) for s in pes[1].sections if s.Characteristics & 0x20000000]
directory=pes[0].OPTIONAL_HEADER.DATA_DIRECTORY[3]
functions=list(struct.iter_unpack('<III',pes[0].get_data(directory.VirtualAddress,directory.Size)))
starts=[x[0] for x in functions]
receipt={'files':[dict(path=str(path),sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),timestamp=p.FILE_HEADER.TimeDateStamp,image_size=p.OPTIONAL_HEADER.SizeOfImage) for path,p in zip(paths,pes)],'matches':[],'vtables':[],'live_epic':False}
cache={}
def match(rva,size):
    if (rva,size) in cache:return cache[(rva,size)]
    code=pes[0].get_data(rva,size);normalized,masked,refs,count=decode(code,rva)
    pattern=b''.join(b'.' if i in masked else re.escape(bytes([v])) for i,v in enumerate(code))
    found=[]
    for section_rva,eblob in sections:
      for m in re.finditer(pattern,eblob,re.DOTALL):
        address=section_rva+m.start();epic=pes[1].get_data(address,size)
        norm,_,erefs,_=decode(epic,address)
        if norm==normalized:found.append(dict(rva=address,context=epic.hex(),references=erefs,sha256=hashlib.sha256(epic).hexdigest()))
    row=dict(steam_rva=rva,size=size,steam_context=code.hex(),steam_sha256=hashlib.sha256(code).hexdigest(),references=refs,candidates=found)
    receipt['matches'].append(row);cache[(rva,size)]=row
    print(hex(rva),size,'candidates',[hex(c['rva']) for c in found[:8]],flush=True)
    return row
def function_size(rva):
    f=functions[bisect.bisect_right(starts,rva)-1]
    if f[0]==rva:return f[1]-rva
    import capstone
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
    end=next(i.address+i.size for i in md.disasm(pes[0].get_data(rva,512),rva) if i.mnemonic=='ret')
    return end-rva
import importlib.util
pkg=types.ModuleType('_farming_qualify');pkg.__path__=[str(Path(__file__).resolve().parents[1]/'mod_extracted/MattsSDKBoostingTools')];sys.modules[pkg.__name__]=pkg
spec=importlib.util.spec_from_file_location('_farming_qualify.guaranteed_drops',Path(pkg.__path__[0])/'guaranteed_drops.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
spec=importlib.util.spec_from_file_location('_farming_qualify.farming_profiles',Path(pkg.__path__[0])/'farming_profiles.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
for rva,size in [(d.CONTEXT_RVA,len(d.CONTEXT)),(f.PROFILES['legendary_roll']['rva'],len(f.PROFILES['legendary_roll']['context']))]:match(rva,size)
for vt in (0xb423b10,0xb6379c0):
    constructor_targets=set()
    if vt==0xb423b10:
      for section in pes[0].sections:
        if not section.Characteristics & 0x20000000:continue
        for lea in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....',section.get_data(),re.DOTALL):
          at=section.VirtualAddress+lea.start()
          if at+7+struct.unpack('<i',lea.group()[3:])[0]!=vt:continue
          f=functions[bisect.bisect_right(starts,at)-1]
          if not f[0]<=at<f[1]:continue
          row=match(f[0],f[1]-f[0])
          if len(row['candidates'])==1:
            other=row['candidates'][0]
            constructor_targets.update(b['target'] for a,b in zip(row['references'],other['references']) if a['kind']=='rip' and a['target']==vt)
      print('Constructor targets',[hex(x) for x in constructor_targets],flush=True)
    targets=[v[0]-pes[0].OPTIONAL_HEADER.ImageBase for v in struct.iter_unpack('<Q',pes[0].get_data(vt,80))]
    index=5;row=match(targets[index],function_size(targets[index]));candidates=set()
    for c in row['candidates']:
        needle=struct.pack('<Q',pes[1].OPTIONAL_HEADER.ImageBase+c['rva'])
        candidates.update(pes[1].get_rva_from_offset(m.start())-index*8 for m in re.finditer(re.escape(needle),pes[1].__data__))
    valid=[]
    for evt in candidates:
        epic_targets=[v[0]-pes[1].OPTIONAL_HEADER.ImageBase for v in struct.iter_unpack('<Q',pes[1].get_data(evt,80))]
        checks=[]
        for srva,erva in zip(targets,epic_targets):
            size=function_size(srva)
            try:
                a,_,ar,_=decode(pes[0].get_data(srva,size),srva)
                b,_,br,_=decode(pes[1].get_data(erva,size),erva)
                if a!=b:break
                checks.append(dict(steam_rva=srva,epic_rva=erva,size=size,steam_references=ar,epic_references=br,epic_context=pes[1].get_data(erva,size).hex()))
            except (ValueError,struct.error):break
        if len(checks)==10:valid.append((evt,checks))
    if constructor_targets:valid=[v for v in valid if v[0] in constructor_targets]
    candidates={v[0] for v in valid}
    assert candidates,(hex(vt),candidates)
    if vt==0xb6379c0:assert len(candidates)==1,(hex(vt),candidates)
    for evt,checks in sorted(valid):
        epic_targets=[v[0]-pes[1].OPTIONAL_HEADER.ImageBase for v in struct.iter_unpack('<Q',pes[1].get_data(evt,80))]
        receipt['vtables'].append(dict(steam_rva=vt,epic_rva=evt,steam_targets=targets,epic_targets=epic_targets,methods=checks))
    print('VTABLE',hex(vt),[hex(v) for v in sorted(candidates)],flush=True)
receipt['ambiguous_searches']=[dict(steam_rva=m['steam_rva'],size=m['size'],candidate_count=len(m['candidates'])) for m in receipt['matches'] if len(m['candidates'])!=1]
receipt['matches']=[m for m in receipt['matches'] if len(m['candidates'])==1]
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(receipt,indent=2)+'\n')

