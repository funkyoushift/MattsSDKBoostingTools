"""Explicit local trial service. Game-thread calls only; no network on import.

The cache is scoped to this enable/session. It is not portable across game
builds, hotfix states, locales or player contexts. No inventory writes.
"""
from collections import OrderedDict
import ctypes as C
import json
import uuid
from .native_sdk_card_probe import run

MAX_ENTRIES = 512
MAX_BYTES = 32 * 1024 * 1024
SCHEMA = 'native-standalone-widget-v1'
PROFILE_REVISION = 'native-card-profiles-20261008'
_thread = None
_session = None
_cache = OrderedDict()
_bytes = 0
_builds = 0
_profile = None


def thread_id():
    kernel=C.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentThreadId.restype=C.c_ulong
    return kernel.GetCurrentThreadId()


def enable(*, expected_game_thread):
    """Call only from an independently verified SDK game-thread entry point."""
    global _thread,_session,_bytes,_builds,_profile
    if not expected_game_thread or thread_id()!=expected_game_thread:
        raise RuntimeError('Native preview must be enabled on the verified game thread')
    _thread=expected_game_thread
    _session=uuid.uuid4().hex
    _cache.clear()
    _bytes=_builds=0
    _profile=None
    return status()


def bind_game_thread():
    """Called exclusively by the registered SDK tick hook, never HTTP workers."""
    if _thread is None:
        enable(expected_game_thread=thread_id())


def status():
    return dict(ok=True,enabled=_thread is not None,session=_session,schema=SCHEMA,
                profile_revision=PROFILE_REVISION,
                build_profile=_profile,
                entries=len(_cache),bytes=_bytes,builds=_builds,
                context='standalone; no loadout or comparison')


def preview(serial):
    global _bytes,_builds,_profile
    if _thread is None or thread_id()!=_thread:
        raise RuntimeError('Native preview is disabled or called from the wrong thread')
    if not isinstance(serial,str) or not serial.startswith('@U') or not serial.isascii() or len(serial)>8192:
        raise ValueError('Expected an exact encoded item serial')
    cached=_cache.get(serial)
    if cached is not None:
        _cache.move_to_end(serial)
        return dict(ok=True,serial=serial,session=_session,schema=SCHEMA,
                    cached=True,widget=json.loads(cached))
    report=run(serial,None,expected_game_thread=_thread,include_widget=True,
               compare_self=False,export_model=False)
    widget=report['default_widget']
    encoded=json.dumps(widget,ensure_ascii=False,allow_nan=False).encode('utf-8')
    _profile=report['profile']
    _builds+=1
    if len(encoded)<=MAX_BYTES:
        while _cache and (len(_cache)>=MAX_ENTRIES or _bytes+len(encoded)>MAX_BYTES):
            _,old=_cache.popitem(last=False)
            _bytes-=len(old)
        _cache[serial]=encoded
        _bytes+=len(encoded)
    return dict(ok=True,serial=serial,session=_session,schema=SCHEMA,cached=False,
                elapsed_ms=report['elapsed_ms'],widget=widget)
