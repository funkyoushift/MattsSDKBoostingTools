(function () {
  window.MSBT_MATT_EDITOR_ADAPTER_VERSION = "deliver-4-target-selector";

  var BASE85_RE = /@U[0-9A-Za-z!#$%&()*+\-;<=>?@^_`{\/}~]+/g;
  var SOURCE_DEFS = [
    { id: "finalOutputBase85", label: "Final Base85 Output" },
    { id: "mi_finalOutputBase85", label: "Modded Item Base85 Output" },
    { id: "serializedOutput", label: "Serialized Output" },
    { id: "bulkSerialOutput", label: "Bulk Serial Output" }
  ];
  var state = {
    detected: [],
    pendingSerial: "",
    confirmedSerial: "",
    stale: false,
    players: [],
    selectedTarget: "",
    selectedTargetLabel: "",
    bridgeOnline: false
  };

  function byId(id) {
    return document.getElementById(id);
  }

  function textFromElement(id) {
    var el = byId(id);
    if (!el) return "";
    if (typeof el.value === "string" && el.value.trim()) return el.value.trim();
    if (typeof el.textContent === "string" && el.textContent.trim()) return el.textContent.trim();
    return "";
  }

  function findBase85Serials(text) {
    var matches = String(text || "").match(BASE85_RE) || [];
    var out = [];
    for (var i = 0; i < matches.length; i += 1) {
      var value = String(matches[i] || "").trim();
      if (value) out.push(value);
    }
    return out;
  }

  function serialShort(serial) {
    if (!serial) return "";
    if (serial.length <= 34) return serial;
    return serial.slice(0, 18) + "..." + serial.slice(-10);
  }

  function collectDetectedSerials() {
    var bySerial = {};
    var ordered = [];
    for (var i = 0; i < SOURCE_DEFS.length; i += 1) {
      var source = SOURCE_DEFS[i];
      var serials = findBase85Serials(textFromElement(source.id));
      for (var j = 0; j < serials.length; j += 1) {
        var serial = serials[j];
        if (!bySerial[serial]) {
          bySerial[serial] = {
            serial: serial,
            labels: []
          };
          ordered.push(bySerial[serial]);
        }
        if (bySerial[serial].labels.indexOf(source.label) < 0) {
          bySerial[serial].labels.push(source.label);
        }
      }
    }
    return ordered;
  }

  function serialValidationMessage(serial) {
    var text = String(serial || "").trim();
    if (!text) return "No confirmed item serial is ready to send. Build or select an item first.";
    if (text.indexOf("\n") >= 0 || text.indexOf("\r") >= 0) return "Invalid serial: the confirmed field contains multiple lines.";
    var matches = findBase85Serials(text);
    if (matches.length !== 1 || matches[0] !== text) return "Invalid serial: select exactly one @U item serial.";
    if (text.indexOf("@U") !== 0) return "Invalid serial: item serial must start with @U.";
    if (text.length < 20) return "Invalid serial: item serial is too short.";
    return "";
  }

  function currentSerial() {
    var serial = String(state.confirmedSerial || "").trim();
    return serialValidationMessage(serial) ? "" : serial;
  }

  function currentLevel() {
    var candidates = ["outputLevel", "mi_level", "level", "itemLevel"];
    for (var i = 0; i < candidates.length; i += 1) {
      var raw = textFromElement(candidates[i]);
      var parsed = parseInt(raw, 10);
      if (!Number.isNaN(parsed)) return Math.max(1, Math.min(60, parsed));
    }
    return 60;
  }

  function setStatus(message, ok) {
    var el = byId("msbt-delivery-status");
    if (!el) return;
    el.textContent = message || "";
    el.style.color = ok ? "#43d17a" : "#ffcc33";
  }

  function playerValue(player) {
    var idx = player && player.index;
    var name = player && player.name ? String(player.name) : "";
    if (idx === null || idx === undefined || idx === "") return name;
    return String(idx) + " | " + name;
  }

  function playerLabel(player) {
    var idx = player && player.index;
    var name = player && player.name ? String(player.name) : "";
    if (idx === null || idx === undefined || idx === "") return name || "Unknown player";
    return "Player " + String(idx) + ": " + (name || "Unknown");
  }

  function targetFromStatus(status) {
    var idx = status && status.selected_player_index;
    var name = status && status.selected_player ? String(status.selected_player) : "";
    if (idx === null || idx === undefined || idx === "" || !name) return "";
    return String(idx) + " | " + name;
  }

  function targetLabelFromValue(value) {
    var text = String(value || "").trim();
    if (!text) return "No target selected";
    var parts = text.split("|");
    if (parts.length >= 2) {
      return "Player " + parts[0].trim() + ": " + parts.slice(1).join("|").trim();
    }
    return text;
  }

  function renderTargetSection() {
    var bridge = byId("msbt-bridge-state");
    var select = byId("msbt-target-select");
    var display = byId("msbt-target-display");
    if (bridge) {
      bridge.textContent = state.bridgeOnline
        ? "Bridge: connected | players: " + String(state.players.length)
        : "Bridge: offline or unknown";
      bridge.style.color = state.bridgeOnline ? "#43d17a" : "#ffcc33";
    }
    if (select) {
      select.innerHTML = "";
      var blank = document.createElement("option");
      blank.value = "";
      blank.textContent = state.players.length ? "Select target player" : "No players loaded";
      select.appendChild(blank);
      for (var i = 0; i < state.players.length; i += 1) {
        var player = state.players[i];
        var opt = document.createElement("option");
        opt.value = playerValue(player);
        opt.textContent = playerLabel(player);
        if (opt.value === state.selectedTarget) opt.selected = true;
        select.appendChild(opt);
      }
      select.disabled = !state.bridgeOnline || state.players.length === 0;
    }
    if (display) {
      display.textContent = "Selected target: " + targetLabelFromValue(state.selectedTarget);
      display.style.color = state.selectedTarget ? "#f1f5ff" : "#ffcc33";
    }
  }

  function applyBridgeStatus(status, message, ok) {
    status = status || {};
    state.bridgeOnline = true;
    state.players = Array.isArray(status.players) ? status.players : [];
    state.selectedTarget = targetFromStatus(status);
    state.selectedTargetLabel = targetLabelFromValue(state.selectedTarget);
    renderTargetSection();
    refreshPreview(message || ("Bridge online. " + state.selectedTargetLabel + " | Players: " + state.players.length), ok !== false);
  }

  function applyBridgeOffline(message) {
    state.bridgeOnline = false;
    state.players = [];
    state.selectedTarget = "";
    state.selectedTargetLabel = "";
    renderTargetSection();
    refreshPreview(message || "Game bridge offline.", false);
  }

  function refreshPreview(message, ok) {
    var preview = byId("msbt-serial-preview");
    var selectWrap = byId("msbt-serial-select-wrap");
    var select = byId("msbt-serial-select");
    var count = byId("msbt-serial-count");
    var sendButtons = document.querySelectorAll("[data-msbt-deliver-mode]");
    var validation = serialValidationMessage(state.confirmedSerial);
    var ready = !validation && !state.stale;

    if (preview) {
      if (state.stale && state.confirmedSerial) {
        preview.textContent = "Confirmed serial may be stale - refresh and confirm before sending:\n" + state.confirmedSerial;
        preview.style.color = "#ffcc33";
      } else if (state.confirmedSerial && validation) {
        preview.textContent = validation + "\n" + state.confirmedSerial;
        preview.style.color = "#ffcc33";
      } else if (state.confirmedSerial) {
        preview.textContent = "Serial to Send confirmed:\n" + state.confirmedSerial;
        preview.style.color = "#f1f5ff";
      } else if (state.pendingSerial) {
        preview.textContent = "Detected serial waiting for confirmation:\n" + state.pendingSerial;
        preview.style.color = "#ffcc33";
      } else if (state.detected.length > 1) {
        preview.textContent = "Multiple @U serials detected. Choose one, then click Confirm Serial to Send.";
        preview.style.color = "#ffcc33";
      } else {
        preview.textContent = "No serial confirmed yet";
        preview.style.color = "#ffcc33";
      }
    }

    if (count) {
      count.textContent = String(state.detected.length) + " detected serial" + (state.detected.length === 1 ? "" : "s");
    }

    if (selectWrap && select) {
      selectWrap.style.display = state.detected.length > 1 ? "block" : "none";
      select.innerHTML = "";
      var blank = document.createElement("option");
      blank.value = "";
      blank.textContent = "Choose which serial to send";
      select.appendChild(blank);
      for (var i = 0; i < state.detected.length; i += 1) {
        var item = state.detected[i];
        var opt = document.createElement("option");
        opt.value = String(i);
        opt.textContent = item.labels.join(", ") + " | " + serialShort(item.serial);
        if (item.serial === state.pendingSerial) opt.selected = true;
        select.appendChild(opt);
      }
    }

    for (var j = 0; j < sendButtons.length; j += 1) {
      var mode = sendButtons[j].getAttribute("data-msbt-deliver-mode") || "";
      var modeReady = ready && (mode !== "selected" || !!state.selectedTarget);
      sendButtons[j].disabled = !modeReady;
      sendButtons[j].style.opacity = modeReady ? "1" : ".55";
      sendButtons[j].style.cursor = modeReady ? "pointer" : "not-allowed";
    }

    if (message) setStatus(message, ok !== false);
  }

  function refreshDetectedSerials() {
    state.detected = collectDetectedSerials();
    state.pendingSerial = "";
    state.confirmedSerial = "";
    state.stale = false;
    if (state.detected.length === 0) {
      refreshPreview("No serial detected. Build or select an item first.", false);
      return;
    }
    if (state.detected.length === 1) {
      state.pendingSerial = state.detected[0].serial;
      refreshPreview("Serial detected. Click Confirm Serial to Send before delivery.", false);
      return;
    }
    refreshPreview("Multiple @U serials detected. Choose the serial to send.", false);
  }

  function confirmPendingSerial() {
    var validation = serialValidationMessage(state.pendingSerial);
    if (validation) {
      setStatus(validation, false);
      return;
    }
    state.confirmedSerial = state.pendingSerial;
    state.stale = false;
    refreshPreview("Serial confirmed and ready to send.", true);
  }

  function markPreviewStale() {
    var active = document.activeElement;
    var panel = byId("msbt-delivery-panel");
    if (panel && active && panel.contains(active)) return;
    if (!state.confirmedSerial || state.stale) return;
    state.stale = true;
    refreshPreview("Serial may be stale - click Refresh Detected Serial before sending.", false);
  }

  function button(label, mode, color) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = label;
    btn.setAttribute("data-msbt-deliver-mode", mode);
    btn.style.cssText = [
      "padding:7px 9px",
      "border:none",
      "background:#172033",
      "color:" + color,
      "font-weight:700",
      "font-size:11px",
      "cursor:pointer"
    ].join(";");
    btn.addEventListener("click", function () {
      deliver(mode);
    });
    return btn;
  }

  async function bridgeStatus() {
    try {
      var response = await fetch("/msbt/status");
      var data = await response.json();
      if (!response.ok || !data.ok) {
        applyBridgeOffline(data.message || "SDK bridge is offline.");
        return;
      }
      var status = data.status || {};
      var selected = status.selected_player || "no selected player";
      var count = Array.isArray(status.players) ? status.players.length : 0;
      applyBridgeStatus(status, "Bridge online. Selected: " + selected + " | Players: " + count, true);
    } catch (err) {
      applyBridgeOffline("SDK bridge status failed: " + err);
    }
  }

  async function setTarget(value) {
    state.selectedTarget = String(value || "").trim();
    var requestedTarget = state.selectedTarget;
    renderTargetSection();
    refreshPreview(state.selectedTarget ? "Updating selected target..." : "Select a target player first.", !!state.selectedTarget);
    if (!state.selectedTarget) return;
    try {
      var response = await fetch("/msbt/target", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_player: state.selectedTarget })
      });
      var data = await response.json();
      if (!response.ok || !data.ok) {
        setStatus(data.message || "Target update failed.", false);
        refreshPreview("", false);
        return;
      }
      if (data.status) {
        applyBridgeStatus(data.status, data.message || ("Selected target: " + targetLabelFromValue(requestedTarget)), true);
      } else {
        state.selectedTarget = requestedTarget;
        state.selectedTargetLabel = targetLabelFromValue(requestedTarget);
        renderTargetSection();
        refreshPreview(data.message || ("Selected target: " + state.selectedTargetLabel), true);
      }
    } catch (err) {
      setStatus("Target update failed: " + err, false);
      refreshPreview("", false);
    }
  }

  async function deliver(mode) {
    var validation = serialValidationMessage(state.confirmedSerial);
    if (state.stale) {
      setStatus("Serial may be stale - click Refresh Detected Serial, then Confirm Serial to Send.", false);
      return;
    }
    if (validation) {
      setStatus(validation, false);
      return;
    }
    var serial = currentSerial();
    if (!serial) {
      setStatus("No confirmed item serial is ready to send. Build or select an item first.", false);
      return;
    }
    if (mode === "selected" && !state.selectedTarget) {
      setStatus("Select a target player first.", false);
      return;
    }
    if (mode !== "selected") {
      var ok = window.confirm("Send this generated item to " + mode + "?");
      if (!ok) return;
    }
    setStatus("Sending item through MSBT bridge...", true);
    try {
      var response = await fetch("/msbt/deliver", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: mode, serial: serial, level: currentLevel(), target_player: state.selectedTarget })
      });
      var data = await response.json();
      var message = data.message || (data.ok ? "Delivery requested." : "Delivery failed.");
      setStatus(message, data.ok !== false && response.ok);
    } catch (err) {
      setStatus("Delivery failed: " + err, false);
    }
  }

  async function copyConfirmedSerial() {
    var validation = serialValidationMessage(state.confirmedSerial);
    if (validation) {
      setStatus(validation, false);
      return;
    }
    try {
      await navigator.clipboard.writeText(state.confirmedSerial);
      setStatus("Copied the confirmed item serial.", true);
    } catch (err) {
      setStatus("Copy failed: " + err, false);
    }
  }

  function installPanel() {
    if (byId("msbt-delivery-panel")) return;
    var panel = document.createElement("div");
    panel.id = "msbt-delivery-panel";
    panel.style.cssText = [
      "position:fixed",
      "right:14px",
      "bottom:14px",
      "z-index:2147483647",
      "width:360px",
      "max-width:calc(100vw - 28px)",
      "background:#090d17",
      "border:1px solid #00d4ff",
      "box-shadow:0 0 18px rgba(0,0,0,.45)",
      "padding:10px",
      "font-family:Segoe UI,Arial,sans-serif",
      "color:#d7def5"
    ].join(";");

    var title = document.createElement("div");
    title.textContent = "MSBT Delivery";
    title.style.cssText = "color:#00d4ff;font-weight:800;font-size:12px;margin-bottom:6px;";
    panel.appendChild(title);

    var hint = document.createElement("div");
    hint.textContent = "MSBT sends only the final @U item serial. Item building stays local in the editor. Pick a target here before sending to Selected Player.";
    hint.style.cssText = "color:#9fb3d9;font-size:11px;margin-bottom:8px;line-height:1.35;";
    panel.appendChild(hint);

    var targetBox = document.createElement("div");
    targetBox.style.cssText = "border:1px solid #334155;background:#0d1422;padding:7px;margin-bottom:8px;";
    var targetTitle = document.createElement("div");
    targetTitle.textContent = "Target";
    targetTitle.style.cssText = "color:#43d17a;font-weight:800;font-size:11px;margin-bottom:5px;";
    targetBox.appendChild(targetTitle);
    var bridgeState = document.createElement("div");
    bridgeState.id = "msbt-bridge-state";
    bridgeState.textContent = "Bridge: unknown";
    bridgeState.style.cssText = "font-size:10px;color:#ffcc33;margin-bottom:5px;";
    targetBox.appendChild(bridgeState);
    var targetRow = document.createElement("div");
    targetRow.style.cssText = "display:grid;grid-template-columns:1fr auto;gap:6px;margin-bottom:5px;";
    var targetSelect = document.createElement("select");
    targetSelect.id = "msbt-target-select";
    targetSelect.style.cssText = "width:100%;background:#211b1f;color:#f1f5ff;border:1px solid #334155;padding:5px;font-size:11px;";
    targetSelect.addEventListener("change", function () {
      setTarget(targetSelect.value);
    });
    targetRow.appendChild(targetSelect);
    var refreshTargetsBtn = document.createElement("button");
    refreshTargetsBtn.type = "button";
    refreshTargetsBtn.textContent = "Refresh";
    refreshTargetsBtn.style.cssText = "padding:6px 9px;border:none;background:#172033;color:#00d4ff;font-weight:700;font-size:11px;cursor:pointer;";
    refreshTargetsBtn.addEventListener("click", bridgeStatus);
    targetRow.appendChild(refreshTargetsBtn);
    targetBox.appendChild(targetRow);
    var targetDisplay = document.createElement("div");
    targetDisplay.id = "msbt-target-display";
    targetDisplay.textContent = "Selected target: No target selected";
    targetDisplay.style.cssText = "font-size:10px;color:#ffcc33;line-height:1.3;";
    targetBox.appendChild(targetDisplay);
    var targetHint = document.createElement("div");
    targetHint.textContent = "Send to Selected Player uses the target selected here. All and Non-Host do not require a selected target.";
    targetHint.style.cssText = "font-size:10px;color:#9fb3d9;line-height:1.3;margin-top:4px;";
    targetBox.appendChild(targetHint);
    panel.appendChild(targetBox);

    var refreshRow = document.createElement("div");
    refreshRow.style.cssText = "display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:6px;";
    var refreshBtn = document.createElement("button");
    refreshBtn.type = "button";
    refreshBtn.textContent = "Refresh Detected Serial";
    refreshBtn.style.cssText = "padding:7px 9px;border:none;background:#172033;color:#00d4ff;font-weight:700;font-size:11px;cursor:pointer;";
    refreshBtn.addEventListener("click", refreshDetectedSerials);
    refreshRow.appendChild(refreshBtn);
    var confirmBtn = document.createElement("button");
    confirmBtn.type = "button";
    confirmBtn.textContent = "Confirm Serial to Send";
    confirmBtn.style.cssText = "padding:7px 9px;border:none;background:#172033;color:#43d17a;font-weight:700;font-size:11px;cursor:pointer;";
    confirmBtn.addEventListener("click", confirmPendingSerial);
    refreshRow.appendChild(confirmBtn);
    var copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.textContent = "Copy Serial";
    copyBtn.style.cssText = "padding:7px 9px;border:none;background:#172033;color:#b36bff;font-weight:700;font-size:11px;cursor:pointer;";
    copyBtn.addEventListener("click", copyConfirmedSerial);
    refreshRow.appendChild(copyBtn);
    panel.appendChild(refreshRow);

    var count = document.createElement("div");
    count.id = "msbt-serial-count";
    count.textContent = "0 detected serials";
    count.style.cssText = "color:#9fb3d9;font-size:10px;margin-bottom:4px;";
    panel.appendChild(count);

    var selectWrap = document.createElement("div");
    selectWrap.id = "msbt-serial-select-wrap";
    selectWrap.style.cssText = "display:none;margin-bottom:6px;";
    var select = document.createElement("select");
    select.id = "msbt-serial-select";
    select.style.cssText = "width:100%;background:#211b1f;color:#f1f5ff;border:1px solid #334155;padding:5px;font-size:11px;";
    select.addEventListener("change", function () {
      var idx = parseInt(select.value, 10);
      if (Number.isNaN(idx) || !state.detected[idx]) {
        state.pendingSerial = "";
        state.confirmedSerial = "";
        refreshPreview("Multiple @U serials detected. Choose the serial to send.", false);
        return;
      }
      state.pendingSerial = state.detected[idx].serial;
      state.confirmedSerial = "";
      state.stale = false;
      refreshPreview("Selected serial. Click Confirm Serial to Send before delivery.", false);
    });
    selectWrap.appendChild(select);
    panel.appendChild(selectWrap);

    var preview = document.createElement("pre");
    preview.id = "msbt-serial-preview";
    preview.textContent = "No serial detected yet";
    preview.style.cssText = [
      "white-space:pre-wrap",
      "word-break:break-all",
      "max-height:90px",
      "overflow:auto",
      "background:#181417",
      "border:1px solid #334155",
      "padding:7px",
      "margin:0 0 8px 0",
      "font-size:10px",
      "line-height:1.35",
      "color:#ffcc33"
    ].join(";");
    panel.appendChild(preview);

    var row = document.createElement("div");
    row.style.cssText = "display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:6px;";
    row.appendChild(button("Send to Selected Player", "selected", "#b36bff"));
    row.appendChild(button("Send to All Players", "all", "#ffcc33"));
    row.appendChild(button("Send to Non-Host Players", "nonhost", "#00d4ff"));
    panel.appendChild(row);

    var statusRow = document.createElement("div");
    statusRow.style.cssText = "display:grid;grid-template-columns:1fr auto;gap:6px;align-items:center;";
    var status = document.createElement("div");
    status.id = "msbt-delivery-status";
    status.textContent = "Build an item, then send it through MSBT.";
    status.style.cssText = "font-size:11px;color:#43d17a;line-height:1.35;min-height:28px;";
    statusRow.appendChild(status);
    var statusBtn = document.createElement("button");
    statusBtn.type = "button";
    statusBtn.textContent = "Status";
    statusBtn.style.cssText = "padding:6px 9px;border:none;background:#172033;color:#00d4ff;font-weight:700;font-size:11px;cursor:pointer;";
    statusBtn.addEventListener("click", bridgeStatus);
    statusRow.appendChild(statusBtn);
    panel.appendChild(statusRow);

    document.body.appendChild(panel);
    renderTargetSection();
    refreshPreview("", false);
    window.setTimeout(bridgeStatus, 200);
    window.setTimeout(refreshDetectedSerials, 600);
    document.addEventListener("input", markPreviewStale, true);
    document.addEventListener("change", markPreviewStale, true);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", installPanel);
  } else {
    installPanel();
  }
})();
