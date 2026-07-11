const BASE85_RE = /@U[0-9A-Za-z!#$%&()*+\-;<=>?@^_`{\/}~]+/g;

const els = {
  statusOutput: document.getElementById("statusOutput"),
  deliveryOutput: document.getElementById("deliveryOutput"),
  updateOutput: document.getElementById("updateOutput"),
  serialInput: document.getElementById("serialInput"),
  editorFrame: document.getElementById("editorFrame"),
  bridgeSummary: document.getElementById("bridgeSummary"),
  targetSummary: document.getElementById("targetSummary"),
  serialSummary: document.getElementById("serialSummary"),
  updateSummary: document.getElementById("updateSummary"),
  targetSelect: document.getElementById("targetSelect")
};

const state = {
  bridgeOnline: false,
  players: [],
  selectedTarget: "",
  confirmedSerial: "",
  latestDownloadUrl: "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/MSBT_External_Beta.zip"
};

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function setOutput(node, value) {
  node.textContent = typeof value === "string" ? value : pretty(value);
}

function setLine(node, text, kind = "") {
  node.textContent = text;
  node.classList.remove("ok", "warning", "bad");
  if (kind) node.classList.add(kind);
}

function bridgeAction(action, payload = {}, timeoutMs = 15000) {
  return window.msbt.bridgeRequest({
    method: "POST",
    path: "/action",
    payload: { action, payload },
    timeoutMs
  });
}

function playerValue(player) {
  const index = player && player.index;
  const name = player && player.name ? String(player.name) : "";
  if (index === null || index === undefined || index === "") return name;
  return String(index);
}

function playerLabel(player) {
  const index = player && player.index;
  const name = player && player.name ? String(player.name) : "";
  if (index === null || index === undefined || index === "") return name || "Unknown player";
  return `${index} | ${name || "Unknown player"}`;
}

function selectedTargetFromStatus(status) {
  const index = status && status.selected_player_index;
  if (index !== null && index !== undefined && index !== "") return String(index);
  const name = status && status.selected_player ? String(status.selected_player) : "";
  return name;
}

function renderPlayers(status = {}) {
  state.players = Array.isArray(status.players) ? status.players : [];
  const selected = selectedTargetFromStatus(status);
  if (selected) state.selectedTarget = selected;

  els.targetSelect.innerHTML = "";
  const blank = document.createElement("option");
  blank.value = "";
  blank.textContent = state.players.length ? "Choose player" : "No players loaded";
  els.targetSelect.appendChild(blank);

  state.players.forEach((player) => {
    const option = document.createElement("option");
    option.value = playerValue(player);
    option.textContent = playerLabel(player);
    if (String(option.value) === String(state.selectedTarget)) option.selected = true;
    els.targetSelect.appendChild(option);
  });

  const selectedLabel = state.players.find((player) => String(playerValue(player)) === String(state.selectedTarget));
  setLine(
    els.targetSummary,
    `Selected target: ${selectedLabel ? playerLabel(selectedLabel) : state.selectedTarget || "none"}`,
    state.selectedTarget ? "ok" : "warning"
  );
}

function serialValidationMessage(serial) {
  const text = String(serial || "").trim();
  if (!text) return "No @U serial is confirmed.";
  if (text.includes("\n") || text.includes("\r")) return "Use exactly one serial, not multiple lines.";
  const matches = text.match(BASE85_RE) || [];
  if (matches.length !== 1 || matches[0] !== text) return "Serial must be exactly one @U Base85 value.";
  if (!text.startsWith("@U")) return "Serial must start with @U.";
  return "";
}

function updateSerialState(message = "", options = {}) {
  const serial = els.serialInput.value.trim();
  const validation = serialValidationMessage(serial);
  const shouldConfirm = Boolean(options.confirm);
  if (validation) {
    state.confirmedSerial = "";
  } else if (shouldConfirm) {
    state.confirmedSerial = serial;
  } else if (state.confirmedSerial && state.confirmedSerial !== serial) {
    state.confirmedSerial = "";
  }
  const ready = !validation && state.confirmedSerial === serial;
  const text = message || (validation ? validation : ready ? "Serial confirmed and ready." : "Serial staged. Click Confirm Serial before delivery.");
  setLine(els.serialSummary, text, validation ? "warning" : ready ? "ok" : "warning");
  document.querySelectorAll("[data-mode]").forEach((button) => {
    const mode = button.dataset.mode;
    const modeReady = ready && (mode !== "selected" || Boolean(state.selectedTarget));
    button.disabled = !modeReady;
  });
}

async function bridgeStatus() {
  setLine(els.bridgeSummary, "Checking bridge...", "warning");
  const result = await window.msbt.bridgeRequest({ method: "GET", path: "/status" });
  setOutput(els.statusOutput, result);

  const data = result && result.data ? result.data : {};
  if (!result.ok || !data.ok) {
    state.bridgeOnline = false;
    state.players = [];
    state.selectedTarget = "";
    renderPlayers({});
    setLine(els.bridgeSummary, data.message || "Bridge offline.", "bad");
    updateSerialState();
    return result;
  }

  state.bridgeOnline = true;
  renderPlayers(data);
  const playerCount = Array.isArray(data.players) ? data.players.length : 0;
  const selected = data.selected_player || "none";
  setLine(els.bridgeSummary, `Bridge online | players: ${playerCount} | selected: ${selected}`, "ok");
  updateSerialState();
  return result;
}

async function setTarget(value) {
  const target = String(value || "").trim();
  if (!target) {
    setLine(els.targetSummary, "Selected target: none", "warning");
    updateSerialState();
    return;
  }

  setLine(els.targetSummary, `Setting target ${target}...`, "warning");
  const result = await bridgeAction("set_target_player", { target_player: target }, 10000);
  setOutput(els.statusOutput, result);
  const ok = Boolean(result && result.data && result.data.ok);
  if (ok) {
    state.selectedTarget = target;
    await bridgeStatus();
  } else {
    setLine(els.targetSummary, result.data && result.data.message ? result.data.message : "Target update failed.", "bad");
    updateSerialState();
  }
}

function firstPlayerTarget() {
  if (!state.players.length) {
    setLine(els.targetSummary, "Refresh status first; no players are loaded.", "warning");
    return;
  }
  const first = playerValue(state.players[0]);
  els.targetSelect.value = first;
  setTarget(first);
}

async function sendSerial(mode) {
  updateSerialState();
  const serial = state.confirmedSerial;
  if (!serial) {
    setOutput(els.deliveryOutput, "Confirm one @U serial before sending.");
    return;
  }
  if (mode === "selected" && !state.selectedTarget) {
    setOutput(els.deliveryOutput, "Set a target player before Give Selected.");
    return;
  }

  const actionByMode = {
    selected: "give_serial_selected",
    all: "give_serial_all",
    nonhost: "give_serial_nonhost"
  };
  const action = actionByMode[mode];
  setOutput(els.deliveryOutput, `Sending ${action}...`);
  const result = await bridgeAction(action, {
    serial_text: serial,
    serial_override_level: false,
    serial_level: 60
  }, 30000);
  setOutput(els.deliveryOutput, result);
  await bridgeStatus();
}

function serialsFromText(text) {
  const matches = String(text || "").match(BASE85_RE) || [];
  return Array.from(new Set(matches.map((item) => item.trim()).filter(Boolean)));
}

function detectSerialFromEditor() {
  let doc;
  try {
    doc = els.editorFrame.contentDocument || (els.editorFrame.contentWindow && els.editorFrame.contentWindow.document);
  } catch (error) {
    setLine(els.serialSummary, `Could not read the editor frame: ${error.message || error}`, "bad");
    return;
  }
  if (!doc) {
    setLine(els.serialSummary, "Load the Matt editor before detecting a serial.", "warning");
    return;
  }

  const ids = ["finalOutputBase85", "mi_finalOutputBase85", "serializedOutput", "bulkSerialOutput"];
  const chunks = ids.map((id) => {
    const element = doc.getElementById(id);
    if (!element) return "";
    return element.value || element.textContent || "";
  });
  chunks.push(doc.body ? doc.body.innerText || "" : "");

  const found = serialsFromText(chunks.join("\n"));
  if (!found.length) {
    setLine(els.serialSummary, "No @U serial found in the editor yet. Build or serialize an item first.", "warning");
    return;
  }
  if (found.length > 1) {
    setLine(els.serialSummary, `Found ${found.length} serials. Using the first one; paste another manually if needed.`, "warning");
  } else {
    setLine(els.serialSummary, "Detected one serial from the editor. Click Confirm Serial.", "ok");
  }
  els.serialInput.value = found[0];
  updateSerialState(found.length > 1 ? "Detected multiple serials; first one is staged." : "Detected serial is staged.");
}

function confirmSerial() {
  updateSerialState("", { confirm: true });
}

async function copyConfirmedSerial() {
  updateSerialState();
  if (!state.confirmedSerial) return;
  await navigator.clipboard.writeText(state.confirmedSerial);
  setLine(els.serialSummary, "Confirmed serial copied.", "ok");
}

async function loadEditor() {
  const url = await window.msbt.mattEditorUrl();
  els.editorFrame.src = url;
}

async function checkUpdates() {
  setLine(els.updateSummary, "Checking GitHub Releases...", "warning");
  const result = await window.msbt.checkUpdates();
  setOutput(els.updateOutput, result);
  state.latestDownloadUrl = result.latestUrl || state.latestDownloadUrl;
  if (!result.ok) {
    setLine(els.updateSummary, result.message || "Update check failed.", "bad");
    return;
  }
  const localVersion = result.local && result.local.package_version ? result.local.package_version : "unknown";
  const remoteVersion = result.remote && result.remote.package_version ? result.remote.package_version : "unknown";
  if (result.updateAvailable) {
    setLine(els.updateSummary, `Update available: ${localVersion} -> ${remoteVersion}`, "warning");
  } else {
    setLine(els.updateSummary, `Current version looks up to date: ${localVersion}`, "ok");
  }
}

document.getElementById("statusBtn").addEventListener("click", bridgeStatus);
document.getElementById("setTargetBtn").addEventListener("click", () => setTarget(els.targetSelect.value));
document.getElementById("firstTargetBtn").addEventListener("click", firstPlayerTarget);
document.getElementById("updateBtn").addEventListener("click", checkUpdates);
document.getElementById("downloadBtn").addEventListener("click", () => window.msbt.openExternal(state.latestDownloadUrl));
document.getElementById("repoBtn").addEventListener("click", () => {
  window.msbt.openExternal("https://github.com/funkyoushift/MattsSDKBoostingTools");
});
document.getElementById("loadEditorBtn").addEventListener("click", loadEditor);
document.getElementById("reloadEditorBtn").addEventListener("click", () => {
  if (els.editorFrame.src) els.editorFrame.src = els.editorFrame.src;
});
document.getElementById("detectSerialBtn").addEventListener("click", detectSerialFromEditor);
document.getElementById("confirmSerialBtn").addEventListener("click", confirmSerial);
document.getElementById("copySerialBtn").addEventListener("click", copyConfirmedSerial);
els.serialInput.addEventListener("input", () => {
  state.confirmedSerial = "";
  updateSerialState("Serial edited. Click Confirm Serial before sending.");
});
document.querySelectorAll("[data-mode]").forEach((button) => {
  button.addEventListener("click", () => sendSerial(button.dataset.mode));
});

bridgeStatus();
checkUpdates();
