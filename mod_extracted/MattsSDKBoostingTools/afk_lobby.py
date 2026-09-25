"""AFK join queue. All game operations run on the existing bridge game tick."""
from __future__ import annotations

import time
from collections import deque


BOOSTS = ("level", "spec", "sdu", "cash", "eridium", "keys", "challenges", "loot")


class Lobby:
    def __init__(self, game):
        self.game = game
        self.enabled = False
        self.config = {}
        self.seen = []
        self.queue = deque()
        self.current = None
        self.history = deque(maxlen=40)
        self.world = None
        self.next_tick = 0.0
        self.message = "Stopped."

    def stop(self):
        if self.current:
            self.game.cancel(self.current)
        self.enabled = False
        self.current = None
        self.queue.clear()
        self.seen.clear()
        self.message = "Stopped. Already applied boosts are kept."
        return {"ok": True, "message": self.message, "afk_lobby": self.status()}

    def start(self, payload):
        if self.enabled:
            return {"ok": False, "message": "Stop AFK Lobby before changing its selections."}
        config = {key: payload.get(key) is True for key in BOOSTS}
        config["auto_accept"] = payload.get("auto_accept", True) is True
        config["auto_kick"] = payload.get("auto_kick", False) is True
        if not any(config[key] for key in BOOSTS):
            return {"ok": False, "message": "Select at least one boost."}
        try:
            config["serials"] = self.game.prepare_loot(payload) if config["loot"] else []
            if config["loot"] and not config["serials"]:
                raise ValueError("Select bookmarks or paste valid item codes for loot.")
            if not self.game.is_host():
                raise ValueError("Load your character and host the lobby first.")
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
        self.stop()
        self.config = config
        self.world = None
        self.history.clear()
        self.enabled = True
        self.next_tick = 0
        self.message = "Running. Waiting for guests."
        return {"ok": True, "message": self.message, "afk_lobby": self.status()}

    def status(self):
        current = self.current
        return {"enabled": self.enabled, "auto_accept": self.enabled and self.config.get("auto_accept", False),
                "message": self.message, "queued": [row["name"] for row in self.queue],
                "current": {"name": current["name"], "step": current.get("step", "Waiting for character")} if current else None,
                "history": list(self.history), "config": self.config}

    def tick(self):
        now = time.monotonic()
        if not self.enabled or now < self.next_tick:
            return
        self.next_tick = now + 0.25
        world, rows = self.game.roster()
        if world != self.world:
            if self.current:
                self.game.cancel(self.current)
            self.current = None
            self.queue.clear()
            self.seen.clear()
            self.world = world
        if world is None or not self.game.is_host():
            self.message = "Waiting for the host's world."
            return
        tokens = [row["token"] for row in rows]
        self.seen = [token for token in self.seen if token in tokens]
        self.queue = deque(row for row in self.queue if row["token"] in tokens)
        for row in rows:
            if row["token"] not in self.seen:
                self.seen.append(row["token"])
                self.queue.append(dict(row, steps=deque(key for key in BOOSTS if self.config[key]), results=[]))
        if self.current and self.current["token"] not in tokens:
            self.game.cancel(self.current)
            self.history.appendleft({"name": self.current["name"], "message": "Left lobby; unfinished steps cancelled."})
            self.current = None
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
            return
        job = self.current
        row = next(row for row in rows if row["token"] == job["token"])
        if not row["ready"]:
            self.message = f"Waiting for {job['name']}'s character."
            return
        job.update(row)
        if not job["steps"]:
            failed = any(not result["ok"] for result in job["results"])
            message = "Finished with errors; player kept in lobby" if failed else "All selected actions finished"
            if self.config.get("auto_kick") and not failed:
                if self.config.get("loot"):
                    deadline = job.setdefault("kick_after", now + 15.0)
                    if now < deadline:
                        job["step"] = "Waiting for loot to settle"
                        self.message = f"{job['name']}: loot sent; kicking in {max(1, int(deadline - now + 0.999))}s"
                        return
                try:
                    result = self.game.kick(job)
                except Exception as exc:
                    result = {"ok": False, "message": str(exc)}
                job["results"].append(dict(result, step="auto_kick"))
                message += "; kick requested" if result["ok"] else "; kick failed"
            self.history.appendleft({"name": job["name"], "message": message,
                                     "results": job["results"]})
            self.current = None
            return
        step = job["steps"][0]
        job["step"] = step
        self.message = f"{job['name']}: {step}"
        try:
            result = self.game.step(step, job, self.config)
        except Exception as exc:
            self.game.cancel(job)
            result = {"ok": False, "message": str(exc)}
        if result is not None:
            job["results"].append(dict(result, step=step))
            job["steps"].popleft()


class Game:
    def __init__(self):
        self.ready_since = {}

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
        if world is None or gs is None:
            return None, []
        from .party_helpers import _gbc_resolve_player_display_name
        local = a.get_pc()
        local_ps = getattr(local, "PlayerState", None)
        rows = []
        present = []
        for index, ps in enumerate(getattr(gs, "PlayerArray", []) or []):
            if ps is None or ps == local_ps:
                continue
            pc = a._gbc_find_pc_for_player_state(ps, world)
            if pc == local:
                continue
            present.append(ps)
            ready = pc is not None and a.player_economy._target_character_for_pc(pc) is not None
            # A pawn can appear before progression/replication has initialized.
            if ready:
                since = self.ready_since.setdefault(ps, time.monotonic())
                ready = time.monotonic() - since >= 5.0
            else:
                self.ready_since.pop(ps, None)
            rows.append({"token": ps, "pc": pc, "index": index,
                         "name": _gbc_resolve_player_display_name(ps), "ready": ready})
        self.ready_since = {ps: since for ps, since in self.ready_since.items() if ps in present}
        return world, rows

    def prepare_loot(self, payload):
        a = self.backend()
        raw = a._parse_serial_text(payload.get("codes", ""))
        serials = a.serial_rewards._resolve_give_serial_strings(raw) if raw else []
        if not serials or len(serials) != len(raw):
            raise ValueError("One or more item codes could not be resolved. Check the loot list.")
        return serials

    def experience_level(self, ps, step):
        economy = self.backend().player_economy
        index = 0 if step == "level" else 1
        states = getattr(ps, "ExperienceState", [])
        row = states[index] if len(states) > index else None
        for token in economy._candidate_experience_tokens(index, row):
            ptr = economy._make_experience_def_ptr(token)
            if ptr is not None:
                return int(ps.BP_GetExperienceLevel(ptr))
        return None

    def kick(self, job):
        a = self.backend()
        if not self.is_host():
            return {"ok": False, "message": "Not hosting; kick skipped."}
        _world, rows = self.roster()
        row = next((row for row in rows if row["token"] == job["token"]), None)
        if row is None:
            return {"ok": False, "message": "Guest already left."}
        for step, expected in job.get("expected_experience", {}).items():
            if self.experience_level(job["token"], step) != expected:
                return {"ok": False, "message": f"{step} no longer reads {expected}; player kept for retry."}
        ok = a._kick_party_player_by_index(row["index"], "AFK boosting complete")
        return {"ok": bool(ok), "message": "Boosting finished; kick requested." if ok else "Kick failed."}

    def cancel(self, job):
        a = self.backend()
        seq = job.pop("serial_job", None)
        if seq is not None:
            a.serial_rewards._pending_serial_delivery_sequences[:] = [s for s in a.serial_rewards._pending_serial_delivery_sequences if s is not seq]
        owned = job.pop("challenge_owned", None)
        if owned is not None and owned is a._challenge_queue:
            a.complete_challenges_cancel()

    def step(self, step, job, config):
        a = self.backend()
        pc, ps = job["pc"], job["token"]
        ok = False
        if step in ("level", "spec"):
            now = time.monotonic()
            state = job.setdefault("experience_attempts", {}).setdefault(step, {"started": now})
            target = a.MAX_PLAYER_LEVEL if step == "level" else a.MAX_SPEC_LEVEL
            if "check_after" in state:
                if now < state["check_after"]:
                    return None
                try:
                    actual = self.experience_level(ps, step)
                except Exception:
                    actual = None
                if actual == target:
                    job.setdefault("expected_experience", {})[step] = target
                    return {"ok": True, "message": f"Host readback confirmed {target} after settling; guest save not confirmed."}
                if now - state["started"] >= 30.0:
                    return {"ok": False, "message": f"Expected {target}, host readback {actual}; player kept in lobby."}
            a._set_experience_on_ps(ps, "player" if step == "level" else "specialization", target)
            state["check_after"] = now + 2.0
            return None
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
            ok = a._give_currency_to_pc(pc, step, a.MAX_WALLET_AMOUNT)
        elif step == "keys":
            results = [a._give_currency_to_pc(pc, f"vaultcard{i}", a.MAX_WALLET_AMOUNT) for i in range(1, 6)]
            ok = all(results)
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
                return {"ok": seq.get("index", 0) >= len(seq["chunks"]) and not seq.get("afk_error"),
                        "message": seq.get("afk_error") or rewards.serial_delivery_status()}
            if rewards._serial_delivery_busy():
                return None
            rewards._do_give_serial_to_player_indices(config["serials"], [job["index"]], scope_label=f"AFK: {job['name']}", mode="selected")
            seq = rewards._pending_serial_delivery_sequences[-1]
            seq["afk_player_state"] = ps
            # AFK is sustained delivery: give remote clients more replication time.
            seq["post_open_delay"] = max(float(seq.get("post_open_delay", 0)), 3.0)
            job["serial_job"] = seq
            return None
        return {"ok": bool(ok), "message": "Applied" if ok else "Action reported failure"}


lobby = Lobby(Game())
