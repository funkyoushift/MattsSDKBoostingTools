/* Background lease client. The native bridge owns the input and view lifecycle. */
;(function () {
    if (window.MsbtShiftBackground) return;
    var state = 'idle', reason = '', token = null, pinned = null;
    var generation = 0, timer = null, request = null, previousStyle = null, backgroundStyle = null, button = null, message = null;
    var seen = [], queued = null;
    var startedHere = false;
    function paint() {
        if (button) button.textContent = state === 'pending' ? 'Starting background...' : 'Play while accepting';
        if (message) message.textContent = reason;
    }
    function styleName(key) { return key === 'transform-origin' ? 'transformOrigin' : key; }
    function readStyle(style, key) {
        var name = styleName(key);
        return {value: typeof style.getPropertyValue === 'function' ? style.getPropertyValue(key) : (style[name] || ''),
                priority: typeof style.getPropertyPriority === 'function' ? style.getPropertyPriority(key) : ''};
    }
    function writeStyle(style, key, value, priority) {
        if (typeof style.setProperty === 'function') style.setProperty(key, value, priority || '');
        else style[styleName(key)] = value;
    }
    function restore() {
        if (backgroundStyle) {
            if (backgroundStyle.parentNode) backgroundStyle.parentNode.removeChild(backgroundStyle);
            backgroundStyle = null;
        }
        if (!previousStyle) return;
        var saved = previousStyle;
        saved.forEach(function (entry) {
            ['transform', 'transform-origin', 'opacity'].forEach(function (key) {
                var old = entry.values[key];
                if (!old.value && typeof entry.element.style.removeProperty === 'function') entry.element.style.removeProperty(key);
                else writeStyle(entry.element.style, key, old.value, old.priority);
            });
        });
        previousStyle = null;
    }
    function hide() {
        if (previousStyle) return;
        var targets = ['body_container', 'msbt-shift-float-bar', 'shift_mini_panel', 'shift_settings_overlay'];
        var saved = [];
        targets.forEach(function (id) {
            var element = document.getElementById(id);
            if (!element || !element.style) return;
            var values = {};
            ['transform', 'transform-origin', 'opacity'].forEach(function (key) { values[key] = readStyle(element.style, key); });
            saved.push({element:element, values:values});
        });
        if (!saved.length || !document.getElementById('body_container')) throw new Error('SHiFT page is not ready');
        previousStyle = saved;
        if (!document.head || !document.createElement) throw new Error('SHiFT stylesheet is unavailable');
        backgroundStyle = document.createElement('style');
        backgroundStyle.textContent = 'html,body{background:transparent!important;}' +
            'html #body_container#body_container,html #msbt-shift-float-bar#msbt-shift-float-bar,html #shift_mini_panel#shift_mini_panel,html #shift_settings_overlay#shift_settings_overlay{transform:scale(0.04)!important;transform-origin:top left!important;opacity:1!important;}';
        document.head.appendChild(backgroundStyle);
        saved.forEach(function (entry) {
            writeStyle(entry.element.style, 'transform', 'scale(0.04)', 'important');
            writeStyle(entry.element.style, 'transform-origin', 'top left', 'important');
            writeStyle(entry.element.style, 'opacity', '1', 'important');
        });
    }
    function presentationError(e) {
        return 'Page presentation failed: ' + ((e && e.name) || 'Error') + ': ' + ((e && e.message) || String(e));
    }
    function ready() {
        try { return !!(window.ShiftFriendAutomation && window.ShiftFriendAutomation.isRunning() && bridge()); }
        catch (_) { return false; }
    }
    function bridge() {
        try {
            var b = window.ShiftMiniPanel && window.ShiftMiniPanel.backgroundBridge();
            if (!b || (typeof b.port !== 'number' || !isFinite(b.port) || Math.floor(b.port) !== b.port) || b.port < 1 || b.port > 65535 || typeof b.instance !== 'string' || !b.instance) return null;
            return {port:b.port, instance:b.instance, start_token:b.start_token};
        } catch (_) { return null; }
    }
    function matches(b) { return b && pinned && b.port === pinned.port && b.instance === pinned.instance; }
    function clear() {
        if (timer !== null) { window.clearTimeout(timer); timer = null; }
        if (request) { var old = request; request = null; old.abort(); }
    }
    function end(next, why) {
        if (startedHere && next !== 'foreground') {
            try { window.ShiftFriendAutomation.stopAutoAccept(); } catch (_) {}
        }
        startedHere = false;
        ++generation; clear(); try { restore(); } catch (e) { why = why || presentationError(e); } state = next; reason = why || ''; token = null; pinned = null; paint();
    }
    function send(mode, done) {
        var current = generation, xhr = new XMLHttpRequest(), b = pinned, t = token;
        request = xhr;
        function finish(err, result) {
            if (request === xhr) request = null;
            if (current !== generation) return;
            done(err, result);
            drain();
        }
        try {
            xhr.open('POST', 'http://127.0.0.1:' + b.port + '/shift-background', true);
            xhr.timeout = 1500;
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('X-MSBT-Shift-Instance', b.instance);
            xhr.onload = function () {
                var result;
                try { result = JSON.parse(xhr.responseText); } catch (_) { finish('Invalid response'); return; }
                var foreground = mode === 'heartbeat' && xhr.status === 409 && result && result.ok === false && result.background && result.background.state === 'foreground';
                if ((!foreground && xhr.status !== 200) || !result || result.service !== 'msbt-shift-storage' || result.protocol !== 1 || result.instance !== b.instance || !result.background) { finish('Background bridge identity or response changed'); return; }
                if (result.background.token !== t && result.background.state !== 'foreground') { finish('Background bridge token changed'); return; }
                queueCommand(result.background.command);
                finish(null, result.background);
            };
            xhr.onerror = xhr.ontimeout = function () { finish('Background bridge unavailable'); };
            xhr.send(JSON.stringify({mode:mode, token:t}));
        } catch (_) { finish('Background bridge unavailable'); }
    }
    function pulse() {
        timer = null;
        if (!matches(bridge())) { end('error', 'Background bridge disconnected; background play ended'); return; }
        if (!ready() || !matches(bridge())) { stop(); return; }
        if (request) return;
        send('heartbeat', receive);
    }
    function receive(err, bg) {
        if (err || !ready() || !matches(bridge())) { end('error', err || 'Background prerequisites changed'); return; }
        if (!bg.available || ['idle','stopping','foreground','error','unsupported'].indexOf(bg.state) >= 0) { end(bg.state || 'error', bg.reason || (bg.state === 'foreground' ? '' : 'Background mode ended')); return; }
        if (bg.state !== 'pending' && bg.state !== 'active') { end('error', 'Unexpected background state'); return; }
        state = bg.state; reason = bg.reason || '';
        try { if (state === 'active') hide(); }
        catch (e) {
            var why = presentationError(e);
            stop(); state = 'error'; reason = why; paint(); return;
        }
        paint(); timer = window.setTimeout(pulse, 1000);
    }
    function start() {
        if (state === 'pending' || state === 'active' || request) return false;
        var b = bridge();
        if (!b) { end('error', 'The SDK background bridge is not connected'); return false; }
        if (!window.ShiftFriendAutomation) { end('error', 'Friend automation is unavailable'); return false; }
        if (typeof b.start_token !== 'string' || !/^[0-9a-f]{32}$/.test(b.start_token)) { end('error', 'The SDK did not supply a background token'); return false; }
        startedHere = !window.ShiftFriendAutomation.isRunning();
        try { if (startedHere) window.ShiftFriendAutomation.startAutoAccept(); } catch (_) { end('error', 'Unable to start accepting'); return false; }
        if (!ready()) { end('error', 'Unable to start accepting'); return false; }
        token = b.start_token;
        pinned = b; state = 'pending'; reason = ''; ++generation; paint();
        try { hide(); } catch (e) { try { restore(); } catch (_) {} end('error', presentationError(e)); return false; }
        var startGeneration = generation;
        timer = window.setTimeout(function () {
            timer = null;
            if (startGeneration !== generation) return;
            if (!ready() || !matches(bridge())) { end('error', 'Background prerequisites changed'); return; }
            send('start', receive);
        }, 150);
        return true;
    }
    function stop() {
        var b = pinned, t = token;
        ++generation; clear(); try { restore(); } catch (_) {} state = 'foreground'; reason = ''; paint();
        if (!b || !t || !matches(bridge())) { token = null; pinned = null; return; }
        send('stop', function () { token = null; pinned = null; });
    }
    function queueCommand(command) {
        if (!command || typeof command.id !== 'string' || !/^[0-9a-f]{32}$/i.test(command.id) || (command.mode !== 'start' && command.mode !== 'stop') || seen.indexOf(command.id) >= 0 || (queued && queued.id === command.id)) return;
        queued = {id:command.id, mode:command.mode};
    }
    function acknowledgeStop(command) {
        var b = bridge();
        if (!b) return;
        try {
            var ack = new XMLHttpRequest();
            ack.open('POST', 'http://127.0.0.1:' + b.port + '/shift-background', true);
            ack.timeout = 1500;
            ack.setRequestHeader('Content-Type', 'application/json');
            ack.setRequestHeader('X-MSBT-Shift-Instance', b.instance);
            ack.send(JSON.stringify({mode:'ack_stop',command_id:command.id}));
        } catch (_) {} // No acknowledgement means the desktop reports the timeout.
    }
    function drain() {
        if (request || !queued) return;
        var command = queued; queued = null; seen.push(command.id);
        if (seen.length > 64) seen.shift();
        if (command.mode === 'stop') {
            try { if (window.ShiftFriendAutomation) window.ShiftFriendAutomation.stopAutoAccept(); } catch (_) {}
            stop();
            if (window.ShiftFriendAutomation && !window.ShiftFriendAutomation.isRunning()) acknowledgeStop(command);
        } else {
            try {
                if (!bridge() || !window.ShiftFriendAutomation) return;
                start();
            } catch (_) { end('error', 'Unable to start accepting'); }
        }
    }
    function onCompanionState(background) {
        if (!background || !bridge()) return;
        if (background.state === 'foreground' && (state === 'active' || state === 'pending')) end('foreground', background.reason || '');
        queueCommand(background.command); drain();
    }
    function stopAccepting() {
        try { if (window.ShiftFriendAutomation) window.ShiftFriendAutomation.stopAutoAccept(); } finally { stop(); }
    }
    function init() {
        var bar = document.getElementById('msbt-shift-float-bar');
        if (!bar) { window.setTimeout(init, 1000); return; }
        button = document.createElement('button'); button.id = 'msbt-shift-background-start'; button.onclick = start;
        bar.appendChild(button);
        var stopButton = document.createElement('button'); stopButton.id = 'msbt-shift-background-stop-accepting'; stopButton.textContent = 'Stop accepting'; stopButton.onclick = stopAccepting; bar.appendChild(stopButton); message = document.createElement('span'); message.id = 'msbt-shift-background-status'; bar.appendChild(message); paint();
    }
    window.MsbtShiftBackground = {start:start, stop:stop, onCompanionState:onCompanionState, status:function () { return {state:state, reason:reason}; }};
    window.setTimeout(init, 1000);
})();
