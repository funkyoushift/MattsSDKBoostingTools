"""AFK join queue. All game operations run on the existing bridge game tick."""
from __future__ import annotations

import time
import random
import hmac
import hashlib
import json
from collections import deque


BOOSTS = ("level", "spec", "sdu", "cash", "eridium", "keys", "vault_levels", "challenges", "uvhm", "cosmetics", "loot")
AMOUNT_LIMITS = {"level": 70, "spec": 701, "cash": 2147483647,
                 "eridium": 2147483647, "keys": 2147483647, "vault_levels": 9999}
JOIN_SETTLE_SECONDS = 20.0
STEP_LABELS = {'inventory_capture':'Saving original backpack', 'level':'Setting level',
               'spec':'Setting specialization rank', 'sdu':'Setting SDUs to 3225',
               'cash':'Setting cash', 'eridium':'Setting Eridium', 'keys':'Setting keys',
               'challenges':'Completing challenges', 'uvhm':'Unlocking UVHM 1-7',
               'vault_levels':'Setting vault card levels', 'cosmetics':'Unlocking cosmetics and vehicles', 'loot':'Delivering selected loot'}
RECOVERY_LABELS = {'prepared':'Preparing reward cleanup', 'clear_pending':'Clearing reward clutter',
                   'deliver_pending':'Delivering selected loot', 'restore_pending':'Returning original backpack',
                   'verify_pending':'Checking backpack return', 'blocked':'Saving repair report',
                   'complete':'Backpack return verified'}
# Other SDK mods share Python's module-level random generator. Use OS entropy
# so another mod reseeding random cannot repeat AFK guest selections.
_loot_rng = random.SystemRandom()


class Lobby:
    def __init__(self, game):
        self.game = game
        self.enabled = False
        self.config = {}
        self.seen = []
        self.queue = deque()
        self.current = None
        self.completed = []
        self.session_joins = 0
        self.lifetime_joins = None
        self.counter_error = ""
        self.counted = []
        self.history = deque(maxlen=40)
        self.world = None
        self.next_tick = 0.0
        self.message = "Stopped."
        self.shared_completed = []

    def stop(self):
        if self.current:
            self._interrupt_job(self.current, 'Operator stopped AFK; unfinished work saved for review.')
        self.enabled = False
        self.current = None
        self.queue.clear()
        self.completed.clear()
        self.seen.clear()
        self.shared_completed.clear()
        self.message = "Stopped. Already applied boosts are kept."
        return {"ok": True, "message": self.message, "afk_lobby": self.status()}

    def start(self, payload):
        if self.enabled:
            return {"ok": False, "message": "Stop AFK Lobby before changing its selections."}
        config = {key: payload.get(key) is True for key in BOOSTS}
        config['test_host'] = payload.get('test_host') is True
        config["auto_accept"] = payload.get("auto_accept", True) is True
        config["auto_kick"] = payload.get("auto_kick", False) is True
        if config['test_host']:
            config['auto_accept'] = False
            config['auto_kick'] = False
        config['cleanup_rewards'] = payload.get('cleanup_rewards') is True
        if config['cleanup_rewards']:
            if not (config['challenges'] or config['uvhm']):
                return {'ok':False,'message':'Select challenges or UVHM to use reward cleanup.'}
        config["loot_mode"] = payload.get("loot_mode", "all")
        if config["loot_mode"] not in ("all", "random70"):
            return {"ok": False, "message": "Choose all loot or a random selection."}
        if not any(config[key] for key in BOOSTS):
            return {"ok": False, "message": "Select at least one boost."}
        try:
            names = payload.get("kick_exempt_names", "")
            if not isinstance(names, str) or len(names) > 8192:
                raise ValueError("Protected SHiFT names must be text, one name per line (up to 8,192 characters).")
            config["kick_exempt_names"] = "\n".join(dict.fromkeys(name.strip() for name in names.splitlines() if name.strip()))
            for key, maximum in AMOUNT_LIMITS.items():
                value = payload.get(key + "_amount", maximum)
                if isinstance(value, bool) or not str(value).isdigit() or not 1 <= int(value) <= maximum:
                    raise ValueError(f"{key} amount must be a whole number from 1 to {maximum}.")
                config[key + "_amount"] = int(value)
            config["serial_override_level"] = payload.get("serial_override_level") is True
            item_level = payload.get("serial_level", 70)
            if config["serial_override_level"] and (isinstance(item_level, bool) or not str(item_level).isdigit() or not 1 <= int(item_level) <= 70):
                raise ValueError("Item level must be a whole number from 1 to 70.")
            config["serial_level"] = int(item_level) if config["serial_override_level"] else 70
            count = payload.get("random_count", 70)
            if isinstance(count, bool) or not str(count).isdigit() or int(count) < 1:
                raise ValueError("Random delivery size must be a positive whole number.")
            config["random_count"] = int(count)
            config["serials"] = self.game.prepare_loot(payload) if config["loot"] else []
            config["loot_classes"] = self.game.classify_loot(config["serials"]) if config["loot"] else []
            config["guaranteed_serials"] = (self.game.prepare_loot({**payload, "codes": payload["guaranteed_codes"]})
                                             if config["loot"] and payload.get("guaranteed_codes", "").strip() else [])
            config["guaranteed_classes"] = self.game.classify_loot(config["guaranteed_serials"]) if config["guaranteed_serials"] else []
            if config["loot"] and not config["serials"] and not config["guaranteed_serials"]:
                raise ValueError("Select bookmarks or paste valid item codes for loot.")
            config["bulk_loot_authorized"] = False
            maximum = len(config["guaranteed_serials"]) + (len(config["serials"]) if config["loot_mode"] == "all" else 0)
            if config["loot_mode"] == "random70":
                maximum = max(len(config["guaranteed_serials"]), min(config["random_count"], len(config["guaranteed_serials"]) + len(config["serials"])))
            if config["loot"] and maximum > 70:
                password = payload.get("bulk_loot_password")
                if not self.game.authorize_bulk_loot(password):
                    return {"ok": False, "password_required": True, "password_kind": "bulk_loot",
                            "message": "Sending more than 70 items per guest requires the password. Choose 70 or fewer items or enter the password."}
                config["bulk_loot_authorized"] = True
            if not self.game.is_host():
                raise ValueError("Load your character and host the lobby first.")
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
        self.stop()
        self.config = config
        self.game.test_host = config['test_host']
        self.session_joins = 0
        self.counted = []
        self._load_counter()
        self.world = None
        self.history.clear()
        self.enabled = True
        self.next_tick = 0
        self.message = "Host test: waiting for your character." if config['test_host'] else "Running. Waiting for guests."
        return {"ok": True, "message": self.message, "afk_lobby": self.status()}

    def _load_counter(self):
        if self.lifetime_joins is None and not self.counter_error:
            try:
                self.lifetime_joins = getattr(self.game, "load_join_count", lambda: 0)()
            except Exception as exc:
                self.counter_error = str(exc)
    def status(self):
        self._load_counter()
        current = self.current
        return {"enabled": self.enabled, "auto_accept": self.enabled and self.config.get("auto_accept", False),
                "message": self.message, "queued": [row["name"] for row in self.queue],
                "current": {"name": current["name"], "step": current.get("step", "Waiting for character")} if current else None,
                "history": list(self.history), "config": self.config,
                "session_joins": self.session_joins, "lifetime_joins": self.lifetime_joins, "counter_error": self.counter_error,
                "awaiting_kick": [job["name"] for job in self.completed if not job.get("kick_attempted") and not job.get("failed")],
                "loot_modes": ["all", "random70"], "bulk_loot_password_required": True, "random_count_supported": True, "guaranteed_loot_supported": True,
                'cleanup_rewards_supported':True, 'host_test_supported':True,
                'config_upload_supported': True, 'item_level_override_supported': True,
                'boost_amounts_supported': True, 'kick_exempt_names_supported': True, 'vault_card_levels_supported': True}

    def tick(self):
        now = time.monotonic()
        if not self.enabled or now < self.next_tick:
            return
        self.next_tick = now + 0.25
        world, rows = self.game.roster()
        if world != self.world:
            if self.current:
                self._interrupt_job(self.current, 'World changed; unfinished work saved for review.')
            self.current = None
            self.queue.clear()
            self.completed.clear()
            self.seen.clear()
            self.shared_completed.clear()
            self.world = world
        if world is None or not self.game.is_host():
            self.message = "Waiting for the host's world."
            return
        tokens = [row["token"] for row in rows]
        def still_ready(member):
            return any(row['token'] == member['token'] and row['pc'] == member['pc']
                       and row['ready'] for row in rows)
        self.shared_completed = [entry for entry in self.shared_completed if still_ready(entry)]
        if self.current and self.current.get('shared_run'):
            run = self.current['shared_run']
            run['members'] = [member for member in run['members'] if still_ready(member)]
        self.counted = [token for token in self.counted if token in tokens]
        for token in ([] if self.config.get('test_host') else tokens):
            if token not in self.counted:
                self.counted.append(token)
                self.session_joins += 1
                if self.lifetime_joins is not None:
                    self.lifetime_joins += 1
                    try:
                        getattr(self.game, "save_join_count", lambda count: None)(self.lifetime_joins)
                        self.counter_error = ""
                    except Exception as exc:
                        self.counter_error = str(exc)
        self.completed = [job for job in self.completed if job["token"] in tokens]
        self.seen = [token for token in self.seen if token in tokens]
        self.queue = deque(row for row in self.queue if row["token"] in tokens)
        for row in rows:
            if row["token"] not in self.seen:
                self.seen.append(row["token"])
                steps = [key for key in BOOSTS if self.config[key]]
                if self.config.get('cleanup_rewards'):
                    steps = ['inventory_capture'] + [key for key in steps if key != 'loot'] + ['inventory_recovery']
                self.queue.append(dict(row, steps=deque(steps), results=[]))
        if self.current and self.current["token"] not in tokens:
            self._interrupt_job(self.current, 'Left lobby; unfinished steps cancelled.')
            self.current = None
        self._flush_kicks(rows, now)
        if not self.current:
            # A guest still loading must not block other ready guests.
            for job in self.queue:
                row = next(row for row in rows if row["token"] == job["token"])
                if row["ready"]:
                    self.current = job
                    self.queue.remove(job)
                    break
        if not self.current:
            self.message = "Waiting for joining characters." if self.queue else "Running. Waiting for guests."
            if not self.queue and any(not j.get("kick_attempted") for j in self.completed):
                self.message = "Waiting for loot settlement and all connection members before auto-kick."
            return
        job = self.current
        row = next(row for row in rows if row["token"] == job["token"])
        if not row["ready"]:
            if now - job.setdefault('not_ready_since', now) >= 120:
                self.game.cancel(job)
                job['results'].append({'ok':False, 'step':job.get('step', 'ready'),
                                       'message':'Character remained unavailable for 120 seconds; unfinished work saved for review.'})
                job['steps'].clear()
                self._complete_job(job, rows, now)
                return
            self.message = f"Waiting for {job['name']}'s character."
            return
        job.pop('not_ready_since', None)
        job.update(row)
        if not job["steps"]:
            self._complete_job(job, rows, now)
            return
        step = job["steps"][0]
        job["step"] = step
        recovery = job.get('inventory_recovery')
        label = (RECOVERY_LABELS.get(recovery.record['phase'], 'Checking backpack')
                 if step == 'inventory_recovery' and recovery else STEP_LABELS.get(step, step))
        self.message = f"{job['name']}: {label}"
        if step in ('challenges', 'uvhm'):
            if any(entry['token'] == job['token'] and entry['pc'] == job['pc']
                   and entry['step'] == step for entry in self.shared_completed):
                job['results'].append({'ok': True, 'step': step, 'shared_run': True,
                                       'message': 'Present and ready for a complete successful lobby run; duplicate skipped. Guest save not confirmed.'})
                job['steps'].popleft()
                return
            if 'shared_run' not in job:
                # Back up other ready guests before the lobby-wide rewards start.
                # Late/loading guests are not credited for this run.
                for pending in self.queue:
                    member = next((r for r in rows if r['token'] == pending['token'] and r['ready']), None)
                    if member is None or not pending['steps'] or pending['steps'][0] != 'inventory_capture':
                        continue
                    pending.update(member)
                    self.message = f"Backing up {pending['name']} before shared {step}"
                    try:
                        captured = self.game.step('inventory_capture', pending, self.config)
                    except Exception as exc:
                        captured = {'ok': False, 'message': str(exc)}
                    if captured is not None:
                        self._finish_step(pending, 'inventory_capture', captured)
                    return
                job['shared_run'] = {'step': step, 'members': [
                    {'token': r['token'], 'pc': r['pc']} for r in rows if r['ready']]}
        try:
            result = self.game.step(step, job, self.config)
        except Exception as exc:
            getattr(self.game, 'cancel_step', lambda job, step: self.game.cancel(job))(job, step)
            result = {"ok": False, "message": str(exc)}
        if result is not None:
            run = job.pop('shared_run', None)
            if run and result['ok']:
                for member in run['members']:
                    if not any(entry['token'] == member['token'] and entry['pc'] == member['pc']
                               and entry['step'] == run['step'] for entry in self.shared_completed):
                        self.shared_completed.append(dict(member, step=run['step']))
            self._finish_step(job, step, result)

    def _interrupt_job(self, job, reason):
        self.game.cancel(job)
        job['results'].append({'ok':False, 'step':job.get('step','ready'), 'message':reason})
        job['record'] = {'name':job['name'], 'message':reason, 'results':job['results'],
                         'unfinished_steps':list(job['steps'])}
        self._save_report(job)
        self.history.appendleft(job['record'])

    def _complete_job(self, job, rows, now):
        failed = any(not result['ok'] for result in job['results'])
        message = 'Run ended with errors; review details' if failed else 'All selected actions finished'
        if any(result.get('cleanup_skipped') for result in job['results']):
            message += '; reward cleanup skipped, original backpack untouched'
        record = {'name':job['name'], 'message':message, 'results':job['results']}
        job['record'] = record
        if self.config.get('auto_kick'):
            job['kick_after'] = now + (15.0 if self.config.get('loot') or self.config.get('cleanup_rewards') else 0.0)
            job['failed'] = failed
            self.completed.append(job)
            record['message'] += '; auto-kick pending settlement and connection members'
        self._save_report(job)
        self.history.appendleft(record)
        self._flush_kicks(rows, now)
        self.current = None

        if self.config.get('test_host'):
            self.enabled = False
            self.queue.clear()
            self.message = 'Host test finished. ' + record['message'] + '; host is not kicked.'

    def _save_report(self, job):
        try:
            save = getattr(self.game, 'save_run_report', None)
            if save:
                job['record']['report_path'] = save(job)
        except Exception as exc:
            job['record']['report_error'] = 'Could not save run report: ' + str(exc)

    def _finish_step(self, job, step, result):
        if step == 'inventory_recovery' and not result['ok'] and result.get('nothing_cleared'):
            # Selected boosts already ran. Do not repeat lobby-wide challenges
            # or omit loot just because cleanup stopped before deletion.
            job['steps'].popleft()
            if self.config.get('loot'):
                job['steps'].appendleft('loot')
            result = dict(result, ok=True, cleanup_skipped=True,
                          message='Cleanup skipped before deletion; original backpack untouched. '
                                  'Continuing selected loot. ' + result.get('message', ''))
        elif step == 'inventory_capture' and not result['ok']:
            # Nothing has been cleared yet. Preserve the backpack and run
            # the ordinary boost/loot path rather than dropping every step.
            result = dict(result, ok=True, cleanup_skipped=True,
                          message="Reward cleanup skipped; original backpack untouched. "
                                  + result.get('message', '')
                                  + ". Continuing selected boosts and loot without cleanup.")
            job['steps'] = deque(key for key in BOOSTS if self.config[key])
        else:
            job["steps"].popleft()
        job["results"].append(dict(result, step=step))

    def _flush_kicks(self, rows, now):
        if not self.config.get("auto_kick"):
            return
        unknown = any(row.get("connection") is None for row in rows)
        for job in self.completed:
            if job.get("kick_attempted"):
                continue
            row = next((r for r in rows if r["token"] == job["token"]), None)
            if row is None:
                continue
            members = rows if unknown else [r for r in rows if r.get("connection") == row.get("connection")]
            protected = {name.casefold() for name in self.config.get("kick_exempt_names", "").splitlines()}
            if any(str(member.get("name", "")).strip().casefold() in protected for member in members):
                job['kick_attempted'] = True
                job['record']['message'] += '; player kept: protected SHiFT name or shared connection'
                self._save_report(job)
                continue
            done = []
            for member in members:
                finished = next((j for j in self.completed if j["token"] == member["token"]), None)
                if finished is None or now < finished["kick_after"]:
                    break
                done.append(finished)
            else:
                # Unknown grouping uses a lobby-wide barrier but still requests
                # each guest's kick; known shared connections need only one.
                targets = [job] if unknown else done
                try:
                    result = self.game.kick(dict(job, pc=row["pc"], index=row["index"]))
                except Exception as exc:
                    result = {"ok": False, "message": str(exc)}
                for target in targets:
                    target['kick_attempts'] = target.get('kick_attempts', 0) + 1
                    target['kick_attempted'] = bool(result['ok']) or target['kick_attempts'] >= 3
                    if not result['ok']:
                        target['kick_after'] = now + 5.0
                    target["results"].append(dict(result, step="auto_kick"))
                    prefix = ('Run ended with errors; needs review; ' if any(
                        not r['ok'] and r.get('step') != 'auto_kick' for r in target['results']) else 'All selected actions finished; ')
                    target["record"]["message"] = prefix + (
                        "connection kick requested" if result["ok"] else
                        "kick failed after 3 attempts; player kept" if target['kick_attempted'] else "retrying kick in 5 seconds")
                    self._save_report(target)



class Game:
    @staticmethod
    def save_run_report(job):
        import os
        import uuid
        from pathlib import Path
        from datetime import datetime, timezone
        folder = Path(os.environ['LOCALAPPDATA']) / 'MattsSDKBoostingTools' / 'afk-run-reports'
        folder.mkdir(parents=True, exist_ok=True)
        path = Path(job.setdefault('run_report_path', str(folder / (uuid.uuid4().hex + '.json'))))
        recovery = job.get('inventory_recovery')
        report = dict(job['record'], updated_at_utc=datetime.now(timezone.utc).isoformat(),
                      recovery_backup=str(recovery.path) if recovery else None,
                      selected_loot=list(job.get('loot_selection', [])),
                      guest_save_verified=False)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporary, path)
        return str(path)

    def __init__(self):
        self.ready_since = {}
        self.ready_world = None

    def load_join_count(self):
        from .afk_join_stats import JoinStats
        self.join_stats = JoinStats()
        return self.join_stats.load()

    def save_join_count(self, count):
        self.join_stats.save(count)

    @staticmethod
    def connection_root(pc):
        # Native schema: PlayerController.NetConnection (1661696),
        # ChildConnection.Parent (1594386), NetConnection.Children (1648275).
        try:
            connection = pc.NetConnection
            if connection is None:
                return None
            parent = getattr(connection, "Parent", None)
            return parent if parent is not None else connection
        except Exception:
            return None

    def character_ready(self, ps, pc, pawn):
        if pc is None or pawn is None:
            self.ready_since.pop(ps, None)
            return False
        now = time.monotonic()
        previous = self.ready_since.get(ps)
        if previous is None or previous[0] != pc or previous[1] != pawn:
            self.ready_since[ps] = (pc, pawn, now)
            return False
        return now - previous[2] >= JOIN_SETTLE_SECONDS

    @staticmethod
    def progression_loaded(ps, pawn):
        # The host can see a pawn before the guest's save data arrives. These
        # are the same containers used by the existing XP and SDU actions.
        # Check initialization only, never whether the guest needs a boost.
        try:
            pools = pawn.GbxProgressionManager.ProgressPointsContainer.PointsAcquiredPerPool
            return len(pools) > 2 and len(ps.ExperienceState) >= 2
        except Exception:
            return False

    @staticmethod
    def backend():
        from . import backend_actions
        return backend_actions

    def is_host(self):
        a = self.backend()
        return a.get_pc() is not None and a._challenge_is_host()[0]

    def roster(self):
        a = self.backend()
        world, gs = a._gbc_session_world_and_gamestate()
        if world != self.ready_world or world is None or gs is None:
            self.ready_since.clear()
            self.ready_world = world
        if world is None or gs is None:
            return None, []
        from .party_helpers import _gbc_resolve_player_display_name
        local = a.get_pc()
        local_ps = getattr(local, "PlayerState", None)
        rows = []
        present = []
        for index, ps in enumerate(getattr(gs, "PlayerArray", []) or []):
            host_test = getattr(self, 'test_host', False)
            if ps is None or (ps != local_ps if host_test else ps == local_ps):
                continue
            pc = local if host_test else a._gbc_find_pc_for_player_state(ps, world)
            if pc == local and not host_test:
                continue
            present.append(ps)
            pawn = a.player_economy._target_character_for_pc(pc) if pc is not None else None
            if not self.progression_loaded(ps, pawn):
                pawn = None
            # Loading can replace a pawn without an intervening empty roster.
            # Give this exact character time to initialize progression/replication.
            ready = self.character_ready(ps, pc, pawn)
            rows.append({"token": ps, "pc": pc, "index": index,
                         "name": _gbc_resolve_player_display_name(ps), "ready": ready, "connection": self.connection_root(pc)})
        self.ready_since = {ps: since for ps, since in self.ready_since.items() if ps in present}
        return world, rows

    def authorize_bulk_loot(self, password=None):
        return self.backend()._installation_authorized(password)

    def prepare_loot(self, payload):
        a = self.backend()
        raw = a._parse_serial_text(payload.get("codes", ""))
        serials = a.serial_rewards._resolve_give_serial_strings(raw) if raw else []
        if len(serials) != len(raw):
            raise ValueError("One or more item codes could not be resolved. Check the loot list.")
        if payload.get("serial_override_level") is True:
            serials, _changed, failures = a._serials_with_level_override(serials, True, int(payload.get("serial_level", 70)))
            if failures:
                raise ValueError("Could not override item level: " + "; ".join(failures[:3]))
        return serials

    @staticmethod
    def classify_loot(serials):
        from . import afk_loot
        return afk_loot.classify_serials(serials)

    def guest_class(self, job):
        from . import afk_loot
        pawn = self.backend().player_economy._target_character_for_pc(job["pc"])
        return afk_loot.player_class(job["pc"], job["token"], pawn)

    @staticmethod
    def loot_for_guest(job, config):
        if "loot_selection" not in job:
            pool = config["serials"]
            if "loot_classes" in config:
                from . import afk_loot
                job["loot_selection"], job["loot_excluded"] = afk_loot.select_loot(
                    pool, config["loot_classes"], job.get("character_class"),
                    config.get("loot_mode") == "random70", _loot_rng,
                    config.get("guaranteed_serials", []), config.get("guaranteed_classes", []), config.get("random_count", 70))
            else:
                job["loot_selection"] = (_loot_rng.sample(pool, min(config.get("random_count", 70), len(pool)))
                                         if config.get("loot_mode") == "random70" else list(pool))
            # Hash the contents, not their order, so identical sets have the
            # same ID. Keep codes out of the activity log.
            contents = json.dumps(sorted(job["loot_selection"]), ensure_ascii=True).encode("utf-8")
            job["loot_selection_id"] = hashlib.sha256(contents).hexdigest()[:12]
        return job["loot_selection"]

    def experience_level(self, ps, step):
        economy = self.backend().player_economy
        index = (int(step.rsplit("_", 1)[1]) + 1 if step.startswith("vaultcard_xp_")
                 else 0 if step == "level" else 1)
        states = getattr(ps, "ExperienceState", [])
        row = states[index] if len(states) > index else None
        for token in economy._candidate_experience_tokens(index, row):
            ptr = economy._make_experience_def_ptr(token)
            if ptr is not None:
                return int(ps.BP_GetExperienceLevel(ptr))
        return None

    def kick(self, job):
        a = self.backend()
        if getattr(self, 'test_host', False):
            return {'ok': False, 'message': 'The host cannot be auto-kicked.'}
        if not self.is_host():
            return {"ok": False, "message": "Not hosting; kick skipped."}
        _world, rows = self.roster()
        row = next((row for row in rows if row["token"] == job["token"]), None)
        if row is None:
            return {"ok": False, "message": "Guest already left."}
        ok = a._kick_party_player_by_index(row["index"], "AFK boosting complete")
        return {"ok": bool(ok), "message": "Boosting finished; kick requested." if ok else "Kick failed."}

    def cancel(self, job):
        a = self.backend()
        recovery = job.get('inventory_recovery')
        if recovery and not recovery.can_kick and not recovery.cancel_before_clear():
            # Finish an already-started return even if the operator stops AFK.
            # Departed guests fail identity checks and retain their journal.
            a._afk_inventory_recovery = recovery
            a._afk_inventory_recovery_adapter = job['inventory_adapter']
        self.cancel_step(job, None)

    def cancel_step(self, job, step):
        # A failed boost must not transfer the same prepared recovery to the
        # background while the lobby still owns and will advance it.
        a = self.backend()
        job.pop("uvhm_plan", None)
        job.pop("uvhm_next_at", None)
        seq = job.pop("serial_job", None)
        if seq is not None:
            cancel_direct = getattr(a.serial_rewards, '_cancel_direct_sequence', None)
            if cancel_direct:
                cancel_direct(seq, 'AFK step interrupted; remaining items retained in the delivery report.')
            a.serial_rewards._pending_serial_delivery_sequences[:] = [s for s in a.serial_rewards._pending_serial_delivery_sequences if s is not seq]
        owned = job.pop("challenge_owned", None)
        if owned is not None and owned is a._challenge_queue:
            a.complete_challenges_cancel()

    def step(self, step, job, config):
        a = self.backend()
        pc, ps = job["pc"], job["token"]
        ok = False
        if step == 'inventory_capture':
            import os
            from pathlib import Path
            from .afk_inventory_capture import Capture
            from .afk_inventory_recovery import Recovery
            from .afk_inventory_native_recovery import NativeAdapter
            directory = Path(os.environ['LOCALAPPDATA']) / 'MattsSDKBoostingTools' / 'inventory-recovery'
            capture = job.get('inventory_capture')
            if capture is None:
                capture = job['inventory_capture'] = Capture(ps)
                job['capture_deadline'] = time.monotonic()+300
            if time.monotonic() >= job['capture_deadline']:
                return {'ok':False,'message':'Original inventory capture timed out; no boosts applied'}
            if time.monotonic() < job.get('capture_retry_after', 0):
                return None
            status = capture.step(ps)
            if not status['done']:
                return None
            original = capture.snapshot() if status['ok'] else None
            if not status['ok'] or not original['rows']:
                if job.get('capture_retries', 0) < 5:
                    job['capture_retries'] = job.get('capture_retries', 0) + 1
                    job['inventory_capture'] = Capture(ps)
                    job['capture_retry_after'] = time.monotonic() + 2
                    return None
                return {'ok':False,'message':status['error'] if not status['ok'] else
                        'Inventory is still empty after loading retries; no boosts or cleanup applied'}
            if any(r['quantity'] != 1 for r in original['rows']):
                return {'ok':False,'message':'Stacked inventory restoration is unsupported; no boosts applied'}
            selected = []
            if config.get('loot'):
                if any(value not in (None,'unknown_item') for value in config.get('loot_classes',[])):
                    character = self.guest_class(job)
                    if not character:
                        return None
                    job['character_class'] = character
                selected = self.loot_for_guest(job,config)
                if len(selected)>70 and not config.get('bulk_loot_authorized'):
                    return {'ok':False,'message':'New loot above 70 requires password authorization'}
            world,_rows = self.roster()
            job['inventory_recovery'] = Recovery(directory,original,player_token=ps,world_token=world,
                guest_name=job['name'],delivery_serials=selected,restore_metadata=False)
            job['inventory_adapter'] = NativeAdapter(self,ps,world,allow_afk=True,open_rewards=True)
            return {'ok':True,'message':f"Saved {len(original['rows'])} original inventory entries"}
        elif step == 'inventory_recovery':
            recovery = job['inventory_recovery']
            world,_rows = self.roster()
            recovery.advance(ps,world,job['inventory_adapter'])
            if recovery.record['phase'] == 'blocked':
                report = recovery.path.parent / 'saved-item-lists' / recovery.path.stem / 'RECOVERY-REVIEW.txt'
                return {'ok':False, 'recovery_report':str(report),
                        'review_kick_allowed':recovery.record.get('review_kick_allowed') is True and report.is_file(),
                        'nothing_cleared':recovery.record.get('nothing_cleared') is True,
                        'message':recovery.record['error'].replace('kick blocked', 'repair needed')+'; AFK continues; manual repair report: '+str(report)}
            if not recovery.can_kick:
                return None
            return {'ok':True,'message':'Reward loot cleared; selected loot and all original items verified'}
        elif step in ("level", "spec", "vault_levels"):
            now = time.monotonic()
            tracks = ([f"vaultcard_xp_{i}" for i in range(1, 6)] if step == "vault_levels" else [step])
            target = config.get(step + "_amount", AMOUNT_LIMITS[step])
            pending = False
            for track in tracks:
                state = job.setdefault("experience_attempts", {}).setdefault(track, {"started": now})
                if now < state.get("check_after", 0):
                    pending = True
                    continue
                actual = self.experience_level(ps, track)
                if actual is not None and actual >= target:
                    job.setdefault("expected_experience", {})[track] = actual
                    continue
                if now - state["started"] >= 30.0:
                    return {"ok": False, "message": f"{track}: expected {target}, host readback {actual}; player kept in lobby."}
                token = "player" if track == "level" else "specialization" if track == "spec" else track
                a._set_experience_on_ps(ps, token, target)
                state["check_after"] = now + 2.0
                pending = True
            if pending:
                return None
            return {"ok": True, "message": f"Host readback at or above target {target}; higher levels kept. Guest save not confirmed."}
        elif step == "sdu":
            now = time.monotonic()
            started = job.setdefault("sdu_started", now)
            if now < job.get("sdu_retry_after", 0):
                return None
            ok = a.player_economy._set_max_sdu_points_on_pc(pc)
            if not ok:
                if now - started < 30.0:
                    job["sdu_retry_after"] = now + 2.0
                    return None
                return {"ok": False, "message": "SDU data/write unavailable after 30 seconds; player kept in lobby."}
        elif step in ("cash", "eridium"):
            ok = a._give_currency_to_pc(pc, step, config.get(step + "_amount", a.MAX_WALLET_AMOUNT))
        elif step == "keys":
            results = [a._give_currency_to_pc(pc, f"vaultcard{i}", config.get("keys_amount", a.MAX_WALLET_AMOUNT)) for i in range(1, 6)]
            ok = all(results)
        elif step == "cosmetics":
            pc.ServerActivateDevPerk(4)
            return {"ok": True, "message": "All Customs + Hovers requested; guest save not confirmed."}
        elif step == "uvhm":
            # Use the existing tier plan and pacing, but keep this guest's work
            # private: the manual queue can add targets or be replaced/resumed.
            if a.uvh_boost_status()["active"]:
                return None
            now = time.monotonic()
            if now < job.get("uvhm_next_at", 0):
                return None
            if "uvhm_plan" not in job:
                plan = a._uvh_build_plan(list(range(len(a.UVH_RANKS))))
                if not plan:
                    return {"ok": False, "message": "No UVHM tier steps available."}
                job["uvhm_plan"] = deque(plan)
            plan = job["uvhm_plan"]
            if not plan:
                job.pop("uvhm_plan", None)
                job.pop("uvhm_next_at", None)
                return {"ok": True, "message": "UVHM 1â€“7 steps sent; guest save not confirmed."}
            _label, challenge, delay = plan[0]
            pc.ServerIncrementChallengeForPlayer(challenge, 1)
            plan.popleft()
            # Also wait after the last tier before allowing auto-kick.
            job["uvhm_next_at"] = now + delay
            return None
        elif step == "challenges":
            if "challenge_owned" in job:
                if job["challenge_owned"] is not a._challenge_queue:
                    job.pop("challenge_owned", None)
                    return {"ok": False, "message": "Challenge run replaced by another action."}
                status = a.complete_challenges_status()
                if status["active"]:
                    return None
                job.pop("challenge_owned", None)
                return {"ok": status["steps_done"] == status["steps_total"] and status["failed_count"] == 0,
                        "message": status["message"]}
            if a.complete_challenges_status()["active"]:
                return None
            result = a._challenge_queue_start(a._challenge_rows_for_category("All non-UVHM"), label="AFK challenges", targets=[pc])
            if result["ok"]:
                job["challenge_owned"] = a._challenge_queue
                return None
            return result
        elif step == "loot":
            rewards = a.serial_rewards
            seq = job.get("serial_job")
            if seq is not None:
                if any(s is seq for s in rewards._pending_serial_delivery_sequences):
                    return None
                job.pop("serial_job", None)
                selection_note = f"Selection {job.get('loot_selection_id', 'unknown')}: {len(job.get('loot_selection', []))} items; class {job.get('character_class') or 'not required'}; {job.get('loot_excluded', 0)} incompatible/unknown entries excluded. "
                return {"ok": seq.get("index", 0) >= len(seq["chunks"]) and not seq.get("afk_error"),
                        "message": selection_note + (seq.get("afk_error") or rewards.serial_delivery_status())}
            if rewards._serial_delivery_busy():
                return None
            if "loot_classes" in config and any(value not in (None, "unknown_item") for value in config["loot_classes"]):
                character = self.guest_class(job)
                if not character:
                    if time.monotonic() - job.setdefault('loot_class_wait', time.monotonic()) >= 30:
                        return {'ok':False, 'message':'Character class unavailable after 30 seconds; loot not sent, saved for review.'}
                    job["step"] = "Waiting for character class before loot"
                    return None
                if job.get("character_class") != character:
                    job.pop("loot_selection", None)
                job["character_class"] = character
            selected = self.loot_for_guest(job, config)
            if len(selected) > 70 and not config.get("bulk_loot_authorized"):
                return {"ok": False, "message": "More than 70 items requires password authorization. Stop and restart AFK with the password."}
            rewards._do_give_serial_to_player_indices(selected, [job["index"]], scope_label=f"AFK: {job['name']} ({len(selected)} items; selection {job['loot_selection_id']})", mode="selected",
                **({"bulk_authorized": True} if config.get("bulk_loot_authorized") else {}))
            seq = rewards._pending_serial_delivery_sequences[-1]
            seq["afk_player_state"] = ps
            if 'direct_delivery' not in seq:
                seq["post_open_delay"] = max(float(seq.get("post_open_delay", 0)), 3.0)
            job["serial_job"] = seq
            return None
        return {"ok": bool(ok), "message": "Applied" if ok else "Action reported failure"}


lobby = Lobby(Game())
