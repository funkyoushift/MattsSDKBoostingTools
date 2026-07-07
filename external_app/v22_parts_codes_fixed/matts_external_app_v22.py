
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import json, re, time, threading
import hashlib
from pathlib import Path
from urllib import request
import webbrowser
from external_serial_tools import convert_serial_tool, serial_parts_breakdown_for_value, human_to_serial
import external_legit_builder
import external_validator
from matts_external_core_v20 import ACCENT_COLORS, http_json, RESOURCE_DIR
from matts_external_legit_travel_v20 import App as V9App

MAX_SERIAL_DELIVERY_CHARS = 20000
SELECTED_SERIALS_PER_CHUNK = 25
SELECTED_CHUNK_DELAY_SECONDS = 5.0
MULTI_SERIALS_PER_CHUNK = 20
MULTI_CHUNK_DELAY_SECONDS = 6.0
SERIAL_DELIVERY_PER_SERIAL_OVERHEAD_CHARS = 16

MOVEMENT_DEFAULTS = {
    'movement_speed_scale': '1.00',
    'movement_walk_speed': '600',
    'movement_jump_height': '198',
    'movement_jump_velocity': '840',
    'movement_sprint_jump_goal': '198',
    'movement_double_jump_goal': '225',
    'movement_slide_jump_goal': '198',
    'movement_individual_jump_goals': 'false',
    'movement_jump_count': '2',
    'movement_jump_off_z_factor': '0.5',
    'movement_gravity_scale': '1.00',
    'movement_step_height': '45',
    'movement_floor_angle': '44.8',
    'movement_floor_z': '0.710',
    'movement_glide_speed': '1200',
    'movement_glide_boost': '0',
    'movement_glide_air_control': '0.60',
    'movement_dash_speed': '2500',
    'movement_zero_vault_on_apply': 'false',
    'movement_time_dilation': '1.00',
}

MOVEMENT_PRESETS = {
    'fast': {
        'movement_speed_scale': '5.00',
        'movement_walk_speed': '3200',
        'movement_jump_height': '560',
        'movement_jump_velocity': '560',
        'movement_sprint_jump_goal': '560',
        'movement_double_jump_goal': '560',
        'movement_slide_jump_goal': '560',
        'movement_individual_jump_goals': 'false',
        'movement_jump_count': '2',
        'movement_glide_speed': '2600',
        'movement_glide_boost': '4200',
        'movement_glide_air_control': '6.00',
        'movement_dash_speed': '3000',
        'movement_zero_vault_on_apply': 'true',
    },
    'veryfast': {
        'movement_speed_scale': '8.00',
        'movement_walk_speed': '5200',
        'movement_jump_height': '700',
        'movement_jump_velocity': '700',
        'movement_sprint_jump_goal': '700',
        'movement_double_jump_goal': '700',
        'movement_slide_jump_goal': '700',
        'movement_individual_jump_goals': 'false',
        'movement_jump_count': '2',
        'movement_glide_speed': '3800',
        'movement_glide_boost': '6500',
        'movement_glide_air_control': '10.00',
        'movement_dash_speed': '5200',
        'movement_zero_vault_on_apply': 'true',
    },
    'moon': {
        'movement_jump_height': '1200',
        'movement_jump_velocity': '1200',
        'movement_sprint_jump_goal': '1200',
        'movement_double_jump_goal': '1200',
        'movement_slide_jump_goal': '1200',
        'movement_individual_jump_goals': 'false',
        'movement_gravity_scale': '0.45',
        'movement_jump_count': '2',
        'movement_zero_vault_on_apply': 'true',
    },
    'wallwalk': {
        'movement_speed_scale': '5.00',
        'movement_walk_speed': '3200',
        'movement_step_height': '700',
        'movement_floor_angle': '89.9',
        'movement_floor_z': '0.001',
        'movement_jump_count': '2',
        'movement_zero_vault_on_apply': 'true',
    },
    'fastglide': {
        'movement_speed_scale': '5.00',
        'movement_walk_speed': '3200',
        'movement_glide_speed': '5200',
        'movement_glide_boost': '8500',
        'movement_glide_air_control': '14.00',
        'movement_dash_speed': '4500',
        'movement_jump_count': '2',
        'movement_zero_vault_on_apply': 'true',
    },
}

class App(V9App):
    def __init__(self):
        self.legit_duplicate_qty_var = None
        self.legit_human_output = ''
        self.legit_base85_output = ''
        self.legit_last_build_signature = ''
        self.legit_rejected_part_lines = []
        self.legit_last_root_value = ''
        self.legit_status_message = 'Select a root, add parts, then Validate or Build Base85.'
        self.bl4_active_id = ''
        self.bl4_selected_ids = set()
        self.bl4_status_message = ''
        self.bl4_progress_message = ''
        self.bl4_mattmab_results = {}
        self.bl4_mattmab_thread = None
        self.bl4_mattmab_run_id = 0
        self.bl4_cache_autoload_attempted = False
        self.validator_thread = None
        self.validator_cancel_event = threading.Event()
        self.validator_run_id = 0
        self.validator_progress = {"running": False, "label": "Idle", "done": 0, "total": 0, "passed": 0, "failed": 0}
        self.bl4_selection_refreshing = False
        self.auto_inventory_after_id = None
        self.auto_inventory_in_flight = False
        self.auto_inventory_last_log = 0.0
        self.auto_inventory_interval_ms = 2000
        self.movement_saved_preset = {}
        self.movement_auto_apply_saved = False
        self.movement_status_message = 'Movement ready.'
        self.serial_delivery_last_message = ''
        super().__init__()
        self.title("Matt's SDK Boosting Tools - External V22 Parts Codes GZO Visible")
        self._load_movement_settings_local()
        try:
            icon_path = RESOURCE_DIR / "app_icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass

    def _truthy(self, value):
        return str(value).strip().lower() in ('1','true','yes','on')

    def _serial_delivery_progress_message(self, progress):
        if not isinstance(progress, dict):
            return ''
        msg = str(progress.get('message') or progress.get('last_message') or '').strip()
        err = str(progress.get('last_error') or '').strip()
        if err and not msg:
            msg = err
        return msg

    def _handle_serial_delivery_progress(self, progress):
        msg = self._serial_delivery_progress_message(progress)
        if not msg:
            return
        active = bool((progress or {}).get('active'))
        stage = str((progress or {}).get('stage') or '').lower()
        err = str((progress or {}).get('last_error') or '').strip()
        if msg == getattr(self, 'serial_delivery_last_message', ''):
            return
        self.serial_delivery_last_message = msg
        if active or stage in ('complete', 'failed') or err:
            self.log(f'SDK serial delivery: {msg}')

    def poll_status(self):
        def work():
            try:
                s = http_json('GET', '/status', timeout=3)
                selected = s.get('selected_player') or 'no selected player'
                text = f"Bridge online | selected: {selected} | players: {len(s.get('players') or [])} | queue: {s.get('queue',0)}"
                delivery = s.get('serial_delivery') or {}
                delivery_msg = self._serial_delivery_progress_message(delivery)
                if delivery_msg:
                    text += ' | serial: ' + delivery_msg
                if s.get('last_error'):
                    text += ' | last error: ' + str(s.get('last_error'))
                self.after(0, lambda t=text: self.status_var.set(t))
                self.after(0, lambda st=s: self._update_player_options(st))
                self.after(0, lambda d=delivery: self._handle_serial_delivery_progress(d))
            except Exception:
                self.after(0, lambda: self.status_var.set('Bridge offline - local UI/resources still loaded'))
        threading.Thread(target=work, daemon=True).start()
        self.after(3000, self.poll_status)

    def _auto_inventory_enabled(self):
        var = self.field_vars.get('auto_inventory_sizes')
        return self._truthy(var.get() if var else '')

    def _auto_inventory_payload(self, enabled=True):
        def as_int(fid, default):
            raw = self.field_vars.get(fid, tk.StringVar(value=str(default))).get()
            return int(str(raw).replace(',','').strip())
        return {
            'enabled': bool(enabled),
            'backpack_size': as_int('backpack_size', 999),
            'bank_size': as_int('bank_size', 1500),
        }

    def _auto_inventory_log(self, message, *, force=False):
        now = time.monotonic()
        if force or now - float(self.auto_inventory_last_log or 0.0) >= 30.0:
            self.auto_inventory_last_log = now
            self.log(message)

    def _field_changed(self, field):
        super()._field_changed(field)
        if field.get('id') == 'auto_inventory_sizes':
            self._auto_inventory_toggle_changed()

    def _auto_inventory_toggle_changed(self):
        if self._auto_inventory_enabled():
            self._auto_inventory_log('Auto inventory enabled.', force=True)
            self._schedule_auto_inventory_apply(250)
        else:
            self._cancel_auto_inventory_apply()
            self._send_auto_inventory_disabled()
            self._auto_inventory_log('Auto inventory disabled.', force=True)

    def _schedule_auto_inventory_apply(self, delay_ms=None):
        if not self._auto_inventory_enabled():
            return
        if self.auto_inventory_after_id is not None:
            try:
                self.after_cancel(self.auto_inventory_after_id)
            except Exception:
                pass
        delay = self.auto_inventory_interval_ms if delay_ms is None else int(delay_ms)
        self.auto_inventory_after_id = self.after(delay, self._auto_inventory_tick)

    def _cancel_auto_inventory_apply(self):
        if self.auto_inventory_after_id is not None:
            try:
                self.after_cancel(self.auto_inventory_after_id)
            except Exception:
                pass
        self.auto_inventory_after_id = None
        self.auto_inventory_in_flight = False

    def _send_auto_inventory_disabled(self):
        try:
            payload = self._auto_inventory_payload(enabled=False)
        except Exception:
            payload = {'enabled': False, 'backpack_size': 999, 'bank_size': 1500}
        def work():
            try:
                http_json('POST','/action',{'action':'auto_inventory_sizes','payload':payload,'timeout':10.0},timeout=8.0)
            except Exception:
                pass
        threading.Thread(target=work,daemon=True).start()

    def _auto_inventory_tick(self):
        self.auto_inventory_after_id = None
        if not self._auto_inventory_enabled():
            return
        if self.auto_inventory_in_flight:
            self._schedule_auto_inventory_apply()
            return
        try:
            payload = self._auto_inventory_payload(enabled=True)
        except Exception:
            self._auto_inventory_log('Automatic inventory sizing waiting for valid backpack/bank numbers.', force=True)
            self._schedule_auto_inventory_apply()
            return
        self.auto_inventory_in_flight = True
        def done(message, applied=0):
            self.auto_inventory_in_flight = False
            if not self._auto_inventory_enabled():
                return
            if applied:
                self._auto_inventory_log(message or 'Auto-applied inventory sizes to party.', force=True)
            else:
                self._auto_inventory_log(message or 'Automatic inventory sizing checked; waiting for players.')
            self._schedule_auto_inventory_apply()
        def failed(exc):
            self.auto_inventory_in_flight = False
            if not self._auto_inventory_enabled():
                return
            self._auto_inventory_log('Bridge offline / waiting for players for automatic inventory sizing.')
            self._schedule_auto_inventory_apply()
        def work():
            try:
                res = http_json('POST','/action',{'action':'auto_inventory_sizes','payload':payload,'timeout':10.0},timeout=12.0)
                self.after(0, lambda r=res: done(r.get('message') or '', int(r.get('applied') or 0)))
            except Exception as exc:
                self.after(0, lambda e=exc: failed(e))
        threading.Thread(target=work,daemon=True).start()

    def _movement_settings_file(self):
        return RESOURCE_DIR / 'user_movement_preset.json'

    def _load_movement_settings_local(self):
        self.movement_saved_preset = {}
        self.movement_auto_apply_saved = False
        try:
            path = self._movement_settings_file()
            if not path.exists():
                return
            data = json.loads(path.read_text(encoding='utf-8') or '{}')
            preset = data.get('preset') if isinstance(data, dict) else {}
            if isinstance(preset, dict):
                self.movement_saved_preset = {str(k): str(v) for k, v in preset.items() if str(k) in MOVEMENT_DEFAULTS}
            self.movement_auto_apply_saved = self._truthy(data.get('auto_apply_on_load', False)) if isinstance(data, dict) else False
        except Exception:
            self.movement_saved_preset = {}
            self.movement_auto_apply_saved = False

    def _save_movement_settings_local(self):
        data = {
            'preset': dict(getattr(self, 'movement_saved_preset', {}) or {}),
            'auto_apply_on_load': bool(getattr(self, 'movement_auto_apply_saved', False)),
        }
        self._movement_settings_file().write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')

    def _movement_set_status(self, message, *, log_global=True):
        self.movement_status_message = str(message or '')
        if 'movement_status' in self.field_vars:
            self.field_vars['movement_status'].set(self.movement_status_message)
        if log_global:
            self.log(self.movement_status_message)

    def _movement_set_field_value(self, fid, value):
        if fid not in self.field_vars:
            self.field_vars[fid] = tk.StringVar(value=str(value))
        self.field_vars[fid].set(str(value))
        w = self.widgets.get(fid)
        try:
            if isinstance(w, tk.Text):
                w.delete('1.0', 'end')
                w.insert('1.0', str(value))
        except Exception:
            pass

    def _movement_apply_values_to_fields(self, values):
        for fid, value in (values or {}).items():
            if fid in MOVEMENT_DEFAULTS:
                self._movement_set_field_value(fid, value)

    def _movement_current_field_values(self):
        out = {}
        for fid, default in MOVEMENT_DEFAULTS.items():
            var = self.field_vars.get(fid)
            out[fid] = str(var.get() if var else default)
        return out

    def _movement_parse_float(self, fid, label, default=None, minimum=None, maximum=None):
        raw = self.field_vars.get(fid, tk.StringVar(value='' if default is None else str(default))).get()
        text = str(raw).replace(',', '').replace('x', '').replace('X', '').strip()
        if text == '' and default is not None:
            value = float(default)
        else:
            value = float(text)
        if minimum is not None:
            value = max(float(minimum), value)
        if maximum is not None:
            value = min(float(maximum), value)
        return value

    def _movement_parse_int(self, fid, label, default=None, minimum=None, maximum=None):
        value = int(round(self._movement_parse_float(fid, label, default, minimum, maximum)))
        if minimum is not None:
            value = max(int(minimum), value)
        if maximum is not None:
            value = min(int(maximum), value)
        return value

    def _movement_payload(self):
        try:
            jump_goal = self._movement_parse_float('movement_jump_height', 'Master JumpGoal Height', 198, 0, 10000)
            individual = self._truthy(self.field_vars.get('movement_individual_jump_goals', tk.StringVar(value='false')).get())
            return {
                'movement_speed_scale': self._movement_parse_float('movement_speed_scale', 'Speed Scale', 1.0, 0.05, 25.0),
                'movement_walk_speed': self._movement_parse_float('movement_walk_speed', 'Walk / Ground Speed', 600, 50, 10000),
                'movement_jump_height': jump_goal,
                'movement_jump_velocity': self._movement_parse_float('movement_jump_velocity', 'JumpZ Velocity', jump_goal, 0, 10000),
                'movement_sprint_jump_goal': self._movement_parse_float('movement_sprint_jump_goal', 'SprintJump GoalHeight', jump_goal, 0, 20000) if individual else jump_goal,
                'movement_double_jump_goal': self._movement_parse_float('movement_double_jump_goal', 'DoubleJump GoalHeight', jump_goal, 0, 20000) if individual else jump_goal,
                'movement_slide_jump_goal': self._movement_parse_float('movement_slide_jump_goal', 'SlideJump GoalHeight', jump_goal, 0, 20000) if individual else jump_goal,
                'movement_individual_jump_goals': 'true' if individual else 'false',
                'movement_gravity_scale': self._movement_parse_float('movement_gravity_scale', 'Gravity Scale', 1.0, 0, 10),
                'movement_step_height': self._movement_parse_float('movement_step_height', 'Max Step Height', 45, 0, 1000),
                'movement_jump_count': self._movement_parse_int('movement_jump_count', 'Jump Count', 2, 1, 50),
                'movement_jump_off_z_factor': self._movement_parse_float('movement_jump_off_z_factor', 'Jump Off Z Factor', 0.5, 0, 80),
                'movement_floor_angle': self._movement_parse_float('movement_floor_angle', 'Walkable Floor Angle', 44.76508331298828, 0, 89.9),
                'movement_floor_z': self._movement_parse_float('movement_floor_z', 'Walkable Floor Z', 0.7099999785423279, 0, 1),
                'movement_glide_speed': self._movement_parse_float('movement_glide_speed', 'Gliding Speed', 1200, 0, 30000),
                'movement_glide_boost': self._movement_parse_float('movement_glide_boost', 'Gliding Speed Boost', 0, 0, 30000),
                'movement_glide_air_control': self._movement_parse_float('movement_glide_air_control', 'Gliding Air Control', 0.6, 0, 50),
                'movement_dash_speed': self._movement_parse_float('movement_dash_speed', 'Dash Speed', 2500, 0, 30000),
                'movement_zero_vault_on_apply': self.field_vars.get('movement_zero_vault_on_apply', tk.StringVar(value='false')).get(),
            }
        except Exception as exc:
            raise ValueError(f'Movement value must be numeric: {exc}')

    def _movement_bridge_action(self, action_id, payload=None, *, success_status=None):
        payload = dict(payload or {})
        self._movement_set_status(f'Sending {action_id}...', log_global=False)
        def work():
            try:
                res = http_json('POST', '/action', {'action':action_id, 'payload':payload, 'timeout':10.0}, timeout=18.0)
                msg = res.get('message') or success_status or f'{action_id} requested.'
                self.after(0, lambda m=msg:self._movement_set_status(m))
                self.after(0, self.poll_status)
            except Exception as exc:
                self.after(0, lambda e=exc:self._movement_set_status(f'Movement action failed: {e!r}'))
        threading.Thread(target=work, daemon=True).start()

    def _movement_apply_now(self):
        try:
            payload = self._movement_payload()
        except ValueError as exc:
            self._movement_set_status(str(exc))
            return messagebox.showerror('Invalid movement value', str(exc))
        self._movement_bridge_action('movement_apply_all', payload, success_status='Apply movement settings requested.')

    def _movement_reset_defaults(self, *, apply_now=True):
        self._movement_apply_values_to_fields(MOVEMENT_DEFAULTS)
        self._movement_set_status('Movement fields reset to defaults.' + (' Applying defaults...' if apply_now else ''))
        if apply_now:
            self._movement_bridge_action('movement_reset_all', {}, success_status='Reset movement settings requested.')

    def _movement_apply_preset_local(self, name):
        key = str(name or '').strip().lower()
        if key not in MOVEMENT_PRESETS:
            return self._movement_set_status(f'Unknown movement preset: {name}')
        values = dict(MOVEMENT_PRESETS[key])
        if key in ('wallwalk', 'fastglide'):
            try:
                cur_speed = self._movement_parse_float('movement_speed_scale', 'Speed Scale', 1.0)
                cur_walk = self._movement_parse_float('movement_walk_speed', 'Walk / Ground Speed', 600)
                values['movement_speed_scale'] = f'{max(cur_speed, float(values.get("movement_speed_scale", 1.0))):.2f}'
                values['movement_walk_speed'] = str(int(max(cur_walk, float(values.get('movement_walk_speed', 600)))))
            except Exception:
                pass
        if key == 'moon':
            for fid in ('movement_speed_scale', 'movement_walk_speed', 'movement_glide_speed', 'movement_glide_boost', 'movement_glide_air_control', 'movement_dash_speed'):
                if fid in self.field_vars and fid not in values:
                    values[fid] = self.field_vars[fid].get()
        self._movement_apply_values_to_fields(values)
        self._movement_set_status(f'Applied {key} preset to fields. Sending to bridge...')
        self._movement_apply_now()

    def _movement_save_preset_local(self):
        self.movement_saved_preset = self._movement_current_field_values()
        self.movement_auto_apply_saved = self._truthy(self.field_vars.get('movement_auto_apply_on_load', tk.StringVar(value='false')).get())
        try:
            self._save_movement_settings_local()
            self._movement_set_status('Saved current movement values as the movement preset.')
        except Exception as exc:
            self._movement_set_status(f'Movement preset save failed: {exc!r}')

    def _movement_load_saved_preset_local(self, *, apply_now=True):
        if not getattr(self, 'movement_saved_preset', None):
            self._load_movement_settings_local()
        if not getattr(self, 'movement_saved_preset', None):
            return self._movement_set_status('No movement preset saved yet.')
        self._movement_apply_values_to_fields(self.movement_saved_preset)
        self._movement_set_status('Loaded saved movement preset into the UI.' + (' Applying now...' if apply_now else ''))
        if apply_now:
            self._movement_apply_now()

    def _movement_auto_apply_toggle_changed(self):
        self.movement_auto_apply_saved = self._truthy(self.field_vars.get('movement_auto_apply_on_load', tk.StringVar(value='false')).get())
        try:
            self._save_movement_settings_local()
        except Exception:
            pass
        if self.movement_auto_apply_saved:
            self._movement_set_status('Auto apply saved preset on game load enabled. It will not run from the external app startup; use Load Saved to apply now.')
        else:
            self._movement_set_status('Auto apply saved preset on game load disabled.')

    def _movement_apply_fields(self):
        return [
            'movement_speed_scale',
            'movement_walk_speed',
            'movement_jump_height',
            'movement_jump_velocity',
            'movement_sprint_jump_goal',
            'movement_double_jump_goal',
            'movement_slide_jump_goal',
            'movement_individual_jump_goals',
            'movement_gravity_scale',
            'movement_jump_count',
            'movement_jump_off_z_factor',
            'movement_step_height',
            'movement_floor_angle',
            'movement_floor_z',
            'movement_glide_speed',
            'movement_glide_boost',
            'movement_glide_air_control',
            'movement_dash_speed',
            'movement_zero_vault_on_apply',
        ]

    def _tab_movement(self, body, cards):
        # Closer copy of Matt's Player Movement tab, including Infinite Jump controls.
        self._movement_presets_card(body).pack(fill='x',padx=6,pady=4)
        grid=tk.Frame(body,bg='#090d17'); grid.pack(fill='both',expand=True,padx=6,pady=0)
        for c in range(3): grid.grid_columnconfigure(c,weight=1,uniform='move')
        self._movement_speed_card(grid).grid(row=0,column=0,sticky='nsew',padx=(0,4),pady=4)
        self._movement_jump_card(grid).grid(row=0,column=1,sticky='nsew',padx=4,pady=4)
        self._movement_infinite_jump_card(grid).grid(row=0,column=2,sticky='nsew',padx=(4,0),pady=4)
        self._movement_wall_card(grid).grid(row=1,column=0,sticky='nsew',padx=(0,4),pady=4)
        self._movement_glide_card(grid).grid(row=1,column=1,sticky='nsew',padx=4,pady=4)
        self._movement_utility_card(grid).grid(row=1,column=2,sticky='nsew',padx=(4,0),pady=4)
        self._movement_teleport_card(grid).grid(row=2,column=2,sticky='nsew',padx=(4,0),pady=4)
        for r in range(3): grid.grid_rowconfigure(r,weight=1)

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

    def _checkbox_row_simple(self, parent, label, fid, default='false', command=None, width=24):
        row=tk.Frame(parent,bg='#090d17'); row.pack(fill='x',padx=8,pady=2)
        var=self.field_vars.get(fid) or tk.StringVar(value='true' if self._truthy(default) else 'false'); self.field_vars[fid]=var
        chk=tk.Checkbutton(row,text=label,variable=var,onvalue='true',offvalue='false',command=command,bg='#090d17',activebackground='#090d17',fg='#cfd8f3',activeforeground='#f1f5ff',selectcolor='#211b1f',relief='flat',font=('Segoe UI',8),anchor='w')
        chk.pack(side='left',fill='x',expand=True); self.widgets[fid]=chk
        return chk

    def _movement_button(self, parent, label, command, accent='cyan', index=0, cols=3):
        color=ACCENT_COLORS.get(accent,'#00d4ff')
        b=tk.Button(parent,text=label,command=command,bg='#172033',activebackground='#22304c',fg=color,activeforeground=color,relief='flat',padx=8,pady=5,font=('Segoe UI',8,'bold'))
        b.grid(row=index//cols,column=index%cols,padx=3,pady=3,sticky='ew')
        for c in range(cols): parent.grid_columnconfigure(c,weight=1,uniform='btn')
        return b

    def _movement_presets_card(self, parent):
        wrap, inner = self._make_card(parent,'Presets / Save / Apply','#00aa55')
        tk.Label(inner,text='UI-only controls. Button actions apply live movement through the SDK bridge; normal field edits do not auto-run.',bg='#090d17',fg='#9fb3d9',font=('Segoe UI',8),anchor='w',wraplength=1200).pack(fill='x',padx=8,pady=(5,2))
        row=tk.Frame(inner,bg='#090d17'); row.pack(fill='x',padx=6,pady=(4,2))
        buttons=[
            ('Apply Now', self._movement_apply_now, 'green'),
            ('Save Preset', self._movement_save_preset_local, 'cyan'),
            ('Load Saved', lambda:self._movement_load_saved_preset_local(apply_now=True), 'purple'),
            ('Reset Defaults', lambda:self._movement_reset_defaults(apply_now=True), 'gold'),
            ('Fast', lambda:self._movement_apply_preset_local('fast'), 'cyan'),
            ('Very Fast', lambda:self._movement_apply_preset_local('veryfast'), 'purple'),
            ('Moon', lambda:self._movement_apply_preset_local('moon'), 'gold'),
            ('Wall Walk', lambda:self._movement_apply_preset_local('wallwalk'), 'green'),
            ('Fast Glide', lambda:self._movement_apply_preset_local('fastglide'), 'cyan'),
        ]
        for i,(label,cmd,accent) in enumerate(buttons):
            self._movement_button(row,label,cmd,accent,i,cols=5)
        self._checkbox_row_simple(inner,'Auto apply saved preset on game load','movement_auto_apply_on_load','true' if getattr(self,'movement_auto_apply_saved',False) else 'false',command=self._movement_auto_apply_toggle_changed)
        self.field_vars['movement_status']=self.field_vars.get('movement_status') or tk.StringVar(value=getattr(self,'movement_status_message','Movement ready.'))
        tk.Label(inner,textvariable=self.field_vars['movement_status'],bg='#090d17',fg='#9fb3d9',font=('Segoe UI',8),anchor='w',justify='left',wraplength=1200).pack(fill='x',padx=8,pady=(2,6))
        return wrap

    def _movement_speed_card(self, parent):
        wrap, inner = self._make_card(parent,'Speed','#00a3d7')
        self._field_row_simple(inner,'Speed Scale','movement_speed_scale',MOVEMENT_DEFAULTS['movement_speed_scale'])
        self._field_row_simple(inner,'Walk / Ground Speed','movement_walk_speed',MOVEMENT_DEFAULTS['movement_walk_speed'])
        tk.Label(inner,text='Writes speed scale and walk speed fields.',bg='#090d17',fg='#8c99b5',font=('Segoe UI',8),anchor='w',wraplength=360).pack(fill='x',padx=8,pady=(2,3))
        bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(4,6))
        self._movement_button(bf,'Apply Movement Settings',self._movement_apply_now,'cyan',0,cols=1)
        return wrap

    def _movement_jump_card(self, parent):
        wrap, inner = self._make_card(parent,'Jump / Gravity','#8a2be2')
        self._field_row_simple(inner,'Master JumpGoal Height','movement_jump_height',MOVEMENT_DEFAULTS['movement_jump_height'])
        self._checkbox_row_simple(inner,'Set individual jump goals','movement_individual_jump_goals',MOVEMENT_DEFAULTS['movement_individual_jump_goals'])
        self._field_row_simple(inner,'SprintJump GoalHeight','movement_sprint_jump_goal',MOVEMENT_DEFAULTS['movement_sprint_jump_goal'])
        self._field_row_simple(inner,'DoubleJump GoalHeight','movement_double_jump_goal',MOVEMENT_DEFAULTS['movement_double_jump_goal'])
        self._field_row_simple(inner,'SlideJump GoalHeight','movement_slide_jump_goal',MOVEMENT_DEFAULTS['movement_slide_jump_goal'])
        self._field_row_simple(inner,'JumpZ Velocity','movement_jump_velocity',MOVEMENT_DEFAULTS['movement_jump_velocity'])
        self._field_row_simple(inner,'Gravity Scale','movement_gravity_scale',MOVEMENT_DEFAULTS['movement_gravity_scale'])
        self._field_row_simple(inner,'Jump Count','movement_jump_count',MOVEMENT_DEFAULTS['movement_jump_count'])
        self._field_row_simple(inner,'Jump Off Z Factor','movement_jump_off_z_factor',MOVEMENT_DEFAULTS['movement_jump_off_z_factor'])
        bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(4,6))
        self._movement_button(bf,'Apply Movement Settings',self._movement_apply_now,'cyan',0,cols=2)
        self._movement_button(bf,'Reset Defaults',lambda:self._movement_reset_defaults(apply_now=True),'gold',1,cols=2)
        return wrap

    def _movement_wall_card(self,parent):
        wrap, inner = self._make_card(parent,'Wall / Step','#d28b00')
        self._field_row_simple(inner,'Max Step Height','movement_step_height',MOVEMENT_DEFAULTS['movement_step_height'])
        self._field_row_simple(inner,'Walkable Floor Angle','movement_floor_angle',MOVEMENT_DEFAULTS['movement_floor_angle'])
        self._field_row_simple(inner,'Walkable Floor Z','movement_floor_z',MOVEMENT_DEFAULTS['movement_floor_z'])
        tk.Label(inner,text='Wall Walk preset uses 89.9 angle and FloorZ near 0.0.',bg='#090d17',fg='#8c99b5',font=('Segoe UI',8),anchor='w',wraplength=360).pack(fill='x',padx=8,pady=(2,3))
        bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(4,6))
        self._movement_button(bf,'Apply Wall / Step',self._movement_apply_now,'cyan',0,cols=1)
        return wrap

    def _movement_glide_card(self,parent):
        wrap, inner = self._make_card(parent,'Glide / Dash / Vault','#0075c9')
        self._field_row_simple(inner,'Gliding Speed','movement_glide_speed',MOVEMENT_DEFAULTS['movement_glide_speed'])
        self._field_row_simple(inner,'Gliding Speed Boost','movement_glide_boost',MOVEMENT_DEFAULTS['movement_glide_boost'])
        self._field_row_simple(inner,'Gliding Air Control','movement_glide_air_control',MOVEMENT_DEFAULTS['movement_glide_air_control'])
        self._field_row_simple(inner,'Dash Speed','movement_dash_speed',MOVEMENT_DEFAULTS['movement_dash_speed'])
        self._checkbox_row_simple(inner,'Set vault power costs to 0 on apply','movement_zero_vault_on_apply',MOVEMENT_DEFAULTS['movement_zero_vault_on_apply'])
        bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(4,6))
        self._movement_button(bf,'Zero Vault Cooldown',lambda:self._movement_bridge_action('movement_zero_vault'),'cyan',0,cols=2)
        self._movement_button(bf,'Apply Glide / Dash',self._movement_apply_now,'cyan',1,cols=2)
        return wrap

    def _movement_utility_card(self,parent):
        wrap, inner = self._make_card(parent,'World / Utility','#8a2be2')
        self._field_row_simple(inner,'Time Dilation','movement_time_dilation',MOVEMENT_DEFAULTS['movement_time_dilation'])
        bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(4,6))
        self._movement_button(bf,'Set Time',self._movement_set_time_local,'gold',0,cols=3)
        self._movement_button(bf,'Reset Time',self._movement_reset_time_local,'purple',1,cols=3)
        self._movement_button(bf,'Players Only',lambda:self._movement_bridge_action('movement_players_only'),'purple',2,cols=3)
        self._movement_button(bf,'No Target',lambda:self._movement_bridge_action('movement_toggle_no_target'),'cyan',3,cols=3)
        self._movement_button(bf,'Delete Ground Items',lambda:self._movement_bridge_action('movement_delete_ground_items'),'red',4,cols=3)
        self._movement_button(bf,'Noclip',lambda:self._movement_bridge_action('movement_toggle_noclip'),'gold',5,cols=3)
        tk.Label(inner,text='No Target and Noclip are live toggles and are not cached between launches.',bg='#090d17',fg='#8c99b5',font=('Segoe UI',8),anchor='w',wraplength=360).pack(fill='x',padx=8,pady=(2,6))
        return wrap

    def _movement_infinite_jump_card(self,parent):
        wrap, inner = self._make_card(parent,'Infinite Jump','#00b060')
        tk.Label(inner,text='Enable per player. Use All ON for multi-jump on every current party player.',bg='#090d17',fg='#9fb3d9',font=('Segoe UI',8),anchor='w',wraplength=500).pack(fill='x',padx=8,pady=(5,2))
        bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(4,3))
        self._movement_button(bf,'All ON',lambda:self._movement_bridge_action('movement_infinite_jump_all_on'),'green',0,cols=2)
        self._movement_button(bf,'All OFF',lambda:self._movement_bridge_action('movement_infinite_jump_all_off'),'red',1,cols=2)
        row=tk.Frame(inner,bg='#090d17'); row.pack(fill='x',padx=8,pady=4)
        tk.Label(row,text='Player',bg='#090d17',fg='#cfd8f3',width=12,anchor='w',font=('Segoe UI',8)).pack(side='left')
        var=self.field_vars.get('infinite_jump_target') or tk.StringVar(value=''); self.field_vars['infinite_jump_target']=var
        cb=ttk.Combobox(row,textvariable=var,values=self.player_options,state='readonly'); cb.pack(side='left',fill='x',expand=True); self.widgets['infinite_jump_target']=cb
        bf2=tk.Frame(inner,bg='#090d17'); bf2.pack(fill='x',padx=6,pady=(2,6))
        self._movement_button(bf2,'Selected ON',lambda:self._movement_infinite_jump_selected(True),'green',0,cols=3)
        self._movement_button(bf2,'Selected OFF',lambda:self._movement_infinite_jump_selected(False),'red',1,cols=3)
        self._movement_button(bf2,'Toggle Selected',lambda:self._movement_infinite_jump_selected(None),'cyan',2,cols=3)
        return wrap

    def _movement_teleport_card(self,parent):
        wrap, inner = self._make_card(parent,'Teleport Selected Player','#00a3d7')
        tk.Label(inner,text='Teleports the selected target player to the selected party slot pawn.',bg='#090d17',fg='#9fb3d9',font=('Segoe UI',8),anchor='w',wraplength=500).pack(fill='x',padx=8,pady=(5,2))
        bf=tk.Frame(inner,bg='#090d17'); bf.pack(fill='x',padx=6,pady=(4,6))
        for i in range(4):
            self._movement_button(bf,f'To P{i+1}',lambda slot=i:self._movement_bridge_action('movement_teleport_to_slot', {'slot':slot}),'cyan',i,cols=4)
        return wrap

    def _movement_set_time_local(self):
        try:
            value = self._movement_parse_float('movement_time_dilation', 'Time Dilation', 1.0, 0.01, 64.0)
        except Exception as exc:
            self._movement_set_status(f'Time Dilation must be numeric: {exc}')
            return messagebox.showerror('Invalid movement value', f'Time Dilation must be numeric: {exc}')
        self._movement_set_field_value('movement_time_dilation', f'{value:.2f}')
        self._movement_bridge_action('movement_set_time', {'movement_time_dilation': value})

    def _movement_reset_time_local(self):
        self._movement_set_field_value('movement_time_dilation', MOVEMENT_DEFAULTS['movement_time_dilation'])
        self._movement_bridge_action('movement_reset_time')

    def _movement_infinite_jump_selected(self, enabled):
        raw = self.field_vars.get('infinite_jump_target', tk.StringVar()).get()
        if not str(raw or '').strip():
            return self._movement_set_status('No Infinite Jump player selected. Press Refresh/Status and choose a player.')
        if enabled is True:
            action = 'movement_infinite_jump_selected_on'
        elif enabled is False:
            action = 'movement_infinite_jump_selected_off'
        else:
            action = 'movement_infinite_jump_toggle_selected'
        self._movement_bridge_action(action, {'infinite_jump_target': raw})

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
                if fid == 'legit_unlock_modded':
                    w.bind('<<ComboboxSelected>>', lambda e:self._legit_unlock_changed())
            elif typ in ('legit_type','legit_manufacturer','legit_root'):
                fake=typ if fid!='legit_root_serial' else 'legit_root'
                vals=self._values_for_field({'id':fid,'type':fake}); w=ttk.Combobox(form,textvariable=var,values=vals,state='readonly')
                if vals and not var.get(): var.set(vals[0])
                w.bind('<<ComboboxSelected>>',lambda e,fid=fid:self._legit_filter_changed(fid))
            else:
                w=ttk.Entry(form,textvariable=var); w.bind('<KeyRelease>',lambda e,fid=fid:self._refresh_legit_root_and_slots(fid))
            w.grid(row=r,column=1,sticky='ew',pady=2); self.widgets[fid]=w
        form.grid_columnconfigure(1,weight=1)
        btns=tk.Frame(inner,bg='#090d17'); btns.pack(fill='x',padx=8,pady=(4,8))
        actions=[
            {'id':'legit_apply_max_passives','label':'Add All Max Passives','accent':'gold','uses_fields':['legit_root_serial','legit_selected_parts','legit_unlock_modded']},
            {'id':'local_legit_validate','label':'Validate','accent':'cyan'},
            {'id':'local_legit_build_base85','label':'Build Base85','accent':'gold'},
            {'id':'legit_give_selected','label':'Give Active to Selected','accent':'gold','uses_fields':['legit_root_serial','legit_selected_parts','legit_unlock_modded','legit_level','legit_signature']},
            {'id':'legit_give_all','label':'Give Active to All','accent':'purple','uses_fields':['legit_root_serial','legit_selected_parts','legit_unlock_modded','legit_level','legit_signature']},
            {'id':'legit_give_nonhost','label':'Give Active to Non-Host','accent':'cyan','uses_fields':['legit_root_serial','legit_selected_parts','legit_unlock_modded','legit_level','legit_signature']},
            {'id':'legit_clear_parts','label':'Clear Selected Parts','accent':'red'},
        ]
        for i,a in enumerate(actions): self._button(btns,a,i,cols=6)
        selected, sel_inner = self._card_wrap(body, 'Selected composition / active build', '#8a2be2')
        selected.pack(fill='x', padx=6, pady=5)
        self.field_vars['legit_selected_parts'] = self.field_vars.get('legit_selected_parts') or tk.StringVar(value='')
        txt=tk.Text(sel_inner,height=5,bg='#0e1320',fg='#d7def5',insertbackground='#f1f5ff',relief='flat',wrap='word',font=('Consolas',8))
        txt.pack(fill='x',padx=8,pady=8); txt.bind('<KeyRelease>',lambda e:self._legit_selected_text_changed()); self.widgets['legit_selected_parts']=txt
        self._legit_output_area(body)
        slot_wrap, slot_inner = self._card_wrap(body,'Slots / Available Parts','#6b7280')
        slot_wrap.pack(fill='both',expand=True,padx=6,pady=5)
        top=tk.Frame(slot_inner,bg='#090d17'); top.pack(fill='x',padx=8,pady=(5,2))
        tk.Label(top,text='Each panel is one Matt SDK slot/dependency. Add/Replace follows legit rules. Add x Qty preserves duplicates for modded/unlock builds.',bg='#090d17',fg='#9fb3d9',font=('Segoe UI',8)).pack(side='left')
        self.legit_slots_area=tk.Frame(slot_inner,bg='#090d17'); self.legit_slots_area.pack(fill='both',expand=True,padx=8,pady=6)
        self._refresh_combo('legit_manufacturer'); self._refresh_combo('legit_root_serial'); self._render_legit_slots()
        self.legit_last_root_value=self.field_vars.get('legit_root_serial', tk.StringVar()).get()

    def _clear_legit_selected_parts_for_root_change(self):
        self.legit_selected_by_slot.clear()
        self.legit_rejected_part_lines=[]
        self.field_vars['legit_selected_parts'].set('')
        txt=self.widgets.get('legit_selected_parts')
        if isinstance(txt, tk.Text):
            txt.delete('1.0','end')
        self._clear_legit_outputs()

    def _legit_unlock_changed(self):
        self._clear_legit_outputs()
        state = str(self.field_vars.get('legit_unlock_modded', tk.StringVar(value='false')).get() or '').lower()
        if state in ('1','true','yes','on'):
            self._set_legit_status('Unlock enabled: builder will ignore legit part rules and allow duplicate parts.', log_global=False)
        else:
            self._set_legit_status('Unlock disabled: builder is using legit part rules.', log_global=False)
        self._render_legit_slots()

    def _legit_filter_changed(self, fid):
        before=getattr(self, 'legit_last_root_value', '')
        if fid == 'legit_type':
            self._refresh_combo('legit_manufacturer')
            self._refresh_combo('legit_root_serial')
        elif fid == 'legit_manufacturer':
            self._refresh_combo('legit_root_serial')
        after=self.field_vars.get('legit_root_serial', tk.StringVar()).get()
        if fid in ('legit_type','legit_manufacturer','legit_root_serial') and after != before:
            self._clear_legit_selected_parts_for_root_change()
            self._set_legit_status('Root changed; selected parts and generated output cleared.', log_global=False)
        self.legit_last_root_value=after
        self._render_legit_slots()

    def _refresh_legit_root_and_slots(self, fid=None):
        if fid == 'legit_root_filter':
            before=getattr(self, 'legit_last_root_value', '')
            self._refresh_combo('legit_root_serial')
            after=self.field_vars.get('legit_root_serial', tk.StringVar()).get()
            if after != before:
                self._clear_legit_selected_parts_for_root_change()
                self._set_legit_status('Root filter changed root; selected parts and generated output cleared.', log_global=False)
            self.legit_last_root_value=after
        elif fid in ('legit_level','legit_signature'):
            self._clear_legit_outputs()
            self._set_legit_status('Level/signature changed; generated output cleared. Rebuild before giving.', log_global=False)
        self._render_legit_slots()

    def _legit_output_area(self, body):
        wrap, inner = self._card_wrap(body, 'Legit Builder Output', '#8a2be2')
        wrap.pack(fill='x', padx=6, pady=5)
        self.field_vars['legit_status'] = self.field_vars.get('legit_status') or tk.StringVar(value=self.legit_status_message)
        tk.Label(inner, textvariable=self.field_vars['legit_status'], bg='#090d17', fg='#21e05f', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1200).pack(fill='x', padx=8, pady=(5,4))
        self._legit_output_box(inner, 'Human Serial Output', 'legit_human_output', 'Copy Human', 'human serial', height=4)
        self._legit_output_box(inner, 'Base85 @U Output', 'legit_base85_output', 'Copy Base85', 'Base85 serial', height=3)
        self._external_player_target_row(inner, 'legit_target_player', 'Legit Builder Target')

    def _legit_output_box(self, parent, label, widget_id, button_text, copy_label, height=4):
        row=tk.Frame(parent,bg='#090d17'); row.pack(fill='x',padx=8,pady=(4,2))
        tk.Label(row,text=label,bg='#090d17',fg='#cfd8f3',font=('Segoe UI',8,'bold'),anchor='w').pack(side='left')
        tk.Button(row,text=button_text,command=lambda wid=widget_id, lab=copy_label:self._copy_text_v13(self._text_get(wid), lab) if self._text_get(wid).strip() else self.log(f'No {lab} to copy.'),bg='#172033',fg='#ffd447',relief='flat',font=('Segoe UI',8,'bold')).pack(side='right')
        txt=tk.Text(parent,height=height,bg='#181417',fg='#f1f5ff',insertbackground='#f1f5ff',relief='flat',wrap='word',font=('Consolas',8))
        txt.pack(fill='x',padx=8,pady=(0,6))
        self.widgets[widget_id]=txt

    def _text_get(self, widget_id):
        widget=self.widgets.get(widget_id)
        if isinstance(widget, tk.Text):
            return widget.get('1.0','end-1c')
        return ''

    def _text_set(self, widget_id, value):
        widget=self.widgets.get(widget_id)
        if isinstance(widget, tk.Text):
            widget.delete('1.0','end')
            widget.insert('1.0',str(value or ''))

    def _clear_legit_outputs(self):
        self.legit_human_output=''
        self.legit_base85_output=''
        self.legit_last_build_signature=''
        self._text_set('legit_human_output','')
        self._text_set('legit_base85_output','')

    def _legit_payload_values(self):
        self._sync_legit_selection_from_text()
        rejected=list(getattr(self, 'legit_rejected_part_lines', []) or [])
        if rejected:
            preview='; '.join(rejected[:4])
            more='' if len(rejected) <= 4 else f'; +{len(rejected)-4} more'
            raise ValueError(f'Malformed or unresolved selected part line(s): {preview}{more}')
        return {
            'root_serial': self.field_vars.get('legit_root_serial', tk.StringVar()).get(),
            'selected_parts': '\n'.join(self._legit_selected_lines_for_core()),
            'unlock_modded': self.field_vars.get('legit_unlock_modded', tk.StringVar(value='false')).get(),
            'level': self.field_vars.get('legit_level', tk.StringVar(value='60')).get(),
            'signature': self.field_vars.get('legit_signature', tk.StringVar(value='1')).get(),
        }

    def _legit_build_signature_from_values(self, values):
        payload={
            'root_serial': str((values or {}).get('root_serial') or '').strip(),
            'selected_parts': str((values or {}).get('selected_parts') or '').strip(),
            'unlock_modded': str((values or {}).get('unlock_modded') or '').strip().lower(),
            'level': str((values or {}).get('level') or '').strip(),
            'signature': str((values or {}).get('signature') or '').strip(),
        }
        return json.dumps(payload, sort_keys=True)

    def _legit_current_build_signature(self):
        values=self._legit_payload_values()
        return self._legit_build_signature_from_values(values)

    def _set_legit_status(self, message, log_global=True):
        self.legit_status_message=str(message or '')
        if 'legit_status' in self.field_vars:
            self.field_vars['legit_status'].set(self.legit_status_message)
        if log_global:
            self.log(self.legit_status_message)

    def _run_local_legit_validate(self):
        try:
            values=self._legit_payload_values()
            result=external_legit_builder.build_base85_external(values['root_serial'], values['selected_parts'], values['unlock_modded'], values['level'], values['signature'])
            self.legit_human_output=str(result.get('human') or '')
            self.legit_base85_output=str(result.get('base85') or '')
            self._text_set('legit_human_output', self.legit_human_output)
            self._text_set('legit_base85_output', self.legit_base85_output)
            self.legit_last_build_signature=self._legit_build_signature_from_values(values) if self.legit_base85_output else ''
            self._set_legit_status(result.get('status') or 'Validation complete.')
        except Exception as exc:
            self._clear_legit_outputs()
            self._set_legit_status(f'Legit validation failed: {exc}')

    def _run_local_legit_build_base85(self):
        try:
            values=self._legit_payload_values()
            result=external_legit_builder.build_base85_external(values['root_serial'], values['selected_parts'], values['unlock_modded'], values['level'], values['signature'])
            self.legit_human_output=str(result.get('human') or '')
            self.legit_base85_output=str(result.get('base85') or '')
            self._text_set('legit_human_output', self.legit_human_output)
            self._text_set('legit_base85_output', self.legit_base85_output)
            self.legit_last_build_signature=self._legit_build_signature_from_values(values) if self.legit_base85_output else ''
            self._set_legit_status(result.get('status') or 'Build complete.')
        except Exception as exc:
            self._clear_legit_outputs()
            self._set_legit_status(f'Legit build failed: {exc}')

    def _legit_current_base85(self):
        text = self._text_get('legit_base85_output').strip()
        serial = text or str(getattr(self, 'legit_base85_output', '') or '').strip()
        if not serial:
            return ''
        try:
            if self._legit_current_build_signature() != getattr(self, 'legit_last_build_signature', ''):
                return ''
        except Exception:
            return ''
        return serial

    def _ensure_legit_base85(self):
        return self._legit_current_base85()

    def _deliver_legit_build(self, mode):
        serial = self._ensure_legit_base85()
        if not serial:
            self._set_legit_status('No current Base85 serial to give. Build Base85 after the latest root/part/level change, then try again.')
            return
        try:
            level = int(str(self.field_vars.get('legit_level', tk.StringVar(value='60')).get()).replace(',','').strip())
        except Exception:
            return messagebox.showerror('Invalid value', 'Legit Builder Level must be a number.')
        aid = {'selected':'give_serial_selected','all':'give_serial_all','nonhost':'give_serial_nonhost'}[mode]
        payload = {'serial_text': serial, 'serial_override_level': False, 'serial_level': level}
        self.log(f'Delivering Legit Builder serial to {mode}...')
        def work():
            try:
                if mode == 'selected':
                    ok, msg = self._set_bridge_target_from_field('legit_target_player', 'Legit Builder Target')
                    if not ok:
                        self.after(0, lambda m=msg:self._set_legit_status(m))
                        return
                res=http_json('POST','/action',{'action':aid,'payload':payload,'timeout':10.0},timeout=18.0)
                self.after(0, lambda:self._set_legit_status(res.get('message') or 'Legit Builder delivery requested.'))
                self.after(0, self.poll_status)
            except Exception as exc:
                self.after(0, lambda:self._set_legit_status('Legit Builder delivery failed: '+repr(exc)))
        threading.Thread(target=work, daemon=True).start()

    def _slot_line_from_part(self,p):
        table=str(p.get('table') or '').strip(); key=str(p.get('key') or '').strip()
        return f'{table}:{key}' if table and key else ''

    def _slot_selection_changed(self, slot, lb, force=False, append=False, qty=1):
        self._sync_legit_selection_from_text()
        rows=self.legit_slot_parts.get(lb,[]); picks=[]
        for i in lb.curselection():
            try:
                _slot,label,p=rows[i]; line=self._slot_line_from_part(p)
                if line: picks.extend([line]*max(1,int(qty or 1)))
            except Exception: pass
        if not picks and not force: return
        unlock = str(self.field_vars.get('legit_unlock_modded', tk.StringVar(value='false')).get() or '').lower() in ('1','true','yes','on')
        if append and unlock:
            self.legit_selected_by_slot.setdefault(slot,[]).extend(picks)
        elif append:
            current = list(self.legit_selected_by_slot.get(slot, []))
            for line in picks:
                selected_for_test = self._legit_selected_lines_for_core(exclude_slot=slot) + current
                ok, _reason = self._legit_is_part_line_allowed(selected_for_test, line)
                if ok and line not in current:
                    current.append(line)
            self.legit_selected_by_slot[slot] = current
        else:
            if not unlock:
                try:
                    root=self._legit_current_root()
                    root_key=str(root.get('key') or '') if root else ''
                    meta={str(x.get('slot') or '').lower():x for x in external_legit_builder.slot_counts(root_key,self._legit_selected_lines_for_core(exclude_slot=slot))}
                    max_count=meta.get(str(slot).lower(),{}).get('max')
                    if max_count is not None:
                        picks=picks[:max(0,int(max_count))]
                    accepted=[]
                    base=self._legit_selected_lines_for_core(exclude_slot=slot)
                    for line in picks:
                        ok, _reason = self._legit_is_part_line_allowed(base + accepted, line)
                        if ok and line not in accepted:
                            accepted.append(line)
                    picks=accepted
                except Exception:
                    pass
            self.legit_selected_by_slot[slot]=picks
        self._sync_legit_selected_text()
        self._clear_legit_outputs()
        self._set_legit_status(f'Updated selected parts: {len(self._legit_selected_lines_for_core())} selected.', log_global=False)
        self._render_legit_slots()

    def _clear_slot(self, slot):
        self._sync_legit_selection_from_text()
        self.legit_selected_by_slot.pop(slot, None)
        self._sync_legit_selected_text()
        self._clear_legit_outputs()
        self._set_legit_status(f'Cleared {slot} selected part(s). Generated output cleared.', log_global=False)
        self._render_legit_slots()

    def _legit_is_part_line_allowed(self, selected_for_test, line):
        root = self._legit_current_root()
        if not root:
            return False, 'No root selected.'
        root_key = str(root.get('key') or '').strip()
        table, key = self._split_legit_part_line(line)
        if not table or not key:
            return False, 'Malformed part line.'
        try:
            return external_legit_builder.is_part_allowed(root_key, selected_for_test, key, table=table)
        except Exception as exc:
            return False, repr(exc)

    def _render_legit_slots(self):
        if not hasattr(self,'legit_slots_area'): return
        scroll_pos = None
        canvas = getattr(self, 'canvas', None)
        try:
            scroll_pos = canvas.yview()[0] if isinstance(canvas, tk.Canvas) else None
        except Exception:
            scroll_pos = None
        for child in self.legit_slots_area.winfo_children(): child.destroy()
        self._sync_legit_selection_from_text()
        self.legit_slot_parts.clear(); root=self._legit_current_root()
        if not root:
            tk.Label(self.legit_slots_area,text='Pick a root variant to load its slot cards.',bg='#090d17',fg='#9fb3d9',font=('Segoe UI',9)).pack(anchor='w',padx=8,pady=8); return
        root_key=str(root.get('key') or '').strip()
        filter_text=(self.field_vars.get('legit_part_filter',tk.StringVar()).get() or '').strip()
        unlock = str(self.field_vars.get('legit_unlock_modded', tk.StringVar(value='false')).get() or '').lower() in ('1','true','yes','on')
        try:
            deps=list(external_legit_builder.slots(root_key))
        except Exception:
            deps=list(root.get('deps') or [])
        slot_meta={}
        try:
            slot_meta={str(x.get('slot') or '').lower():x for x in external_legit_builder.slot_counts(root_key,self._legit_selected_lines_for_core())}
        except Exception:
            slot_meta={}
        grouped={d:[] for d in deps}
        for slot in deps:
            try:
                meta=slot_meta.get(str(slot).lower(),{})
                selected_for_test=self._legit_selected_lines_for_core(exclude_slot=slot) if (not unlock and meta.get('max') is not None and int(meta.get('max') or 0)==1) else self._legit_selected_lines_for_core()
            except Exception:
                selected_for_test=self._legit_selected_lines_for_core()
            try:
                candidates=external_legit_builder.search_parts(root_key,filter_text,table=slot,limit=1000)
            except Exception:
                candidates=[]
            for p in candidates:
                if not unlock:
                    try:
                        ok,_reason=external_legit_builder.is_part_allowed(root_key,selected_for_test,p.get('key'),table=p.get('table'))
                    except Exception:
                        ok=False
                    if not ok:
                        continue
                label=self._part_label(p)
                grouped.setdefault(slot,[]).append((label,p))
        cols=3
        for idx,slot in enumerate([d for d in deps if grouped.get(d) or self.legit_selected_by_slot.get(d)] + [d for d in grouped if d not in deps and grouped.get(d)]):
            r,c=divmod(idx,cols); wrap,inner=self._card_wrap(self.legit_slots_area,slot,'#333a48'); wrap.grid(row=r,column=c,sticky='nsew',padx=4,pady=4)
            self.legit_slots_area.grid_columnconfigure(c,weight=1,uniform='slot'); self.legit_slots_area.grid_rowconfigure(r,weight=1)
            meta=slot_meta.get(str(slot).lower(),{})
            mn='?' if meta.get('min') is None else str(meta.get('min'))
            mx='?' if meta.get('max') is None else str(meta.get('max'))
            current=len(self.legit_selected_by_slot.get(slot,[])); tk.Label(inner,text=f'{len(grouped.get(slot,[]))} available part(s) | selected {current} | min {mn} | max {mx}',bg='#090d17',fg='#8c99b5',font=('Segoe UI',8),anchor='w').pack(fill='x',padx=6,pady=(3,0))
            lb=tk.Listbox(inner,height=7,selectmode='extended',bg='#0e1320',fg='#d7def5',selectbackground='#1f3b63',relief='flat',font=('Consolas',8),exportselection=False)
            lb.pack(fill='both',expand=True,padx=6,pady=4); self.legit_slot_parts[lb]=[(slot,label,p) for label,p in grouped[slot]]
            for label,p in grouped[slot]: lb.insert('end',label)
            controls=tk.Frame(inner,bg='#090d17'); controls.pack(fill='x',padx=6,pady=(0,5))
            tk.Button(controls,text='Add / Replace Slot',command=lambda slot=slot,lb=lb:self._slot_selection_changed(slot,lb,force=True,append=False,qty=1),bg='#172033',fg='#00d4ff',relief='flat',font=('Segoe UI',8,'bold')).grid(row=0,column=0,sticky='ew',padx=2,pady=2)
            tk.Button(controls,text='Add x Qty',command=lambda slot=slot,lb=lb:self._slot_selection_changed(slot,lb,force=True,append=True,qty=self.field_vars.get('legit_duplicate_qty',tk.StringVar(value='1')).get()),bg='#172033',fg='#ffd447',relief='flat',font=('Segoe UI',8,'bold')).grid(row=0,column=1,sticky='ew',padx=2,pady=2)
            tk.Button(controls,text='Clear Slot',command=lambda slot=slot:self._clear_slot(slot),bg='#172033',fg='#ff5b5b',relief='flat',font=('Segoe UI',8,'bold')).grid(row=0,column=2,sticky='ew',padx=2,pady=2)
            for cc in range(3): controls.grid_columnconfigure(cc,weight=1)
        if scroll_pos is not None and isinstance(canvas, tk.Canvas):
            self.after_idle(lambda pos=scroll_pos, canv=canvas: canv.yview_moveto(pos))



    def _legit_selected_lines_without_root(self):
        raw = self.field_vars.get('legit_selected_parts', tk.StringVar(value='')).get() or ''
        return [line.strip() for line in raw.splitlines() if line.strip() and not line.strip().lower().startswith('root:')]

    def _split_legit_part_line(self, line):
        text=str(line or '').strip()
        if not text or text.lower().startswith('root:') or ':' not in text:
            return '', ''
        table,key=text.split(':',1)
        return table.strip(), key.strip()

    def _normalize_legit_part_line(self, line):
        text=str(line or '').strip()
        if not text or text.lower().startswith('root:') or text.startswith('#'):
            return ''
        table=''
        key=text
        if ':' in text and not text.startswith('{'):
            table,key=text.split(':',1)
            table=table.strip()
            key=key.strip()
        root=self._legit_current_root()
        root_key=str(root.get('key') or '').strip() if root else ''
        if root_key:
            try:
                part=external_legit_builder.describe_part(root_key, key, table=table or None)
                if part:
                    p_table=str(part.get('table') or table or '').strip()
                    p_key=str(part.get('key') or key or '').strip()
                    if p_table and p_key:
                        return f'{p_table}:{p_key}'
            except Exception:
                pass
        return f'{table}:{key}' if table and key else ''

    def _legit_selected_lines_for_core(self, exclude_slot=None):
        out=[]
        skip=str(exclude_slot or '').strip().lower()
        for slot in sorted(self.legit_selected_by_slot.keys()):
            if skip and str(slot).strip().lower()==skip:
                continue
            for val in self.legit_selected_by_slot.get(slot,[]):
                table,key=self._split_legit_part_line(val)
                if table and key:
                    out.append(f'{table}:{key}')
        return out

    def _sync_legit_selection_from_text(self):
        raw = self.field_vars.get('legit_selected_parts', tk.StringVar(value='')).get() or ''
        txt = self.widgets.get('legit_selected_parts')
        if isinstance(txt, tk.Text):
            raw = txt.get('1.0','end-1c')
            self.field_vars['legit_selected_parts'].set(raw)
        rebuilt={}
        rejected=[]
        for line in raw.splitlines():
            stripped=str(line or '').strip()
            if not stripped or stripped.lower().startswith('root:') or stripped.startswith('#'):
                continue
            normalized=self._normalize_legit_part_line(stripped)
            table,key=self._split_legit_part_line(normalized)
            if table and key:
                rebuilt.setdefault(table,[]).append(f'{table}:{key}')
            else:
                rejected.append(stripped)
        self.legit_selected_by_slot = rebuilt
        self.legit_rejected_part_lines = rejected

    def _sync_legit_selected_text(self):
        # Keep the bridge payload clean: only selected part lines go into legit_selected_parts.
        # Root is already sent separately as legit_root_serial, so a root: comment line can break build/give actions.
        self.legit_rejected_part_lines=[]
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

    def _legit_selected_text_changed(self):
        txt=self.widgets.get('legit_selected_parts')
        if isinstance(txt, tk.Text):
            self.field_vars['legit_selected_parts'].set(txt.get('1.0','end-1c'))
        self._sync_legit_selection_from_text()
        self._clear_legit_outputs()
        if getattr(self, 'legit_rejected_part_lines', None):
            self._set_legit_status(f'Selected parts edited; {len(self.legit_rejected_part_lines)} unresolved line(s). Generated output cleared.', log_global=False)
        else:
            self._set_legit_status(f'Selected parts edited: {len(self._legit_selected_lines_for_core())} selected. Generated output cleared.', log_global=False)
        self._render_legit_slots()

    def _legit_passive_base_key(self, key):
        import re
        try:
            return re.sub(r'_tier_\d+$', '', str(key or '').strip().lower())
        except Exception:
            return str(key or '').strip().lower()

    def _legit_root_is_class_mod(self, root):
        if not root:
            return False
        root_key = str(root.get('key') or '').strip()
        for field in ('item_type', '_item_type', 'type'):
            value = str(root.get(field) or '').strip().lower().replace(' ', '_')
            if value in ('class_mod', 'classmod'):
                return True
        try:
            core_root = external_legit_builder.get_root(root_key)
        except Exception:
            core_root = None
        if core_root:
            value = str(core_root.get('item_type') or core_root.get('_item_type') or '').strip().lower().replace(' ', '_')
            if value in ('class_mod', 'classmod'):
                return True
        try:
            if self._root_item_type(root) == 'class_mod':
                return True
        except Exception:
            pass
        return bool(root_key.lower().startswith('classmod_') and core_root and str(core_root.get('item_type') or '').strip().lower() == 'class_mod')

    def _legit_apply_max_passives_local(self):
        self._sync_legit_selection_from_text()
        root = self._legit_current_root()
        if not root:
            return self._set_legit_status('Choose a class mod root first before using Add All Max Passives.')
        if not self._legit_root_is_class_mod(root):
            return self._set_legit_status('Add All Max Passives is only for class mod roots.')
        unlock = str(self.field_vars.get('legit_unlock_modded', tk.StringVar(value='false')).get() or '').lower() in ('1','true','yes','on')
        if not unlock:
            return self._set_legit_status('Turn on Unlock rules for modded gear before adding every max passive.')
        root_key = str(root.get('key') or '').strip()
        if not root_key:
            return self._set_legit_status('No class mod root key selected.')
        try:
            chains = external_legit_builder.max_passive_point_chains(root_key, limit=5000)
        except Exception as exc:
            return self._set_legit_status(f'Legit passive max scan failed for {root_key}: {exc!r}')
        scanned = sum(len(c.get('parts') or []) for c in chains)
        max_lines = []
        for chain in chains:
            for line in chain.get('lines') or []:
                if line and ':' in str(line):
                    max_lines.append(str(line))
        if not max_lines:
            return self._set_legit_status(f'No passive_points tier chains found for {root_key}. Scanned {scanned} passive parts.')
        # Replace existing passive_points selection with full max-point chains, preserving all other selected slots.
        self.legit_selected_by_slot['passive_points'] = list(max_lines)
        self._sync_legit_selected_text()
        self._clear_legit_outputs()
        self._set_legit_status(
            f'Added max passive points for {len(chains)} passive(s), {len(max_lines)} total passive point parts '
            f'for {root.get("build_label") or root_key}. Replaced existing passive_points selections.'
        )



    # ---------------- V20 BL4 Codes: local Lootlemon + live GZO import ----------------
    GZO_CODES_URL = 'https://save-editor.be/GZO/Borderlands4/Codes.html'
    GZO_CATALOG_URL = 'https://save-editor.be/GZO/Borderlands4/codes/api.php?action=catalog'
    GZO_CACHE_NAME = 'MattsSDKBoostingTools_gzo_codes.json'
    CUSTOM_BL4_CODES_NAME = 'custom_bl4_codes.json'
    GZO_CACHE_VERSION = 5
    GZO_SERIAL_RE = re.compile(r"@U[0-9A-Za-z!#$%&()*+\-;<=>?@^_`{/}~]{12,}")
    CODE_MANUFACTURER_ALIASES = {
        'atlas': 'Atlas', 'c4sh': 'C4SH', 'cov': 'COV', 'co v': 'COV', 'daedalus': 'Daedalus',
        'deadlus': 'Daedalus', 'hyperion': 'Hyperion', 'jakobs': 'Jakobs', 'maliwan': 'Maliwan',
        'order': 'Order', 'ripper': 'Ripper', 'borg': 'Ripper', 'bor': 'Ripper',
        'tediore': 'Tediore', 'torgue': 'Torgue', 'vladof': 'Vladof',
    }
    CODE_TYPE_ALIASES = {
        'armor': 'Armor', 'assault rifle': 'Assault Rifle', 'assault_rifle': 'Assault Rifle',
        'asr': 'Assault Rifle', 'class mod': 'Class Mods', 'class_mod': 'Class Mods',
        'classmod': 'Class Mods', 'class mods': 'Class Mods', 'energy': 'Energy',
        'enhancement': 'Enhancements', 'enhancements': 'Enhancements', 'gadget': 'Gadget', 'grenade': 'Ordnance',
        'grenades': 'Ordnance', 'ordnance': 'Ordnance', 'heavy': 'Heavy Weapon',
        'heavy weapon': 'Heavy Weapon', 'other': 'Other', 'pistol': 'Pistol',
        'repkit': 'Repkits', 'repkits': 'Repkits', 'repair kit': 'Repkits',
        'repair_kit': 'Repkits', 'shield': 'Shields', 'shields': 'Shields',
        'shotgun': 'Shotgun', 'shutgun': 'Shotgun', 'smg': 'SMG', 'sniper': 'Sniper',
        'weapon': 'Weapons', 'weapons': 'Weapons',
    }
    CODE_RARITY_ALIASES = {
        'common': 'Common', 'uncommon': 'Uncommon', 'rare': 'Rare', 'epic': 'Epic',
        'legendary': 'Legendary', 'legendr': 'Legendary', 'pearlescent': 'Pearlescent',
        'pearl': 'Pearlescent', 'perle': 'Pearlescent',
    }
    CODE_CLASS_ALIASES = {
        'ai': 'AI', 'c4sh': 'C4SH', 'exo soldier': 'Exo Soldier', 'exo_soldier': 'Exo Soldier',
        'forgeknight': 'Paladin', 'gravitar': 'Gravitar', 'paladin': 'Paladin', 'siren': 'Siren',
        'vex': 'Siren', 'rafa': 'Exo Soldier', 'amon': 'Forgeknight', 'harlowe': 'Gravitar',
    }
    CODE_MATTMAB_STATUS_ALIASES = {
        'pass': 'PASS', 'passed': 'PASS', 'legit': 'PASS',
        'fail': 'FAIL', 'failed': 'FAIL', 'modded': 'FAIL',
        'error': 'ERROR', 'skipped': 'SKIPPED', '?': 'ERROR',
        'unchecked': '', 'not checked': '', '': '',
    }

    def _gzo_cache_path_external(self):
        return RESOURCE_DIR / self.GZO_CACHE_NAME

    def _custom_bl4_codes_path_external(self):
        return RESOURCE_DIR / self.CUSTOM_BL4_CODES_NAME

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
        return self._stable_code_id('gzo', row)

    def _stable_code_id(self, prefix, row):
        basis = '|'.join(str((row or {}).get(k, '') or '') for k in ('serial', 'name', 'listing', 'source'))
        digest = hashlib.sha1(basis.encode('utf-8', errors='ignore')).hexdigest()[:16]
        return f'{prefix}:{digest}'

    def _norm_listing(self, *vals):
        text = ' '.join(str(v or '') for v in vals).lower()
        if 'modded' in text: return 'Modded'
        if 'legit' in text: return 'Legit'
        if 'lootlemon' in text: return 'Lootlemon'
        return 'GZO'

    def _code_norm_key(self, value):
        text = self._ascii_clean(value).lower().replace('_', ' ').replace('-', ' ')
        return re.sub(r'\s+', ' ', text).strip()

    def _looks_like_code_payload(self, value):
        text = str(value or '').strip()
        if not text:
            return False
        if text.startswith('@U') or self.GZO_SERIAL_RE.search(text):
            return True
        low = text.lower()
        if low.startswith(('http://', 'https://', 'bl4(')):
            return True
        if len(text) > 96 and re.search(r'[{}|=@]', text):
            return True
        if text.count('{') >= 2 or text.count('|') >= 2:
            return True
        return False

    def _code_token_values(self, value):
        if value in (None, ''):
            return []
        if isinstance(value, dict):
            raw = [str(v) for v in value.values() if v not in (None, '')]
        elif isinstance(value, (list, tuple, set)):
            raw = [str(v) for v in value if v not in (None, '')]
        else:
            raw = [str(value)]
        out = []
        for item in raw:
            if self._looks_like_code_payload(item):
                continue
            for token in re.split(r'[,|;/]+', item):
                clean = self._ascii_clean(token)
                if clean:
                    out.append(clean)
        return out

    def _normalize_code_listing(self, value, fallback=''):
        text = self._ascii_clean(value)
        if not text or self._looks_like_code_payload(text):
            text = self._ascii_clean(fallback)
        key = self._code_norm_key(text)
        if key in self.CODE_MATTMAB_STATUS_ALIASES and key not in ('modded', 'legit'):
            return ''
        if 'custom static' in key or 'community' in key or 'crayons82' in key:
            return 'Custom Static'
        if 'lootlemon' in key:
            return 'Lootlemon'
        if 'modded' in key or 'non legit' in key or 'nonlegit' in key:
            return 'Modded'
        if 'legit' in key:
            return 'Legit'
        if 'gzo' in key:
            return 'GZO'
        return text if text in ('Custom Static', 'Community Modded') else ''

    def _normalize_code_source(self, value, fallback=''):
        text = self._ascii_clean(value) or self._ascii_clean(fallback)
        if not text or self._looks_like_code_payload(text):
            return ''
        key = self._code_norm_key(text)
        if 'custom' in key or 'crayons82' in key:
            return 'Custom Static'
        if 'lootlemon' in key:
            return 'Local Lootlemon Cache' if 'local' in key or 'cache' in key else 'Lootlemon'
        if 'gzo' in key:
            return 'GZO'
        return text[:64]

    def _normalize_code_type(self, value):
        key = self._code_norm_key(value)
        if not key or self._looks_like_code_payload(value):
            return ''
        return self.CODE_TYPE_ALIASES.get(key, '')

    def _normalize_code_manufacturer(self, value):
        key = self._code_norm_key(value)
        if not key or self._looks_like_code_payload(value):
            return ''
        return self.CODE_MANUFACTURER_ALIASES.get(key, '')

    def _normalize_code_rarity(self, value):
        key = self._code_norm_key(value)
        if not key or self._looks_like_code_payload(value):
            return ''
        return self.CODE_RARITY_ALIASES.get(key, '')

    def _normalize_code_class(self, value):
        key = self._code_norm_key(value)
        if not key or self._looks_like_code_payload(value):
            return ''
        return self.CODE_CLASS_ALIASES.get(key, '')

    def _normalize_code_classification(self, value):
        key = self._code_norm_key(value)
        if not key or self._looks_like_code_payload(value):
            return ''
        if key in ('modded', 'working modded', 'custom modded', 'non legit', 'nonlegit'):
            return 'Modded'
        if key in ('legit', 'official legit'):
            return 'Legit'
        return self._ascii_clean(value)[:64]

    def _normalize_code_creator(self, value):
        text = self._ascii_clean(value)
        if not text or self._looks_like_code_payload(text):
            return ''
        key = self._code_norm_key(text)
        if key in self.CODE_MANUFACTURER_ALIASES or key in self.CODE_TYPE_ALIASES or key in self.CODE_RARITY_ALIASES:
            return ''
        return text[:80]

    def _normalize_code_mattmab_status(self, value):
        key = self._code_norm_key(value)
        return self.CODE_MATTMAB_STATUS_ALIASES.get(key, self._ascii_clean(value).upper() if key in ('pass', 'fail', 'error', 'skipped') else '')

    def _classify_code_metadata_values(self, *values):
        info = {'manufacturer': '', 'type': '', 'rarity': '', 'character_class': '', 'tags': ''}
        extras = []
        for value in values:
            for token in self._code_token_values(value):
                key = self._code_norm_key(token)
                if not info['manufacturer'] and key in self.CODE_MANUFACTURER_ALIASES:
                    info['manufacturer'] = self.CODE_MANUFACTURER_ALIASES[key]
                elif not info['type'] and key in self.CODE_TYPE_ALIASES:
                    info['type'] = self.CODE_TYPE_ALIASES[key]
                elif not info['rarity'] and key in self.CODE_RARITY_ALIASES:
                    info['rarity'] = self.CODE_RARITY_ALIASES[key]
                elif not info['character_class'] and key in self.CODE_CLASS_ALIASES:
                    info['character_class'] = self.CODE_CLASS_ALIASES[key]
                elif len(token) <= 80 and not self._looks_like_code_payload(token):
                    extras.append(token)
        seen = set()
        clean_extras = []
        for token in extras:
            norm = self._code_norm_key(token)
            if norm and norm not in seen:
                seen.add(norm); clean_extras.append(token)
        info['tags'] = ', '.join(clean_extras)
        return info

    def _normalize_code_entry(self, raw, default_source='', default_listing=''):
        if not isinstance(raw, dict):
            return None
        row = dict(raw)
        serial = str(row.get('serial') or row.get('base85') or row.get('Base85') or row.get('code') or row.get('value') or '').strip()
        if not self._is_valid_bl4_serial(serial):
            return None
        classified = self._classify_code_metadata_values(
            row.get('category'), row.get('type'), row.get('manufacturer'), row.get('maker'),
            row.get('rarity'), row.get('character_class'), row.get('tags'), row.get('extra_tags'),
        )
        source = self._normalize_code_source(row.get('source'), default_source)
        listing = self._normalize_code_listing(row.get('listing'), default_listing or source)
        if not listing:
            listing = self._normalize_code_listing(source) or 'GZO'
        type_value = self._normalize_code_type(row.get('type')) or self._normalize_code_type(row.get('category')) or classified.get('type', '')
        manufacturer = self._normalize_code_manufacturer(row.get('manufacturer')) or self._normalize_code_manufacturer(row.get('maker')) or classified.get('manufacturer', '')
        rarity = self._normalize_code_rarity(row.get('rarity')) or classified.get('rarity', '')
        character_class = self._normalize_code_class(row.get('character_class')) or classified.get('character_class', '')
        classification = self._normalize_code_classification(row.get('classification') or row.get('item_classification') or row.get('classify'))
        creator = self._normalize_code_creator(row.get('creator') or row.get('author') or row.get('creatorName') or row.get('owner'))
        tags = row.get('tags', '')
        if isinstance(tags, (list, tuple, set)):
            tags = ', '.join(self._ascii_clean(t) for t in tags if self._ascii_clean(t))
        tag_values = []
        for group in (self._ascii_clean(tags), classified.get('tags', '')):
            for token in self._code_token_values(group):
                if token:
                    tag_values.append(token)
        seen_tags = set()
        deduped_tags = []
        for token in tag_values:
            norm = self._code_norm_key(token)
            if norm and norm not in seen_tags:
                seen_tags.add(norm)
                deduped_tags.append(token)
        tags = ', '.join(deduped_tags)
        category = self._normalize_code_type(row.get('category')) or type_value or self._ascii_clean(row.get('category'))[:64]
        if self._normalize_code_manufacturer(category) or self._normalize_code_rarity(category) or self._looks_like_code_payload(category):
            category = type_value or 'BL4 Codes'
        normalized = {
            'id': str(row.get('id') or ''),
            'name': self._ascii_clean(row.get('name') or row.get('displayName') or row.get('title') or row.get('itemName')) or 'BL4 Code',
            'serial': serial,
            'listing': listing,
            'category': category or 'BL4 Codes',
            'type': type_value,
            'rarity': rarity,
            'manufacturer': manufacturer,
            'creator': creator,
            'character_class': character_class,
            'classification': classification,
            'source': source or default_source or listing,
            'url': str(row.get('lootlemon_url') or row.get('url') or '').strip(),
            'lootlemon_url': str(row.get('lootlemon_url') or row.get('url') or '').strip(),
            'mattmab_validator': self._normalize_code_mattmab_status(row.get('mattmab_validator') or row.get('mattmab_result') or row.get('mattmabResult') or row.get('result')),
            'mattmab_validator_detail': self._ascii_clean(row.get('mattmab_validator_detail') or row.get('validatorDetail') or row.get('detail')),
            'tags': tags,
            'extra_tags': self._ascii_clean(row.get('extra_tags')),
            'notes': self._ascii_clean(row.get('notes')),
            'decoded_identity': row.get('decoded_identity') if isinstance(row.get('decoded_identity'), dict) else {},
        }
        if not normalized['id'].startswith('custom:'):
            prefix = self._code_norm_key(normalized['source'] or normalized['listing']).split(' ')[0] or 'code'
            normalized['id'] = self._stable_code_id(prefix, normalized)
        return normalized

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
        self._set_bl4_status('Refreshing GZO BL4 codes from save-editor.be catalog API...', log_global=True)
        self._set_bl4_progress('Refreshing GZO catalog locally...')
        def work():
            try:
                rows = self._fetch_gzo_catalog_entries()
                self._save_gzo_cache_external(rows)
                def done():
                    self._populate_bl4_filter_values()
                    self._populate_bl4_codes_v13()
                    self._set_bl4_progress('')
                    self._set_bl4_status(f'Refreshed GZO catalog: {len(rows)} code(s) cached locally. Use Listing = Modded or Legit to filter GZO rows.', log_global=True)
                self.after(0, done)
            except Exception as exc:
                def failed():
                    self._set_bl4_progress('')
                    self._set_bl4_status(f'GZO refresh failed: {exc!r}', log_global=True)
                self.after(0, failed)
        threading.Thread(target=work, daemon=True).start()

    def _get_lootlemon_entries(self):
        data = self.resources.get('lootlemon_codes') or {}
        entries = data.get('entries', []) if isinstance(data, dict) else []
        out=[]
        for e in entries:
            if not isinstance(e,dict): continue
            row = self._normalize_code_entry(e, default_source='Local Lootlemon Cache', default_listing='Lootlemon')
            if row:
                out.append(row)
        return out

    def _get_gzo_entries(self):
        out = []
        for row in self._load_gzo_cache_external():
            normalized = self._normalize_code_entry(row, default_source='GZO', default_listing=row.get('listing') or 'GZO')
            if normalized:
                out.append(normalized)
        return out

    def _get_custom_bl4_entries(self):
        path = self._custom_bl4_codes_path_external()
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding='utf-8') or '[]')
        except Exception:
            return []
        entries = payload.get('entries', []) if isinstance(payload, dict) else payload
        out = []
        for row in entries if isinstance(entries, list) else []:
            if not isinstance(row, dict) or row.get('enabled') is False:
                continue
            normalized = self._normalize_code_entry(row, default_source='Custom Static', default_listing='Custom Static')
            if normalized:
                if not normalized.get('id', '').startswith('custom:'):
                    normalized['id'] = self._stable_code_id('custom', normalized)
                out.append(normalized)
        return out

    def _get_code_entries(self):
        # Merge by exact serial. GZO fills catalog bucket metadata; custom static rows
        # are applied last so refreshable cache updates cannot erase community entries.
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
        for custom in self._get_custom_bl4_entries():
            serial=str(custom.get('serial') or '').strip()
            if not serial:
                continue
            if serial in by_serial:
                merged=dict(by_serial[serial])
                for key, value in custom.items():
                    if value not in (None, '', [], {}):
                        merged[key]=value
                sources = [str(merged.get('source') or '').strip(), str(by_serial[serial].get('source') or '').strip()]
                merged['merged_sources'] = ', '.join(sorted({s for s in sources if s}, key=str.lower))
                by_serial[serial]=merged
            else:
                by_serial[serial]=custom
        rows += list(by_serial.values())
        results=getattr(self, 'bl4_mattmab_results', {}) or {}
        if results:
            for row in rows:
                serial=str(row.get('serial') or '').strip()
                update=results.get(serial) or results.get(self._bl4_row_id(row))
                if isinstance(update, dict):
                    row.update(update)
        return rows

    def _code_display(self, e):
        name = e.get('name') or 'Unnamed'
        listing = e.get('listing') or ''
        eid=self._bl4_row_id(e)
        active='> ' if eid == getattr(self, 'bl4_active_id', '') else '  '
        checked='[X]' if eid in getattr(self, 'bl4_selected_ids', set()) else '[ ]'
        prefix=f"[{listing.upper()}] " if listing in ('Legit','Modded') else ''
        meta=' | '.join(x for x in [
            self._mattmab_validator_short_local(e),
            str(e.get('type') or ''),
            str(e.get('manufacturer') or ''),
            str(e.get('rarity') or ''),
            str(e.get('character_class') or ''),
            str(e.get('creator') or ''),
        ] if x and x != 'GZO')
        return f"{active}{checked} {prefix}{name}    {meta}"

    def _code_value(self, e, key):
        if key == 'listing': return self._normalize_code_listing(e.get('listing') or e.get('source') or '')
        if key in ('category','type'): return self._normalize_code_type(e.get('type') or e.get('category') or '')
        if key == 'manufacturer': return self._normalize_code_manufacturer(e.get('manufacturer') or '')
        if key == 'rarity': return self._normalize_code_rarity(e.get('rarity') or '')
        if key == 'creator': return self._normalize_code_creator(e.get('creator') or '')
        if key == 'source': return self._normalize_code_source(e.get('source') or '')
        return self._ascii_clean(e.get(key) or '')

    def _code_filter_values(self, key, label_all='All'):
        vals = sorted({self._code_value(e,key) for e in self._get_code_entries() if self._code_value(e,key)})
        return [label_all] + vals

    def _populate_bl4_filter_values(self):
        mapping = {
            'code_listing':self._bl4_listing_values(),
            'code_type':self._code_filter_values('type'),
            'code_manufacturer':self._code_filter_values('manufacturer'),
            'code_rarity':self._code_filter_values('rarity'),
            'code_creator':self._code_filter_values('creator'),
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
        if tab.get('id') == 'serial_bookmarks':
            return self._tab_serial_bookmarks_local(body, cards)
        if tab.get('id') == 'validator':
            return self._tab_validator_blimgui(body)
        return super()._tab_two_col(body, tab, cards)

    def _validator_text_area(self, parent, fid, height, initial=''):
        self.field_vars[fid] = self.field_vars.get(fid) or tk.StringVar(value=str(initial or ''))
        txt = tk.Text(parent, height=height, bg='#181417', fg='#f1f5ff', insertbackground='#f1f5ff', relief='flat', wrap='word', font=('Consolas',8))
        txt.insert('1.0', self.field_vars[fid].get())
        txt.pack(fill='x', padx=8, pady=(2,6))
        txt.bind('<KeyRelease>', lambda e,v=self.field_vars[fid],w=txt:v.set(w.get('1.0','end-1c')))
        self.widgets[fid] = txt
        return txt

    def _validator_get_text(self, fid):
        widget = self.widgets.get(fid)
        if isinstance(widget, tk.Text):
            return widget.get('1.0', 'end-1c')
        return self.field_vars.get(fid, tk.StringVar(value='')).get()

    def _validator_set_text(self, fid, value):
        value = str(value or '')
        self.field_vars[fid] = self.field_vars.get(fid) or tk.StringVar(value='')
        self.field_vars[fid].set(value)
        widget = self.widgets.get(fid)
        if isinstance(widget, tk.Text):
            widget.delete('1.0', 'end')
            widget.insert('1.0', value)

    def _validator_set_progress(self, label='Idle', done=0, total=0, passed=0, failed=0, running=False):
        self.validator_progress = {
            "running": bool(running),
            "label": str(label or 'Idle'),
            "done": int(done or 0),
            "total": int(total or 0),
            "passed": int(passed or 0),
            "failed": int(failed or 0),
        }
        self._validator_refresh_progress()

    def _validator_progress_text(self):
        p = getattr(self, 'validator_progress', {}) or {}
        label = str(p.get('label') or 'Idle')
        total = int(p.get('total') or 0)
        done = int(p.get('done') or 0)
        passed = int(p.get('passed') or 0)
        failed = int(p.get('failed') or 0)
        if total > 0:
            return f"{label} ({done}/{total}) legit {passed} / modded {failed}"
        return label

    def _validator_refresh_progress(self):
        if hasattr(self, 'validator_progress_var'):
            self.validator_progress_var.set(self._validator_progress_text())
        btn = getattr(self, 'validator_cancel_button', None)
        if btn:
            if (getattr(self, 'validator_progress', {}) or {}).get('running'):
                btn.pack(side='left', padx=(8,0))
            else:
                btn.pack_forget()

    def _tab_validator_blimgui(self, body):
        wrap, inner = self._card_wrap(body, 'Validator', '#00a3d7')
        wrap.pack(fill='both', expand=True, padx=6, pady=5)
        tk.Label(inner, text='Validate one serial or a large pasted list. Validation runs on a background thread so the menu does not stall the game thread. Bulk input expects one serial per line.', bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1300).pack(fill='x', padx=8, pady=(6,2))
        tk.Label(inner, text=external_validator.validator_definition(), bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1300).pack(fill='x', padx=8, pady=(0,2))
        tk.Label(inner, text='DISCLAIMER: This tool has not been fully verified for Legit loot and all outputs should still be verified against https://save-editor.be.', bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1300).pack(fill='x', padx=8, pady=(0,5))

        prow = tk.Frame(inner, bg='#090d17')
        prow.pack(fill='x', padx=8, pady=(0,6))
        self.validator_progress_var = tk.StringVar(value=self._validator_progress_text())
        tk.Label(prow, textvariable=self.validator_progress_var, bg='#181417', fg='#f1f5ff', font=('Segoe UI',8), anchor='w', padx=6, pady=4).pack(side='left', fill='x', expand=True)
        self.validator_cancel_button = tk.Button(prow, text='Cancel', command=self._validator_cancel_current, bg='#172033', fg=ACCENT_COLORS.get('pink','#ff5db7'), relief='flat', padx=10, pady=4, font=('Segoe UI',8,'bold'))
        self._validator_refresh_progress()

        tk.Frame(inner, bg='#333a48', height=1).pack(fill='x', padx=8, pady=(2,5))
        tk.Label(inner, text='Basic validation', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').pack(fill='x', padx=8)
        self._validator_text_area(inner, 'validator_basic_input', 4)
        basic_buttons = tk.Frame(inner, bg='#090d17')
        basic_buttons.pack(fill='x', padx=6, pady=(0,3))
        for i,(txt,cmd,col) in enumerate([
            ('Validate Basic', self._validator_validate_basic, 'cyan'),
            ('Clear Validator', self._validator_clear, 'pink'),
        ]):
            tk.Button(basic_buttons, text=txt, command=cmd, bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
        for i in range(2): basic_buttons.grid_columnconfigure(i, weight=1)
        self._validator_text_area(inner, 'validator_basic_output', 5, 'Paste one @U/Base85 or decoded human serial, then Validate Basic.')

        tk.Frame(inner, bg='#333a48', height=1).pack(fill='x', padx=8, pady=(5,5))
        tk.Label(inner, text='Bulk validation', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').pack(fill='x', padx=8)
        self._validator_text_area(inner, 'validator_bulk_input', 9)
        bulk_buttons = tk.Frame(inner, bg='#090d17')
        bulk_buttons.pack(fill='x', padx=6, pady=(0,3))
        for i,(txt,cmd,col) in enumerate([
            ('Validate Bulk', self._validator_validate_bulk, 'gold'),
            ('Clear Validator', self._validator_clear, 'pink'),
        ]):
            tk.Button(bulk_buttons, text=txt, command=cmd, bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
        for i in range(2): bulk_buttons.grid_columnconfigure(i, weight=1)
        self._validator_text_area(inner, 'validator_bulk_output', 12, 'Paste one serial per line, then Validate Bulk.')

    def _validator_worker_active(self):
        thread = getattr(self, 'validator_thread', None)
        return bool(thread is not None and thread.is_alive())

    def _validator_start(self, rows, mode):
        if self._validator_worker_active():
            self.log('Validator is already running.')
            return False
        self.validator_cancel_event.clear()
        self.validator_run_id += 1
        run_id = self.validator_run_id
        total = len(rows)
        self._validator_set_progress(f'Validating {mode}', 0, total, 0, 0, True)
        def progress(snapshot):
            self.after(0, lambda s=dict(snapshot): self._validator_set_progress(
                s.get('label') or f'Validating {mode}',
                s.get('done') or 0,
                s.get('total') or total,
                s.get('passed') or 0,
                s.get('failed') or 0,
                s.get('running', True),
            ))
        def work():
            result = external_validator.validate_many(
                rows,
                cancel_check=self.validator_cancel_event.is_set,
                progress_callback=progress,
            )
            def finish():
                if run_id != self.validator_run_id:
                    return
                output = result.get('output') or result.get('summary') or ''
                if mode == 'basic':
                    if result.get('results'):
                        output = external_validator.format_validation_result(result['results'][0])
                    self._validator_set_text('validator_basic_output', output)
                else:
                    self._validator_set_text('validator_bulk_output', output)
                self._validator_set_progress('Validation cancelled' if result.get('cancelled') else 'Validation complete', result.get('processed') or 0, result.get('total') or total, result.get('passed') or 0, result.get('failed') or 0, False)
                self.log(result.get('summary') or 'Validation complete.')
            self.after(0, finish)
        self.validator_thread = threading.Thread(target=work, daemon=True)
        self.validator_thread.start()
        return True

    def _validator_validate_basic(self):
        text = self._validator_get_text('validator_basic_input').strip()
        if not text:
            self._validator_set_text('validator_basic_output', 'Paste one @U/Base85 or decoded human serial first.')
            return
        self._validator_set_text('validator_basic_output', 'Queued basic validation...')
        self._validator_start([text], 'basic')

    def _validator_validate_bulk(self):
        text = self._validator_get_text('validator_bulk_input')
        rows = external_validator.parse_serial_text(text)
        if not rows:
            self._validator_set_text('validator_bulk_output', 'Paste one serial per line first.')
            return
        self._validator_set_text('validator_bulk_output', f'Queued {len(rows)} serials for background validation...')
        self._validator_start(rows, 'bulk')

    def _validator_cancel_current(self):
        self.validator_cancel_event.set()
        total = int((getattr(self, 'validator_progress', {}) or {}).get('total') or 0)
        done = int((getattr(self, 'validator_progress', {}) or {}).get('done') or 0)
        self._validator_set_progress(f'Cancelled after {done}/{total} serials.', done, total, int((getattr(self, 'validator_progress', {}) or {}).get('passed') or 0), int((getattr(self, 'validator_progress', {}) or {}).get('failed') or 0), False)

    def _validator_clear(self):
        self._validator_cancel_current()
        self.validator_run_id += 1
        self._validator_set_text('validator_basic_input', '')
        self._validator_set_text('validator_bulk_input', '')
        self._validator_set_text('validator_basic_output', 'Paste one @U/Base85 or decoded human serial, then Validate Basic.')
        self._validator_set_text('validator_bulk_output', 'Paste one serial per line, then Validate Bulk.')
        self._validator_set_progress('Idle', 0, 0, 0, 0, False)
        self.log('Validator cleared.')

    def _tab_serial_bookmarks_local(self, body, cards):
        self._ensure_bookmark_state()
        wrap, inner = self._card_wrap(body, 'Serial Bookmarks', '#8a2be2')
        wrap.pack(fill='both', expand=True, padx=6, pady=5, anchor='n')
        header=tk.Frame(inner, bg='#090d17')
        header.pack(fill='x', padx=8, pady=(6,2))
        tk.Label(header, text='SERIAL BOOKMARKS', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').pack(side='left')
        for txt,cmd,col in [
            ('+ New Serial', lambda:self._serial_bookmark_action_local('serial_bookmark_new'), 'cyan'),
            ('Import', lambda:self._serial_bookmark_action_local('serial_bookmark_import'), 'gold'),
        ]:
            tk.Button(header, text=txt, command=cmd, bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold'), padx=8, pady=5).pack(side='left', padx=(10,0))
        tk.Label(inner, text='Browse saved serials, edit the active entry, then deliver the checked items from the footer.', bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1100).pack(fill='x', padx=8, pady=(0,5))

        filters=tk.Frame(inner, bg='#090d17')
        filters.pack(fill='x', padx=8, pady=(0,5))
        filters.grid_columnconfigure(0, weight=1)
        self.field_vars['bookmark_search']=self.field_vars.get('bookmark_search') or tk.StringVar(value='')
        search=ttk.Entry(filters, textvariable=self.field_vars['bookmark_search'])
        search.grid(row=0, column=0, sticky='ew')
        search.bind('<KeyRelease>', lambda e:self._refresh_serial_bookmarks_ui())
        self.widgets['bookmark_search']=search
        tk.Label(filters, text='Search', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8), anchor='w').grid(row=0, column=1, sticky='w', padx=(6,0))
        self.bookmark_group_filter_combo=ttk.Combobox(filters, textvariable=self.bookmark_group_filter_var, values=['All'], state='readonly', width=24)
        self.bookmark_group_filter_combo.grid(row=1, column=0, sticky='ew', pady=(3,0))
        tk.Label(filters, text='Groups', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8), anchor='w').grid(row=1, column=1, sticky='w', padx=(6,0), pady=(3,0))
        self.bookmark_group_filter_combo.bind('<<ComboboxSelected>>', lambda e:self._refresh_serial_bookmarks_ui())

        panes=tk.Frame(inner, bg='#090d17')
        panes.pack(fill='both', expand=True, padx=8, pady=4)
        panes.grid_columnconfigure(0, weight=3)
        panes.grid_columnconfigure(1, weight=2)
        panes.grid_rowconfigure(3, weight=1)
        tk.Label(panes, text='SERIALS', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').grid(row=0,column=0,sticky='ew')
        tk.Label(panes, text='DETAILS', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').grid(row=0,column=1,sticky='ew',padx=(8,0))
        self.bookmark_count_var=tk.StringVar(value='0 shown / 0 saved | 0 selected')
        tk.Label(panes, textvariable=self.bookmark_count_var, bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w').grid(row=1,column=0,sticky='ew')
        buttons=tk.Frame(panes, bg='#090d17')
        buttons.grid(row=2,column=0,sticky='ew',pady=(3,0))
        for i,(txt,cmd,col) in enumerate([
            ('Select All', self._select_all_visible_bookmarks, 'purple'),
            ('Clear', self._clear_checked_bookmarks, 'red'),
            ('Copy Selected Serials', self._copy_checked_bookmark_serials, 'gold'),
            ('Toggle Checked', self._toggle_active_bookmark_checked, 'cyan'),
        ]):
            tk.Button(buttons, text=txt, command=cmd, bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
        for i in range(4): buttons.grid_columnconfigure(i, weight=1)
        self.serial_bookmarks_listbox=tk.Listbox(panes, height=18, selectmode='browse', bg='#0e1320', fg='#d7def5', selectbackground='#1f3b63', relief='flat', font=('Consolas',8), exportselection=False)
        self.serial_bookmarks_listbox.grid(row=3,column=0,sticky='nsew',pady=(4,0))
        self.serial_bookmarks_listbox.bind('<<ListboxSelect>>', lambda e:self._serial_bookmark_selected())
        self.serial_bookmarks_listbox.bind('<Double-Button-1>', lambda e:'break')
        details=tk.Frame(panes, bg='#090d17')
        details.grid(row=1,column=1,rowspan=3,sticky='nsew',padx=(8,0),pady=(0,0))
        details.grid_columnconfigure(0, weight=1)
        details.grid_rowconfigure(5, weight=1)
        self._bookmark_detail_entry(details, 'Name', 'bookmark_name', 0)
        self._bookmark_detail_entry(details, 'Group', 'bookmark_group', 2)
        tk.Label(details, text='Serial', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8), anchor='w').grid(row=4,column=0,sticky='ew',pady=(6,1))
        self.field_vars['bookmark_serial']=self.field_vars.get('bookmark_serial') or tk.StringVar(value='')
        serial_txt=tk.Text(details, height=9, bg='#181417', fg='#f1f5ff', insertbackground='#f1f5ff', relief='flat', wrap='word', font=('Consolas',8))
        serial_txt.insert('1.0', self.field_vars['bookmark_serial'].get())
        serial_txt.grid(row=5,column=0,sticky='nsew')
        serial_txt.bind('<KeyRelease>', lambda e,v=self.field_vars['bookmark_serial'],w=serial_txt:v.set(w.get('1.0','end-1c')))
        self.widgets['bookmark_serial']=serial_txt
        detail_buttons=tk.Frame(details, bg='#090d17')
        detail_buttons.grid(row=6,column=0,sticky='ew',pady=(5,0))
        for i,(txt,aid,col) in enumerate([
            ('Save','serial_bookmark_save','cyan'),
            ('Duplicate','serial_bookmark_duplicate','purple'),
            ('Delete','serial_bookmark_delete','red'),
            ('Copy','serial_bookmark_copy','gold'),
        ]):
            tk.Button(detail_buttons, text=txt, command=lambda a=aid:self._serial_bookmark_action_local(a), bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
        for i in range(4): detail_buttons.grid_columnconfigure(i, weight=1)
        self.bookmark_status_var=tk.StringVar(value=self.bookmark_status_message)
        tk.Label(details, textvariable=self.bookmark_status_var, bg='#090d17', fg='#21e05f', font=('Segoe UI',8), anchor='w', justify='left', wraplength=520).grid(row=7,column=0,sticky='ew',pady=(4,0))

        footer=tk.Frame(inner, bg='#090d17')
        footer.pack(fill='x', padx=8, pady=(6,8))
        self._external_player_target_row(footer, 'bookmark_target_player', 'Serial Bookmarks Target')
        footer_buttons=tk.Frame(footer, bg='#090d17')
        footer_buttons.pack(fill='x', padx=8, pady=(3,0))
        self.bookmark_delivery_status_var=tk.StringVar(value='0 selected')
        tk.Label(footer_buttons, textvariable=self.bookmark_delivery_status_var, bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w').grid(row=0,column=0,sticky='ew',padx=3)
        tk.Label(footer_buttons, text='Delivery uses GiveRewardAllPlayers, then patches requested target(s)', bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w').grid(row=0,column=1,sticky='ew',padx=3)
        for i,(txt,mode,col) in enumerate([
            ('Deliver Selected','selected','purple'),
            ('Deliver All','all','gold'),
            ('Deliver Non-Host','nonhost','cyan'),
        ], start=2):
            tk.Button(footer_buttons, text=txt, command=lambda m=mode:self._deliver_bookmark_serials(m), bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
        for i in range(5): footer_buttons.grid_columnconfigure(i, weight=1)
        self.bookmark_split_preview_var=tk.StringVar(value='Delivery preview: no checked bookmarks.')
        tk.Label(footer, textvariable=self.bookmark_split_preview_var, bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1100).pack(fill='x', padx=8, pady=(2,0))
        self.serial_bookmark_rows=[]
        self._refresh_serial_bookmarks_ui()

    def _bookmark_detail_entry(self, parent, label, fid, row):
        tk.Label(parent, text=label, bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8), anchor='w').grid(row=row,column=0,sticky='ew',pady=(0,1))
        self.field_vars[fid]=self.field_vars.get(fid) or tk.StringVar(value='')
        ent=ttk.Entry(parent, textvariable=self.field_vars[fid])
        ent.grid(row=row+1,column=0,sticky='ew',pady=(0,4))
        self.widgets[fid]=ent
        return ent

    def _serial_tools_text_area(self, parent, fid, height, readonly=False):
        txt = tk.Text(parent, height=height, bg='#181417', fg='#f1f5ff', insertbackground='#f1f5ff', relief='flat', wrap='word', font=('Consolas',8))
        txt.pack(fill='x', padx=8, pady=(2,6))
        self.widgets[fid] = txt
        self.field_vars[fid] = self.field_vars.get(fid) or tk.StringVar(value='')
        initial = self.field_vars[fid].get()
        if initial:
            txt.insert('1.0', initial)
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
        inp = self._serial_tools_text_area(inner, 'serial_tools_input', 5)
        inp.bind('<KeyRelease>', self._serial_tools_input_changed)

        buttons = tk.Frame(inner, bg='#090d17')
        buttons.pack(fill='x', padx=8, pady=(0,6))
        for label, cmd, color in [
            ('Convert', self._serial_convert_local, 'cyan'),
            ('Clear', self._clear_serial_tools_local, 'pink'),
        ]:
            tk.Button(buttons, text=label, command=cmd, bg='#172033', activebackground='#22304c', fg=ACCENT_COLORS.get(color,'#00d4ff'), activeforeground=ACCENT_COLORS.get(color,'#00d4ff'), relief='flat', padx=12, pady=5, width=14, font=('Segoe UI',8,'bold')).pack(side='left', padx=(0,6), pady=3)

        status = self.field_vars.get('serial_tools_status') or tk.StringVar(value='Paste a @U serial or deserialized serial text above.')
        self.field_vars['serial_tools_status'] = status
        self.widgets['serial_tools_status'] = tk.Label(inner, textvariable=status, bg='#090d17', fg='#21e05f', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1100)
        self.widgets['serial_tools_status'].pack(fill='x', padx=8, pady=(0,6))

        self._serial_tools_output_section(inner, 'Deserialized Output', 'serial_tools_deserialized', 6, 'Copy Deserialized', 'deserialized serial')
        self._serial_tools_output_section(inner, 'Parts Breakdown', 'serial_tools_parts_breakdown', 8, 'Copy Parts Breakdown', 'parts breakdown')
        self._serial_tools_output_section(inner, '@U Serialized Output', 'serial_tools_serialized', 4, 'Copy Serialized', 'serialized @U serial')

    def _serial_tools_output_section(self, parent, title, fid, height, copy_button, copy_label):
        tk.Frame(parent, bg='#333a48', height=1).pack(fill='x', padx=8, pady=(5,5))
        tk.Label(parent, text=title, bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').pack(fill='x', padx=8, pady=(0,1))
        self._serial_tools_text_area(parent, fid, height)
        tk.Button(
            parent,
            text=copy_button,
            command=lambda f=fid, c=copy_label: self._copy_serial_tools_text(self._serial_tools_get_text(f), c),
            bg='#172033',
            activebackground='#22304c',
            fg=ACCENT_COLORS.get('purple','#b36bff'),
            activeforeground=ACCENT_COLORS.get('purple','#b36bff'),
            relief='flat',
            padx=8,
            pady=5,
            font=('Segoe UI',8,'bold'),
        ).pack(anchor='w', padx=8, pady=(0,6))

    def _copy_serial_tools_text(self, text, label):
        value=str(text or '')
        if not value:
            return self.log(f'{label}: nothing to copy.')
        try:
            self.clipboard_clear()
            self.clipboard_append(value)
            self.log(f'Copied {label} to clipboard.')
        except Exception:
            self.log(f'Clipboard copy unavailable for {label}; select the output text and copy manually.')

    def _serial_tools_input_changed(self, _event=None):
        widget = self.widgets.get('serial_tools_input')
        if isinstance(widget, tk.Text):
            value=widget.get('1.0', 'end-1c')
            self.field_vars['serial_tools_input'].set(value)
            self.field_vars['serial_input']=self.field_vars.get('serial_input') or tk.StringVar(value='')
            self.field_vars['serial_input'].set(value)
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

    def _external_player_target_row(self, parent, field_id, label):
        row = tk.Frame(parent, bg='#090d17'); row.pack(fill='x', padx=8, pady=2)
        tk.Label(row, text=label, bg='#090d17', fg='#cfd8f3', width=18, anchor='w', font=('Segoe UI',8)).pack(side='left')
        var = self.field_vars.get(field_id) or tk.StringVar(value='')
        self.field_vars[field_id] = var
        cb = ttk.Combobox(row, textvariable=var, values=self.player_options, state='readonly')
        cb.pack(side='left', fill='x', expand=True)
        self.widgets[field_id] = cb
        self._bind_external_target_combo(cb, field_id, label)
        if self.player_options and not var.get():
            var.set(self.player_options[0])
        tk.Button(row, text='Set Target', command=lambda f=field_id, l=label:self._set_bridge_target_from_field_async(f, l), bg='#172033', fg='#21e05f', relief='flat', font=('Segoe UI',8,'bold'), padx=8, pady=4).pack(side='left', padx=(5,0))
        tk.Button(row, text='Refresh Players', command=self.poll_status, bg='#172033', fg='#00d4ff', relief='flat', font=('Segoe UI',8,'bold'), padx=8, pady=4).pack(side='left', padx=(5,0))
        return cb

    def _resolve_external_target_value(self, field_id):
        raw = str(self.field_vars.get(field_id, tk.StringVar(value='')).get() or '').strip()
        if not raw:
            return ''
        return raw.split('|', 1)[0].strip() if '|' in raw else raw

    def _bind_external_target_combo(self, cb, field_id, label):
        try:
            cb.bind('<<ComboboxSelected>>', lambda _e, f=field_id, l=label:self._set_bridge_target_from_field_async(f, l))
        except Exception:
            pass

    def _set_bridge_target_from_field(self, field_id, label='Target'):
        value = self._resolve_external_target_value(field_id)
        if not str(value or '').strip():
            return False, f'{label}: no player selected.'
        try:
            res = http_json('POST', '/action', {'action':'set_target_player','payload':{'target_player':value},'timeout':10.0}, timeout=12.0)
        except Exception as exc:
            return False, f'{label}: set target failed: {exc!r}'
        return bool(res.get('ok', True)), str(res.get('message') or f'{label} set.')

    def _set_bridge_target_from_field_async(self, field_id, label='Target'):
        def work():
            ok, msg = self._set_bridge_target_from_field(field_id, label)
            self.after(0, lambda:self.log(msg if ok else 'Target failed: ' + msg))
            self.after(0, self.poll_status)
        threading.Thread(target=work, daemon=True).start()

    def _uses_global_target(self, action_id):
        return action_id in {
            'kick_player',
            'give_serial_selected',
            'set_level',
            'give_currency',
            'max_player_level',
            'max_spec_level',
            'max_currency',
            'max_eridium',
            'max_sdu',
            'max_all',
            'set_backpack_bank_selected',
            'drop_all_shinies',
            'toggle_debug_cam',
            'teleport_debug_cam',
        } or str(action_id or '').startswith('devperk_')

    def _run_action_with_global_target(self, action):
        aid = action.get('id')
        self.log(f'Setting target before {aid}...')
        def work():
            ok, msg = self._set_bridge_target_from_field('target_player', 'Target Player')
            if not ok:
                self.after(0, lambda m=msg:self.log(m))
                return
            self.after(0, lambda a=action: super(App, self).run_action(a))
        threading.Thread(target=work, daemon=True).start()

    def _tab_bl4_codes_v13(self, body, cards):
        self._ensure_bl4_state()
        if not self.bl4_cache_autoload_attempted:
            self.bl4_cache_autoload_attempted=True
            self._load_bl4_cache_local(silent=True)
        wrap, inner = self._card_wrap(body, 'BL4 Codes', '#b37a00')
        wrap.pack(fill='both', expand=True, padx=6, pady=5)
        tk.Label(inner, text='Merged BL4 Codes catalog', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').pack(fill='x', padx=8, pady=(6,1))
        tk.Label(inner, text='Single merged codes tab. Refresh GZO updates from save-editor.be. Local Lootlemon JSON is used only as a serial/link cache and local-only fallback rows. This never scrapes lootlemon.com.', bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1200).pack(fill='x', padx=8, pady=(0,2))
        tk.Label(inner, text='Mattmab Validation labels: Legit = the serial structure passed the conservative real-count/rule validator with no hard errors. Modded = the validator found hard structural problems such as wrong-root parts, unresolved parts, disallowed selected components, duplicate/slot-count breaks, or obvious cross-root modded tokens. Error = the serial could not be parsed/validated. This is a tooling classification, not a Gearbox/official authenticity guarantee.', bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1200).pack(fill='x', padx=8, pady=(0,4))

        cache_buttons = tk.Frame(inner, bg='#090d17'); cache_buttons.pack(fill='x', padx=8, pady=(0,5))
        for i,(txt,cmd,col) in enumerate([
            ('Load Cache', self._load_bl4_cache_local, 'cyan'),
            ('Refresh GZO', self._refresh_gzo_catalog_async, 'gold'),
            ('Reload Lootlemon Cache', self._reload_bl4_lootlemon_cache_local, 'gold'),
            ('Mattmab Validation', self._run_bl4_mattmab_validation_local, 'green'),
            ('Import Selected To Bookmarks', self._import_selected_bl4_bookmarks, 'purple'),
        ]):
            tk.Button(cache_buttons, text=txt, command=cmd, bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
            cache_buttons.grid_columnconfigure(i, weight=1)

        self.bl4_progress_var=tk.StringVar(value=getattr(self,'bl4_progress_message',''))
        tk.Label(inner, textvariable=self.bl4_progress_var, bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1200).pack(fill='x', padx=8, pady=(0,3))
        tk.Frame(inner, bg='#333a48', height=1).pack(fill='x', padx=8, pady=(2,5))
        tk.Label(inner, text='Filters', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').pack(fill='x', padx=8)

        top = tk.Frame(inner, bg='#090d17'); top.pack(fill='x', padx=8, pady=(1,4))
        left_filters = tk.Frame(top, bg='#090d17'); left_filters.pack(side='left', fill='x', expand=True)
        right_filters = tk.Frame(top, bg='#090d17'); right_filters.pack(side='left', fill='x', expand=True, padx=(10,0))

        self._field_row_entry_v13(left_filters, 'Search', 'code_search', '')
        self._field_row_combo_v13(left_filters, 'Listing', 'code_listing', self._bl4_listing_values())
        self._field_row_combo_v13(left_filters, 'Type', 'code_type', self._code_filter_values('type'))
        self._field_row_combo_v13(right_filters, 'Manufacturer', 'code_manufacturer', self._code_filter_values('manufacturer'))
        self._field_row_combo_v13(right_filters, 'Rarity', 'code_rarity', self._code_filter_values('rarity'))
        self._field_row_combo_v13(right_filters, 'Creator', 'code_creator', self._code_filter_values('creator'))
        self._field_row_combo_v13(right_filters, 'Mattmab Result', 'code_mattmab_result', ['All','Legit','Modded','Error','Unchecked'])

        filter_buttons = tk.Frame(inner, bg='#090d17'); filter_buttons.pack(fill='x', padx=8, pady=(0,4))
        for i,(txt,val,col) in enumerate([('All Results','All','cyan'),('Legit','Legit','green'),('Modded','Modded','purple'),('Error','Error','gold'),('?','Unchecked','purple')]):
            tk.Button(filter_buttons, text=txt, command=lambda v=val:self._set_bl4_result_filter(v), bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0, column=i, sticky='ew', padx=3, pady=3)
        for i in range(5): filter_buttons.grid_columnconfigure(i, weight=1)

        self.bl4_count_var=tk.StringVar(value='0 shown / 0 merged | 0 selected')
        tk.Label(inner, textvariable=self.bl4_count_var, bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w').pack(fill='x', padx=8, pady=(0,2))

        list_buttons = tk.Frame(inner, bg='#090d17'); list_buttons.pack(fill='x', padx=8, pady=(0,4))
        for i,(txt,cmd,col) in enumerate([
            ('Select All', self._select_all_bl4_codes, 'purple'),
            ('Clear', self._clear_bl4_code_selection, 'pink'),
            ('Copy Selected Serials', self._copy_selected_bl4_serials, 'gold'),
        ]):
            tk.Button(list_buttons, text=txt, command=cmd, bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
            list_buttons.grid_columnconfigure(i,weight=1)

        main = tk.Frame(inner, bg='#090d17'); main.pack(fill='both', expand=True, padx=8, pady=4)
        main.grid_columnconfigure(0, weight=3); main.grid_columnconfigure(1, weight=2); main.grid_rowconfigure(1, weight=1)
        tk.Label(main, text='CODES', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').grid(row=0,column=0,sticky='ew')
        tk.Label(main, text='DETAILS', bg='#090d17', fg='#cfd8f3', font=('Segoe UI',8,'bold'), anchor='w').grid(row=0,column=1,sticky='ew',padx=(8,0))
        self.bl4_codes_listbox = tk.Listbox(main, height=18, selectmode='browse', bg='#0e1320', fg='#d7def5', selectbackground='#1f3b63', relief='flat', font=('Consolas',8), exportselection=False)
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
        self.bl4_detail_buttons = detail_buttons

        tk.Frame(inner, bg='#333a48', height=1).pack(fill='x', padx=8, pady=(3,5))
        footer = tk.Frame(inner, bg='#090d17'); footer.pack(fill='x', padx=8, pady=(4,8))
        self._external_player_target_row(footer, 'code_target_player', 'BL4 Codes Target')
        self._field_row_combo_v13(footer, 'Override delivery level?', 'code_override_level', ['false','true'], readonly=True)
        self._field_row_entry_v13(footer, 'Delivery Level', 'code_delivery_level', '60')
        self.bl4_delivery_status_var=tk.StringVar(value='0 selected | Delivery uses GiveRewardAllPlayers, then patches requested target(s)')
        tk.Label(footer, textvariable=self.bl4_delivery_status_var, bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w').pack(fill='x', padx=8, pady=(2,0))
        deliver = tk.Frame(footer, bg='#090d17'); deliver.pack(fill='x', padx=8, pady=(3,0))
        for i,(txt,mode,col) in enumerate([('Deliver Selected','selected','purple'),('Deliver All','all','gold'),('Deliver Non-Host','nonhost','cyan')]):
            tk.Button(deliver, text=txt, command=lambda m=mode:self._deliver_bl4_codes(m), bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=3,pady=3)
        tk.Button(deliver, text='Refresh Players', command=self.poll_status, bg='#172033', fg='#00d4ff', relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=3,sticky='ew',padx=3,pady=3)
        for i in range(4): deliver.grid_columnconfigure(i,weight=1)
        self.bl4_split_preview_var=tk.StringVar(value='Delivery split: no valid serials selected yet.')
        tk.Label(footer, textvariable=self.bl4_split_preview_var, bg='#090d17', fg='#9fb3d9', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1200).pack(fill='x', padx=8, pady=(3,0))
        self.bl4_status_var=tk.StringVar(value=self.bl4_status_message)
        tk.Label(footer, textvariable=self.bl4_status_var, bg='#090d17', fg='#21e05f', font=('Segoe UI',8), anchor='w', justify='left', wraplength=1200).pack(fill='x', padx=8, pady=(2,0))
        self.bl4_filtered_entries=[]
        self._populate_bl4_filter_values()
        self._populate_bl4_codes_v13()

    def _ensure_bl4_state(self):
        if not hasattr(self, 'bl4_active_id'):
            self.bl4_active_id=''
        if not hasattr(self, 'bl4_selected_ids'):
            self.bl4_selected_ids=set()
        if not hasattr(self, 'bl4_status_message'):
            self.bl4_status_message=''
        if not hasattr(self, 'bl4_progress_message'):
            self.bl4_progress_message=''
        if not hasattr(self, 'bl4_mattmab_results'):
            self.bl4_mattmab_results={}
        if not hasattr(self, 'bl4_mattmab_thread'):
            self.bl4_mattmab_thread=None
        if not hasattr(self, 'bl4_mattmab_run_id'):
            self.bl4_mattmab_run_id=0
        if not hasattr(self, 'bl4_cache_autoload_attempted'):
            self.bl4_cache_autoload_attempted=False
        if not hasattr(self, 'bl4_selection_refreshing'):
            self.bl4_selection_refreshing=False

    def _set_bl4_status(self, message, log_global=False):
        self._ensure_bl4_state()
        self.bl4_status_message=str(message or '')
        if hasattr(self, 'bl4_status_var'):
            self.bl4_status_var.set(self.bl4_status_message)
        if log_global and self.bl4_status_message:
            self.log(self.bl4_status_message)

    def _set_bl4_progress(self, message):
        self.bl4_progress_message=str(message or '')
        if hasattr(self, 'bl4_progress_var'):
            self.bl4_progress_var.set(self.bl4_progress_message)

    def _load_bl4_cache_local(self, silent=False):
        rows=self._get_code_entries()
        if rows and not self.bl4_active_id:
            self.bl4_active_id=str(rows[0].get('id') or self._gzo_entry_id(rows[0]))
        if not silent:
            self._set_bl4_status(f'Loaded {len(rows)} merged BL4 code(s) from local cache.', log_global=True)
        self._populate_bl4_filter_values()
        self._populate_bl4_codes_v13()

    def _reload_bl4_lootlemon_cache_local(self):
        self._populate_bl4_filter_values()
        self._populate_bl4_codes_v13()
        local_count=len(self._get_lootlemon_entries())
        self._set_bl4_status(f'Reloaded local Lootlemon cache: {local_count} local row(s) available. Direct lootlemon.com scraping is disabled.', log_global=True)

    def _bl4_mattmab_detail_from_result(self, result):
        if not isinstance(result, dict):
            return 'Validation failed: invalid validator result.'
        lines=[str(result.get('message') or external_validator.format_validation_result(result))]
        errors=[str(x) for x in (result.get('errors') or []) if str(x).strip()]
        warnings=[str(x) for x in (result.get('warnings') or []) if str(x).strip()]
        root_key=str(result.get('root_key') or '').strip()
        if root_key:
            lines.append(f'Root: {root_key}')
        if errors:
            lines.append('Reasons: ' + '; '.join(errors[:8]))
            if len(errors) > 8:
                lines.append(f'+{len(errors) - 8} more reason(s).')
        if warnings:
            lines.append('Warnings: ' + '; '.join(warnings[:5]))
        return self._ascii_clean('\n'.join(lines))

    def _bl4_mattmab_update_from_result(self, result):
        status=str((result or {}).get('mattmab_validator') or '').strip().upper()
        if status not in ('PASS','FAIL','ERROR'):
            label=str((result or {}).get('status') or (result or {}).get('result') or '').strip().upper()
            if label == external_validator.STATUS_LEGIT:
                status='PASS'
            elif label == external_validator.STATUS_MODDED:
                status='FAIL'
            else:
                status='ERROR'
        return {
            'mattmab_validator': status,
            'mattmab_validator_detail': self._bl4_mattmab_detail_from_result(result),
        }

    def _bl4_mattmab_apply_results(self, run_id, updates, counts, total):
        if run_id != getattr(self, 'bl4_mattmab_run_id', 0):
            return
        for serial, row_id, update in updates:
            if serial:
                self.bl4_mattmab_results[serial]=dict(update)
            if row_id:
                self.bl4_mattmab_results[row_id]=dict(update)
        self._populate_bl4_codes_v13()
        self._set_bl4_progress('')
        summary=(
            f"Mattmab validation complete: {counts.get('PASS',0)} legit, "
            f"{counts.get('FAIL',0)} modded, {counts.get('ERROR',0)} error, "
            f"{counts.get('SKIPPED',0)} skipped, {sum(counts.values())}/{total} processed."
        )
        self._set_bl4_status(summary, log_global=True)

    def _run_bl4_mattmab_validation_local(self):
        self._ensure_bl4_state()
        thread=getattr(self, 'bl4_mattmab_thread', None)
        if thread is not None and thread.is_alive():
            return self._set_bl4_status('Mattmab validation is already running.', log_global=True)
        if hasattr(self, 'bl4_filtered_entries'):
            entries=list(self.bl4_filtered_entries)
        else:
            entries=list(self._get_code_entries())
        total=len(entries)
        if total <= 0:
            self._set_bl4_progress('')
            return self._set_bl4_status('No visible BL4 Codes rows to validate.', log_global=True)

        self.bl4_mattmab_run_id += 1
        run_id=self.bl4_mattmab_run_id
        self._set_bl4_progress(f'Mattmab validation running: 0/{total} rows...')
        self._set_bl4_status(f'Running local Mattmab validation for {total} visible/filtered BL4 code row(s)...', log_global=True)

        def work():
            updates=[]
            counts={'PASS':0, 'FAIL':0, 'ERROR':0, 'SKIPPED':0}
            for idx, entry in enumerate(entries, 1):
                serial=str((entry or {}).get('serial') or '').strip()
                row_id=self._bl4_row_id(entry)
                if not self._is_valid_bl4_serial(serial):
                    update={
                        'mattmab_validator': 'SKIPPED',
                        'mattmab_validator_detail': 'Validation skipped: selected BL4 row has no valid @U serial.',
                    }
                    counts['SKIPPED'] += 1
                else:
                    try:
                        result=external_validator.validate_serial_text(serial, idx if total != 1 else None)
                        update=self._bl4_mattmab_update_from_result(result)
                    except Exception as exc:
                        update={
                            'mattmab_validator': 'ERROR',
                            'mattmab_validator_detail': f'Validation failed: {exc!r}',
                        }
                    counts[update.get('mattmab_validator') or 'ERROR'] = counts.get(update.get('mattmab_validator') or 'ERROR', 0) + 1
                updates.append((serial, row_id, update))
                if idx == total or idx == 1 or idx % 25 == 0:
                    self.after(0, lambda i=idx, c=dict(counts): self._set_bl4_progress(
                        f"Mattmab validation running: {i}/{total} rows... "
                        f"{c.get('PASS',0)} legit, {c.get('FAIL',0)} modded, {c.get('ERROR',0)} error, {c.get('SKIPPED',0)} skipped"
                    ))
            self.after(0, lambda: self._bl4_mattmab_apply_results(run_id, updates, counts, total))

        self.bl4_mattmab_thread=threading.Thread(target=work, daemon=True)
        self.bl4_mattmab_thread.start()

    def _bl4_listing_values(self):
        vals=sorted({self._code_value(e, 'listing') for e in self._get_code_entries() if self._code_value(e, 'listing')}, key=lambda x:x.lower())
        if any(self._normalize_code_classification(e.get('classification')) == 'Modded' for e in self._get_code_entries()):
            vals.append('Modded')
            vals=sorted(set(vals), key=lambda x:x.lower())
        preferred=[x for x in ('Legit','Modded','Lootlemon','GZO','Custom Static','Community Modded') if x in vals]
        rest=[x for x in vals if x not in preferred]
        return ['All'] + preferred + rest

    def _bl4_entry_matches_listing_filter(self, row, filt):
        want=str(filt or 'All').strip()
        if want == 'All':
            return True
        if self._code_value(row, 'listing').lower() == want.lower():
            return True
        classification = self._normalize_code_classification((row or {}).get('classification'))
        if classification and classification.lower() == want.lower():
            return True
        if want.lower() == 'modded':
            tags = ' '.join(self._code_token_values((row or {}).get('tags'))).lower()
            return 'modded' in tags.split()
        return False

    def _mattmab_entry_matches_filter_local(self, row, filt):
        want=str(filt or 'All').strip().upper()
        if want == 'ALL':
            return True
        status=str((row or {}).get('mattmab_validator') or '').strip().upper()
        if want == 'UNCHECKED':
            return status not in ('PASS','FAIL','ERROR')
        if want == 'LEGIT':
            return status == 'PASS'
        if want == 'MODDED':
            return status == 'FAIL'
        return status == want

    def _mattmab_validator_label_local(self, row):
        status=str((row or {}).get('mattmab_validator') or '').strip().upper()
        if status == 'PASS':
            return 'Mattmab Validation: Legit'
        if status == 'FAIL':
            return 'Mattmab Validation: Modded'
        if status == 'ERROR':
            return 'Mattmab Validation: Error'
        if status == 'SKIPPED':
            return 'Mattmab Validation: skipped'
        return 'Mattmab Validation: not checked'

    def _mattmab_validator_short_local(self, row):
        status=str((row or {}).get('mattmab_validator') or '').strip().upper()
        if status == 'PASS':
            return '[Legit]'
        if status == 'FAIL':
            return '[Modded]'
        if status == 'ERROR':
            return '[Validation Error]'
        if status == 'SKIPPED':
            return '[Skipped]'
        return '[Unchecked]'

    def _gzo_meta_label_local(self, row):
        return ' | '.join(str(row.get(k) or '').strip() for k in ('listing','type','manufacturer','rarity','creator','tags') if str(row.get(k) or '').strip())

    def _bl4_row_id(self, row):
        return str((row or {}).get('id') or self._gzo_entry_id(row or {}))

    def _bl4_active_entry(self):
        rows=self._get_code_entries()
        for row in rows:
            if self._bl4_row_id(row) == self.bl4_active_id:
                return row
        return rows[0] if rows else None

    def _set_bl4_result_filter(self, value):
        if 'code_mattmab_result' in self.field_vars:
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
            decoded = e.get('decoded_identity') if isinstance(e.get('decoded_identity'), dict) else {}
            hay=' '.join(str(e.get(k) or '') for k in ('name','listing','source','type','rarity','manufacturer','creator','character_class','classification','tags','extra_tags','notes','serial')).lower()
            if decoded:
                hay += ' ' + ' '.join(str(v or '') for v in decoded.values()).lower()
            if q and not all(term in hay for term in q.split()): continue
            listing=self._code_value(e, 'listing')
            if self.field_vars.get('code_listing'):
                lf=self.field_vars['code_listing'].get()
                if not self._bl4_entry_matches_listing_filter(e, lf): continue
            if cat!='All' and self._code_value(e,'type')!=cat: continue
            if man!='All' and self._code_value(e,'manufacturer')!=man: continue
            if rar!='All' and self._code_value(e,'rarity')!=rar: continue
            if creator!='All' and self._code_value(e,'creator')!=creator: continue
            if not self._mattmab_entry_matches_filter_local(e, result): continue
            rows.append(e)
        self.bl4_filtered_entries=rows
        all_ids={self._bl4_row_id(r) for r in self._get_code_entries()}
        self.bl4_selected_ids={bid for bid in self.bl4_selected_ids if bid in all_ids}
        self.bl4_codes_listbox.delete(0,'end')
        visible=rows[:240]
        if len(rows) > len(visible):
            self.bl4_codes_listbox.insert('end', f'Showing first {len(visible)} row(s); narrow Search/Filters for more. Select All still selects all filtered rows.')
        for e in visible:
            self.bl4_codes_listbox.insert('end', self._code_display(e))
        if rows and not self.bl4_active_id:
            self.bl4_active_id=self._bl4_row_id(rows[0])
        if rows and not any(self._bl4_row_id(r) == self.bl4_active_id for r in rows):
            self.bl4_active_id=self._bl4_row_id(rows[0])
        if rows:
            self._set_bl4_active_detail(self._bl4_active_entry())
            offset=1 if len(rows) > len(visible) else 0
            for idx,row in enumerate(visible):
                if self._bl4_row_id(row) == self.bl4_active_id:
                    self.bl4_selection_refreshing=True
                    try:
                        self.bl4_codes_listbox.selection_clear(0,'end')
                        self.bl4_codes_listbox.selection_set(idx+offset)
                        self.bl4_codes_listbox.see(idx+offset)
                    finally:
                        self.bl4_selection_refreshing=False
                    break
        else:
            self._set_bl4_detail('', '', '')
        if hasattr(self, 'bl4_count_var'):
            self.bl4_count_var.set(f'{len(rows)} shown / {len(self._get_code_entries())} merged | {len(self.bl4_selected_ids)} selected')
        self._refresh_bl4_delivery_preview()

    def _selected_bl4_entries(self):
        rows=[e for e in self._get_code_entries() if self._bl4_row_id(e) in self.bl4_selected_ids]
        if rows:
            return rows
        active=self._bl4_active_entry()
        return [active] if active else []

    def _set_bl4_detail(self, detail, serial, breakdown):
        for widget, text in [(getattr(self,'bl4_detail_text',None), detail), (getattr(self,'bl4_serial_text',None), serial), (getattr(self,'bl4_breakdown_text',None), breakdown)]:
            if widget:
                widget.configure(state='normal'); widget.delete('1.0','end'); widget.insert('1.0', text); widget.configure(state='normal')
        self.field_vars['code_serial']=self.field_vars.get('code_serial') or tk.StringVar(value='')
        self.field_vars['code_serial'].set(serial)
        if not detail and not serial and not breakdown:
            parent=getattr(self, 'bl4_detail_buttons', None)
            if parent:
                for child in parent.winfo_children():
                    child.destroy()

    def _bl4_code_selected(self):
        if getattr(self, 'bl4_selection_refreshing', False):
            return
        lb=getattr(self, 'bl4_codes_listbox', None)
        if not lb:
            return
        sel=list(lb.curselection())
        if not sel:
            return
        visible_offset=1 if len(getattr(self,'bl4_filtered_entries',[])) > 240 else 0
        idx=sel[0]-visible_offset
        if idx < 0 or idx >= min(len(getattr(self,'bl4_filtered_entries',[])), 240):
            return
        e=self.bl4_filtered_entries[idx]
        eid=self._bl4_row_id(e)
        self.bl4_active_id=eid
        if eid in self.bl4_selected_ids:
            self.bl4_selected_ids.discard(eid)
        else:
            self.bl4_selected_ids.add(eid)
        self._populate_bl4_codes_v13()

    def _set_bl4_active_detail(self, e):
        if not e: return self._set_bl4_detail('', '', '')
        detail_lines=[
            f"Name: {e.get('name','')}",
            f"Source: {e.get('source','Local')}",
            f"Listing: {e.get('listing','')}",
            f"Type: {e.get('type') or e.get('category','')}",
            f"Manufacturer: {e.get('manufacturer','')}",
            f"Rarity: {e.get('rarity','')}",
            f"Creator: {e.get('creator','')}",
            f"Classification: {e.get('classification','')}",
            self._mattmab_validator_label_local(e),
            str(e.get('mattmab_validator_detail') or ''),
            f"Tags: {e.get('tags','')}",
            f"Notes: {e.get('notes','')}",
        ]
        decoded = e.get('decoded_identity') if isinstance(e.get('decoded_identity'), dict) else {}
        if decoded:
            decoded_text = ' | '.join(f'{k}: {v}' for k, v in decoded.items() if v not in (None, '', [], {}))
            if decoded_text:
                detail_lines.append(f"Decoded: {decoded_text}")
        detail_lines.append(f"URL: {e.get('url','')}")
        detail='\n'.join(detail_lines)
        serial=e.get('serial') or ''
        breakdown=self._bl4_parts_breakdown_text(serial, quiet=True)
        self._set_bl4_detail(detail, serial, breakdown)
        self._draw_bl4_detail_buttons(e)

    def _select_all_bl4_codes(self):
        if hasattr(self,'bl4_codes_listbox'):
            for row in getattr(self, 'bl4_filtered_entries', []):
                self.bl4_selected_ids.add(self._bl4_row_id(row))
            self._populate_bl4_codes_v13()

    def _clear_bl4_code_selection(self):
        if hasattr(self,'bl4_codes_listbox'):
            self.bl4_selected_ids.clear()
            self._populate_bl4_codes_v13()

    def _selected_bl4_serials(self):
        return [str(e.get('serial') or '').strip() for e in self._selected_bl4_entries() if self._is_valid_bl4_serial(e.get('serial',''))]

    def _serial_delivery_plan_local(self, serials, mode='selected'):
        mode_key=str(mode or 'selected').lower()
        max_serials=SELECTED_SERIALS_PER_CHUNK if mode_key == 'selected' else MULTI_SERIALS_PER_CHUNK
        delay=SELECTED_CHUNK_DELAY_SECONDS if mode_key == 'selected' else MULTI_CHUNK_DELAY_SECONDS
        chunks=[]
        current=[]
        current_chars=0
        for raw in serials:
            text=str(raw or '').strip()
            if not text:
                continue
            n=len(text)+SERIAL_DELIVERY_PER_SERIAL_OVERHEAD_CHARS
            if current and (len(current) >= max_serials or current_chars + n > MAX_SERIAL_DELIVERY_CHARS):
                chunks.append(current)
                current=[]
                current_chars=0
            current.append(text)
            current_chars += n
        if current:
            chunks.append(current)
        estimated_wait=max(0.0, (len(chunks)-1) * delay) if chunks else 0.0
        return {'chunks':chunks,'max_serials':max_serials,'delay':delay,'estimated_wait':estimated_wait}

    def _copy_text_v13(self, text, label):
        try:
            self.clipboard_clear(); self.clipboard_append(text); self.log(f'Copied {label}.')
        except Exception as exc: self.log(f'Copy failed: {exc}')

    def _copy_selected_bl4_serials(self):
        serials=self._selected_bl4_serials()
        if not serials:
            return self._set_bl4_status('Select one or more BL4 serials to copy.', log_global=True)
        self._copy_text_v13('\n'.join(serials), f'{len(serials)} selected BL4 serial(s)')
        self._set_bl4_status(f'Copied {len(serials)} selected BL4 serial(s) to clipboard.')

    def _copy_bl4_serial(self):
        serial=self.field_vars.get('code_serial', tk.StringVar()).get()
        if not serial: return self.log('No serial selected.')
        self._copy_text_v13(serial, 'serial')

    def _copy_bl4_breakdown(self):
        text=getattr(self,'bl4_breakdown_text',None).get('1.0','end-1c') if getattr(self,'bl4_breakdown_text',None) else ''
        if not text: return self.log('No parts breakdown to copy.')
        self._copy_text_v13(text, 'parts breakdown')

    def _draw_bl4_detail_buttons(self, active):
        parent=getattr(self, 'bl4_detail_buttons', None)
        if not parent:
            return
        for child in parent.winfo_children():
            child.destroy()
        buttons=[
            ('Copy Parts Breakdown', self._copy_bl4_breakdown, 'purple'),
            ('Copy Serial', self._copy_bl4_serial, 'purple'),
        ]
        url=str((active or {}).get('lootlemon_url') or (active or {}).get('url') or '').strip()
        if url and 'lootlemon.com' in url.lower():
            buttons.append(('Open Lootlemon', self._open_bl4_lootlemon, 'gold'))
        buttons.append(('Bookmark This', self._bookmark_bl4_selected, 'cyan'))
        for i,(txt,cmd,col) in enumerate(buttons):
            tk.Button(parent, text=txt, command=cmd, bg='#172033', fg=ACCENT_COLORS.get(col,'#00d4ff'), relief='flat', font=('Segoe UI',8,'bold')).grid(row=0,column=i,sticky='ew',padx=2,pady=2)
            parent.grid_columnconfigure(i,weight=1)

    def _bl4_bookmark_payload(self, e):
        return {
            'name': e.get('name') or 'BL4 Code',
            'group': e.get('category') or e.get('type') or e.get('listing') or 'BL4 Codes',
            'serial': e.get('serial') or '',
            'source': e.get('source') or '',
            'listing': e.get('listing') or '',
            'type': e.get('type') or e.get('category') or '',
            'manufacturer': e.get('manufacturer') or '',
            'rarity': e.get('rarity') or '',
            'creator': e.get('creator') or '',
            'classification': e.get('classification') or '',
            'url': e.get('url') or '',
            'tags': e.get('tags') or '',
            'notes': e.get('notes') or '',
            'decoded_identity': e.get('decoded_identity') if isinstance(e.get('decoded_identity'), dict) else {},
            'mattmab_validator': e.get('mattmab_validator') or '',
            'mattmab_validator_detail': e.get('mattmab_validator_detail') or '',
        }

    def _bookmark_bl4_selected(self):
        active=self._bl4_active_entry()
        if not active:
            return self._set_bl4_status('No selected code to bookmark.', log_global=True)
        self.bl4_selected_ids.add(self._bl4_row_id(active))
        self._import_selected_bl4_bookmarks()

    def _import_selected_bl4_bookmarks(self):
        entries=self._selected_bl4_entries()
        rows=[self._bl4_bookmark_payload(e) for e in entries if self._is_valid_bl4_serial(e.get('serial',''))]
        if not rows:
            return self._set_bl4_status('No selected valid @U BL4 Codes serials to import.', log_global=True)
        added=self._add_bookmarks_local(rows, update_existing=False)
        self._set_bl4_status(f'Imported {added} BL4 Codes serial(s) to Serial Bookmarks.', log_global=True)

    def _bl4_parts_breakdown_text(self, serial, quiet=False):
        serial=str(serial or '').strip()
        if not serial:
            return ''
        try:
            out=serial_parts_breakdown_for_value(serial)
        except Exception as exc:
            out=f'Parts breakdown unavailable locally: {exc}'
        if not str(out or '').strip():
            out='Parts breakdown unavailable locally. Check that resources/gzo_parts_map.json exists.'
        if not quiet:
            self.log('Parts breakdown generated locally.')
        return out

    def _set_bl4_breakdown_text(self, text):
        if getattr(self,'bl4_breakdown_text',None):
            self.bl4_breakdown_text.delete('1.0','end')
            self.bl4_breakdown_text.insert('1.0', text or '')

    def _run_bl4_parts_breakdown(self):
        serial=self.field_vars.get('code_serial', tk.StringVar()).get().strip()
        if not serial: return self.log('No serial selected for parts breakdown.')
        self._set_bl4_breakdown_text(self._bl4_parts_breakdown_text(serial))

    def _open_bl4_lootlemon(self):
        active=self._bl4_active_entry()
        if not active: return self.log('No selected code to open.')
        url=str(active.get('lootlemon_url') or active.get('url') or '').strip()
        if not url: return self.log('Selected BL4 code has no Lootlemon URL.')
        if not re.match(r'^https?://', url, re.I): return self.log('Selected BL4 code URL is not a web link.')
        try:
            webbrowser.open(url)
            self.log('Opened Lootlemon link.')
        except Exception as exc:
            self.log(f'Open Lootlemon failed: {exc!r}')

    def _deliver_bl4_codes(self, mode):
        serials=self._selected_bl4_serials()
        if not serials: return self._set_bl4_status('Select one or more valid GZO serials first.', log_global=True)
        oversized=[i+1 for i,s in enumerate(serials) if len(str(s or '')) > MAX_SERIAL_DELIVERY_CHARS]
        if oversized:
            return self._set_bl4_status(f'Serial {oversized[0]} exceeds the {MAX_SERIAL_DELIVERY_CHARS} character delivery limit.', log_global=True)
        plan=self._serial_delivery_plan_local(serials, mode)
        try: level=int(str(self.field_vars.get('code_delivery_level', tk.StringVar(value='60')).get()).replace(',','').strip())
        except Exception: return messagebox.showerror('Invalid value','Delivery Level must be a number.')
        override=str(self.field_vars.get('code_override_level', tk.StringVar(value='false')).get()).lower() in ('1','true','yes','on')
        payload={'serial_text':'\n'.join(serials),'serial_level':level,'serial_override_level':override}
        aid={'selected':'give_serial_selected','all':'give_serial_all','nonhost':'give_serial_nonhost'}[mode]
        chunk_count=len(plan['chunks'])
        target_note=''
        if mode == 'selected':
            target_raw=str(self.field_vars.get('code_target_player', tk.StringVar()).get() or '').strip()
            target_note=f' to {target_raw}' if target_raw else ' to selected target'
        plan_msg=f"Submitting {len(serials)} {mode} serial(s){target_note} in {chunk_count} chunk(s), max {plan['max_serials']} per chunk, {plan['delay']:.1f}s delay."
        if plan['estimated_wait'] >= 10:
            plan_msg += f" Large delivery queued; this may take about {plan['estimated_wait']:.0f} seconds."
        self._set_bl4_status(plan_msg, log_global=True)
        timeout=max(30.0, plan['estimated_wait'] + (chunk_count * 6.0) + 20.0)
        def work():
            try:
                if mode == 'selected':
                    ok, msg = self._set_bridge_target_from_field('code_target_player', 'BL4 Codes Target')
                    if not ok:
                        self.after(0, lambda m=msg:self._set_bl4_status(m, log_global=True))
                        return
                res=http_json('POST','/action',{'action':aid,'payload':payload,'timeout':timeout},timeout=timeout)
                self.after(0, lambda:self.log(res.get('message') or 'BL4 code delivery requested.'))
                self.after(0, self.poll_status)
            except Exception as exc:
                self.after(0, lambda:self.log('Delivery failed: '+repr(exc)))
        threading.Thread(target=work, daemon=True).start()

    def _refresh_bl4_delivery_preview(self):
        rows=self._selected_bl4_entries()
        serials=[str(e.get('serial') or '').strip() for e in rows if e and self._is_valid_bl4_serial(e.get('serial',''))]
        if hasattr(self, 'bl4_delivery_status_var'):
            self.bl4_delivery_status_var.set(f'{len(self.bl4_selected_ids)} selected | Delivery uses GiveRewardAllPlayers, then patches requested target(s)')
        if hasattr(self, 'bl4_split_preview_var'):
            if not serials:
                self.bl4_split_preview_var.set('Delivery split: no valid serials selected yet.')
            else:
                total=sum(len(s) for s in serials)
                plan=self._serial_delivery_plan_local(serials, 'selected')
                self.bl4_split_preview_var.set(f"Delivery split: {len(plan['chunks'])} part(s) | {len(serials)} serial(s) | max {plan['max_serials']}/chunk | {plan['delay']:.1f}s delay | {total} raw chars")
        if hasattr(self, 'bl4_status_var'):
            self.bl4_status_var.set(self.bl4_status_message)

    def _update_player_options(self, status):
        super()._update_player_options(status)
        try:
            for fid, label in (
                ('target_player', 'Target Player'),
                ('code_target_player', 'BL4 Codes Target'),
                ('bookmark_target_player', 'Serial Bookmarks Target'),
                ('legit_target_player', 'Legit Builder Target'),
                ('infinite_jump_target', 'Infinite Jump Target'),
            ):
                cb=self.widgets.get(fid)
                if not isinstance(cb, ttk.Combobox):
                    continue
                self._bind_external_target_combo(cb, fid, label)
                cb.configure(values=self.player_options)
                cur=self.field_vars.get(fid, tk.StringVar()).get()
                cur_idx=str(cur).split('|',1)[0].strip() if cur else ''
                replacement=''
                if cur_idx:
                    replacement=next((opt for opt in self.player_options if opt.split('|',1)[0].strip()==cur_idx), '')
                if replacement:
                    self.field_vars[fid].set(replacement)
        except Exception: pass


    def _clear_external_log_local(self):
        try:
            self.log_text.configure(state='normal'); self.log_text.delete('1.0','end'); self.log_text.configure(state='disabled')
            self.status_var.set('Log cleared.')
        except Exception:
            self.log('Log cleared.')

    def _clear_serial_tools_local(self):
        for fid in ('serial_tools_input','serial_input','serial_tools_serialized','serial_tools_deserialized','serial_tools_parts_breakdown'):
            if hasattr(self, '_serial_tools_set_text'):
                self._serial_tools_set_text(fid, '')
            else:
                var=self.field_vars.get(fid)
                if var: var.set('')
        if 'serial_tools_status' in self.field_vars:
            self.field_vars['serial_tools_status'].set('Paste a @U serial or deserialized serial text above.')
        self.log('Cleared Serial Tools input/output.')

    def _clear_boosting_serials_local(self):
        var=self.field_vars.get('serial_text')
        if var: var.set('')
        widget=self.widgets.get('serial_text')
        if isinstance(widget, tk.Text):
            try:
                widget.delete('1.0','end')
            except Exception:
                pass
        self.log('Cleared Boosting serial input.')

    def _bookmark_store_path(self):
        from pathlib import Path
        p=RESOURCE_DIR/'user_serial_bookmarks.json'
        return p

    def _ensure_bookmark_state(self):
        if not hasattr(self, 'active_bookmark_id'):
            self.active_bookmark_id=''
        if not hasattr(self, 'checked_bookmark_ids'):
            self.checked_bookmark_ids=set()
        if not hasattr(self, 'bookmark_group_filter_var'):
            self.bookmark_group_filter_var=tk.StringVar(value='All')
        if not hasattr(self, 'bookmark_status_message'):
            self.bookmark_status_message='Ready.'

    def _load_bookmark_store(self):
        import json
        p=self._bookmark_store_path()
        if not p.exists(): return []
        try:
            data=json.loads(p.read_text(encoding='utf-8'))
            return data.get('entries', data) if isinstance(data, dict) else data
        except Exception: return []

    def _save_bookmark_store(self, rows):
        import json
        p=self._bookmark_store_path(); p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps({'entries': rows},indent=2),encoding='utf-8')

    def _bookmark_generated_id(self, row):
        basis='|'.join(str((row or {}).get(k) or '') for k in ('serial','name','group','source','url'))
        digest=hashlib.sha1(basis.encode('utf-8', errors='ignore')).hexdigest()[:16]
        return f'bm_{digest}'

    def _bookmark_id(self, row):
        return str((row or {}).get('id') or self._bookmark_generated_id(row))

    def _bookmark_serial_key(self, row):
        return str((row or {}).get('serial') or '').strip()

    def _normalize_bookmark_row(self, row):
        row=dict(row or {})
        row['id']=self._bookmark_id(row)
        row['name']=str(row.get('name') or row.get('title') or 'Untitled Serial')
        row['group']=str(row.get('group') or row.get('category') or 'Default')
        row['serial']=str(row.get('serial') or '').strip()
        row['source']=str(row.get('source') or '')
        row['listing']=str(row.get('listing') or '')
        row['type']=str(row.get('type') or row.get('category') or '')
        row['manufacturer']=str(row.get('manufacturer') or '')
        row['rarity']=str(row.get('rarity') or '')
        row['creator']=str(row.get('creator') or '')
        row['classification']=str(row.get('classification') or '')
        row['url']=str(row.get('url') or '')
        row['tags']=str(row.get('tags') or '')
        row['notes']=str(row.get('notes') or '')
        row['decoded_identity']=row.get('decoded_identity') if isinstance(row.get('decoded_identity'), dict) else {}
        row['mattmab_validator']=str(row.get('mattmab_validator') or '')
        row['mattmab_validator_detail']=str(row.get('mattmab_validator_detail') or '')
        return row

    def _add_bookmarks_local(self, incoming, update_existing=True, allow_duplicates=False):
        self._ensure_bookmark_state()
        rows=[self._normalize_bookmark_row(r) for r in self._load_bookmark_store()]
        by_serial={self._bookmark_serial_key(r): i for i,r in enumerate(rows) if self._bookmark_serial_key(r)}
        added=0
        for raw in incoming:
            row=self._normalize_bookmark_row(raw)
            key=self._bookmark_serial_key(row)
            if not key:
                continue
            if key in by_serial and not allow_duplicates:
                if update_existing:
                    current=rows[by_serial[key]]
                    current.update({k:v for k,v in row.items() if v})
                    self.active_bookmark_id=str(current.get('id') or '')
                continue
            if key not in by_serial:
                by_serial[key]=len(rows)
            if allow_duplicates:
                row['id']=f"{row['id']}_{len(rows)}"
            rows.append(row)
            self.active_bookmark_id=str(row.get('id') or '')
            added += 1
        self._save_bookmark_store(rows)
        self._refresh_serial_bookmarks_ui()
        return added

    def _set_bookmark_field(self, fid, value):
        value=str(value or '')
        var=self.field_vars.get(fid)
        if var:
            var.set(value)
        widget=self.widgets.get(fid)
        try:
            if isinstance(widget, tk.Text):
                widget.delete('1.0','end')
                widget.insert('1.0', value)
        except Exception:
            pass

    def _bookmark_list_label(self, row):
        bid=self._bookmark_id(row)
        active='> ' if bid == getattr(self, 'active_bookmark_id', '') else '  '
        checked='[X]' if bid in getattr(self, 'checked_bookmark_ids', set()) else '[ ]'
        group=row.get('group') or 'Default'
        name=row.get('name') or 'Untitled Serial'
        return f"{active}{checked} {name}        {group}"

    def _bookmark_groups(self, rows):
        groups=sorted({str(r.get('group') or 'Default') for r in rows})
        return ['All'] + (groups or ['Default'])

    def _set_bookmark_status(self, message, log_global=False):
        self._ensure_bookmark_state()
        self.bookmark_status_message=str(message or '')
        if hasattr(self, 'bookmark_status_var'):
            self.bookmark_status_var.set(self.bookmark_status_message)
        if log_global:
            self.log(self.bookmark_status_message)

    def _bookmark_row_by_id(self, bookmark_id):
        for row in [self._normalize_bookmark_row(r) for r in self._load_bookmark_store()]:
            if self._bookmark_id(row) == bookmark_id:
                return row
        return None

    def _refresh_serial_bookmarks_ui(self):
        self._ensure_bookmark_state()
        lb=getattr(self, 'serial_bookmarks_listbox', None)
        if not lb:
            return
        q=(self.field_vars.get('bookmark_search', tk.StringVar()).get() or '').lower().strip()
        rows=[self._normalize_bookmark_row(r) for r in self._load_bookmark_store()]
        all_ids={self._bookmark_id(r) for r in rows}
        self.checked_bookmark_ids={bid for bid in self.checked_bookmark_ids if bid in all_ids}
        groups=self._bookmark_groups(rows)
        cb=getattr(self, 'bookmark_group_filter_combo', None)
        if isinstance(cb, ttk.Combobox):
            cur=self.bookmark_group_filter_var.get() or 'All'
            cb.configure(values=groups)
            if cur not in groups:
                self.bookmark_group_filter_var.set('All')
        group_filter=self.bookmark_group_filter_var.get() or 'All'
        if group_filter != 'All':
            rows=[r for r in rows if str(r.get('group') or 'Default') == group_filter]
        if q:
            rows=[r for r in rows if q in ' '.join(str(r.get(k) or '') for k in ('name','group','serial','source','listing','type','manufacturer','rarity','creator','url')).lower()]
        self.serial_bookmark_rows=rows
        lb.delete(0,'end')
        for row in rows:
            lb.insert('end', self._bookmark_list_label(row))
        for idx,row in enumerate(rows):
            if self._bookmark_id(row) == self.active_bookmark_id:
                lb.selection_set(idx)
                lb.see(idx)
                break
        if hasattr(self, 'bookmark_count_var'):
            total=len([self._normalize_bookmark_row(r) for r in self._load_bookmark_store()])
            self.bookmark_count_var.set(f'{len(rows)} shown / {total} saved | {len(self.checked_bookmark_ids)} selected')
        self._refresh_bookmark_delivery_preview()

    def _serial_bookmark_selected(self):
        self._ensure_bookmark_state()
        lb=getattr(self, 'serial_bookmarks_listbox', None)
        if not lb:
            return
        sel=list(lb.curselection())
        if not sel:
            return
        idx=sel[0]
        if idx < 0 or idx >= len(getattr(self, 'serial_bookmark_rows', [])):
            return
        row=self.serial_bookmark_rows[idx]
        self.active_bookmark_id=self._bookmark_id(row)
        self._set_bookmark_field('bookmark_name', row.get('name') or '')
        self._set_bookmark_field('bookmark_group', row.get('group') or '')
        self._set_bookmark_field('bookmark_serial', row.get('serial') or '')
        if self.active_bookmark_id in self.checked_bookmark_ids:
            self.checked_bookmark_ids.discard(self.active_bookmark_id)
        else:
            self.checked_bookmark_ids.add(self.active_bookmark_id)
        self._refresh_serial_bookmarks_ui()

    def _toggle_active_bookmark_checked(self):
        self._ensure_bookmark_state()
        if not self.active_bookmark_id:
            return self._set_bookmark_status('No active bookmark to toggle.', log_global=True)
        if self.active_bookmark_id in self.checked_bookmark_ids:
            self.checked_bookmark_ids.discard(self.active_bookmark_id)
        else:
            self.checked_bookmark_ids.add(self.active_bookmark_id)
        self._refresh_serial_bookmarks_ui()

    def _select_all_visible_bookmarks(self):
        self._ensure_bookmark_state()
        for row in getattr(self, 'serial_bookmark_rows', []):
            self.checked_bookmark_ids.add(self._bookmark_id(row))
        self._refresh_serial_bookmarks_ui()
        self._set_bookmark_status(f'Selected {len(getattr(self, "serial_bookmark_rows", []))} visible bookmark(s).', log_global=True)

    def _clear_checked_bookmarks(self):
        self._ensure_bookmark_state()
        self.checked_bookmark_ids.clear()
        self._refresh_serial_bookmarks_ui()

    def _checked_bookmark_rows(self):
        self._ensure_bookmark_state()
        rows=[self._normalize_bookmark_row(r) for r in self._load_bookmark_store()]
        return [r for r in rows if self._bookmark_id(r) in self.checked_bookmark_ids]

    def _selected_bookmark_rows(self):
        rows=self._checked_bookmark_rows()
        if rows:
            return rows
        active=self._bookmark_row_by_id(getattr(self, 'active_bookmark_id', ''))
        return [active] if active else []

    def _bookmark_parse_serial_text(self, raw):
        tokens=[]
        for line in (raw or '').splitlines():
            text=line.strip()
            if not text:
                continue
            if '|' in text:
                tokens.append(text)
                continue
            starts=[m.start() for m in re.finditer(r'(?=@U)', text)]
            if len(starts) > 1:
                starts.append(len(text))
                for i in range(len(starts)-1):
                    part=text[starts[i]:starts[i+1]].strip()
                    if part:
                        tokens.append(part)
                continue
            tokens.append(text)
        return tokens

    def _bookmark_resolve_deliverable_serials(self, raw_serials):
        out=[]
        for raw in raw_serials or []:
            text=str(raw or '').strip()
            if not text:
                continue
            if text.startswith('@U'):
                out.append(text)
                continue
            if '|' in text:
                try:
                    out.append(human_to_serial(text))
                except Exception as exc:
                    self.log(f'Serial Bookmarks: serialize failed for bookmarked serial: {exc!r}')
                    return []
                continue
            out.append(text)
        return out

    def _bookmark_serials_from_entries(self, rows):
        serials=[]
        seen=set()
        for row in rows or []:
            serial=str((row or {}).get('serial') or '').strip()
            if not serial or serial in seen:
                continue
            seen.add(serial)
            serials.append(serial)
        return serials

    def _copy_checked_bookmark_serials(self):
        rows=self._selected_bookmark_rows()
        serials=self._bookmark_serials_from_entries(rows)
        if not serials:
            self._set_bookmark_status('Select one or more bookmarked serials to copy.', log_global=True)
            return
        self._copy_text_v13('\n'.join(serials), f'{len(serials)} selected bookmarked serial(s)')
        self._set_bookmark_status(f'Copied {len(serials)} selected bookmarked serial(s) to clipboard.')

    def _bookmark_delivery_rows(self):
        return self._selected_bookmark_rows()

    def _refresh_bookmark_delivery_preview(self):
        rows=self._bookmark_delivery_rows()
        serials=[]
        for row in rows:
            serials.extend(self._bookmark_parse_serial_text(str((row or {}).get('serial') or '').strip()))
        if hasattr(self, 'bookmark_delivery_status_var'):
            self.bookmark_delivery_status_var.set(f'{len(rows)} selected')
        if hasattr(self, 'bookmark_split_preview_var'):
            if not serials:
                self.bookmark_split_preview_var.set('Delivery split: no valid serials selected yet.')
            else:
                total=sum(len(str(s or '').strip()) for s in serials if str(s or '').strip())
                self.bookmark_split_preview_var.set(f'Delivery split: 1 part | {len(serials)} serial(s) | {total} raw chars | {total} estimated payload chars.')

    def _deliver_bookmark_serials(self, mode):
        rows=self._bookmark_delivery_rows()
        if not rows:
            return self._set_bookmark_status('Select one or more saved serials first.', log_global=True)
        raw=[]
        for row in rows:
            raw.extend(self._bookmark_parse_serial_text(str((row or {}).get('serial') or '').strip()))
        serials=self._bookmark_resolve_deliverable_serials(raw)
        if not serials:
            return self._set_bookmark_status('Selected entries did not resolve to any deliverable serials.', log_global=True)
        payload={'serial_text':'\n'.join(serials)}
        aid={'selected':'give_serial_selected','all':'give_serial_all','nonhost':'give_serial_nonhost'}[mode]
        self.log(f'Delivering {len(serials)} bookmarked serial(s) to {mode}...')
        def work():
            try:
                if mode == 'selected':
                    ok, msg = self._set_bridge_target_from_field('bookmark_target_player', 'Serial Bookmarks Target')
                    if not ok:
                        self.after(0, lambda m=msg:self._set_bookmark_status(m, log_global=True))
                        return
                res=http_json('POST','/action',{'action':aid,'payload':payload,'timeout':10.0},timeout=18.0)
                self.after(0, lambda:self._set_bookmark_status(res.get('message') or 'Bookmark delivery requested.', log_global=True))
                self.after(0, self.poll_status)
            except Exception as exc:
                self.after(0, lambda:self._set_bookmark_status('Bookmark delivery failed: '+repr(exc), log_global=True))
        threading.Thread(target=work, daemon=True).start()

    def _serial_tools_import_source(self):
        for fid in ('serial_tools_serialized', 'serial_tools_deserialized', 'serial_tools_input', 'serial_input'):
            if hasattr(self, '_serial_tools_get_text'):
                text=self._serial_tools_get_text(fid)
            else:
                text=self.field_vars.get(fid, tk.StringVar(value='')).get()
            if str(text or '').strip():
                return str(text).strip()
        return ''

    def _save_current_bookmark(self, cur):
        rows=[self._normalize_bookmark_row(r) for r in self._load_bookmark_store()]
        if self.active_bookmark_id:
            for row in rows:
                if self._bookmark_id(row) == self.active_bookmark_id:
                    row.update({k:v for k,v in cur.items() if k != 'id' or v})
                    row['id']=self.active_bookmark_id
                    self._save_bookmark_store(rows)
                    self._refresh_serial_bookmarks_ui()
                    return False
        row=self._normalize_bookmark_row(cur)
        self.active_bookmark_id=self._bookmark_id(row)
        rows.append(row)
        self._save_bookmark_store(rows)
        self._refresh_serial_bookmarks_ui()
        return True

    def _bookmark_current_payload(self):
        self._ensure_bookmark_state()
        payload={
            'name': self.field_vars.get('bookmark_name',tk.StringVar()).get().strip(),
            'group': self.field_vars.get('bookmark_group',tk.StringVar()).get().strip() or 'Default',
            'serial': self.field_vars.get('bookmark_serial',tk.StringVar()).get().strip(),
        }
        if self.active_bookmark_id:
            payload['id']=self.active_bookmark_id
        return payload

    def _serial_bookmark_action_local(self, aid):
        self._ensure_bookmark_state()
        rows=self._load_bookmark_store(); cur=self._bookmark_current_payload()
        if aid=='serial_bookmark_new':
            self.active_bookmark_id=''
            self._set_bookmark_field('bookmark_name', '')
            self._set_bookmark_field('bookmark_group', 'Default')
            self._set_bookmark_field('bookmark_serial', '')
            lb=getattr(self, 'serial_bookmarks_listbox', None)
            if lb: lb.selection_clear(0,'end')
            self._refresh_serial_bookmarks_ui()
            self._set_bookmark_status('Ready for a new saved serial.')
            return
        if aid=='serial_bookmark_import':
            src=self._serial_tools_import_source()
            if not src:
                return self._set_bookmark_status('Serial Tools has no output/input to import.')
            self._set_bookmark_field('bookmark_serial', src)
            self._set_bookmark_status('Imported text from Serial Tools. Add a name/group, then save.')
            return
        if aid=='serial_bookmark_save':
            if not cur['name']:
                return self._set_bookmark_status('Name is required before saving.', log_global=True)
            if not cur['serial']:
                return self._set_bookmark_status('Serial is required before saving.', log_global=True)
            expanded=self._bookmark_parse_serial_text(cur['serial'])
            resolved=self._bookmark_resolve_deliverable_serials(expanded)
            if not resolved:
                return self._set_bookmark_status('Could not resolve the serial text into a deliverable serial.', log_global=True)
            created=self._save_current_bookmark(cur)
            self._set_bookmark_status(f"Saved {cur['name']}." if created else f"Updated {cur['name']}.")
            return
        if aid=='serial_bookmark_duplicate':
            active=self._bookmark_row_by_id(self.active_bookmark_id)
            if not active: return self._set_bookmark_status('Select a saved serial before duplicating.', log_global=True)
            self.active_bookmark_id=''
            self._set_bookmark_field('bookmark_name', ((active.get('name') or 'Serial').strip() or 'Serial')+' Copy')
            self._set_bookmark_field('bookmark_group', active.get('group') or 'Default')
            self._set_bookmark_field('bookmark_serial', active.get('serial') or '')
            self._refresh_serial_bookmarks_ui()
            return self._set_bookmark_status('Duplicated into a new unsaved entry. Review, then Save.')
        if aid=='serial_bookmark_delete':
            if not self.active_bookmark_id:
                return self._set_bookmark_status('No saved serial selected to delete.')
            before=len(rows)
            rows=[self._normalize_bookmark_row(r) for r in rows]
            deleted_id=self.active_bookmark_id
            rows=[r for r in rows if self._bookmark_id(r)!=deleted_id]
            self.checked_bookmark_ids.discard(deleted_id)
            self._save_bookmark_store(rows)
            self.active_bookmark_id=''
            self._set_bookmark_field('bookmark_name', '')
            self._set_bookmark_field('bookmark_group', 'Default')
            self._set_bookmark_field('bookmark_serial', '')
            self._refresh_serial_bookmarks_ui()
            return self._set_bookmark_status(f'Deleted {before-len(rows)} saved serial(s).')
        if aid=='serial_bookmark_copy':
            serial=cur['serial']
            if not serial: return self.log('No bookmark serial to copy.')
            self._copy_text_v13(serial,'bookmark serial')
            return

    def _codes_local_action(self, aid):
        if aid == 'codes_refresh_gzo':
            return self._refresh_gzo_catalog_async()
        if aid == 'codes_load_cache':
            return self._load_bl4_cache_local()
        if aid == 'codes_reload_lootlemon':
            return self._reload_bl4_lootlemon_cache_local()
        if aid=='codes_import_bookmarks':
            return self._import_selected_bl4_bookmarks()
        if aid == 'codes_mattmab_validation':
            return self._run_bl4_mattmab_validation_local()

    def _serial_tools_input_value(self):
        if hasattr(self, '_serial_tools_get_text'):
            text=self._serial_tools_get_text('serial_tools_input')
            if text:
                return text
            return self._serial_tools_get_text('serial_input')
        return self.field_vars.get('serial_tools_input', self.field_vars.get('serial_input', tk.StringVar(value=''))).get()

    def _serial_tools_set_status(self, message, *, log_message=None, log_global=True):
        if 'serial_tools_status' in self.field_vars:
            self.field_vars['serial_tools_status'].set(str(message or ''))
        if log_global:
            self.log(log_message if log_message is not None else message)

    def _serial_convert_local(self, auto=False):
        text = self._serial_tools_input_value()
        if 'serial_input' not in self.field_vars:
            self.field_vars['serial_input']=tk.StringVar(value='')
        self.field_vars['serial_input'].set(str(text or ''))
        try:
            res = convert_serial_tool(text)
        except Exception as exc:
            self._serial_tools_set_text('serial_tools_serialized', '')
            self._serial_tools_set_text('serial_tools_deserialized', '')
            self._serial_tools_set_text('serial_tools_parts_breakdown', '')
            self._serial_tools_set_status(f'Conversion failed: {exc}', log_global=False)
            return self.log(f'Serial Tools conversion failed: {exc!r}')
        if res.get('ok') != 'true':
            self._serial_tools_set_text('serial_tools_serialized', '')
            self._serial_tools_set_text('serial_tools_deserialized', '')
            self._serial_tools_set_text('serial_tools_parts_breakdown', '')
            status = res.get('message') or 'Conversion failed.'
            return self._serial_tools_set_status(status, log_global=False)
        self._serial_tools_set_text('serial_tools_deserialized', res.get('deserialized') or '')
        self._serial_tools_set_text('serial_tools_parts_breakdown', res.get('breakdown') or '')
        self._serial_tools_set_text('serial_tools_serialized', res.get('serialized') or '')
        self._serial_tools_set_status(res.get('message') or 'Converted successfully.', log_global=False)

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
            return self._codes_local_action(aid)
        if aid == 'validator_basic':
            return self._validator_validate_basic()
        if aid == 'validator_bulk':
            return self._validator_validate_bulk()
        if aid == 'validator_clear':
            return self._validator_clear()
        if aid == 'movement_apply_all':
            return self._movement_apply_now()
        if aid == 'movement_reset_all':
            return self._movement_reset_defaults(apply_now=True)
        if aid == 'movement_save_preset':
            return self._movement_save_preset_local()
        if aid == 'movement_load_saved':
            return self._movement_load_saved_preset_local(apply_now=True)
        if aid == 'movement_set_time':
            return self._movement_set_time_local()
        if aid == 'movement_reset_time':
            return self._movement_reset_time_local()
        if aid in ('movement_zero_vault','movement_delete_ground_items','movement_toggle_no_target','movement_toggle_noclip','movement_players_only','movement_infinite_jump_all_on','movement_infinite_jump_all_off'):
            return self._movement_bridge_action(aid)
        if aid == 'movement_infinite_jump_toggle_selected':
            return self._movement_infinite_jump_selected(None)
        if aid == 'movement_infinite_jump_selected_on':
            return self._movement_infinite_jump_selected(True)
        if aid == 'movement_infinite_jump_selected_off':
            return self._movement_infinite_jump_selected(False)
        if aid.startswith('movement_preset_'):
            return self._movement_apply_preset_local(aid.replace('movement_preset_', '', 1))
        if self._uses_global_target(aid):
            return self._run_action_with_global_target(action)
        if aid in ('set_backpack_bank_selected','set_backpack_bank_all'):
            action=dict(action); action['uses_fields']=['backpack_size','bank_size']
        if aid == 'local_legit_validate':
            return self._run_local_legit_validate()
        if aid == 'local_legit_build_base85':
            return self._run_local_legit_build_base85()
        if aid == 'legit_give_selected':
            return self._deliver_legit_build('selected')
        if aid == 'legit_give_all':
            return self._deliver_legit_build('all')
        if aid == 'legit_give_nonhost':
            return self._deliver_legit_build('nonhost')
        if aid == 'legit_apply_max_passives':
            return self._legit_apply_max_passives_local()
        if aid == 'legit_clear_parts':
            self.legit_selected_by_slot.clear()
            self.legit_rejected_part_lines=[]
            self._sync_legit_selected_text()
            self._clear_legit_outputs()
            self._set_legit_status('Cleared selected Legit Builder parts. Generated output cleared.')
            self._render_legit_slots()
            return
        # Ensure bridge build/give receives only selected part lines; root is already sent separately.
        if aid in ('legit_validate_build','legit_give_selected','legit_give_all'):
            self.field_vars['legit_selected_parts'].set('\n'.join(self._legit_selected_lines_without_root()))
        return super().run_action(action)

if __name__ == '__main__':
    App().mainloop()
