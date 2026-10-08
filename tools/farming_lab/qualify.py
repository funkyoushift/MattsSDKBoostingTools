"""Read-only current EXE function and instruction qualification receipts."""
from pathlib import Path
import bisect, hashlib, json, re, struct
import capstone, pefile
PRIMARY=Path(r'C:/Users/mwenn/Desktop/MSBT_Codex_Work/working')
OUT=Path('work/farming-qualification');OUT.mkdir(parents=True,exist_ok=True)
data=json.loads((PRIMARY/'output/trainer-feature-audit/extracted.json').read_text())
raw=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Borderlands 4/OakGame/Binaries/Win64/Borderlands4.exe').read_bytes()
pe=pefile.PE(data=raw,fast_load=True)
text=next(s for s in pe.sections if s.Name.startswith(b'.text'));blob=text.get_data()
directory=pe.OPTIONAL_HEADER.DATA_DIRECTORY[3]
pdata=pe.get_data(directory.VirtualAddress,directory.Size)
functions=sorted(struct.iter_unpack('<III',pdata[:len(pdata)//12*12]));starts=[r[0] for r in functions]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
receipts=[]
for index in (9,10,14,15,17,19,21,23,51,53,54,58,63):
 script=data['scripts'][index]; sig=re.search(r'aobscanmodule\([^,]+,[^,]+,([^\)]+)\)',script['text'])[1]
 parts=[]
 for t in sig.split():
  if re.fullmatch('[0-9a-fA-F]{2}',t):parts.append(re.escape(bytes.fromhex(t)))
  elif t in ('*','??'):parts.append(b'.')
  else:parts.append(b'.'*int(t.split('.')[1]))
 matches=[text.VirtualAddress+m.start() for m in re.finditer(b''.join(parts),blob,re.DOTALL)]
 for rva in matches:
  f=functions[bisect.bisect_right(starts,rva)-1]
  if not f[0]<=rva<f[1]:raise ValueError('No function boundary')
  code=pe.get_data(f[0],f[1]-f[0]);allins=list(md.disasm(code,f[0]));near=[ins for ins in allins if rva-110 <= ins.address < rva+180]
  receipt=dict(script=index,trainer_offset=script['offset'],rva=hex(rva),function=[hex(f[0]),hex(f[1])],context_rva=hex(rva),context=pe.get_data(rva,64).hex(' '),instructions=[f'{i.address:08x} {i.bytes.hex(" "):28s} {i.mnemonic} {i.op_str}' for i in near])
  receipts.append(receipt)
  print('SCRIPT',index,'RVA',hex(rva),'FUNCTION',receipt['function']);print('\n'.join(receipt['instructions']))
out=dict(game_sha256=hashlib.sha256(raw).hexdigest(),timestamp=pe.FILE_HEADER.TimeDateStamp,size_of_image=pe.OPTIONAL_HEADER.SizeOfImage,sites=receipts)
(OUT/'instructions.json').write_text(json.dumps(out,indent=2)+'\n')
