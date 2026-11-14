"""Repair the ambiguous protected-name form in the pinned upstream dashboard."""


def repair_html(text):
    start = text.index('            <div class="shift-settings-protected-tools">')
    end = text.index('            <div id="shift_settings_protected_list"', start)
    assert text.count('id="shift_settings_protected_add_input"') == 1
    return text[:start] + '''            <label for="shift_settings_protected_add_input" style="display:block; margin-bottom:0.5vh;">SHiFT / display name to protect</label>
            <div class="shift-settings-protected-tools">
                <input id="shift_settings_protected_add_input" class="shift-settings-input" type="text" onkeydown="if (event.key === 'Enter' || event.keyCode === 13) { window.ShiftMiniPanel.addProtectedFromSettings(); return false; }">
                <div id="shift_settings_protected_add_btn" class="shift-settings-small-btn" role="button" tabindex="0" onclick="return window.ShiftMiniPanel.addProtectedFromSettings();" onkeydown="if (event.key === 'Enter' || event.key === ' ') { window.ShiftMiniPanel.addProtectedFromSettings(); return false; }">Add</div>
            </div>
            <div id="shift_settings_protected_feedback" class="shift-settings-note" role="status" aria-live="polite">Add a name, review the list, then choose Save.</div>
            <label for="shift_settings_protected_search" style="display:block; margin-top:0.8vh; margin-bottom:0.5vh;">Search names already protected</label>
            <div class="shift-settings-protected-tools">
                <input id="shift_settings_protected_search" class="shift-settings-input" type="text" oninput="window.ShiftMiniPanel.filterProtected(this.value);">
            </div>
''' + text[end:]


def repair_controller(text):
    start = text.index('    function addProtectedFromSettings()')
    end = text.index('    function filterProtected(value)', start)
    return text[:start] + '''    function setSettingsProtectedFeedback(message)
    {
        var feedback = byId("shift_settings_protected_feedback");
        if (!feedback) return;
        while (feedback.firstChild) feedback.removeChild(feedback.firstChild);
        feedback.appendChild(document.createTextNode(message));
    }

    function addProtectedFromSettings()
    {
        var input = byId("shift_settings_protected_add_input");
        if (!input) return false;
        var name = String(input.value || "").replace(/^\\s+|\\s+$/g, "");
        if (!name) {
            setSettingsProtectedFeedback("Enter a SHiFT / display name in the field beside Add.");
            input.focus();
            return false;
        }
        if (!window.ShiftFriendAutomation || !window.ShiftFriendAutomation.addProtectedName) {
            setSettingsProtectedFeedback("Protected-player controls are unavailable. Close and reopen this menu.");
            return false;
        }
        var added = window.ShiftFriendAutomation.addProtectedName(name);
        // A previous search must not hide the name just added (or an existing duplicate).
        currentProtectedFilter = "";
        var search = byId("shift_settings_protected_search");
        if (search) search.value = "";
        if (added) input.value = "";
        renderProtectedNames();
        renderSettingsProtectedNames();
        if (added) notifySettingsChanged();
        setSettingsProtectedFeedback(added ? "Added: " + name + ". Review the list, then choose Save." : "Already protected: " + name + ".");
        return false;
    }

''' + text[end:]
