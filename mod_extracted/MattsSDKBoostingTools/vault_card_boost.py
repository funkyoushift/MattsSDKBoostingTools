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
        _CURRENCY_KIND_ALIASES,
        _MAX_WALLET_AMOUNT,
        _give_currency_on_pc,
        _set_experience_level_via_bp,
    )

    ps = getattr(target_pc, "PlayerState", None)
    if ps is None:
        return False, "no PlayerState"

    ok_bits: list[str] = []
    fail = False

    for kind in ("vaultcard1", "vaultcard2", "vaultcard3"):
        token = _CURRENCY_KIND_ALIASES.get(kind)
        if token and _give_currency_on_pc(target_pc, token, _MAX_WALLET_AMOUNT):
            ok_bits.append(f"{kind}=direct GiveCurrency")
        else:
            fail = True

    for slot, label in ((2, "vaultcard_xp_1"), (3, "vaultcard_xp_2"), (4, "vaultcard_xp_3")):
        if _set_experience_level_via_bp(ps, slot, _MAX_VAULT_XP_LEVEL):
            ok_bits.append(f"{label}=BP_SetLevel")
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

    from .player_economy import _CURRENCY_KIND_ALIASES, _give_currency_on_pc, _set_experience_level_via_bp

    ok_bits: list[str] = []
    token = _CURRENCY_KIND_ALIASES.get("vaultcard3")
    if token and _give_currency_on_pc(target_pc, token, _MAX_WALLET):
        ok_bits.append("vaultcard3=direct GiveCurrency")
    if _set_experience_level_via_bp(ps, 4, _MAX_VAULT_XP_LEVEL):
        ok_bits.append("vaultcard_xp_3=BP_SetLevel")
    if len(ok_bits) >= 2:
        return True, ", ".join(ok_bits)
    return False, ", ".join(ok_bits) or "vaultcard3 direct fallback made no writes"
