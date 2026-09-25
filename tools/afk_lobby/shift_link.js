/* MSBT AFK link. Appended to the existing SHiFT dashboard controller. */
;(function () {
    if (window.MsbtAfkShiftLink) return;
    window.MsbtAfkShiftLink = true;
    var controlled = false;
    try { controlled = window.localStorage.getItem("msbt_afk_managed") === "1"; } catch (_) {}
    var endpoint = "http://127.0.0.1:49774/afk_shift";
    function poll() {
        var request = new XMLHttpRequest();
        request.open("GET", endpoint, true);
        request.timeout = 3000;
        request.onload = function () {
            try {
                if (request.status !== 200 || !window.ShiftFriendAutomation) return;
                var data = JSON.parse(request.responseText);
                if (data.ok !== true) return;
                if (data.auto_accept === true) {
                    controlled = true;
                    try { window.localStorage.setItem("msbt_afk_managed", "1"); } catch (_) {}
                    if (!ShiftFriendAutomation.isRunning()) ShiftFriendAutomation.startAutoAccept();
                } else if (controlled) {
                    ShiftFriendAutomation.stopAutoAccept({ silent: true });
                    controlled = false;
                    try { window.localStorage.removeItem("msbt_afk_managed"); } catch (_) {}
                }
                var report = new XMLHttpRequest();
                report.open("POST", endpoint, true);
                report.setRequestHeader("Content-Type", "text/plain");
                report.timeout = 3000;
                report.send(JSON.stringify({ running: ShiftFriendAutomation.isRunning() }));
            } catch (error) { /* Keep the existing SHiFT controls usable. */ }
        };
        request.onloadend = function () { window.setTimeout(poll, 2000); };
        request.send();
    }
    window.setTimeout(poll, 1000);
})();
