"""Compile cached translations; fails on missing entries or damaged substitutions."""
import json,re
from pathlib import Path
base=Path('output/languages')
source=json.loads((base/'english.json').read_text(encoding='utf-8'))
langs=['es','fr','pt-BR','de','nl']
translations={l:json.loads((base/(l+'.json')).read_text(encoding='utf-8')) for l in langs}
rows={s:{l:translations[l][s] for l in langs} for s in source}
for vals in json.loads(Path('electron_poc/ui_language_overrides.json').read_text(encoding='utf-8')):rows[vals[0]]=dict(zip(langs,vals[1:]))
for k in ['Borderlands 4 Modding Tools','Powered by Funk','SHiFT','AFK','UVHM','UVHM 1–7','MSBT','Steam','Epic Games']:
 if k in rows:rows[k]={l:k for l in langs}
for key,values in rows.items():
 for lang,text in values.items():
  values[lang]=re.sub(r'\{\s*(\d+)\s*\}',r'{\1}',text)
  assert sorted(re.findall(r'\{\d+\}',key))==sorted(re.findall(r'\{\d+\}',values[lang])),(lang,key,values[lang])
  assert text.strip(),(lang,key)
text='/* Bundled interface translations: automatic first pass with reviewed navigation terminology. No runtime translation requests. */\nwindow.MsbtLanguageCatalog = '+json.dumps(rows,ensure_ascii=False,separators=(',',':'))+';\n'
Path('electron_poc/ui_language_catalog.js').write_text(text,encoding='utf-8')
for name in ['ui_language_catalog.js','ui_localization.js','ui_i18n.js']:
 Path('mobile_controller/app/src/main/assets',name).write_bytes(Path('electron_poc',name).read_bytes())
print('Bundled strings:',len(rows),'templates:',sum(bool(re.search(r'\{\d+\}',k)) for k in rows))
