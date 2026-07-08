
from __future__ import annotations
import json, threading, webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from urllib import request, error
from external_app_paths import BASE_DIR, RESOURCE_DIR

BRIDGE = "http://127.0.0.1:49774"
SUPPORT_LINKS = {
    "Support on Ko-fi": "https://ko-fi.com/mattmab",
    "FunkYouSHiFT Twitch": "https://www.twitch.tv/FunkYouSHiFT",
    "FunkYouSHiFT YouTube": "https://www.youtube.com/@Funkyoushift",
}
LOCAL_RESOURCE_FILES = {
    "lootlemon_codes": "MattsSDKBoostingTools_lootlemon_codes.json",
    "custom_bl4_codes": "custom_bl4_codes.json",
    "item_pools": "item_pools.json",
    "travel_maps": "travelmaps_flat.json",
    "travel_stations": "travelstations.json",
    "gzo_parts_map": "gzo_parts_map.json",
    "legit_rules": "legit_rules_flat.json",
}
SETTINGS_FILE = RESOURCE_DIR / "user_external_app_settings.json"
def load_local_json(filename):
    with open(RESOURCE_DIR / filename, "r", encoding="utf-8") as f: return json.load(f)
ACCENT_COLORS={"cyan":"#00d4ff","gold":"#ffcc33","green":"#43d17a","purple":"#b36bff","pink":"#ff5db7","red":"#ff5b5b"}
NUMERIC_FIELDS={"amount","level","serial_level","itempool_count","itempool_level","code_delivery_level","backpack_size","bank_size"}
CARD_BORDER={"target_player":"#6b7280","quick_max":"#6b7280","serial_rewards":"#8a2be2","experience":"#00a3d7","currency":"#00aa55","backpack_bank":"#00a3d7","rarity_weights":"#8a2be2","cheats_debug":"#b01258","sdu_shinies":"#b37a00","movement_presets":"#00aa55","movement_speed":"#00a3d7","movement_jump":"#8a2be2","movement_utility":"#8a2be2","serial_convert":"#00a3d7","serial_output":"#00a3d7","legit_builder_main":"#00a3d7","legit_slot_grid":"#6b7280","item_pool_main":"#b37a00","dev_spawner_info":"#ff5b5b","dev_spawner_actor":"#00a3d7","dev_spawner_ai":"#8a2be2","dev_spawner_logo":"#b37a00","map_travel_main":"#b01258","activity_log_main":"#8a2be2","bl4_codes_catalog":"#b37a00","serial_bookmarks_main":"#8a2be2","validator_basic":"#00a3d7"}

def http_json(method,path,data=None,timeout=8.0):
    body=None; headers={"Content-Type":"application/json"}
    if data is not None: body=json.dumps(data).encode('utf-8')
    req=request.Request(BRIDGE+path,data=body,headers=headers,method=method)
    with request.urlopen(req,timeout=timeout) as resp: return json.loads(resp.read().decode('utf-8',errors='replace') or '{}')

class ScrollFrame(tk.Frame):
    def __init__(self,parent,bg="#090d17"):
        super().__init__(parent,bg=bg)
        self.canvas=tk.Canvas(self,bg=bg,highlightthickness=0)
        self.vbar=ttk.Scrollbar(self,orient='vertical',command=self.canvas.yview)
        self.body=tk.Frame(self.canvas,bg=bg)
        self.window=self.canvas.create_window((0,0),window=self.body,anchor='nw')
        self.body.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.window,width=e.width))
        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.canvas.pack(side='left',fill='both',expand=True); self.vbar.pack(side='right',fill='y')
        self.canvas.bind_all('<MouseWheel>',lambda e:self.canvas.yview_scroll(int(-1*(e.delta/120)),'units'))

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Matt's SDK Boosting Tools - External V18 Clean Current")
        self.geometry('1920x980'); self.minsize(1400,820); self.configure(bg='#090d17')
        self.app_settings=self._load_app_settings()
        self.app_opacity_var=tk.IntVar(value=self._initial_opacity_percent())
        self.field_vars={}; self.widgets={}; self.resources={}; self.legit_roots=[]; self.player_options=[]; self.current_layout=None
        self.status_var=tk.StringVar(value='Not connected'); self.log_var=tk.StringVar(value="V20 GZO import build: local Matt resources + bridge for live actions.")
        self.output_text=None; self._style(); self._header(); self.notebook=ttk.Notebook(self); self.notebook.pack(fill='both',expand=True,padx=6,pady=(0,6))
        self._set_app_opacity(self.app_opacity_var.get(), save=False)
        self.after(200,self.load_layout); self.after(1600,self.poll_status)
    def _load_app_settings(self):
        try:
            if SETTINGS_FILE.exists():
                data=json.loads(SETTINGS_FILE.read_text(encoding='utf-8') or '{}')
                return data if isinstance(data,dict) else {}
        except Exception:
            pass
        return {}
    def _save_app_settings(self):
        try:
            SETTINGS_FILE.parent.mkdir(parents=True,exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(self.app_settings,indent=2,sort_keys=True),encoding='utf-8')
        except Exception:
            pass
    def _initial_opacity_percent(self):
        try:
            raw=int(float(self.app_settings.get('app_opacity_percent',100)))
        except Exception:
            raw=100
        return max(50,min(100,raw))
    def _set_app_opacity(self,value,save=True):
        try:
            percent=max(50,min(100,int(float(value))))
        except Exception:
            percent=100
        if hasattr(self,'app_opacity_var') and self.app_opacity_var.get()!=percent:
            self.app_opacity_var.set(percent)
        try:
            self.attributes('-alpha',percent/100.0)
        except Exception:
            return
        if save:
            self.app_settings['app_opacity_percent']=percent
            self._save_app_settings()
    def _on_opacity_changed(self,value):
        self._set_app_opacity(value,save=True)
    def _style(self):
        st=ttk.Style(self)
        try: st.theme_use('clam')
        except Exception: pass
        st.configure('TNotebook',background='#090d17',borderwidth=0)
        st.configure('TFrame',background='#090d17')
        st.configure('TLabel',background='#090d17',foreground='#cfd8f3',font=('Segoe UI',8))
        st.configure('TNotebook.Tab',padding=(12,5),background='#0b4e61',foreground='#f1f5ff',font=('Segoe UI',8))
        st.map('TNotebook.Tab',background=[('selected','#7a1d6b')],foreground=[('selected','#ffffff')])
        st.configure('TCombobox',fieldbackground='#211b1f',background='#172033',foreground='#f1f5ff',arrowcolor='#d7def5',selectbackground='#1f6f8b',selectforeground='#ffffff',padding=2)
        st.map('TCombobox',
            fieldbackground=[('disabled','#252a35')],
            foreground=[('disabled','#8c99b5')],
            selectbackground=[('!disabled','#1f6f8b')],
            selectforeground=[('!disabled','#ffffff')],
            arrowcolor=[('disabled','#8c99b5'),('!disabled','#f8fafc')])
        st.configure('TEntry',fieldbackground='#211b1f',foreground='#f1f5ff',insertcolor='#f1f5ff',padding=2)
    def _header(self):
        top=tk.Frame(self,bg='#090d17'); top.pack(fill='x',padx=6,pady=(6,2))
        left=tk.Frame(top,bg='#090d17'); left.pack(side='left',fill='x',expand=True)
        tk.Label(left,text="MATT'S SDK BOOSTING TOOLS",fg='#00d4ff',bg='#090d17',font=('Segoe UI',9,'bold')).pack(anchor='w')
        tk.Label(left,text='Boost smarter. Not harder.',fg='#ff5db7',bg='#090d17',font=('Segoe UI',8,'bold')).pack(anchor='w')
        tk.Label(left,text='External control panel using bundled Matt resources; live commands run through the SDK bridge.',fg='#9fb3d9',bg='#090d17',font=('Segoe UI',8)).pack(anchor='w')
        link_row=tk.Frame(left,bg='#090d17'); link_row.pack(anchor='w',pady=(3,0))
        for label,url in SUPPORT_LINKS.items():
            tk.Button(link_row,text=label,command=lambda u=url:self._open_support_link(u),bg='#172033',fg='#ffd447',relief='flat',padx=8,pady=3,font=('Segoe UI',8,'bold')).pack(side='left',padx=(0,6))
        tk.Button(top,text='Reconnect',command=self.load_layout,bg='#172033',fg='#f1f5ff',relief='flat',padx=14,pady=6).pack(side='right',padx=(6,0))
        tk.Button(top,text='Status',command=self.poll_status,bg='#172033',fg='#f1f5ff',relief='flat',padx=14,pady=6).pack(side='right')
        opacity=tk.Frame(top,bg='#090d17'); opacity.pack(side='right',padx=(10,4))
        tk.Label(opacity,text='App Opacity',fg='#9fb3d9',bg='#090d17',font=('Segoe UI',8)).pack(anchor='e')
        tk.Scale(opacity,from_=50,to=100,orient='horizontal',variable=self.app_opacity_var,command=self._on_opacity_changed,length=125,showvalue=True,bg='#090d17',fg='#cfd8f3',troughcolor='#211b1f',highlightthickness=0,relief='flat').pack(anchor='e')
        tk.Label(self,textvariable=self.status_var,fg='#9fb3d9',bg='#090d17',anchor='w',font=('Segoe UI',8)).pack(fill='x',padx=6,pady=(2,0))
        tk.Label(self,textvariable=self.log_var,fg='#21e05f',bg='#090d17',anchor='w',justify='left',wraplength=1800,font=('Segoe UI',8)).pack(fill='x',padx=6,pady=(0,3))
        sep=tk.Frame(self,bg='#333a48',height=1); sep.pack(fill='x',padx=6,pady=(0,3))
    def _open_support_link(self,url):
        try:
            webbrowser.open(str(url), new=2)
            self.log(f'Opened link: {url}')
        except Exception as exc:
            self.log(f'Could not open link: {exc!r}')
    def log(self,msg):
        self.log_var.set(str(msg))
        if self.output_text:
            self.output_text.configure(state='normal'); self.output_text.insert('end',str(msg)+'\n'); self.output_text.see('end'); self.output_text.configure(state='disabled')
    def load_layout(self):
        try:
            layout=load_local_json('ui_layout.json'); resources={}; missing=[]
            for name,fn in LOCAL_RESOURCE_FILES.items():
                try: resources[name]=load_local_json(fn)
                except Exception as exc: resources[name]={"_error":repr(exc)}; missing.append(f'{name}: {exc}')
            self._apply_layout(layout,resources)
            if missing: self.log('Local resource load warnings: '+'; '.join(missing))
        except Exception as exc:
            self.log(f'Could not load bundled resources: {exc}'); self.status_var.set('Local resources failed')
        self.poll_status()
    def _apply_layout(self,layout,resources):
        self.current_layout=layout; self.resources=resources; self._prepare_resources()
        for tid in self.notebook.tabs(): self.notebook.forget(tid)
        self.field_vars.clear(); self.widgets.clear(); self.output_text=None
        for tab in layout.get('tabs',[]):
            fr=ttk.Frame(self.notebook); self.notebook.add(fr,text=tab.get('label',tab.get('id','Tab'))); self._tab(fr,tab)
        self._refresh_combo('legit_manufacturer'); self._refresh_combo('legit_root_serial'); self._refresh_combo('legit_part_select')
        self.log(f"Connected. V20 GZO import full-tab layout loaded {len(layout.get('tabs',[]))} Matt-style tabs from bundled resources.")
    def _root_item_type(self,r):
        key=str(r.get('key') or '').lower(); inv=str(r.get('inv') or '').lower(); name=str(r.get('name') or '').lower(); val=' '.join([key,inv,name])
        if 'classmod' in val or 'class_mod' in val or 'class mod' in val: return 'class_mod'
        if inv.endswith('_ps') or 'weapon_ps' in inv or key.endswith('_ps'): return 'pistol'
        if inv.endswith('_sm') or 'weapon_sm' in inv or key.endswith('_sm'): return 'smg'
        if inv.endswith('_sg') or 'weapon_sg' in inv or key.endswith('_sg'): return 'shotgun'
        if inv.endswith('_ar') or 'weapon_ar' in inv or key.endswith('_ar'): return 'assault_rifle'
        if inv.endswith('_sr') or 'weapon_sr' in inv or key.endswith('_sr'): return 'sniper'
        if inv.endswith('_hw') or 'heavy' in val: return 'heavy'
        if 'shield' in val: return 'shield'
        if 'repair_kit' in val or 'repkit' in val or 'repair kit' in val: return 'repair_kit'
        if 'enhancement' in val: return 'enhancement'
        if 'gadget' in val or 'turret' in val or 'terminal' in val or 'hover' in val: return 'gadget'
        return ''
    def _root_manufacturer(self,r):
        import re
        key=str(r.get('key') or ''); inv=str(r.get('inv') or ''); name=str(r.get('name') or ''); text=' '.join([key,inv,name]); low=text.lower()
        m=re.search(r"manufacturer'([^']+)'", text)
        if m:
            man=m.group(1); return 'Ripper' if man.lower() in ('borg','bor') else man
        if 'robodealer' in low: return 'C4SH'
        if 'dark_siren' in low or 'siren' in low: return 'Vex / Siren'
        if 'paladin' in low: return 'Amon / Paladin'
        if 'exo_soldier' in low or 'soldier' in low: return 'Rafa / Exo Soldier'
        if 'gravitar' in low: return 'Harlowe / Gravitar'
        mapping={'dad':'Daedalus','jak':'Jakobs','ord':'Order','ted':'Tediore','tor':'Torgue','vla':'Vladof','mal':'Maliwan','bor':'Ripper','borg':'Ripper','hyp':'Hyperion','atl':'Atlas','cov':'COV'}
        for prefix,man in mapping.items():
            if key.lower().startswith(prefix+'_') or inv.lower().startswith(prefix+'_') or (' '+prefix+'_') in low: return man
        if ',' in name:
            tail=name.split(',')[-1].strip()
            for man in set(mapping.values())|{'C4SH'}:
                if tail.lower().startswith(man.lower()): return man
        return 'Other'
    def _root_label(self,r):
        name=str(r.get('name') or '')
        if ',' in name:
            tail=name.split(',')[-1].strip()
            if tail: return tail
        return str(r.get('display') or r.get('build_label') or r.get('key') or r.get('serial') or '')
    def _prepare_resources(self):
        lr=(self.resources.get('legit_rules') or {}).get('roots',[]) if isinstance(self.resources.get('legit_rules'),dict) else []
        self.legit_roots=[]
        for r in lr:
            if not isinstance(r,dict): continue
            item_type=self._root_item_type(r)
            if item_type not in {'pistol','smg','shotgun','assault_rifle','sniper','shield','repair_kit','enhancement','gadget','heavy','class_mod'}: continue
            rr=dict(r); rr['_item_type']=item_type; rr['_manufacturer']=self._root_manufacturer(r); rr['_label']=self._root_label(r); self.legit_roots.append(rr)
        self.legit_roots.sort(key=lambda r:(str(r.get('_item_type')),str(r.get('_manufacturer')),int(r.get('serial') or 0)))
    def _tab(self,parent,tab):
        sf=ScrollFrame(parent); sf.pack(fill='both',expand=True); body=sf.body
        cards={c.get('id'):c for c in tab.get('cards',[])}; tid=tab.get('id')
        if tid=='boosting': return self._tab_boosting(body,cards)
        if tid=='player_movement': return self._tab_movement(body,cards)
        if tid in ('serial_tools','legit_builder','item_pool','map_travel','bl4_codes','serial_bookmarks','validator'):
            return self._tab_two_col(body,tab,cards)
        for c in tab.get('cards',[]): self._place_card(body,c).pack(fill='both',expand=True,padx=6,pady=5,anchor='n')
    def _grid_weight(self,frame,cols):
        for c in range(cols): frame.grid_columnconfigure(c,weight=1,uniform='col')
    def _tab_boosting(self,body,cards):
        self._place_card(body,cards['target_player']).pack(fill='x',padx=6,pady=4)
        grid=tk.Frame(body,bg='#090d17'); grid.pack(fill='both',expand=True,padx=6,pady=0); self._grid_weight(grid,3)
        self._place_card(grid,cards['serial_rewards']).grid(row=0,column=0,rowspan=3,sticky='nsew',padx=(0,4),pady=4)
        self._place_card(grid,cards['experience']).grid(row=3,column=0,sticky='nsew',padx=(0,4),pady=4)
        self._place_card(grid,cards['quick_max']).grid(row=0,column=1,columnspan=2,sticky='nsew',padx=4,pady=4)
        self._place_card(grid,cards['currency']).grid(row=1,column=1,sticky='nsew',padx=4,pady=4)
        self._place_card(grid,cards['backpack_bank']).grid(row=2,column=1,sticky='nsew',padx=4,pady=4)
        self._place_card(grid,cards['rarity_weights']).grid(row=3,column=1,sticky='nsew',padx=4,pady=4)
        self._place_card(grid,cards['cheats_debug']).grid(row=1,column=2,rowspan=2,sticky='nsew',padx=(4,0),pady=4)
        self._place_card(grid,cards['sdu_shinies']).grid(row=3,column=2,sticky='nsew',padx=(4,0),pady=4)
        for r in range(4): grid.grid_rowconfigure(r,weight=1)
    def _tab_movement(self,body,cards):
        self._place_card(body,cards['movement_presets']).pack(fill='x',padx=6,pady=4)
        grid=tk.Frame(body,bg='#090d17'); grid.pack(fill='both',expand=True,padx=6,pady=0); self._grid_weight(grid,3)
        self._place_card(grid,cards['movement_speed']).grid(row=0,column=0,sticky='nsew',padx=(0,4),pady=4)
        self._place_card(grid,cards['movement_jump']).grid(row=0,column=1,sticky='nsew',padx=4,pady=4)
        self._place_card(grid,cards['movement_utility']).grid(row=0,column=2,sticky='nsew',padx=(4,0),pady=4)
        for c in range(3): grid.grid_rowconfigure(0,weight=1)
    def _tab_two_col(self,body,tab,cards):
        tid=tab.get('id')
        if tid=='legit_builder':
            self._place_card(body,cards['legit_builder_main'],compact=False).pack(fill='x',padx=6,pady=5)
            self._place_card(body,cards['legit_slot_grid'],compact=False).pack(fill='both',expand=True,padx=6,pady=5)
            return
        for c in tab.get('cards',[]): self._place_card(body,c,compact=False).pack(fill='both',expand=True,padx=6,pady=5,anchor='n')
    def _place_card(self,parent,card,compact=True):
        cid=card.get('id',''); border=CARD_BORDER.get(cid,'#333a48')
        wrap=tk.Frame(parent,bg=border,padx=1,pady=1)
        head=tk.Frame(wrap,bg='#0e1320'); head.pack(fill='x')
        tk.Label(head,text=card.get('label','').upper(),bg='#0e1320',fg=border,font=('Segoe UI',8,'bold'),anchor='w').pack(side='left',padx=6,pady=(3,1))
        inner=tk.Frame(wrap,bg='#090d17'); inner.pack(fill='both',expand=True)
        if card.get('text'): tk.Label(inner,text=card['text'],bg='#090d17',fg='#8c99b5',wraplength=980,justify='left',font=('Segoe UI',8)).pack(anchor='w',fill='x',padx=8,pady=(4,2))
        for f in card.get('fields',[]): self._field(inner,f,compact=compact)
        acts=card.get('actions') or []
        if acts:
            bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(3,6)); cols=3 if compact else 4
            if cid in ('quick_max','cheats_debug','sdu_shinies','movement_presets'): cols=5 if not compact else 3
            if cid in ('target_player',): cols=3
            for i,a in enumerate(acts): self._button(bf,a,i,cols=cols)
        if cid in ('serial_convert','activity_log_main','serial_output'):
            self._output_box(inner)
        return wrap
    def _field(self,parent,field,compact=True):
        fid=field.get('id'); typ=field.get('type')
        if not fid: return
        row=tk.Frame(parent,bg='#090d17'); row.pack(fill='x',padx=8,pady=2)
        tk.Label(row,text=field.get('label',fid),bg='#090d17',fg='#cfd8f3',width=16 if compact else 18,anchor='w',font=('Segoe UI',8)).pack(side='left')
        var=tk.StringVar(value=str(field.get('default',''))); self.field_vars[fid]=var
        if typ in ('choice','editable_choice','resource_choice','player_choice','legit_type','legit_manufacturer','legit_root','legit_part'):
            values=self._values_for_field(field); cb=ttk.Combobox(row,textvariable=var,values=values,state='normal' if typ in ('editable_choice','resource_choice') else 'readonly',height=max(5,min(20,len(values) or 5)))
            cb.pack(side='left',fill='x',expand=True); self.widgets[fid]=cb
            if values and not var.get(): var.set(values[0])
            cb.bind('<<ComboboxSelected>>',lambda e,f=field:self._field_changed(f))
        elif typ=='slider':
            try: min_v=float(field.get('min',0))
            except Exception: min_v=0.0
            try: max_v=float(field.get('max',100))
            except Exception: max_v=100.0
            try: step=float(field.get('step',1))
            except Exception: step=1.0
            scale=tk.Scale(row,from_=min_v,to=max_v,resolution=step,orient='horizontal',variable=var,showvalue=False,bg='#090d17',fg='#cfd8f3',troughcolor='#211b1f',highlightthickness=0,relief='flat')
            scale.pack(side='left',fill='x',expand=True)
            ent=ttk.Entry(row,textvariable=var,width=6); ent.pack(side='left',padx=(6,0))
            tk.Label(row,text=field.get('suffix',''),bg='#090d17',fg='#8c99b5',font=('Segoe UI',8)).pack(side='left',padx=(3,0))
            self.widgets[fid]=scale
        elif typ=='multiline':
            h=4 if compact else 6
            if fid in ('serial_text','bookmark_serial','validator_bulk_input'): h=8
            txt=tk.Text(row,height=h,bg='#181417',fg='#f1f5ff',insertbackground='#f1f5ff',relief='flat',wrap='word',font=('Consolas',8))
            txt.insert('1.0',var.get()); txt.pack(side='left',fill='x',expand=True)
            txt.bind('<KeyRelease>',lambda e,v=var,w=txt:v.set(w.get('1.0','end-1c'))); self.widgets[fid]=txt
        elif typ in ('checkbox','bool'):
            default=str(field.get('default','false')).strip().lower()
            var.set('true' if default in ('1','true','yes','on') else 'false')
            chk=tk.Checkbutton(row,variable=var,onvalue='true',offvalue='false',command=lambda f=field:self._field_changed(f),bg='#090d17',activebackground='#090d17',fg='#cfd8f3',activeforeground='#f1f5ff',selectcolor='#211b1f',relief='flat')
            chk.pack(side='left',anchor='w'); self.widgets[fid]=chk
        else:
            ent=ttk.Entry(row,textvariable=var); ent.pack(side='left',fill='x',expand=True); self.widgets[fid]=ent
    def _values_for_field(self,field):
        typ=field.get('type'); src=field.get('source')
        if typ in ('choice','editable_choice'): return list(field.get('choices',[]))
        if typ=='player_choice': return list(self.player_options)
        if typ=='resource_choice':
            data=self.resources.get(src)
            if src=='item_pools' and isinstance(data,list): return [f"{x.get('display_name')} | {x.get('itempool')}" for x in data]
            if src=='travel_maps' and isinstance(data,dict): return [f"{x.get('display_name')} | {x.get('map')}" for x in data.get('maps',[])]
            if src=='travel_stations' and isinstance(data,dict): return [f"{x.get('world')} - {x.get('display_name')} | {x.get('station')}" for x in data.get('stations',[])]
            if src=='lootlemon_codes' and isinstance(data,dict): return [f"{x.get('name')} [{x.get('category')}] | {x.get('serial')}" for x in data.get('entries',[])]
            return []
        if typ=='legit_type':
            order=['pistol','smg','shotgun','assault_rifle','sniper','shield','repair_kit','enhancement','gadget','heavy','class_mod']; seen={str(r.get('_item_type')) for r in self.legit_roots if r.get('_item_type')}
            return [x for x in order if x in seen]+sorted(seen.difference(order))
        if typ=='legit_manufacturer':
            t=self.field_vars.get('legit_type',tk.StringVar()).get(); return sorted({str(r.get('_manufacturer')) for r in self.legit_roots if str(r.get('_item_type'))==t})
        if typ=='legit_root':
            t=self.field_vars.get('legit_type',tk.StringVar()).get(); m=self.field_vars.get('legit_manufacturer',tk.StringVar()).get()
            return [f"{r.get('serial')} | {r.get('_label') or r.get('key')} | {r.get('key')}" for r in self.legit_roots if str(r.get('_item_type'))==t and str(r.get('_manufacturer'))==m]
        if typ=='legit_part': return self._legit_part_values()
        return []
    def _field_changed(self,field):
        fid=field.get('id')
        if fid in ('legit_type','legit_manufacturer','legit_root_serial'):
            if fid=='legit_type': self._refresh_combo('legit_manufacturer')
            if fid in ('legit_type','legit_manufacturer'): self._refresh_combo('legit_root_serial')
            self._refresh_combo('legit_part_select')
        if fid=='code_entry': self._copy_pipe_value('code_entry','code_serial')
    def _refresh_combo(self,fid):
        cb=self.widgets.get(fid)
        if not isinstance(cb,ttk.Combobox): return
        fake={'id':fid,'type':{'legit_manufacturer':'legit_manufacturer','legit_root_serial':'legit_root','legit_part_select':'legit_part'}.get(fid,'choice')}
        vals=self._values_for_field(fake); cb.configure(values=vals); self.field_vars[fid].set(vals[0] if vals else '')
    def _copy_pipe_value(self,source,target):
        val=self.field_vars.get(source,tk.StringVar()).get(); actual=val.split('|',1)[1].strip() if '|' in val else val
        if target in self.field_vars: self.field_vars[target].set(actual); w=self.widgets.get(target)
        else: w=None
        try:
            if isinstance(w,tk.Text): w.delete('1.0','end'); w.insert('1.0',actual)
        except Exception: pass
    def _legit_current_root(self):
        raw=self.field_vars.get('legit_root_serial',tk.StringVar()).get(); serial=None
        try: serial=int(raw.split('|',1)[0].strip())
        except Exception: return None
        for r in self.legit_roots:
            try:
                if int(r.get('serial') or -1)==serial: return r
            except Exception: pass
        return None
    def _legit_part_values(self):
        r=self._legit_current_root(); vals=[]
        if not r: return vals
        for p in r.get('parts',[]):
            table=str(p.get('table') or '').strip(); key=str(p.get('key') or '').strip(); serial=p.get('serial'); label=p.get('display') or p.get('name') or key
            if table and key: vals.append(f"{table}:{key} | +{{{serial}}} {label}")
        return vals[:3000]
    def _button(self,parent,action,i,cols=4):
        color=ACCENT_COLORS.get(action.get('accent','cyan'),'#00d4ff')
        b=tk.Button(parent,text=action.get('label',action.get('id')),command=lambda a=action:self.run_action(a),bg='#172033',activebackground='#22304c',fg=color,activeforeground=color,relief='flat',padx=8,pady=5,font=('Segoe UI',8,'bold'))
        b.grid(row=i//cols,column=i%cols,padx=3,pady=3,sticky='ew')
        for c in range(cols): parent.grid_columnconfigure(c,weight=1,uniform='btn')
    def _output_box(self,parent):
        if self.output_text: return
        box=tk.Text(parent,height=8,bg='#0e1320',fg='#d7def5',insertbackground='#f1f5ff',relief='flat',wrap='word',font=('Consolas',8)); box.configure(state='disabled'); box.pack(fill='both',expand=True,padx=8,pady=(5,8)); self.output_text=box
    def run_action(self,action):
        aid=action.get('id')
        if aid=='rarity_reset':
            for key in ('common','uncommon','rare','epic','legendary','pearlescent'):
                var=self.field_vars.get(f'rarity_{key}_percent')
                if var: var.set('100')
        elif aid=='rarity_only_legendary':
            for key in ('common','uncommon','rare','epic','legendary','pearlescent'):
                var=self.field_vars.get(f'rarity_{key}_percent')
                if var: var.set('100' if key=='legendary' else '0')
        elif aid=='rarity_only_pearlescent':
            for key in ('common','uncommon','rare','epic','legendary','pearlescent'):
                var=self.field_vars.get(f'rarity_{key}_percent')
                if var: var.set('100' if key=='pearlescent' else '0')
        if aid=='local_legit_add_part':
            part=self.field_vars.get('legit_part_select',tk.StringVar()).get().split('|',1)[0].strip()
            if not part: return self.log('No legit part selected.')
            txt=self.widgets.get('legit_selected_parts'); cur=self.field_vars.get('legit_selected_parts').get(); new=(cur+'\n'+part).strip() if cur else part; self.field_vars['legit_selected_parts'].set(new)
            if isinstance(txt,tk.Text): txt.delete('1.0','end'); txt.insert('1.0',new)
            return self.log(f'Added selected part: {part}')
        payload={}
        for fid in action.get('uses_fields',[]) or []:
            var=self.field_vars.get(fid)
            if not var: continue
            value=var.get()
            if fid in ('itempool_name','travel_map','travel_station','legit_root_serial','target_player') and '|' in str(value): value=str(value).split('|')[-1].strip() if fid in ('itempool_name','travel_map','travel_station') else str(value).split('|',1)[0].strip()
            if fid=='code_serial' and '|' in str(value): value=str(value).split('|',1)[1].strip()
            if fid in NUMERIC_FIELDS:
                try: value=int(str(value).replace(',','').strip())
                except Exception: return messagebox.showerror('Invalid value',f'{fid} must be a number.')
            payload[fid]=value
        self.log(f'Sending action: {aid} ...')
        def work():
            try:
                res=http_json('POST','/action',{'action':aid,'payload':payload,'timeout':10.0},timeout=12.0); msg=res.get('message') or json.dumps(res)
                extra=''.join(f"\n\n{k}:\n{res.get(k)}" for k in ('serialized','deserialized','breakdown','base85','human') if res.get(k))
                self.after(0,lambda:self.log(str(msg)+extra)); self.after(0,self.poll_status)
            except error.HTTPError as exc:
                try: data=json.loads(exc.read().decode('utf-8',errors='replace') or '{}'); msg=data.get('message') or str(exc)
                except Exception: msg=str(exc)
                self.after(0,lambda:self.log('Action failed: '+msg))
            except Exception as exc: self.after(0,lambda:self.log('Action failed: '+repr(exc)))
        threading.Thread(target=work,daemon=True).start()
    def _update_player_options(self,status):
        try:
            opts=[]
            for pl in status.get('players') or []:
                idx=pl.get('index'); name=pl.get('name') or f'Player {idx}'; opts.append(f'{idx} | {name}')
            self.player_options=opts; cb=self.widgets.get('target_player')
            if isinstance(cb,ttk.Combobox):
                current=self.field_vars.get('target_player',tk.StringVar()).get(); cb.configure(values=opts)
                selected_idx=status.get('selected_player_index'); selected_name=status.get('selected_player') or ''; wanted=f'{selected_idx} | {selected_name}' if selected_idx not in (None,'') and selected_name else ''
                if wanted and wanted in opts and current!=wanted: self.field_vars['target_player'].set(wanted)
        except Exception: pass
    def poll_status(self):
        def work():
            try:
                s=http_json('GET','/status',timeout=3); selected=s.get('selected_player') or 'no selected player'; text=f"Bridge online | selected: {selected} | players: {len(s.get('players') or [])} | queue: {s.get('queue',0)}"
                if s.get('last_error'): text+=' | last error: '+str(s.get('last_error'))
                self.after(0,lambda:self.status_var.set(text)); self.after(0,lambda st=s:self._update_player_options(st))
            except Exception: self.after(0,lambda:self.status_var.set('Bridge offline - local UI/resources still loaded'))
        threading.Thread(target=work,daemon=True).start(); self.after(3000,self.poll_status)
if __name__=='__main__': App().mainloop()
