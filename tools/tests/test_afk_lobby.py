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
    def classify_loot(self, serials): return [None] * len(serials)
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


def test_random_loot_is_seventy_from_pool_and_fixed_per_guest(monkeypatch):
    rng = module.random.Random(12)
    monkeypatch.setattr(module, "_loot_rng", SimpleNamespace(sample=rng.sample))
    pool = [f"serial-{i}" for i in range(952)]
    config = {"serials": pool, "loot_mode": "random70"}
    first_job = {}; first = module.Game.loot_for_guest(first_job, config)
    second = module.Game.loot_for_guest({}, config)
    assert len(first) == len(set(first)) == 70
    assert set(first).issubset(pool) and set(second).issubset(pool)
    assert first != second
    assert module.Game.loot_for_guest(first_job, config) is first
    assert pool == [f"serial-{i}" for i in range(952)]


def test_guest_draws_ignore_other_mods_reseeding_random(monkeypatch):
    def shared_random_used(*_):
        raise AssertionError("Must not use the shared random generator")
    monkeypatch.setattr(module.random, "sample", shared_random_used)
    config = {"serials": [f"item-{i}" for i in range(956)], "loot_mode": "random70"}
    jobs = [{} for _ in range(32)]
    for job in jobs:
        module.random.seed(1)
        selected = module.Game.loot_for_guest(job, config)
        assert len(selected) == 70 and len(set(selected)) == 70
        assert module.Game.loot_for_guest(job, config) is selected
    assert len({job["loot_selection_id"] for job in jobs}) == 32
    assert len(config["serials"]) == 956


def test_random_small_pools_and_unlimited_preserve_copies():
    small = ["@UCase", "@Ucase", "@UCase"]
    assert sorted(module.Game.loot_for_guest({}, {"serials": small, "loot_mode": "random70"})) == sorted(small)
    large = small * 1000
    assert module.Game.loot_for_guest({}, {"serials": large, "loot_mode": "all"}) == large
    assert module.Game.loot_for_guest({}, {"serials": large}) == large


def test_loot_mode_validation_and_legacy_default():
    lobby = module.Lobby(FakeGame())
    assert not lobby.start({"loot": True, "loot_mode": "bad"})["ok"]
    assert lobby.start({"loot": True})["ok"] and lobby.config["loot_mode"] == "all"


def test_over_seventy_needs_password_and_cannot_reuse_authorization():
    game = FakeGame(); game.prepare_loot = lambda _: [str(i) for i in range(71)]
    lobby = module.Lobby(game)
    for extra in ({}, {"bulk_loot_password": "bad"}, {"bulk_loot_authorized": True}):
        assert lobby.start({"loot": True, **extra})["password_required"]
        assert not lobby.enabled
    assert lobby.start({"loot": True, "bulk_loot_password": "funkyou"})["ok"]
    assert lobby.config["bulk_loot_authorized"]
    assert "bulk_loot_password" not in lobby.config
    lobby.stop()
    assert lobby.start({"loot": True})["password_required"]
    assert lobby.start({"loot": True, "loot_mode": "random70"})["ok"]
    assert not lobby.config["bulk_loot_authorized"]
    lobby.stop(); game.prepare_loot = lambda _: [str(i) for i in range(70)]
    assert lobby.start({"loot": True})["ok"]


def test_random_delivery_sends_only_selection_and_does_not_resend():
    calls = []; sequences = []
    def send(serials, indices, **kwargs):
        calls.append((serials, indices))
        sequences.append({"chunks": [serials], "index": 0})
    rewards = SimpleNamespace(_pending_serial_delivery_sequences=sequences,
        _serial_delivery_busy=lambda: False, _do_give_serial_to_player_indices=send,
        serial_delivery_status=lambda: "finished")
    game = module.Game(); game.backend = lambda: SimpleNamespace(serial_rewards=rewards)
    job = {"pc": "guest", "token": "ps", "index": 2, "name": "Guest"}
    config = {"serials": [str(i) for i in range(952)], "loot_mode": "random70"}
    assert game.step("loot", job, config) is None
    assert len(calls) == 1 and len(calls[0][0]) == 70 and calls[0][1] == [2]
    assert game.step("loot", job, config) is None and len(calls) == 1
    sequences[0]["index"] = 1; sequences.clear()
    assert game.step("loot", job, config)["ok"] and len(calls) == 1


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


def test_new_boosts_are_independent_and_opt_in():
    for selected in ("challenges", "uvhm", "cosmetics"):
        game = FakeGame(); lobby = module.Lobby(game)
        assert lobby.start({selected: True})["ok"]
        game.rows = [row("guest")]; ticks(lobby)
        assert game.calls == [(selected, "guest", 1)]


def test_join_waits_twenty_seconds_for_same_character(monkeypatch):
    clock = [100.0]; monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    game = module.Game()
    assert not game.character_ready("ps", "pc", "pawn")
    clock[0] += 5
    assert not game.character_ready("ps", "pc", "pawn")
    clock[0] += 14.9
    assert not game.character_ready("ps", "pc", "pawn")
    clock[0] += .1
    assert game.character_ready("ps", "pc", "pawn")
    # A replacement pawn must start a fresh wait even without a null frame.
    assert not game.character_ready("ps", "pc", "replacement")
    clock[0] += 20
    assert game.character_ready("ps", "pc", "replacement")
    assert not game.character_ready("ps", None, None)
    assert not game.character_ready("ps", "pc", "replacement")


def test_world_loss_discards_join_timer():
    game = module.Game()
    game.character_ready("ps", "pc", "pawn")
    game.backend = lambda: SimpleNamespace(_gbc_session_world_and_gamestate=lambda: (None, None))
    assert game.roster() == (None, [])
    assert game.ready_since == {}


def test_progression_must_load_before_join_delay_starts(monkeypatch):
    clock = [100.0]; monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    class State:
        ExperienceState = []
    ps = State(); pools = []
    pawn = SimpleNamespace(GbxProgressionManager=SimpleNamespace(
        ProgressPointsContainer=SimpleNamespace(PointsAcquiredPerPool=pools)))
    game = module.Game()
    def ready():
        return game.character_ready(ps, "pc", pawn if game.progression_loaded(ps, pawn) else None)
    assert not ready()
    clock[0] += 90
    assert not ready()  # a long-lived loading pawn cannot bypass the gate
    pools.extend([0, 0, 0])
    assert not ready()  # XP data still absent
    ps.ExperienceState = [object(), object()]
    assert not ready()
    clock[0] += 20
    assert ready()
    pools.clear()
    assert not ready()  # loading resumes: discard the old countdown
    pools.extend([0, 0, 3225])
    assert not ready()
    clock[0] += 20
    assert ready()  # already-max SDUs do not skip the unconditional run


def test_uvhm_guest_plan_pacing_final_settle_and_manual_queue(monkeypatch):
    clock = [100.0]; monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    calls = []; indices_seen = []; manual = [True]
    game = module.Game()
    pc = SimpleNamespace(ServerIncrementChallengeForPlayer=lambda *args: calls.append(args))
    game.backend = lambda: SimpleNamespace(
        uvh_boost_status=lambda: {"active": manual[0]}, UVH_RANKS=list(range(7)),
        _uvh_build_plan=lambda indices: indices_seen.append(indices) or [("1", "first", .3), ("7", "final", .3)])
    job = {"pc": pc, "token": "guest"}
    assert game.step("uvhm", job, {}) is None and not calls
    manual[0] = False
    assert game.step("uvhm", job, {}) is None
    assert indices_seen == [list(range(7))] and calls == [("first", 1)]
    assert game.step("uvhm", job, {}) is None and len(calls) == 1
    clock[0] += 1
    assert game.step("uvhm", job, {}) is None and calls[-1] == ("final", 1)
    assert game.step("uvhm", job, {}) is None
    clock[0] += 1
    assert game.step("uvhm", job, {})["ok"]


def test_uvhm_failure_keeps_guest_and_continues_other_boosts():
    game = FakeGame(); adapter = module.Game()
    def fail(*_): raise RuntimeError("RPC failed")
    adapter.backend = lambda: SimpleNamespace(uvh_boost_status=lambda: {"active": False},
        UVH_RANKS=[1], _uvh_build_plan=lambda _: [("1", "first", .3)])
    original_step = game.step
    game.step = lambda step, job, config: adapter.step(step, job, config) if step == "uvhm" else original_step(step, job, config)
    game.cancel = adapter.cancel
    lobby = module.Lobby(game)
    lobby.start({"uvhm": True, "loot": True, "auto_kick": True})
    game.rows = [dict(row("guest"), pc=SimpleNamespace(ServerIncrementChallengeForPlayer=fail))]
    ticks(lobby)
    assert game.kicked == [] and game.calls == [("loot", "guest", 1)]
    assert not lobby.history[0]["results"][0]["ok"]


def test_cancel_discards_private_uvhm_without_touching_manual_work():
    game = module.Game(); game.backend = lambda: SimpleNamespace()
    job = {"uvhm_plan": deque([1]), "uvhm_next_at": 200}
    game.cancel(job)
    assert job == {}


def test_customs_and_hovers_matches_boosting_button_and_targets_guest():
    calls = []; game = module.Game()
    pc = SimpleNamespace(ServerActivateDevPerk=lambda code: calls.append(code))
    game.backend = lambda: SimpleNamespace()
    job = {"pc": pc, "token": "guest"}
    assert game.step("cosmetics", job, {})["ok"] and calls == [4]
    html = (FILE.parents[2] / "electron_poc/renderer.html").read_text(encoding="utf-8")
    assert '<button data-action="devperk_4">All Customs + Hovers</button>' in html
    assert 'data-afk-boost="cosmetics"> All Customs + Hovers' in html
    assert 'data-afk-boost="vehicles"' not in html


def test_guaranteed_counts_and_combined_password_boundary():
 game=FakeGame(); game.prepare_loot=lambda payload: payload.get('codes','').splitlines()
 lobby=module.Lobby(game)
 codes='\n'.join(str(i) for i in range(69))
 fixed='fixed1\nfixed2'
 assert lobby.start({'loot':True,'codes':codes,'guaranteed_codes':fixed})['password_required']
 assert lobby.start({'loot':True,'codes':codes,'guaranteed_codes':fixed,'loot_mode':'random70'})['ok']
 assert lobby.config['guaranteed_serials']==['fixed1','fixed2']
 lobby.stop()
 assert lobby.start({'loot':True,'codes':'','guaranteed_codes':fixed,'loot_mode':'random70'})['ok']
 lobby.stop()
 over='\n'.join(str(i) for i in range(71))
 assert lobby.start({'loot':True,'guaranteed_codes':over,'loot_mode':'random70'})['password_required']
 assert lobby.start({'loot':True,'guaranteed_codes':over,'loot_mode':'random70','bulk_loot_password':'funkyou'})['ok']
 assert lobby.config['bulk_loot_authorized']
