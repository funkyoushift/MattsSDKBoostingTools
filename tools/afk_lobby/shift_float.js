/* Keep the SHiFT page alive while reducing its visible footprint. */
;(function () {
    if (window.MsbtShiftFloat) return;
    window.MsbtShiftFloat = true;
    function init() {
        var root = document.getElementById('body_container');
        if (!root || !document.body) { window.setTimeout(init, 500); return; }
        var style = document.createElement('style');
        style.textContent = 'html.msbt-shift-floating,html.msbt-shift-floating body{background:transparent!important;}' +
            'html.msbt-shift-floating #body_container{position:fixed!important;transform:scale(.42)!important;transform-origin:0 0!important;width:100vw!important;height:100vh!important;left:var(--msbt-float-x)!important;top:var(--msbt-float-y)!important;}' +
            '#msbt-shift-float-bar{position:fixed;right:12px;top:12px;z-index:20050;background:#101c22;color:white;border:1px solid #3ecf6b;padding:10px;font:16px sans-serif;}' +
            '#msbt-shift-float-bar button{background:#29434e;color:white;border:1px solid #70929e;margin-left:8px;padding:7px;cursor:pointer;}' +
            '#msbt-shift-float-drag{cursor:move;display:inline-block;padding:7px;}' +
            '#msbt-shift-float-status{display:inline-block;margin-left:8px;}';
        document.head.appendChild(style);
        var bar = document.createElement('div'); bar.id = 'msbt-shift-float-bar';
        bar.innerHTML = '<span id="msbt-shift-float-drag">SHiFT • drag here</span><span id="msbt-shift-float-status"></span><button id="msbt-shift-float-accept">Start accepter</button><span> Size </span><button id="msbt-shift-size-compact">Compact</button><button id="msbt-shift-size-medium">Medium</button><button id="msbt-shift-size-regular">Regular</button><button id="msbt-shift-float-toggle">Regular size</button>';
        document.body.appendChild(bar);
        // Mini Panel owns its own visibility and remains usable in either layout.
        if (window.ShiftMiniPanel) {
            var manage = document.createElement('button');
            manage.textContent = 'Manage SHiFT';
            manage.onclick = function () { window.ShiftMiniPanel.show(); };
            bar.appendChild(manage);
        }
        // Gameface builds may expose CSS properties without CSSStyleDeclaration methods.
        function setStyle(element, key, value) {
            var style = element.style;
            if (typeof style.setProperty === 'function') style.setProperty(key, value, 'important');
            else style[key] = value;
        }
        function clearStyle(element, key) {
            var style = element.style;
            if (typeof style.removeProperty === 'function') style.removeProperty(key);
            else style[key] = '';
        }
        var scale = .42;
        try { var saved = Number(localStorage.getItem('msbt.shift.size')); if ([.42,.7,1].indexOf(saved) >= 0) scale = saved; } catch (_) {}
        var floating = scale < 1, x = 12, y = 70, drag = null;
        var sizes = [{id:'compact', value:.42}, {id:'medium', value:.7}, {id:'regular', value:1}];
        function place() {
            x = Math.max(0, Math.min(x, window.innerWidth * (1-scale)));
            y = Math.max(50, Math.min(y, window.innerHeight * (1-scale)));
            // Inline important properties avoid depending on CSS variable support in Cohtml.
            setStyle(root, 'left', x + 'px');
            setStyle(root, 'top', y + 'px');
            style.textContent = style.textContent.replace(/left:var\(--msbt-float-x\)/, 'left:' + x + 'px').replace(/top:var\(--msbt-float-y\)/, 'top:' + y + 'px');
            bar.style.left = floating ? x + 'px' : '';
            bar.style.top = floating ? Math.max(0, y - 58) + 'px' : '12px';
            bar.style.right = floating ? 'auto' : '12px';
        }
        function apply() {
            floating = scale < 1;
            // Keep the stylesheet's important rule in sync even where inline priorities are unavailable.
            style.textContent = style.textContent.replace(/transform:scale\([^)]*\)!important/, 'transform:scale(' + scale + ')!important');
            sizes.forEach(function (size) {
                document.getElementById('msbt-shift-size-' + size.id).setAttribute('aria-pressed', String(scale === size.value));
            });
            try { localStorage.setItem('msbt.shift.size', String(scale)); } catch (_) {}
            document.documentElement.classList.toggle('msbt-shift-floating', floating);
            if (floating) setStyle(root, 'transform', 'scale('+scale+')');
            else clearStyle(root, 'transform');
            document.getElementById('msbt-shift-float-toggle').textContent = floating ? 'Regular size' : 'Compact size';
            if (floating) place();
            else { clearStyle(root, 'left'); clearStyle(root, 'top'); bar.style.left='';bar.style.top='12px';bar.style.right='12px'; }
        }
        document.getElementById('msbt-shift-float-toggle').onclick = function () { scale = floating ? 1 : .42; apply(); };
        sizes.forEach(function (size) {
            document.getElementById('msbt-shift-size-' + size.id).onclick = function () { scale = size.value; apply(); };
        });
        document.getElementById('msbt-shift-float-accept').onclick = function () {
            var a = window.ShiftFriendAutomation;
            if (!a) return;
            if (a.isRunning()) a.stopAutoAccept(); else a.startAutoAccept();
            refresh();
        };
        document.getElementById('msbt-shift-float-drag').onmousedown = function (e) {
            if (!floating) return;
            drag = {x:e.clientX-x,y:e.clientY-y}; e.preventDefault();
        };
        document.addEventListener('mousemove', function (e) { if (drag) {x=e.clientX-drag.x;y=e.clientY-drag.y;place();} });
        document.addEventListener('mouseup', function () {drag=null;});
        window.addEventListener('resize', function () {if(floating)place();});
        function refresh() {
            var a=window.ShiftFriendAutomation, running=!!(a&&a.isRunning());
            document.getElementById('msbt-shift-float-status').textContent=running?'Accepter running':'Accepter stopped';
            document.getElementById('msbt-shift-float-accept').textContent=running?'Stop accepter':'Start accepter';
        }
        apply(); refresh(); window.setInterval(refresh,2000);
    }
    window.setTimeout(init,700);
})();
