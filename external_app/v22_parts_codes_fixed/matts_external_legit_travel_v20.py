from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from matts_external_core_v20 import App as BaseApp, ACCENT_COLORS

class App(BaseApp):
    def __init__(self):
        self.legit_slot_frames = []
        self.legit_slot_parts = {}
        self.legit_selected_by_slot = {}
        self.map_listbox = None
        self.station_listbox = None
        self.travel_map_rows = []
        self.travel_station_rows = []
        super().__init__()
        self.title("Matt's SDK Boosting Tools - External V18 Legit/Travel")

    def _tab_two_col(self, body, tab, cards):
        tid = tab.get('id')
        if tid == 'legit_builder':
            return self._tab_legit_builder_v9(body, cards)
        if tid == 'map_travel':
            return self._tab_map_travel_v9(body, cards)
        if tid == 'item_pool_spawning':
            return self._tab_item_pool_v9(body, cards)
        return super()._tab_two_col(body, tab, cards)

    def _small_label(self, parent, text, color='#cfd8f3'):
        return tk.Label(parent, text=text, bg='#090d17', fg=color, font=('Segoe UI', 8), anchor='w')

    def _card_wrap(self, parent, title, color='#00a3d7'):
        wrap = tk.Frame(parent, bg=color, padx=1, pady=1)
        head = tk.Frame(wrap, bg='#0e1320'); head.pack(fill='x')
        tk.Label(head, text=title.upper(), bg='#0e1320', fg=color, font=('Segoe UI', 8, 'bold'), anchor='w').pack(side='left', padx=6, pady=(3,1))
        inner = tk.Frame(wrap, bg='#090d17'); inner.pack(fill='both', expand=True)
        return wrap, inner

    def _tab_legit_builder_v9(self, body, cards):
        main, inner = self._card_wrap(body, 'Stripped Legit Builder', '#00a3d7')
        main.pack(fill='x', padx=6, pady=5)
        tk.Label(inner, text="External version now mirrors Matt's slot-card builder: choose Type → Manufacturer → Root, then pick parts inside each slot panel.", bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w').pack(fill='x', padx=8, pady=(5,2))

        form = tk.Frame(inner, bg='#090d17'); form.pack(fill='x', padx=8, pady=4)
        labels = [('Unlock rules for modded gear','legit_unlock_modded','choice'),('Type','legit_type','legit_type'),('Manufacturer','legit_manufacturer','legit_manufacturer'),('Optional Root Filter','legit_root_filter','text'),('Root Variant','legit_root_serial','legit_root'),('Filter Available Parts','legit_part_filter','text')]
        for r,(lab,fid,typ) in enumerate(labels):
            tk.Label(form, text=lab, bg='#090d17', fg='#cfd8f3', width=22, anchor='w', font=('Segoe UI',8)).grid(row=r, column=0, sticky='w', pady=2)
            var = self.field_vars.get(fid) or tk.StringVar(value='false' if fid=='legit_unlock_modded' else '')
            self.field_vars[fid] = var
            if typ == 'choice':
                w = ttk.Combobox(form, textvariable=var, values=['false','true'], state='readonly')
                if not var.get(): var.set('false')
            elif typ in ('legit_type','legit_manufacturer','legit_root'):
                fake_type = typ
                if fid=='legit_root_serial': fake_type='legit_root'
                vals = self._values_for_field({'id':fid,'type':fake_type})
                w = ttk.Combobox(form, textvariable=var, values=vals, state='readonly')
                if vals and not var.get(): var.set(vals[0])
                w.bind('<<ComboboxSelected>>', lambda e, f={'id':fid}: self._legit_filter_changed(f['id']))
            else:
                w = ttk.Entry(form, textvariable=var)
                w.bind('<KeyRelease>', lambda e: self._refresh_legit_root_and_slots())
            w.grid(row=r, column=1, sticky='ew', pady=2)
            self.widgets[fid] = w
        form.grid_columnconfigure(1, weight=1)

        btns = tk.Frame(inner, bg='#090d17'); btns.pack(fill='x', padx=8, pady=(4,8))
        actions = cards['legit_builder_main'].get('actions', [])
        for i,a in enumerate(actions): self._button(btns, a, i, cols=6)

        selected, sel_inner = self._card_wrap(body, 'Selected composition / active build', '#8a2be2')
        selected.pack(fill='x', padx=6, pady=5)
        self.field_vars['legit_selected_parts'] = tk.StringVar(value='')
        txt = tk.Text(sel_inner, height=4, bg='#0e1320', fg='#d7def5', insertbackground='#f1f5ff', relief='flat', wrap='word', font=('Consolas',8))
        txt.pack(fill='x', padx=8, pady=8)
        txt.bind('<KeyRelease>', lambda e, w=txt: self.field_vars['legit_selected_parts'].set(w.get('1.0','end-1c')))
        self.widgets['legit_selected_parts'] = txt

        slot_wrap, slot_inner = self._card_wrap(body, 'Slots / Available Parts', '#6b7280')
        slot_wrap.pack(fill='both', expand=True, padx=6, pady=5)
        top = tk.Frame(slot_inner, bg='#090d17'); top.pack(fill='x', padx=8, pady=(5,2))
        tk.Label(top, text='Each panel is one Matt SDK slot/dependency. Select parts directly in the slot they belong to. Search filters all slot lists.', bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8)).pack(side='left')
        self.legit_slots_area = tk.Frame(slot_inner, bg='#090d17')
        self.legit_slots_area.pack(fill='both', expand=True, padx=8, pady=6)
        self._refresh_combo('legit_manufacturer'); self._refresh_combo('legit_root_serial')
        self._render_legit_slots()

    def _legit_filter_changed(self, fid):
        if fid == 'legit_type':
            self._refresh_combo('legit_manufacturer')
            self._refresh_combo('legit_root_serial')
        elif fid == 'legit_manufacturer':
            self._refresh_combo('legit_root_serial')
        self._render_legit_slots()

    def _refresh_legit_root_and_slots(self):
        self._refresh_combo('legit_root_serial')
        self._render_legit_slots()

    def _values_for_field(self, field):
        # Add root text filtering on top of V8's resource-backed values.
        if field.get('type') == 'legit_root':
            vals = super()._values_for_field(field)
            flt = (self.field_vars.get('legit_root_filter', tk.StringVar()).get() or '').lower().strip()
            return [v for v in vals if flt in v.lower()] if flt else vals
        return super()._values_for_field(field)

    def _part_label(self, p):
        serial = p.get('serial')
        label = p.get('display') or p.get('name') or p.get('key') or ''
        key = p.get('key') or ''
        rarity = p.get('rarity') or ''
        tags = ','.join(p.get('base_tags') or [])
        extra = f' | {rarity}' if rarity else ''
        if tags: extra += f' | tags: {tags}'
        return f'+{{{serial}}} {label} [{key}]{extra}'

    def _render_legit_slots(self):
        if not hasattr(self, 'legit_slots_area'): return
        for child in self.legit_slots_area.winfo_children(): child.destroy()
        self.legit_slot_parts.clear()
        root = self._legit_current_root()
        if not root:
            tk.Label(self.legit_slots_area, text='Pick a root variant to load its slot cards.', bg='#090d17', fg='#9fb3d9', font=('Segoe UI',9)).pack(anchor='w', padx=8, pady=8)
            return
        deps = list(root.get('deps') or [])
        parts = list(root.get('parts') or [])
        filter_text = (self.field_vars.get('legit_part_filter', tk.StringVar()).get() or '').lower().strip()
        grouped = {d: [] for d in deps}
        for p in parts:
            slot = str(p.get('table') or '')
            if slot not in grouped: grouped[slot] = []
            label = self._part_label(p)
            if filter_text and filter_text not in label.lower() and filter_text not in slot.lower():
                continue
            grouped[slot].append((label, p))
        cols = 3
        for idx, slot in enumerate([d for d in deps if grouped.get(d)] + [d for d in grouped if d not in deps and grouped.get(d)]):
            r, c = divmod(idx, cols)
            wrap, inner = self._card_wrap(self.legit_slots_area, slot, '#333a48')
            wrap.grid(row=r, column=c, sticky='nsew', padx=4, pady=4)
            self.legit_slots_area.grid_columnconfigure(c, weight=1, uniform='slot')
            self.legit_slots_area.grid_rowconfigure(r, weight=1)
            info = f'{len(grouped[slot])} available part(s)'
            tk.Label(inner, text=info, bg='#090d17', fg='#8c99b5', font=('Segoe UI',8), anchor='w').pack(fill='x', padx=6, pady=(3,0))
            lb = tk.Listbox(inner, height=7, selectmode='extended', bg='#0e1320', fg='#d7def5', selectbackground='#1f3b63', relief='flat', font=('Consolas',8), exportselection=False)
            lb.pack(fill='both', expand=True, padx=6, pady=4)
            self.legit_slot_parts[lb] = [(slot, label, p) for label,p in grouped[slot]]
            for label,p in grouped[slot]: lb.insert('end', label)
            lb.bind('<<ListboxSelect>>', lambda e, slot=slot, lb=lb: self._slot_selection_changed(slot, lb))
            controls = tk.Frame(inner, bg='#090d17'); controls.pack(fill='x', padx=6, pady=(0,5))
            tk.Button(controls, text='Add / Replace Slot', command=lambda slot=slot, lb=lb: self._slot_selection_changed(slot, lb, force=True), bg='#172033', fg='#00d4ff', relief='flat', font=('Segoe UI',8,'bold')).pack(side='left', fill='x', expand=True, padx=(0,2))
            tk.Button(controls, text='Clear Slot', command=lambda slot=slot: self._clear_slot(slot), bg='#172033', fg='#ff5b5b', relief='flat', font=('Segoe UI',8,'bold')).pack(side='left', fill='x', expand=True, padx=(2,0))

    def _slot_selection_changed(self, slot, lb, force=False):
        rows = self.legit_slot_parts.get(lb, [])
        selected = []
        for i in lb.curselection():
            try:
                slot, label, p = rows[i]
                selected.append(f"{p.get('table')}:{p.get('key')}")
            except Exception: pass
        if selected or force:
            self.legit_selected_by_slot[slot] = selected
            self._sync_legit_selected_text()

    def _clear_slot(self, slot):
        self.legit_selected_by_slot.pop(slot, None)
        self._sync_legit_selected_text()

    def _sync_legit_selected_text(self):
        parts=[]
        root = self._legit_current_root()
        if root:
            parts.append(f"root:{root.get('serial')}  # {root.get('_label') or root.get('key')}")
        for slot in sorted(self.legit_selected_by_slot.keys()):
            for val in self.legit_selected_by_slot[slot]: parts.append(val)
        value='\n'.join(parts)
        self.field_vars['legit_selected_parts'].set(value)
        txt=self.widgets.get('legit_selected_parts')
        if isinstance(txt, tk.Text):
            txt.delete('1.0','end'); txt.insert('1.0',value)

    def _tab_map_travel_v9(self, body, cards):
        wrap, inner = self._card_wrap(body, 'Map Travel', '#b01258')
        wrap.pack(fill='both', expand=True, padx=6, pady=5)
        tk.Label(inner, text="Matt-style two-list travel picker: select a map first, then choose a station filtered to that map. Lists are loaded locally from the external resources folder.", bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w').pack(fill='x', padx=8, pady=(6,2))
        self.field_vars['travel_map_search'] = tk.StringVar(value='')
        self.field_vars['travel_station_search'] = tk.StringVar(value='')
        self.field_vars['travel_map'] = tk.StringVar(value='')
        self.field_vars['travel_station'] = tk.StringVar(value='')
        srow = tk.Frame(inner, bg='#090d17'); srow.pack(fill='x', padx=8, pady=4)
        tk.Label(srow, text='Search Maps', bg='#090d17', fg='#cfd8f3', width=14, anchor='w', font=('Segoe UI',8)).pack(side='left')
        em = ttk.Entry(srow, textvariable=self.field_vars['travel_map_search']); em.pack(side='left', fill='x', expand=True, padx=(0,12)); em.bind('<KeyRelease>', lambda e:self._populate_maps())
        tk.Label(srow, text='Search Stations', bg='#090d17', fg='#cfd8f3', width=14, anchor='w', font=('Segoe UI',8)).pack(side='left')
        es = ttk.Entry(srow, textvariable=self.field_vars['travel_station_search']); es.pack(side='left', fill='x', expand=True); es.bind('<KeyRelease>', lambda e:self._populate_stations())
        lists = tk.Frame(inner, bg='#090d17'); lists.pack(fill='both', expand=True, padx=8, pady=4); lists.grid_columnconfigure(0, weight=1); lists.grid_columnconfigure(1, weight=1); lists.grid_rowconfigure(1, weight=1)
        tk.Label(lists, text='MAPS', bg='#090d17', fg='#00d4ff', font=('Segoe UI',8,'bold'), anchor='w').grid(row=0,column=0,sticky='ew')
        tk.Label(lists, text='TRAVEL STATIONS', bg='#090d17', fg='#ff5db7', font=('Segoe UI',8,'bold'), anchor='w').grid(row=0,column=1,sticky='ew')
        self.map_listbox = tk.Listbox(lists, height=16, bg='#0e1320', fg='#d7def5', selectbackground='#1f3b63', relief='flat', font=('Consolas',8), exportselection=False)
        self.station_listbox = tk.Listbox(lists, height=16, bg='#0e1320', fg='#d7def5', selectbackground='#1f3b63', relief='flat', font=('Consolas',8), exportselection=False)
        self.map_listbox.grid(row=1,column=0,sticky='nsew',padx=(0,4),pady=4); self.station_listbox.grid(row=1,column=1,sticky='nsew',padx=(4,0),pady=4)
        self.map_listbox.bind('<<ListboxSelect>>', self._map_selected); self.station_listbox.bind('<<ListboxSelect>>', self._station_selected)
        btns = tk.Frame(inner, bg='#090d17'); btns.pack(fill='x', padx=8, pady=(4,8))
        for i,a in enumerate(cards['map_travel_main'].get('actions',[])): self._button(btns, a, i, cols=4)
        self._populate_maps()

    def _populate_maps(self):
        data = self.resources.get('travel_maps') or {}
        rows = data.get('maps', []) if isinstance(data, dict) else []
        q = (self.field_vars.get('travel_map_search', tk.StringVar()).get() or '').lower().strip()
        self.travel_map_rows = [m for m in rows if not q or q in (m.get('display_name','') + ' ' + m.get('map','')).lower()]
        if self.map_listbox:
            self.map_listbox.delete(0,'end')
            for m in self.travel_map_rows: self.map_listbox.insert('end', f"{m.get('display_name')} | {m.get('map')}")
            if self.travel_map_rows and not self.field_vars['travel_map'].get():
                self.map_listbox.selection_set(0); self._map_selected(None)

    def _map_selected(self, event):
        sel = self.map_listbox.curselection() if self.map_listbox else []
        if not sel: return
        m = self.travel_map_rows[sel[0]]
        self.field_vars['travel_map'].set(m.get('map',''))
        self._populate_stations()

    def _populate_stations(self):
        data = self.resources.get('travel_stations') or {}
        rows = data.get('stations', []) if isinstance(data, dict) else []
        mapv = self.field_vars.get('travel_map', tk.StringVar()).get()
        q = (self.field_vars.get('travel_station_search', tk.StringVar()).get() or '').lower().strip()
        self.travel_station_rows = [s for s in rows if (not mapv or s.get('world') == mapv or str(s.get('station','')).startswith(mapv+'.')) and (not q or q in (s.get('display_name','')+' '+s.get('station','')+' '+s.get('category','')).lower())]
        if self.station_listbox:
            self.station_listbox.delete(0,'end')
            for s in self.travel_station_rows: self.station_listbox.insert('end', f"[{s.get('category','')}] {s.get('display_name')} | {s.get('station')}")
            if self.travel_station_rows:
                self.station_listbox.selection_set(0); self._station_selected(None)

    def _station_selected(self, event):
        sel = self.station_listbox.curselection() if self.station_listbox else []
        if not sel: return
        s = self.travel_station_rows[sel[0]]
        self.field_vars['travel_station'].set(s.get('station',''))

    def _tab_item_pool_v9(self, body, cards):
        # Keep V8 behavior for now but clarify local resource use.
        return super()._tab_two_col(body, {'id':'item_pool_spawning','cards':[cards['item_pool_main']]}, cards)

    def run_action(self, action):
        aid = action.get('id')
        if aid == 'legit_clear_parts':
            self.legit_selected_by_slot.clear(); self._sync_legit_selected_text(); return self.log('Cleared selected Legit Builder parts.')
        return super().run_action(action)

if __name__ == '__main__':
    App().mainloop()
