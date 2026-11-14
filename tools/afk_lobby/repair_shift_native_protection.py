"""Expose the existing protected-list editor through BL4's native Friends UI.

Apply after repair_shift_protected_inputs. Native action IDs, model binding and
SHIFT_SERVICE name selection come from the pinned v4.4 dashboard source.
"""


def _replace(text, before, after, count=1):
    assert text.count(before) == count, f"Unexpected SHiFT source: {before!r}"
    return text.replace(before, after)


def repair_html(text):
    protected_title = '            <div class="shift-settings-section-title">Protected Players</div>'
    start = text.rindex('        <div class="shift-settings-section">', 0, text.index(protected_title))
    end = text.index('        <div class="shift-settings-section">', text.index(protected_title))
    protected = text[start:end]
    text = text[:start] + '''        <div class="shift-settings-section">
            <div class="shift-settings-section-title">Protected Players</div>
            <div class="shift-settings-note">Manage the saved protection list in the SHiFT Friends menu.</div>
            <div id="shift_settings_open_protected" class="shift-settings-small-btn" role="button" tabindex="0" onclick="return window.ShiftMiniPanel.openProtectedList();">Open protected players</div>
        </div>

''' + text[end:]
    storage_title = '            <div class="shift-settings-section-title">Storage</div>'
    start = text.rindex('        <div class="shift-settings-section">', 0, text.index(storage_title))
    end = text.index('        <div class="shift-settings-footer">', start)
    storage = text[start:end]
    text = text[:start] + text[end:]
    panel = '''
                    <div id="msbt_native_protection_panel" class="base-cont content-font" style="display:none; position:absolute; left:0; right:0; top:0; height:100%; max-height:86.8vh; overflow-y:auto; padding:2vh; z-index:100; color:#fff; background:#13232b; border:1px solid #3ecfba; box-sizing:border-box;">
                        <div class="shift-settings-header">
                            <div class="shift-settings-title">Protected players</div>
                            <div id="msbt_native_protection_close" class="shift-settings-close" role="button" tabindex="0" onclick="return window.ShiftMiniPanel.closeProtectedList();">Back</div>
                            <div id="msbt_native_protection_save" class="shift-settings-footer-btn primary" role="button" tabindex="0" onclick="return window.ShiftMiniPanel.saveSettingsNow();">Save protected list</div>
                        </div>
                        <div class="shift-settings-note">Players on this list are excluded from Remove All and Remove Offline. Changes require review and Save.</div>
''' + protected + storage + '''
                    </div>
'''
    marker = '                <div id="friends_container" class="friends-container hide">'
    text = _replace(text, marker, marker + panel)
    for suffix in ('', '_two_col'):
        marker = f'                                            <div id="friends_remove_all_btn{suffix}"'
        button = f'''                                            <div id="friends_protected_list_btn{suffix}" class="sw_btn-icon friend-automation-btn is-visible" role="button" tabindex="0" style="margin-right:2vh; cursor:pointer;" onclick="return window.ShiftMiniPanel.openProtectedList();">
                                                <div class="sw_btn-icon-text pc content-font">Protected players</div>
                                            </div>
'''
        text = _replace(text, marker, button + marker)
    # Keep the native profile/editor focus visible without relying on :focus support.
    text = _replace(text, '    </style>', '''        #msbt_native_protection_panel .msbt-protection-focused { outline:2px solid #3ecfba; }
        #msbt_native_protection_panel label { display:block; font-size:1.6vh; }
        #msbt_native_protection_panel .shift-settings-title { font-size:2.5vh; }
        #msbt_native_protection_panel .shift-settings-section-title,
        #msbt_native_protection_panel .shift-settings-row,
        #msbt_native_protection_panel .shift-settings-input,
        #msbt_native_protection_panel .shift-settings-small-btn,
        #msbt_native_protection_panel .shift-settings-footer-btn,
        #msbt_native_protection_panel .shift-settings-protected-item { font-size:1.8vh; }
        #msbt_native_protection_panel .shift-settings-close,
        #msbt_native_protection_panel .shift-settings-choice { font-size:1.6vh; }
        #msbt_native_protection_panel .shift-settings-note { font-size:1.35vh; }
        #msbt_native_protection_panel .shift-settings-storage-status { font-size:1.4vh; }
        #msbt_native_protection_panel .shift-settings-protected-list { max-height:26vh; }
    </style>''')
    return text


NATIVE_API = '''
// Native Friends protection uses the same mutable list and explicit Save guard.
window.MsbtNativeProtection = (function () {
    function selectedName() {
        var player = friends_model.selectedPlayer;
        if (!player || !Array.isArray(player.info)) return "";
        for (var i = 0; i < player.info.length; i++) {
            var info = player.info[i];
            if (info && info.service === SHIFT_SERVICE && typeof info.text === "string")
                return info.text.replace(/^\\s+|\\s+$/g, "");
        }
        return "";
    }
    function protectedAlready(name) {
        return !!(window.ShiftFriendAutomation && window.ShiftFriendAutomation.getProtectedNames().some(function (value) {
            return String(value).toLowerCase() === name.toLowerCase();
        }));
    }
    function appendAction(actions) {
        var name = selectedName();
        if (!name || !window.ShiftFriendAutomation) return;
        actions.unshift({id:"msbtProtectPlayerActionId", display:protectedAlready(name) ? "Protected player - view list" : "Protect player", disabled:false});
    }
    function protectSelected() {
        var name = selectedName();
        if (!name || !window.ShiftFriendAutomation || !window.ShiftMiniPanel) return false;
        var added = window.ShiftFriendAutomation.addProtectedName(name);
        window.ShiftMiniPanel.openProtectedList();
        window.ShiftMiniPanel.filterProtected("");
        var search = document.getElementById("shift_settings_protected_search");
        if (search) search.value = "";
        if (added) window.ShiftMiniPanel.notifySettingsChanged();
        var feedback = document.getElementById("shift_settings_protected_feedback");
        if (feedback) {
            while (feedback.firstChild) feedback.removeChild(feedback.firstChild);
            feedback.appendChild(document.createTextNode(added ? "Added: " + name + ". Review the list, then choose Save protected list." : "Already protected: " + name + "."));
        }
        return false;
    }
    return {appendAction:appendAction, protectSelected:protectSelected};
})();
'''


PANEL_METHODS = '''    var nativeProtectionFocus = 0;
    function openProtectedList()
    {
        closeSettings(false);
        // Use the dashboard's existing side-menu route if opened from Customize.
        if ($("#friends_container").hasClass("hide")) {
            side_menu_controller.showSideMenu();
            side_menu_controller.onFriendsClick();
        }
        var panel = byId("msbt_native_protection_panel");
        if (!panel) return false;
        panel.style.display = "block";
        loadSettingsIntoControls();
        ensureProtectionReview();
        renderProtectedNames();
        renderSettingsProtectedNames();
        if (currentStorageMode !== "session") requestSDKSettings();
        nativeProtectionFocus = 0;
        focusNativeProtection(0);
        return false;
    }

    function closeProtectedList()
    {
        var panel = byId("msbt_native_protection_panel");
        if (panel) panel.style.display = "none";
        return false;
    }

    function nativeProtectionActions()
    {
        var panel = byId("msbt_native_protection_panel");
        return panel ? panel.querySelectorAll("#shift_protection_review, #msbt_native_protection_save, #msbt_native_protection_close, .shift-settings-protected-remove") : [];
    }

    function focusNativeProtection(offset)
    {
        var actions = nativeProtectionActions();
        if (!actions.length) return;
        nativeProtectionFocus = Math.max(0, Math.min(actions.length - 1, nativeProtectionFocus + offset));
        for (var i = 0; i < actions.length; i++) {
            actions[i].className = String(actions[i].className).replace(/\\s*msbt-protection-focused/g, "");
            if (i === nativeProtectionFocus) actions[i].className += " msbt-protection-focused";
        }
        if (actions[nativeProtectionFocus].scrollIntoView) actions[nativeProtectionFocus].scrollIntoView(false);
    }

    function handleProtectedListPad(action, phase)
    {
        var panel = byId("msbt_native_protection_panel");
        if (!panel || panel.style.display === "none" || $("#friends_container").hasClass("hide")) return false;
        if (phase === "held") {
            if (!dashboard_control.isButtonHeld) {
                dashboard_control.buttonPressStartTime = Date.now();
                dashboard_control.isButtonHeld = true;
                dashboard_control.gamepadHasScrolled = false;
            } else if ((action === PadKeys.Up || action === PadKeys.Down) && Date.now() - dashboard_control.buttonPressStartTime > dashboard_control.gamepadScrollInterval) {
                dashboard_control.gamepadHasScrolled = true;
                dashboard_control.buttonPressStartTime = Date.now();
                handleProtectedListPad(action);
            }
            return true;
        }
        if (phase === "released") {
            var repeated = dashboard_control.gamepadHasScrolled && (action === PadKeys.Up || action === PadKeys.Down);
            dashboard_control.buttonPressStartTime = 0;
            dashboard_control.gamepadHasScrolled = false;
            dashboard_control.isButtonHeld = false;
            if (repeated) return true;
        }
        if (action === PadKeys.B) closeProtectedList();
        else if (action === PadKeys.Down) focusNativeProtection(1);
        else if (action === PadKeys.Up) focusNativeProtection(-1);
        else if (action === PadKeys.A || action === Keys.FEnter) {
            var active = document.activeElement;
            if (active && active.tagName === "INPUT") return true;
            var actions = nativeProtectionActions();
            if (actions[nativeProtectionFocus]) actions[nativeProtectionFocus].click();
        }
        // Never route hidden underlying profile actions while this panel is open.
        return true;
    }

'''


def repair_controller(text):
    text = _replace(text,
                    '        friends_model.playerProfileActions = JSON.parse(JSON.stringify(actions));',
                    '        friends_model.playerProfileActions = JSON.parse(JSON.stringify(actions));\n'
                    '        if (actions !== friends_model.reportActionsList && window.MsbtNativeProtection) window.MsbtNativeProtection.appendAction(friends_model.playerProfileActions);')
    text = _replace(text,
                    '                var btn = $(this).attr("action-id");\n\n                // View Friend Profile',
                    '                var btn = $(this).attr("action-id");\n'
                    '                if (btn === "msbtProtectPlayerActionId") return window.MsbtNativeProtection.protectSelected();\n\n'
                    '                // View Friend Profile')
    text = _replace(text, '    function openSettings()\n    {', PANEL_METHODS + '    function openSettings()\n    {\n        closeProtectedList();')
    text = _replace(text,
                    '        openSettings: openSettings, closeSettings: closeSettings,',
                    '        openSettings: openSettings, closeSettings: closeSettings,\n'
                    '        openProtectedList: openProtectedList, closeProtectedList: closeProtectedList, handleProtectedListPad: handleProtectedListPad,')
    text = _replace(text,
                    '            friends_control.handlePad(btnAction, isKeyboard);',
                    '            if (window.ShiftMiniPanel && window.ShiftMiniPanel.handleProtectedListPad(btnAction)) return;\n'
                    '            friends_control.handlePad(btnAction, isKeyboard);')
    text = _replace(text,
                    '\t\thandleButtonRelease(btnAction, isKeyboard)\n\t\t{',
                    '\t\thandleButtonRelease(btnAction, isKeyboard)\n\t\t{\n'
                    '            if (window.ShiftMiniPanel && window.ShiftMiniPanel.handleProtectedListPad(btnAction, "released")) return;')
    text = _replace(text,
                    '\t\thandleButtonHeld(btnAction, isKeyboard)\n\t\t{',
                    '\t\thandleButtonHeld(btnAction, isKeyboard)\n\t\t{\n'
                    '            if (window.ShiftMiniPanel && window.ShiftMiniPanel.handleProtectedListPad(btnAction, "held")) return;')
    return text + '\n' + NATIVE_API
