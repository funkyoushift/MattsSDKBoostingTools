"""Join/rejoin, targeting, stop and existing-action wiring regressions."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from collections import deque

FILE = Path(__file__).resolve().parents[2] / "mod_extracted/MattsSDKBoostingTools/afk_lobby.py"
spec = importlib.util.spec_from_file_location("afk_test", FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeGame:
    def __init__(self):
        self.rows = []
        self.world = "world"
        self.calls = []
        self.cancelled = []
        self.wait = False
        self.kicked = []
    def is_host(self): return True
    def roster(self): return self.world, self.rows
    def prepare_loot(self, payload): return ["serial"]
    def step(self, step, job, config):
        if self.wait: return None
        self.calls.append((step, job["token"], job["index"]))
        return {"ok": True, "message": "submitted"}
    def cancel(self, job): self.cancelled.append(job["token"])
    def kick(self, job):
        self.kicked.append(job["token"])
        return {"ok": True, "message": "kick requested"}


def row(token, index=1, ready=True):
    return {"token": token, "index": index, "ready": ready, "name": str(token), "pc": token}


def ticks(lobby, count=10):
    for _ in range(count):
        lobby.next_tick = 0
        lobby.tick()


def test_each_join_runs_once_and_rejoining_runs_again():
    game = FakeGame(); lobby = module.Lobby(game)
    assert lobby.start({"level": True, "sdu": True})["ok"]
    game.rows = [row("guest")]; ticks(lobby)
    assert game.calls == [("level", "guest", 1), ("sdu", "guest", 1)]
    ticks(lobby); assert len(game.calls) == 2
    game.rows = []; ticks(lobby)
    game.rows = [row("guest")]; ticks(lobby)
    assert len(game.calls) == 4


def test_loading_guest_does_not_block_ready_guest_or_duplicate():
    game = FakeGame(); lobby = module.Lobby(game)
    lobby.start({"spec": True})
    game.rows = [row("slow", ready=False), row("ready", index=2)]
    ticks(lobby); assert game.calls == [("spec", "ready", 2)]
    game.rows[0]["ready"] = True; ticks(lobby)
    assert game.calls[-1] == ("spec", "slow", 1)
    assert len(game.calls) == 2


def test_slot_reuse_cancels_old_player_and_boosts_new_player():
    game = FakeGame(); lobby = module.Lobby(game)
    lobby.start({"loot": True}); game.rows = [row("old")]
    game.wait = True; ticks(lobby, 1)
    game.rows = [row("new")]; game.wait = False; ticks(lobby)
    assert game.cancelled == ["old"]
    assert game.calls == [("loot", "new", 1)]


def test_slot_reorder_tracks_identity_and_stop_cancels_pending():
    game = FakeGame(); lobby = module.Lobby(game)
    lobby.start({"level": True, "loot": True}); game.rows = [row("guest", 2)]
    ticks(lobby, 1)
    game.rows[0]["index"] = 1; ticks(lobby, 1)
    assert game.calls == [("level", "guest", 2), ("loot", "guest", 1)]
    lobby.stop(); ticks(lobby)
    assert not lobby.enabled and not lobby.queue
    assert len(game.calls) == 2


def test_failure_does_not_skip_remaining_selected_actions():
    game = FakeGame(); lobby = module.Lobby(game)
    original = game.step
    def step(key, job, config):
        if key == "level": raise RuntimeError("rejected")
        return original(key, job, config)
    game.step = step
    lobby.start({"level": True, "sdu": True}); game.rows = [row("g")]; ticks(lobby)
    assert game.calls == [("sdu", "g", 1)]
    assert lobby.history[0]["message"].startswith("Finished with errors")


def test_auto_kick_waits_for_last_step_and_is_optional(monkeypatch):
    clock = [100.0]; monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    game = FakeGame(); lobby = module.Lobby(game)
    lobby.start({"loot": True, "auto_kick": True})
    game.rows = [row("guest")]; game.wait = True
    ticks(lobby, 5); assert game.kicked == []
    game.wait = False; ticks(lobby, 1); assert game.kicked == []
    ticks(lobby, 1); assert game.kicked == []
    clock[0] += 14; ticks(lobby, 1); assert game.kicked == []
    clock[0] += 1; ticks(lobby, 1); assert game.kicked == ["guest"]
    ticks(lobby, 5); assert game.kicked == ["guest"]
    lobby.stop(); lobby.start({"level": True}); ticks(lobby)
    assert game.kicked == ["guest"]


def test_auto_kick_does_not_kick_failed_or_disconnected_guests():
    game = FakeGame(); lobby = module.Lobby(game)
    game.step = lambda *_: {"ok": False, "message": "delivery failed"}
    lobby.start({"loot": True, "auto_kick": True})
    game.rows = [row("guest")]; ticks(lobby)
    assert game.kicked == []

    lobby.stop(); lobby.start({"loot": True, "auto_kick": True})
    game.step = lambda *_: None
    ticks(lobby, 1); game.rows = []; ticks(lobby)
    assert game.kicked == []


def test_kick_re_resolves_guest_identity_after_slot_reorder():
    game = module.Game(); calls = []
    game.is_host = lambda: True
    game.roster = lambda: ("world", [row("other", 1), row("guest", 2)])
    game.backend = lambda: SimpleNamespace(_kick_party_player_by_index=lambda index, reason: calls.append(index) or True)
    assert game.kick({"token": "guest", "index": 1})["ok"]
    assert calls == [2]
    assert not game.kick({"token": "gone", "index": 1})["ok"]
    assert calls == [2]


def test_empty_config_and_running_reconfigure_rejected():
    lobby = module.Lobby(FakeGame())
    assert not lobby.start({})["ok"]
    assert lobby.start({"level": True})["ok"]
    assert not lobby.start({"cash": True})["ok"]
    assert lobby.config["level"] and not lobby.config["cash"]


def test_loot_has_no_500_code_cap_and_preserves_duplicates_and_case():
    codes = ["@UCaseSensitive", "@Ucasesensitive", "@UCaseSensitive"] * 1000
    game = module.Game()
    game.backend = lambda: SimpleNamespace(
        _parse_serial_text=lambda text: text.splitlines(),
        serial_rewards=SimpleNamespace(_resolve_give_serial_strings=lambda raw: list(raw)))
    assert game.prepare_loot({"codes": "\n".join(codes)}) == codes


def test_sdu_uses_existing_max_helper_and_keys_target_only_guest():
    calls = []
    game = module.Game()
    game.backend = lambda: SimpleNamespace(
        player_economy=SimpleNamespace(_set_max_sdu_points_on_pc=lambda pc: calls.append(("sdu", pc)) or True),
        _give_currency_to_pc=lambda pc, kind, amount: calls.append((kind, pc, amount)) or True,
        MAX_WALLET_AMOUNT=2147483647)
    assert game.step("sdu", {"pc": "guest", "token": "ps"}, {})["ok"]
    assert game.step("keys", {"pc": "guest", "token": "ps"}, {})["ok"]
    assert calls == [("sdu", "guest")] + [(f"vaultcard{i}", "guest", 2147483647) for i in range(1, 6)]


def test_challenges_use_single_guest_and_wait_for_completion():
    calls = []; queue = deque([1])
    status = {"active": True, "steps_done": 0, "steps_total": 1, "failed_count": 0, "message": "running"}
    backend = SimpleNamespace(_challenge_queue=queue,
        complete_challenges_status=lambda: dict(status),
        _challenge_rows_for_category=lambda category: [("challenge", 1)],
        _challenge_queue_start=lambda rows, **kw: calls.append(kw) or {"ok": True})
    game = module.Game(); game.backend = lambda: backend
    job = {"pc": "guest", "token": "ps"}
    assert game.step("challenges", job, {}) is None
    assert not calls  # don't replace a manual challenge job
    status["active"] = False
    assert game.step("challenges", job, {}) is None
    assert calls[0]["targets"] == ["guest"]
    status.update(active=False, steps_done=1, message="finished")
    assert game.step("challenges", job, {})["ok"]


def test_travel_discards_old_controller_work():
    game = FakeGame(); lobby = module.Lobby(game)
    lobby.start({"loot": True}); game.rows = [row("guest")]; game.wait = True
    ticks(lobby, 1); game.world = None; game.rows = []; ticks(lobby)
    assert game.cancelled == ["guest"]
    assert not lobby.current and not lobby.queue


def test_sdu_retries_are_paced_and_bounded(monkeypatch):
    clock = [100.0]; monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    calls = []; success = [False]
    game = module.Game()
    game.backend = lambda: SimpleNamespace(player_economy=SimpleNamespace(
        _set_max_sdu_points_on_pc=lambda pc: calls.append(pc) or success[0]))
    job = {"pc": "guest", "token": "ps"}
    assert game.step("sdu", job, {}) is None
    clock[0] += 1
    assert game.step("sdu", job, {}) is None and len(calls) == 1
    clock[0] += 1; success[0] = True
    assert game.step("sdu", job, {})["ok"] and len(calls) == 2
    job = {"pc": "guest", "token": "ps"}; success[0] = False
    assert game.step("sdu", job, {}) is None
    clock[0] += 31
    assert not game.step("sdu", job, {})["ok"]


def test_experience_waits_retries_and_requires_delayed_readback(monkeypatch):
    clock = [100.0]; monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    calls = []; actual = [1]
    game = module.Game(); game.experience_level = lambda *_: actual[0]
    game.backend = lambda: SimpleNamespace(MAX_PLAYER_LEVEL=70, MAX_SPEC_LEVEL=701,
        _set_experience_on_ps=lambda *args: calls.append(args) or True)
    job = {"pc": "guest", "token": "ps"}
    assert game.step("level", job, {}) is None
    assert game.step("level", job, {}) is None and len(calls) == 1
    clock[0] += 2
    assert game.step("level", job, {}) is None and len(calls) == 2
    actual[0] = 70; clock[0] += 2
    assert game.step("level", job, {})["ok"]
    assert job["expected_experience"] == {"level": 70}
    actual[0] = 1; clock[0] += 30
    assert not game.step("level", job, {})["ok"]


def test_kick_withheld_if_experience_changes_after_loot():
    game = module.Game(); calls = []
    game.is_host = lambda: True
    game.roster = lambda: ("world", [row("guest")])
    game.experience_level = lambda *_: 1
    game.backend = lambda: SimpleNamespace(_kick_party_player_by_index=lambda *args: calls.append(args))
    assert not game.kick({"token": "guest", "expected_experience": {"level": 70}})["ok"]
    assert calls == []


def test_guest_leaving_during_loot_settle_is_never_kicked(monkeypatch):
    clock = [100.0]; monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    game = FakeGame(); lobby = module.Lobby(game)
    lobby.start({"loot": True, "auto_kick": True}); game.rows = [row("guest")]
    ticks(lobby, 2); assert lobby.current["kick_after"] == 115.0
    game.rows = []; clock[0] += 16; ticks(lobby)
    assert game.kicked == [] and lobby.current is None
