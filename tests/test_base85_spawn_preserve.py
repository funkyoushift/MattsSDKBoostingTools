"""Regression tests for Spawn-In Base85 payload preservation."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"
sys.path.insert(0, str(PKG))

# Stub SDK-only deps so serial_rewards can import offline.
for name in ("unrealsdk", "unrealsdk.unreal", "mods_base"):
    sys.modules.setdefault(name, types.ModuleType(name))
u = sys.modules["unrealsdk"]
u.find_all = u.find_class = u.find_object = u.make_struct = lambda *a, **k: None
u.logging = types.SimpleNamespace(info=print, warning=print, error=print)
sys.modules["unrealsdk.unreal"].FGbxDefPtr = object
sys.modules["unrealsdk.unreal"].UObject = object
mb = sys.modules["mods_base"]

class _Cmd:
    def add_argument(self, *a, **k):
        return None

def _command(*a, **k):
    def deco(f):
        f.add_argument = _Cmd().add_argument
        return f
    return deco

mb.command = _command
mb.get_pc = lambda: None
mb.hook = lambda *a, **k: (lambda f: f)

pkg = types.ModuleType("MattsSDKBoostingTools")
pkg.__path__ = [str(PKG)]
sys.modules["MattsSDKBoostingTools"] = pkg

spec_sc = importlib.util.spec_from_file_location(
    "MattsSDKBoostingTools.serial_converter", PKG / "serial_converter.py"
)
sc = importlib.util.module_from_spec(spec_sc)
sys.modules["MattsSDKBoostingTools.serial_converter"] = sc
spec_sc.loader.exec_module(sc)

ph = types.ModuleType("MattsSDKBoostingTools.party_helpers")
for n in (
    "_gbc_find_pc_for_player_state",
    "_gbc_resolve_player_display_name",
    "_gbc_resolve_player_index_for_name_substring",
    "_gbc_run_session_timer_from_give_serial",
    "_gbc_session_world_and_gamestate",
):
    setattr(ph, n, lambda *a, **k: None)
sys.modules["MattsSDKBoostingTools.party_helpers"] = ph

inv = types.ModuleType("MattsSDKBoostingTools.inventory_capacity")
inv.set_backpack_size_for_player_state = lambda *a, **k: None
sys.modules["MattsSDKBoostingTools.inventory_capacity"] = inv

spec_sr = importlib.util.spec_from_file_location(
    "MattsSDKBoostingTools.serial_rewards", PKG / "serial_rewards.py"
)
sr = importlib.util.module_from_spec(spec_sr)
sys.modules["MattsSDKBoostingTools.serial_rewards"] = sr
spec_sr.loader.exec_module(sr)

# backend_actions pulls many deps; replicate only _parse_serial_text logic here
# by importing after lighter stubs where possible. Prefer serial_rewards helpers.

SAMPLE = "@Ugv4Ng35E/MjE@Uii%N$/RHKFprA5_4-9wc" + chr(96) + "g+aAJ)j{1stwPmA00"


def parse_serial_text(raw: object) -> list[str]:
    tokens: list[str] = []
    for line in str(raw or "").strip().splitlines():
        text = sr._strip_wrapping_markdown_backticks(line.strip())
        if not text:
            continue
        if "|" in text:
            tokens.append(text)
            continue
        parts = [sr._strip_wrapping_markdown_backticks(part) for part in text.split()]
        parts = [part for part in parts if part]
        if len(parts) > 1 and all(part.startswith("@U") for part in parts):
            tokens.extend(parts)
            continue
        tokens.append(text)
    return tokens


def test_spawn_input_preserves_backtick_and_mid_at_u():
    forwarded = parse_serial_text(SAMPLE)
    assert forwarded == [SAMPLE], forwarded
    assert "`" in forwarded[0]
    assert forwarded[0].endswith("A00")
    assert forwarded[0].find("`") == SAMPLE.find("`")
    human = sc.serial_to_human(forwarded[0])
    assert "{1:10}" in human
    assert sr._resolve_give_serial_strings(forwarded) == [SAMPLE]


def test_no_o_to_0_substitution():
    bad = SAMPLE[:-2] + "OO"
    assert sr._resolve_give_serial_strings([bad]) is None


def test_whitespace_separated_serials_still_split():
    a = SAMPLE
    b = "@Uge8^+m/*xI!fYv^M>VQ_G&;nG^Z)"
    out = parse_serial_text(f"{a} {b}")
    assert out == [a, b]


def test_outer_markdown_backticks_only():
    wrapped = "`" + SAMPLE + "`"
    assert sr._strip_wrapping_markdown_backticks(wrapped) == SAMPLE
    # Interior backtick must survive
    assert "`" in sr._strip_wrapping_markdown_backticks(wrapped)


def test_expand_token_preserves_mid_at_u():
    assert sr._expand_serial_token(SAMPLE) == [SAMPLE]


if __name__ == "__main__":
    test_spawn_input_preserves_backtick_and_mid_at_u()
    test_no_o_to_0_substitution()
    test_whitespace_separated_serials_still_split()
    test_outer_markdown_backticks_only()
    test_expand_token_preserves_mid_at_u()
    print("ALL TESTS PASSED")
