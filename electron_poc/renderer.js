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
    payload: { action, payload },
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
  await Promise.all([loadItemPools(), loadTravelResources()]);
  await bridgeStatus();
  await checkUpdates();
}

init();
