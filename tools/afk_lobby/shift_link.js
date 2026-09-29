/* MSBT AFK link. Appended to the existing SHiFT dashboard controller. */
;(function () {
    if (window.MsbtAfkShiftLink) return;
    window.MsbtAfkShiftLink = true;
    var controlled = false;
    try { controlled = window.localStorage.getItem("msbt_afk_managed") === "1"; } catch (_) {}
    var ports = [49774, 27874, 27875, 27876], portIndex = 0;
    function poll() {
        var endpoint = "http://127.0.0.1:" + ports[portIndex] + "/afk_shift";
        var verified = false;
        var request = new XMLHttpRequest();
        request.open("GET", endpoint, true);
        request.timeout = 3000;
        request.onload = function () {
            try {
                if (request.status !== 200 || !window.ShiftFriendAutomation) return;
                var data = JSON.parse(request.responseText);
                if (data.ok !== true || data.service !== "msbt-sdk-bridge" || !/^[a-f0-9]{32}$/.test(data.instance) || typeof data.auto_accept !== "boolean") return;
                verified = true;
                // v4.4 keeps manual preferences separate from MSBT's AFK policy.
                if (ShiftFriendAutomation.setAfkManaged) ShiftFriendAutomation.setAfkManaged(data.auto_accept === true);
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
                report.setRequestHeader("X-MSBT-Instance", data.instance);
                report.timeout = 3000;
                report.send(JSON.stringify({ running: ShiftFriendAutomation.isRunning() }));
            } catch (error) { /* Keep the existing SHiFT controls usable. */ }
        };
        request.onloadend = function () { if (!verified) portIndex = (portIndex + 1) % ports.length; window.setTimeout(poll, 2000); };
        request.send();
    }
    window.setTimeout(poll, 1000);
})();
