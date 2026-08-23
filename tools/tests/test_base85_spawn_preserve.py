"""Regression tests for Spawn-In Base85 payload preservation."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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
    # Letter O is alphabet-legal; we must not auto-repair it to digit 0.
    bad = SAMPLE[:-2] + "OO"
    resolved = sr._resolve_give_serial_strings([bad])
    assert resolved == [bad]
    assert resolved[0].endswith("OO")
    assert not resolved[0].endswith("00")


def test_rejects_non_alphabet_base85():
    bad = SAMPLE[:-1] + "\u00b4"  # acute accent, not in BL4 alphabet
    assert sr._resolve_give_serial_strings([bad]) is None
    bad_ascii = SAMPLE[:-1] + "|"  # printable ASCII but not in alphabet
    assert sr._resolve_give_serial_strings([bad_ascii]) is None


def test_skips_bad_keeps_good_in_batch():
    bad = SAMPLE[:-1] + "\u00b4"
    assert sr._resolve_give_serial_strings([bad, SAMPLE]) == [SAMPLE]


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


def _sample_human() -> str:
    return sc.serial_to_human(SAMPLE)


def _space_header(human: str) -> str:
    match = __import__("re").match(
        r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\|",
        human,
    )
    assert match, human[:80]
    return f"{match.group(1)} {match.group(2)} {match.group(3)} {match.group(4)}|{human[match.end():]}"


def test_human_comma_encodes_locally_without_http():
    human = _sample_human()
    assert sr._looks_like_deserialized_human(human)
    original = sr._serialize_deserialized_to_b85
    sr._serialize_deserialized_to_b85 = lambda *_a, **_k: (_ for _ in ()).throw(
        AssertionError("HTTP serialize should not run when local encode works")
    )
    try:
        out = sr._resolve_give_serial_strings([human])
    finally:
        sr._serialize_deserialized_to_b85 = original
    assert out and len(out) == 1
    assert out[0].startswith("@U")
    assert sr.needs_async_serial_resolution([human]) is False


def test_human_space_head_encodes_locally():
    spaced = _space_header(_sample_human())
    assert sr._looks_like_deserialized_human(spaced)
    assert "," not in spaced.split("|", 1)[0]
    original = sr._serialize_deserialized_to_b85
    sr._serialize_deserialized_to_b85 = lambda *_a, **_k: (_ for _ in ()).throw(
        AssertionError("HTTP serialize should not run when local encode works")
    )
    try:
        out = sr._resolve_give_serial_strings([spaced])
    finally:
        sr._serialize_deserialized_to_b85 = original
    assert out and out[0].startswith("@U")


def test_bad_human_keeps_good_base85():
    import os

    os.environ["GENIE_SERIALIZE_ENABLED"] = "0"
    try:
        out = sr._resolve_give_serial_strings(["7, 0, 1, 60| {{{broken", SAMPLE])
    finally:
        os.environ.pop("GENIE_SERIALIZE_ENABLED", None)
    assert out == [SAMPLE]


def test_needs_async_when_local_fails_and_genie_on():
    import os

    os.environ["GENIE_SERIALIZE_ENABLED"] = "1"
    try:
        assert sr.needs_async_serial_resolution(["7, 0, 1, 60| {{{broken"]) is True
    finally:
        os.environ.pop("GENIE_SERIALIZE_ENABLED", None)
    os.environ["GENIE_SERIALIZE_ENABLED"] = "0"
    try:
        assert sr.needs_async_serial_resolution(["7, 0, 1, 60| {{{broken"]) is False
    finally:
        os.environ.pop("GENIE_SERIALIZE_ENABLED", None)


if __name__ == "__main__":
    test_spawn_input_preserves_backtick_and_mid_at_u()
    test_no_o_to_0_substitution()
    test_rejects_non_alphabet_base85()
    test_skips_bad_keeps_good_in_batch()
    test_whitespace_separated_serials_still_split()
    test_outer_markdown_backticks_only()
    test_expand_token_preserves_mid_at_u()
    test_human_comma_encodes_locally_without_http()
    test_human_space_head_encodes_locally()
    test_bad_human_keeps_good_base85()
    test_needs_async_when_local_fails_and_genie_on()
    print("ALL TESTS PASSED")
