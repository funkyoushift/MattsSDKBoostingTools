"""Read-only, JSON-safe player snapshot. Call only on the game thread."""
import time


def read_player(pc, expected_name, name_reader, economy):
    result = {"available": False, "name": expected_name, "sampled_at": time.time(),
              "level": None, "specialization": None, "currencies": {}, "vault_cards": []}
    if pc is None:
        return result
    try:
        ps = pc.PlayerState
        if name_reader(ps) != expected_name:
            return result
    except Exception:
        return result
    result["available"] = True
    try:
        for row in ps.ExperienceState:
            token = economy._experience_state_token_name(row)
            if not token:
                continue
            rank = int(ps.BP_GetExperienceLevel(economy._make_experience_def_ptr(token)))
            if token == "Character":
                result["level"] = rank
            elif token == "Specialization":
                result["specialization"] = rank
            else:
                for i in range(1, 6):
                    if token == f"VaultCard{i:02d}_Experience":
                        result["vault_cards"].append({"card": i, "rank": rank,
                                                       "active": bool(row.bIsUnlocked)})
    except Exception:
        pass
    try:
        for row in pc.CurrencyManager.currencies:
            token = str(row.type.Name)
            if token in ("Cash", "eridium") or token in [f"VaultCard{i:02d}_Tokens" for i in range(1, 6)]:
                result["currencies"][token] = int(row.Amount)
    except Exception:
        pass
    return result
