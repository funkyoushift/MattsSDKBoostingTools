"""Exact, offline-qualified mission build profiles. Unknown builds fail closed.

Source executable hashes, complete normalized bodies and RIP/vtable evidence:
docs/native-missions/EPIC_PROFILE.json, STEAM_26007962_PROFILE.json and
EPIC_6D531D91_PROFILE.json.
The new Steam profile has three reviewed native field-displacement bytes; its
live execution is not established by offline comparisons. This module never
scans runtime memory.
"""
import json
from importlib.resources import files

PROFILES = json.loads(files(__package__).joinpath('mission_build_profiles.json').read_text())
STEAM = 'steam-25372571'
STEAM_26007962 = 'steam-26007962'
EPIC = 'epic-4845623'


def select_profile(digest):
    matches = [key for key, value in PROFILES.items() if value['sha256'] == digest]
    if len(matches) != 1:
        raise RuntimeError('Unsupported executable; no snapshot taken')
    return matches[0]


def _profile(runtime):
    key = getattr(runtime, 'profile', None)
    if key not in PROFILES:
        raise RuntimeError('Mission executable profile is unavailable; no native operation issued')
    return PROFILES[key]


def native_address(runtime, source_rva):
    value = _profile(runtime)['addresses'].get(hex(source_rva))
    if value is None:
        raise RuntimeError('Unmapped mission native address: '+hex(source_rva))
    return runtime.base + int(value, 16)


def native_fingerprint(runtime, source_rva, source_expected):
    """Translate an existing source gate only when its recorded evidence agrees."""
    key = hex(source_rva)
    source = source_expected.hex() if isinstance(source_expected, bytes) else source_expected
    recorded = PROFILES[STEAM]['fingerprints'].get(key)
    if not source or recorded is None or not recorded.startswith(source):
        raise RuntimeError('Mission source fingerprint evidence mismatch: '+key)
    target = _profile(runtime)['fingerprints'].get(key)
    if target is None:
        raise RuntimeError('Unmapped mission native fingerprint: '+key)
    target = target[:len(source)]
    return bytes.fromhex(target) if isinstance(source_expected, bytes) else target
