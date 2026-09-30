"""Explicit maintenance tool: sends only extracted public UI strings for translation. Never used by the app at runtime."""
import json,urllib.request,urllib.parse,time,concurrent.futures
from pathlib import Path
root=Path('output/languages');source=json.loads((root/'english.json').read_text(encoding='utf-8-sig'))
def translate(lang):
 p=root/(lang+'.json');cache=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
 todo=[s for s in source if s not in cache];batches=[];batch=[];size=0
 for s in todo:
  if size+len(s)>2500 or len(batch)>=25:batches.append(batch);batch=[];size=0
  batch.append(s);size+=len(s)+1
 if batch:batches.append(batch)
 def call(strings):
  u='https://translate.googleapis.com/translate_a/single?'+urllib.parse.urlencode({'client':'gtx','sl':'en','tl':lang,'dt':'t','q':'\n'.join(strings)})
  with urllib.request.urlopen(u,timeout=30) as r:data=json.load(r)
  return ''.join(x[0] for x in data[0] if x[0]).split('\n')
 for i,b in enumerate(batches):
  out=call(b)
  if len(out)!=len(b):
   out=['\n'.join(call([s])) for s in b]
  if any(not s.strip() for s in out):raise ValueError('Empty translation '+lang)
  cache.update(zip(b,[s.strip() for s in out]));p.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8')
  if i%20==0:print(lang,i+1,'/',len(batches),flush=True)
  time.sleep(.12)
 return lang,len(cache)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for result in pool.map(translate,['es','fr','pt-BR','de','nl']):print('DONE',result,flush=True)
