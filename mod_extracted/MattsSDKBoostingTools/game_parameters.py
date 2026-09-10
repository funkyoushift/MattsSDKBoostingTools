"""Shared bridge-safe game limits and experience-track identifiers.

The September 10, 2026 v1.10 update adds ten levels to March's level-60 cap
and introduces Vault Card 5. Source: https://borderlands.2k.com/borderlands-4/update-notes/
Caps and Vault Card 5 identifiers were also verified in installed build 25234898:
Nexus-Data-xp_progression0, Nexus-Data-Capital0 and Nexus-Data-vault_cards0.
These describe the bundled data, not a claim that the running game was inspected.
"""

from __future__ import annotations

import re
from typing import Any

MAX_PLAYER_LEVEL = 70
MAX_ITEM_LEVEL = 70
MAX_SPEC_LEVEL = 701
MAX_VAULT_CARD_LEVEL = 9_999
VAULT_CARD_COUNT = 5
CURRENCY_KINDS = ["cash", "eridium", *(f"vaultcard{n}" for n in range(1, VAULT_CARD_COUNT + 1))]
EXP_TRACKS = ["player", "specialization", *(f"vaultcard_xp_{n}" for n in range(1, VAULT_CARD_COUNT + 1))]


def status_parameters() -> dict[str, Any]:
    return {
        "game_update": "2026-09-10",
        "game_version": "1.10",
        "source": "installed_game_data",
        "extracted_game_build": "25234898",
        "player_level_cap": MAX_PLAYER_LEVEL,
        "item_level_cap": MAX_ITEM_LEVEL,
        "specialization_level_cap": MAX_SPEC_LEVEL,
        "vault_card_level_cap": MAX_VAULT_CARD_LEVEL,
        "vault_card_count": VAULT_CARD_COUNT,
        "currency_kinds": list(CURRENCY_KINDS),
        "experience_tracks": list(EXP_TRACKS),
    }


def experience_token_name(row: Any) -> str | None:
    """Read the game's own token from a reflected ExperienceState row."""
    try:
        token = getattr(row, "ExperienceId", None)
    except Exception:
        return None
    if token is None:
        return None
    for attr in ("Name", "name"):
        try:
            value = getattr(token, attr)
            if isinstance(value, str) and value:
                return value
        except Exception:
            pass
    try:
        match = re.search(r'''Name:\s*['"]([^'"]+)['"]''', str(token))
        return match.group(1) if match else None
    except Exception:
        return None


def experience_track_for_token(token: str | None) -> int | None:
    if not token:
        return None
    key = token.rsplit("/", 1)[-1].casefold()
    if key == "character":
        return 0
    if key in ("specialization", "specialisation"):
        return 1
    match = re.fullmatch(r"vaultcard0*(\d+)(?:_xp|_experience)?", key)
    if match and 1 <= int(match.group(1)) <= VAULT_CARD_COUNT:
        return int(match.group(1)) + 1
    return None


def experience_row_for_track(rows: Any, track: int) -> Any | None:
    """Resolve by token so added/reordered tracks cannot redirect a level write.

    Legacy rows whose tokens cannot be read keep the established slot fallback.
    The new fifth card requires a matching live token until its layout is known.
    """
    if rows is None or track < 0 or track >= len(EXP_TRACKS):
        return None
    try:
        for row in rows:
            if experience_track_for_token(experience_token_name(row)) == track:
                return row
        row = rows[track]
    except Exception:
        return None
    if track < 6 and experience_token_name(row) is None:
        return row
    return None
