
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import json, re, time, threading
from pathlib import Path
from urllib import request
from external_serial_tools import convert_serial_tool, serial_parts_breakdown_for_value
from matts_external_core_v20 import ACCENT_COLORS, http_json, RESOURCE_DIR
from matts_external_legit_travel_v20 import App as V9App

class App(V9App):
    def __init__(self):
        self.legit_duplicate_qty_var = None
        super().__init__()
        self.title("Matt's SDK Boosting Tools - External V22 Parts Codes GZO Visible")

    def _tab_movement(self, body, cards):
        # Closer copy of Matt's Player Movement tab, including Infinite Jump controls.
        self._place_card(body,cards['movement_presets']).pack(fill='x',padx=6,pady=4)
        grid=tk.Frame(body,bg='#090d17'); grid.pack(fill='both',expand=True,padx=6,pady=0)
        for c in range(3): grid.grid_columnconfigure(c,weight=1,uniform='move')
        self._place_card(grid,cards['movement_speed']).grid(row=0,column=0,sticky='nsew',padx=(0,4),pady=4)
        self._movement_jump_card(grid).grid(row=0,column=1,sticky='nsew',padx=4,pady=4)
        self._movement_infinite_jump_card(grid).grid(row=0,column=2,sticky='nsew',padx=(4,0),pady=4)
        self._movement_wall_card(grid).grid(row=1,column=0,sticky='nsew',padx=(0,4),pady=4)
        self._movement_glide_card(grid).grid(row=1,column=1,sticky='nsew',padx=4,pady=4)
        self._place_card(grid,cards['movement_utility']).grid(row=1,column=2,sticky='nsew',padx=(4,0),pady=4)
        for r in range(2): grid.grid_rowconfigure(r,weight=1)

    def _custom_card(self, title, color):
        wrap, inner = self._card_wrap(self._tmp_parent, title, color)  # overwritten by caller pattern
        return wrap, inner

    def _make_card(self, parent, title, color):
        wrap, inner = self._card_wrap(parent, title, color)
        return wrap, inner

    def _field_row_simple(self, parent, label, fid, default='', width=16):
        row=tk.Frame(parent,bg='#090d17'); row.pack(fill='x',padx=8,pady=2)
        tk.Label(row,text=label,bg='#090d17',fg='#cfd8f3',width=width,anchor='w',font=('Segoe UI',8)).pack(side='left')
        var=self.field_vars.get(fid) or tk.StringVar(value=str(default)); self.field_vars[fid]=var
        ent=ttk.Entry(row,textvariable=var); ent.pack(side='left',fill='x',expand=True); self.widgets[fid]=ent
        return ent

    def _movement_jump_card(self, parent):
        wrap, inner = self._make_card(parent,'Jump / Gravity','#8a2be2')
        self._field_row_simple(inner,'Master JumpGoal Height','movement_jump_height','198')
        self._field_row_simple(inner,'Gravity Scale','movement_gravity_scale','1.00')
        bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(4,6))
        for i,a in enumerate([
            {'id':'movement_apply_all','label':'Apply Movement Settings','accent':'cyan','uses_fields':['movement_speed_scale','movement_walk_speed','movement_jump_height','movement_gravity_scale','movement_step_height','movement_floor_angle','movement_glide_speed','movement_dash_speed']},
            {'id':'movement_reset_all','label':'Reset Defaults','accent':'gold'},
        ]): self._button(bf,a,i,cols=2)
        return wrap

    def _movement_wall_card(self,parent):
        wrap, inner = self._make_card(parent,'Wall / Step','#d28b00')
        self._field_row_simple(inner,'Max Step Height','movement_step_height','45')
        self._field_row_simple(inner,'Walkable Floor Angle','movement_floor_angle','44.8')
        bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(4,6))
        self._button(bf,{'id':'movement_apply_all','label':'Apply Wall / Step','accent':'cyan','uses_fields':['movement_speed_scale','movement_walk_speed','movement_jump_height','movement_gravity_scale','movement_step_height','movement_floor_angle','movement_glide_speed','movement_dash_speed']},0,cols=1)
        return wrap

    def _movement_glide_card(self,parent):
        wrap, inner = self._make_card(parent,'Glide / Dash / Vault','#0075c9')
        self._field_row_simple(inner,'Gliding Speed','movement_glide_speed','1200')
        self._field_row_simple(inner,'Dash Speed','movement_dash_speed','2500')
        bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(4,6))
        self._button(bf,{'id':'movement_zero_vault','label':'Zero Vault Cooldown','accent':'cyan'},0,cols=2)
        self._button(bf,{'id':'movement_apply_all','label':'Apply Glide / Dash','accent':'cyan','uses_fields':['movement_speed_scale','movement_walk_speed','movement_jump_height','movement_gravity_scale','movement_step_height','movement_floor_angle','movement_glide_speed','movement_dash_speed']},1,cols=2)
        return wrap

    def _movement_infinite_jump_card(self,parent):
        wrap, inner = self._make_card(parent,'Infinite Jump','#00b060')
        tk.Label(inner,text='Enable per player. Use All ON for multi-jump on every current party player.',bg='#090d17',fg='#9fb3d9',font=('Segoe UI',8),anchor='w',wraplength=500).pack(fill='x',padx=8,pady=(5,2))
        bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(4,3))
        self._button(bf,{'id':'movement_infinite_jump_all_on','label':'All ON','accent':'green'},0,cols=2)
        self._button(bf,{'id':'movement_infinite_jump_all_off','label':'All OFF','accent':'red'},1,cols=2)
        row=tk.Frame(inner,bg='#090d17'); row.pack(fill='x',padx=8,pady=4)
        tk.Label(row,text='Player',bg='#090d17',fg='#cfd8f3',width=12,anchor='w',font=('Segoe UI',8)).pack(side='left')
        var=self.field_vars.get('infinite_jump_target') or tk.StringVar(value=''); self.field_vars['infinite_jump_target']=var
        cb=ttk.Combobox(row,textvariable=var,values=self.player_options,state='readonly'); cb.pack(side='left',fill='x',expand=True); self.widgets['infinite_jump_target']=cb
        bf2=tk.Frame(inner,bg='#090d17'); bf2.pack(fill='x',padx=6,pady=(2,6))
        self._button(bf2,{'id':'movement_infinite_jump_toggle_selected','label':'Toggle Selected Infinite Jump','accent':'cyan','uses_fields':['infinite_jump_target']},0,cols=1)
        return wrap

    def _update_player_options(self,status):
        super()._update_player_options(status)
        try:
            cb=self.widgets.get('infinite_jump_target')
            if isinstance(cb,ttk.Combobox):
                cb.configure(values=self.player_options)
                cur=self.field_vars.get('infinite_jump_target',tk.StringVar()).get()
                if not cur and self.player_options: self.field_vars['infinite_jump_target'].set(self.player_options[0])
        except Exception: pass

    def _tab_legit_builder_v9(self, body, cards):
        main, inner = self._card_wrap(body, 'Stripped Legit Builder', '#00a3d7')
        main.pack(fill='x', padx=6, pady=5)
        tk.Label(inner, text="Matt-style external builder: choose Type → Manufacturer → Root, then pick parts inside each slot panel. Unlock mode preserves duplicates.", bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w').pack(fill='x', padx=8, pady=(5,2))
        form=tk.Frame(inner,bg='#090d17'); form.pack(fill='x',padx=8,pady=4)
        labels=[('Unlock rules for modded gear','legit_unlock_modded','choice'),('Type','legit_type','legit_type'),('Manufacturer','legit_manufacturer','legit_manufacturer'),('Optional Root Filter','legit_root_filter','text'),('Root Variant','legit_root_serial','legit_root'),('Filter Available Parts','legit_part_filter','text'),('Duplicate / Add Count','legit_duplicate_qty','int'),('Level','legit_level','int'),('Signature','legit_signature','int')]
        defaults={'legit_unlock_modded':'false','legit_duplicate_qty':'1','legit_level':'60','legit_signature':'1534'}
        for r,(lab,fid,typ) in enumerate(labels):
            tk.Label(form,text=lab,bg='#090d17',fg='#cfd8f3',width=22,anchor='w',font=('Segoe UI',8)).grid(row=r,column=0,sticky='w',pady=2)
            var=self.field_vars.get(fid) or tk.StringVar(value=defaults.get(fid,'')); self.field_vars[fid]=var
            if typ=='choice':
                w=ttk.Combobox(form,textvariable=var,values=['false','true'],state='readonly')
            elif typ in ('legit_type','legit_manufacturer','legit_root'):
                fake=typ if fid!='legit_root_serial' else 'legit_root'
                vals=self._values_for_field({'id':fid,'type':fake}); w=ttk.Combobox(form,textvariable=var,values=vals,state='readonly')
                if vals and not var.get(): var.set(vals[0])
                w.bind('<<ComboboxSelected>>',lambda e,fid=fid:self._legit_filter_changed(fid))
            else:
                w=ttk.Entry(form,textvariable=var); w.bind('<KeyRelease>',lambda e:self._refresh_legit_root_and_slots())
            w.grid(row=r,column=1,sticky='ew',pady=2); self.widgets[fid]=w
        form.grid_columnconfigure(1,weight=1)
        btns=tk.Frame(inner,bg='#090d17'); btns.pack(fill='x',padx=8,pady=(4,8))
        actions=[
            {'id':'legit_apply_max_passives','label':'Add All Max Passives','accent':'gold','uses_fields':['legit_root_serial','legit_selected_parts','legit_unlock_modded']},
            {'id':'legit_validate_build','label':'Validate / Build Active','accent':'cyan','uses_fields':['legit_root_serial','legit_selected_parts','legit_unlock_modded','legit_level','legit_signature']},
            {'id':'legit_give_selected','label':'Give Active to Selected','accent':'gold','uses_fields':['legit_root_serial','legit_selected_parts','legit_unlock_modded','legit_level','legit_signature']},
            {'id':'legit_give_all','label':'Give Active to All','accent':'purple','uses_fields':['legit_root_serial','legit_selected_parts','legit_unlock_modded','legit_level','legit_signature']},
            {'id':'legit_clear_parts','label':'Clear Selected Parts','accent':'red'},
        ]
        for i,a in enumerate(actions): self._button(btns,a,i,cols=5)
        selected, sel_inner = self._card_wrap(body, 'Selected composition / active build', '#8a2be2')
        selected.pack(fill='x', padx=6, pady=5)
        self.field_vars['legit_selected_parts'] = self.field_vars.get('legit_selected_parts') or tk.StringVar(value='')
        txt=tk.Text(sel_inner,height=5,bg='#0e1320',fg='#d7def5',insertbackground='#f1f5ff',relief='flat',wrap='word',font=('Consolas',8))
        txt.pack(fill='x',padx=8,pady=8); txt.bind('<KeyRelease>',lambda e,w=txt:self.field_vars['legit_selected_parts'].set(w.get('1.0','end-1c'))); self.widgets['legit_selected_parts']=txt
        slot_wrap, slot_inner = self._card_wrap(body,'Slots / Available Parts','#6b7280')
        slot_wrap.pack(fill='both',expand=True,padx=6,pady=5)
        top=tk.Frame(slot_inner,bg='#090d17'); top.pack(fill='x',padx=8,pady=(5,2))
        tk.Label(top,text='Each panel is one Matt SDK slot/dependency. Add/Replace follows legit rules. Add x Qty preserves duplicates for modded/unlock builds.',bg='#090d17',fg='#9fb3d9',font=('Segoe UI',8)).pack(side='left')
        self.legit_slots_area=tk.Frame(slot_inner,bg='#090d17'); self.legit_slots_area.pack(fill='both',expand=True,padx=8,pady=6)
        self._refresh_combo('legit_manufacturer'); self._refresh_combo('legit_root_serial'); self._render_legit_slots()

    def _slot_line_from_part(self,p):
        table=str(p.get('table') or '').strip(); key=str(p.get('key') or '').strip()
        return f'{table}:{key}' if table and key else ''

    def _slot_selection_changed(self, slot, lb, force=False, append=False, qty=1):
        rows=self.legit_slot_parts.get(lb,[]); picks=[]
        for i in lb.curselection():
            try:
                _slot,label,p=rows[i]; line=self._slot_line_from_part(p)
                if line: picks.extend([line]*max(1,int(qty or 1)))
            except Exception: pass
        if not picks and not force: return
        if append:
            self.legit_selected_by_slot.setdefault(slot,[]).extend(picks)
        else:
            self.legit_selected_by_slot[slot]=picks
        self._sync_legit_selected_text()

    def _render_legit_slots(self):
        if not hasattr(self,'legit_slots_area'): return
        for child in self.legit_slots_area.winfo_children(): child.destroy()
        self.legit_slot_parts.clear(); root=self._legit_current_root()
        if not root:
            tk.Label(self.legit_slots_area,text='Pick a root variant to load its slot cards.',bg='#090d17',fg='#9fb3d9',font=('Segoe UI',9)).pack(anchor='w',padx=8,pady=8); return
        deps=list(root.get('deps') or []); parts=list(root.get('parts') or []); filter_text=(self.field_vars.get('legit_part_filter',tk.StringVar()).get() or '').lower().strip(); grouped={d:[] for d in deps}
        for p in parts:
            slot=str(p.get('table') or '')
            if slot not in grouped: grouped[slot]=[]
            label=self._part_label(p)
            if filter_text and filter_text not in label.lower() and filter_text not in slot.lower(): continue
            grouped[slot].append((label,p))
        cols=3
        for idx,slot in enumerate([d for d in deps if grouped.get(d)] + [d for d in grouped if d not in deps and grouped.get(d)]):
            r,c=divmod(idx,cols); wrap,inner=self._card_wrap(self.legit_slots_area,slot,'#333a48'); wrap.grid(row=r,column=c,sticky='nsew',padx=4,pady=4)
            self.legit_slots_area.grid_columnconfigure(c,weight=1,uniform='slot'); self.legit_slots_area.grid_rowconfigure(r,weight=1)
            current=len(self.legit_selected_by_slot.get(slot,[])); tk.Label(inner,text=f'{len(grouped[slot])} available part(s) | selected in slot: {current}',bg='#090d17',fg='#8c99b5',font=('Segoe UI',8),anchor='w').pack(fill='x',padx=6,pady=(3,0))
            lb=tk.Listbox(inner,height=7,selectmode='extended',bg='#0e1320',fg='#d7def5',selectbackground='#1f3b63',relief='flat',font=('Consolas',8),exportselection=False)
            lb.pack(fill='both',expand=True,padx=6,pady=4); self.legit_slot_parts[lb]=[(slot,label,p) for label,p in grouped[slot]]
            for label,p in grouped[slot]: lb.insert('end',label)
            controls=tk.Frame(inner,bg='#090d17'); controls.pack(fill='x',padx=6,pady=(0,5))
            tk.Button(controls,text='Add / Replace Slot',command=lambda slot=slot,lb=lb:self._slot_selection_changed(slot,lb,force=True,append=False,qty=1),bg='#172033',fg='#00d4ff',relief='flat',font=('Segoe UI',8,'bold')).grid(row=0,column=0,sticky='ew',padx=2,pady=2)
            tk.Button(controls,text='Add x Qty',command=lambda slot=slot,lb=lb:self._slot_selection_changed(slot,lb,force=True,append=True,qty=self.field_vars.get('legit_duplicate_qty',tk.StringVar(value='1')).get()),bg='#172033',fg='#ffd447',relief='flat',font=('Segoe UI',8,'bold')).grid(row=0,column=1,sticky='ew',padx=2,pady=2)
            tk.Button(controls,text='Clear Slot',command=lambda slot=slot:self._clear_slot(slot),bg='#172033',fg='#ff5b5b',relief='flat',font=('Segoe UI',8,'bold')).grid(row=0,column=2,sticky='ew',padx=2,pady=2)
            for cc in range(3): controls.grid_columnconfigure(cc,weight=1)



    def _legit_selected_lines_without_root(self):
        raw = self.field_vars.get('legit_selected_parts', tk.StringVar(value='')).get() or ''
        return [line.strip() for line in raw.splitlines() if line.strip() and not line.strip().lower().startswith('root:')]

    def _sync_legit_selected_text(self):
        # Keep the bridge payload clean: only selected part lines go into legit_selected_parts.
        # Root is already sent separately as legit_root_serial, so a root: comment line can break build/give actions.
        parts=[]
        for slot in sorted(self.legit_selected_by_slot.keys()):
            for val in self.legit_selected_by_slot[slot]:
                if val and not str(val).strip().lower().startswith('root:'):
                    parts.append(str(val).strip())
        value='\n'.join(parts)
        self.field_vars['legit_selected_parts'].set(value)
        txt=self.widgets.get('legit_selected_parts')
        if isinstance(txt, tk.Text):
            txt.delete('1.0','end'); txt.insert('1.0',value)

    def _legit_passive_base_key(self, key):
        import re
        try:
            return re.sub(r'_tier_\d+$', '', str(key or '').strip().lower())
        except Exception:
            return str(key or '').strip().lower()

    def _legit_apply_max_passives_local(self):
        import re
        root = self._legit_current_root()
        if not root:
            return self.log('Choose a class mod root first before using Add All Max Passives.')
        root_name = (str(root.get('key') or '') + ' ' + str(root.get('name') or '') + ' ' + str(root.get('display') or '') + ' ' + str(root.get('basetype') or '')).lower()
        if 'classmod' not in root_name and 'class_mod' not in root_name and 'class mod' not in root_name:
            return self.log('Add All Max Passives is only for class mod roots.')
        unlock = str(self.field_vars.get('legit_unlock_modded', tk.StringVar(value='false')).get() or '').lower() in ('1','true','yes','on')
        if not unlock:
            return self.log('Turn on Unlock rules for modded gear before adding every max passive.')
        best = {}
        scanned = 0
        for p in root.get('parts', []) or []:
            if str(p.get('table') or '').strip() != 'passive_points':
                continue
            key = str(p.get('key') or p.get('internal') or '').strip()
            if not key.lower().startswith('passive_'):
                continue
            m = re.search(r'_tier_(\d+)$', key.lower())
            if not m:
                continue
            scanned += 1
            try:
                tier = int(m.group(1))
            except Exception:
                tier = 0
            base = self._legit_passive_base_key(key)
            line = self._slot_line_from_part(p) if hasattr(self, '_slot_line_from_part') else f"{p.get('table')}:{p.get('key')}"
            if not line or ':' not in line:
                continue
            old = best.get(base)
            if old is None or tier > old[0]:
                best[base] = (tier, line)
        max_lines = [line for _tier, line in sorted(best.values(), key=lambda item: item[1].lower())]
        if not max_lines:
            return self.log(f'No passive_points max-tier parts found for {root.get("key") or root.get("display") or "selected root"}. Scanned {scanned} passive parts.')
        # Replace existing passive_points selection with exactly the max-tier set, preserving all other selected slots.
        self.legit_selected_by_slot['passive_points'] = list(max_lines)
        self._sync_legit_selected_text()
        self._render_legit_slots()
        self.log(f'Added {len(max_lines)} max-tier passive point parts for {root.get("display") or root.get("key")}. Replaced existing passive_points selections.')



    # ---------------- V20 BL4 Codes: local Lootlemon + live GZO import ----------------
    GZO_CODES_URL = 'https://save-editor.be/GZO/Borderlands4/Codes.html'
    GZO_CATALOG_URL = 'https://save-editor.be/GZO/Borderlands4/codes/api.php?action=catalog'
    GZO_CACHE_NAME = 'MattsSDKBoostingTools_gzo_codes.json'
    GZO_CACHE_VERSION = 5
    GZO_SERIAL_RE = re.compile(r"@U[0-9A-Za-z!#$%&()*+\-;<=>?@^_`{/}~]{12,}")

    def _gzo_cache_path_external(self):
        return RESOURCE_DIR / self.GZO_CACHE_NAME

    def _ascii_clean(self, text):
        text = str(text or '')
        repl = {'–':'-','—':'-','’':"'",'‘':"'",'“':'"','”':'"','…':'...','✔':'X','✕':'X','▷':'>','◇':'*'}
        for k,v in repl.items(): text = text.replace(k,v)
        return text.encode('ascii','ignore').decode('ascii').strip()

    def _is_valid_bl4_serial(self, serial):
        serial = str(serial or '').strip()
        if not self.GZO_SERIAL_RE.fullmatch(serial): return False
        tail = serial[2:].lower()
        if len(set(tail)) <= 2 and ('x' in tail or '0' in tail): return False
        return True

    def _gzo_entry_id(self, row):
        return str(abs(hash('|'.join(str(row.get(k,'')) for k in ('name','serial','listing','source')))))

    def _norm_listing(self, *vals):
        text = ' '.join(str(v or '') for v in vals).lower()
        if 'modded' in text: return 'Modded'
        if 'legit' in text: return 'Legit'
        if 'lootlemon' in text: return 'Lootlemon'
        return 'GZO'

    def _gzo_get_field(self, obj, *keys):
        if not isinstance(obj, dict): return ''
        low = {str(k).lower(): v for k,v in obj.items()}
        for key in keys:
            if key in obj and obj[key] not in (None, ''): return obj[key]
            v = low.get(str(key).lower())
            if v not in (None, ''): return v
        return ''

    def _gzo_collect_tags(self, obj):
        vals=[]
        for k in ('tags','tag','labels','categories','meta','notes'):
            v = self._gzo_get_field(obj, k)
            if isinstance(v, list): vals += [str(x) for x in v]
            elif isinstance(v, dict): vals += [str(x) for x in v.values()]
            elif v: vals.append(str(v))
        return vals

    def _gzo_classify_tags(self, tags):
        text = ' '.join(tags).lower()
        out = {'type':'','rarity':'','manufacturer':'','character_class':'','tags':self._ascii_clean(', '.join(tags))}
        type_map = [('class mod','Class Mods'),('classmod','Class Mods'),('weapon','Weapons'),('shield','Shields'),('grenade','Ordnance'),('repkit','Repkits'),('enhancement','Enhancements'),('firmware','Firmware')]
        for needle,label in type_map:
            if needle in text: out['type']=label; break
        for r in ('Pearlescent','Legendary','Epic','Rare','Uncommon','Common'):
            if r.lower() in text: out['rarity']=r; break
        for m in ('C4SH','Atlas','COV','Daedalus','Hyperion','Jakobs','Maliwan','Order','Ripper','Tediore','Torgue','Vladof'):
            if m.lower() in text: out['manufacturer']=m; break
        for c in ('Vex','Rafa','Harlowe','Amon'):
            if c.lower() in text: out['character_class']=c; break
        return out

    def _normalize_gzo_row(self, raw, inherited_listing=''):
        serial = self._gzo_get_field(raw, 'base85','Base85','serial','code','value') if isinstance(raw,dict) else ''
        if not self._is_valid_bl4_serial(serial): return None
        tags = self._gzo_collect_tags(raw) if isinstance(raw,dict) else []
        classified = self._gzo_classify_tags(tags)
        listing = self._norm_listing(inherited_listing, self._gzo_get_field(raw,'targetListing','listing','destination','bucket','folder','legitOrModded','list','category') if isinstance(raw,dict) else '')
        name = self._gzo_get_field(raw,'name','displayName','title','itemName') if isinstance(raw,dict) else ''
        row = {
            'id':'',
            'name': self._ascii_clean(name) or 'GZO Serial',
            'serial': str(serial).strip(),
            'listing': listing,
            'category': self._ascii_clean(self._gzo_get_field(raw,'category','type','itemType') if isinstance(raw,dict) else '') or classified.get('type','') or 'BL4 Codes',
            'type': self._ascii_clean(self._gzo_get_field(raw,'type','itemType') if isinstance(raw,dict) else '') or classified.get('type',''),
            'rarity': self._ascii_clean(self._gzo_get_field(raw,'rarity') if isinstance(raw,dict) else '') or classified.get('rarity',''),
            'manufacturer': self._ascii_clean(self._gzo_get_field(raw,'manufacturer','maker') if isinstance(raw,dict) else '') or classified.get('manufacturer',''),
            'creator': self._ascii_clean(self._gzo_get_field(raw,'creator','author','creatorName','owner') if isinstance(raw,dict) else ''),
            'source': 'GZO',
            'url': self.GZO_CODES_URL,
            'mattmab_validator': self._ascii_clean(self._gzo_get_field(raw,'mattmab_validator','validator','validation','mattmabResult','result') if isinstance(raw,dict) else ''),
            'mattmab_validator_detail': self._ascii_clean(self._gzo_get_field(raw,'mattmab_validator_detail','validatorDetail','detail') if isinstance(raw,dict) else ''),
            'tags': classified.get('tags',''),
        }
        row['id'] = self._gzo_entry_id(row)
        return row

    def _walk_gzo_json(self, obj, out, seen, inherited_listing=''):
        if isinstance(obj, dict):
            listing = self._norm_listing(inherited_listing, self._gzo_get_field(obj,'targetListing','listing','destination','bucket','folder','legitOrModded','list'))
            row = self._normalize_gzo_row(obj, listing)
            if row and row['serial'] not in seen:
                seen.add(row['serial']); out.append(row)
            for v in obj.values(): self._walk_gzo_json(v, out, seen, listing)
        elif isinstance(obj, list):
            for v in obj: self._walk_gzo_json(v, out, seen, inherited_listing)

    def _fetch_gzo_catalog_entries(self):
        req = request.Request(self.GZO_CATALOG_URL, headers={'User-Agent':'MattsBoostingToolsExternal/1.0','Accept':'application/json,text/plain,*/*'})
        with request.urlopen(req, timeout=20) as resp:
            text = resp.read(12_000_000).decode('utf-8','replace')
        out=[]; seen=set()
        try:
            self._walk_gzo_json(json.loads(text), out, seen, '')
        except Exception:
            # Fallback for odd API responses: scan visible text for serials, mark them as GZO.
            for m in self.GZO_SERIAL_RE.finditer(text):
                serial=m.group(0)
                if self._is_valid_bl4_serial(serial) and serial not in seen:
                    row={'id':'','name':'GZO Serial','serial':serial,'listing':'GZO','category':'BL4 Codes','type':'','rarity':'','manufacturer':'','creator':'','source':'GZO','url':self.GZO_CODES_URL,'mattmab_validator':'','mattmab_validator_detail':''}
                    row['id']=self._gzo_entry_id(row); seen.add(serial); out.append(row)
        # If the server gives only raw GZO rows, merge local Lootlemon rows too for complete catalog behavior.
        return out

    def _save_gzo_cache_external(self, entries):
        path = self._gzo_cache_path_external(); path.parent.mkdir(parents=True, exist_ok=True)
        payload={'version':self.GZO_CACHE_VERSION,'updated':int(time.time()),'source':self.GZO_CATALOG_URL,'entries':entries}
        path.write_text(json.dumps(payload, indent=2), encoding='utf-8')

    def _load_gzo_cache_external(self):
        path = self._gzo_cache_path_external()
        if not path.exists(): return []
        try:
            payload=json.loads(path.read_text(encoding='utf-8'))
            rows=payload.get('entries',[]) if isinstance(payload,dict) else []
            return [r for r in rows if isinstance(r,dict) and self._is_valid_bl4_serial(r.get('serial',''))]
        except Exception:
            return []

    def _refresh_gzo_catalog_async(self):
        self.log('Refreshing GZO BL4 codes from save-editor.be catalog API...')
        def work():
            try:
                rows = self._fetch_gzo_catalog_entries()
                self._save_gzo_cache_external(rows)
                def done():
                    self._populate_bl4_filter_values()
                    self._populate_bl4_codes_v13()
                    self.log(f'Refreshed GZO catalog: {len(rows)} code(s) cached locally. Use Listing = Modded or Legit to filter GZO rows.')
                self.after(0, done)
            except Exception as exc:
                self.after(0, lambda:self.log(f'GZO refresh failed: {exc!r}'))
        threading.Thread(target=work, daemon=True).start()

    def _get_lootlemon_entries(self):
        data = self.resources.get('lootlemon_codes') or {}
        entries = data.get('entries', []) if isinstance(data, dict) else []
        out=[]
        for e in entries:
            if not isinstance(e,dict): continue
            row=dict(e)
            row.setdefault('listing','Lootlemon')
            row.setdefault('source','Lootlemon')
            row.setdefault('type', row.get('category',''))
            out.append(row)
        return out

    def _get_gzo_entries(self):
        return self._load_gzo_cache_external()

    def _get_code_entries(self):
        # Merge by serial, preferring GZO metadata because it carries Legit/Modded listing.
        rows=[]; by_serial={}
        for e in self._get_lootlemon_entries():
            serial=str(e.get('serial') or '').strip()
            if serial:
                by_serial[serial]=e
            else:
                rows.append(e)
        for g in self._get_gzo_entries():
            serial=str(g.get('serial') or '').strip()
            if serial and serial in by_serial:
                merged=dict(by_serial[serial]); merged.update({k:v for k,v in g.items() if v not in (None,'')})
                by_serial[serial]=merged
            elif serial:
                by_serial[serial]=g
        rows += list(by_serial.values())
        return rows

    def _code_display(self, e):
        name = e.get('name') or 'Unnamed'
        cat = e.get('type') or e.get('category') or 'Unknown'
        rarity = e.get('rarity') or ''
        man = e.get('manufacturer') or ''
        source = e.get('source') or 'Local'
        listing = e.get('listing') or ''
        status = e.get('mattmab_validator') or 'Unchecked'
        pieces = [f"[ ] [{source}/{listing}] {name}", f"[{cat}]", rarity, status]
        if man: pieces.append(man)
        return ' | '.join([p for p in pieces if p])

    def _code_value(self, e, key):
        if key == 'category': return str(e.get('type') or e.get('category') or '').strip()
        if key == 'source': return str(e.get('creator') or e.get('source') or '').strip()
        return str(e.get(key) or '').strip()

    def _code_filter_values(self, key, label_all='All'):
        vals = sorted({self._code_value(e,key) for e in self._get_code_entries() if self._code_value(e,key)})
        return [label_all] + vals

    def _populate_bl4_filter_values(self):
        mapping = {
            'code_listing':['All','GZO','Legit','Modded','Lootlemon','Local Cache'],
            'code_type':self._code_filter_values('category'),
            'code_manufacturer':self._code_filter_values('manufacturer'),
            'code_rarity':self._code_filter_values('rarity'),
            'code_creator':self._code_filter_values('source'),
        }
        for fid, values in mapping.items():
            cb=self.widgets.get(fid)
            if isinstance(cb, ttk.Combobox):
                cur=self.field_vars.get(fid, tk.StringVar(value='All')).get()
                cb.configure(values=values)
                if cur not in values: self.field_vars[fid].set(values[0] if values else '')

    def _tab_two_col(self, body, tab, cards):
        if tab.get('id') == 'serial_tools':
            return self._tab_serial_tools_blimgui(body)
        if tab.get('id') == 'bl4_codes':
            return self._tab_bl4_codes_v13(body, cards)
        return super()._tab_two_col(body, tab, cards)

    def _serial_tools_text_area(self, parent, fid, height, readonly=False):
        txt = tk.Text(parent, height=height, bg='#181417', fg='#f1f5ff', insertbackground='#f1f5ff', relief='flat', wrap='word', font=('Consolas',8))
        txt.pack(fill='x', padx=8, pady=(2,6))
        self.widgets[fid] = txt
        self.field_vars[fid] = self.field_vars.get(fid) or tk.StringVar(value='')
        if readonly:
            txt.configure(state='disabled')
        return txt

    def _serial_tools_get_text(self, fid):
        widget = self.widgets.get(fid)
        if isinstance(widget, tk.Text):
            try:
                return widget.get('1.0', 'end-1c')
            except Exception:
                return ''
        return self.field_vars.get(fid, tk.StringVar(value='')).get()

    def _serial_tools_set_text(self, fid, value):
        value = str(value or '')
        self.field_vars[fid] = self.field_vars.get(fid) or tk.StringVar(value='')
        self.field_vars[fid].set(value)
        widget = self.widgets.get(fid)
        if isinstance(widget, tk.Text):
            try:
                state = str(widget.cget('state'))
                if state == 'disabled':
                    widget.configure(state='normal')
                widget.delete('1.0', 'end')
                widget.insert('1.0', value)
                if state == 'disabled':
                    widget.configure(state='disabled')
            except Exception:
                pass

    def _tab_serial_tools_blimgui(self, body):
        wrap, inner = self._card_wrap(body, 'Serial Tools', '#00a3d7')
        wrap.pack(fill='both', expand=True, padx=6, pady=5)
        tk.Label(
            inner,
            text='Paste a @U serialized value or deserialized human-readable serial below. The converter returns both formats.',
            bg='#090d17',
            fg='#9fb3d9',
            font=('Segoe UI',8),
            anchor='w',
            justify='left',
            wraplength=1100,
        ).pack(fill='x', padx=8, pady=(6,2))

        tk.Label(inner, text='Input', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').pack(fill='x', padx=8, pady=(4,0))
        inp = self._serial_tools_text_area(inner, 'serial_input', 5)
        inp.bind('<KeyRelease>', self._serial_tools_input_changed)

        buttons = tk.Frame(inner, bg='#090d17')
        buttons.pack(fill='x', padx=6, pady=(0,6))
        for i, (label, cmd, color) in enumerate([
            ('Convert', self._serial_convert_local, 'cyan'),
            ('Clear', self._clear_serial_tools_local, 'red'),
        ]):
            tk.Button(buttons, text=label, command=cmd, bg='#172033', activebackground='#22304c', fg=ACCENT_COLORS.get(color,'#00d4ff'), activeforeground=ACCENT_COLORS.get(color,'#00d4ff'), relief='flat', padx=8, pady=5, font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
            buttons.grid_columnconfigure(i, weight=1, uniform='serial_tools_buttons')

        status = self.field_vars.get('serial_tools_status') or tk.StringVar(value='Paste a @U serial or deserialized serial text above.')
        self.field_vars['serial_tools_status'] = status
        self.widgets['serial_tools_status'] = tk.Label(inner, textvariable=status, bg='#090d17', fg='#21e05f', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1100)
        self.widgets['serial_tools_status'].pack(fill='x', padx=8, pady=(0,6))

        self._serial_tools_output_section(inner, 'Deserialized Output', 'serial_tools_deserialized', 5, 'Copy Deserialized', 'deserialized serial')
        self._serial_tools_output_section(inner, 'Parts Breakdown', 'serial_tools_parts_breakdown', 7, 'Copy Parts Breakdown', 'parts breakdown')
        self._serial_tools_output_section(inner, '@U Serialized Output', 'serial_tools_serialized', 3, 'Copy Serialized', 'serialized @U serial')

    def _serial_tools_output_section(self, parent, title, fid, height, copy_button, copy_label):
        tk.Frame(parent, bg='#333a48', height=1).pack(fill='x', padx=8, pady=(5,5))
        header = tk.Frame(parent, bg='#090d17')
        header.pack(fill='x', padx=8, pady=(0,1))
        tk.Label(header, text=title, bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').pack(side='left')
        tk.Button(
            header,
            text=copy_button,
            command=lambda f=fid, c=copy_label: self._copy_text_v13(self._serial_tools_get_text(f), c) if self._serial_tools_get_text(f).strip() else self.log(f'No {c} to copy.'),
            bg='#172033',
            activebackground='#22304c',
            fg=ACCENT_COLORS.get('purple','#b36bff'),
            activeforeground=ACCENT_COLORS.get('purple','#b36bff'),
            relief='flat',
            padx=8,
            pady=5,
            font=('Segoe UI',8,'bold'),
        ).pack(side='right', padx=3, pady=1)
        self._serial_tools_text_area(parent, fid, height)

    def _serial_tools_input_changed(self, _event=None):
        widget = self.widgets.get('serial_input')
        if isinstance(widget, tk.Text):
            self.field_vars['serial_input'].set(widget.get('1.0', 'end-1c'))
        pending = getattr(self, '_serial_tools_after_id', None)
        if pending:
            try:
                self.after_cancel(pending)
            except Exception:
                pass
        self._serial_tools_after_id = self.after(350, lambda: self._serial_convert_local(auto=True))

    def _field_row_combo_v13(self, parent, label, fid, values, readonly=True):
        row = tk.Frame(parent, bg='#090d17'); row.pack(fill='x', padx=8, pady=2)
        tk.Label(row, text=label, bg='#090d17', fg='#cfd8f3', width=18, anchor='w', font=('Segoe UI',8)).pack(side='left')
        var = self.field_vars.get(fid) or tk.StringVar(value='')
        self.field_vars[fid] = var
        cb = ttk.Combobox(row, textvariable=var, values=values, state='readonly' if readonly else 'normal')
        cb.pack(side='left', fill='x', expand=True)
        self.widgets[fid] = cb
        if values and not var.get(): var.set(values[0])
        cb.bind('<<ComboboxSelected>>', lambda e: self._populate_bl4_codes_v13())
        return cb

    def _field_row_entry_v13(self, parent, label, fid, default='', multiline=False, height=4):
        row = tk.Frame(parent, bg='#090d17'); row.pack(fill='x', padx=8, pady=2)
        tk.Label(row, text=label, bg='#090d17', fg='#cfd8f3', width=18, anchor='w', font=('Segoe UI',8)).pack(side='left')
        var = self.field_vars.get(fid) or tk.StringVar(value=str(default))
        self.field_vars[fid] = var
        if multiline:
            w = tk.Text(row, height=height, bg='#181417', fg='#f1f5ff', insertbackground='#f1f5ff', relief='flat', wrap='word', font=('Consolas',8))
            w.insert('1.0', var.get())
            w.pack(side='left', fill='x', expand=True)
            w.bind('<KeyRelease>', lambda e,v=var,w=w: v.set(w.get('1.0','end-1c')))
        else:
            w = ttk.Entry(row, textvariable=var)
            w.pack(side='left', fill='x', expand=True)
            w.bind('<KeyRelease>', lambda e: self._populate_bl4_codes_v13())
        self.widgets[fid] = w
        return w

    def _tab_bl4_codes_v13(self, body, cards):
        wrap, inner = self._card_wrap(body, 'BL4 Codes', '#b37a00')
        wrap.pack(fill='both', expand=True, padx=6, pady=5)
        tk.Label(inner, text='Merged local BL4 codes catalog. Search/filter works without the game; delivery and live breakdown run through the bridge.', bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w').pack(fill='x', padx=8, pady=(6,2))

        top = tk.Frame(inner, bg='#090d17'); top.pack(fill='x', padx=8, pady=4)
        left_filters = tk.Frame(top, bg='#090d17'); left_filters.pack(side='left', fill='x', expand=True)
        right_filters = tk.Frame(top, bg='#090d17'); right_filters.pack(side='left', fill='x', expand=True, padx=(10,0))

        self._field_row_entry_v13(left_filters, 'Search', 'code_search', '')
        self._field_row_combo_v13(left_filters, 'Listing', 'code_listing', ['All','Lootlemon','Local Cache'])
        self._field_row_combo_v13(left_filters, 'Type', 'code_type', self._code_filter_values('category'))
        self._field_row_combo_v13(right_filters, 'Manufacturer', 'code_manufacturer', self._code_filter_values('manufacturer'))
        self._field_row_combo_v13(right_filters, 'Rarity', 'code_rarity', self._code_filter_values('rarity'))
        self._field_row_combo_v13(right_filters, 'Creator', 'code_creator', self._code_filter_values('source'))
        self._field_row_combo_v13(right_filters, 'Mattmab Result', 'code_mattmab_result', ['All','Unchecked','Legit','Modded','Error','?'])

        filter_buttons = tk.Frame(inner, bg='#090d17'); filter_buttons.pack(fill='x', padx=8, pady=(0,4))
        for i,(txt,val,col) in enumerate([('All Results','All','cyan'),('Legit','Legit','green'),('Modded','Modded','purple'),('Error','Error','red'),('?','?','purple')]):
            tk.Button(filter_buttons, text=txt, command=lambda v=val:self._set_bl4_result_filter(v), bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0, column=i, sticky='ew', padx=3, pady=3)
        for i in range(5): filter_buttons.grid_columnconfigure(i, weight=1)

        # V21: show the code-cache/GZO controls directly in this custom BL4 Codes tab.
        # Earlier builds had the actions in ui_layout.json, but this tab renderer replaced the generic
        # card renderer, so Refresh GZO was wired but never drawn.
        cache_buttons = tk.Frame(inner, bg='#090d17'); cache_buttons.pack(fill='x', padx=8, pady=(0,6))
        for i,(txt,cmd,col) in enumerate([
            ('Load Cache', lambda:self._codes_local_action('codes_load_cache'), 'cyan'),
            ('Refresh GZO', self._refresh_gzo_catalog_async, 'gold'),
            ('Reload Lootlemon Cache', lambda:self._codes_local_action('codes_reload_lootlemon'), 'gold'),
            ('Mattmab Validation', lambda:self.run_action({'id':'codes_mattmab_validation','label':'Mattmab Validation','uses_fields':['code_serial']}), 'green'),
        ]):
            tk.Button(cache_buttons, text=txt, command=cmd, bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
        for i in range(4): cache_buttons.grid_columnconfigure(i, weight=1)

        main = tk.Frame(inner, bg='#090d17'); main.pack(fill='both', expand=True, padx=8, pady=4)
        main.grid_columnconfigure(0, weight=3); main.grid_columnconfigure(1, weight=2); main.grid_rowconfigure(1, weight=1)
        tk.Label(main, text='CODES', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').grid(row=0,column=0,sticky='ew')
        tk.Label(main, text='DETAILS', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').grid(row=0,column=1,sticky='ew',padx=(8,0))
        self.bl4_codes_listbox = tk.Listbox(main, height=18, selectmode='extended', bg='#0e1320', fg='#d7def5', selectbackground='#1f3b63', relief='flat', font=('Consolas',8), exportselection=False)
        self.bl4_codes_listbox.grid(row=1,column=0,sticky='nsew',pady=4)
        self.bl4_codes_listbox.bind('<<ListboxSelect>>', lambda e:self._bl4_code_selected())
        details = tk.Frame(main, bg='#090d17'); details.grid(row=1,column=1,sticky='nsew',padx=(8,0),pady=4); details.grid_rowconfigure(1,weight=1); details.grid_rowconfigure(3,weight=1); details.grid_columnconfigure(0,weight=1)
        self.bl4_detail_text = tk.Text(details, height=7, bg='#181417', fg='#f1f5ff', insertbackground='#f1f5ff', relief='flat', wrap='word', font=('Consolas',8))
        self.bl4_detail_text.grid(row=0,column=0,sticky='ew')
        self.bl4_serial_text = tk.Text(details, height=5, bg='#181417', fg='#f1f5ff', insertbackground='#f1f5ff', relief='flat', wrap='word', font=('Consolas',8))
        self.bl4_serial_text.grid(row=1,column=0,sticky='nsew',pady=(5,0))
        self.bl4_breakdown_text = tk.Text(details, height=8, bg='#181417', fg='#f1f5ff', insertbackground='#f1f5ff', relief='flat', wrap='word', font=('Consolas',8))
        self.bl4_breakdown_text.grid(row=3,column=0,sticky='nsew',pady=(5,0))
        detail_buttons = tk.Frame(details, bg='#090d17'); detail_buttons.grid(row=4,column=0,sticky='ew',pady=(4,0))
        for i,(txt,cmd,col) in enumerate([
            ('Copy Parts Breakdown', self._copy_bl4_breakdown, 'purple'),
            ('Copy Serial', self._copy_bl4_serial, 'cyan'),
            ('Bookmark This', self._bookmark_bl4_selected, 'gold'),
            ('Run Parts Breakdown', self._run_bl4_parts_breakdown, 'cyan'),
        ]):
            tk.Button(detail_buttons, text=txt, command=cmd, bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=2,pady=2)
        for i in range(4): detail_buttons.grid_columnconfigure(i,weight=1)

        list_buttons = tk.Frame(inner, bg='#090d17'); list_buttons.pack(fill='x', padx=8, pady=(0,4))
        for i,(txt,cmd,col) in enumerate([
            ('Select All', self._select_all_bl4_codes, 'purple'),
            ('Clear Selection', self._clear_bl4_code_selection, 'red'),
            ('Copy Selected Serials', self._copy_selected_bl4_serials, 'gold'),
            ('Import Selected To Bookmarks', self._import_selected_bl4_bookmarks, 'purple'),
        ]):
            tk.Button(list_buttons, text=txt, command=cmd, bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
        for i in range(4): list_buttons.grid_columnconfigure(i,weight=1)

        footer = tk.Frame(inner, bg='#090d17'); footer.pack(fill='x', padx=8, pady=(4,8))
        self._field_row_combo_v13(footer, 'BL4 Codes Target', 'code_target_player', self.player_options, readonly=True)
        self._field_row_combo_v13(footer, 'Override delivery level?', 'code_override_level', ['false','true'], readonly=True)
        self._field_row_entry_v13(footer, 'Delivery Level', 'code_delivery_level', '60')
        deliver = tk.Frame(footer, bg='#090d17'); deliver.pack(fill='x', padx=8, pady=(3,0))
        for i,(txt,mode,col) in enumerate([('Deliver Selected','selected','purple'),('Deliver All','all','gold'),('Deliver Non-Host','nonhost','cyan')]):
            tk.Button(deliver, text=txt, command=lambda m=mode:self._deliver_bl4_codes(m), bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
        tk.Button(deliver, text='Refresh Players', command=self.poll_status, bg='#172033', fg='#00d4ff', relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=3,sticky='ew',padx=3,pady=3)
        for i in range(4): deliver.grid_columnconfigure(i,weight=1)
        self.bl4_filtered_entries=[]
        self._populate_bl4_filter_values()
        self._populate_bl4_codes_v13()

    def _set_bl4_result_filter(self, value):
        # In Matt's BLImGui, GZO has a separate Legit/Modded listing filter.
        # In this external tab the quick Legit/Modded buttons should be useful immediately,
        # so they switch the GZO Listing filter instead of hiding rows behind Mattmab status.
        if value in ('Legit','Modded') and 'code_listing' in self.field_vars:
            self.field_vars['code_listing'].set(value)
            if 'code_mattmab_result' in self.field_vars:
                self.field_vars['code_mattmab_result'].set('All')
        elif 'code_mattmab_result' in self.field_vars:
            self.field_vars['code_mattmab_result'].set(value)
        self._populate_bl4_codes_v13()

    def _populate_bl4_codes_v13(self):
        if not hasattr(self, 'bl4_codes_listbox'): return
        q=(self.field_vars.get('code_search', tk.StringVar()).get() or '').lower().strip()
        cat=self.field_vars.get('code_type', tk.StringVar(value='All')).get()
        man=self.field_vars.get('code_manufacturer', tk.StringVar(value='All')).get()
        rar=self.field_vars.get('code_rarity', tk.StringVar(value='All')).get()
        creator=self.field_vars.get('code_creator', tk.StringVar(value='All')).get()
        result=self.field_vars.get('code_mattmab_result', tk.StringVar(value='All')).get()
        rows=[]
        for e in self._get_code_entries():
            hay=' '.join(str(e.get(k) or '') for k in ('name','category','type','manufacturer','rarity','source','creator','listing','url','serial','tags')).lower()
            if q and q not in hay: continue
            listing=str(e.get('listing') or e.get('source') or '').strip()
            src=str(e.get('source') or '').strip()
            if self.field_vars.get('code_listing'):
                lf=self.field_vars['code_listing'].get()
                if lf == 'GZO' and src != 'GZO': continue
                elif lf == 'Lootlemon' and src != 'Lootlemon': continue
                elif lf == 'Local Cache' and src not in ('GZO','Lootlemon'): continue
                elif lf not in ('All','GZO','Lootlemon','Local Cache') and listing != lf: continue
            if cat!='All' and self._code_value(e,'category')!=cat: continue
            if man!='All' and self._code_value(e,'manufacturer')!=man: continue
            if rar!='All' and self._code_value(e,'rarity')!=rar: continue
            if creator!='All' and self._code_value(e,'source')!=creator: continue
            status=str(e.get('mattmab_validator') or '').strip() or 'Unchecked'
            if result != 'All' and status.upper() != result.upper(): continue
            rows.append(e)
        self.bl4_filtered_entries=rows
        self.bl4_codes_listbox.delete(0,'end')
        for e in rows: self.bl4_codes_listbox.insert('end', self._code_display(e))
        if rows:
            self.bl4_codes_listbox.selection_set(0)
            self._bl4_code_selected()
        else:
            self._set_bl4_detail('', '', '')
        self.log(f'BL4 Codes: showing {len(rows)} / {len(self._get_code_entries())} merged local entries. GZO cache: {len(self._get_gzo_entries())}.')

    def _selected_bl4_entries(self):
        if not hasattr(self, 'bl4_codes_listbox'): return []
        sel=list(self.bl4_codes_listbox.curselection())
        if not sel and self.bl4_filtered_entries: sel=[0]
        out=[]
        for i in sel:
            if 0 <= i < len(self.bl4_filtered_entries): out.append(self.bl4_filtered_entries[i])
        return out

    def _set_bl4_detail(self, detail, serial, breakdown):
        for widget, text in [(getattr(self,'bl4_detail_text',None), detail), (getattr(self,'bl4_serial_text',None), serial), (getattr(self,'bl4_breakdown_text',None), breakdown)]:
            if widget:
                widget.configure(state='normal'); widget.delete('1.0','end'); widget.insert('1.0', text); widget.configure(state='normal')
        self.field_vars['code_serial']=self.field_vars.get('code_serial') or tk.StringVar(value='')
        self.field_vars['code_serial'].set(serial)

    def _bl4_code_selected(self):
        entries=self._selected_bl4_entries()
        if not entries: return self._set_bl4_detail('', '', '')
        e=entries[0]
        detail='\n'.join([
            f"Name: {e.get('name','')}",
            f"Source: {e.get('source','Local')}",
            f"Listing: {e.get('listing','')}",
            f"Type: {e.get('type') or e.get('category','')}",
            f"Manufacturer: {e.get('manufacturer','')}",
            f"Rarity: {e.get('rarity','')}",
            f"Creator: {e.get('creator','')}",
            f"Mattmab Validation: {e.get('mattmab_validator') or 'Unchecked'}",
            f"URL: {e.get('url','')}",
        ])
        serial=e.get('serial') or ''
        breakdown='Select Run Parts Breakdown to ask the in-game bridge/SDK decoder for this serial.'
        self._set_bl4_detail(detail, serial, breakdown)

    def _select_all_bl4_codes(self):
        if hasattr(self,'bl4_codes_listbox'):
            self.bl4_codes_listbox.selection_set(0,'end'); self.log(f'Selected {len(self.bl4_filtered_entries)} BL4 code rows.')

    def _clear_bl4_code_selection(self):
        if hasattr(self,'bl4_codes_listbox'):
            self.bl4_codes_listbox.selection_clear(0,'end'); self.log('Cleared BL4 code selection.')

    def _selected_bl4_serials(self):
        return [str(e.get('serial') or '').strip() for e in self._selected_bl4_entries() if str(e.get('serial') or '').strip()]

    def _copy_text_v13(self, text, label):
        try:
            self.clipboard_clear(); self.clipboard_append(text); self.log(f'Copied {label}.')
        except Exception as exc: self.log(f'Copy failed: {exc}')

    def _copy_selected_bl4_serials(self):
        serials=self._selected_bl4_serials()
        if not serials: return self.log('No BL4 codes selected.')
        self._copy_text_v13('\n'.join(serials), f'{len(serials)} selected serial(s)')

    def _copy_bl4_serial(self):
        serial=self.field_vars.get('code_serial', tk.StringVar()).get()
        if not serial: return self.log('No serial selected.')
        self._copy_text_v13(serial, 'serial')

    def _copy_bl4_breakdown(self):
        text=getattr(self,'bl4_breakdown_text',None).get('1.0','end-1c') if getattr(self,'bl4_breakdown_text',None) else ''
        if not text: return self.log('No parts breakdown to copy.')
        self._copy_text_v13(text, 'parts breakdown')

    def _bookmark_bl4_selected(self):
        entries=self._selected_bl4_entries()
        if not entries: return self.log('No selected code to bookmark.')
        self.log(f'Bookmark staging: {entries[0].get("name")} is selected. Full bookmark save/edit parity is still a local-data pass item.')

    def _import_selected_bl4_bookmarks(self):
        entries=self._selected_bl4_entries()
        self.log(f'Import selected to bookmarks staged for {len(entries)} item(s). Full persistent bookmark write is still a local-data pass item.')

    def _run_bl4_parts_breakdown(self):
        serial=self.field_vars.get('code_serial', tk.StringVar()).get().strip()
        if not serial: return self.log('No serial selected for parts breakdown.')
        action={'id':'serial_breakdown','uses_fields':['code_serial']}
        old=self.field_vars.get('serial_input')
        self.field_vars['serial_input']=tk.StringVar(value=serial)
        # send directly because bridge expects serial_input for serial_breakdown
        payload={'serial_input':serial}
        self.log('Requesting SDK parts breakdown for selected BL4 code...')
        def work():
            try:
                res=http_json('POST','/action',{'action':'serial_breakdown','payload':payload,'timeout':10.0},timeout=12.0)
                msg=res.get('message') or json.dumps(res)
                def done():
                    if getattr(self,'bl4_breakdown_text',None):
                        self.bl4_breakdown_text.delete('1.0','end'); self.bl4_breakdown_text.insert('1.0',msg)
                    self.log('Parts breakdown returned.')
                self.after(0, done)
            except Exception as exc:
                self.after(0, lambda:self.log('Parts breakdown failed: '+repr(exc)))
        threading.Thread(target=work, daemon=True).start()

    def _deliver_bl4_codes(self, mode):
        serials=self._selected_bl4_serials()
        if not serials:
            serial=(self.field_vars.get('code_serial', tk.StringVar()).get() or '').strip()
            if serial: serials=[serial]
        if not serials: return self.log('No BL4 serial selected to deliver.')
        try: level=int(str(self.field_vars.get('code_delivery_level', tk.StringVar(value='60')).get()).replace(',','').strip())
        except Exception: return messagebox.showerror('Invalid value','Delivery Level must be a number.')
        override=str(self.field_vars.get('code_override_level', tk.StringVar(value='false')).get()).lower() in ('1','true','yes','on')
        payload={'serial_text':'\n'.join(serials),'serial_level':level,'serial_override_level':override}
        aid={'selected':'give_serial_selected','all':'give_serial_all','nonhost':'give_serial_nonhost'}[mode]
        self.log(f'Delivering {len(serials)} BL4 code serial(s) to {mode}...')
        def work():
            try:
                res=http_json('POST','/action',{'action':aid,'payload':payload,'timeout':10.0},timeout=18.0)
                self.after(0, lambda:self.log(res.get('message') or 'BL4 code delivery requested.'))
                self.after(0, self.poll_status)
            except Exception as exc:
                self.after(0, lambda:self.log('Delivery failed: '+repr(exc)))
        threading.Thread(target=work, daemon=True).start()

    def _update_player_options(self, status):
        super()._update_player_options(status)
        try:
            cb=self.widgets.get('code_target_player')
            if isinstance(cb, ttk.Combobox):
                cb.configure(values=self.player_options)
                cur=self.field_vars.get('code_target_player', tk.StringVar()).get()
                if not cur and self.player_options: self.field_vars['code_target_player'].set(self.player_options[0])
        except Exception: pass


    def _clear_external_log_local(self):
        try:
            self.log_text.configure(state='normal'); self.log_text.delete('1.0','end'); self.log_text.configure(state='disabled')
            self.status_var.set('Log cleared.')
        except Exception:
            self.log('Log cleared.')

    def _clear_serial_tools_local(self):
        for fid in ('serial_input','serial_tools_serialized','serial_tools_deserialized','serial_tools_parts_breakdown','serial_output','serial_result'):
            if hasattr(self, '_serial_tools_set_text'):
                self._serial_tools_set_text(fid, '')
            else:
                var=self.field_vars.get(fid)
                if var: var.set('')
        if 'serial_tools_status' in self.field_vars:
            self.field_vars['serial_tools_status'].set('Paste a @U serial or deserialized serial text above.')
        if getattr(self,'output_text',None):
            try:
                self.output_text.configure(state='normal'); self.output_text.delete('1.0','end'); self.output_text.configure(state='disabled')
            except Exception: pass
        self.log('Cleared Serial Tools input/output.')

    def _clear_boosting_serials_local(self):
        var=self.field_vars.get('serial_text')
        if var: var.set('')
        self.log('Cleared Boosting serial input.')

    def _bookmark_store_path(self):
        from pathlib import Path
        p=Path(__file__).resolve().parent/'resources'/'user_serial_bookmarks.json'
        return p

    def _load_bookmark_store(self):
        import json
        p=self._bookmark_store_path()
        if not p.exists(): return []
        try: return json.loads(p.read_text(encoding='utf-8'))
        except Exception: return []

    def _save_bookmark_store(self, rows):
        import json
        p=self._bookmark_store_path(); p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(rows,indent=2),encoding='utf-8')

    def _bookmark_current_payload(self):
        return {
            'name': self.field_vars.get('bookmark_name',tk.StringVar()).get().strip() or 'Untitled Serial',
            'group': self.field_vars.get('bookmark_group',tk.StringVar()).get().strip(),
            'serial': self.field_vars.get('bookmark_serial',tk.StringVar()).get().strip(),
        }

    def _serial_bookmark_action_local(self, aid):
        rows=self._load_bookmark_store(); cur=self._bookmark_current_payload()
        if aid=='serial_bookmark_new':
            self.field_vars.setdefault('bookmark_name',tk.StringVar()).set('')
            self.field_vars.setdefault('bookmark_group',tk.StringVar()).set('')
            self.field_vars.setdefault('bookmark_serial',tk.StringVar()).set('')
            return self.log('New bookmark fields cleared.')
        if aid in ('serial_bookmark_save','serial_bookmark_import'):
            if not cur['serial']: return self.log('No bookmark serial to save/import.')
            rows.append(cur); self._save_bookmark_store(rows); return self.log(f"Saved bookmark: {cur['name']}")
        if aid=='serial_bookmark_duplicate':
            if not cur['serial']: return self.log('No bookmark serial to duplicate.')
            cur['name']=cur['name']+' Copy'; rows.append(cur); self._save_bookmark_store(rows); return self.log(f"Duplicated bookmark: {cur['name']}")
        if aid=='serial_bookmark_delete':
            serial=cur['serial']; before=len(rows); rows=[r for r in rows if r.get('serial')!=serial]
            self._save_bookmark_store(rows); return self.log(f'Deleted {before-len(rows)} matching bookmark(s).')
        if aid=='serial_bookmark_copy':
            serial=cur['serial']
            if not serial: return self.log('No bookmark serial to copy.')
            self._copy_text_v13(serial,'bookmark serial')
            return

    def _codes_local_action(self, aid):
        if aid == 'codes_refresh_gzo':
            return self._refresh_gzo_catalog_async()
        if aid in ('codes_load_cache','codes_reload_lootlemon'):
            try:
                self._populate_bl4_filter_values(); self._populate_bl4_codes_v13(); self.log('Reloaded bundled Lootlemon + local GZO cache resources.')
            except Exception as exc: self.log(f'Reload code resources failed: {exc!r}')
            return
        if aid=='codes_import_bookmarks':
            entries=self._selected_bl4_entries()
            if not entries: return self.log('No BL4 codes selected to import.')
            rows=self._load_bookmark_store()
            for e in entries:
                rows.append({'name':e.get('name') or 'BL4 Code','group':e.get('category') or 'BL4 Codes','serial':e.get('serial') or ''})
            self._save_bookmark_store(rows); self.log(f'Imported {len(entries)} selected BL4 code(s) to local bookmarks.')
            return

    def _serial_tools_input_value(self):
        if hasattr(self, '_serial_tools_get_text'):
            return self._serial_tools_get_text('serial_input')
        return self.field_vars.get('serial_input', tk.StringVar(value='')).get()

    def _serial_tools_set_status(self, message, *, log_message=None, log_global=True):
        if 'serial_tools_status' in self.field_vars:
            self.field_vars['serial_tools_status'].set(str(message or ''))
        if log_global:
            self.log(log_message if log_message is not None else message)

    def _serial_convert_local(self, auto=False):
        text = self._serial_tools_input_value()
        try:
            res = convert_serial_tool(text)
        except Exception as exc:
            self._serial_tools_set_text('serial_tools_serialized', '')
            self._serial_tools_set_text('serial_tools_deserialized', '')
            self._serial_tools_set_text('serial_tools_parts_breakdown', '')
            return self._serial_tools_set_status(f'Conversion failed: {exc}', log_message=f'Serial conversion failed: {exc}', log_global=not auto)
        if res.get('ok') != 'true':
            self._serial_tools_set_text('serial_tools_serialized', '')
            self._serial_tools_set_text('serial_tools_deserialized', '')
            self._serial_tools_set_text('serial_tools_parts_breakdown', '')
            status = res.get('message') or 'Conversion failed.'
            return self._serial_tools_set_status(status, log_message=status, log_global=not auto)
        self._serial_tools_set_text('serial_tools_deserialized', res.get('deserialized') or '')
        self._serial_tools_set_text('serial_tools_parts_breakdown', res.get('breakdown') or '')
        self._serial_tools_set_text('serial_tools_serialized', res.get('serialized') or '')
        self._serial_tools_set_status('Converted locally.', log_message='Serial converted locally.', log_global=not auto)

    def _serial_breakdown_local(self):
        text = self._serial_tools_input_value()
        if not str(text or '').strip():
            return self._serial_tools_set_status('No serial input to break down.', log_message='No serial input to break down.')
        out = serial_parts_breakdown_for_value(text)
        self._serial_tools_set_text('serial_tools_parts_breakdown', out or '')
        self._serial_tools_set_status('Parts breakdown generated locally.' if out else 'No parts breakdown.', log_message='Serial parts breakdown generated locally.' if out else 'No parts breakdown.')

    def run_action(self,action):
        aid = action.get('id')
        if aid == 'serial_convert':
            return self._serial_convert_local()
        if aid == 'serial_breakdown':
            return self._serial_breakdown_local()
        if aid == 'clear_external_log':
            return self._clear_external_log_local()
        if aid == 'clear_serial_tools':
            return self._clear_serial_tools_local()
        if aid == 'clear_serials':
            return self._clear_boosting_serials_local()
        if aid in ('serial_bookmark_new','serial_bookmark_import','serial_bookmark_save','serial_bookmark_duplicate','serial_bookmark_delete','serial_bookmark_copy'):
            return self._serial_bookmark_action_local(aid)
        if aid in ('codes_load_cache','codes_refresh_gzo','codes_reload_lootlemon','codes_import_bookmarks'):
            return self._codes_local_action(aid)
        if aid == 'codes_mattmab_validation':
            action=dict(action); action['uses_fields']=['code_serial']
        if aid == 'validator_basic':
            action=dict(action); action['uses_fields']=['validator_basic_input']
        if aid == 'validator_bulk':
            action=dict(action); action['uses_fields']=['validator_bulk_input']
        if aid == 'validator_clear':
            action=dict(action); action['uses_fields']=[]
        if aid in ('set_backpack_bank_selected','set_backpack_bank_all'):
            action=dict(action); action['uses_fields']=['backpack_size','bank_size']
        if aid == 'legit_apply_max_passives':
            return self._legit_apply_max_passives_local()
        # Route all movement apply buttons with current field values even if the original card action did not declare them.
        if aid=='movement_apply_all':
            action=dict(action); action['uses_fields']=['movement_speed_scale','movement_walk_speed','movement_jump_height','movement_gravity_scale','movement_step_height','movement_floor_angle','movement_glide_speed','movement_dash_speed']
        # Ensure bridge build/give receives only selected part lines; root is already sent separately.
        if aid in ('legit_validate_build','legit_give_selected','legit_give_all'):
            self.field_vars['legit_selected_parts'].set('\n'.join(self._legit_selected_lines_without_root()))
        return super().run_action(action)

if __name__=='__main__': App().mainloop()


if __name__ == '__main__':
    App().mainloop()
