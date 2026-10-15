"""Session-only manual dialogue skipping on the shared game-thread pump."""
import os
import time

from .progress_dialogue import DialogueSkipper

NAME = 'dialogue_skip'
_enabled = False
_next_at = 0.
_skipper = DialogueSkipper()
_runtime = None


def status():
    detail = _skipper.status()
    return dict(ok=not detail['disabled'], enabled=_enabled, **detail,
                message=('Dialogue skip stopped: ' + detail['error'] if detail['disabled'] else
                         'Experimental dialogue skip is on. Native line completion requests: '+str(detail['completion_requests'])+
                         '. Native dialogue thread ends observed: '+str(detail['native_thread_ends'])+
                         '. Authored timed sequences may remain.' if _enabled else 'Dialogue skip is off.'))


def set_enabled(enabled):
    global _enabled, _next_at, _skipper
    if type(enabled) is not bool:
        return dict(ok=False, message='Choose on or off for dialogue skip.')
    from . import camera_tick
    if enabled != _enabled or _skipper.disabled:
        _skipper = DialogueSkipper()
        _next_at = 0.
    _enabled = enabled
    camera_tick.register(NAME, _tick, priority=95)
    camera_tick.set_needed(NAME, enabled)
    return status()


def clear_runtime_state():
    global _runtime
    set_enabled(False)
    _runtime = None


def _tick(*_args):
    global _enabled, _next_at, _runtime
    now = time.monotonic()
    if not _enabled or now < _next_at:
        return
    _next_at = now + .25
    try:
        from mods_base import get_pc
        from .travel_gate import is_travel_quiet
        if is_travel_quiet():
            return
        pc = get_pc(possibly_loading=True)
        if pc is None or pc.Pawn is None:
            return
        world = pc.GetLevel().OwningWorld
        if world is None or world._path_name().startswith('/Engine/') or not pc._path_name().startswith(world._path_name() + ':'):
            return
        # A client cannot own the replicated dialogue performance.
        if not pc.HasAuthority():
            raise RuntimeError('Dialogue skip requires the host or a solo game')
        import unrealsdk
        providers = unrealsdk.find_all('GbxDialogProvider', exact=False)
        from .dialogue_native import complete
        if _runtime is None:
            from .mission_runtime import MissionRuntime
            _runtime = MissionRuntime()
        # This reader only supplies executable identity/code reads. Dialogue has
        # its own current-PC/world guard; never borrow a mission job's world binding.
        engine = _runtime
        dialog = unrealsdk.find_object('GbxDialogBlueprintLibrary','/Script/GbxGame.Default__GbxDialogBlueprintLibrary')
        _skipper.poll((os.getpid(), world._get_address()), world._path_name(), providers, now,
                      finish_performance=lambda provider,thread:complete(provider,engine,thread),
                      thread_playing=lambda thread:bool(dialog.IsDialogThreadPlaying(pc,thread)))

    except Exception as exc:
        _skipper.disabled = True
        _skipper.error = str(exc)
    if _skipper.disabled:
        _enabled = False
        from . import camera_tick
        camera_tick.set_needed(NAME, False)
