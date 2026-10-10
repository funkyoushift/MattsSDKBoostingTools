"""Compile cached translations; fails on missing entries or damaged substitutions."""
import argparse,json,re
from pathlib import Path
langs=['es','fr','pt-BR','de','nl']
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--from-cache',action='store_true',help='Replace automatic base translations with newly generated maintenance caches.')
args=parser.parse_args()
if args.from_cache:
 base=Path('output/languages')
 source=json.loads((base/'english.json').read_text(encoding='utf-8'))
 translations={l:json.loads((base/(l+'.json')).read_text(encoding='utf-8')) for l in langs}
 rows={s:{l:translations[l][s] for l in langs} for s in source}
else:
 # Review edits can be compiled offline in a clean checkout, without translation caches.
 bundled=Path('electron_poc/ui_language_catalog.js').read_text(encoding='utf-8')
 rows=json.JSONDecoder().raw_decode(bundled.split('window.MsbtLanguageCatalog = ',1)[1])[0]
additions=Path('electron_poc/ui_language_additions.json')
if additions.exists():
 for key,values in json.loads(additions.read_text(encoding='utf-8')).items():
  assert set(values)==set(langs),(key,'Missing language')
  rows[key]=dict(values)
for vals in json.loads(Path('electron_poc/ui_language_overrides.json').read_text(encoding='utf-8')):rows[vals[0]]=dict(zip(langs,vals[1:]))
reviewed=set()
for entry in json.loads(Path('electron_poc/ui_language_context.json').read_text(encoding='utf-8')):
 assert set(entry['translations'])==set(langs),entry
 for key in entry['keys']:
  assert key not in reviewed,('Duplicate context entry',key)
  reviewed.add(key)
  rows[key]=dict(entry['translations'])
australian=json.loads(Path('electron_poc/ui_language_australian.json').read_text(encoding='utf-8'))
for key in australian:
 assert key in rows,('Australian copy needs translations for the other languages',key)
for key,values in rows.items():
 values['en-AU']=australian.get(key,key)
for k in ['Borderlands 4 Modding Tools','Powered by Funk','SHiFT','AFK','UVHM','UVHM 1–7','MSBT','Steam','Epic Games']:
 if k in rows:rows[k]={l:k for l in langs+['en-AU']}
for key,values in rows.items():
 for lang,text in values.items():
  values[lang]=re.sub(r'\{\s*(\d+)\s*\}',r'{\1}',text)
  assert sorted(re.findall(r'\{\d+\}',key))==sorted(re.findall(r'\{\d+\}',values[lang])),(lang,key,values[lang])
  assert text.strip(),(lang,key)
text='/* Bundled interface translations with reviewed game-context phrases and opt-in Australian slang. No runtime translation requests. */\nwindow.MsbtLanguageCatalog = '+json.dumps(rows,ensure_ascii=False,separators=(',',':'))+';\n'
text+='window.MsbtReviewedLanguageKeys = '+json.dumps(sorted(reviewed),ensure_ascii=False)+';\n'
Path('electron_poc/ui_language_catalog.js').write_text(text,encoding='utf-8')
for name in ['ui_language_catalog.js','ui_localization.js','ui_i18n.js']:
 Path('mobile_controller/app/src/main/assets',name).write_bytes(Path('electron_poc',name).read_bytes())
 Path('external_app/v22_parts_codes_fixed/matt_editor/js',name).write_bytes(Path('electron_poc',name).read_bytes())
print('Bundled strings:',len(rows),'templates:',sum(bool(re.search(r'\{\d+\}',k)) for k in rows))
