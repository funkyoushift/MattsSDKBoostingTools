"""Vault card 1/2/3 max for boosting mods — ULM struct writes + economy fallback."""

from __future__ import annotations

from typing import Any, Callable

_MAX_WALLET = 2_147_483_647
_MAX_VAULT_XP_LEVEL = 9_999_999


def _economy_max_vault_cards(
    target_pc: Any,
    *,
    log: Callable[[str], None],
) -> tuple[bool, str]:
    from .player_economy import (
        _MAX_WALLET_AMOUNT,
        _do_give_currency,
        _do_give_experience,
        _set_experience_level_via_bp,
    )

    ps = getattr(target_pc, "PlayerState", None)
    if ps is None:
        return False, "no PlayerState"

    name = ""
    try:
        name = str(getattr(ps, "PlayerName", None) or getattr(ps, "Name", "") or "").strip()
    except Exception:  # noqa: BLE001
        name = ""

    ok_bits: list[str] = []
    fail = False

    for kind in ("vaultcard1", "vaultcard2", "vaultcard3"):
        if name:
            _do_give_currency(kind, _MAX_WALLET_AMOUNT, name)
            ok_bits.append(f"{kind}=GiveCurrency")
        else:
            fail = True

    for track in ("vaultcard_xp_1", "vaultcard_xp_2", "vaultcard_xp_3"):
        if name:
            _do_give_experience(track, _MAX_VAULT_XP_LEVEL, name)
            ok_bits.append(f"{track}=BP_SetLevel")
        else:
            fail = True

    es = getattr(ps, "ExperienceState", None)
    if es is not None:
        try:
            n = len(es)
        except Exception:  # noqa: BLE001
            n = 0
        for slot in range(2, min(n, 5)):
            if _set_experience_level_via_bp(ps, slot, _MAX_VAULT_XP_LEVEL):
                ok_bits.append(f"slot{slot}=BP")
            else:
                fail = True

    summary = ", ".join(ok_bits) if ok_bits else "no writes"
    return not fail, summary


def max_all_vault_cards_for_pc(
    target_pc: Any,
    *,
    log: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """Max all vault cards (tokens + XP) on one PlayerController."""
    log_fn = log or (lambda _m: None)
    ps = getattr(target_pc, "PlayerState", None)
    if ps is None:
        return False, "no PlayerState on target PlayerController"

    try:
        from ultra_local_menu.vault_cards import apply_max_to_all_vault_cards

        ok, bits = apply_max_to_all_vault_cards(target_pc, ps, selector="all")
        summary = "; ".join(bits[:14])
        if ok:
            log_fn(f"Vault cards max (ULM): {summary}")
            return True, summary
        log_fn(f"Vault cards max partial (ULM): {summary}")
    except Exception as exc:  # noqa: BLE001
        log_fn(f"ULM vault_cards unavailable ({exc!r}) — using economy fallback")

    ok, summary = _economy_max_vault_cards(target_pc, log=log_fn)
    log_fn(f"Vault cards max (economy): {summary}")
    return ok, summary


def max_vault_card_three_for_pc(
    target_pc: Any,
    *,
    log: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """Max Raid 3 / vault card 3 only."""
    log_fn = log or (lambda _m: None)
    ps = getattr(target_pc, "PlayerState", None)
    if ps is None:
        return False, "no PlayerState"

    try:
        from ultra_local_menu.vault_cards import apply_max_to_all_vault_cards

        ok, bits = apply_max_to_all_vault_cards(target_pc, ps, selector="raid3")
        summary = "; ".join(bits[:10])
        log_fn(f"Vault card 3 (ULM): {summary}")
        if ok:
            return True, summary
    except Exception as exc:  # noqa: BLE001
        log_fn(f"ULM raid3 path failed ({exc!r}) — economy fallback")

    from .player_economy import _do_give_currency, _do_give_experience

    name = str(getattr(ps, "PlayerName", None) or getattr(ps, "Name", "") or "").strip()
    if not name:
        return False, "could not resolve player name for economy commands"
    _do_give_currency("vaultcard3", _MAX_WALLET, name)
    _do_give_experience("vaultcard_xp_3", _MAX_VAULT_XP_LEVEL, name)
    return True, "vaultcard3 tokens + XP via GiveCurrency/BP_SetExperienceLevel"
