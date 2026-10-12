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

    def poll(self, scope, world_path, providers, now):
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
                provider.NetMulticast_StopDialog(thread, .1)
                issued += 1
                self.skipped += 1
            self.lines = {k: v for k, v in self.lines.items() if k in present}
        except Exception as exc:
            # Dialogue acceleration is optional; normal mission checks continue.
            self.disabled = True
            self.error = str(exc)
        return self.status()

    def status(self):
        return dict(skipped=self.skipped, disabled=self.disabled, error=self.error)
