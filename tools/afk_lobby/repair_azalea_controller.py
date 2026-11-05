"""Small, checked repairs to the supplied v4.4 dashboard source; no game writes."""


def repair_controller(text):
    start = text.index('var ShiftFriendAutomation = (function ()')
    end = text.index('window.ShiftFriendAutomation = ShiftFriendAutomation;', start)
    module = text[start:end]

    # The upstream personal first-run list is not a product default. Existing
    # local or companion-saved names are still loaded by the original code.
    seed_start = module.index('    var DEFAULT_PROTECTED_NAMES = [')
    seed_end = module.index('    ];', seed_start) + len('    ];')
    assert module.count('    var DEFAULT_PROTECTED_NAMES = [') == 1
    module = module[:seed_start] + '    var DEFAULT_PROTECTED_NAMES = [];' + module[seed_end:]
    module = module.replace('    // Persistent editable protection list.  The V3 hard-coded names are used\n'
                            '    // only as the first-run seed; after that the user\'s saved list wins, so\n'
                            '    // even a seeded name can be deliberately removed from the whitelist.',
                            '    // Persistent editable protection list; new users start empty.')

    def replace(before, after, count=1):
        nonlocal module
        assert module.count(before) == count, f'Unexpected v4.4 source: {before!r}'
        module = module.replace(before, after)

    replace('    var autoAccepting = false;', '''    var autoAccepting = false;
    var automationGeneration = 0;
    var autoResumeTimer;

    function automatedOptions()
    {
        var generation = automationGeneration;
        var options = getButtonOptions();
        options.shouldContinue = function () { return autoAccepting && generation === automationGeneration; };
        return options;
    }''')
    replace('writeProtectedNames(); writeAutoAcceptFlag(autoAccepting);',
            'writeProtectedNames(removeAllExclusions.names); writeAutoAcceptFlag(autoAccepting);')
    replace('''    function onAutoAcceptRequestList(response)
    {
        if (!autoAccepting) return;''', '''    function onAutoAcceptRequestList(response)
    {
        if (!autoAccepting || !Array.isArray(response)) return;''')
    # An explicit empty native response is authoritative, not a request to reuse a cache.
    replace('if (!requests || requests.length === 0)', 'if (list === undefined && (!requests || requests.length === 0))', 2)
    for bound in ('targets', 'invites'):
        replace(f'            if (index >= {bound}.length) return;',
                f'            if (options.shouldContinue && !options.shouldContinue()) return;\n'
                f'            if (index >= {bound}.length) return;', 1 if bound == 'targets' else 2)
    for call in ('callEach(PLAYER_PROFILE_MENU_ACCEPT_REQUEST, requests',
                 'callEach(PLAYER_PROFILE_MENU_DECLINE_REQUEST, requests',
                 'declineGameInvites(gameInvites', 'acceptGameInvites(gameInvites'):
        replace(call + ', getButtonOptions());', call + ', automatedOptions());')
    # Poll only at the configured interval. Response-triggered reloads could form a
    # second polling loop even with both modes set to Ignore.
    replace('        reloadFriendsData({ reloadDelayMs: 1500 });',
            '        // The configured polling timer owns the next request-list refresh.')
    replace('if (readAutoAcceptFlag())', '''if (readAutoAcceptFlag() && (function () {
        try { return window.localStorage.getItem("msbt_afk_managed") !== "1"; }
        catch (_) { return true; }
    })())''')
    replace('''        window.setTimeout(function ()
        {
            autoAccepting = true;''', '''        autoResumeTimer = window.setTimeout(function ()
        {
            autoResumeTimer = undefined;
            autoAccepting = true;''')
    replace('setAfkManaged: function (value) { msbtAfkManaged = value === true; },',
            '''setAfkManaged: function (value) {
            if (msbtAfkManaged !== (value === true)) automationGeneration++;
            msbtAfkManaged = value === true;
        },''')
    replace('''            automationSettings = normalizeAutomationSettings(value);''',
            '''            automationGeneration++;
            automationSettings = normalizeAutomationSettings(value);''')
    replace('''            automationSettings = normalizeAutomationSettings(DEFAULT_AUTOMATION_SETTINGS);''',
            '''            automationGeneration++;
            automationSettings = normalizeAutomationSettings(DEFAULT_AUTOMATION_SETTINGS);''')
    replace('''            autoAccepting = false;
            writeAutoAcceptFlag(false);''', '''            autoAccepting = false;
            automationGeneration++;
            if (autoResumeTimer !== undefined) window.clearTimeout(autoResumeTimer);
            autoResumeTimer = undefined;
            writeAutoAcceptFlag(false);''')
    replace('Started accepting friend requests and declining game invites.',
            'Started using the selected friend-request and game-invite settings.')
    for before in ("        removeAllExclusions.names.push(cleaned);", "        if (removeAllExclusions.names.length === before) return false;", "        removeAllExclusions.names = normalizeProtectedNames(Array.isArray(names) ? names : []);"):
        replace(before, before + "\n        if (!window.MsbtApplyingProtection) { window.MsbtProtectionDirty = true; window.MsbtProtectionReviewed = false; if (window.MsbtResetProtectionReview) window.MsbtResetProtectionReview(); }")
    replace("    var removeAllExclusions = {", "    window.MsbtProtectionDirty = false; window.MsbtProtectionReviewed = false;\n    var removeAllExclusions = {")
    guard = """            if (!window.ShiftMiniPanel || !window.ShiftMiniPanel.protectionReady()) {
                showStatusMessage("Protected list unavailable", "Bulk removal is disabled until protected SDK settings are verified.");
                return { action: PLAYER_PROFILE_MENU_REMOVE, count: 0, ids: [] };
            }
"""
    for fn in ("confirmRemoveAllFriends", "confirmRemoveAllOfflineFriends"):
        replace("        " + fn + ": function ()\n        {\n", "        " + fn + ": function ()\n        {\n" + guard)
    replace("""            while (index < targets.length && sent < batchSize)
            {
                engine.call(callName, targets[index].id);
                index++;
                sent++;
            }""", """            while (index < targets.length && sent < batchSize)
            {
                if (callName === PLAYER_PROFILE_MENU_REMOVE) {
                    if (!window.ShiftMiniPanel || !window.ShiftMiniPanel.protectionReady()) return;
                    if (isRemoveAllExcluded(targets[index])) { index++; continue; }
                }
                engine.call(callName, targets[index].id);
                index++;
                sent++;
            }""")
    # Recheck at confirmation time, since the bridge can disappear while the popup is open.
    replace('''            $(confirmationPopup_controller.ids.popup_confirm_btn).on("click", function ()
            {
                callEachBatched(PLAYER_PROFILE_MENU_REMOVE, friends,''', '''            $(confirmationPopup_controller.ids.popup_confirm_btn).on("click", function ()
            {
                if (!window.ShiftMiniPanel || !window.ShiftMiniPanel.protectionReady()) return;
                callEachBatched(PLAYER_PROFILE_MENU_REMOVE, friends,''', 2)
    text = text[:start] + module + text[end:]
    old = '            if (!data) return;\n            applyingSDK = true;'
    new = '            if (!data || data.storageValid !== true || !Array.isArray(data.protectedPlayers) || !data.protectedPlayers.every(function (name) { return typeof name === "string"; })) { sdkDetected = false; sdkRemoteReviewed = false; window.MsbtProtectionReviewed = false; if ((!data || data.storageState !== "missing") && window.MsbtResetProtectionReview) window.MsbtResetProtectionReview(); sdkStorageState = data && data.storageState || "unavailable"; sdkStateSeen = Date.now(); updateStorageStatus(); return; }\n            applyingSDK = true;'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '                window.ShiftFriendAutomation.setProtectedNames(data.protectedPlayers);'
    new = '                if (!window.MsbtProtectionDirty) { window.MsbtApplyingProtection = true; try { window.ShiftFriendAutomation.setProtectedNames(window.ShiftFriendAutomation.getProtectedNames().concat(data.protectedPlayers)); } finally { window.MsbtApplyingProtection = false; } }'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '            applyingSDK = true;'
    new = '            sdkRemoteReviewed = data.reviewed === true; if (!sdkRemoteReviewed) { if (window.MsbtProtectionReviewed && window.MsbtResetProtectionReview) window.MsbtResetProtectionReview(); window.MsbtProtectionReviewed = false; }\n            if (data.reviewed === true && saveAckReceived && pendingProtection !== null && protectionSignature(data.protectedPlayers) === pendingProtection && protectionSignature(window.ShiftFriendAutomation.getProtectedNames()) === pendingProtection) { window.MsbtProtectionDirty = false; window.MsbtProtectionReviewed = true; pendingProtection = null; saveAckReceived = false; }\n            applyingSDK = true;'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '    function handleSDKSettings(payload)'
    new = '    function protectionSignature(names) { return JSON.stringify(names.map(function (n) { return String(n).trim().toLowerCase(); }).sort()); }\n\n    function handleSDKSettings(payload)'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '            applyingSDK = false;\n            sdkDetected = true;'
    new = '            applyingSDK = false;\n            if (!window.MsbtProtectionDirty && data.reviewed === true && protectionSignature(window.ShiftFriendAutomation.getProtectedNames()) === protectionSignature(data.protectedPlayers)) window.MsbtProtectionReviewed = true;\n            if (window.MsbtProtectionReviewed && window.MsbtSetProtectionReview) window.MsbtSetProtectionReview(true);\n            sdkDetected = true;'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '            sdkLastSeen = Date.now ? Date.now() : 1;\n            renderProtectedNames();'
    new = '            sdkLastSeen = Date.now ? Date.now() : 1;\n            if (window.MsbtShiftBackground && window.MsbtShiftBackground.onCompanionState) { try { window.MsbtShiftBackground.onCompanionState(data.background); } catch (_) {} }\n            renderProtectedNames();'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '    function handleSDKSaved()\n    {\n        sdkDetected = true;'
    new = '    function handleSDKSaved()\n    {\n        if (pendingProtection === null) return;\n        saveAckReceived = true;\n        if (!sdkDetected) return;'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '    var sdkDetected = false;'
    assert text.count(old) == 1
    text = text.replace(old, old + '\n    var sdkSettingsApplied = false;\n    var sdkRemoteReviewed = false;\n    var sdkStorageState = "unavailable";\n    var sdkStateSeen = 0;\n    var pendingProtection = null;\n    var saveAckReceived = false;\n    var sdkSending = false;')
    old = '            if (data.settings && window.ShiftFriendAutomation) window.ShiftFriendAutomation.setSettings(data.settings);'
    new = '            if (!sdkSettingsApplied && data.settings && window.ShiftFriendAutomation) { window.ShiftFriendAutomation.setSettings(data.settings); sdkSettingsApplied = true; }'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '        catch (e) { applyingSDK = false; }'
    new = '        catch (e) { applyingSDK = false; sdkDetected = false; sdkRemoteReviewed = false; window.MsbtProtectionReviewed = false; if (window.MsbtResetProtectionReview) window.MsbtResetProtectionReview(); }'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '        sdkLastSeen = Date.now ? Date.now() : 1;\n        if (saveAckTimer'
    new = '        if (saveAckTimer'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '            el.innerHTML = (currentStorageMode === "sdk") ? "SDK JSON selected, but the direct Gameface/SDK bridge has not answered yet. Session values are still being used." : "Auto: waiting for the direct Gameface/SDK bridge; session fallback is active until it answers.";'
    new = '            el.innerHTML = sdkStorageState === "missing" ? "First-time setup: review the protected list, select the review button, then choose Save (an empty list is allowed)." : sdkStorageState === "invalid" || sdkStorageState === "changed" ? "SDK settings are invalid or changed. They were not overwritten; restore or repair the file before saving." : "Waiting for the SDK bridge. Bulk removal is disabled until protection is verified.";'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '    function sendSettingsToSDK()'
    new = '    function sendSettingsToSDK(initialize)'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '        if (!(window.engine && engine.trigger)) return false;'
    new = '        if (!(window.engine && engine.trigger) || sdkSending) return false;'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '        if (!bytes || !bytes.length) return false;'
    new = old + '\n        sdkSending = true;'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '                engine.trigger(SDK_COMMIT_EVENT);\n            }\n            catch (e)'
    new = '                engine.trigger(SDK_COMMIT_EVENT);\n                sdkSending = false;\n            }\n            catch (e)'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '            catch (e)\n            {\n                if (status)'
    new = '            catch (e)\n            {\n                sdkSending = false;\n                if (status)'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '        if (currentStorageMode === "session") return;\n        try'
    new = '        if (currentStorageMode === "session" || sdkSending) return;\n        try'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '        try { bytes = utf8Bytes(JSON.stringify(compactPayload())); }'
    new = '        try { var payload = compactPayload(); payload.reviewed = true; if (initialize === true) payload.initialize = true; bytes = utf8Bytes(JSON.stringify(payload)); }'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '    function saveSettingsNow()'
    new = """    function ensureProtectionReview() {
        var review = byId("shift_protection_review");
        if (review) return review;
        var status = byId("shift_settings_storage_status");
        if (!status || !status.parentNode || !document.createElement) return null;
        var row = document.createElement("div");
        row.className = "shift-settings-storage-status";
        row.innerHTML = '<div id="shift_protection_review" class="shift-settings-footer-btn primary" role="button" tabindex="0" aria-pressed="false" onclick="window.MsbtToggleProtectionReview(); return false;" onkeydown="if (event.key === &quot;Enter&quot; || event.key === &quot; &quot;) { window.MsbtToggleProtectionReview(); return false; }">Not reviewed — click after reviewing the list</div><span>If the list is empty, no friends are protected.</span>';
        status.parentNode.insertBefore(row, status);
        return byId("shift_protection_review");
    }
    window.MsbtSetProtectionReview = function (pressed) {
        var review = byId("shift_protection_review");
        if (!review) return;
        review.setAttribute("aria-pressed", pressed ? "true" : "false");
        review.textContent = pressed ? "Reviewed — click to undo" : "Not reviewed — click after reviewing the list";
    };
    window.MsbtToggleProtectionReview = function () {
        var review = byId("shift_protection_review");
        if (!review) return;
        var pressed = review.getAttribute("aria-pressed") !== "true";
        if (!pressed && window.MsbtProtectionReviewed === true) {
            window.MsbtProtectionReviewed = false;
            window.MsbtProtectionDirty = true;
        }
        review.setAttribute("aria-pressed", pressed ? "true" : "false");
        review.textContent = pressed ? "Reviewed — click to undo" : "Not reviewed — click after reviewing the list";
    };
    window.MsbtResetProtectionReview = function () {
        var review = byId("shift_protection_review");
        if (review) {
            review.setAttribute("aria-pressed", "false");
            review.textContent = "Not reviewed — click after reviewing the list";
        }
    };

    function saveSettingsNow()"""
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '        var sent = sendSettingsToSDK();'
    new = """        var initialize = false;
        if (!sdkDetected) {
            if (sdkStorageState !== "missing" || !sdkStateSeen || Date.now() - sdkStateSeen >= 10000) {
                updateStorageStatus();
                return false;
            }
            initialize = true;
        }
        if (initialize || window.MsbtProtectionDirty || !window.MsbtProtectionReviewed) {
            var review = ensureProtectionReview();
            if (!review || review.getAttribute("aria-pressed") !== "true") {
                var reviewStatus = byId("shift_settings_storage_status");
                if (reviewStatus) reviewStatus.innerHTML = "Review the protected list and select the review button before Save. An empty list protects no friends.";
                return false;
            }
        }
        saveAckReceived = false;
        pendingProtection = protectionSignature(window.ShiftFriendAutomation.getProtectedNames());
        var sent = sendSettingsToSDK(initialize);
        if (!sent) pendingProtection = null;"""
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '        requestSDKSettings: requestSDKSettings\n'
    new = '        requestSDKSettings: requestSDKSettings,\n        protectionReady: function () { return currentStorageMode !== "session" && !window.MsbtProtectionDirty && window.MsbtProtectionReviewed === true && sdkRemoteReviewed && sdkDetected && sdkLastSeen > 0 && Date.now() - sdkLastSeen < 10000; },\n        backgroundBridge: function () { return sdkPort !== null && sdkInstance && sdkBridgeSeen > 0 && Date.now() - sdkBridgeSeen < 10000 ? {port:sdkPort, instance:sdkInstance, start_token:sdkStartToken} : null; }\n'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '    setupSDKBridge();'
    new = '    ensureProtectionReview();\n    setupSDKBridge();'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = '        window.setTimeout(requestSDKSettings, 2500);'
    new = old + '\n        window.setInterval(requestSDKSettings, 5000);'
    assert text.count(old) == 1
    text = text.replace(old, new)
    # The local HTTP bridge is authenticated by the SDK companion against the
    # connecting TCP owner PID, not by an Origin or User-Agent string.
    start = text.index('    function sendSettingsToSDK(initialize)')
    end = text.index('    function notifySettingsChanged()', start)
    text = text[:start] + HTTP_SEND + text[end:]
    start = text.index('    function requestSDKSettings()')
    end = text.index('    function protectionSignature(', start)
    text = text[:start] + HTTP_GET + text[end:]
    start = text.index('    function setupSDKBridge()')
    end = text.index('    function resetAllSettings()', start)
    text = text[:start] + HTTP_SETUP + text[end:]
    return text


HTTP_SEND = """    var sdkPort = null, sdkInstance = null, sdkRequesting = false, sdkBridgeSeen = 0, sdkStartToken = null;
    var sdkPorts = [47991, 47992, 47993], sdkNextPort = 0;

    function validBridgeResponse(data) {
        return !!data && data.ok === true && data.service === "msbt-shift-storage" &&
            data.protocol === 1 && typeof data.instance === "string" && /^[0-9a-f]{32}$/.test(data.instance) &&
            typeof data.storageValid === "boolean" && typeof data.storageState === "string" &&
            (data.storageValid !== true || (Array.isArray(data.protectedPlayers) &&
             data.protectedPlayers.every(function (name) { return typeof name === "string"; }) &&
             data.settings && typeof data.settings === "object" && !Array.isArray(data.settings) &&
             typeof data.reviewed === "boolean"));
    }
    function bridgeFailed() {
        sdkDetected = false; sdkRemoteReviewed = false; window.MsbtProtectionReviewed = false; if (window.MsbtResetProtectionReview) window.MsbtResetProtectionReview(); sdkLastSeen = 0; sdkStorageState = "unavailable";
        sdkPort = null; sdkInstance = null; sdkBridgeSeen = 0; sdkStartToken = null; updateStorageStatus();
    }
    function sendSettingsToSDK(initialize) {
        if (sdkSending || sdkRequesting || sdkPort === null || !sdkInstance) return false;
        var payload, body, xhr, port = sdkPort, instance = sdkInstance, done = false;
        try {
            payload = compactPayload(); payload.reviewed = true;
            if (initialize === true) payload.initialize = true;
            body = JSON.stringify(payload); xhr = new XMLHttpRequest();
            sdkSending = true;
            function finish(success) {
                if (done) return; done = true; sdkSending = false;
                if (!success) { saveAckReceived = false; bridgeFailed(); }
            }
            xhr.open("POST", "http://127.0.0.1:" + port + "/shift-settings", true);
            xhr.timeout = 2500;
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.setRequestHeader("X-MSBT-Shift-Instance", instance);
            xhr.onload = function () {
                var data;
                try { data = JSON.parse(xhr.responseText); } catch (_) { finish(false); return; }
                if (xhr.status !== 200 || !validBridgeResponse(data) || data.instance !== instance ||
                    data.saved !== true || data.storageValid !== true) { finish(false); return; }
                finish(true); sdkBridgeSeen = Date.now(); sdkStartToken = data.background && data.background.start_token; handleSDKSaved(); handleSDKSettings(data);
            };
            xhr.onerror = xhr.ontimeout = xhr.onabort = function () { finish(false); };
            xhr.send(body);
            return true;
        } catch (_) { sdkSending = false; bridgeFailed(); return false; }
    }

"""

HTTP_GET = """    function requestSDKSettings() {
        if (sdkSending || sdkRequesting) return;
        sdkRequesting = true;
        var attempts = 0;
        function probe() {
            if (sdkSending) { sdkRequesting = false; return; }
            var port = sdkPorts[sdkNextPort]; sdkNextPort = (sdkNextPort + 1) % sdkPorts.length;
            var xhr, done = false;
            function failed() {
                if (done) return; done = true;
                if (++attempts < sdkPorts.length) probe();
                else { sdkRequesting = false; bridgeFailed(); }
            }
            try {
                xhr = new XMLHttpRequest();
                xhr.open("GET", "http://127.0.0.1:" + port + "/shift-settings", true);
                xhr.timeout = 1000;
                xhr.onload = function () {
                    var data;
                    try { data = JSON.parse(xhr.responseText); } catch (_) { failed(); return; }
                    if (xhr.status !== 200 || !validBridgeResponse(data)) { failed(); return; }
                    done = true; sdkRequesting = false; if (sdkInstance && sdkInstance !== data.instance) { sdkRemoteReviewed = false; window.MsbtProtectionReviewed = false; if (window.MsbtResetProtectionReview) window.MsbtResetProtectionReview(); } sdkPort = port; sdkInstance = data.instance; sdkBridgeSeen = Date.now(); sdkStartToken = data.background && data.background.start_token;
                    if (currentStorageMode === "session") { if (window.MsbtShiftBackground && window.MsbtShiftBackground.onCompanionState) { try { window.MsbtShiftBackground.onCompanionState(data.background); } catch (_) {} } return; }
                    handleSDKSettings(data);
                };
                xhr.onerror = xhr.ontimeout = xhr.onabort = failed;
                xhr.send();
            } catch (_) { failed(); }
        }
        probe();
    }

"""

HTTP_SETUP = """    function setupSDKBridge() {
        window.setTimeout(requestSDKSettings, 700);
        window.setTimeout(requestSDKSettings, 2500);
        window.setInterval(requestSDKSettings, 5000);
    }

"""
