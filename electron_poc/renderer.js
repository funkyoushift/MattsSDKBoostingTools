const BASE85_RE = /@U[0-9A-Za-z!#$%&()*+\-;<=>?@^_`{\/}~]+/g;

const els = {
  activityOutput: document.getElementById("activityOutput"),
  autoInventorySizes: document.getElementById("autoInventorySizes"),
  bankSize: document.getElementById("bankSize"),
  backpackSize: document.getElementById("backpackSize"),
  boostOutput: document.getElementById("boostOutput"),
  boostSerialLevel: document.getElementById("boostSerialLevel"),
  boostSerialOverride: document.getElementById("boostSerialOverride"),
  boostSerialText: document.getElementById("boostSerialText"),
  bridgeSummary: document.getElementById("bridgeSummary"),
  currencyAmount: document.getElementById("currencyAmount"),
  currencyKind: document.getElementById("currencyKind"),
  deliveryOutput: document.getElementById("deliveryOutput"),
  devActorCategoryButtons: document.getElementById("devActorCategoryButtons"),
  devActorClass: document.getElementById("devActorClass"),
  devActorCount: document.getElementById("devActorCount"),
  devActorDetails: document.getElementById("devActorDetails"),
  devActorDistance: document.getElementById("devActorDistance"),
  devActorIncludeNonGenerated: document.getElementById("devActorIncludeNonGenerated"),
  devActorName: document.getElementById("devActorName"),
  devActorRows: document.getElementById("devActorRows"),
  devActorScale: document.getElementById("devActorScale"),
  devActorSearch: document.getElementById("devActorSearch"),
  devActorSpacing: document.getElementById("devActorSpacing"),
  devActorSummary: document.getElementById("devActorSummary"),
  devActorTargetLimit: document.getElementById("devActorTargetLimit"),
  devActorZOffset: document.getElementById("devActorZOffset"),
  devAiClass: document.getElementById("devAiClass"),
  devAiCount: document.getElementById("devAiCount"),
  devAiDirectOnly: document.getElementById("devAiDirectOnly"),
  devAiIndex: document.getElementById("devAiIndex"),
  devAiLimit: document.getElementById("devAiLimit"),
  devAiLoad: document.getElementById("devAiLoad"),
  devAiName: document.getElementById("devAiName"),
  devMyFavoriteAddBtn: document.getElementById("devMyFavoriteAddBtn"),
  devMyFavoriteRemoveBtn: document.getElementById("devMyFavoriteRemoveBtn"),
  devMyFavoriteRows: document.getElementById("devMyFavoriteRows"),
  devMyFavoriteSummary: document.getElementById("devMyFavoriteSummary"),
  devNextActorPageBtn: document.getElementById("devNextActorPageBtn"),
  devPrevActorPageBtn: document.getElementById("devPrevActorPageBtn"),
  devQuickPickRows: document.getElementById("devQuickPickRows"),
  devQuickPickSummary: document.getElementById("devQuickPickSummary"),
  devRefreshLogBtn: document.getElementById("devRefreshLogBtn"),
  devSpawnerOutput: document.getElementById("devSpawnerOutput"),
  devSpawnerWarning: document.getElementById("devSpawnerWarning"),
  editorFrame: document.getElementById("editorFrame"),
  itempoolCategory: document.getElementById("itempoolCategory"),
  itempoolCount: document.getElementById("itempoolCount"),
  itempoolLevel: document.getElementById("itempoolLevel"),
  itempoolList: document.getElementById("itempoolList"),
  itempoolOutput: document.getElementById("itempoolOutput"),
  itempoolSearch: document.getElementById("itempoolSearch"),
  itempoolSummary: document.getElementById("itempoolSummary"),
  inventoryStatus: document.getElementById("inventoryStatus"),
  copyBreakdownBtn: document.getElementById("copyBreakdownBtn"),
  copyDeserializedBtn: document.getElementById("copyDeserializedBtn"),
  copySerializedBtn: document.getElementById("copySerializedBtn"),
  serialInput: document.getElementById("serialInput"),
  serialSummary: document.getElementById("serialSummary"),
  serialToolsBreakdown: document.getElementById("serialToolsBreakdown"),
  serialToolsConvertBtn: document.getElementById("serialToolsConvertBtn"),
  serialToolsClearBtn: document.getElementById("serialToolsClearBtn"),
  serialToolsDeserialized: document.getElementById("serialToolsDeserialized"),
  serialToolsInput: document.getElementById("serialToolsInput"),
  serialToolsSerialized: document.getElementById("serialToolsSerialized"),
  serialToolsStatus: document.getElementById("serialToolsStatus"),
  statusOutput: document.getElementById("statusOutput"),
  targetSelect: document.getElementById("targetSelect"),
  targetSummary: document.getElementById("targetSummary"),
  travelMapBtn: document.getElementById("travelMapBtn"),
  travelMapList: document.getElementById("travelMapList"),
  travelMapSearch: document.getElementById("travelMapSearch"),
  travelMapSummary: document.getElementById("travelMapSummary"),
  travelOutput: document.getElementById("travelOutput"),
  travelShowAllStations: document.getElementById("travelShowAllStations"),
  travelStationBtn: document.getElementById("travelStationBtn"),
  travelStationList: document.getElementById("travelStationList"),
  travelStationSearch: document.getElementById("travelStationSearch"),
  travelStationSummary: document.getElementById("travelStationSummary"),
  updateOutput: document.getElementById("updateOutput"),
  updateSummary: document.getElementById("updateSummary"),
  validatorBasicBtn: document.getElementById("validatorBasicBtn"),
  validatorBasicInput: document.getElementById("validatorBasicInput"),
  validatorBulkBtn: document.getElementById("validatorBulkBtn"),
  validatorBulkInput: document.getElementById("validatorBulkInput"),
  validatorClearBtn: document.getElementById("validatorClearBtn"),
  validatorOutput: document.getElementById("validatorOutput"),
  validatorStatus: document.getElementById("validatorStatus"),
  xpLevel: document.getElementById("xpLevel"),
  xpTrack: document.getElementById("xpTrack")
};

const state = {
  activity: [],
  autoInventoryInFlight: false,
  autoInventoryLastMessage: "",
  autoInventoryTimer: null,
  bridgeOnline: false,
  confirmedSerial: "",
  devActorPage: 0,
  devActiveCategory: "",
  devSpawnerCatalog: null,
  devSpawnerFilteredActors: [],
  devSpawnerFilteredMyFavorites: [],
  devSpawnerFilteredQuickPicks: [],
  devSpawnerMyFavorites: { version: 1, favorites: {} },
  devSpawnerSelectedActor: "",
  devSpawnerWarningAccepted: false,
  filteredItemPools: [],
  filteredMaps: [],
  filteredStations: [],
  itemPools: [],
  latestDownloadUrl: "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/MSBT_External_Beta.zip",
  players: [],
  selectedItemPool: "",
  selectedMap: "",
  selectedStation: "",
  selectedTarget: "",
  travelMaps: [],
  travelStations: []
};

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function setOutput(node, value) {
  if (!node) return;
  node.textContent = typeof value === "string" ? value : pretty(value);
}

function setTextValue(node, value) {
  if (!node) return;
  node.value = typeof value === "string" ? value : pretty(value);
}

function setLine(node, text, kind = "") {
  if (!node) return;
  node.textContent = text;
  node.classList.remove("ok", "warning", "bad");
  if (kind) node.classList.add(kind);
}

function appendActivity(message) {
  const stamp = new Date().toLocaleTimeString();
  state.activity.push(`[${stamp}] ${message}`);
  if (state.activity.length > 250) state.activity.shift();
  setOutput(els.activityOutput, state.activity.join("\n"));
}

async function copyText(value, statusNode, label) {
  const text = String(value || "");
  if (!text.trim()) {
    setLine(statusNode, `${label} is empty.`, "warning");
    return;
  }
  await navigator.clipboard.writeText(text);
  setLine(statusNode, `${label} copied.`, "ok");
}

function resultMessage(result) {
  const data = result && result.data ? result.data : result;
  if (data && typeof data.message === "string" && data.message.trim()) return data.message;
  if (result && typeof result.message === "string" && result.message.trim()) return result.message;
  return pretty(result);
}

function actionSucceeded(result) {
  const data = result && result.data ? result.data : result;
  if (data && data.ok === false) return false;
  if (data && data.ok === true) return true;
  return Boolean(result && result.ok);
}

function bridgeAction(action, payload = {}, timeoutMs = 15000) {
  return window.msbt.bridgeRequest({
    method: "POST",
    path: "/action",
    payload: { action, payload, timeout: Math.max(1, Math.ceil(timeoutMs / 1000)) },
    timeoutMs
  });
}

async function runAction(action, payload = {}, outNode = els.boostOutput, timeoutMs = 30000) {
  appendActivity(`Sending ${action}...`);
  setOutput(outNode, `Sending ${action}...`);
  const result = await bridgeAction(action, payload, timeoutMs);
  setOutput(outNode, result);
  appendActivity(`${action}: ${resultMessage(result)}`);
  return result;
}

function getValue(nodeOrId) {
  const node = typeof nodeOrId === "string" ? document.getElementById(nodeOrId) : nodeOrId;
  return node && typeof node.value === "string" ? node.value.trim() : "";
}

function getInt(nodeOrId, minValue, maxValue, fallback) {
  const parsed = parseInt(getValue(nodeOrId), 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(minValue, Math.min(maxValue, parsed));
}

function getFloat(nodeOrId, minValue, maxValue, fallback) {
  const parsed = parseFloat(getValue(nodeOrId));
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(minValue, Math.min(maxValue, parsed));
}

function boolFromSelect(node) {
  return String(getValue(node)).toLowerCase() === "true";
}

function inventoryPayload(enabled = true) {
  return {
    enabled: Boolean(enabled),
    backpack_size: getInt(els.backpackSize, 1, 999999, 999),
    bank_size: getInt(els.bankSize, 1, 999999, 1500)
  };
}

function setInventoryStatus(message, kind = "warning") {
  setLine(els.inventoryStatus, message, kind);
}

function scheduleAutoInventory(delayMs = 2000) {
  if (!els.autoInventorySizes || !els.autoInventorySizes.checked) return;
  if (state.autoInventoryTimer) window.clearTimeout(state.autoInventoryTimer);
  state.autoInventoryTimer = window.setTimeout(autoInventoryTick, delayMs);
}

function cancelAutoInventory() {
  if (state.autoInventoryTimer) window.clearTimeout(state.autoInventoryTimer);
  state.autoInventoryTimer = null;
  state.autoInventoryInFlight = false;
}

async function autoInventoryTick() {
  state.autoInventoryTimer = null;
  if (!els.autoInventorySizes || !els.autoInventorySizes.checked) return;
  if (state.autoInventoryInFlight) {
    scheduleAutoInventory();
    return;
  }
  state.autoInventoryInFlight = true;
  try {
    const result = await bridgeAction("auto_inventory_sizes", inventoryPayload(true), 12000);
    const data = result && result.data ? result.data : result;
    const applied = Number(data && data.applied ? data.applied : 0);
    const message = resultMessage(result);
    setInventoryStatus(message || "Automatic inventory sizing checked.", applied > 0 ? "ok" : "warning");
    if (applied > 0 || message !== state.autoInventoryLastMessage) {
      appendActivity(`auto_inventory_sizes: ${message}`);
      state.autoInventoryLastMessage = message;
    }
  } catch (error) {
    const message = `Bridge offline / waiting for players for automatic inventory sizing.`;
    setInventoryStatus(message, "warning");
    if (message !== state.autoInventoryLastMessage) {
      appendActivity(message);
      state.autoInventoryLastMessage = message;
    }
  } finally {
    state.autoInventoryInFlight = false;
    scheduleAutoInventory();
  }
}

async function toggleAutoInventory() {
  if (!els.autoInventorySizes) return;
  if (els.autoInventorySizes.checked) {
    state.autoInventoryLastMessage = "";
    setInventoryStatus("Auto inventory enabled.", "ok");
    appendActivity("Auto inventory enabled.");
    scheduleAutoInventory(250);
    return;
  }

  cancelAutoInventory();
  setInventoryStatus("Auto inventory disabled.", "warning");
  appendActivity("Auto inventory disabled.");
  try {
    await bridgeAction("auto_inventory_sizes", inventoryPayload(false), 8000);
  } catch (_error) {
    // Disabling is best-effort; the app-side timer is already stopped.
  }
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

  if (!els.targetSelect) return;
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

  const selectedPlayer = state.players.find((player) => String(playerValue(player)) === String(state.selectedTarget));
  setLine(
    els.targetSummary,
    `Selected target: ${selectedPlayer ? playerLabel(selectedPlayer) : state.selectedTarget || "none"}`,
    state.selectedTarget ? "ok" : "warning"
  );
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
    appendActivity(data.message || "Bridge offline.");
    return result;
  }

  state.bridgeOnline = true;
  renderPlayers(data);
  const playerCount = Array.isArray(data.players) ? data.players.length : 0;
  const selected = data.selected_player || "none";
  const queue = data.queue || 0;
  setLine(els.bridgeSummary, `Bridge online | players: ${playerCount} | selected: ${selected} | queue: ${queue}`, "ok");
  updateSerialState();
  appendActivity(`Bridge online | players: ${playerCount} | selected: ${selected} | queue: ${queue}`);
  return result;
}

async function setTarget(value) {
  const target = String(value || "").trim();
  if (!target) {
    state.selectedTarget = "";
    setLine(els.targetSummary, "Selected target: none", "warning");
    updateSerialState();
    return null;
  }

  setLine(els.targetSummary, `Setting target ${target}...`, "warning");
  const result = await bridgeAction("set_target_player", { target_player: target }, 10000);
  setOutput(els.statusOutput, result);
  const ok = Boolean(result && result.data && result.data.ok);
  if (ok) {
    state.selectedTarget = target;
    await bridgeStatus();
  } else {
    setLine(els.targetSummary, resultMessage(result) || "Target update failed.", "bad");
    updateSerialState();
  }
  return result;
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

async function ensureSelectedTarget(outNode) {
  if (!state.selectedTarget) {
    setOutput(outNode, "Set a target player before sending to selected.");
    setLine(els.targetSummary, "Select a target player first.", "warning");
    return false;
  }
  const result = await setTarget(state.selectedTarget);
  return Boolean(result && result.data && result.data.ok);
}

function serialsFromText(text) {
  const matches = String(text || "").match(BASE85_RE) || [];
  return Array.from(new Set(matches.map((item) => item.trim()).filter(Boolean)));
}

function collectEditorSerials() {
  let doc;
  try {
    doc = els.editorFrame.contentDocument || (els.editorFrame.contentWindow && els.editorFrame.contentWindow.document);
  } catch (error) {
    setLine(els.serialSummary, `Could not read the editor frame: ${error.message || error}`, "bad");
    return [];
  }
  if (!doc) return [];

  const ids = ["finalOutputBase85", "mi_finalOutputBase85", "serializedOutput", "bulkSerialOutput"];
  const chunks = ids.map((id) => {
    const element = doc.getElementById(id);
    if (!element) return "";
    return element.value || element.textContent || "";
  });
  chunks.push(doc.body ? doc.body.innerText || "" : "");
  return serialsFromText(chunks.join("\n"));
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
  const serial = getValue(els.serialInput);
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
  const text = message || (validation ? validation : ready ? "Serial confirmed and ready." : "Serial staged. Send can auto-confirm one serial.");
  setLine(els.serialSummary, text, validation ? "warning" : ready ? "ok" : "warning");
  document.querySelectorAll("[data-editor-serial-mode]").forEach((button) => {
    const mode = button.dataset.editorSerialMode;
    const modeReady = mode !== "selected" || Boolean(state.selectedTarget);
    button.disabled = !modeReady;
  });
}

function detectSerialFromEditor() {
  const found = collectEditorSerials();
  if (!found.length && !els.editorFrame.contentWindow) {
    setLine(els.serialSummary, "Load the Matt editor before detecting a serial.", "warning");
    return;
  }
  if (!found.length) {
    setLine(els.serialSummary, "No @U serial found in the editor yet. Build or serialize an item first.", "warning");
    return;
  }
  els.serialInput.value = found[0];
  state.confirmedSerial = "";
  updateSerialState(found.length > 1 ? `Detected ${found.length} serials; first one is staged.` : "Detected one serial from the editor.");
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
  setOutput(els.deliveryOutput, "Starting hosted Matt editor...");
  const result = await window.msbt.mattEditorUrl();
  const url = typeof result === "string" ? result : result.url;
  const hosted = typeof result === "string" ? false : Boolean(result.hosted);
  const message = typeof result === "string" ? "Loaded raw editor file." : result.message;
  els.editorFrame.src = url;
  setOutput(els.deliveryOutput, message || (hosted ? "Hosted Matt editor loaded." : "Editor loaded."));
  setLine(
    els.serialSummary,
    hosted
      ? "Hosted editor loaded. Use the MSBT Delivery panel inside the editor, or detect one serial here."
      : "Raw editor fallback loaded. Delivery adapter may be unavailable.",
    hosted ? "ok" : "warning"
  );
}

async function sendEditorSerial(mode) {
  updateSerialState();
  let serial = state.confirmedSerial;
  if (!serial) {
    const manualSerial = getValue(els.serialInput);
    if (!serialValidationMessage(manualSerial)) {
      state.confirmedSerial = manualSerial;
      serial = manualSerial;
      setLine(els.serialSummary, "Serial auto-confirmed for delivery.", "ok");
    }
  }
  if (!serial) {
    const found = collectEditorSerials();
    if (found.length === 1) {
      els.serialInput.value = found[0];
      state.confirmedSerial = found[0];
      serial = found[0];
      setLine(els.serialSummary, "Detected and confirmed one editor serial for delivery.", "ok");
    } else if (found.length > 1) {
      setOutput(els.deliveryOutput, `Found ${found.length} serials. Click Detect Serial From Editor, choose/verify the one to send, then send again.`);
      setLine(els.serialSummary, "Multiple serials detected. Pick one before sending.", "warning");
      return;
    }
  }
  if (!serial) {
    setOutput(els.deliveryOutput, "No single @U serial is ready to send. Build an item or paste one serial first.");
    return;
  }
  await sendSerialPayload(mode, serial, false, 60, els.deliveryOutput);
}

async function sendBoostSerial(mode) {
  const serialText = getValue(els.boostSerialText);
  if (!serialText) {
    setOutput(els.boostOutput, "Paste at least one serial before sending.");
    return;
  }
  await sendSerialPayload(
    mode,
    serialText,
    boolFromSelect(els.boostSerialOverride),
    getInt(els.boostSerialLevel, 1, 60, 60),
    els.boostOutput
  );
}

async function sendSerialPayload(mode, serialText, overrideLevel, level, outNode) {
  if (mode === "selected") {
    const ok = await ensureSelectedTarget(outNode);
    if (!ok) return;
  }

  const actionByMode = {
    selected: "give_serial_selected",
    all: "give_serial_all",
    nonhost: "give_serial_nonhost"
  };
  const action = actionByMode[mode];
  const result = await runAction(action, {
    serial_text: serialText,
    serial_override_level: Boolean(overrideLevel),
    serial_level: level,
    code_delivery_level: level
  }, outNode, 60000);
  await bridgeStatus();
  return result;
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

async function convertSerialTools() {
  const text = getValue(els.serialToolsInput);
  setLine(els.serialToolsStatus, "Converting locally...", "warning");
  const result = await window.msbt.serialToolsConvert(text);
  const ok = String(result && result.ok).toLowerCase() === "true" || result.ok === true;
  setTextValue(els.serialToolsDeserialized, result.deserialized || "");
  setTextValue(els.serialToolsBreakdown, result.breakdown || result.parts_breakdown || "");
  setTextValue(els.serialToolsSerialized, result.serialized || "");
  setLine(els.serialToolsStatus, result.message || (ok ? "Converted successfully." : "Conversion failed."), ok ? "ok" : "bad");
  appendActivity(ok ? "Serial converted locally." : `Serial conversion failed: ${result.message || "unknown error"}`);
}

function clearSerialTools() {
  setTextValue(els.serialToolsInput, "");
  setTextValue(els.serialToolsDeserialized, "");
  setTextValue(els.serialToolsBreakdown, "");
  setTextValue(els.serialToolsSerialized, "");
  setLine(els.serialToolsStatus, "Paste a @U serial or deserialized serial text above.", "warning");
  appendActivity("Cleared Serial Tools.");
}

async function validateBasic() {
  setLine(els.validatorStatus, "Running basic validation locally...", "warning");
  const result = await window.msbt.validatorBasic(getValue(els.validatorBasicInput));
  setTextValue(els.validatorOutput, result.output || result.message || pretty(result));
  setLine(els.validatorStatus, result.summary || result.message || "Basic validation complete.", result.ok ? "ok" : "warning");
  appendActivity(`Validator basic: ${result.summary || result.message || "complete"}`);
}

async function validateBulk() {
  setLine(els.validatorStatus, "Running bulk validation locally...", "warning");
  const result = await window.msbt.validatorBulk(getValue(els.validatorBulkInput));
  setTextValue(els.validatorOutput, result.output || result.message || pretty(result));
  setLine(els.validatorStatus, result.summary || result.message || "Bulk validation complete.", result.ok ? "ok" : "warning");
  appendActivity(`Validator bulk: ${result.summary || result.message || "complete"}`);
}

function clearValidator() {
  setTextValue(els.validatorBasicInput, "");
  setTextValue(els.validatorBulkInput, "");
  setTextValue(els.validatorOutput, "");
  setLine(els.validatorStatus, "Idle", "warning");
  appendActivity("Cleared Validator.");
}

async function loadResourceJson(name) {
  const result = await window.msbt.readResourceJson(name);
  if (!result || !result.ok) {
    throw new Error(result && result.message ? result.message : `Failed to load ${name}`);
  }
  return result.data;
}

function itemPoolLabel(item) {
  const category = item.category || "Other";
  const name = item.display_name || item.name || item.itempool || "Unknown";
  return `[${category}] ${name}`;
}

function itemPoolSearchText(item) {
  return [
    item.category,
    item.display_name,
    item.name,
    item.itempool
  ].filter(Boolean).join(" ").toLowerCase();
}

function populateItemPoolCategories() {
  const categories = Array.from(new Set(state.itemPools.map((item) => item.category || "Other"))).sort();
  els.itempoolCategory.innerHTML = "";
  ["All", ...categories].forEach((category) => {
    const option = document.createElement("option");
    option.value = category;
    option.textContent = category;
    els.itempoolCategory.appendChild(option);
  });
}

function renderItemPools() {
  const query = getValue(els.itempoolSearch).toLowerCase();
  const category = getValue(els.itempoolCategory) || "All";
  state.filteredItemPools = state.itemPools.filter((item) => {
    const categoryOk = category === "All" || (item.category || "Other") === category;
    const queryOk = !query || itemPoolSearchText(item).includes(query);
    return categoryOk && queryOk;
  });

  const previous = state.selectedItemPool;
  els.itempoolList.innerHTML = "";
  state.filteredItemPools.slice(0, 400).forEach((item) => {
    const option = document.createElement("option");
    option.value = item.itempool || "";
    option.textContent = `${itemPoolLabel(item)} | ${item.itempool || ""}`;
    if (option.value === previous) option.selected = true;
    els.itempoolList.appendChild(option);
  });
  if (!els.itempoolList.value && els.itempoolList.options.length) {
    els.itempoolList.options[0].selected = true;
    state.selectedItemPool = els.itempoolList.value;
  }
  setLine(
    els.itempoolSummary,
    `${state.filteredItemPools.length} shown / ${state.itemPools.length} saved | selected: ${state.selectedItemPool || els.itempoolList.value || "none"}`,
    state.filteredItemPools.length ? "ok" : "warning"
  );
}

async function loadItemPools() {
  try {
    const data = await loadResourceJson("item_pools.json");
    state.itemPools = Array.isArray(data) ? data : [];
    populateItemPoolCategories();
    renderItemPools();
  } catch (error) {
    setLine(els.itempoolSummary, `Item pools failed to load: ${error.message || error}`, "bad");
  }
}

async function spawnItemPool() {
  const name = state.selectedItemPool || getValue(els.itempoolList);
  if (!name) {
    setOutput(els.itempoolOutput, "Select an item pool first.");
    return;
  }
  await runAction("spawn_itempool", {
    itempool_name: name,
    itempool_level: getInt(els.itempoolLevel, 1, 60, 60),
    itempool_count: getInt(els.itempoolCount, 1, 100, 1)
  }, els.itempoolOutput, 30000);
}

function mapLabel(map) {
  return map.display_name || map.map || "Unknown map";
}

function stationLabel(station) {
  const category = station.category || "Station";
  return `[${category}] ${station.display_name || station.station_name || station.station || "Unknown station"}`;
}

function renderMaps() {
  const query = getValue(els.travelMapSearch).toLowerCase();
  state.filteredMaps = state.travelMaps.filter((map) => {
    const haystack = [map.display_name, map.map, map.map_key, map.mappath].filter(Boolean).join(" ").toLowerCase();
    return !query || haystack.includes(query);
  });

  const previous = state.selectedMap;
  els.travelMapList.innerHTML = "";
  state.filteredMaps.slice(0, 250).forEach((map) => {
    const option = document.createElement("option");
    option.value = map.map || "";
    option.textContent = mapLabel(map);
    if (option.value === previous) option.selected = true;
    els.travelMapList.appendChild(option);
  });
  if (!els.travelMapList.value && els.travelMapList.options.length) {
    els.travelMapList.options[0].selected = true;
    state.selectedMap = els.travelMapList.value;
  }
  setLine(els.travelMapSummary, `${state.filteredMaps.length} shown / ${state.travelMaps.length} maps | selected: ${state.selectedMap || "none"}`, state.filteredMaps.length ? "ok" : "warning");
  renderStations();
}

function renderStations() {
  const query = getValue(els.travelStationSearch).toLowerCase();
  const showAll = Boolean(els.travelShowAllStations && els.travelShowAllStations.checked);
  const selectedMap = state.selectedMap || getValue(els.travelMapList);
  state.filteredStations = state.travelStations.filter((station) => {
    const mapOk = showAll || !selectedMap || station.world === selectedMap;
    const haystack = [
      station.category,
      station.display_name,
      station.station,
      station.station_key,
      station.station_name,
      station.world
    ].filter(Boolean).join(" ").toLowerCase();
    return mapOk && (!query || haystack.includes(query));
  });

  const previous = state.selectedStation;
  els.travelStationList.innerHTML = "";
  state.filteredStations.slice(0, 350).forEach((station) => {
    const option = document.createElement("option");
    option.value = station.station || "";
    option.textContent = `${stationLabel(station)} | ${station.station || ""}`;
    if (option.value === previous) option.selected = true;
    els.travelStationList.appendChild(option);
  });
  if (!els.travelStationList.value && els.travelStationList.options.length) {
    els.travelStationList.options[0].selected = true;
    state.selectedStation = els.travelStationList.value;
  }
  const scope = showAll ? "all maps" : selectedMap || "selected map";
  setLine(els.travelStationSummary, `${state.filteredStations.length} shown for ${scope} | selected: ${state.selectedStation || "none"}`, state.filteredStations.length ? "ok" : "warning");
}

async function loadTravelResources() {
  try {
    const maps = await loadResourceJson("travelmaps_flat.json");
    const stations = await loadResourceJson("travelstations.json");
    state.travelMaps = Array.isArray(maps.maps) ? maps.maps : [];
    state.travelStations = Array.isArray(stations.stations) ? stations.stations : [];
    renderMaps();
  } catch (error) {
    setLine(els.travelMapSummary, `Travel resources failed to load: ${error.message || error}`, "bad");
    setLine(els.travelStationSummary, "Travel stations unavailable.", "bad");
  }
}

async function travelToSelectedMap() {
  const mapName = state.selectedMap || getValue(els.travelMapList);
  if (!mapName) {
    setOutput(els.travelOutput, "Select a map first.");
    return;
  }
  await runAction("travel_to_map", { travel_map: mapName }, els.travelOutput, 30000);
}

async function travelToSelectedStation() {
  const stationName = state.selectedStation || getValue(els.travelStationList);
  if (!stationName) {
    setOutput(els.travelOutput, "Select a travel station first.");
    return;
  }
  await runAction("travel_to_station", { travel_station: stationName }, els.travelOutput, 30000);
}

function devActorDisplayName(actorName) {
  const catalog = state.devSpawnerCatalog || {};
  const displayNames = catalog.display_names || {};
  return String(displayNames[actorName] || "").trim();
}

function devActorFavoriteLabel(actorName) {
  const catalog = state.devSpawnerCatalog || {};
  const favorites = catalog.favorites || {};
  return String(favorites[actorName] || "").trim();
}

function devMyFavoritesMap() {
  const data = state.devSpawnerMyFavorites || {};
  return data.favorites && typeof data.favorites === "object" ? data.favorites : {};
}

function devMyFavoriteEntry(actorName) {
  return devMyFavoritesMap()[actorName] || null;
}

function devActorMyFavoriteLabel(actorName) {
  const entry = devMyFavoriteEntry(actorName);
  return String((entry && entry.label) || "").trim();
}

function devIsMyFavorite(actorName) {
  return Object.prototype.hasOwnProperty.call(devMyFavoritesMap(), actorName);
}

function devMyFavoriteActors() {
  return Object.keys(devMyFavoritesMap()).sort((left, right) => {
    return devActorLabel(left).localeCompare(devActorLabel(right));
  });
}

function devActorDerivedLabel(actorName) {
  const cleaned = String(actorName || "")
    .replace(/^(TESTChar|Char|AI|IO|BP|BPChar|BPActor|InteractiveObject|NPC)_?/i, "")
    .replace(/_/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/\s+/g, " ")
    .trim();
  return cleaned || String(actorName || "").trim();
}

function devSearchTokens(text) {
  const normalized = devNormalizeSearch(text);
  return normalized ? normalized.split(/\s+/).filter((token) => token.length > 2) : [];
}

function devHasTokenOverlap(left, right) {
  const rightTokens = new Set(devSearchTokens(right));
  return devSearchTokens(left).some((token) => rightTokens.has(token));
}

function devQuickPickLabelInfo(actorName) {
  const reference = devActorFavoriteLabel(actorName);
  const mapped = devActorDisplayName(actorName);
  const derived = devActorDerivedLabel(actorName);
  const categories = devActorCategories(actorName);
  const reasons = [];

  if (!reference) {
    reasons.push("missing reference label");
  }
  if (/^\?+$/.test(reference) || /^[-_\s]+$/.test(reference)) {
    reasons.push("malformed reference label");
  }
  if (reference && devNormalizeSearch(reference) === devNormalizeSearch(actorName)) {
    reasons.push("reference label matches raw actor key");
  }
  if (reference && /^(io|char|ai|bp)[_\s]/i.test(reference)) {
    reasons.push("reference label looks like a raw actor key");
  }

  const invalidReference = reasons.some((reason) => reason.includes("missing") || reason.includes("malformed") || reason.includes("raw actor key"));
  const sourceSpecific = Boolean(reference && mapped && !devHasTokenOverlap(reference, `${mapped} ${actorName} ${derived} ${categories.join(" ")}`));
  if (sourceSpecific) {
    reasons.push("reference label differs from mapped display name");
  }

  let primary = "";
  let secondary = "";
  let source = "";

  if (!invalidReference && !sourceSpecific) {
    primary = reference;
    secondary = mapped && devNormalizeSearch(mapped) !== devNormalizeSearch(reference) ? `Mapped: ${mapped}` : "";
    source = "Reference Quick Pick label";
  } else if (mapped) {
    primary = mapped;
    secondary = reference ? `Reference: ${reference}` : "";
    source = "Mapped display name; reference label kept as metadata";
  } else if (!invalidReference && reference) {
    primary = reference;
    secondary = derived && devNormalizeSearch(derived) !== devNormalizeSearch(reference) ? `Derived: ${derived}` : "";
    source = "Reference Quick Pick label";
  } else {
    primary = derived || actorName;
    secondary = actorName;
    source = derived ? "Actor-key-derived label" : "Exact actor key";
  }

  return {
    primary,
    secondary,
    source,
    reasons,
    reference,
    mapped,
    derived
  };
}

function devMyFavoriteLabelInfo(actorName) {
  const saved = devActorMyFavoriteLabel(actorName);
  const mapped = devActorDisplayName(actorName);
  const reference = devActorFavoriteLabel(actorName);
  const derived = devActorDerivedLabel(actorName);
  const primary = saved || mapped || reference || derived || actorName;
  const secondary = mapped && devNormalizeSearch(mapped) !== devNormalizeSearch(primary)
    ? `Mapped: ${mapped}`
    : reference && devNormalizeSearch(reference) !== devNormalizeSearch(primary)
      ? `Reference: ${reference}`
      : actorName;
  return { primary, secondary };
}

function devActorCategories(actorName) {
  const catalog = state.devSpawnerCatalog || {};
  const categories = catalog.categories || {};
  return Object.keys(categories).filter((category) => {
    return category !== "All" && Array.isArray(categories[category]) && categories[category].includes(actorName);
  });
}

function devActorPrimaryCategory(actorName) {
  return devActorCategories(actorName)[0] || "Other / Uncategorized";
}

function devActorExistsInCatalog(actorName) {
  const catalog = state.devSpawnerCatalog || {};
  const categories = catalog.categories || {};
  return Array.isArray(categories.All) && categories.All.includes(actorName);
}

function devActorLabel(actorName) {
  const displayName = devActorDisplayName(actorName);
  return displayName ? `${displayName} | ${actorName}` : actorName;
}

function devNormalizeSearch(text) {
  return String(text || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function devActorSearchText(actorName) {
  return devNormalizeSearch(`${actorName} ${devActorDisplayName(actorName)} ${devActorFavoriteLabel(actorName)} ${devActorMyFavoriteLabel(actorName)} ${devActorDerivedLabel(actorName)} ${devActorCategories(actorName).join(" ")}`);
}

function devCategoryNames() {
  const catalog = state.devSpawnerCatalog || {};
  const categories = catalog.categories || {};
  return Object.keys(categories);
}

function devActorsForActiveCategory() {
  const catalog = state.devSpawnerCatalog || {};
  const categories = catalog.categories || {};
  const category = state.devActiveCategory || "All";
  return Array.isArray(categories[category]) ? categories[category] : [];
}

function devGroupedActorRows(actorNames, category) {
  const groups = [];
  const byName = new Map();

  actorNames.forEach((actorName) => {
    const groupName = category && category !== "All" ? category : devActorPrimaryCategory(actorName);
    if (!byName.has(groupName)) {
      const group = { name: groupName, actors: [] };
      byName.set(groupName, group);
      groups.push(group);
    }
    byName.get(groupName).actors.push(actorName);
  });

  return groups;
}

function devReferenceQuickPickActors() {
  const catalog = state.devSpawnerCatalog || {};
  const favorites = catalog.favorites || {};
  return Object.keys(favorites).filter((actorName) => devActorExistsInCatalog(actorName));
}

function devReferenceQuickPickGroupName(actorName) {
  if (actorName.startsWith("IO_")) return "Interactive Objects";
  if (actorName.startsWith("Char_") || actorName.startsWith("TESTChar_")) return "Characters";
  return devActorPrimaryCategory(actorName);
}

function devGroupedQuickPickRows(actorNames) {
  const groups = [];
  const byName = new Map();
  actorNames.forEach((actorName) => {
    const groupName = devReferenceQuickPickGroupName(actorName);
    if (!byName.has(groupName)) {
      const group = { name: groupName, actors: [] };
      byName.set(groupName, group);
      groups.push(group);
    }
    byName.get(groupName).actors.push(actorName);
  });
  return groups;
}

function devGroupedMyFavoriteRows(actorNames) {
  const groups = [];
  const byName = new Map();
  actorNames.forEach((actorName) => {
    const groupName = devActorPrimaryCategory(actorName);
    if (!byName.has(groupName)) {
      const group = { name: groupName, actors: [] };
      byName.set(groupName, group);
      groups.push(group);
    }
    byName.get(groupName).actors.push(actorName);
  });
  return groups;
}

function devFilteredReferenceQuickPicks(query) {
  return devReferenceQuickPickActors().filter((actorName) => {
    return !query || devActorSearchText(actorName).includes(query);
  });
}

function devFilteredMyFavorites(query) {
  return devMyFavoriteActors().filter((actorName) => {
    return !query || devActorSearchText(actorName).includes(query);
  });
}

function clearDevActorSelection() {
  state.devSpawnerSelectedActor = "";
  if (els.devActorName) els.devActorName.value = "";
  if (els.devAiName) els.devAiName.value = "";
}

function makeDevDetailRow(label, value, className = "") {
  const row = document.createElement("div");
  row.className = "dev-detail-row";

  const term = document.createElement("div");
  term.className = "dev-detail-label";
  term.textContent = label;

  const detail = document.createElement("div");
  detail.className = `dev-detail-value${className ? ` ${className}` : ""}`;
  detail.textContent = value || "Not available in catalog.";

  row.appendChild(term);
  row.appendChild(detail);
  return row;
}

function renderDevMyFavoriteControls() {
  const actorName = state.devSpawnerSelectedActor;
  const isFavorite = Boolean(actorName && devIsMyFavorite(actorName));
  if (els.devMyFavoriteAddBtn) {
    els.devMyFavoriteAddBtn.disabled = !actorName || isFavorite;
    els.devMyFavoriteAddBtn.textContent = isFavorite ? "Already In My Favorites" : "Add Selected Actor";
  }
  if (els.devMyFavoriteRemoveBtn) {
    els.devMyFavoriteRemoveBtn.disabled = !isFavorite;
  }
}

function renderDevActorDetails() {
  if (!els.devActorDetails) return;
  els.devActorDetails.innerHTML = "";
  renderDevMyFavoriteControls();

  const actorName = state.devSpawnerSelectedActor;
  if (!actorName) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "Select an actor row to view local catalog details.";
    els.devActorDetails.appendChild(empty);
    return;
  }

  const displayName = devActorDisplayName(actorName);
  const categories = devActorCategories(actorName);
  const primaryCategory = devActorPrimaryCategory(actorName);
  const alternateCategories = categories.filter((category) => category !== primaryCategory);
  const favoriteLabel = devActorFavoriteLabel(actorName);
  const myFavoriteLabel = devActorMyFavoriteLabel(actorName);
  const catalog = state.devSpawnerCatalog || {};
  const existsInCatalog = devActorExistsInCatalog(actorName);

  els.devActorDetails.appendChild(makeDevDetailRow("Display name", displayName || actorName));
  els.devActorDetails.appendChild(makeDevDetailRow("Actor key", actorName, "mono"));
  els.devActorDetails.appendChild(makeDevDetailRow("Primary category", primaryCategory));
  els.devActorDetails.appendChild(makeDevDetailRow("Alternate categories", alternateCategories.join(", ") || "None in local catalog."));
  els.devActorDetails.appendChild(makeDevDetailRow("Display source", displayName ? "Mapped display name" : "Generated from actor key fallback"));
  els.devActorDetails.appendChild(makeDevDetailRow("Runtime identifier", existsInCatalog ? "Actor key used for ASD_spawnai" : "Not present in local All catalog."));
  els.devActorDetails.appendChild(makeDevDetailRow("Catalog source", String(catalog.source || "").trim()));
  if (favoriteLabel) {
    els.devActorDetails.appendChild(makeDevDetailRow("Reference favorite label", favoriteLabel));
  }
  els.devActorDetails.appendChild(makeDevDetailRow("My Favorites", myFavoriteLabel ? `Saved as ${myFavoriteLabel}` : "Not saved in My Favorites."));

  const note = document.createElement("div");
  note.className = "dev-detail-note";
  note.textContent = "Package paths, object paths, aliases, and live-confirmed status are not present in this local catalog.";
  els.devActorDetails.appendChild(note);
}

function populateDevSpawnerCatalog() {
  const catalog = state.devSpawnerCatalog || {};
  const categories = catalog.categories || {};
  const names = Object.keys(categories);
  if (names.includes("Characters")) {
    state.devActiveCategory = "Characters";
  } else if (names.includes("All")) {
    state.devActiveCategory = "All";
  } else if (names.length) {
    state.devActiveCategory = names[0];
  }

  renderDevCategories();
  renderDevActors();
}

function renderDevCategories() {
  const catalog = state.devSpawnerCatalog || {};
  const categories = catalog.categories || {};
  if (!els.devActorCategoryButtons) return;
  els.devActorCategoryButtons.innerHTML = "";
  const names = devCategoryNames();
  if (!names.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "No actor categories loaded.";
    els.devActorCategoryButtons.appendChild(empty);
    return;
  }
  names.forEach((category) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = category === state.devActiveCategory ? "active" : "";
    button.textContent = `${category} (${(categories[category] || []).length})`;
    button.title = category === "All"
      ? "Search across every actor in the source catalog."
      : `Show ${category} actors only. Search will filter inside this category.`;
    button.addEventListener("click", () => {
      state.devActiveCategory = category;
      state.devActorPage = 0;
      renderDevCategories();
      renderDevActors();
    });
    els.devActorCategoryButtons.appendChild(button);
  });
}

function makeDevActorRow(actorName, options = {}) {
  const row = document.createElement("div");
  row.className = "dev-actor-row";
  if (options.rowClass) {
    row.classList.add(options.rowClass);
  }
  if (actorName === state.devSpawnerSelectedActor) {
    row.classList.add("selected");
  }
  const spawn = document.createElement("button");
  spawn.type = "button";
  spawn.className = "dev-spawn-button";
  spawn.textContent = "Spawn";
  spawn.addEventListener("click", () => spawnDevActor(actorName));

  const label = document.createElement("button");
  label.type = "button";
  label.className = "dev-actor-label";
  label.addEventListener("click", () => {
    useDevActor(actorName);
    renderDevActors();
  });

  const displayName = devActorDisplayName(actorName);
  const title = document.createElement("span");
  title.className = "dev-actor-title";
  title.textContent = options.titleText || displayName || actorName;

  const key = document.createElement("span");
  key.className = "dev-actor-key";
  key.textContent = actorName;

  const meta = document.createElement("span");
  meta.className = "dev-actor-meta";
  const categories = devActorCategories(actorName);
  const groupName = options.groupName || devActorPrimaryCategory(actorName);
  meta.textContent = options.metaText || `Category: ${groupName}${categories.length > 1 ? ` | Also in: ${categories.filter((name) => name !== groupName).join(", ")}` : ""}`;

  label.appendChild(title);
  label.appendChild(key);
  label.appendChild(meta);

  row.appendChild(spawn);
  row.appendChild(label);
  return row;
}

function renderDevQuickPicks(query, rawQuery) {
  if (!els.devQuickPickRows) return;

  const catalog = state.devSpawnerCatalog || {};
  const favorites = catalog.favorites || {};
  const favoriteCount = Object.keys(favorites).length;
  const availableActors = devReferenceQuickPickActors();
  const omittedCount = Math.max(0, favoriteCount - availableActors.length);
  state.devSpawnerFilteredQuickPicks = devFilteredReferenceQuickPicks(query);

  els.devQuickPickRows.innerHTML = "";
  if (!favoriteCount) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "No reference Quick Picks are packaged in the local catalog.";
    els.devQuickPickRows.appendChild(empty);
  } else if (!state.devSpawnerFilteredQuickPicks.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = query
      ? `No reference Quick Picks match "${rawQuery}". Clear Search actors to see all packaged Quick Picks.`
      : "No reference Quick Picks are available in the active local actor catalog.";
    els.devQuickPickRows.appendChild(empty);
  } else {
    devGroupedQuickPickRows(state.devSpawnerFilteredQuickPicks).forEach((group) => {
      const groupNode = document.createElement("details");
      groupNode.className = "dev-actor-group";
      groupNode.open = true;
      const summary = document.createElement("summary");
      summary.textContent = `${group.name} (${group.actors.length})`;
      groupNode.appendChild(summary);
      group.actors.forEach((actorName) => {
        const labelInfo = devQuickPickLabelInfo(actorName);
        const categories = devActorCategories(actorName);
        const primaryCategory = devActorPrimaryCategory(actorName);
        const categoryText = `Category: ${primaryCategory}${categories.length > 1 ? ` | Also in: ${categories.filter((name) => name !== primaryCategory).join(", ")}` : ""}`;
        const metaParts = [];
        if (labelInfo.secondary) metaParts.push(labelInfo.secondary);
        metaParts.push(categoryText);
        metaParts.push(labelInfo.source);
        groupNode.appendChild(makeDevActorRow(actorName, {
          groupName: group.name,
          metaText: metaParts.join(" | "),
          rowClass: "quick-pick-row",
          titleText: labelInfo.primary
        }));
      });
      els.devQuickPickRows.appendChild(groupNode);
    });
  }

  const searchNote = query ? ` | search: "${rawQuery}"` : "";
  const omittedNote = omittedCount ? ` | ${omittedCount} omitted pending catalog review` : "";
  setLine(
    els.devQuickPickSummary,
    `${state.devSpawnerFilteredQuickPicks.length} shown / ${availableActors.length} available / ${favoriteCount} reference Quick Picks${searchNote}${omittedNote}`,
    state.devSpawnerFilteredQuickPicks.length ? "ok" : "warning"
  );
}

function renderDevMyFavorites(query, rawQuery) {
  if (!els.devMyFavoriteRows) return;

  const favorites = devMyFavoritesMap();
  const favoriteCount = Object.keys(favorites).length;
  state.devSpawnerFilteredMyFavorites = devFilteredMyFavorites(query);

  els.devMyFavoriteRows.innerHTML = "";
  if (!favoriteCount) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "No My Favorites saved yet. Select an actor row, then use Add Selected Actor.";
    els.devMyFavoriteRows.appendChild(empty);
  } else if (!state.devSpawnerFilteredMyFavorites.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = query
      ? `No My Favorites match "${rawQuery}". Clear Search actors to see all saved favorites.`
      : "No My Favorites are visible.";
    els.devMyFavoriteRows.appendChild(empty);
  } else {
    devGroupedMyFavoriteRows(state.devSpawnerFilteredMyFavorites).forEach((group) => {
      const groupNode = document.createElement("details");
      groupNode.className = "dev-actor-group";
      groupNode.open = true;
      const summary = document.createElement("summary");
      summary.textContent = `${group.name} (${group.actors.length})`;
      groupNode.appendChild(summary);
      group.actors.forEach((actorName) => {
        const labelInfo = devMyFavoriteLabelInfo(actorName);
        const categories = devActorCategories(actorName);
        const primaryCategory = devActorPrimaryCategory(actorName);
        const existsText = devActorExistsInCatalog(actorName) ? "Catalog actor" : "Not present in local All catalog";
        const metaParts = [];
        if (labelInfo.secondary) metaParts.push(labelInfo.secondary);
        metaParts.push(`Category: ${primaryCategory}${categories.length > 1 ? ` | Also in: ${categories.filter((name) => name !== primaryCategory).join(", ")}` : ""}`);
        metaParts.push(existsText);
        groupNode.appendChild(makeDevActorRow(actorName, {
          groupName: group.name,
          metaText: metaParts.join(" | "),
          rowClass: "my-favorite-row",
          titleText: labelInfo.primary
        }));
      });
      els.devMyFavoriteRows.appendChild(groupNode);
    });
  }

  const searchNote = query ? ` | search: "${rawQuery}"` : "";
  const selectedNote = state.devSpawnerSelectedActor
    ? devIsMyFavorite(state.devSpawnerSelectedActor) ? " | selected actor is saved" : " | selected actor is not saved"
    : "";
  setLine(
    els.devMyFavoriteSummary,
    `${state.devSpawnerFilteredMyFavorites.length} shown / ${favoriteCount} My Favorites${searchNote}${selectedNote}`,
    favoriteCount ? "ok" : "warning"
  );
  renderDevMyFavoriteControls();
}

function renderDevActors() {
  const catalog = state.devSpawnerCatalog || {};
  const category = state.devActiveCategory || "All";
  const rawQuery = getValue(els.devActorSearch).trim();
  const query = devNormalizeSearch(rawQuery);
  const allNames = devActorsForActiveCategory();
  state.devSpawnerFilteredActors = allNames.filter((actorName) => {
    return !query || devActorSearchText(actorName).includes(query);
  });
  state.devSpawnerFilteredQuickPicks = devFilteredReferenceQuickPicks(query);
  state.devSpawnerFilteredMyFavorites = devFilteredMyFavorites(query);

  if (
    state.devSpawnerSelectedActor
    && !state.devSpawnerFilteredActors.includes(state.devSpawnerSelectedActor)
    && !state.devSpawnerFilteredQuickPicks.includes(state.devSpawnerSelectedActor)
    && !state.devSpawnerFilteredMyFavorites.includes(state.devSpawnerSelectedActor)
  ) {
    clearDevActorSelection();
  }

  renderDevQuickPicks(query, rawQuery);
  renderDevMyFavorites(query, rawQuery);

  const pageSize = 36;
  const totalPages = Math.max(1, Math.ceil(state.devSpawnerFilteredActors.length / pageSize));
  state.devActorPage = Math.max(0, Math.min(totalPages - 1, state.devActorPage || 0));
  const start = state.devActorPage * pageSize;
  const shown = state.devSpawnerFilteredActors.slice(start, start + pageSize);

  if (els.devActorRows) {
    els.devActorRows.innerHTML = "";
    devGroupedActorRows(shown, category).forEach((group) => {
      const groupNode = document.createElement("details");
      groupNode.className = "dev-actor-group";
      groupNode.open = true;
      const summary = document.createElement("summary");
      summary.textContent = `${group.name} (${group.actors.length} on this page)`;
      groupNode.appendChild(summary);
      group.actors.forEach((actorName) => {
        groupNode.appendChild(makeDevActorRow(actorName, { groupName: group.name }));
      });
      els.devActorRows.appendChild(groupNode);
    });
    if (!shown.length) {
      const empty = document.createElement("div");
      empty.className = "dev-empty-row";
      if (!allNames.length) {
        empty.textContent = "This category has no actors in the local catalog.";
      } else if (query) {
        empty.textContent = `No actors match "${rawQuery}" in ${category}. Clear Search actors, try All, or search by display name, actor key, or category.`;
      } else {
        empty.textContent = "No actors match this category. Try All or another category.";
      }
      els.devActorRows.appendChild(empty);
    }
  }

  if (els.devPrevActorPageBtn) {
    els.devPrevActorPageBtn.disabled = state.devActorPage <= 0;
  }
  if (els.devNextActorPageBtn) {
    els.devNextActorPageBtn.disabled = state.devActorPage >= totalPages - 1;
  }

  const range = shown.length ? `${start + 1}-${start + shown.length}` : "0";
  const searchNote = query ? ` | search: "${rawQuery}"` : "";
  setLine(
    els.devActorSummary,
    `${range} of ${state.devSpawnerFilteredActors.length} shown / ${allNames.length} in ${category}${searchNote} | page ${state.devActorPage + 1}/${totalPages}`,
    state.devSpawnerFilteredActors.length ? "ok" : "warning"
  );
  renderDevActorDetails();
}

async function loadDevSpawnerCatalog() {
  try {
    const result = await window.msbt.readDevSpawnerCatalog();
    if (!result || !result.ok) {
      throw new Error(result && result.message ? result.message : "Dev Spawner catalog failed to load.");
    }
    state.devSpawnerCatalog = result.data || {};
    populateDevSpawnerCatalog();
    const count = Number(state.devSpawnerCatalog.actor_count || 0);
    setLine(els.devSpawnerWarning, `Loaded SDK Debug Menu source catalog: ${count} actors.`, "ok");
  } catch (error) {
    setLine(els.devSpawnerWarning, `Dev Spawner catalog failed to load: ${error.message || error}`, "bad");
    setLine(els.devActorSummary, "Actor catalog unavailable.", "bad");
  }
}

async function loadDevSpawnerFavorites() {
  if (!window.msbt || typeof window.msbt.loadDevSpawnerFavorites !== "function") {
    state.devSpawnerMyFavorites = { version: 1, favorites: {} };
    setLine(els.devMyFavoriteSummary, "My Favorites storage is not available in this build.", "warning");
    return;
  }

  try {
    const result = await window.msbt.loadDevSpawnerFavorites();
    if (!result || !result.ok) {
      throw new Error(result && result.message ? result.message : "My Favorites failed to load.");
    }
    state.devSpawnerMyFavorites = result.data || { version: 1, favorites: {} };
    const warnings = Array.isArray(result.warnings) ? result.warnings.filter(Boolean) : [];
    renderDevMyFavorites(devNormalizeSearch(getValue(els.devActorSearch)), getValue(els.devActorSearch).trim());
    if (warnings.length) {
      setLine(els.devMyFavoriteSummary, warnings[0], "warning");
    }
  } catch (error) {
    state.devSpawnerMyFavorites = { version: 1, favorites: {} };
    setLine(els.devMyFavoriteSummary, `My Favorites failed to load: ${error.message || error}`, "bad");
  }
}

async function saveDevSpawnerFavorites(statusMessage) {
  if (!window.msbt || typeof window.msbt.saveDevSpawnerFavorites !== "function") {
    setLine(els.devMyFavoriteSummary, "My Favorites storage is not available in this build.", "warning");
    return false;
  }
  const result = await window.msbt.saveDevSpawnerFavorites(state.devSpawnerMyFavorites);
  if (!result || !result.ok) {
    setLine(els.devMyFavoriteSummary, `My Favorites failed to save: ${result && result.message ? result.message : "Unknown save error"}`, "bad");
    return false;
  }
  state.devSpawnerMyFavorites = result.data || state.devSpawnerMyFavorites;
  const warning = Array.isArray(result.warnings) && result.warnings.length ? ` ${result.warnings[0]}` : "";
  renderDevActors();
  setLine(els.devMyFavoriteSummary, `${statusMessage}${warning}`, warning ? "warning" : "ok");
  return true;
}

function devFavoriteLabelForActor(actorName) {
  return devActorDisplayName(actorName) || devActorFavoriteLabel(actorName) || devActorDerivedLabel(actorName) || actorName;
}

async function addSelectedDevMyFavorite() {
  const actorName = String(state.devSpawnerSelectedActor || getValue(els.devActorName) || "").trim();
  if (!actorName) {
    setLine(els.devMyFavoriteSummary, "Select an actor before adding it to My Favorites.", "warning");
    return;
  }
  if (devIsMyFavorite(actorName)) {
    setLine(els.devMyFavoriteSummary, `${devActorLabel(actorName)} is already in My Favorites.`, "warning");
    renderDevMyFavoriteControls();
    return;
  }
  const now = new Date().toISOString();
  state.devSpawnerMyFavorites = {
    version: 1,
    favorites: {
      ...devMyFavoritesMap(),
      [actorName]: {
        label: devFavoriteLabelForActor(actorName),
        created_at: now,
        updated_at: now
      }
    }
  };
  await saveDevSpawnerFavorites(`Added ${devFavoriteLabelForActor(actorName)} to My Favorites.`);
}

async function removeSelectedDevMyFavorite() {
  const actorName = String(state.devSpawnerSelectedActor || getValue(els.devActorName) || "").trim();
  if (!actorName || !devIsMyFavorite(actorName)) {
    setLine(els.devMyFavoriteSummary, "Select a saved favorite before removing it.", "warning");
    renderDevMyFavoriteControls();
    return;
  }
  const favorites = { ...devMyFavoritesMap() };
  const label = devFavoriteLabelForActor(actorName);
  delete favorites[actorName];
  state.devSpawnerMyFavorites = { version: 1, favorites };
  await saveDevSpawnerFavorites(`Removed ${label} from My Favorites.`);
}

function useDevActor(actorName) {
  const value = String(actorName || "").trim();
  if (!value) return;
  state.devSpawnerSelectedActor = value;
  if (els.devActorName) els.devActorName.value = value;
  if (els.devAiName) els.devAiName.value = value;
  setLine(els.devSpawnerWarning, `Selected actor: ${devActorLabel(value)}`, "ok");
  renderDevActorDetails();
  renderDevMyFavorites(devNormalizeSearch(getValue(els.devActorSearch)), getValue(els.devActorSearch).trim());
}

function selectDevActorFromList() {
  useDevActor(state.devSpawnerSelectedActor || state.devSpawnerFilteredActors[0] || "");
}

function syncDevSpawnerAdvancedControls() {
  // Retained as a no-op for older event hooks. The source menu uses row-level Spawn
  // with a single session warning instead of a separate risky-mode checkbox.
}

function spawnDevActor(actorName) {
  useDevActor(actorName);
  runDevSpawnerAction("dev_spawner_spawnai");
}

function devSpawnerConfirm() {
  if (state.devSpawnerWarningAccepted) return true;
  const accepted = window.confirm(
    "Experimental Dev Spawner tools can crash the game, corrupt saves, or affect other players in your lobby.\n\nOnly continue if you understand the risk."
  );
  if (accepted) {
    state.devSpawnerWarningAccepted = true;
    setLine(els.devSpawnerWarning, "Experimental Dev Spawner actions enabled for this app session.", "warning");
  }
  return accepted;
}

function devSpawnerPayload() {
  const actorDistance = getFloat(els.devActorDistance, 0, 20000, 350);
  const actorSpacing = getFloat(els.devActorSpacing, 1, 5000, 125);
  const actorScale = getFloat(els.devActorScale, 0.05, 20, 1);
  const actorZOffset = getFloat(els.devActorZOffset, -5000, 5000, 0);
  return {
    dev_actor_name: getValue(els.devActorName),
    dev_actor_class: getValue(els.devActorClass),
    dev_actor_count: getInt(els.devActorCount, 1, 12, 1),
    dev_actor_distance: actorDistance,
    dev_actor_include_non_generated: Boolean(els.devActorIncludeNonGenerated && els.devActorIncludeNonGenerated.checked),
    dev_actor_scale: actorScale,
    dev_actor_spacing: actorSpacing,
    dev_actor_target_limit: getInt(els.devActorTargetLimit, 1, 200, 20),
    dev_actor_z_offset: actorZOffset,
    dev_ai_name: getValue(els.devAiName),
    dev_ai_class: getValue(els.devAiClass),
    dev_ai_count: getInt(els.devActorCount, 1, 12, 1),
    dev_ai_cache_index: getInt(els.devAiIndex, 0, 99, 0),
    dev_ai_cache_limit: getInt(els.devAiLimit, 1, 100, 10),
    dev_ai_advanced_spawn: true,
    dev_ai_direct_only: Boolean(els.devAiDirectOnly && els.devAiDirectOnly.checked),
    dev_ai_distance: actorDistance,
    dev_ai_load: getValue(els.devAiLoad),
    dev_ai_scale: actorScale,
    dev_ai_spacing: actorSpacing,
    dev_ai_z_offset: actorZOffset
  };
}

function devSpawnerResultText(action, payload, result, analysis) {
  const lines = [];
  lines.push("Electron request:");
  lines.push(pretty({ action, payload }));
  lines.push("");
  if (analysis && analysis.details && analysis.details.length) {
    lines.push("Dev Spawner diagnosis:");
    analysis.details.forEach((line) => lines.push(`- ${line}`));
    lines.push("");
  }
  lines.push("Bridge response:");
  lines.push(pretty(result));
  const data = result && result.data ? result.data : {};
  if (data.command) {
    lines.push("", `Command sent: ${data.command}`);
  }
  if (action === "dev_spawner_spawnai" && (
    Object.prototype.hasOwnProperty.call(data, "resolved")
    || Object.prototype.hasOwnProperty.call(data, "spawned_count")
    || Object.prototype.hasOwnProperty.call(data, "alive_count")
  )) {
    lines.push(
      "",
      "Spawn verification:",
      `- accepted: ${data.accepted === false ? "no" : "yes"}`,
      `- verification: ${data.verification_status || "unknown"}`,
      `- actor definition resolved: ${data.resolved === null || typeof data.resolved === "undefined" ? "unknown" : String(data.resolved)}`,
      `- spawned count: ${data.spawned_count === null || typeof data.spawned_count === "undefined" ? "unknown" : String(data.spawned_count)}`,
      `- alive count: ${data.alive_count === null || typeof data.alive_count === "undefined" ? "unknown" : String(data.alive_count)}`
    );
    if (Array.isArray(data.warnings) && data.warnings.length) {
      lines.push("- warnings:");
      data.warnings.slice(0, 4).forEach((warning) => lines.push(`  ${warning}`));
    }
  }
  if (action === "dev_spawner_targets") {
    lines.push(
      "",
      "Target scans report detailed counts in unrealsdk.log.",
      "If the scan finds 0 results, try another category result, move closer to the object, enable Include Non-Generated, or run Cache Status/Targets after the area fully loads."
    );
  }
  return lines.join("\n");
}

async function readDevSpawnerLogTail() {
  if (!window.msbt || typeof window.msbt.readSdkLogTail !== "function") {
    return { ok: false, text: "SDK log reader is not available in this app build." };
  }
  return window.msbt.readSdkLogTail({ lines: 160 });
}

function formatDevSpawnerLogTail(logResult) {
  if (!logResult || !logResult.ok) {
    return `SDK log tail unavailable: ${logResult && logResult.message ? logResult.message : pretty(logResult)}`;
  }
  const header = logResult.path ? `Recent SDK log lines from ${logResult.path}` : "Recent SDK log lines";
  return `${header}\n${logResult.text || "No recent MSBT/ActorScriptDeployer log lines found."}`;
}

function analyzeDevSpawnerOutcome(action, result, logResult) {
  const data = result && result.data ? result.data : result;
  const message = resultMessage(result);
  const logLines = logResult && Array.isArray(logResult.lines)
    ? logResult.lines
    : String((logResult && logResult.text) || "").split(/\r?\n/).filter(Boolean);
  let focusedLines = logLines.slice(-60);
  if (data && data.command) {
    const commandParts = String(data.command).split(/\s+/).filter(Boolean);
    const commandName = commandParts[0] || "";
    const commandSubject = commandParts[1] || "";
    for (let idx = logLines.length - 1; idx >= 0; idx -= 1) {
      const line = logLines[idx] || "";
      if (line.includes(data.command) || (commandName && line.includes(commandName) && (!commandSubject || line.includes(commandSubject)))) {
        focusedLines = logLines.slice(idx);
        break;
      }
    }
  }
  const logText = focusedLines.join("\n");
  const details = [];
  let kind = actionSucceeded(result) ? "ok" : "bad";
  let status = message;

  if (data && data.queued) {
    kind = "warning";
    status = "Command is still queued; wait in-game or unpause, then refresh the SDK log.";
    details.push("The bridge did not process this action before the app timeout. It may still run later, so avoid repeatedly clicking the same dangerous action.");
  }
  if (data && data.verification_status === "queued_unverified") {
    kind = "warning";
    status = "ASD accepted the spawn, but immediate verification is unknown.";
    details.push("ActorScriptDeployer reported no alive actor during the first poll, but some spawns can finish shortly after the bridge response.");
    details.push("Confirm visually in game, then use the SDK log tail only as supporting evidence.");
  }

  const spawnAction = [
    "dev_spawner_spawn",
    "dev_spawner_spawnai",
    "dev_spawner_lostloot",
    "dev_spawner_barrel_logo"
  ].includes(action);
  const lookupAction = [
    "dev_spawner_targets",
    "dev_spawner_probeai",
    "dev_spawner_cache",
    "dev_spawner_spawnerdiag"
  ].includes(action);

  const noLiveSource = /no live (template|actor-def source) found|did not return an actor|source_counts=\(0,\s*0,\s*0/i.test(logText);
  const noSpawn = /did not report any newly spawned actors|spawned 0 actor|spawned_delta\s*=\s*0/i.test(logText) || noLiveSource;
  const zeroTargets = /returned\s+0\/0|0\s+matches|0\s+result|no matching actor/i.test(logText);
  const spawnComplete = /ASD_spawnai complete|spawned\s+[1-9]\d*\s+actor/i.test(logText);

  if (spawnAction && data && data.verification_status === "queued_unverified") {
    // Keep the warning above. ASD's immediate no-actor output can be a false
    // negative for async spawns such as Char_TargetDummy.
  } else if (spawnAction && noSpawn) {
    kind = "bad";
    status = "ASD received the command, but no actor spawned.";
    details.push("ActorScriptDeployer could not resolve a live template/source for that actor in the current area or cache.");
    details.push("Try List Targets, move near the object, enable Include Non-Generated, run Cache/Probe, or test the same name in SDK Debug Menu.");
  } else if (lookupAction && (noLiveSource || zeroTargets)) {
    kind = "warning";
    status = "ASD ran the lookup, but found no matching live source.";
    details.push("This is a normal 0-result scan, not a bridge failure. Try another preset/category, move near the object, or scan again after the area fully loads.");
  } else if (spawnAction && spawnComplete) {
    kind = "ok";
    status = "ASD reported a spawned actor.";
    details.push("ActorScriptDeployer reported a spawn in the SDK log.");
  }

  if (data && data.command) {
    details.push(`Command: ${data.command}`);
  }

  return { details, kind, status };
}

async function refreshDevSpawnerLogTail() {
  setOutput(els.devSpawnerOutput, "Reading SDK log...");
  const logResult = await readDevSpawnerLogTail();
  setOutput(els.devSpawnerOutput, formatDevSpawnerLogTail(logResult));
  setLine(
    els.devSpawnerWarning,
    logResult && logResult.ok ? "SDK log refreshed." : "SDK log could not be read.",
    logResult && logResult.ok ? "ok" : "warning"
  );
  appendActivity(logResult && logResult.ok ? "Dev Spawner SDK log refreshed." : "Dev Spawner SDK log unavailable.");
}

async function runDevSpawnerAction(action) {
  if (!devSpawnerConfirm()) {
    setOutput(els.devSpawnerOutput, "Dev Spawner action cancelled.");
    return;
  }
  const shouldRestoreSearchFocus = document.activeElement === els.devActorSearch;

  if (action === "dev_spawner_spawn" || action === "dev_spawner_targets") {
    if (!getValue(els.devActorName)) {
      selectDevActorFromList();
    }
  }
  if (action === "dev_spawner_spawnai" || action === "dev_spawner_probeai" || action === "dev_spawner_cache") {
    if (!getValue(els.devAiName)) {
      selectDevActorFromList();
    }
    if (!getValue(els.devAiName)) {
      setOutput(els.devSpawnerOutput, "Select or enter an AI Actor Def / Cache value first.");
      return;
    }
  }

  appendActivity(`Sending ${action}...`);
  setOutput(els.devSpawnerOutput, `Sending ${action}...`);
  try {
    const payload = devSpawnerPayload();
    const result = await bridgeAction(action, payload, 45000);
    const logResult = await readDevSpawnerLogTail();
    const analysis = analyzeDevSpawnerOutcome(action, result, logResult);
    setOutput(
      els.devSpawnerOutput,
      `${devSpawnerResultText(action, payload, result, analysis)}\n\n${formatDevSpawnerLogTail(logResult)}`
    );
    setLine(els.devSpawnerWarning, analysis.status || resultMessage(result), analysis.kind || (actionSucceeded(result) ? "ok" : "bad"));
    appendActivity(`${action}: ${analysis.status || resultMessage(result)}`);
  } catch (error) {
    const message = error && error.message ? error.message : String(error || "Unknown Dev Spawner error");
    setOutput(els.devSpawnerOutput, `Dev Spawner action failed before the bridge returned:\n${message}`);
    setLine(els.devSpawnerWarning, `Dev Spawner action failed: ${message}`, "bad");
    appendActivity(`${action}: failed before bridge response`);
  } finally {
    if (els.devActorSearch) {
      els.devActorSearch.disabled = false;
      if (shouldRestoreSearchFocus) {
        setTimeout(() => els.devActorSearch.focus(), 0);
      }
    }
  }
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-bar [data-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tabId}`);
  });
}

function wireEvents() {
  document.querySelectorAll(".tab-bar [data-tab]").forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  });

  document.getElementById("statusBtn").addEventListener("click", bridgeStatus);
  document.getElementById("setTargetBtn").addEventListener("click", () => setTarget(els.targetSelect.value));
  document.getElementById("firstTargetBtn").addEventListener("click", firstPlayerTarget);
  document.getElementById("kickTargetBtn").addEventListener("click", () => runAction("kick_player", {}, els.boostOutput, 15000));
  els.targetSelect.addEventListener("change", () => setTarget(els.targetSelect.value));

  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => runAction(button.dataset.action, {}, els.boostOutput, 30000));
  });
  document.querySelectorAll("[data-boost-serial-mode]").forEach((button) => {
    button.addEventListener("click", () => sendBoostSerial(button.dataset.boostSerialMode));
  });
  document.getElementById("boostClearSerialsBtn").addEventListener("click", () => {
    els.boostSerialText.value = "";
    setOutput(els.boostOutput, "Cleared local serial input.");
    appendActivity("Cleared Boosting serial input.");
  });
  document.getElementById("setLevelBtn").addEventListener("click", () => runAction("set_level", {
    xp_track: getValue(els.xpTrack),
    level: getInt(els.xpLevel, 1, 9999999, 60)
  }, els.boostOutput, 30000));
  document.getElementById("giveCurrencyBtn").addEventListener("click", () => runAction("give_currency", {
    currency_kind: getValue(els.currencyKind),
    amount: getInt(els.currencyAmount, 0, 2147483647, 1000000)
  }, els.boostOutput, 30000));
  document.getElementById("setInventorySelectedBtn").addEventListener("click", async () => {
    const result = await runAction("set_backpack_bank_selected", inventoryPayload(true), els.boostOutput, 30000);
    setInventoryStatus(resultMessage(result), actionSucceeded(result) ? "ok" : "warning");
  });
  document.getElementById("setInventoryAllBtn").addEventListener("click", async () => {
    const result = await runAction("set_backpack_bank_all", inventoryPayload(true), els.boostOutput, 30000);
    setInventoryStatus(resultMessage(result), actionSucceeded(result) ? "ok" : "warning");
  });
  els.autoInventorySizes.addEventListener("change", toggleAutoInventory);

  els.serialToolsConvertBtn.addEventListener("click", convertSerialTools);
  els.serialToolsClearBtn.addEventListener("click", clearSerialTools);
  els.copyDeserializedBtn.addEventListener("click", () => copyText(els.serialToolsDeserialized.value, els.serialToolsStatus, "Deserialized output"));
  els.copyBreakdownBtn.addEventListener("click", () => copyText(els.serialToolsBreakdown.value, els.serialToolsStatus, "Parts breakdown"));
  els.copySerializedBtn.addEventListener("click", () => copyText(els.serialToolsSerialized.value, els.serialToolsStatus, "@U serialized output"));

  els.validatorBasicBtn.addEventListener("click", validateBasic);
  els.validatorBulkBtn.addEventListener("click", validateBulk);
  els.validatorClearBtn.addEventListener("click", clearValidator);

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
  document.querySelectorAll("[data-editor-serial-mode]").forEach((button) => {
    button.addEventListener("click", () => sendEditorSerial(button.dataset.editorSerialMode));
  });

  els.itempoolSearch.addEventListener("input", renderItemPools);
  els.itempoolCategory.addEventListener("change", renderItemPools);
  els.itempoolList.addEventListener("change", () => {
    state.selectedItemPool = getValue(els.itempoolList);
    renderItemPools();
  });
  document.getElementById("spawnItempoolBtn").addEventListener("click", spawnItemPool);

  if (els.devActorSearch) {
    els.devActorSearch.addEventListener("input", () => {
      state.devActorPage = 0;
      renderDevActors();
    });
  }
  if (els.devPrevActorPageBtn) {
    els.devPrevActorPageBtn.addEventListener("click", () => {
      state.devActorPage = Math.max(0, state.devActorPage - 1);
      renderDevActors();
    });
  }
  if (els.devNextActorPageBtn) {
    els.devNextActorPageBtn.addEventListener("click", () => {
      state.devActorPage += 1;
      renderDevActors();
    });
  }
  if (els.devRefreshLogBtn) {
    els.devRefreshLogBtn.addEventListener("click", refreshDevSpawnerLogTail);
  }
  if (els.devMyFavoriteAddBtn) {
    els.devMyFavoriteAddBtn.addEventListener("click", addSelectedDevMyFavorite);
  }
  if (els.devMyFavoriteRemoveBtn) {
    els.devMyFavoriteRemoveBtn.addEventListener("click", removeSelectedDevMyFavorite);
  }
  document.querySelectorAll("[data-dev-spawner-action]").forEach((button) => {
    button.addEventListener("click", () => runDevSpawnerAction(button.dataset.devSpawnerAction));
  });

  els.travelMapSearch.addEventListener("input", renderMaps);
  els.travelMapList.addEventListener("change", () => {
    state.selectedMap = getValue(els.travelMapList);
    state.selectedStation = "";
    renderMaps();
  });
  els.travelStationSearch.addEventListener("input", renderStations);
  els.travelShowAllStations.addEventListener("change", renderStations);
  els.travelStationList.addEventListener("change", () => {
    state.selectedStation = getValue(els.travelStationList);
    renderStations();
  });
  els.travelMapBtn.addEventListener("click", travelToSelectedMap);
  els.travelStationBtn.addEventListener("click", travelToSelectedStation);

  document.getElementById("refreshActivityBtn").addEventListener("click", bridgeStatus);
  document.getElementById("clearActivityBtn").addEventListener("click", () => {
    state.activity = [];
    setOutput(els.activityOutput, "Activity starts here.");
  });
  document.getElementById("clearBridgeLogBtn").addEventListener("click", () => runAction("clear_external_log", {}, els.activityOutput, 10000));
}

async function init() {
  wireEvents();
  syncDevSpawnerAdvancedControls();
  await Promise.all([loadItemPools(), loadTravelResources(), loadDevSpawnerCatalog(), loadDevSpawnerFavorites()]);
  await bridgeStatus();
  await checkUpdates();
}

init();
