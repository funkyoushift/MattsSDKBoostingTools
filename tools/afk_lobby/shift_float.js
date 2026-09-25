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
            'html.msbt-shift-floating #shift_mini_panel{display:none!important;}' +
            '#msbt-shift-float-bar{position:fixed;right:12px;top:12px;z-index:20050;background:#101c22;color:white;border:1px solid #3ecf6b;padding:10px;font:16px sans-serif;}' +
            '#msbt-shift-float-bar button{background:#29434e;color:white;border:1px solid #70929e;margin-left:8px;padding:7px;cursor:pointer;}' +
            '#msbt-shift-float-drag{cursor:move;display:inline-block;padding:7px;}' +
            '#msbt-shift-float-status{display:inline-block;margin-left:8px;}';
        document.head.appendChild(style);
        var bar = document.createElement('div'); bar.id = 'msbt-shift-float-bar';
        bar.innerHTML = '<span id="msbt-shift-float-drag">SHiFT • drag here</span><span id="msbt-shift-float-status"></span><button id="msbt-shift-float-accept">Start accepter</button><button id="msbt-shift-float-toggle">Full menu</button>';
        document.body.appendChild(bar);
        var floating = true, x = 12, y = 70, drag = null;
        function place() {
            x = Math.max(0, Math.min(x, window.innerWidth * .58));
            y = Math.max(50, Math.min(y, window.innerHeight * .58));
            // Inline important properties avoid depending on CSS variable support in Cohtml.
            root.style.setProperty('left', x + 'px', 'important');
            root.style.setProperty('top', y + 'px', 'important');
            style.textContent = style.textContent.replace(/left:var\(--msbt-float-x\)/, 'left:' + x + 'px').replace(/top:var\(--msbt-float-y\)/, 'top:' + y + 'px');
            bar.style.left = floating ? x + 'px' : '';
            bar.style.top = floating ? Math.max(0, y - 58) + 'px' : '12px';
            bar.style.right = floating ? 'auto' : '12px';
        }
        function apply() {
            document.documentElement.classList.toggle('msbt-shift-floating', floating);
            document.getElementById('msbt-shift-float-toggle').textContent = floating ? 'Full menu' : 'Floating menu';
            if (floating) place();
            else { root.style.removeProperty('left'); root.style.removeProperty('top'); bar.style.left='';bar.style.top='12px';bar.style.right='12px'; }
        }
        document.getElementById('msbt-shift-float-toggle').onclick = function () { floating = !floating; apply(); };
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
