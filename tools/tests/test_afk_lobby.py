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
    def authorize_bulk_loot(self, password=None): return password == 'funkyou'
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


def test_custom_amount_validation_and_legacy_defaults():
    lobby = module.Lobby(FakeGame())
    assert lobby.start({'cash': True, 'cash_amount': 1250, 'level_amount': 30})['ok']
    assert lobby.config['cash_amount'] == 1250
    assert lobby.config['level_amount'] == 30
    assert lobby.config['keys_amount'] == 2147483647
    lobby.stop()
    for value in (0, -1, True, 1.5, 'bad', 2147483648):
        assert not lobby.start({'cash': True, 'cash_amount': value})['ok']


def test_custom_amounts_reach_targeted_actions():
    calls = []
    game = module.Game()
    game.backend = lambda: SimpleNamespace(
        MAX_PLAYER_LEVEL=70, MAX_SPEC_LEVEL=701, MAX_WALLET_AMOUNT=2147483647,
        _give_currency_to_pc=lambda pc, kind, amount: calls.append((pc, kind, amount)) or True,
        _set_experience_on_ps=lambda ps, track, amount: calls.append((ps, track, amount)))
    game.experience_level = lambda ps, step: 4
    config = {'level_amount': 30, 'spec_amount': 50, 'cash_amount': 1250,
              'eridium_amount': 100, 'keys_amount': 5}
    for step in ('level', 'spec', 'cash', 'eridium', 'keys'):
        game.step(step, {'pc': 'guest-pc', 'token': 'guest-ps'}, config)
    assert calls == [('guest-ps', 'player', 30), ('guest-ps', 'specialization', 50),
                     ('guest-pc', 'cash', 1250), ('guest-pc', 'eridium', 100)] + [
                     ('guest-pc', f'vaultcard{i}', 5) for i in range(1, 6)]
    calls.clear()
    game.experience_level = lambda ps, step: 60
    assert game.step('level', {'pc': 'guest-pc', 'token': 'guest-ps'}, config)['ok']
    assert not calls


def row(token, index=1, ready=True):
    return {"token": token, "index": index, "ready": ready, "name": str(token), "pc": token}


def ticks(lobby, count=10):
    for _ in range(count):
        lobby.next_tick = 0
        lobby.tick()


def test_host_test_runs_once_no_kick_accept_or_join_count():
    game = FakeGame()
    game.rows = [row('host', index=0)]
    lobby = module.Lobby(game)
    assert lobby.start({'test_host':True, 'level':True, 'loot':True,
                        'auto_accept':True, 'auto_kick':True})['ok']
    assert game.test_host
    assert not lobby.config['auto_accept'] and not lobby.config['auto_kick']
    ticks(lobby, 30)
    assert game.calls == [('level','host',0), ('loot','host',0)]
    assert not lobby.enabled and not game.kicked
    assert lobby.session_joins == 0 and lobby.lifetime_joins == 0
    assert 'Host test finished' in lobby.message
    assert lobby.start({'level':True})['ok']
    assert not game.test_host


def test_host_test_cleanup_uses_same_steps_and_stops_on_completion():
    game = FakeGame()
    game.rows = [row('host', index=0)]
    lobby = module.Lobby(game)
    assert lobby.start({'test_host':True, 'challenges':True, 'loot':True,
                        'cleanup_rewards':True, 'auto_kick':True})['ok']
    ticks(lobby, 30)
    assert [c[0] for c in game.calls] == ['inventory_capture','challenges','inventory_recovery']
    assert not lobby.enabled and not game.kicked


def test_real_roster_selects_only_local_character_in_host_test(monkeypatch):
    import sys
    import types
    helpers = types.ModuleType('afk_host_test.party_helpers')
    helpers._gbc_resolve_player_display_name = lambda ps: ps
    monkeypatch.setitem(sys.modules, helpers.__name__, helpers)
    monkeypatch.setattr(module, '__package__', 'afk_host_test')
    local = SimpleNamespace(PlayerState='host')
    remote = SimpleNamespace(PlayerState='guest')
    game = module.Game()
    game.backend = lambda: SimpleNamespace(
        _gbc_session_world_and_gamestate=lambda: ('world', SimpleNamespace(PlayerArray=['host','guest'])),
        get_pc=lambda:local,
        _gbc_find_pc_for_player_state=lambda ps,world:local if ps=='host' else remote,
        player_economy=SimpleNamespace(_target_character_for_pc=lambda pc:'pawn'))
    game.progression_loaded = lambda ps,pawn:True
    game.character_ready = lambda ps,pc,pawn:True
    game.connection_root = lambda pc:None
    assert [r['token'] for r in game.roster()[1]] == ['guest']
    game.test_host = True
    rows = game.roster()[1]
    assert len(rows) == 1 and rows[0]['token'] == 'host' and rows[0]['index'] == 0
    assert rows[0]['pc'] is local
    assert not game.kick(rows[0])['ok']


def test_cleanup_needs_no_password_and_composes_originals_with_selected_loot():
    game=FakeGame();lobby=module.Lobby(game)
    config={'challenges':True,'uvhm':True,'loot':True,'cleanup_rewards':True,'auto_kick':True}
    assert lobby.start(config)['ok']
    game.rows=[row('guest')];ticks(lobby,8)
    assert [c[0] for c in game.calls]==['inventory_capture','challenges','uvhm','inventory_recovery']
    assert not game.kicked
    assert 'backpack_password' not in lobby.config


def test_cleanup_capture_failure_falls_back_without_clearing_backpack():
    game=FakeGame();lobby=module.Lobby(game)
    assert lobby.start({'level':True,'challenges':True,'loot':True,'cleanup_rewards':True,'auto_kick':True})['ok']
    normal_step=game.step
    game.step=lambda step,*args: ({'ok':False,'message':'unreadable original'}
                                 if step=='inventory_capture' else normal_step(step,*args))
    game.rows=[row('guest')];ticks(lobby,12)
    assert [call[0] for call in game.calls]==['level','challenges','loot']
    assert not game.kicked  # existing loot settlement delay remains in force
    assert lobby.history[0]['results'][0]['cleanup_skipped']
    assert all(result['ok'] for result in lobby.history[0]['results'])


def test_failed_recovery_keeps_report_and_advances_to_next_guest():
    game = FakeGame(); lobby = module.Lobby(game)
    normal_step = game.step
    def step(action, job, config):
        result = normal_step(action, job, config)
        if action == 'inventory_recovery' and job['token'] == 'first':
            return dict(ok=False, message='Manual repair report saved', recovery_report='report.txt')
        return result
    game.step = step
    assert lobby.start(dict(challenges=True, cleanup_rewards=True, auto_kick=True))['ok']
    game.rows = [row('first'), row('second', 2)]
    ticks(lobby, 30)
    assert ('inventory_recovery', 'second', 2) in game.calls
    assert lobby.current is None
    assert any(result.get('recovery_report') == 'report.txt'
               for history in lobby.history for result in history['results'])
    assert 'first' not in game.kicked


def test_preclear_failure_delivers_selected_loot_without_repeating_boosts():
    game=FakeGame(); lobby=module.Lobby(game)
    normal=game.step
    def step(action, job, config):
        result=normal(action, job, config)
        return dict(ok=False, nothing_cleared=True, message='Read failed') if action=='inventory_recovery' else result
    game.step=step
    lobby.start(dict(level=True, challenges=True, loot=True, cleanup_rewards=True))
    game.rows=[row('guest')]; ticks(lobby,20)
    assert [c[0] for c in game.calls] == ['inventory_capture','level','challenges','inventory_recovery','loot']
    assert all(r['ok'] for r in lobby.history[0]['results'])


def test_kick_retries_are_bounded_and_spaced(monkeypatch):
    clock=[100.0]; monkeypatch.setattr(module.time,'monotonic',lambda:clock[0])
    game=FakeGame(); lobby=module.Lobby(game); attempts=[]
    game.kick=lambda job: attempts.append(job['token']) or dict(ok=False,message='Not yet')
    lobby.start(dict(level=True, auto_kick=True)); game.rows=[row('guest')]
    ticks(lobby); assert len(attempts)==1
    ticks(lobby); assert len(attempts)==1
    clock[0]+=5; ticks(lobby); assert len(attempts)==2
    clock[0]+=5; ticks(lobby); assert len(attempts)==3
    clock[0]+=50; ticks(lobby); assert len(attempts)==3


def test_unavailable_current_guest_does_not_hold_queue_forever(monkeypatch):
    clock=[100.0]; monkeypatch.setattr(module.time,'monotonic',lambda:clock[0])
    game=FakeGame(); lobby=module.Lobby(game)
    lobby.start(dict(level=True,sdu=True)); game.rows=[row('first'),row('second',2)]
    ticks(lobby,1); game.rows[0]['ready']=False; ticks(lobby,1)
    clock[0]+=121; ticks(lobby,10)
    assert 'first' in game.cancelled
    assert ('sdu','second',2) in game.calls
    assert any('unavailable' in r['message'] for h in lobby.history for r in h['results'])


def test_run_report_retains_selection_and_failure(tmp_path,monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    import json
    job=dict(record=dict(name='guest',message='Needs review',results=[dict(ok=False,step='loot')]),
             loot_selection=['@UOne','@UOne'])
    path=module.Game.save_run_report(job)
    saved=json.loads(Path(path).read_text(encoding='utf-8'))
    assert saved['selected_loot']==['@UOne','@UOne'] and not saved['guest_save_verified']
    assert module.Game.save_run_report(job)==path


def test_boost_exception_does_not_transfer_owned_recovery_to_background():
    game=module.Game()
    backend=SimpleNamespace(_afk_inventory_recovery=None)
    game.backend=lambda:backend
    recovery=object()
    job={'inventory_recovery':recovery,'uvhm_plan':deque(['step'])}
    game.cancel_step(job,'uvhm')
    assert backend._afk_inventory_recovery is None
    assert job['inventory_recovery'] is recovery and 'uvhm_plan' not in job


def test_cleanup_password_only_applies_to_more_than_seventy_new_items():
    game=FakeGame();lobby=module.Lobby(game)
    base={'challenges':True,'cleanup_rewards':True}
    assert lobby.start(base)['ok']
    lobby.stop()
    game.prepare_loot=lambda _:['@UItem']*70
    assert lobby.start(dict(base,loot=True))['ok']
    lobby.stop()
    game.prepare_loot=lambda _:['@UItem']*71
    denied=lobby.start(dict(base,loot=True))
    assert denied['password_required'] and denied['password_kind']=='bulk_loot'
    assert not lobby.start(dict(base,loot=True,backpack_password='funkyou'))['ok']
    assert lobby.start(dict(base,loot=True,bulk_loot_password='funkyou'))['ok']


def test_each_join_runs_once_and_rejoining_runs_again():
    game = FakeGame(); lobby = module.Lobby(game)
    assert lobby.start({"level": True, "sdu": True})["ok"]
    game.rows = [row("guest")]; ticks(lobby)
    assert game.calls == [("level", "guest", 1), ("sdu", "guest", 1)]
    ticks(lobby); assert len(game.calls) == 2
    game.rows = []; ticks(lobby)
    game.rows = [row("guest")]; ticks(lobby)
    assert len(game.calls) == 4


def test_shared_runs_once_but_other_boosts_and_loot_run_for_every_guest():
    game=FakeGame(); lobby=module.Lobby(game)
    lobby.start({'level':True,'challenges':True,'uvhm':True,'loot':True})
    game.rows=[row('a'),row('b',2),row('c',3)];ticks(lobby,40)
    for step in ('challenges','uvhm'):
        assert len([c for c in game.calls if c[0]==step])==1
    for step in ('level','loot'):
        assert {c[1] for c in game.calls if c[0]==step}=={'a','b','c'}


def test_late_join_does_not_get_partial_challenge_credit_but_gets_full_uvhm_credit():
    game=FakeGame(); lobby=module.Lobby(game)
    lobby.start({'challenges':True,'uvhm':True})
    game.rows=[row('a')];game.wait=True;ticks(lobby,1)
    game.rows.append(row('late',2));game.wait=False;ticks(lobby,20)
    assert [c for c in game.calls if c[0]=='challenges']==[('challenges','a',1),('challenges','late',2)]
    assert len([c for c in game.calls if c[0]=='uvhm'])==1


def test_shared_member_disconnect_and_rejoin_during_run_is_not_credited():
    game=FakeGame(); lobby=module.Lobby(game)
    lobby.start({'challenges':True});game.rows=[row('a'),row('b',2)]
    game.wait=True;ticks(lobby,1)
    game.rows=[row('a')];ticks(lobby,1)
    game.rows.append(row('b',2));game.wait=False;ticks(lobby,20)
    assert len(game.calls)==2


def test_loading_member_is_not_credited_even_if_ready_at_finish():
    game=FakeGame();lobby=module.Lobby(game)
    lobby.start({'challenges':True});game.rows=[row('a'),row('b',2,False)]
    game.wait=True;ticks(lobby,1)
    game.rows[1]['ready']=True;game.wait=False;ticks(lobby,20)
    assert len(game.calls)==2


def test_failed_shared_run_gives_no_credit_to_other_guest():
    game=FakeGame();lobby=module.Lobby(game)
    lobby.start({'challenges':True});game.rows=[row('a'),row('b',2)]
    original=game.step
    def step(key,job,config):
        result=original(key,job,config)
        return dict(result,ok=job['token']!='a')
    game.step=step;ticks(lobby,20)
    assert len(game.calls)==2


def test_shared_rewards_wait_for_every_ready_backpack_capture():
    game=FakeGame();lobby=module.Lobby(game)
    lobby.start({'challenges':True,'uvhm':True,'cleanup_rewards':True,'loot':True})
    game.rows=[row('a'),row('b',2)];ticks(lobby,30)
    assert game.calls[:3]==[('inventory_capture','a',1),('inventory_capture','b',2),('challenges','a',1)]
    assert {c[1] for c in game.calls if c[0]=='inventory_recovery'}=={'a','b'}
    assert len([c for c in game.calls if c[0]=='uvhm'])==1


def test_shared_capture_failure_preserves_fallback_loot_for_that_guest():
    game=FakeGame();lobby=module.Lobby(game)
    lobby.start({'challenges':True,'cleanup_rewards':True,'loot':True})
    original=game.step
    def step(key,job,config):
        if key=='inventory_capture' and job['token']=='b': return {'ok':False,'message':'unreadable'}
        return original(key,job,config)
    game.step=step;game.rows=[row('a'),row('b',2)];ticks(lobby,30)
    assert ('inventory_recovery','b',2) not in game.calls
    assert ('loot','b',2) in game.calls
    assert len([c for c in game.calls if c[0]=='challenges'])==1


def test_shared_credit_does_not_survive_world_change_or_afk_restart():
    game=FakeGame();lobby=module.Lobby(game)
    config={'challenges':True};lobby.start(config);game.rows=[row('a'),row('b',2)];ticks(lobby,20)
    game.world='next';ticks(lobby,20)
    assert len(game.calls)==2
    lobby.stop();lobby.start(config);ticks(lobby,20)
    assert len(game.calls)==3


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
    assert lobby.history[0]["message"].startswith("Run ended with errors")


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


def test_kick_is_not_blocked_by_changed_experience():
    game = module.Game(); calls = []
    game.is_host = lambda: True
    game.roster = lambda: ("world", [row("guest")])
    game.experience_level = lambda *_: 1
    repairs = []
    game.backend = lambda: SimpleNamespace(_kick_party_player_by_index=lambda *args: calls.append(args) or True,
        _set_experience_on_ps=lambda *args: repairs.append(args))
    assert game.kick({"token": "guest", "expected_experience": {"level": 70}})["ok"]
    assert calls == [(1, "AFK boosting complete")]
    assert repairs == []


def test_guest_leaving_during_loot_settle_is_never_kicked(monkeypatch):
    clock = [100.0]; monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    game = FakeGame(); lobby = module.Lobby(game)
    lobby.start({"loot": True, "auto_kick": True}); game.rows = [row("guest")]
    ticks(lobby, 2); assert lobby.completed[0]["kick_after"] == 115.0
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

def test_adjustable_random_count_password_and_validation():
 game=FakeGame();game.prepare_loot=lambda payload:payload.get('codes','').splitlines()
 lobby=module.Lobby(game);payload={'loot':True,'codes':'\n'.join(str(i) for i in range(100)),'loot_mode':'random70'}
 for bad in (0,-1,1.5,True,'oops'):
  assert not lobby.start({**payload,'random_count':bad})['ok']
 assert lobby.start({**payload,'random_count':35})['ok'];assert lobby.config['random_count']==35
 lobby.stop()
 assert lobby.start({**payload,'random_count':85})['password_required']
 assert lobby.start({**payload,'random_count':85,'bulk_loot_password':'funkyou'})['ok']
 assert lobby.config['bulk_loot_authorized'] and lobby.config['random_count']==85


def test_shared_connection_waits_for_loading_member_and_both_settle(monkeypatch):
    clock = [100.0]; monkeypatch.setattr(module.time, 'monotonic', lambda: clock[0])
    game = FakeGame(); lobby = module.Lobby(game)
    lobby.start({'loot': True, 'auto_kick': True})
    game.rows = [dict(row('first'), connection='shared'), dict(row('second', 2, False), connection='shared')]
    ticks(lobby); clock[0] += 20; ticks(lobby)
    assert not game.kicked and lobby.current is None
    game.rows[1]['ready'] = True; ticks(lobby)
    assert [call[1] for call in game.calls] == ['first', 'second']
    assert not game.kicked
    clock[0] += 15; ticks(lobby)
    assert game.kicked == ['first']
    assert all(j['kick_attempted'] for j in lobby.completed)


def test_unknown_connection_waits_for_every_guest():
    game = FakeGame(); lobby = module.Lobby(game)
    lobby.start({'level': True, 'auto_kick': True})
    game.rows = [row('first'), row('second', 2, False)]
    ticks(lobby); assert not game.kicked
    game.rows[1]['ready'] = True; ticks(lobby)
    assert game.kicked == ['first', 'second']


def test_failed_shared_guest_does_not_block_finished_connection_kick():
    game = FakeGame(); lobby = module.Lobby(game)
    game.step = lambda step, job, config: {'ok': job['token'] != 'failed', 'message': 'result'}
    lobby.start({'level': True, 'auto_kick': True})
    game.rows = [dict(row('ready'), connection='shared'), dict(row('failed', 2), connection='shared')]
    ticks(lobby); assert game.kicked == ['ready']
    assert len(lobby.history) == 2


def test_new_member_during_settlement_delays_kick_and_reordered_slot_is_used(monkeypatch):
    clock = [100.0]; monkeypatch.setattr(module.time, 'monotonic', lambda: clock[0])
    game = FakeGame(); lobby = module.Lobby(game); indices = []
    game.kick = lambda job: indices.append(job['index']) or {'ok': True, 'message': 'done'}
    lobby.start({'loot': True, 'auto_kick': True})
    game.rows = [dict(row('first'), connection='shared')]; ticks(lobby)
    game.rows[0]['index'] = 3
    game.rows.append(dict(row('new', 2, False), connection='shared'))
    clock[0] += 16; ticks(lobby); assert not indices
    game.rows.pop(); ticks(lobby); assert indices == [3]


def test_counters_count_rejoins_reset_session_and_keep_lifetime():
    game = FakeGame(); saved = []; game.load_join_count = lambda: 12
    game.save_join_count = saved.append
    lobby = module.Lobby(game)
    assert lobby.status()['lifetime_joins'] == 12
    lobby.start({'level': True})
    game.rows = [row('one'), row('two', 2, False)]; ticks(lobby)
    assert lobby.session_joins == 2 and lobby.lifetime_joins == 14
    game.rows = [row('two', 1, False)]; ticks(lobby)
    game.rows.append(row('one', 2)); ticks(lobby)
    assert lobby.session_joins == 3 and saved == [13, 14, 15]
    lobby.stop(); lobby.start({'level': True}); ticks(lobby)
    assert lobby.session_joins == 2 and lobby.lifetime_joins == 17


def test_counter_read_failure_never_overwrites_original():
    game = FakeGame(); saved = []
    def fail(): raise ValueError('corrupt file')
    game.load_join_count = fail; game.save_join_count = saved.append
    lobby = module.Lobby(game); lobby.start({'level': True})
    game.rows = [row('one')]; ticks(lobby)
    assert lobby.session_joins == 1 and lobby.lifetime_joins is None
    assert lobby.status()['counter_error'] == 'corrupt file' and not saved


def test_connection_roots_use_native_parent_and_unknown_fallback():
    parent = SimpleNamespace()
    assert module.Game.connection_root(SimpleNamespace(NetConnection=SimpleNamespace(Parent=parent))) is parent
    assert module.Game.connection_root(SimpleNamespace(NetConnection=parent)) is parent
    assert module.Game.connection_root(SimpleNamespace()) is None


def test_review_only_guest_can_kick_after_saved_report(monkeypatch):
    clock=[100.0];monkeypatch.setattr(module.time,'monotonic',lambda:clock[0])
    game=FakeGame();lobby=module.Lobby(game)
    game.save_run_report=lambda job:'saved-report.json'
    game.step=lambda *args:dict(ok=False,review_kick_allowed=True,message='New loot review')
    lobby.start(dict(loot=True,auto_kick=True));game.rows=[row('guest')]
    ticks(lobby);assert not game.kicked
    clock[0]+=16;ticks(lobby);assert game.kicked==['guest']
    assert 'needs review' in lobby.history[0]['message']


def test_review_kick_does_not_require_saved_report():
    game=FakeGame();lobby=module.Lobby(game)
    game.step=lambda *args:dict(ok=False,review_kick_allowed=True,message='New loot review')
    lobby.start(dict(level=True,auto_kick=True));game.rows=[row('guest')]
    ticks(lobby);assert game.kicked == ['guest'] and lobby.completed[0]['failed']


def test_any_terminal_errors_and_report_write_failure_still_auto_kick(monkeypatch):
    clock=[100.0];monkeypatch.setattr(module.time,'monotonic',lambda:clock[0])
    game=FakeGame();lobby=module.Lobby(game)
    game.step=lambda *args:dict(ok=False,message='Original return unverified')
    def report(job):raise OSError('disk full')
    game.save_run_report=report
    lobby.start(dict(loot=True,auto_kick=True));game.rows=[row('guest')]
    ticks(lobby);assert not game.kicked
    clock[0]+=16;ticks(lobby)
    assert game.kicked==['guest']
    assert 'disk full' in lobby.history[0]['report_error']
    assert not lobby.history[0]['results'][0]['ok']


def test_item_level_override_reaches_both_pools_and_is_saved():
    game = FakeGame()
    prepared = []
    game.prepare_loot = lambda p: prepared.append(dict(p)) or ['serial']
    lobby = module.Lobby(game)
    assert lobby.start({'loot':True, 'codes':'pool', 'guaranteed_codes':'guaranteed',
                        'serial_override_level':True, 'serial_level':35})['ok']
    assert len(prepared) == 2
    assert all(p['serial_override_level'] and p['serial_level'] == 35 for p in prepared)
    assert lobby.config['serial_level'] == 35
    assert lobby.config['serial_override_level'] is True


def test_item_level_override_rejects_invalid_levels_before_preparing():
    for level in (0,71,True,1.5,'bad'):
        game=FakeGame()
        game.prepare_loot=lambda p: (_ for _ in ()).throw(AssertionError('prepared invalid level'))
        result=module.Lobby(game).start({'loot':True,'serial_override_level':True,'serial_level':level})
        assert not result['ok'] and 'Item level' in result['message']


def test_item_level_override_uses_existing_rewriter_and_fails_without_partial_list():
    import pytest
    game=module.Game()
    backend=SimpleNamespace(_parse_serial_text=lambda s:s.splitlines(),
        serial_rewards=SimpleNamespace(_resolve_give_serial_strings=lambda s:s),
        _serials_with_level_override=lambda s,enabled,level:([f'{x}-L{level}' for x in s],len(s),[]))
    game.backend=lambda:backend
    assert game.prepare_loot({'codes':'A\nA','serial_override_level':True,'serial_level':35}) == ['A-L35','A-L35']
    assert game.prepare_loot({'codes':'A\nA'}) == ['A','A']
    backend._serials_with_level_override=lambda *a:(['A'],1,['serial #2 invalid'])
    with pytest.raises(ValueError,match='Could not override item level'):
        game.prepare_loot({'codes':'A\nB','serial_override_level':True,'serial_level':35})
