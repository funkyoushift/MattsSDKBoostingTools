"""Game-thread lifecycle for the opt-in SHiFT background view."""
from __future__ import annotations

import itertools
import re
import threading
import time

_TOKEN = re.compile(r"^[0-9a-f]{32}$")
_LEASE = 5.0
_MAX_RESTORE_ATTEMPTS = 3


class BackgroundController:
    def __init__(self, native, sdk, get_pc, clock=time.monotonic, error=None):
        self.native, self.sdk, self.get_pc, self.clock = native, sdk, get_pc, clock
        self.report_error = error
        self._lock = threading.RLock()
        self._state = 'idle' if native is not None else 'unsupported'
        self._reason = '' if native is not None else 'Background view is unavailable.'
        self._failure_reason = ''
        self._token = None
        self._deadline = 0.0
        self._command = None
        self._pc = self._pawn = None
        self._attempts = 0
        self._stop_foreground = False
        self._stop_close = True
        self._thread = None
        self._closing = False
        self._ownership = False
        self._shutdown = False
        self._tick_running = False

    def status(self):
        with self._lock:
            return {'available': self._state != 'unsupported', 'state': self._state,
                    'reason': self._reason, 'token': self._token}

    @property
    def quiescent(self):
        with self._lock:
            return not self._ownership and not self._closing and self._command is None and self._state not in ('pending', 'stopping')

    def _owned(self):
        return bool(self.native is not None and self.native.owned)

    def request(self, payload):
        if not isinstance(payload, dict) or set(payload) != {'mode', 'token'}:
            return {'ok': False, 'error': 'Invalid request.'}
        mode, token = payload['mode'], payload['token']
        if mode not in ('start', 'heartbeat', 'stop') or not isinstance(token, str) or not _TOKEN.fullmatch(token):
            return {'ok': False, 'error': 'Invalid request.'}
        with self._lock:
            now = self.clock()
            if self._state == 'unsupported' or self._shutdown:
                return {'ok': False, 'error': 'Background view is unavailable.'}
            if mode == 'start':
                if self._state in ('pending', 'active') and now < self._deadline:
                    if token != self._token:
                        return {'ok': False, 'error': 'Another page owns the background view.'}
                    return {'ok': True, **self.status()}
                if self._state in ('pending', 'active', 'stopping') or self._ownership or self._closing:
                    return {'ok': False, 'error': 'Previous background session is stopping.'}
                # This lease controls presentation/input only. Protected-list
                # review gates destructive removal in the page, not accepting.
                self._token, self._deadline = token, now + _LEASE
                self._state, self._reason, self._command = 'pending', '', 'start'
                self._failure_reason = ''
            elif mode == 'heartbeat':
                if token != self._token or self._state not in ('pending', 'active') or now >= self._deadline:
                    return {'ok': False, 'error': 'Background session is not active.'}
                self._deadline = now + _LEASE
            else:
                if token != self._token or self._state not in ('pending', 'active', 'stopping'):
                    return {'ok': False, 'error': 'Background session is not active.'}
                self._state, self._command = 'stopping', 'stop'
            return {'ok': True, **self.status()}

    def _bind(self, allow_bind=False):
        ident = threading.get_ident()
        if self._thread is None:
            if not allow_bind:
                raise RuntimeError('Background game thread has not been pinned.')
            self.native.bind_thread()
            self._thread = ident
        elif self._thread != ident:
            raise RuntimeError('Background lifecycle must run on its game thread.')

    def _class_default(self, name):
        cls = self.sdk.find_class(name)
        if cls is None or cls.ClassDefaultObject is None:
            raise RuntimeError('Required game interface is unavailable.')
        return cls.ClassDefaultObject

    def _check_contexts(self, pc):
        if pc is None or getattr(pc, 'Player', None) is None or getattr(pc, 'Pawn', None) is None:
            raise RuntimeError('A local player and pawn are required.')
        subs = list(itertools.islice(self.sdk.find_all('EnhancedInputLocalPlayerSubsystem', False), 129))
        if len(subs) > 128:
            raise RuntimeError('Input subsystem scan exceeded its limit.')
        subs = [s for s in subs if not str(s.Name).startswith('Default__') and s.Outer == pc.Player]
        if len(subs) != 1:
            raise RuntimeError('A unique local input subsystem is required.')
        interface = self.sdk.find_class('/Script/EnhancedInput.EnhancedInputSubsystemInterface')
        fn = self.sdk.find_object('Function', '/Script/EnhancedInput.EnhancedInputSubsystemInterface:HasMappingContext')
        if interface is None or fn is None or not subs[0].Class._implements(interface):
            raise RuntimeError('Input context inspection is unavailable.')
        contexts = list(itertools.islice((x for x in self.sdk.find_all('InputMappingContext', False)
                                         if not str(x.Name).startswith('Default__')), 129))
        if len(contexts) > 128:
            raise RuntimeError('Input context scan exceeded its limit.')
        bound = self.sdk.unreal.BoundFunction(fn, subs[0])
        for context in contexts:
            result = bound(context, 0)
            if not isinstance(result, tuple) or len(result) != 2 or type(result[0]) is not bool or type(result[1]) is not int:
                raise RuntimeError('Unexpected input context result.')
            if result[0] and '/UI/' in str(context._path_name()).upper():
                raise RuntimeError('Close other menus and open SHiFT with F10 before starting.')
        if self.get_pc() != pc or subs[0].Outer != pc.Player:
            raise RuntimeError('Player changed while checking input.')

    def _release_input(self, pc):
        lib = self._class_default('/Script/UMG.WidgetBlueprintLibrary')
        def call(obj, name, *args):
            try:
                fn = getattr(obj, name, None)
                if callable(fn):
                    fn(*args)
                    return True
            except Exception:
                pass
            return False
        call(lib, 'ClearAllUserFocus', pc)
        if not call(lib, 'SetInputMode_GameOnly', pc, True):
            call(lib, 'SetInputMode_GameOnly', pc)
        call(lib, 'SetFocusToGameViewport')
        for attr in ('bShowMouseCursor', 'bEnableMouseOverEvents', 'bEnableClickEvents', 'bEnableTouchEvents', 'bBlockInput'):
            try:
                setattr(pc, attr, False)
            except Exception:
                pass
        for name in ('ResetIgnoreLookInput', 'ResetIgnoreMoveInput', 'ResetIgnoreInputFlags'):
            call(pc, name)

    def _start(self):
        pc = self.get_pc()
        self._check_contexts(pc)
        pawn = pc.Pawn
        current = self.native.inspect()
        if (current.get('owned') or current.get('visible') is not True
                or current.get('visibility') != [25, 25, 25]
                or current.get('canvas_visibility') != 2):
            raise RuntimeError('Open SHiFT normally before starting background view.')
        if self.get_pc() != pc or pc.Pawn != pawn:
            raise RuntimeError('Player changed before background entry.')
        statics = self._class_default('GameplayStatics')
        statics.SetGamePaused(pc, False)
        if statics.IsGamePaused(pc) is not False:
            raise RuntimeError('The game could not be unpaused.')
        self._release_input(pc)
        if self.get_pc() != pc or pc.Pawn != pawn:
            raise RuntimeError('Player changed before background entry.')
        try:
            self.native.enter()
        finally:
            self._ownership = self._owned()
        self._release_input(pc)
        self._pc, self._pawn = pc, pawn

    def _finish(self, foreground=False, close=True):
        if self._ownership:
            try:
                self.native.restore()
            finally:
                self._ownership = self._owned()
            if self._ownership:
                raise RuntimeError('Background view restoration remains incomplete.')
            self._closing = close
        if self._closing:
            lib = self._class_default('/Script/ShiftUI.ShiftUIFunctionLibrary')
            lib.Close()
            self._closing = False
        self._pc = self._pawn = None
        self._token = None
        self._deadline = 0.0
        self._command = None
        self._attempts = 0
        self._state = 'error' if self._failure_reason else ('foreground' if foreground else 'idle')
        self._reason, self._failure_reason = self._failure_reason, ''

    def _stop_attempt(self, foreground=False, close=True):
        if self._attempts == 0:
            self._stop_foreground, self._stop_close = foreground, close
        try:
            self._finish(self._stop_foreground, self._stop_close)
            return True
        except Exception as exc:
            self._attempts += 1
            self._reason = str(exc)[:300]
            if self.report_error:
                try:
                    self.report_error(self._reason)
                except Exception:
                    pass
            if self._attempts >= _MAX_RESTORE_ATTEMPTS:
                self._state, self._command = 'error', None
            else:
                self._state, self._command = 'stopping', 'stop'
            return False

    def tick(self):
        with self._lock:
            if self._tick_running:
                return
            self._tick_running = True
            try:
                self._tick_once()
            finally:
                self._tick_running = False

    def _tick_once(self):
        with self._lock:
            if self.native is None:
                return
            self._bind(allow_bind=True)
            now = self.clock()
            if self._state in ('pending', 'active') and now >= self._deadline:
                self._failure_reason = 'Background lease expired before the next heartbeat.'
                self._state, self._command = 'stopping', 'stop'
            if self._command == 'start' and self._state == 'pending':
                self._command = None
                try:
                    self._start()
                    self._state, self._reason = 'active', ''
                except Exception as exc:
                    self._reason = str(exc)[:300]
                    self._failure_reason = self._reason
                    if self._ownership:
                        self._state, self._command = 'stopping', 'stop'
                    else:
                        self._state, self._token = 'error', None
                return
            if self._command == 'stop' or self._state == 'stopping':
                self._stop_attempt()
                return
            if self._state != 'active':
                return
            try:
                try:
                    current = self.native.inspect()
                finally:
                    self._ownership = self._owned()
                if not self._ownership:
                    raise RuntimeError('Background view ownership was lost.')
                visibility = current['visibility']
                if visibility == [25, 25, 25]:
                    self._stop_attempt(foreground=True, close=False)
                elif visibility == [2, 2, 2]:
                    self._stop_attempt(close=False)
                elif visibility != [1, 1, 1]:
                    self._failure_reason = 'SHiFT background visibility changed unexpectedly.'
                    self._state, self._command = 'stopping', 'stop'
                    self._stop_attempt()
                elif self.get_pc() != self._pc or getattr(self.get_pc(), 'Pawn', None) != self._pawn:
                    self._state, self._command = 'stopping', 'stop'
                    self._stop_attempt()
            except Exception as exc:
                self._reason = str(exc)[:300]
                self._failure_reason = self._reason
                self._state, self._command = 'stopping', 'stop'
                self._stop_attempt()

    def before_open(self):
        with self._lock:
            if self._tick_running:
                return False
            if self.native is None:
                return True
            if self._thread is None and not self._ownership:
                if self._state == 'pending':
                    self._finish(foreground=True, close=False)
                return True
            self._bind()
            if self._closing:
                # A prior native Close failed during this handoff. Retry it
                # here so the current Open body stays blocked until reset.
                return self._stop_attempt(foreground=True, close=True)
            if self._ownership:
                # Restore our child widgets, then use the normal native Close
                # before this original Open continues. A collapsed canvas is
                # separate from those widgets and is reset by the game API.
                return self._stop_attempt(foreground=True, close=True)
            if self._state == 'pending':
                self._finish(foreground=True, close=False)
            return True

    def before_close(self):
        with self._lock:
            if self._tick_running:
                # Permit the close initiated by our completed restore only.
                return self._closing and not self._ownership
            if self.native is None:
                return True
            if self._thread is None and not self._ownership:
                if self._state == 'pending':
                    self._finish(close=False)
                return True
            self._bind()
            if self._ownership:
                return self._stop_attempt(close=False)
            if self._state == 'pending':
                self._finish(close=False)
            return True

    def shutdown(self):
        with self._lock:
            self._shutdown = True
            if self._ownership or self._closing or self._state in ('pending', 'active', 'stopping'):
                self._state, self._command = 'stopping', 'stop'
