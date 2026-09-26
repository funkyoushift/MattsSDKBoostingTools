"""AFK class restrictions from extracted inventory definitions, not display names."""
import json
import pkgutil

_roots = None


def roots():
    global _roots
    if _roots is None:
        data = pkgutil.get_data(__package__, "afk_loot_classes.json")
        _roots = json.loads(data)["roots"]
    return _roots


def classify_serials(serials):
    from .serial_converter import _read_header_numbers
    definitions = roots()
    result = []
    cache = {}
    for index, serial in enumerate(serials, 1):
        if serial not in cache:
            # Classification needs only the type header, not the part payload.
            try:
                numbers, _ = _read_header_numbers(serial)
            except (ValueError, EOFError) as exc:
                raise ValueError(f"Cannot read AFK item code {index}: {exc}") from exc
            row = definitions.get(str(numbers[0]))
            # Unknown/new inventory roots are excluded, never guessed to be
            # ordinary items which could bypass the class-mod filter.
            cache[serial] = row["class"] if row is not None else "unknown_item"
        result.append(cache[serial])
    return result


def player_class(pc, ps, pawn):
    known = {row["class"] for row in roots().values() if row["class"] not in (None, "unknown_class")}
    # GbxPlayerState.ReplicatedCharacterDef is a NameProperty in the native
    # schema. Class mods name the corresponding Char_* in their class aspect.
    # No pawn-name matching: cosmetics, proxies and vehicles are not classes.
    try:
        value = str(ps.ReplicatedCharacterDef)
        if value in known:
            return value
    except Exception:
        pass
    return None


def select_loot(serials, classes, character, random_mode, rng, guaranteed=(), guaranteed_classes=()):
    if len(serials) != len(classes) or len(guaranteed) != len(guaranteed_classes):
        raise ValueError("AFK loot classifications do not match the pool. Restart AFK.")
    restricted = any(value not in (None, "unknown_item") for value in (*classes, *guaranteed_classes))
    if restricted and not character:
        raise ValueError("Waiting for the guest's character class; no loot sent.")
    def compatible(value):
        return value is None or value == character and character is not None
    fixed_indices = [i for i, value in enumerate(guaranteed_classes) if compatible(value)]
    fixed = [guaranteed[i] for i in fixed_indices]
    fixed_codes = set(fixed)
    eligible = [i for i, value in enumerate(classes) if compatible(value) and serials[i] not in fixed_codes]
    matching = [i for i in eligible if classes[i] == character and character is not None]
    fixed_has_class_mod = any(guaranteed_classes[i] == character and character is not None for i in fixed_indices)
    if not eligible and not fixed:
        raise ValueError("No compatible items in the AFK pool for this character; no loot sent.")
    if not random_mode:
        indices = eligible
    else:
        count = min(max(0, 70 - len(fixed)), len(eligible))
        if matching and not fixed_has_class_mod:
            if count == 0:
                raise ValueError("Guaranteed items leave no slot for a matching class mod. Remove one guaranteed item or include a matching class mod in that list.")
            guaranteed = rng.choice(matching)
            indices = [guaranteed] + rng.sample([i for i in eligible if i != guaranteed], count - 1)
            rng.shuffle(indices)
        else:
            indices = rng.sample(eligible, count)
    return fixed + [serials[i] for i in indices], len(serials) - len(eligible) + len(guaranteed_classes) - len(fixed)
