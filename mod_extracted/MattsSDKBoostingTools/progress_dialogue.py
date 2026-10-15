"""Bounded, game-thread dialogue skipping during a validated mission batch.

Native-call lead: Yeti's Dialog Skipper (user-supplied v1 package, GPL3).
The reflected BL4 GbxDialogProvider API confirms the call and arguments.
No worker timers, persistent hooks, audio setting changes or time dilation.
"""


class DialogueSkipper:
    def __init__(self):
        self.scope = None
        self.lines = {}
        self.disabled = False
        self.skipped = 0
        self.error = ''
        self.pending_threads = {}
        self.completed_threads = 0
        self.completion_requests = 0

    def poll(self, scope, world_path, providers, now, *, stop_playback=None, thread_playing=None, finish_performance=None):
        if scope != self.scope:
            self.__init__()
            self.scope = scope
        if self.disabled:
            return self.status()
        present = set()
        issued = 0
        try:
            for provider in providers:
                path = provider._path_name()
                if not path.startswith(world_path + ':') or 'Default__' in path:
                    continue
                current = provider.CurrentPerformance
                thread = int(current.DialogThreadID)
                if thread <= 0:
                    continue
                key = (path, thread, str(current.Performance), str(current.DialogLineRef.LineName))
                present.add(key)
                first, sent = self.lines.setdefault(key, (now, False))
                if sent or now - first < .3 or issued >= 4:
                    continue
                # Mark before calling: an exception must never cause a retry.
                self.lines[key] = (first, True)
                current = provider.CurrentPerformance
                if (int(current.DialogThreadID), str(current.Performance), str(current.DialogLineRef.LineName)) != key[1:]:
                    continue
                if finish_performance is not None:
                    if not finish_performance(provider,thread):
                        continue
                    self.pending_threads.setdefault(thread, now)
                    self.completion_requests += 1
                elif stop_playback is None:
                    provider.NetMulticast_StopDialog(thread, .1)
                else:
                    # Stop the native playback instance so its normal end callback
                    # can release dialogue waits; the provider multicast is audio-only.
                    self.pending_threads.setdefault(thread, now)
                    stop_playback(current.PlayingAudioInstance)
                issued += 1
                self.skipped += 1
            self.lines = {k: v for k, v in self.lines.items() if k in present}
            if thread_playing is not None:
                for thread, requested in list(self.pending_threads.items())[:8]:
                    if not thread_playing(thread):
                        self.completed_threads += 1
                        del self.pending_threads[thread]
                    elif now-requested > 2.:
                        del self.pending_threads[thread]
        except Exception as exc:
            # Dialogue acceleration is optional; normal mission checks continue.
            self.disabled = True
            self.error = str(exc)
        return self.status()

    def status(self):
        # Keep the legacy key for clients; this counts requests, not proof that
        # the conversation or its authored script waits actually ended.
        return dict(skipped=self.skipped, audio_stop_requests=self.skipped,
                    native_thread_ends=self.completed_threads, completion_requests=self.completion_requests,
                    skip_verified=self.completed_threads>0, disabled=self.disabled, error=self.error)
