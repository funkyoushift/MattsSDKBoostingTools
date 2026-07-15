const BASE85_RE = /@U[0-9A-Za-z!#$%&()*+\-;<=>?@^_`{\/}~]+/g;

const els = {
  activityOutput: document.getElementById("activityOutput"),
  appOpacity: document.getElementById("appOpacity"),
  appOpacityValue: document.getElementById("appOpacityValue"),
  appVersionLine: document.getElementById("appVersionLine"),
  autoInventorySizes: document.getElementById("autoInventorySizes"),
  bankSize: document.getElementById("bankSize"),
  backpackSize: document.getElementById("backpackSize"),
  bl4BookmarkBtn: document.getElementById("bl4BookmarkBtn"),
  bl4Breakdown: document.getElementById("bl4Breakdown"),
  bl4Cards: document.getElementById("bl4Cards"),
  bl4CardSummary: document.getElementById("bl4CardSummary"),
  bl4ClearSelectionBtn: document.getElementById("bl4ClearSelectionBtn"),
  bl4CopyBreakdownBtn: document.getElementById("bl4CopyBreakdownBtn"),
  bl4CopySelectedBtn: document.getElementById("bl4CopySelectedBtn"),
  bl4CopySerialBtn: document.getElementById("bl4CopySerialBtn"),
  bl4Count: document.getElementById("bl4Count"),
  bl4CreatorFilter: document.getElementById("bl4CreatorFilter"),
  bl4DeliveryLevel: document.getElementById("bl4DeliveryLevel"),
  bl4DeliveryStatus: document.getElementById("bl4DeliveryStatus"),
  bl4Detail: document.getElementById("bl4Detail"),
  bl4ImportSelectedBtn: document.getElementById("bl4ImportSelectedBtn"),
  bl4ListingFilter: document.getElementById("bl4ListingFilter"),
  bl4ManufacturerFilter: document.getElementById("bl4ManufacturerFilter"),
  bl4MattmabFilter: document.getElementById("bl4MattmabFilter"),
  bl4OpenLootlemonBtn: document.getElementById("bl4OpenLootlemonBtn"),
  bl4Output: document.getElementById("bl4Output"),
  bl4OverrideLevel: document.getElementById("bl4OverrideLevel"),
  bl4RarityFilter: document.getElementById("bl4RarityFilter"),
  bl4RefreshGzoBtn: document.getElementById("bl4RefreshGzoBtn"),
  bl4ReloadBtn: document.getElementById("bl4ReloadBtn"),
  bl4Rows: document.getElementById("bl4Rows"),
  bl4SearchBtn: document.getElementById("bl4SearchBtn"),
  bl4SearchInput: document.getElementById("bl4SearchInput"),
  bl4SelectAllBtn: document.getElementById("bl4SelectAllBtn"),
  bl4Serial: document.getElementById("bl4Serial"),
  bl4SetTargetBtn: document.getElementById("bl4SetTargetBtn"),
  bl4RefreshPlayersBtn: document.getElementById("bl4RefreshPlayersBtn"),
  bl4Status: document.getElementById("bl4Status"),
  bl4SubmitGzoBtn: document.getElementById("bl4SubmitGzoBtn"),
  bl4TargetSelect: document.getElementById("bl4TargetSelect"),
  bl4TargetSummary: document.getElementById("bl4TargetSummary"),
  bl4TypeFilter: document.getElementById("bl4TypeFilter"),
  bl4ValidateBtn: document.getElementById("bl4ValidateBtn"),
  boostOutput: document.getElementById("boostOutput"),
  boostSerialLevel: document.getElementById("boostSerialLevel"),
  boostSerialOverride: document.getElementById("boostSerialOverride"),
  boostSerialText: document.getElementById("boostSerialText"),
  boostUpdateDownloadBtn: document.getElementById("boostUpdateDownloadBtn"),
  boostUpdateInstallBtn: document.getElementById("boostUpdateInstallBtn"),
  boostUpdateMessage: document.getElementById("boostUpdateMessage"),
  boostUpdateNotice: document.getElementById("boostUpdateNotice"),
  boostUpdateOpenInstallerBtn: document.getElementById("boostUpdateOpenInstallerBtn"),
  boostUpdateOpenUpdatesBtn: document.getElementById("boostUpdateOpenUpdatesBtn"),
  boostUpdateTitle: document.getElementById("boostUpdateTitle"),
  bridgeSummary: document.getElementById("bridgeSummary"),
  currencyAmount: document.getElementById("currencyAmount"),
  currencyKind: document.getElementById("currencyKind"),
  deliveryOutput: document.getElementById("deliveryOutput"),
  bundledSdkStatus: document.getElementById("bundledSdkStatus"),
  bundledSdkVersion: document.getElementById("bundledSdkVersion"),
  devActorCategoryButtons: document.getElementById("devActorCategoryButtons"),
  devActorClass: document.getElementById("devActorClass"),
  devActorCount: document.getElementById("devActorCount"),
  devActorDelay: document.getElementById("devActorDelay"),
  devActorDetails: document.getElementById("devActorDetails"),
  devActorDistance: document.getElementById("devActorDistance"),
  devActorDisableStates: document.getElementById("devActorDisableStates"),
  devActorEnableStates: document.getElementById("devActorEnableStates"),
  devActorIncludeNonGenerated: document.getElementById("devActorIncludeNonGenerated"),
  devActorName: document.getElementById("devActorName"),
  devActorNoActivate: document.getElementById("devActorNoActivate"),
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
  devLogoActor: document.getElementById("devLogoActor"),
  devLogoDistance: document.getElementById("devLogoDistance"),
  devLogoHeight: document.getElementById("devLogoHeight"),
  devLogoIncludeNonGenerated: document.getElementById("devLogoIncludeNonGenerated"),
  devLogoScale: document.getElementById("devLogoScale"),
  devLogoSpacing: document.getElementById("devLogoSpacing"),
  devLogoText: document.getElementById("devLogoText"),
  devLogoUseSelectedBtn: document.getElementById("devLogoUseSelectedBtn"),
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
  electronAppCurrent: document.getElementById("electronAppCurrent"),
  electronAppInstaller: document.getElementById("electronAppInstaller"),
  electronAppLatest: document.getElementById("electronAppLatest"),
  editorFrame: document.getElementById("editorFrame"),
  gzoSubmitBase85: document.getElementById("gzoSubmitBase85"),
  gzoSubmitCategory: document.getElementById("gzoSubmitCategory"),
  gzoSubmitCloseBtn: document.getElementById("gzoSubmitCloseBtn"),
  gzoSubmitCreator: document.getElementById("gzoSubmitCreator"),
  gzoSubmitDeserialized: document.getElementById("gzoSubmitDeserialized"),
  gzoSubmitForm: document.getElementById("gzoSubmitForm"),
  gzoSubmitImage: document.getElementById("gzoSubmitImage"),
  gzoSubmitImagePreview: document.getElementById("gzoSubmitImagePreview"),
  gzoSubmitListing: document.getElementById("gzoSubmitListing"),
  gzoSubmitModal: document.getElementById("gzoSubmitModal"),
  gzoSubmitName: document.getElementById("gzoSubmitName"),
  gzoSubmitNotes: document.getElementById("gzoSubmitNotes"),
  gzoSubmitRarity: document.getElementById("gzoSubmitRarity"),
  gzoSubmitResetBtn: document.getElementById("gzoSubmitResetBtn"),
  gzoSubmitSendBtn: document.getElementById("gzoSubmitSendBtn"),
  gzoSubmitStatus: document.getElementById("gzoSubmitStatus"),
  gzoSubmitType: document.getElementById("gzoSubmitType"),
  itempoolCategory: document.getElementById("itempoolCategory"),
  itempoolCount: document.getElementById("itempoolCount"),
  itempoolLevel: document.getElementById("itempoolLevel"),
  itempoolList: document.getElementById("itempoolList"),
  itempoolOutput: document.getElementById("itempoolOutput"),
  itempoolSearch: document.getElementById("itempoolSearch"),
  itempoolSummary: document.getElementById("itempoolSummary"),
  inventoryStatus: document.getElementById("inventoryStatus"),
  installedSdkPath: document.getElementById("installedSdkPath"),
  installedSdkStatus: document.getElementById("installedSdkStatus"),
  movementAutoApplySaved: document.getElementById("movementAutoApplySaved"),
  movementDashSpeed: document.getElementById("movementDashSpeed"),
  movementDoubleJumpGoal: document.getElementById("movementDoubleJumpGoal"),
  movementFloorAngle: document.getElementById("movementFloorAngle"),
  movementFloorZ: document.getElementById("movementFloorZ"),
  movementGlideAirControl: document.getElementById("movementGlideAirControl"),
  movementGlideBoost: document.getElementById("movementGlideBoost"),
  movementGlideSpeed: document.getElementById("movementGlideSpeed"),
  movementGravityScale: document.getElementById("movementGravityScale"),
  movementIndividualJumpGoals: document.getElementById("movementIndividualJumpGoals"),
  movementJumpHeight: document.getElementById("movementJumpHeight"),
  movementLoadSavedBtn: document.getElementById("movementLoadSavedBtn"),
  movementOutput: document.getElementById("movementOutput"),
  movementSavePresetBtn: document.getElementById("movementSavePresetBtn"),
  movementSavedSummary: document.getElementById("movementSavedSummary"),
  movementSlideJumpGoal: document.getElementById("movementSlideJumpGoal"),
  movementSpeedScale: document.getElementById("movementSpeedScale"),
  movementSprintJumpGoal: document.getElementById("movementSprintJumpGoal"),
  movementStatus: document.getElementById("movementStatus"),
  movementStepHeight: document.getElementById("movementStepHeight"),
  movementTargetSelect: document.getElementById("movementTargetSelect"),
  movementTimeDilation: document.getElementById("movementTimeDilation"),
  movementWalkSpeed: document.getElementById("movementWalkSpeed"),
  movementZeroVaultOnApply: document.getElementById("movementZeroVaultOnApply"),
  rarityCommonPercent: document.getElementById("rarityCommonPercent"),
  rarityCommonValue: document.getElementById("rarityCommonValue"),
  rarityEpicPercent: document.getElementById("rarityEpicPercent"),
  rarityEpicValue: document.getElementById("rarityEpicValue"),
  rarityLegendaryPercent: document.getElementById("rarityLegendaryPercent"),
  rarityLegendaryValue: document.getElementById("rarityLegendaryValue"),
  rarityLoadPresetBtn: document.getElementById("rarityLoadPresetBtn"),
  rarityPearlescentPercent: document.getElementById("rarityPearlescentPercent"),
  rarityPearlescentValue: document.getElementById("rarityPearlescentValue"),
  rarityRarePercent: document.getElementById("rarityRarePercent"),
  rarityRareValue: document.getElementById("rarityRareValue"),
  rarityRememberPreset: document.getElementById("rarityRememberPreset"),
  raritySavePresetBtn: document.getElementById("raritySavePresetBtn"),
  rarityStatus: document.getElementById("rarityStatus"),
  rarityUncommonPercent: document.getElementById("rarityUncommonPercent"),
  rarityUncommonValue: document.getElementById("rarityUncommonValue"),
  reportActual: document.getElementById("reportActual"),
  reportCopyBtn: document.getElementById("reportCopyBtn"),
  reportDescription: document.getElementById("reportDescription"),
  reportExpected: document.getElementById("reportExpected"),
  reportGithubBtn: document.getElementById("reportGithubBtn"),
  reportIncludeDiagnostics: document.getElementById("reportIncludeDiagnostics"),
  reportKind: document.getElementById("reportKind"),
  reportNotes: document.getElementById("reportNotes"),
  reportPreview: document.getElementById("reportPreview"),
  reportPreviewBtn: document.getElementById("reportPreviewBtn"),
  reportSaveBtn: document.getElementById("reportSaveBtn"),
  reportStatus: document.getElementById("reportStatus"),
  reportSteps: document.getElementById("reportSteps"),
  reportTitle: document.getElementById("reportTitle"),
  bookmarkClearSelectedBtn: document.getElementById("bookmarkClearSelectedBtn"),
  bookmarkCopyBtn: document.getElementById("bookmarkCopyBtn"),
  bookmarkCopySelectedBtn: document.getElementById("bookmarkCopySelectedBtn"),
  bookmarkCount: document.getElementById("bookmarkCount"),
  bookmarkDeleteBtn: document.getElementById("bookmarkDeleteBtn"),
  bookmarkDuplicateBtn: document.getElementById("bookmarkDuplicateBtn"),
  bookmarkGroup: document.getElementById("bookmarkGroup"),
  bookmarkGroupFilter: document.getElementById("bookmarkGroupFilter"),
  bookmarkImportBtn: document.getElementById("bookmarkImportBtn"),
  bookmarkName: document.getElementById("bookmarkName"),
  bookmarkNewBtn: document.getElementById("bookmarkNewBtn"),
  bookmarkOutput: document.getElementById("bookmarkOutput"),
  bookmarkRefreshPlayersBtn: document.getElementById("bookmarkRefreshPlayersBtn"),
  bookmarkRows: document.getElementById("bookmarkRows"),
  bookmarkSaveBtn: document.getElementById("bookmarkSaveBtn"),
  bookmarkSearch: document.getElementById("bookmarkSearch"),
  bookmarkSelectAllBtn: document.getElementById("bookmarkSelectAllBtn"),
  bookmarkSerial: document.getElementById("bookmarkSerial"),
  bookmarkSetTargetBtn: document.getElementById("bookmarkSetTargetBtn"),
  bookmarkStatus: document.getElementById("bookmarkStatus"),
  bookmarkTargetSelect: document.getElementById("bookmarkTargetSelect"),
  bookmarkTargetSummary: document.getElementById("bookmarkTargetSummary"),
  bookmarkValidateBtn: document.getElementById("bookmarkValidateBtn"),
  bookmarkValidationStatus: document.getElementById("bookmarkValidationStatus"),
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
  savedDataBackupBtn: document.getElementById("savedDataBackupBtn"),
  savedDataOpenBtn: document.getElementById("savedDataOpenBtn"),
  savedDataOutput: document.getElementById("savedDataOutput"),
  savedDataRefreshBtn: document.getElementById("savedDataRefreshBtn"),
  savedDataSummary: document.getElementById("savedDataSummary"),
  serialDeliveryBar: document.getElementById("serialDeliveryBar"),
  serialDeliveryLabel: document.getElementById("serialDeliveryLabel"),
  serialDeliveryMessage: document.getElementById("serialDeliveryMessage"),
  serialDeliveryMeta: document.getElementById("serialDeliveryMeta"),
  serialDeliveryPanel: document.getElementById("serialDeliveryPanel"),
  startupUpdateDismissBtn: document.getElementById("startupUpdateDismissBtn"),
  startupUpdateDownloadBtn: document.getElementById("startupUpdateDownloadBtn"),
  startupUpdateInstallBtn: document.getElementById("startupUpdateInstallBtn"),
  startupUpdateInstallerBtn: document.getElementById("startupUpdateInstallerBtn"),
  startupUpdateMessage: document.getElementById("startupUpdateMessage"),
  startupUpdateModal: document.getElementById("startupUpdateModal"),
  startupUpdateTitle: document.getElementById("startupUpdateTitle"),
  startupUpdateUpdatesTabBtn: document.getElementById("startupUpdateUpdatesTabBtn"),
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
  updateDownloadBtn: document.getElementById("updateDownloadBtn"),
  updateInstallBtn: document.getElementById("updateInstallBtn"),
  updateSummary: document.getElementById("updateSummary"),
  versionSummary: document.getElementById("versionSummary"),
  sdkInstallSummary: document.getElementById("sdkInstallSummary"),
  sdkModsPath: document.getElementById("sdkModsPath"),
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
  bl4ActiveId: "",
  bl4CatalogWarnings: [],
  bl4ConfirmedId: "",
  bl4ConfirmedSerial: "",
  bl4Entries: [],
  bl4FilteredEntries: [],
  bl4ResultFilter: "All",
  bl4SearchQuery: "",
  bl4SelectedIds: new Set(),
  bridgeOnline: false,
  bridgeStatusPollInFlight: false,
  bridgeStatusPollTimer: null,
  bookmarkActiveId: "",
  bookmarkCheckedIds: new Set(),
  bookmarkConfirmedId: "",
  bookmarkConfirmedSerial: "",
  bookmarkFilterGroup: "All",
  bookmarkLastValidation: null,
  bookmarkStatusWarnings: [],
  bookmarks: [],
  bookmarkVisibleRows: [],
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
  devperkToggles: { "5": false, "6": false },
  filteredItemPools: [],
  filteredMaps: [],
  filteredStations: [],
  gzoSubmitImageObjectUrl: "",
  itemPools: [],
  latestInstallerUrl: "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest",
  latestDownloadUrl: "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest",
  manualZipDownloadUrl: "https://github.com/funkyoushift/MattsSDKBoostingTools/releases",
  latestUpdateState: null,
  movementAutoAppliedThisSession: false,
  movementAutoApplyOnStart: false,
  movementSavedPreset: null,
  opacitySaveTimer: null,
  players: [],
  rarityRememberOnStart: false,
  raritySavedPreset: null,
  reportPreviewText: "",
  serialDeliveryIdlePolls: 0,
  serialDeliveryLastMessage: "",
  serialDeliveryTimer: null,
  serialToolsAutoTimer: null,
  serialToolsRunId: 0,
  selectedItemPool: "",
  selectedItemPools: new Set(),
  selectedMap: "",
  selectedStation: "",
  selectedTarget: "",
  selectedTargetName: "",
  startupUpdateNoticeShown: false,
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

function clampOpacityPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 100;
  return Math.max(35, Math.min(100, Math.round(number)));
}

function setOpacityControl(percent) {
  const clamped = clampOpacityPercent(percent);
  if (els.appOpacity) els.appOpacity.value = String(clamped);
  if (els.appOpacityValue) els.appOpacityValue.textContent = `${clamped}%`;
}

async function loadWindowSettings() {
  if (!window.msbt || typeof window.msbt.getWindowSettings !== "function") return;
  const result = await window.msbt.getWindowSettings();
  if (result && result.ok) {
    setOpacityControl(Number(result.opacity || 1) * 100);
  }
}

async function saveWindowOpacity() {
  if (!window.msbt || typeof window.msbt.setWindowOpacity !== "function" || !els.appOpacity) return;
  if (state.opacitySaveTimer) {
    clearTimeout(state.opacitySaveTimer);
    state.opacitySaveTimer = null;
  }
  const percent = clampOpacityPercent(els.appOpacity.value);
  setOpacityControl(percent);
  await window.msbt.setWindowOpacity(percent / 100);
}

function queueWindowOpacitySave() {
  if (state.opacitySaveTimer) clearTimeout(state.opacitySaveTimer);
  setOpacityControl(els.appOpacity ? els.appOpacity.value : 100);
  state.opacitySaveTimer = setTimeout(() => {
    state.opacitySaveTimer = null;
    saveWindowOpacity();
  }, 250);
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

function inferToggleStateFromMessage(message, previousValue) {
  const text = String(message || "").toLowerCase();
  if (/\b(off|disabled|inactive)\b/.test(text)) return false;
  if (/\b(on|enabled|active)\b/.test(text)) return true;
  return !previousValue;
}

function updateDevperkToggleButtons() {
  document.querySelectorAll("[data-devperk-toggle]").forEach((button) => {
    const key = String(button.dataset.devperkToggle || "");
    const label = button.dataset.devperkName || button.textContent.replace(/\s+\[(?:ON|OFF)\]$/i, "");
    const isOn = Boolean(state.devperkToggles[key]);
    button.textContent = `${label} [${isOn ? "ON" : "OFF"}]`;
    button.classList.toggle("is-on", isOn);
  });
}

async function runBoostActionButton(button) {
  const action = button.dataset.action;
  const result = await runAction(action, {}, els.boostOutput, 30000);
  const toggleKey = button.dataset.devperkToggle;
  if (toggleKey && actionSucceeded(result)) {
    state.devperkToggles[toggleKey] = inferToggleStateFromMessage(resultMessage(result), state.devperkToggles[toggleKey]);
    updateDevperkToggleButtons();
  }
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

const MOVEMENT_DEFAULTS = {
  speedScale: "1.00",
  walkSpeed: "600",
  jumpHeight: "198",
  gravityScale: "1.00",
  stepHeight: "45",
  floorAngle: "44.8",
  floorZ: "0.71",
  sprintJumpGoal: "198",
  doubleJumpGoal: "198",
  slideJumpGoal: "198",
  glideSpeed: "1200",
  glideBoost: "0",
  glideAirControl: "0.60",
  dashSpeed: "2500",
  timeDilation: "1.00"
};

function resetMovementControlsToDefaults() {
  setTextValue(els.movementSpeedScale, MOVEMENT_DEFAULTS.speedScale);
  setTextValue(els.movementWalkSpeed, MOVEMENT_DEFAULTS.walkSpeed);
  setTextValue(els.movementJumpHeight, MOVEMENT_DEFAULTS.jumpHeight);
  setTextValue(els.movementGravityScale, MOVEMENT_DEFAULTS.gravityScale);
  setTextValue(els.movementStepHeight, MOVEMENT_DEFAULTS.stepHeight);
  setTextValue(els.movementFloorAngle, MOVEMENT_DEFAULTS.floorAngle);
  setTextValue(els.movementFloorZ, MOVEMENT_DEFAULTS.floorZ);
  setTextValue(els.movementSprintJumpGoal, MOVEMENT_DEFAULTS.sprintJumpGoal);
  setTextValue(els.movementDoubleJumpGoal, MOVEMENT_DEFAULTS.doubleJumpGoal);
  setTextValue(els.movementSlideJumpGoal, MOVEMENT_DEFAULTS.slideJumpGoal);
  setTextValue(els.movementGlideSpeed, MOVEMENT_DEFAULTS.glideSpeed);
  setTextValue(els.movementGlideBoost, MOVEMENT_DEFAULTS.glideBoost);
  setTextValue(els.movementGlideAirControl, MOVEMENT_DEFAULTS.glideAirControl);
  setTextValue(els.movementDashSpeed, MOVEMENT_DEFAULTS.dashSpeed);
  setTextValue(els.movementTimeDilation, MOVEMENT_DEFAULTS.timeDilation);
  if (els.movementIndividualJumpGoals) els.movementIndividualJumpGoals.checked = false;
  if (els.movementZeroVaultOnApply) els.movementZeroVaultOnApply.checked = false;
}

function currentMovementPreset() {
  return {
    speedScale: getValue(els.movementSpeedScale) || MOVEMENT_DEFAULTS.speedScale,
    walkSpeed: getValue(els.movementWalkSpeed) || MOVEMENT_DEFAULTS.walkSpeed,
    jumpHeight: getValue(els.movementJumpHeight) || MOVEMENT_DEFAULTS.jumpHeight,
    gravityScale: getValue(els.movementGravityScale) || MOVEMENT_DEFAULTS.gravityScale,
    stepHeight: getValue(els.movementStepHeight) || MOVEMENT_DEFAULTS.stepHeight,
    floorAngle: getValue(els.movementFloorAngle) || MOVEMENT_DEFAULTS.floorAngle,
    floorZ: getValue(els.movementFloorZ) || MOVEMENT_DEFAULTS.floorZ,
    sprintJumpGoal: getValue(els.movementSprintJumpGoal) || MOVEMENT_DEFAULTS.sprintJumpGoal,
    doubleJumpGoal: getValue(els.movementDoubleJumpGoal) || MOVEMENT_DEFAULTS.doubleJumpGoal,
    slideJumpGoal: getValue(els.movementSlideJumpGoal) || MOVEMENT_DEFAULTS.slideJumpGoal,
    glideSpeed: getValue(els.movementGlideSpeed) || MOVEMENT_DEFAULTS.glideSpeed,
    glideBoost: getValue(els.movementGlideBoost) || MOVEMENT_DEFAULTS.glideBoost,
    glideAirControl: getValue(els.movementGlideAirControl) || MOVEMENT_DEFAULTS.glideAirControl,
    dashSpeed: getValue(els.movementDashSpeed) || MOVEMENT_DEFAULTS.dashSpeed,
    timeDilation: getValue(els.movementTimeDilation) || MOVEMENT_DEFAULTS.timeDilation,
    individualJumpGoals: Boolean(els.movementIndividualJumpGoals && els.movementIndividualJumpGoals.checked),
    zeroVaultOnApply: Boolean(els.movementZeroVaultOnApply && els.movementZeroVaultOnApply.checked)
  };
}

function applyMovementPresetToControls(preset) {
  const source = preset && typeof preset === "object" ? preset : {};
  setTextValue(els.movementSpeedScale, source.speedScale || MOVEMENT_DEFAULTS.speedScale);
  setTextValue(els.movementWalkSpeed, source.walkSpeed || MOVEMENT_DEFAULTS.walkSpeed);
  setTextValue(els.movementJumpHeight, source.jumpHeight || MOVEMENT_DEFAULTS.jumpHeight);
  setTextValue(els.movementGravityScale, source.gravityScale || MOVEMENT_DEFAULTS.gravityScale);
  setTextValue(els.movementStepHeight, source.stepHeight || MOVEMENT_DEFAULTS.stepHeight);
  setTextValue(els.movementFloorAngle, source.floorAngle || MOVEMENT_DEFAULTS.floorAngle);
  setTextValue(els.movementFloorZ, source.floorZ || MOVEMENT_DEFAULTS.floorZ);
  setTextValue(els.movementSprintJumpGoal, source.sprintJumpGoal || MOVEMENT_DEFAULTS.sprintJumpGoal);
  setTextValue(els.movementDoubleJumpGoal, source.doubleJumpGoal || MOVEMENT_DEFAULTS.doubleJumpGoal);
  setTextValue(els.movementSlideJumpGoal, source.slideJumpGoal || MOVEMENT_DEFAULTS.slideJumpGoal);
  setTextValue(els.movementGlideSpeed, source.glideSpeed || MOVEMENT_DEFAULTS.glideSpeed);
  setTextValue(els.movementGlideBoost, source.glideBoost || MOVEMENT_DEFAULTS.glideBoost);
  setTextValue(els.movementGlideAirControl, source.glideAirControl || MOVEMENT_DEFAULTS.glideAirControl);
  setTextValue(els.movementDashSpeed, source.dashSpeed || MOVEMENT_DEFAULTS.dashSpeed);
  setTextValue(els.movementTimeDilation, source.timeDilation || MOVEMENT_DEFAULTS.timeDilation);
  if (els.movementIndividualJumpGoals) els.movementIndividualJumpGoals.checked = Boolean(source.individualJumpGoals);
  if (els.movementZeroVaultOnApply) els.movementZeroVaultOnApply.checked = Boolean(source.zeroVaultOnApply);
}

function hasMovementPreset(preset) {
  return Boolean(preset && typeof preset === "object" && Object.keys(preset).length);
}

function setMovementSavedSummary(message, kind = "") {
  setLine(els.movementSavedSummary, message, kind);
}

function movementSettingsPayload() {
  return {
    version: 1,
    preset: currentMovementPreset(),
    autoApplyOnStart: Boolean(els.movementAutoApplySaved && els.movementAutoApplySaved.checked)
  };
}

async function loadMovementSettings() {
  if (!window.msbt || typeof window.msbt.loadMovementSettings !== "function") {
    setMovementSavedSummary("Movement preset storage is unavailable in this shell.", "warning");
    return;
  }
  const result = await window.msbt.loadMovementSettings();
  const data = result && result.data ? result.data : {};
  if (!result || !result.ok) {
    setMovementSavedSummary(resultMessage(result) || "Movement preset load failed.", "warning");
    return;
  }
  state.movementSavedPreset = hasMovementPreset(data.preset) ? data.preset : null;
  state.movementAutoApplyOnStart = Boolean(data.autoApplyOnStart);
  if (els.movementAutoApplySaved) els.movementAutoApplySaved.checked = state.movementAutoApplyOnStart;
  if (state.movementSavedPreset) {
    applyMovementPresetToControls(state.movementSavedPreset);
    setMovementSavedSummary(
      state.movementAutoApplyOnStart
        ? "Saved movement preset loaded. Auto apply is enabled."
        : "Saved movement preset loaded.",
      "ok"
    );
  } else {
    setMovementSavedSummary("No saved movement preset yet.", "warning");
  }
}

async function saveMovementSettings(message = "Saved current movement values as the movement preset.") {
  if (!window.msbt || typeof window.msbt.saveMovementSettings !== "function") {
    setMovementSavedSummary("Movement preset storage is unavailable in this shell.", "warning");
    return null;
  }
  const result = await window.msbt.saveMovementSettings(movementSettingsPayload());
  const data = result && result.data ? result.data : {};
  if (result && result.ok) {
    state.movementSavedPreset = hasMovementPreset(data.preset) ? data.preset : currentMovementPreset();
    state.movementAutoApplyOnStart = Boolean(data.autoApplyOnStart);
    if (els.movementAutoApplySaved) els.movementAutoApplySaved.checked = state.movementAutoApplyOnStart;
    setMovementSavedSummary(message, "ok");
  } else {
    setMovementSavedSummary(resultMessage(result) || "Movement preset save failed.", "bad");
  }
  return result;
}

async function loadSavedMovementPresetIntoControls() {
  if (!state.movementSavedPreset) {
    setMovementSavedSummary("No saved movement preset to load.", "warning");
    return;
  }
  applyMovementPresetToControls(state.movementSavedPreset);
  setMovementSavedSummary("Loaded saved movement preset into the visible fields.", "ok");
}

async function autoApplySavedMovementPresetIfNeeded() {
  if (state.movementAutoAppliedThisSession) return;
  if (!state.bridgeOnline || !state.movementAutoApplyOnStart || !state.movementSavedPreset) return;
  state.movementAutoAppliedThisSession = true;
  applyMovementPresetToControls(state.movementSavedPreset);
  setLine(els.movementStatus, "Auto applying saved movement preset...", "warning");
  const result = await runMovementAction("movement_apply_all");
  setMovementSavedSummary(
    actionSucceeded(result)
      ? "Auto-applied saved movement preset after bridge connection."
      : "Saved movement preset auto-apply was attempted; check the movement result.",
    actionSucceeded(result) ? "ok" : "warning"
  );
}

function movementPayload() {
  const jumpGoal = getFloat(els.movementJumpHeight, 0, 10000, 198);
  const selectedTarget = getValue(els.movementTargetSelect) || state.selectedTarget;
  return {
    movement_speed_scale: getFloat(els.movementSpeedScale, 0.05, 25, 1),
    movement_walk_speed: getFloat(els.movementWalkSpeed, 50, 10000, 600),
    movement_jump_height: jumpGoal,
    movement_jump_velocity: jumpGoal,
    movement_gravity_scale: getFloat(els.movementGravityScale, 0, 10, 1),
    movement_step_height: getFloat(els.movementStepHeight, 0, 1000, 45),
    movement_jump_count: 2,
    movement_jump_off_z_factor: 0.5,
    movement_floor_angle: getFloat(els.movementFloorAngle, 0, 89.9, 44.8),
    movement_floor_z: getFloat(els.movementFloorZ, 0, 1, 0.71),
    movement_individual_jump_goals: Boolean(els.movementIndividualJumpGoals && els.movementIndividualJumpGoals.checked),
    movement_sprint_jump_goal: getFloat(els.movementSprintJumpGoal, 0, 10000, jumpGoal),
    movement_double_jump_goal: getFloat(els.movementDoubleJumpGoal, 0, 10000, jumpGoal),
    movement_slide_jump_goal: getFloat(els.movementSlideJumpGoal, 0, 10000, jumpGoal),
    movement_glide_speed: getFloat(els.movementGlideSpeed, 0, 20000, 1200),
    movement_glide_boost: getFloat(els.movementGlideBoost, 0, 20000, 0),
    movement_glide_air_control: getFloat(els.movementGlideAirControl, 0, 20, 0.6),
    movement_dash_speed: getFloat(els.movementDashSpeed, 0, 50000, 2500),
    movement_zero_vault_on_apply: Boolean(els.movementZeroVaultOnApply && els.movementZeroVaultOnApply.checked),
    movement_time_dilation: getFloat(els.movementTimeDilation, 0.01, 64, 1),
    target_player: selectedTarget,
    infinite_jump_target: selectedTarget
  };
}

async function runMovementAction(action, extraPayload = {}) {
  if (action === "movement_reset_all") {
    resetMovementControlsToDefaults();
  }
  const payload = { ...movementPayload(), ...extraPayload };
  setLine(els.movementStatus, `Sending ${action}...`, "warning");
  const result = await runAction(action, payload, els.movementOutput, 30000);
  setLine(els.movementStatus, resultMessage(result), actionSucceeded(result) ? "ok" : "warning");
  return result;
}

function rarityControls() {
  return [
    { key: "common", input: els.rarityCommonPercent, value: els.rarityCommonValue },
    { key: "uncommon", input: els.rarityUncommonPercent, value: els.rarityUncommonValue },
    { key: "rare", input: els.rarityRarePercent, value: els.rarityRareValue },
    { key: "epic", input: els.rarityEpicPercent, value: els.rarityEpicValue },
    { key: "legendary", input: els.rarityLegendaryPercent, value: els.rarityLegendaryValue },
    { key: "pearlescent", input: els.rarityPearlescentPercent, value: els.rarityPearlescentValue }
  ];
}

function updateRarityValueLabels() {
  rarityControls().forEach(({ input, value }) => {
    if (!input || !value) return;
    value.textContent = `${getInt(input, 0, 100, 100)}%`;
  });
}

function setRarityPreset(values) {
  rarityControls().forEach(({ key, input }) => {
    if (!input) return;
    const nextValue = Object.prototype.hasOwnProperty.call(values, key) ? values[key] : 100;
    input.value = String(Math.max(0, Math.min(100, Number(nextValue) || 0)));
  });
  updateRarityValueLabels();
}

function rarityPayload() {
  const payload = {};
  rarityControls().forEach(({ key, input }) => {
    payload[`rarity_${key}_percent`] = getInt(input, 0, 100, 100);
  });
  return payload;
}

function currentRarityPreset() {
  const preset = {};
  rarityControls().forEach(({ key, input }) => {
    preset[key] = getInt(input, 0, 100, 100);
  });
  return preset;
}

function hasRarityPreset(preset) {
  return Boolean(preset && typeof preset === "object" && Object.keys(preset).length);
}

function raritySettingsPayload() {
  return {
    version: 1,
    preset: currentRarityPreset(),
    rememberOnStart: Boolean(els.rarityRememberPreset && els.rarityRememberPreset.checked)
  };
}

async function loadRaritySettings() {
  if (!window.msbt || typeof window.msbt.loadRaritySettings !== "function") {
    setLine(els.rarityStatus, "Rarity preset storage is unavailable in this shell.", "warning");
    return;
  }
  const result = await window.msbt.loadRaritySettings();
  const data = result && result.data ? result.data : {};
  if (!result || !result.ok) {
    setLine(els.rarityStatus, resultMessage(result) || "Rarity preset load failed.", "warning");
    return;
  }

  const hasSavedFile = Boolean(data.updated_at);
  state.raritySavedPreset = hasSavedFile && hasRarityPreset(data.preset) ? data.preset : null;
  state.rarityRememberOnStart = Boolean(data.rememberOnStart);
  if (els.rarityRememberPreset) els.rarityRememberPreset.checked = state.rarityRememberOnStart;

  if (state.raritySavedPreset && state.rarityRememberOnStart) {
    setRarityPreset(state.raritySavedPreset);
    setLine(els.rarityStatus, "Saved rarity sliders loaded. Drops stay unchanged until you click Apply.", "ok");
  } else if (state.raritySavedPreset) {
    setLine(els.rarityStatus, "Saved rarity sliders found, but startup loading is off. Current sliders remain vanilla until you load or change them.", "warning");
  } else {
    setLine(els.rarityStatus, "No saved rarity preset. Startup sliders use vanilla 100% weights.", "warning");
  }
}

async function saveRaritySettings(message = "Saved current rarity sliders as the rarity preset.") {
  if (!window.msbt || typeof window.msbt.saveRaritySettings !== "function") {
    setLine(els.rarityStatus, "Rarity preset storage is unavailable in this shell.", "warning");
    return null;
  }
  const result = await window.msbt.saveRaritySettings(raritySettingsPayload());
  const data = result && result.data ? result.data : {};
  if (result && result.ok) {
    state.raritySavedPreset = hasRarityPreset(data.preset) ? data.preset : currentRarityPreset();
    state.rarityRememberOnStart = Boolean(data.rememberOnStart);
    if (els.rarityRememberPreset) els.rarityRememberPreset.checked = state.rarityRememberOnStart;
    setLine(els.rarityStatus, message, "ok");
  } else {
    setLine(els.rarityStatus, resultMessage(result) || "Rarity preset save failed.", "bad");
  }
  return result;
}

async function loadSavedRarityPresetIntoControls() {
  if (!state.raritySavedPreset) {
    setLine(els.rarityStatus, "No saved rarity preset to load.", "warning");
    return;
  }
  setRarityPreset(state.raritySavedPreset);
  setLine(els.rarityStatus, "Loaded saved rarity sliders. Drops stay unchanged until you click Apply.", "ok");
}

async function runRarityAction(action) {
  if (action === "rarity_reset") {
    setRarityPreset({});
  } else if (action === "rarity_only_legendary") {
    setRarityPreset({ common: 0, uncommon: 0, rare: 0, epic: 0, legendary: 100, pearlescent: 0 });
  } else if (action === "rarity_only_pearlescent") {
    setRarityPreset({ common: 0, uncommon: 0, rare: 0, epic: 0, legendary: 0, pearlescent: 100 });
  } else {
    updateRarityValueLabels();
  }

  const payload = action === "rarity_apply" ? rarityPayload() : {};
  setLine(els.rarityStatus, `Sending ${action}...`, "warning");
  const result = await runAction(action, payload, els.boostOutput, 30000);
  setLine(els.rarityStatus, resultMessage(result), actionSucceeded(result) ? "ok" : "warning");
  return result;
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
  return name ? `${index}|${name}` : String(index);
}

function playerLabel(player) {
  const index = player && player.index;
  const name = player && player.name ? String(player.name) : "";
  if (index === null || index === undefined || index === "") return name || "Unknown player";
  return `${index} | ${name || "Unknown player"}`;
}

function targetValueFromParts(index, name) {
  const cleanName = String(name || "").trim();
  if (index !== null && index !== undefined && index !== "") {
    return cleanName ? `${index}|${cleanName}` : String(index);
  }
  return cleanName;
}

function targetNameFromValue(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  if (raw.includes("|")) return raw.split("|").slice(1).join("|").trim();
  if (/^\d+$/.test(raw)) return "";
  return raw;
}

function targetIndexFromValue(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const indexText = raw.includes("|") ? raw.split("|", 1)[0].trim() : raw;
  return /^\d+$/.test(indexText) ? indexText : "";
}

function playerNameKey(name) {
  return String(name || "").trim().toLowerCase();
}

function resolveTargetValue(targetValue, players) {
  const list = Array.isArray(players) ? players : [];
  const targetName = targetNameFromValue(targetValue);
  const targetIndex = targetIndexFromValue(targetValue);
  if (targetName) {
    const byName = list.find((player) => playerNameKey(player && player.name) === playerNameKey(targetName));
    if (byName) return playerValue(byName);
    return "";
  }
  if (targetIndex) {
    const byIndex = list.find((player) => String(player && player.index) === String(targetIndex));
    if (byIndex) return playerValue(byIndex);
  }
  return "";
}

function selectedTargetFromStatus(status) {
  const index = status && status.selected_player_index;
  const name = status && status.selected_player ? String(status.selected_player) : "";
  return targetValueFromParts(index, name);
}

function renderPlayers(status = {}) {
  state.players = Array.isArray(status.players) ? status.players : [];
  const selected = selectedTargetFromStatus(status);
  if (selected) {
    state.selectedTarget = selected;
    state.selectedTargetName = targetNameFromValue(selected) || state.selectedTargetName;
  }

  const resolved = resolveTargetValue(state.selectedTarget, state.players);
  if (resolved) {
    state.selectedTarget = resolved;
    state.selectedTargetName = targetNameFromValue(resolved);
  } else if (state.selectedTarget && state.players.length) {
    state.selectedTarget = "";
    state.selectedTargetName = "";
  } else if (!state.players.length) {
    state.selectedTarget = "";
    state.selectedTargetName = "";
  }

  const fillSelect = (selectNode) => {
    if (!selectNode) return;
    selectNode.innerHTML = "";
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = state.players.length ? "Choose player" : "No players loaded";
    selectNode.appendChild(blank);

    state.players.forEach((player) => {
      const option = document.createElement("option");
      option.value = playerValue(player);
      option.textContent = playerLabel(player);
      if (String(option.value) === String(state.selectedTarget)) option.selected = true;
      selectNode.appendChild(option);
    });
  };

  fillSelect(els.targetSelect);
  fillSelect(els.bookmarkTargetSelect);
  fillSelect(els.bl4TargetSelect);
  fillSelect(els.movementTargetSelect);

  const selectedPlayer = state.players.find((player) => String(playerValue(player)) === String(state.selectedTarget));
  const text = `Selected target: ${selectedPlayer ? playerLabel(selectedPlayer) : state.selectedTarget || "none"}`;
  const kind = state.selectedTarget ? "ok" : "warning";
  setLine(els.targetSummary, text, kind);
  setLine(els.bookmarkTargetSummary, text, kind);
  setLine(els.bl4TargetSummary, text, kind);
  setLine(els.movementStatus, text, kind);
}

function serialDeliveryMessage(progress = {}) {
  if (!progress || typeof progress !== "object") return "";
  const message = String(progress.message || progress.last_message || "").trim();
  const error = String(progress.last_error || "").trim();
  return message || error;
}

function updateSerialDeliveryProgress(progress = {}) {
  const message = serialDeliveryMessage(progress);
  const active = Boolean(progress && progress.active);
  const stage = String(progress && progress.stage ? progress.stage : active ? "active" : "idle");
  const hasMessage = Boolean(message);
  if (!els.serialDeliveryPanel) return;

  if (!active && !hasMessage) {
    els.serialDeliveryPanel.classList.add("hidden");
    if (els.serialDeliveryBar) els.serialDeliveryBar.style.width = "0%";
    if (els.serialDeliveryLabel) els.serialDeliveryLabel.textContent = "Idle";
    if (els.serialDeliveryMessage) els.serialDeliveryMessage.textContent = "No active serial delivery.";
    if (els.serialDeliveryMeta) els.serialDeliveryMeta.textContent = "";
    return;
  }

  const percent = Number.isFinite(Number(progress.percent))
    ? Math.max(0, Math.min(100, Number(progress.percent)))
    : Math.max(0, Math.min(100, Number(progress.fraction || 0) * 100));
  const totalChunks = Number(progress.total_chunks || progress.total || 0);
  const currentChunk = Number(progress.current_chunk || progress.index || 0);
  const totalSerials = Number(progress.total_serials || 0);
  const currentChunkSerials = Number(progress.current_chunk_serials || 0);
  const target = String(progress.target_label || progress.scope || "").trim();
  const delay = Number(progress.next_delay_seconds || progress.wait_remaining || 0);

  const metaParts = [];
  if (totalChunks > 0 && currentChunk > 0) metaParts.push(`package ${currentChunk}/${totalChunks}`);
  if (currentChunkSerials > 0) metaParts.push(`${currentChunkSerials} serial(s) in current package`);
  if (totalSerials > 0) metaParts.push(`${totalSerials} serial(s) total`);
  if (target) metaParts.push(target);
  if (delay > 0.05) metaParts.push(`next step in ${delay.toFixed(1)}s`);

  els.serialDeliveryPanel.classList.remove("hidden");
  if (els.serialDeliveryBar) els.serialDeliveryBar.style.width = `${percent.toFixed(0)}%`;
  if (els.serialDeliveryLabel) els.serialDeliveryLabel.textContent = progress.label || `${percent.toFixed(0)}%`;
  if (els.serialDeliveryMessage) {
    els.serialDeliveryMessage.textContent = message || (active ? "Serial delivery is running..." : "Serial delivery status updated.");
    els.serialDeliveryMessage.className = `status-line ${progress.last_error ? "bad" : active ? "warning" : "ok"}`;
  }
  if (els.serialDeliveryMeta) els.serialDeliveryMeta.textContent = metaParts.length ? metaParts.join(" | ") : `stage: ${stage}`;

  if (message && message !== state.serialDeliveryLastMessage) {
    state.serialDeliveryLastMessage = message;
    appendActivity(`SDK serial delivery: ${message}`);
  }
}

function applyBridgeStatusResult(result, options = {}) {
  const data = result && result.data ? result.data : {};
  if (!result.ok || !data.ok) {
    state.bridgeOnline = false;
    state.players = [];
    state.selectedTarget = "";
    state.selectedTargetName = "";
    renderPlayers({});
    setLine(els.bridgeSummary, data.message || "Bridge offline.", "bad");
    updateSerialState();
    if (!options.quiet) appendActivity(data.message || "Bridge offline.");
    return data;
  }

  state.bridgeOnline = true;
  renderPlayers(data);
  const playerCount = Array.isArray(data.players) ? data.players.length : 0;
  const selected = data.selected_player || "none";
  const queue = data.queue || 0;
  setLine(els.bridgeSummary, `Bridge online | players: ${playerCount} | selected: ${selected} | queue: ${queue}`, "ok");
  updateSerialDeliveryProgress(data.serial_delivery || {});
  updateSerialState();
  if (!options.quiet) appendActivity(`Bridge online | players: ${playerCount} | selected: ${selected} | queue: ${queue}`);
  return data;
}

async function bridgeStatus(options = {}) {
  if (!options.quiet) setLine(els.bridgeSummary, "Checking bridge...", "warning");
  const result = await window.msbt.bridgeRequest({ method: "GET", path: "/status" });
  if (!options.quiet) setOutput(els.statusOutput, result);
  applyBridgeStatusResult(result, options);
  await autoApplySavedMovementPresetIfNeeded();
  return result;
}

function startBridgeStatusPolling() {
  if (state.bridgeStatusPollTimer) return;
  state.bridgeStatusPollTimer = window.setInterval(async () => {
    if (state.bridgeStatusPollInFlight) return;
    state.bridgeStatusPollInFlight = true;
    try {
      await bridgeStatus({ quiet: true });
    } finally {
      state.bridgeStatusPollInFlight = false;
    }
  }, 3000);
}

function scheduleSerialDeliveryPoll() {
  if (state.serialDeliveryTimer) return;
  state.serialDeliveryTimer = window.setTimeout(pollSerialDeliveryProgress, 750);
}

async function pollSerialDeliveryProgress() {
  state.serialDeliveryTimer = null;
  let keepPolling = false;
  try {
    const result = await window.msbt.bridgeRequest({ method: "GET", path: "/status" });
    const data = applyBridgeStatusResult(result, { quiet: true });
    const progress = data && data.serial_delivery ? data.serial_delivery : {};
    const active = Boolean(progress && progress.active);
    const hasMessage = Boolean(serialDeliveryMessage(progress));
    if (active) {
      state.serialDeliveryIdlePolls = 0;
      keepPolling = true;
    } else if (hasMessage && state.serialDeliveryIdlePolls < 8) {
      state.serialDeliveryIdlePolls += 1;
      keepPolling = true;
    } else {
      state.serialDeliveryIdlePolls = 0;
    }
  } catch (error) {
    state.serialDeliveryIdlePolls += 1;
    keepPolling = state.serialDeliveryIdlePolls < 4;
  }
  if (keepPolling) scheduleSerialDeliveryPoll();
}

function startSerialDeliveryProgressWatch() {
  state.serialDeliveryIdlePolls = 0;
  scheduleSerialDeliveryPoll();
}

async function setTarget(value) {
  const target = String(value || "").trim();
  if (!target) {
    state.selectedTarget = "";
    state.selectedTargetName = "";
    setLine(els.targetSummary, "Selected target: none", "warning");
    setLine(els.bookmarkTargetSummary, "Selected target: none", "warning");
    setLine(els.bl4TargetSummary, "Selected target: none", "warning");
    setLine(els.movementStatus, "Selected target: none", "warning");
    updateSerialState();
    return null;
  }

  setLine(els.targetSummary, `Setting target ${target}...`, "warning");
  setLine(els.bookmarkTargetSummary, `Setting target ${target}...`, "warning");
  setLine(els.bl4TargetSummary, `Setting target ${target}...`, "warning");
  setLine(els.movementStatus, `Setting target ${target}...`, "warning");
  const result = await bridgeAction("set_target_player", { target_player: target }, 10000);
  setOutput(els.statusOutput, result);
  const ok = Boolean(result && result.data && result.data.ok);
  if (ok) {
    const data = result.data || {};
    state.selectedTarget = targetValueFromParts(data.selected_player_index, data.selected_player) || target;
    state.selectedTargetName = targetNameFromValue(state.selectedTarget);
    await bridgeStatus({ quiet: true });
  } else {
    const message = resultMessage(result) || "Target update failed.";
    setLine(els.targetSummary, message, "bad");
    setLine(els.bookmarkTargetSummary, message, "bad");
    setLine(els.bl4TargetSummary, message, "bad");
    setLine(els.movementStatus, message, "bad");
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
  startSerialDeliveryProgressWatch();
  await bridgeStatus({ quiet: true });
  return result;
}

function bookmarkNow() {
  return new Date().toISOString();
}

function bookmarkId() {
  return `bm_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function bookmarkSummarySerial(serial) {
  const text = String(serial || "").trim();
  if (!text) return "No serial";
  return text.length > 82 ? `${text.slice(0, 42)}...${text.slice(-24)}` : text;
}

function normalizeBookmarkForRenderer(row = {}) {
  const now = bookmarkNow();
  const tags = Array.isArray(row.tags)
    ? row.tags.map((tag) => String(tag || "").trim()).filter(Boolean)
    : String(row.tags || "").split(/[;,|]/g).map((tag) => tag.trim()).filter(Boolean);
  return {
    id: String(row.id || bookmarkId()).trim(),
    name: String(row.name || "Untitled Serial").trim() || "Untitled Serial",
    group: String(row.group || "Default").trim() || "Default",
    serial: String(row.serial || "").trim(),
    source: String(row.source || "").trim(),
    listing: String(row.listing || "").trim(),
    type: String(row.type || "").trim(),
    manufacturer: String(row.manufacturer || "").trim(),
    rarity: String(row.rarity || "").trim(),
    creator: String(row.creator || "").trim(),
    classification: String(row.classification || "").trim(),
    url: String(row.url || "").trim(),
    tags,
    notes: String(row.notes || "").trim(),
    mattmab_validator: String(row.mattmab_validator || row.mattmab_result || "").trim(),
    mattmab_validator_detail: String(row.mattmab_validator_detail || "").trim(),
    decoded_identity: row.decoded_identity && typeof row.decoded_identity === "object" && !Array.isArray(row.decoded_identity)
      ? { ...row.decoded_identity }
      : {},
    created_at: String(row.created_at || now),
    updated_at: String(row.updated_at || now)
  };
}

function activeBookmark() {
  return state.bookmarks.find((row) => row.id === state.bookmarkActiveId) || null;
}

function bookmarkSearchText(row) {
  return [
    row.name,
    row.group,
    row.serial
  ].filter(Boolean).join(" ").toLowerCase();
}

function bookmarkGroups() {
  return Array.from(new Set(state.bookmarks.map((row) => row.group || "Default"))).sort((a, b) => a.localeCompare(b));
}

function bookmarkGroupCounts() {
  const counts = new Map([["All", state.bookmarks.length]]);
  state.bookmarks.forEach((row) => {
    const group = row.group || "Default";
    counts.set(group, (counts.get(group) || 0) + 1);
  });
  return counts;
}

function bookmarkSelectedEntries() {
  const checked = state.bookmarks.filter((row) => state.bookmarkCheckedIds.has(row.id));
  if (checked.length) return checked;
  const active = activeBookmark();
  return active ? [active] : [];
}

function bookmarkSerialLinesForEntry(row) {
  return String(row && row.serial ? row.serial : "")
    .split(/\r?\n/g)
    .map((line) => line.trim())
    .filter(Boolean);
}

function bookmarkSerialLinesForEntries(entries) {
  return entries.flatMap(bookmarkSerialLinesForEntry);
}

function bookmarkInvalidSerialLines(serials) {
  return serials
    .map((serial, index) => ({ serial, index, message: serialValidationMessage(serial) }))
    .filter((entry) => entry.message);
}

function setBookmarkStatus(message, kind = "warning") {
  setLine(els.bookmarkStatus, message, kind);
}

function setBookmarkValidation(message, kind = "warning") {
  setLine(els.bookmarkValidationStatus, message, kind);
}

function invalidateBookmarkConfirmation(message = "Serial changed. Validate / Confirm Serial before sending.") {
  state.bookmarkConfirmedId = "";
  state.bookmarkConfirmedSerial = "";
  state.bookmarkLastValidation = null;
  setBookmarkValidation(message, "warning");
}

function renderBookmarkGroupFilter() {
  if (!els.bookmarkGroupFilter) return;
  const previous = getValue(els.bookmarkGroupFilter) || state.bookmarkFilterGroup || "All";
  const counts = bookmarkGroupCounts();
  els.bookmarkGroupFilter.innerHTML = "";
  ["All", ...bookmarkGroups()].forEach((group) => {
    const option = document.createElement("option");
    option.value = group;
    option.textContent = `${group} (${counts.get(group) || 0})`;
    if (group === previous) option.selected = true;
    els.bookmarkGroupFilter.appendChild(option);
  });
  state.bookmarkFilterGroup = Array.from(els.bookmarkGroupFilter.options).some((option) => option.value === previous)
    ? previous
    : "All";
  els.bookmarkGroupFilter.value = state.bookmarkFilterGroup;
}

function filteredBookmarks() {
  const query = getValue(els.bookmarkSearch).toLowerCase();
  const group = getValue(els.bookmarkGroupFilter) || state.bookmarkFilterGroup || "All";
  state.bookmarkFilterGroup = group;
  return state.bookmarks.filter((row) => {
    const groupOk = group === "All" || (row.group || "Default") === group;
    const queryOk = !query || bookmarkSearchText(row).includes(query);
    return groupOk && queryOk;
  });
}

function renderBookmarks() {
  renderBookmarkGroupFilter();
  const rows = filteredBookmarks();
  state.bookmarkVisibleRows = rows;
  const selectedCount = bookmarkSelectedEntries().length;
  setLine(els.bookmarkCount, `${rows.length} shown / ${state.bookmarks.length} saved | ${selectedCount} selected`, rows.length ? "ok" : "warning");

  if (!els.bookmarkRows) return;
  els.bookmarkRows.innerHTML = "";
  if (!state.bookmarks.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "No saved serial bookmarks yet. Add a name and one @U serial, then Save.";
    els.bookmarkRows.appendChild(empty);
    return;
  }
  if (!rows.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "No bookmarks match the current search and group filter.";
    els.bookmarkRows.appendChild(empty);
    return;
  }

  rows.forEach((row) => {
    const button = document.createElement("button");
    button.type = "button";
    const checked = state.bookmarkCheckedIds.has(row.id);
    button.className = `bookmark-row${row.id === state.bookmarkActiveId ? " active" : ""}${checked ? " checked" : ""}`;
    button.addEventListener("click", () => selectBookmark(row.id, { toggleChecked: true }));

    const main = document.createElement("span");
    const title = document.createElement("span");
    title.className = "bookmark-title";
    title.textContent = `${row.id === state.bookmarkActiveId ? "> " : "  "}${checked ? "[X]" : "[ ]"} ${row.name || "Untitled Serial"}`;
    const serial = document.createElement("span");
    serial.className = "bookmark-serial";
    serial.textContent = bookmarkSummarySerial(row.serial);
    main.append(title, serial);

    const group = document.createElement("span");
    group.className = "bookmark-group";
    group.textContent = row.group || "Default";

    button.append(main, group);
    els.bookmarkRows.appendChild(button);
  });
}

function clearBookmarkForm() {
  state.bookmarkActiveId = "";
  setTextValue(els.bookmarkName, "");
  setTextValue(els.bookmarkGroup, "Default");
  setTextValue(els.bookmarkSerial, "");
  invalidateBookmarkConfirmation("New bookmark staged. Add one @U serial, save, then validate before sending.");
  renderBookmarks();
}

function selectBookmark(id, options = {}) {
  const row = state.bookmarks.find((item) => item.id === id);
  if (!row) {
    clearBookmarkForm();
    return;
  }
  if (options.toggleChecked) {
    if (state.bookmarkCheckedIds.has(row.id)) {
      state.bookmarkCheckedIds.delete(row.id);
    } else {
      state.bookmarkCheckedIds.add(row.id);
    }
  }
  state.bookmarkActiveId = row.id;
  setTextValue(els.bookmarkName, row.name || "");
  setTextValue(els.bookmarkGroup, row.group || "Default");
  setTextValue(els.bookmarkSerial, row.serial || "");
  invalidateBookmarkConfirmation("Bookmark loaded. Validate / Confirm Serial before sending.");
  setBookmarkStatus(`Selected bookmark: ${row.name || "Untitled Serial"}`, "ok");
  renderBookmarks();
}

async function persistSerialBookmarks(successMessage) {
  const result = await window.msbt.saveSerialBookmarks({ version: 1, bookmarks: state.bookmarks });
  if (!result || !result.ok) {
    setBookmarkStatus(result && result.message ? result.message : "Serial bookmarks could not be saved.", "bad");
    return false;
  }
  state.bookmarks = Array.isArray(result.data && result.data.bookmarks)
    ? result.data.bookmarks.map(normalizeBookmarkForRenderer)
    : [];
  const validIds = new Set(state.bookmarks.map((row) => row.id));
  state.bookmarkCheckedIds = new Set(Array.from(state.bookmarkCheckedIds).filter((id) => validIds.has(id)));
  if (state.bookmarkActiveId && !activeBookmark()) state.bookmarkActiveId = "";
  renderBookmarks();
  const warning = Array.isArray(result.warnings) && result.warnings.length ? ` ${result.warnings.join(" ")}` : "";
  setBookmarkStatus(`${successMessage}${warning}`, warning ? "warning" : "ok");
  return true;
}

async function loadSerialBookmarks() {
  if (!window.msbt || typeof window.msbt.loadSerialBookmarks !== "function") {
    setBookmarkStatus("Serial bookmark storage is not available in this Electron build.", "bad");
    return;
  }
  const result = await window.msbt.loadSerialBookmarks();
  if (!result || !result.ok) {
    state.bookmarks = [];
    renderBookmarks();
    setBookmarkStatus(result && result.message ? result.message : "Serial bookmarks could not be loaded.", "bad");
    return;
  }
  state.bookmarks = Array.isArray(result.data && result.data.bookmarks)
    ? result.data.bookmarks.map(normalizeBookmarkForRenderer)
    : [];
  state.bookmarkCheckedIds.clear();
  const warnings = Array.isArray(result.warnings) ? result.warnings : [];
  renderBookmarks();
  if (state.bookmarks.length && !state.bookmarkActiveId) {
    selectBookmark(state.bookmarks[0].id);
  }
  const message = warnings.length
    ? `Loaded ${state.bookmarks.length} bookmark(s). ${warnings.join(" ")}`
    : `Loaded ${state.bookmarks.length} bookmark(s).`;
  setBookmarkStatus(message, warnings.length ? "warning" : "ok");
}

function bookmarkFormRecord(existing = null) {
  const now = bookmarkNow();
  return {
    id: existing && existing.id ? existing.id : bookmarkId(),
    name: getValue(els.bookmarkName) || "Untitled Serial",
    group: getValue(els.bookmarkGroup) || "Default",
    serial: getValue(els.bookmarkSerial),
    created_at: existing && existing.created_at ? existing.created_at : now,
    updated_at: now
  };
}

async function saveBookmark() {
  const serial = getValue(els.bookmarkSerial);
  const validation = serialValidationMessage(serial);
  if (validation) {
    setBookmarkStatus(`Cannot save bookmark: ${validation}`, "bad");
    invalidateBookmarkConfirmation("Fix the serial before validating or sending.");
    return;
  }
  const previous = state.bookmarks.slice();
  const existing = activeBookmark();
  const record = normalizeBookmarkForRenderer(bookmarkFormRecord(existing));
  if (existing) {
    state.bookmarks = state.bookmarks.map((row) => (row.id === existing.id ? record : row));
  } else {
    state.bookmarks = [...state.bookmarks, record];
  }
  state.bookmarkActiveId = record.id;
  invalidateBookmarkConfirmation("Bookmark saved. Validate / Confirm Serial before sending.");
  const saved = await persistSerialBookmarks(existing ? "Bookmark updated." : "Bookmark added.");
  if (!saved) {
    state.bookmarks = previous;
    renderBookmarks();
  }
}

async function deleteBookmark() {
  const row = activeBookmark();
  if (!row) {
    setBookmarkStatus("Select a bookmark to delete.", "warning");
    return;
  }
  const previous = state.bookmarks.slice();
  state.bookmarks = state.bookmarks.filter((item) => item.id !== row.id);
  clearBookmarkForm();
  const saved = await persistSerialBookmarks(`Deleted bookmark: ${row.name || "Untitled Serial"}.`);
  if (!saved) {
    state.bookmarks = previous;
    state.bookmarkActiveId = row.id;
    selectBookmark(row.id);
  }
}

function duplicateBookmark() {
  const row = activeBookmark();
  if (!row) {
    setBookmarkStatus("Select a bookmark before duplicating.", "warning");
    return;
  }
  state.bookmarkActiveId = "";
  setTextValue(els.bookmarkName, `${(row.name || "Serial").trim() || "Serial"} Copy`);
  setTextValue(els.bookmarkGroup, row.group || "Default");
  setTextValue(els.bookmarkSerial, row.serial || "");
  invalidateBookmarkConfirmation("Duplicated into a new unsaved entry. Review, then Save.");
  setBookmarkStatus("Duplicated into a new unsaved entry. Review, then Save.", "ok");
  renderBookmarks();
}

function importBookmarkFromSerialTools() {
  const source = [
    getValue(els.serialToolsSerialized),
    getValue(els.serialToolsDeserialized),
    getValue(els.serialToolsInput)
  ].map((value) => value.trim()).find(Boolean);
  if (!source) {
    setBookmarkStatus("Serial Tools has no output/input to import.", "warning");
    return;
  }
  state.bookmarkActiveId = "";
  setTextValue(els.bookmarkSerial, source);
  if (!getValue(els.bookmarkGroup)) setTextValue(els.bookmarkGroup, "Default");
  invalidateBookmarkConfirmation("Imported text from Serial Tools. Add a name/group, then save.");
  setBookmarkStatus("Imported text from Serial Tools. Add a name/group, then save.", "ok");
  renderBookmarks();
}

async function copyBookmarkSerial() {
  const serial = getValue(els.bookmarkSerial);
  await copyText(serial, els.bookmarkValidationStatus, "Bookmark serial");
}

function selectAllVisibleBookmarks() {
  state.bookmarkVisibleRows.forEach((row) => state.bookmarkCheckedIds.add(row.id));
  renderBookmarks();
  const group = getValue(els.bookmarkGroupFilter) || "All";
  setBookmarkStatus(`Selected ${state.bookmarkVisibleRows.length} visible bookmark(s)${group !== "All" ? ` in ${group}` : ""}.`, "ok");
}

function clearBookmarkSelection() {
  state.bookmarkCheckedIds.clear();
  renderBookmarks();
  setBookmarkStatus("Cleared checked bookmark rows.", "ok");
}

async function copySelectedBookmarkSerials() {
  const entries = bookmarkSelectedEntries();
  const serials = bookmarkSerialLinesForEntries(entries);
  if (!serials.length) {
    setBookmarkStatus("Select one or more bookmarked serials to copy.", "warning");
    return;
  }
  await copyText(serials.join("\n"), els.bookmarkStatus, `${serials.length} bookmarked serial(s)`);
}

function bookmarkValidationFailure(message) {
  state.bookmarkConfirmedId = "";
  state.bookmarkConfirmedSerial = "";
  state.bookmarkLastValidation = null;
  setBookmarkValidation(message, "bad");
  setOutput(els.bookmarkOutput, message);
}

async function validateBookmarkSerial() {
  const serial = getValue(els.bookmarkSerial);
  const validation = serialValidationMessage(serial);
  if (validation) {
    bookmarkValidationFailure(validation);
    return false;
  }

  setBookmarkValidation("Validating serial locally...", "warning");
  const result = await window.msbt.validatorBasic(serial);
  const first = Array.isArray(result && result.results) && result.results.length ? result.results[0] : {};
  const status = String(first.status || result.status || "").toUpperCase();
  if (!result || !result.ok || result.total !== 1 || status === "ERROR") {
    const message = result && (result.summary || result.message || result.output)
      ? (result.summary || result.message || result.output)
      : "Serial validation failed.";
    bookmarkValidationFailure(message);
    return false;
  }

  state.bookmarkConfirmedId = state.bookmarkActiveId || "";
  state.bookmarkConfirmedSerial = serial;
  state.bookmarkLastValidation = result;
  const summary = result.summary || first.message || `Validation complete: ${status || "serial parsed"}.`;
  setBookmarkValidation(
    status === "LEGIT" ? `Confirmed: ${summary}` : `Confirmed with warning: ${summary}`,
    status === "LEGIT" ? "ok" : "warning"
  );
  setOutput(els.bookmarkOutput, result.output || summary);
  return true;
}

async function sendBookmarkSerial(mode) {
  const entries = bookmarkSelectedEntries();
  if (!entries.length) {
    const message = "Select one or more saved serial bookmarks first.";
    setOutput(els.bookmarkOutput, message);
    setBookmarkStatus(message, "warning");
    return;
  }
  const serials = bookmarkSerialLinesForEntries(entries);
  if (!serials.length) {
    const message = "Selected bookmarks did not contain any deliverable @U serials.";
    setOutput(els.bookmarkOutput, message);
    setBookmarkStatus(message, "bad");
    return;
  }
  const invalid = bookmarkInvalidSerialLines(serials);
  if (invalid.length) {
    const shown = invalid.slice(0, 6).map((entry) => `#${entry.index + 1}: ${entry.message}`).join("\n");
    const extra = invalid.length > 6 ? `\n...and ${invalid.length - 6} more.` : "";
    const message = `Selected bookmarks include invalid serials. Fix or uncheck them before delivery.\n${shown}${extra}`;
    setOutput(els.bookmarkOutput, message);
    setBookmarkStatus("Selected bookmarks include invalid serials.", "bad");
    return;
  }
  if (mode === "selected" && !state.selectedTarget) {
    const message = "Select and set a Serial Bookmarks target before Send Selected.";
    setOutput(els.bookmarkOutput, message);
    setLine(els.bookmarkTargetSummary, message, "warning");
    return;
  }

  const destination = mode === "selected" ? (state.selectedTarget || "selected target") : mode === "all" ? "all players" : "non-host players";
  const label = entries.length === 1 ? `"${entries[0].name || "selected bookmark"}"` : `${entries.length} bookmark row(s)`;
  if (!window.confirm(`Deliver ${serials.length} serial(s) from ${label} to ${destination}?`)) {
    setBookmarkStatus("Serial bookmark delivery cancelled.", "warning");
    return;
  }

  const serialText = serials.join("\n");
  setBookmarkStatus(`Sending ${serials.length} bookmarked serial(s) to ${destination}...`, "warning");
  setOutput(
    els.bookmarkOutput,
    `Sending Serial Bookmarks delivery:\nDestination: ${destination}\nBookmark rows: ${entries.length}\nSerial count: ${serials.length}\n${entries.map((row) => `${row.name || "Untitled Serial"} | ${row.group || "Default"}`).join("\n")}`
  );
  const result = await sendSerialPayload(mode, serialText, false, 60, els.bookmarkOutput);
  if (!result) return;
  const message = resultMessage(result);
  if (actionSucceeded(result)) {
    setBookmarkStatus(`Delivery accepted: ${message}`, "ok");
  } else {
    setBookmarkStatus(`Delivery failed: ${message}`, "bad");
  }
}

function setBl4Status(message, kind = "warning") {
  setLine(els.bl4Status, message, kind);
}

function setBl4DeliveryStatus(message, kind = "warning") {
  setLine(els.bl4DeliveryStatus, message, kind);
}

function bl4EntryId(row) {
  return String(row && row.id ? row.id : "");
}

function activeBl4Entry() {
  return state.bl4Entries.find((row) => bl4EntryId(row) === state.bl4ActiveId) || null;
}

function bl4TagText(row) {
  return Array.isArray(row.tags) ? row.tags.join(", ") : String(row.tags || "");
}

function bl4DecodedText(row) {
  const identity = row && row.decoded_identity && typeof row.decoded_identity === "object" ? row.decoded_identity : {};
  return Object.entries(identity).map(([key, value]) => `${key} ${value}`).join(" ");
}

function bl4SearchBlob(row) {
  return [
    row.name,
    row.serial,
    row.source,
    row.listing,
    row.type,
    row.manufacturer,
    row.rarity,
    row.creator,
    row.classification,
    row.mattmab_validator,
    row.deserialized,
    row.notes,
    row.url,
    row.image_url,
    bl4TagText(row),
    bl4DecodedText(row)
  ].filter(Boolean).join(" ").toLowerCase();
}

function bl4MattmabLabel(value) {
  const key = String(value || "UNCHECKED").toUpperCase();
  if (key === "PASS" || key === "LEGIT") return "Legit";
  if (key === "FAIL" || key === "MODDED") return "Modded";
  if (key === "ERROR") return "Error";
  return "Unchecked";
}

function bl4MattmabKind(value) {
  const label = bl4MattmabLabel(value);
  if (label === "Legit") return "ok";
  if (label === "Modded") return "warning";
  if (label === "Error") return "bad";
  return "warning";
}

function bl4SelectedEntries() {
  const selected = state.bl4Entries.filter((row) => state.bl4SelectedIds.has(bl4EntryId(row)));
  if (selected.length) return selected;
  const active = activeBl4Entry();
  return active ? [active] : [];
}

function bl4ValidSerialEntries(entries) {
  return entries.filter((row) => !serialValidationMessage(row.serial));
}

function bl4DeliveryRowLabel(row, index) {
  const name = String(row && row.name ? row.name : "Selected BL4 code").trim();
  const source = String(row && (row.source || row.listing) ? row.source || row.listing : "").trim();
  return `${index + 1}. ${name}${source ? ` (${source})` : ""}`;
}

async function preflightBl4LevelOverride(rows, serialText, deliveryLevel) {
  if (!window.msbt || typeof window.msbt.serialDecodeCheck !== "function") {
    return { ok: true, rows, serialText, skipped: [] };
  }

  setBl4DeliveryStatus(`Checking ${rows.length} BL4 serial(s) for level override...`, "warning");
  const result = await window.msbt.serialDecodeCheck({ text: serialText, level: deliveryLevel });
  if (!result || result.ok === false) {
    const message = result && result.message ? result.message : "Local level-override check is unavailable; trying bridge delivery.";
    setBl4DeliveryStatus(message, "warning");
    appendActivity(`BL4 level override preflight unavailable: ${message}`);
    return { ok: true, rows, serialText, skipped: [] };
  }

  const results = Array.isArray(result.results) ? result.results : [];
  const checked = rows.map((row, index) => ({ item: results[index] || { ok: false, message: "No decode result returned." }, index, row }));
  const failures = checked.filter((entry) => !entry.item.ok);
  if (!failures.length) return { ok: true, rows, serialText, skipped: [] };

  const shown = failures.slice(0, 8).map((entry) => (
    `${bl4DeliveryRowLabel(entry.row, entry.index)} - ${entry.item.message || "could not decode"}`
  ));
  const extra = failures.length > shown.length ? `\n...and ${failures.length - shown.length} more.` : "";
  const deliverableRows = checked.filter((entry) => entry.item.ok).map((entry) => entry.row);
  if (!deliverableRows.length) {
    const message = `Level override cannot be applied to any selected code. Nothing will be delivered.`;
    const details = `${message}\n\n${shown.join("\n")}${extra}`;
    setBl4DeliveryStatus(message, "bad");
    setOutput(els.bl4Output, details);
    appendActivity(`BL4 level override blocked: all ${failures.length} selected serial(s) could not be decoded.`);
    return { ok: false, rows: [], serialText: "", skipped: failures };
  }

  const message = `Level override cannot be applied to ${failures.length} selected code(s); those row(s) will be skipped.`;
  const details = `${message}\n\nSkipped:\n${shown.join("\n")}${extra}\n\nDelivering ${deliverableRows.length} remaining code(s).`;
  setBl4DeliveryStatus(message, "warning");
  setOutput(els.bl4Output, details);
  appendActivity(`BL4 level override skipped ${failures.length} serial(s); ${deliverableRows.length} still deliverable.`);
  return {
    ok: true,
    rows: deliverableRows,
    serialText: deliverableRows.map((row) => String(row.serial || "").trim()).join("\n"),
    skipped: failures
  };
}

function fillBl4Filter(selectNode, values, currentValue = "All") {
  if (!selectNode) return;
  const previous = currentValue || getValue(selectNode) || "All";
  selectNode.innerHTML = "";
  ["All", ...(values || [])].forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    selectNode.appendChild(option);
  });
  const hasPrevious = Array.from(selectNode.options).some((option) => option.value === previous);
  selectNode.value = hasPrevious ? previous : "All";
}

function populateBl4Filters(filters = {}) {
  fillBl4Filter(els.bl4ListingFilter, filters.listings || []);
  fillBl4Filter(els.bl4TypeFilter, filters.types || []);
  fillBl4Filter(els.bl4ManufacturerFilter, filters.manufacturers || []);
  fillBl4Filter(els.bl4RarityFilter, filters.rarities || []);
  fillBl4Filter(els.bl4CreatorFilter, filters.creators || []);
  fillBl4Filter(els.bl4MattmabFilter, ["Legit", "Modded", "Error", "Unchecked"]);
}

function bl4ListingMatches(row, value) {
  if (!value || value === "All") return true;
  const wanted = value.toLowerCase();
  const tags = Array.isArray(row.tags) ? row.tags.map((tag) => String(tag).toLowerCase()) : [];
  return [
    row.listing,
    row.source,
    row.classification
  ].some((item) => String(item || "").toLowerCase() === wanted)
    || tags.includes(wanted)
    || (wanted === "modded" && (String(row.classification || "").toLowerCase() === "modded" || tags.includes("modded")));
}

function bl4MattmabMatches(row, value) {
  if (!value || value === "All") return true;
  return bl4MattmabLabel(row.mattmab_validator).toLowerCase() === value.toLowerCase();
}

function bl4FilterValue(selectNode) {
  return getValue(selectNode) || "All";
}

function filteredBl4Entries() {
  const terms = (state.bl4SearchQuery || "").toLowerCase().split(/\s+/).filter(Boolean);
  const listing = bl4FilterValue(els.bl4ListingFilter);
  const type = bl4FilterValue(els.bl4TypeFilter);
  const manufacturer = bl4FilterValue(els.bl4ManufacturerFilter);
  const rarity = bl4FilterValue(els.bl4RarityFilter);
  const creator = bl4FilterValue(els.bl4CreatorFilter);
  const mattmab = bl4FilterValue(els.bl4MattmabFilter);
  const resultFilter = state.bl4ResultFilter || "All";

  return state.bl4Entries.filter((row) => {
    const termOk = terms.every((term) => bl4SearchBlob(row).includes(term));
    const listingOk = bl4ListingMatches(row, listing);
    const typeOk = type === "All" || String(row.type || "") === type;
    const manufacturerOk = manufacturer === "All" || String(row.manufacturer || "") === manufacturer;
    const rarityOk = rarity === "All" || String(row.rarity || "") === rarity;
    const creatorOk = creator === "All" || String(row.creator || "") === creator;
    const mattmabOk = bl4MattmabMatches(row, mattmab);
    const resultOk = bl4MattmabMatches(row, resultFilter);
    return termOk && listingOk && typeOk && manufacturerOk && rarityOk && creatorOk && mattmabOk && resultOk;
  });
}

function formatBl4Detail(row) {
  if (!row) return "Select a BL4 code.";
  const identity = row.decoded_identity && typeof row.decoded_identity === "object" ? row.decoded_identity : {};
  const identityLines = Object.keys(identity).length
    ? Object.entries(identity).map(([key, value]) => `  ${key}: ${value}`)
    : ["  Not available in catalog."];
  return [
    `Name: ${row.name || ""}`,
    `Source: ${row.source || ""}`,
    `Listing: ${row.listing || ""}`,
    `Classification: ${row.classification || ""}`,
    `Mattmab Result: ${bl4MattmabLabel(row.mattmab_validator)}`,
    `Type: ${row.type || ""}`,
    `Manufacturer: ${row.manufacturer || ""}`,
    `Rarity: ${row.rarity || ""}`,
    `Creator: ${row.creator || ""}`,
    `Tags: ${bl4TagText(row) || ""}`,
    row.url ? `Lootlemon URL: ${row.url}` : "",
    row.image_url ? `Image URL: ${row.image_url}` : "",
    row.notes ? `Notes: ${row.notes}` : "",
    "Decoded identity:",
    ...identityLines
  ].filter((line) => line !== "").join("\n");
}

function bl4ImageUrl(row) {
  return String(row && (row.image_url || row.imageUrl || row.image || row.thumbnail || row.screenshot) ? row.image_url || row.imageUrl || row.image || row.thumbnail || row.screenshot : "").trim();
}

function bl4IsGzoRow(row) {
  return String(row && row.source ? row.source : "").toLowerCase() === "gzo";
}

function bl4ImageStats(rows = state.bl4Entries) {
  const list = Array.isArray(rows) ? rows : [];
  const gzoRows = list.filter((row) => bl4IsGzoRow(row));
  return {
    total: list.length,
    withImages: list.filter((row) => bl4ImageUrl(row)).length,
    gzo: gzoRows.length,
    gzoWithImages: gzoRows.filter((row) => bl4ImageUrl(row)).length
  };
}

function bl4ImageHint(rows = state.bl4Entries) {
  const stats = bl4ImageStats(rows);
  if (stats.gzo > 0 && stats.gzoWithImages === 0) {
    return "GZO image metadata is not in this local cache yet. Click Refresh GZO once to load website images.";
  }
  if (stats.gzo > 0 && stats.gzoWithImages < stats.gzo) {
    return `${stats.gzoWithImages}/${stats.gzo} GZO rows include images; local, Lootlemon, and custom rows may not.`;
  }
  if (stats.withImages === 0 && stats.total > 0) {
    return "No image URLs are available for these local rows.";
  }
  return `${stats.withImages}/${stats.total} visible rows include image URLs.`;
}

function renderBl4Cards() {
  if (!els.bl4Cards) return;
  els.bl4Cards.innerHTML = "";
  if (!state.bl4Entries.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "No BL4 catalog is loaded.";
    els.bl4Cards.appendChild(empty);
    if (els.bl4CardSummary) els.bl4CardSummary.textContent = "GZO images load directly from save-editor.be when available.";
    return;
  }
  if (!state.bl4FilteredEntries.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "No image cards match the current filters.";
    els.bl4Cards.appendChild(empty);
    if (els.bl4CardSummary) els.bl4CardSummary.textContent = "No visible cards.";
    return;
  }

  const maxCards = 48;
  const shown = state.bl4FilteredEntries.slice(0, maxCards);
  if (els.bl4CardSummary) {
    els.bl4CardSummary.textContent = `${shown.length} card(s) shown; ${bl4ImageHint(shown)} Use filters to narrow more.`;
  }

  shown.forEach((row) => {
    const id = bl4EntryId(row);
    const card = document.createElement("button");
    card.type = "button";
    card.className = `bl4-code-card${id === state.bl4ActiveId ? " active" : ""}`;
    card.addEventListener("click", () => selectBl4Entry(id));

    const imageWrap = document.createElement("div");
    imageWrap.className = "bl4-card-image";
    const imageUrl = bl4ImageUrl(row);
    if (imageUrl) {
      const img = document.createElement("img");
      img.loading = "lazy";
      img.decoding = "async";
      img.alt = row.name || "BL4 item image";
      img.src = imageUrl;
      img.addEventListener("error", () => {
        imageWrap.textContent = "Image unavailable";
        imageWrap.classList.add("missing");
      });
      imageWrap.appendChild(img);
    } else {
      imageWrap.textContent = bl4IsGzoRow(row) ? "No GZO image" : "No image";
      imageWrap.classList.add("missing");
    }

    const title = document.createElement("div");
    title.className = "bl4-card-title";
    title.textContent = row.name || "Unnamed Code";
    const meta = document.createElement("div");
    meta.className = "bl4-card-meta";
    meta.textContent = [
      row.listing,
      row.type,
      row.rarity,
      row.creator
    ].filter(Boolean).join(" | ");
    const result = document.createElement("div");
    result.className = `bl4-card-result ${bl4MattmabKind(row.mattmab_validator)}`;
    result.textContent = bl4MattmabLabel(row.mattmab_validator);
    card.append(imageWrap, title, meta, result);
    els.bl4Cards.appendChild(card);
  });

  if (state.bl4FilteredEntries.length > maxCards) {
    const note = document.createElement("div");
    note.className = "dev-empty-row";
    note.textContent = `Showing first ${maxCards} card(s). Narrow Search or filters for more images.`;
    els.bl4Cards.appendChild(note);
  }
}

function bl4SubmitListing(row) {
  const classification = String(row && row.classification ? row.classification : "").toLowerCase();
  const listing = String(row && row.listing ? row.listing : "").toLowerCase();
  if (classification === "modded" || listing === "modded") return "Modded";
  return "Legit";
}

function clearGzoSubmitImagePreview() {
  if (state.gzoSubmitImageObjectUrl) {
    URL.revokeObjectURL(state.gzoSubmitImageObjectUrl);
    state.gzoSubmitImageObjectUrl = "";
  }
  if (els.gzoSubmitImage) els.gzoSubmitImage.value = "";
  if (els.gzoSubmitImagePreview) {
    els.gzoSubmitImagePreview.innerHTML = "";
    els.gzoSubmitImagePreview.textContent = "No image selected.";
  }
}

function updateGzoSubmitImagePreview() {
  if (!els.gzoSubmitImage || !els.gzoSubmitImagePreview) return;
  if (state.gzoSubmitImageObjectUrl) {
    URL.revokeObjectURL(state.gzoSubmitImageObjectUrl);
    state.gzoSubmitImageObjectUrl = "";
  }
  const file = els.gzoSubmitImage.files && els.gzoSubmitImage.files.length ? els.gzoSubmitImage.files[0] : null;
  els.gzoSubmitImagePreview.innerHTML = "";
  if (!file) {
    els.gzoSubmitImagePreview.textContent = "No image selected.";
    return;
  }
  state.gzoSubmitImageObjectUrl = URL.createObjectURL(file);
  const img = document.createElement("img");
  img.alt = file.name;
  img.src = state.gzoSubmitImageObjectUrl;
  const label = document.createElement("div");
  label.textContent = `${file.name} (${Math.ceil(file.size / 1024)} KB)`;
  els.gzoSubmitImagePreview.append(img, label);
  setLine(els.gzoSubmitStatus, "Image attached. The form is ready for API wiring once Ynot sends the endpoint.", "ok");
}

function fillGzoSubmitForm(row) {
  if (!row) return;
  if (els.gzoSubmitListing) els.gzoSubmitListing.value = bl4SubmitListing(row);
  setTextValue(els.gzoSubmitName, row.name || "");
  setTextValue(els.gzoSubmitCreator, row.creator || "");
  setTextValue(els.gzoSubmitType, row.type || "");
  setTextValue(els.gzoSubmitCategory, row.category || row.type || "");
  setTextValue(els.gzoSubmitRarity, row.rarity || "");
  setTextValue(els.gzoSubmitBase85, row.serial || "");
  setTextValue(els.gzoSubmitDeserialized, row.deserialized || "");
  setTextValue(els.gzoSubmitNotes, row.notes || "");
  clearGzoSubmitImagePreview();
  const imageHint = bl4ImageUrl(row)
    ? "This catalog row already has a web image. Upload a screenshot/image file when submitting a new item."
    : "Upload a screenshot or generated item image before submitting.";
  setLine(els.gzoSubmitStatus, `API URL is not configured yet. ${imageHint}`, "warning");
}

function openGzoSubmitModal() {
  const row = activeBl4Entry();
  if (!row) {
    setBl4Status("Select a BL4 code before opening the GZO submission form.", "warning");
    return;
  }
  fillGzoSubmitForm(row);
  if (els.gzoSubmitModal) els.gzoSubmitModal.classList.remove("hidden");
}

function closeGzoSubmitModal() {
  if (els.gzoSubmitModal) els.gzoSubmitModal.classList.add("hidden");
}

function validateGzoSubmitForm() {
  const required = [
    ["listing", getValue(els.gzoSubmitListing)],
    ["name", getValue(els.gzoSubmitName)],
    ["creator", getValue(els.gzoSubmitCreator)],
    ["type", getValue(els.gzoSubmitType)],
    ["rarity", getValue(els.gzoSubmitRarity)]
  ];
  const missing = required.filter(([, value]) => !String(value || "").trim()).map(([label]) => label);
  if (!getValue(els.gzoSubmitBase85).trim()) missing.push("base85");
  const image = els.gzoSubmitImage && els.gzoSubmitImage.files && els.gzoSubmitImage.files.length ? els.gzoSubmitImage.files[0] : null;
  if (!image) missing.push("image");
  return { ok: !missing.length, missing };
}

function handleGzoSubmit(event) {
  if (event) event.preventDefault();
  const check = validateGzoSubmitForm();
  if (!check.ok) {
    setLine(els.gzoSubmitStatus, `Required before submission: ${check.missing.join(", ")}.`, "bad");
    return;
  }
  setLine(
    els.gzoSubmitStatus,
    "Form data and image are ready. Waiting for Ynot's API URL before enabling the actual upload.",
    "warning"
  );
}

function clearBl4Detail(message = "Select a BL4 code.") {
  state.bl4ActiveId = "";
  state.bl4ConfirmedId = "";
  state.bl4ConfirmedSerial = "";
  setOutput(els.bl4Detail, message);
  setTextValue(els.bl4Serial, "");
  setTextValue(els.bl4Breakdown, "");
  setBl4DeliveryStatus("Delivery sends checked rows, or the active code if none are checked.", "warning");
}

async function loadBl4Breakdown(row) {
  if (!row || !row.serial) return;
  const activeId = bl4EntryId(row);
  setTextValue(els.bl4Breakdown, "Generating parts breakdown locally...");
  if (!window.msbt || typeof window.msbt.bl4PartsBreakdown !== "function") {
    setTextValue(els.bl4Breakdown, "Parts breakdown helper is not available in this Electron build.");
    return;
  }
  const result = await window.msbt.bl4PartsBreakdown(row.serial);
  if (state.bl4ActiveId !== activeId) return;
  if (result && result.ok) {
    setTextValue(els.bl4Breakdown, result.breakdown || "No parts breakdown returned.");
  } else {
    setTextValue(els.bl4Breakdown, result && result.message ? `Parts breakdown unavailable: ${result.message}` : "Parts breakdown unavailable.");
  }
}

function selectBl4Entry(id) {
  const row = state.bl4Entries.find((item) => bl4EntryId(item) === id);
  if (!row) {
    clearBl4Detail();
    renderBl4Codes();
    return;
  }
  state.bl4ActiveId = id;
  state.bl4ConfirmedId = "";
  state.bl4ConfirmedSerial = "";
  setOutput(els.bl4Detail, formatBl4Detail(row));
  setTextValue(els.bl4Serial, row.serial || "");
  setBl4DeliveryStatus("Active code ready. Delivery sends checked rows, or this active code if none are checked.", "warning");
  loadBl4Breakdown(row);
  renderBl4Codes();
}

function renderBl4Codes() {
  state.bl4FilteredEntries = filteredBl4Entries();
  state.bl4SelectedIds = new Set(
    Array.from(state.bl4SelectedIds).filter((id) => state.bl4Entries.some((row) => bl4EntryId(row) === id))
  );
  const selectedCount = state.bl4SelectedIds.size;
  setLine(
    els.bl4Count,
    `${state.bl4FilteredEntries.length} shown / ${state.bl4Entries.length} merged | ${selectedCount} selected`,
    state.bl4FilteredEntries.length ? "ok" : "warning"
  );
  renderBl4Cards();

  if (!els.bl4Rows) return;
  els.bl4Rows.innerHTML = "";
  if (!state.bl4Entries.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "No BL4 catalog is loaded.";
    els.bl4Rows.appendChild(empty);
    clearBl4Detail("No BL4 catalog is loaded.");
    return;
  }
  if (!state.bl4FilteredEntries.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "No BL4 codes match the current filters. Use Search, All Results, or loosen a dropdown filter.";
    els.bl4Rows.appendChild(empty);
    clearBl4Detail("No BL4 code is visible with the current filters.");
    return;
  }

  if (state.bl4ActiveId && !state.bl4FilteredEntries.some((row) => bl4EntryId(row) === state.bl4ActiveId)) {
    clearBl4Detail("The active code is hidden by the current filters.");
  }

  const maxRows = 320;
  state.bl4FilteredEntries.slice(0, maxRows).forEach((row) => {
    const id = bl4EntryId(row);
    const item = document.createElement("div");
    item.className = `bl4-code-row${id === state.bl4ActiveId ? " active" : ""}`;
    item.addEventListener("click", () => selectBl4Entry(id));

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = state.bl4SelectedIds.has(id);
    checkbox.addEventListener("click", (event) => {
      event.stopPropagation();
      if (checkbox.checked) {
        state.bl4SelectedIds.add(id);
      } else {
        state.bl4SelectedIds.delete(id);
      }
      renderBl4Codes();
    });

    const body = document.createElement("div");
    body.className = "bl4-row-body";
    const title = document.createElement("div");
    title.className = "bl4-row-title";
    title.textContent = row.name || "Unnamed Code";
    const meta = document.createElement("div");
    meta.className = "bl4-row-meta";
    meta.textContent = [
      bl4MattmabLabel(row.mattmab_validator),
      row.listing,
      row.type,
      row.rarity,
      row.creator
    ].filter(Boolean).join(" | ");
    const serial = document.createElement("div");
    serial.className = "bl4-row-serial";
    serial.textContent = row.serial;
    body.append(title, meta, serial);
    item.append(checkbox, body);
    els.bl4Rows.appendChild(item);
  });

  if (state.bl4FilteredEntries.length > maxRows) {
    const note = document.createElement("div");
    note.className = "dev-empty-row";
    note.textContent = `Showing first ${maxRows} row(s). Narrow Search or filters for more.`;
    els.bl4Rows.appendChild(note);
  }

  if (!state.bl4ActiveId && state.bl4FilteredEntries.length) {
    selectBl4Entry(bl4EntryId(state.bl4FilteredEntries[0]));
  }
}

function applyBl4Search() {
  state.bl4SearchQuery = getValue(els.bl4SearchInput);
  renderBl4Codes();
}

function setBl4ResultFilter(value) {
  state.bl4ResultFilter = value || "All";
  renderBl4Codes();
}

function selectAllBl4Visible() {
  state.bl4FilteredEntries.forEach((row) => state.bl4SelectedIds.add(bl4EntryId(row)));
  renderBl4Codes();
  setBl4Status(`Selected ${state.bl4FilteredEntries.length} visible BL4 code(s).`, "ok");
}

function clearBl4Selection() {
  state.bl4SelectedIds.clear();
  renderBl4Codes();
  setBl4Status("Cleared selected BL4 code rows.", "ok");
}

async function copySelectedBl4Serials() {
  const entries = bl4ValidSerialEntries(bl4SelectedEntries());
  const serials = entries.map((row) => row.serial).join("\n");
  await copyText(serials, els.bl4Status, `${entries.length} BL4 serial(s)`);
}

async function copyBl4Serial() {
  const row = activeBl4Entry();
  await copyText(row ? row.serial : "", els.bl4Status, "BL4 serial");
}

async function copyBl4Breakdown() {
  await copyText(getValue(els.bl4Breakdown), els.bl4Status, "BL4 parts breakdown");
}

function openBl4Lootlemon() {
  const row = activeBl4Entry();
  if (!row || !row.url) {
    setBl4Status("This BL4 code does not have a Lootlemon URL in the local catalog.", "warning");
    return;
  }
  window.msbt.openExternal(row.url);
  setBl4Status("Opened Lootlemon link.", "ok");
}

function bl4BookmarkPayload(row) {
  return normalizeBookmarkForRenderer({
    name: row.name || "BL4 Code",
    group: row.type || row.listing || "BL4 Codes",
    serial: row.serial,
    source: row.source,
    listing: row.listing,
    type: row.type,
    manufacturer: row.manufacturer,
    rarity: row.rarity,
    creator: row.creator,
    classification: row.classification,
    url: row.url,
    image_url: row.image_url,
    tags: row.tags,
    notes: row.notes,
    mattmab_validator: row.mattmab_validator,
    mattmab_validator_detail: row.mattmab_validator_detail,
    deserialized: row.deserialized,
    decoded_identity: row.decoded_identity
  });
}

async function addBl4EntriesToBookmarks(entries, successPrefix) {
  const rows = bl4ValidSerialEntries(entries);
  if (!rows.length) {
    setBl4Status("No valid @U serials were available to bookmark.", "warning");
    return;
  }
  const now = bookmarkNow();
  const existingBySerial = new Map(state.bookmarks.map((row) => [String(row.serial || "").toLowerCase(), row]));
  let added = 0;
  let updated = 0;
  const next = state.bookmarks.slice();
  rows.forEach((row) => {
    const payload = bl4BookmarkPayload(row);
    const key = payload.serial.toLowerCase();
    const existing = existingBySerial.get(key);
    if (existing) {
      updated += 1;
      const merged = {
        ...existing,
        ...payload,
        id: existing.id,
        name: existing.name || payload.name,
        group: existing.group || payload.group,
        created_at: existing.created_at || payload.created_at,
        updated_at: now
      };
      const index = next.findIndex((item) => item.id === existing.id);
      if (index >= 0) next[index] = merged;
      existingBySerial.set(key, merged);
      return;
    }
    added += 1;
    next.push(payload);
    existingBySerial.set(key, payload);
  });
  state.bookmarks = next;
  const saved = await persistSerialBookmarks(`${successPrefix}: ${added} added, ${updated} updated.`);
  if (saved) {
    setBl4Status(`${successPrefix}: ${added} added, ${updated} updated.`, "ok");
  }
}

async function bookmarkActiveBl4Code() {
  const row = activeBl4Entry();
  if (!row) {
    setBl4Status("Select a BL4 code to bookmark.", "warning");
    return;
  }
  await addBl4EntriesToBookmarks([row], "Bookmarked selected BL4 code locally");
}

async function importSelectedBl4Bookmarks() {
  await addBl4EntriesToBookmarks(bl4SelectedEntries(), "Imported selected BL4 code(s) to bookmarks");
}

async function validateBl4ActiveSerial() {
  const row = activeBl4Entry();
  if (!row) {
    setBl4DeliveryStatus("Select a BL4 code first.", "warning");
    return false;
  }
  const validation = serialValidationMessage(row.serial);
  if (validation) {
    state.bl4ConfirmedId = "";
    state.bl4ConfirmedSerial = "";
    setBl4DeliveryStatus(validation, "bad");
    return false;
  }

  setBl4DeliveryStatus("Validating active BL4 serial locally...", "warning");
  const result = await window.msbt.validatorBasic(row.serial);
  const first = Array.isArray(result && result.results) && result.results.length ? result.results[0] : {};
  const status = String(first.status || result.status || "").toUpperCase();
  const validatorReturned = result && result.ok && result.total === 1;
  const mapped = !validatorReturned
    ? "UNCHECKED"
    : status === "LEGIT"
      ? "PASS"
      : status === "ERROR"
        ? "ERROR"
        : "FAIL";
  state.bl4Entries = state.bl4Entries.map((item) => (
    bl4EntryId(item) === bl4EntryId(row)
      ? { ...item, mattmab_validator: mapped, mattmab_validator_detail: (result && result.summary) || first.message || "" }
      : item
  ));
  state.bl4ConfirmedId = bl4EntryId(row);
  state.bl4ConfirmedSerial = row.serial;
  const summary = validatorReturned
    ? (result.summary || first.message || `Validation complete: ${status || "serial parsed"}.`)
    : "Local validator unavailable or inconclusive; confirmed exact @U serial format only.";
  const clean = validatorReturned && status === "LEGIT";
  const warningPrefix = validatorReturned && status === "ERROR"
    ? "Confirmed format, validator returned Error"
    : "Confirmed with warning";
  setBl4DeliveryStatus(clean ? `Confirmed: ${summary}` : `${warningPrefix}: ${summary}`, clean ? "ok" : "warning");
  setOutput(els.bl4Output, validatorReturned ? (result.output || summary) : { ok: true, message: summary, validator: result });
  renderBl4Codes();
  return true;
}

async function sendBl4Serial(mode) {
  const rows = bl4ValidSerialEntries(bl4SelectedEntries());
  if (!rows.length) {
    setBl4DeliveryStatus("Select a BL4 code before delivery.", "warning");
    return;
  }

  let deliveryRows = rows;
  let serialText = rows.map((row) => String(row.serial || "").trim()).join("\n");
  const overrideLevel = boolFromSelect(els.bl4OverrideLevel);
  const deliveryLevel = getInt(els.bl4DeliveryLevel, 1, 60, 60);
  let skippedByOverride = [];
  if (overrideLevel) {
    const preflight = await preflightBl4LevelOverride(rows, serialText, deliveryLevel);
    if (!preflight || !preflight.ok) return;
    deliveryRows = Array.isArray(preflight.rows) ? preflight.rows : rows;
    serialText = preflight.serialText || deliveryRows.map((row) => String(row.serial || "").trim()).join("\n");
    skippedByOverride = Array.isArray(preflight.skipped) ? preflight.skipped : [];
    if (!deliveryRows.length || !serialText.trim()) {
      setBl4DeliveryStatus("No BL4 serials remain after level-override filtering.", "bad");
      return;
    }
  }

  const destination = mode === "selected" ? (state.selectedTarget || "selected target") : mode === "all" ? "all players" : "non-host players";
  const label = deliveryRows.length === 1 ? `"${deliveryRows[0].name || "selected BL4 code"}"` : `${deliveryRows.length} selected BL4 codes`;
  const skipNote = skippedByOverride.length ? `\n\n${skippedByOverride.length} selected code(s) will be skipped because their level could not be changed.` : "";
  const confirmed = window.confirm(`Deliver ${label} to ${destination}?${skipNote}`);
  if (!confirmed) {
    setBl4DeliveryStatus("BL4 delivery cancelled.", "warning");
    return;
  }

  const actionByMode = {
    selected: "give_serial_selected",
    all: "give_serial_all",
    nonhost: "give_serial_nonhost"
  };
  setBl4DeliveryStatus(`Sending ${deliveryRows.length} BL4 serial(s) to ${destination}...`, "warning");
  setOutput(
    els.bl4Output,
    `Sending BL4 code delivery:\nAction: ${actionByMode[mode] || mode}\nDestination: ${destination}\nSerial count: ${deliveryRows.length}\n${deliveryRows.map((row) => row.name || "Selected BL4 code").join("\n")}${skippedByOverride.length ? `\n\nSkipped by level override: ${skippedByOverride.length}` : ""}`
  );
  appendActivity(`BL4 delivery: sending ${deliveryRows.length} serial(s) via ${mode}${skippedByOverride.length ? `; skipped ${skippedByOverride.length}` : ""}.`);

  const result = await sendSerialPayload(
    mode,
    serialText,
    overrideLevel,
    deliveryLevel,
    els.bl4Output
  );
  if (!result) return;
  const message = resultMessage(result);
  setBl4DeliveryStatus(actionSucceeded(result) ? `Delivery accepted: ${message}` : `Delivery failed: ${message}`, actionSucceeded(result) ? "ok" : "bad");
}

function acceptBl4CatalogResult(result) {
  state.bl4Entries = Array.isArray(result.entries) ? result.entries : [];
  state.bl4CatalogWarnings = Array.isArray(result.warnings) ? result.warnings : [];
  state.bl4SelectedIds.clear();
  state.bl4ConfirmedId = "";
  state.bl4ConfirmedSerial = "";
  const activeStillExists = state.bl4Entries.some((entry) => bl4EntryId(entry) === state.bl4ActiveId);
  if (!activeStillExists) state.bl4ActiveId = "";
  populateBl4Filters(result.filters || {});
  renderBl4Codes();
  if (state.bl4Entries.length && !state.bl4ActiveId) {
    selectBl4Entry(bl4EntryId(state.bl4Entries[0]));
  }
  return result.counts || {};
}

async function loadBl4Catalog() {
  if (!window.msbt || typeof window.msbt.loadBl4Catalog !== "function") {
    setBl4Status("BL4 catalog loader is not available in this Electron build.", "bad");
    return;
  }
  setBl4Status("Loading BL4 Codes catalog from local resources and cached GZO data...", "warning");
  const result = await window.msbt.loadBl4Catalog();
  if (!result || !result.ok) {
    state.bl4Entries = [];
    renderBl4Codes();
    setBl4Status(result && result.message ? result.message : "BL4 Codes catalog could not be loaded.", "bad");
    return;
  }
  const counts = acceptBl4CatalogResult(result);
  const warnings = state.bl4CatalogWarnings.length ? ` ${state.bl4CatalogWarnings.join(" ")}` : "";
  setBl4Status(
    `Loaded ${counts.merged || state.bl4Entries.length} local BL4 code(s): ${counts.lootlemon || 0} Lootlemon, ${counts.custom || 0} Custom Static, ${counts.gzo || 0} GZO.${warnings}`,
    state.bl4CatalogWarnings.length ? "warning" : "ok"
  );
}

async function refreshBl4GzoCatalog() {
  if (!window.msbt || typeof window.msbt.refreshGzoCatalog !== "function") {
    setBl4Status("GZO refresh is not available in this Electron build.", "bad");
    return;
  }
  if (els.bl4RefreshGzoBtn) els.bl4RefreshGzoBtn.disabled = true;
  setBl4Status("Refreshing GZO from save-editor.be and updating the local cache...", "warning");
  try {
    const result = await window.msbt.refreshGzoCatalog();
    if (!result || !result.ok) {
      setBl4Status(result && result.message ? result.message : "GZO refresh failed.", "bad");
      return;
    }
    const counts = acceptBl4CatalogResult(result);
    const warnings = state.bl4CatalogWarnings.length ? ` ${state.bl4CatalogWarnings.join(" ")}` : "";
    setBl4Status(
      `Refreshed ${result.refreshed || counts.gzo || 0} GZO code(s). Loaded ${counts.merged || state.bl4Entries.length} merged BL4 code(s): ${counts.lootlemon || 0} Lootlemon, ${counts.custom || 0} Custom Static, ${counts.gzo || 0} GZO.${warnings}`,
      state.bl4CatalogWarnings.length ? "warning" : "ok"
    );
  } catch (error) {
    setBl4Status(`GZO refresh failed: ${error && error.message ? error.message : error}`, "bad");
  } finally {
    if (els.bl4RefreshGzoBtn) els.bl4RefreshGzoBtn.disabled = false;
  }
}

function versionValue(value) {
  return value === null || value === undefined || value === "" ? "unavailable" : String(value);
}

function shortHash(value) {
  const text = String(value || "");
  return text ? text.slice(0, 10) : "no hash";
}

function installedSdkKind(installed) {
  const status = String(installed && installed.status ? installed.status : "");
  if (status === "current") return "ok";
  if (status === "different" || status === "missing" || status === "not_detected") return "warning";
  return installed && installed.available ? "ok" : "warning";
}

function renderUpdateCards(info) {
  const data = info || {};
  const remote = data.remote || data.remoteManifest || {};
  const updater = data.updateState || data.updater || state.latestUpdateState || {};
  const updaterStatus = String(updater && updater.status ? updater.status : "idle");
  const updaterMessage = updater && updater.message ? updater.message : "Installer updater has not checked yet.";
  const bundled = data.bundledSdkmod || {};
  const installed = data.installedSdkmod || {};
  const localManifest = data.localManifest || data.local || {};
  const remotePackage = remote.package_version || "";
  const remoteElectron = remote.electron_version || remote.app_version || remote.package_version || "";
  const electronNeedsUpdate = Boolean(data.electronUpdateAvailable);
  const packageNeedsUpdate = Boolean(data.packageUpdateAvailable || data.updateAvailable);

  setLine(els.electronAppCurrent, `Current: app ${versionValue(data.appVersion)} | package ${versionValue(data.packageVersion || localManifest.package_version)}`);
  setLine(
    els.electronAppLatest,
    remoteElectron ? `Latest app: ${remoteElectron}${remotePackage ? ` | package ${remotePackage}` : ""}` : "Latest app: not checked yet.",
    electronNeedsUpdate ? "warning" : packageNeedsUpdate ? "warning" : ""
  );
  setLine(
    els.electronAppInstaller,
    `Installer updater: ${updaterMessage}`,
    updaterStatus === "available" || updaterStatus === "progress" ? "warning" : updaterStatus === "error" ? "bad" : updaterStatus === "downloaded" || updaterStatus === "none" ? "ok" : ""
  );

  setLine(els.bundledSdkVersion, `Version: ${versionValue(data.sdkmodVersion || localManifest.sdkmod_version)}`);
  setLine(
    els.bundledSdkStatus,
    bundled.available ? `Bundled file: ready (${shortHash(bundled.sha256)})` : "Bundled file: missing from this app build.",
    bundled.available ? "ok" : "bad"
  );

  setLine(
    els.installedSdkStatus,
    installed.message || "Installed file: not detected yet.",
    installedSdkKind(installed)
  );
  setLine(
    els.installedSdkPath,
    installed.path ? `Path: ${installed.path}` : "Path: not detected yet.",
    installed.path ? "" : "warning"
  );
}

function sdkModNeedsAttention(data) {
  const installed = data && data.installedSdkmod ? data.installedSdkmod : {};
  const status = String(installed.status || "");
  return status === "different" || status === "missing" || status === "not_detected";
}

function updateNoticeInfo(info) {
  const data = info || {};
  const updater = data.updateState || data.updater || state.latestUpdateState || {};
  const updaterStatus = String(updater && updater.status ? updater.status : "idle");
  const remote = data.remote || data.remoteManifest || {};
  const localAppVersion = data.appVersion || "current";
  const remoteAppVersion = remote.electron_version || remote.app_version || remote.package_version || "latest";
  const localPackageVersion = data.packageVersion || data.localManifest && data.localManifest.package_version || "current";
  const remotePackageVersion = remote.package_version || "latest";
  const restartGameNote = "If the SDK mod is updated, close and restart Borderlands 4 before testing live actions.";

  if (updaterStatus === "downloaded") {
    return {
      kind: "downloaded",
      title: "Electron Update Ready",
      message: `The Electron app update has downloaded. Restart MSBT to install it. ${restartGameNote}`,
      showDownload: false,
      showInstall: true,
      showInstaller: false,
      showUpdates: true
    };
  }
  if (updaterStatus === "progress") {
    const progress = updater.progress && Number.isFinite(Number(updater.progress.percent))
      ? ` ${Number(updater.progress.percent).toFixed(1)}%`
      : "";
    return {
      kind: "progress",
      title: "Downloading Electron Update",
      message: `The Electron app update is downloading.${progress}`,
      showDownload: false,
      showInstall: false,
      showInstaller: false,
      showUpdates: true
    };
  }
  if (updaterStatus === "available") {
    return {
      kind: "app",
      title: "Electron App Update Available",
      message: `A newer Electron app is available: ${localAppVersion} -> ${remoteAppVersion}. Download it here, then restart/install when it is ready. ${restartGameNote}`,
      showDownload: true,
      showInstall: false,
      showInstaller: true,
      showUpdates: true
    };
  }
  if (data.electronUpdateAvailable) {
    return {
      kind: "app",
      title: "Electron App Update Available",
      message: `A newer Electron app is available: ${localAppVersion} -> ${remoteAppVersion}. Open the installer download to update.`,
      showDownload: false,
      showInstall: false,
      showInstaller: true,
      showUpdates: true
    };
  }
  if (data.packageUpdateAvailable || data.updateAvailable) {
    const sameVersionRebuild = Boolean(data.packageBuildChanged && localPackageVersion === remotePackageVersion);
    return {
      kind: "package",
      title: "MSBT Package Update Available",
      message: sameVersionRebuild
        ? `A newer rebuild of MSBT ${localPackageVersion} is available. Update the Electron app and bundled SDK mod together. ${restartGameNote}`
        : `A newer MSBT package is available: ${localPackageVersion} -> ${remotePackageVersion}. Update the Electron app and bundled SDK mod together. ${restartGameNote}`,
      showDownload: updaterStatus === "available",
      showInstall: updaterStatus === "downloaded",
      showInstaller: true,
      showUpdates: true
    };
  }
  if (sdkModNeedsAttention(data)) {
    const installed = data.installedSdkmod || {};
    return {
      kind: "sdk",
      title: "SDK Mod Needs Attention",
      message: `${installed.message || "Installed SDK mod does not match this app build."} Open Updates, install the bundled SDK mod, then restart Borderlands 4.`,
      showDownload: false,
      showInstall: false,
      showInstaller: false,
      showUpdates: true
    };
  }
  return null;
}

function renderBoostUpdateNotice(info) {
  if (!els.boostUpdateNotice) return;
  const notice = updateNoticeInfo(info);
  if (!notice) {
    els.boostUpdateNotice.classList.add("hidden");
    return;
  }
  els.boostUpdateNotice.classList.remove("hidden");
  els.boostUpdateNotice.dataset.kind = notice.kind || "";
  setLine(els.boostUpdateTitle, notice.title || "Update Available");
  setLine(els.boostUpdateMessage, notice.message || "A newer MSBT update is available.");
  if (els.boostUpdateDownloadBtn) els.boostUpdateDownloadBtn.classList.toggle("hidden", !notice.showDownload);
  if (els.boostUpdateInstallBtn) els.boostUpdateInstallBtn.classList.toggle("hidden", !notice.showInstall);
  if (els.boostUpdateOpenInstallerBtn) els.boostUpdateOpenInstallerBtn.classList.toggle("hidden", !notice.showInstaller);
  if (els.boostUpdateOpenUpdatesBtn) els.boostUpdateOpenUpdatesBtn.classList.toggle("hidden", !notice.showUpdates);
}

function hideStartupUpdateModal() {
  if (els.startupUpdateModal) els.startupUpdateModal.classList.add("hidden");
}

function renderStartupUpdateModal(notice) {
  if (!els.startupUpdateModal || !notice) return;
  els.startupUpdateModal.classList.remove("hidden");
  els.startupUpdateModal.dataset.kind = notice.kind || "";
  setLine(els.startupUpdateTitle, notice.title || "Update Available");
  setLine(els.startupUpdateMessage, notice.message || "A newer MSBT update is available.");
  if (els.startupUpdateDownloadBtn) els.startupUpdateDownloadBtn.classList.toggle("hidden", !notice.showDownload);
  if (els.startupUpdateInstallBtn) els.startupUpdateInstallBtn.classList.toggle("hidden", !notice.showInstall);
  if (els.startupUpdateInstallerBtn) els.startupUpdateInstallerBtn.classList.toggle("hidden", !notice.showInstaller);
  if (els.startupUpdateUpdatesTabBtn) els.startupUpdateUpdatesTabBtn.classList.toggle("hidden", !notice.showUpdates);
}

function maybeShowStartupUpdateModal(info) {
  if (state.startupUpdateNoticeShown) return;
  const notice = updateNoticeInfo(info);
  if (!notice) return;
  state.startupUpdateNoticeShown = true;
  renderStartupUpdateModal(notice);
}

function renderVersionInfo(info) {
  state.versionInfo = info || null;
  const data = info || {};
  const parts = [
    `App ${versionValue(data.appVersion)}`,
    `package ${versionValue(data.packageVersion)}`,
    `SDK mod ${versionValue(data.sdkmodVersion)}`,
    `resources ${versionValue(data.resourcesVersion)}`
  ];
  const required = data.sdkRequired ? `Requires ${data.sdkRequired}` : "Requires oak2-mod-manager v0.3";
  const text = `${parts.join(" | ")} | ${required}`;
  setLine(els.appVersionLine, text);
  setLine(els.versionSummary, text, data.bundledSdkmod && data.bundledSdkmod.available ? "ok" : "warning");
  renderUpdateCards(data);
  renderBoostUpdateNotice(data);
}

async function refreshVersionInfo() {
  if (!window.msbt || typeof window.msbt.getVersionInfo !== "function") return null;
  const info = await window.msbt.getVersionInfo();
  renderVersionInfo(info);
  if (info && info.updateState) renderUpdateState(info.updateState);
  return info;
}

function renderUpdateState(updateState) {
  state.latestUpdateState = updateState || null;
  const status = String(updateState && updateState.status ? updateState.status : "idle");
  const message = updateState && updateState.message ? updateState.message : "No Electron installer update check has run yet.";
  const progress = updateState && updateState.progress && Number.isFinite(Number(updateState.progress.percent))
    ? ` (${Number(updateState.progress.percent).toFixed(1)}%)`
    : "";
  const error = updateState && updateState.error ? ` ${updateState.error}` : "";

  if (els.updateDownloadBtn) {
    els.updateDownloadBtn.disabled = status !== "available";
  }
  if (els.updateInstallBtn) {
    els.updateInstallBtn.disabled = status !== "downloaded";
  }

  if (status === "available") {
    setLine(els.updateSummary, `${message} Click Download Electron Update when ready.`, "warning");
  } else if (status === "downloaded") {
    setLine(els.updateSummary, `${message} Click Restart / Install Downloaded Update when ready.`, "ok");
  } else if (status === "error") {
    setLine(els.updateSummary, `${message}${error}`, "bad");
  } else if (status === "progress") {
    setLine(els.updateSummary, `${message}${progress}`, "warning");
  }
  if (state.versionInfo) {
    renderUpdateCards({ ...state.versionInfo, updateState });
    renderBoostUpdateNotice({ ...state.versionInfo, updateState });
  }
}

async function checkUpdates(options = {}) {
  const startup = Boolean(options && options.startup);
  setLine(els.updateSummary, "Checking GitHub Releases...", "warning");
  await refreshVersionInfo();
  const result = await window.msbt.checkUpdates();
  setOutput(els.updateOutput, result);
  state.latestInstallerUrl = result.electronInstallerUrl || result.latestUrl || state.latestInstallerUrl;
  state.latestDownloadUrl = state.latestInstallerUrl;
  state.manualZipDownloadUrl = result.manualZipUrl || result.remote && result.remote.manual_zip_download_url || state.manualZipDownloadUrl;
  renderVersionInfo(result);
  if (result.updater) renderUpdateState(result.updater);
  if (startup) {
    maybeShowStartupUpdateModal({ ...result, updateState: result.updater });
  }
  if (!result.ok) {
    setLine(els.updateSummary, result.message || "Update check failed.", "bad");
    return;
  }
  const localVersion = result.local && result.local.package_version ? result.local.package_version : "unknown";
  const remoteVersion = result.remote && result.remote.package_version ? result.remote.package_version : "unknown";
  const localAppVersion = result.appVersion || "unknown";
  const remoteAppVersion = result.remote && (result.remote.electron_version || result.remote.app_version || result.remote.package_version)
    ? (result.remote.electron_version || result.remote.app_version || result.remote.package_version)
    : "unknown";
  const updaterStatus = String(result.updater && result.updater.status ? result.updater.status : "");
  if (["available", "downloaded", "progress"].includes(updaterStatus)) return;
  if (result.electronUpdateAvailable) {
    setLine(els.updateSummary, `Electron update available: ${localAppVersion} -> ${remoteAppVersion}`, "warning");
  } else if (result.packageUpdateAvailable) {
    const sameVersionRebuild = Boolean(result.packageBuildChanged && localVersion === remoteVersion);
    setLine(
      els.updateSummary,
      sameVersionRebuild ? `MSBT package rebuild available for ${localVersion}` : `SDK/resources update available: ${localVersion} -> ${remoteVersion}`,
      "warning"
    );
  } else {
    setLine(els.updateSummary, `Current Electron app looks up to date: ${localAppVersion}`, "ok");
  }
}

async function downloadElectronUpdate() {
  setLine(els.updateSummary, "Requesting Electron update download...", "warning");
  const result = await window.msbt.downloadUpdate();
  setOutput(els.updateOutput, result);
  if (result && result.state) renderUpdateState(result.state);
  setLine(els.updateSummary, result.message || "Electron update download request finished.", result.ok ? "ok" : "bad");
}

async function installDownloadedElectronUpdate() {
  const confirmed = window.confirm("Restart MSBT Electron Beta now and install the downloaded update?");
  if (!confirmed) return;
  const result = await window.msbt.installDownloadedUpdate();
  setOutput(els.updateOutput, result);
  setLine(els.updateSummary, result.message || "Install request finished.", result.ok ? "ok" : "bad");
}

async function detectSdkModsFolder() {
  setLine(els.sdkInstallSummary, "Detecting Borderlands 4 sdk_mods folder...", "warning");
  const result = await window.msbt.detectSdkMods();
  if (result && result.path) setTextValue(els.sdkModsPath, result.path);
  setOutput(els.updateOutput, result);
  if (result && result.installedSdkmod) {
    renderVersionInfo({ ...(state.versionInfo || {}), installedSdkmod: { ...result.installedSdkmod, sdkModsPath: result.path } });
  }
  setLine(els.sdkInstallSummary, result.message || "sdk_mods detection finished.", result.ok ? "ok" : "warning");
}

async function browseSdkModsFolder() {
  setLine(els.sdkInstallSummary, "Choose the Borderlands 4 sdk_mods folder...", "warning");
  const result = await window.msbt.browseSdkMods();
  if (result && result.path) setTextValue(els.sdkModsPath, result.path);
  setOutput(els.updateOutput, result);
  if (result && result.installedSdkmod) {
    renderVersionInfo({ ...(state.versionInfo || {}), installedSdkmod: { ...result.installedSdkmod, sdkModsPath: result.path } });
  }
  setLine(els.sdkInstallSummary, result.message || "sdk_mods folder selection finished.", result.ok ? "ok" : "warning");
}

async function installBundledSdkMod() {
  const confirmed = window.confirm("Install or replace MattsSDKBoostingTools.sdkmod and ActorScriptDeployer in the selected sdk_mods folder? Borderlands 4 must be closed.");
  if (!confirmed) return;
  setLine(els.sdkInstallSummary, "Installing bundled SDK mod files...", "warning");
  const result = await window.msbt.installSdkMod(getValue(els.sdkModsPath));
  setOutput(els.updateOutput, result);
  if (result && result.installedSdkmod) {
    renderVersionInfo({ ...(state.versionInfo || {}), installedSdkmod: { ...result.installedSdkmod, sdkModsPath: result.path } });
  }
  setLine(els.sdkInstallSummary, result.message || "SDK mod install/update finished.", result.ok ? "ok" : "bad");
}

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function renderSavedDataInfo(result) {
  if (!result || !result.ok) {
    setLine(els.savedDataSummary, result && result.message ? result.message : "Saved data check failed.", "bad");
    setOutput(els.savedDataOutput, result || "Saved data check failed.");
    return;
  }
  const files = Array.isArray(result.files) ? result.files : [];
  const found = files.filter((file) => file.exists).length;
  setLine(
    els.savedDataSummary,
    `${found}/${files.length} saved data file(s) found. Folder: ${result.path}`,
    "ok"
  );
  const lines = [
    result.message || "Saved data folder checked.",
    "",
    `Folder: ${result.path}`,
    "",
    ...files.map((file) => {
      if (!file.exists) return `${file.label}: not created yet (${file.fileName})`;
      const modified = file.modifiedAt ? ` | modified ${file.modifiedAt}` : "";
      return `${file.label}: ${formatBytes(file.size)}${modified}`;
    })
  ];
  setOutput(els.savedDataOutput, lines.join("\n"));
}

async function refreshSavedDataInfo() {
  if (!window.msbt || typeof window.msbt.getUserDataInfo !== "function") return null;
  setLine(els.savedDataSummary, "Checking saved Electron data...", "warning");
  const result = await window.msbt.getUserDataInfo();
  renderSavedDataInfo(result);
  return result;
}

async function openSavedDataFolder() {
  setLine(els.savedDataSummary, "Opening saved data folder...", "warning");
  const result = await window.msbt.openUserDataFolder();
  if (result && result.ok) {
    setLine(els.savedDataSummary, result.message || "Opened saved data folder.", "ok");
  } else {
    setLine(els.savedDataSummary, result && result.message ? result.message : "Could not open saved data folder.", "bad");
  }
  setOutput(els.savedDataOutput, result);
}

async function exportSavedDataBackup() {
  setLine(els.savedDataSummary, "Choose where to save the backup...", "warning");
  const result = await window.msbt.exportUserDataBackup();
  if (result && result.canceled) {
    setLine(els.savedDataSummary, result.message || "Backup export cancelled.", "warning");
    return;
  }
  if (result && result.ok) {
    await refreshSavedDataInfo();
    setLine(els.savedDataSummary, result.message || "Saved data backup exported.", "ok");
  } else {
    setLine(els.savedDataSummary, result && result.message ? result.message : "Backup export failed.", "bad");
  }
  setOutput(els.savedDataOutput, result);
}

function resetSerialToolsOutputs(status = "Paste a @U serial or deserialized serial text above.") {
  setTextValue(els.serialToolsDeserialized, "");
  setTextValue(els.serialToolsBreakdown, "");
  setTextValue(els.serialToolsSerialized, "");
  setLine(els.serialToolsStatus, status, "warning");
}

async function convertSerialTools(options = {}) {
  const quiet = Boolean(options && options.quiet);
  const text = getValue(els.serialToolsInput);
  const runId = ++state.serialToolsRunId;
  if (!text) {
    resetSerialToolsOutputs();
    if (!quiet) appendActivity("Serial Tools input is empty.");
    return null;
  }
  setLine(els.serialToolsStatus, "Converting locally...", "warning");
  const result = await window.msbt.serialToolsConvert(text);
  if (runId !== state.serialToolsRunId) return result;
  const ok = String(result && result.ok).toLowerCase() === "true" || result.ok === true;
  setTextValue(els.serialToolsDeserialized, result.deserialized || "");
  setTextValue(els.serialToolsBreakdown, result.breakdown || result.parts_breakdown || "");
  setTextValue(els.serialToolsSerialized, result.serialized || "");
  setLine(els.serialToolsStatus, result.message || (ok ? "Converted successfully." : "Conversion failed."), ok ? "ok" : "bad");
  if (!quiet) appendActivity(ok ? "Serial converted locally." : `Serial conversion failed: ${result.message || "unknown error"}`);
  return result;
}

function scheduleSerialToolsAutoConvert() {
  if (state.serialToolsAutoTimer) window.clearTimeout(state.serialToolsAutoTimer);
  state.serialToolsAutoTimer = window.setTimeout(() => {
    state.serialToolsAutoTimer = null;
    convertSerialTools({ quiet: true });
  }, 450);
}

function clearSerialTools() {
  if (state.serialToolsAutoTimer) window.clearTimeout(state.serialToolsAutoTimer);
  state.serialToolsAutoTimer = null;
  state.serialToolsRunId += 1;
  setTextValue(els.serialToolsInput, "");
  resetSerialToolsOutputs();
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

  const previous = new Set(state.selectedItemPools);
  if (state.selectedItemPool) previous.add(state.selectedItemPool);
  els.itempoolList.innerHTML = "";
  state.filteredItemPools.slice(0, 400).forEach((item) => {
    const option = document.createElement("option");
    option.value = item.itempool || "";
    option.textContent = `${itemPoolLabel(item)} | ${item.itempool || ""}`;
    if (previous.has(option.value)) option.selected = true;
    els.itempoolList.appendChild(option);
  });
  if (!els.itempoolList.value && els.itempoolList.options.length) {
    els.itempoolList.options[0].selected = true;
  }
  updateSelectedItemPoolsFromList();
  updateItemPoolSummary();
}

function selectedItemPoolNames() {
  const names = Array.from(state.selectedItemPools).filter(Boolean);
  if (!names.length && getValue(els.itempoolList)) names.push(getValue(els.itempoolList));
  return Array.from(new Set(names));
}

function updateSelectedItemPoolsFromList() {
  const values = Array.from(els.itempoolList.selectedOptions || [])
    .map((option) => String(option.value || "").trim())
    .filter(Boolean);
  state.selectedItemPools = new Set(values);
  state.selectedItemPool = values[0] || "";
}

function updateItemPoolSummary() {
  const selected = selectedItemPoolNames();
  const selectedLabel = selected.length === 1 ? selected[0] : `${selected.length} selected`;
  setLine(
    els.itempoolSummary,
    `${state.filteredItemPools.length} shown / ${state.itemPools.length} saved | selected: ${selected.length ? selectedLabel : "none"}`,
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
  const names = selectedItemPoolNames();
  if (!names.length) {
    setOutput(els.itempoolOutput, "Select an item pool first.");
    return;
  }
  const level = getInt(els.itempoolLevel, 1, 60, 60);
  const count = getInt(els.itempoolCount, 1, 100, 1);
  setOutput(els.itempoolOutput, `Spawning ${names.length} item pool(s)...`);

  const results = [];
  for (const name of names) {
    appendActivity(`Sending spawn_itempool for ${name}...`);
    const result = await bridgeAction("spawn_itempool", {
      itempool_name: name,
      itempool_level: level,
      itempool_count: count
    }, 30000);
    results.push({ itempool: name, result });
    appendActivity(`spawn_itempool ${name}: ${resultMessage(result)}`);
  }
  setOutput(els.itempoolOutput, {
    ok: results.every(({ result }) => actionSucceeded(result)),
    message: `Finished ${results.length} item pool spawn request(s).`,
    results
  });
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

function devActorMetadata(actorName) {
  const catalog = state.devSpawnerCatalog || {};
  const metadata = catalog.actor_metadata || {};
  return metadata[actorName] && typeof metadata[actorName] === "object" ? metadata[actorName] : {};
}

function devSpawnMetadata(actorName) {
  const catalog = state.devSpawnerCatalog || {};
  const metadata = catalog.spawn_metadata || {};
  return metadata[actorName] && typeof metadata[actorName] === "object" ? metadata[actorName] : {};
}

function devCatalogCategories() {
  const catalog = state.devSpawnerCatalog || {};
  return catalog.categories || {};
}

function devUniqueActorNames(values) {
  return Array.from(new Set((values || []).filter(Boolean).map((value) => String(value).trim()).filter(Boolean)))
    .sort((left, right) => devActorLabel(left).localeCompare(devActorLabel(right)));
}

function devActorLooksLikeCharacter(actorName) {
  return /^(Char|TESTChar|AI)_/i.test(String(actorName || ""));
}

function devActorLooksLikeInteractiveObject(actorName) {
  return /^(IO_|io_|InteractiveObject|BP_Interactive)/.test(String(actorName || ""));
}

function devAllKnownActors() {
  const catalog = state.devSpawnerCatalog || {};
  const categories = devCatalogCategories();
  const values = [];
  Object.values(categories).forEach((list) => {
    if (Array.isArray(list)) values.push(...list);
  });
  values.push(...Object.keys(catalog.display_names || {}));
  values.push(...Object.keys(catalog.favorites || {}));
  values.push(...Object.keys(catalog.actor_metadata || {}));
  values.push(...Object.keys(catalog.spawn_metadata || {}));
  values.push(...Object.keys(devMyFavoritesMap()));
  return devUniqueActorNames(values);
}

function devActorsForCategoryName(category) {
  const catalog = state.devSpawnerCatalog || {};
  const categories = devCatalogCategories();
  const actorMetadata = catalog.actor_metadata || {};
  const spawnMetadata = catalog.spawn_metadata || {};
  const values = [];

  if (category === "All") {
    return devAllKnownActors();
  }
  if (Array.isArray(categories[category])) {
    values.push(...categories[category]);
  }
  if (category === "Characters") {
    values.push(...Object.keys(actorMetadata).filter(devActorLooksLikeCharacter));
  }
  if (category === "Interactive Objects") {
    values.push(...Object.keys(spawnMetadata).filter(devActorLooksLikeInteractiveObject));
  }
  if (category === "Loot Reference") {
    values.push(...Object.keys(actorMetadata));
  }
  if (category === "IO Spawn Catalog") {
    values.push(...Object.keys(spawnMetadata));
  }

  return devUniqueActorNames(values);
}

function devMetadataSearchText(actorName) {
  const actorMeta = devActorMetadata(actorName);
  const spawnMeta = devSpawnMetadata(actorName);
  const values = [
    actorMeta.reference_display_name,
    actorMeta.display_key,
    actorMeta.true_boss_actor,
    actorMeta.parent_actor,
    actorMeta.balance_row,
    actorMeta.dedicated_drop,
    actorMeta.ai_path,
    actorMeta.ai_category,
    actorMeta.source_file,
    spawnMeta.label,
    spawnMeta.source_category,
    spawnMeta.browser_category,
    spawnMeta.command,
    spawnMeta.source
  ];
  if (actorMeta.dedicated_drop && typeof actorMeta.dedicated_drop === "object") {
    values.push(...Object.values(actorMeta.dedicated_drop));
  }
  if (Array.isArray(actorMeta.itempool_lists)) {
    values.push(actorMeta.itempool_lists.join(" "));
  }
  if (actorMeta.is_boss) values.push("boss");
  if (actorMeta.is_true_boss) values.push("true boss");
  return values.filter(Boolean).join(" ");
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
  const categories = devCatalogCategories();
  const names = Object.keys(categories).filter((category) => {
    return category !== "All" && Array.isArray(categories[category]) && categories[category].includes(actorName);
  });
  if (devActorMetadata(actorName).reference_display_name && devActorLooksLikeCharacter(actorName) && !names.includes("Characters")) {
    names.push("Characters");
  }
  if (Object.keys(devSpawnMetadata(actorName)).length && devActorLooksLikeInteractiveObject(actorName) && !names.includes("Interactive Objects")) {
    names.push("Interactive Objects");
  }
  if (Object.keys(devActorMetadata(actorName)).length && !names.includes("Loot Reference")) {
    names.push("Loot Reference");
  }
  if (Object.keys(devSpawnMetadata(actorName)).length && !names.includes("IO Spawn Catalog")) {
    names.push("IO Spawn Catalog");
  }
  return names;
}

function devActorPrimaryCategory(actorName) {
  const categories = devActorCategories(actorName);
  const sourceCategory = categories.find((category) => !["Loot Reference", "IO Spawn Catalog"].includes(category));
  return sourceCategory || categories[0] || "Other / Uncategorized";
}

function devActorExistsInCatalog(actorName) {
  const name = String(actorName || "").trim();
  if (!name) return false;
  const catalog = state.devSpawnerCatalog || {};
  const categories = devCatalogCategories();
  if (Array.isArray(categories.All) && categories.All.includes(name)) return true;
  if (Object.prototype.hasOwnProperty.call(catalog.display_names || {}, name)) return true;
  if (Object.prototype.hasOwnProperty.call(catalog.favorites || {}, name)) return true;
  if (Object.prototype.hasOwnProperty.call(catalog.actor_metadata || {}, name)) return true;
  if (Object.prototype.hasOwnProperty.call(catalog.spawn_metadata || {}, name)) return true;
  if (Object.prototype.hasOwnProperty.call(devMyFavoritesMap(), name)) return true;
  return Object.values(categories).some((list) => Array.isArray(list) && list.includes(name));
}

function devActorLabel(actorName) {
  const displayName = devActorDisplayName(actorName);
  return displayName ? `${displayName} | ${actorName}` : actorName;
}

function devNormalizeSearch(text) {
  return String(text || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function devActorSearchText(actorName) {
  const normalized = devNormalizeSearch(`${actorName} ${devActorDisplayName(actorName)} ${devActorFavoriteLabel(actorName)} ${devActorMyFavoriteLabel(actorName)} ${devActorDerivedLabel(actorName)} ${devActorCategories(actorName).join(" ")} ${devMetadataSearchText(actorName)}`);
  const compact = normalized.replace(/\s+/g, "");
  return `${normalized} ${compact}`.trim();
}

function devCategoryNames() {
  const catalog = state.devSpawnerCatalog || {};
  const categories = devCatalogCategories();
  const names = Object.keys(categories);
  if (Object.keys(catalog.actor_metadata || {}).length && !names.includes("Loot Reference")) {
    names.push("Loot Reference");
  }
  if (Object.keys(catalog.spawn_metadata || {}).length && !names.includes("IO Spawn Catalog")) {
    names.push("IO Spawn Catalog");
  }
  return names;
}

function devActorsForActiveCategory() {
  const category = state.devActiveCategory || "All";
  return devActorsForCategoryName(category);
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
  let formatted = "";
  if (Array.isArray(value)) {
    formatted = value.filter(Boolean).join(", ");
  } else if (value && typeof value === "object") {
    formatted = Object.entries(value)
      .filter((entry) => entry[1] !== undefined && entry[1] !== null && entry[1] !== "")
      .map((entry) => `${entry[0]}: ${entry[1]}`)
      .join(" | ");
  } else {
    formatted = String(value || "").trim();
  }
  detail.textContent = formatted || "Not available in catalog.";

  row.appendChild(term);
  row.appendChild(detail);
  return row;
}

function devDetailList(value) {
  if (Array.isArray(value)) {
    return value.length ? value.join(", ") : "";
  }
  return String(value || "").trim();
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
  const actorMeta = devActorMetadata(actorName);
  const spawnMeta = devSpawnMetadata(actorName);

  els.devActorDetails.appendChild(makeDevDetailRow("Display name", displayName || actorName));
  els.devActorDetails.appendChild(makeDevDetailRow("Actor key", actorName, "mono"));
  els.devActorDetails.appendChild(makeDevDetailRow("Primary category", primaryCategory));
  els.devActorDetails.appendChild(makeDevDetailRow("Alternate categories", alternateCategories.join(", ") || "None in local catalog."));
  els.devActorDetails.appendChild(makeDevDetailRow("Display source", displayName ? "Mapped display name" : "Generated from actor key fallback"));
  els.devActorDetails.appendChild(makeDevDetailRow("Runtime identifier", existsInCatalog ? "Actor key used for ASD_spawnai" : "Not present in local All catalog."));
  els.devActorDetails.appendChild(makeDevDetailRow("Catalog source", String(catalog.source || "").trim()));
  if (actorMeta.reference_display_name && actorMeta.reference_display_name !== displayName) {
    els.devActorDetails.appendChild(makeDevDetailRow("Loot reference name", actorMeta.reference_display_name));
  }
  if (actorMeta.display_key) {
    els.devActorDetails.appendChild(makeDevDetailRow("Display key", actorMeta.display_key, "mono"));
  }
  if (actorMeta.is_boss || actorMeta.is_true_boss) {
    els.devActorDetails.appendChild(makeDevDetailRow("Boss metadata", [
      actorMeta.is_boss ? "Boss" : "",
      actorMeta.is_true_boss ? "True boss" : "",
      actorMeta.true_boss_actor ? `True-boss actor: ${actorMeta.true_boss_actor}` : ""
    ].filter(Boolean).join(" | ")));
  }
  if (actorMeta.parent_actor) {
    els.devActorDetails.appendChild(makeDevDetailRow("Parent actor", actorMeta.parent_actor, "mono"));
  }
  if (actorMeta.balance_row) {
    els.devActorDetails.appendChild(makeDevDetailRow("Balance row", actorMeta.balance_row, "mono"));
  }
  if (actorMeta.dedicated_drop) {
    els.devActorDetails.appendChild(makeDevDetailRow("Dedicated drop", actorMeta.dedicated_drop));
  }
  if (devDetailList(actorMeta.itempool_lists)) {
    els.devActorDetails.appendChild(makeDevDetailRow("Item pool lists", devDetailList(actorMeta.itempool_lists), "mono"));
  }
  if (actorMeta.ai_path) {
    els.devActorDetails.appendChild(makeDevDetailRow("AI path", actorMeta.ai_path, "mono"));
  }
  if (actorMeta.ai_category) {
    els.devActorDetails.appendChild(makeDevDetailRow("AI category", actorMeta.ai_category));
  }
  if (actorMeta.source_file) {
    els.devActorDetails.appendChild(makeDevDetailRow("Reference source file", actorMeta.source_file, "mono"));
  }
  if (Object.keys(spawnMeta).length) {
    els.devActorDetails.appendChild(makeDevDetailRow("IO spawn label", spawnMeta.label || ""));
    els.devActorDetails.appendChild(makeDevDetailRow("IO source category", spawnMeta.source_category || ""));
    els.devActorDetails.appendChild(makeDevDetailRow("IO browser category", spawnMeta.browser_category || ""));
    els.devActorDetails.appendChild(makeDevDetailRow("IO catalog command", spawnMeta.command || "", "mono"));
    els.devActorDetails.appendChild(makeDevDetailRow("IO catalog source", spawnMeta.source || ""));
  }
  if (favoriteLabel) {
    els.devActorDetails.appendChild(makeDevDetailRow("Reference favorite label", favoriteLabel));
  }
  els.devActorDetails.appendChild(makeDevDetailRow("My Favorites", myFavoriteLabel ? `Saved as ${myFavoriteLabel}` : "Not saved in My Favorites."));

  const note = document.createElement("div");
  note.className = "dev-detail-note";
  note.textContent = "Details are read from local bundled catalog/reference data only. Live-confirmed status is not inferred from names.";
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
    button.textContent = `${category} (${devActorsForCategoryName(category).length})`;
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

function normalizedDevLogoText() {
  return getValue(els.devLogoText)
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .join("|");
}

function useSelectedDevActorForLogo() {
  const actorName = String(state.devSpawnerSelectedActor || getValue(els.devAiName) || getValue(els.devActorName) || "").trim();
  if (!actorName) {
    setLine(els.devSpawnerWarning, "Select an actor row before copying it into the Barrel Logo actor field.", "warning");
    return;
  }
  if (els.devLogoActor) {
    els.devLogoActor.value = actorName;
  }
  setLine(els.devSpawnerWarning, `Barrel Logo actor set to ${devActorLabel(actorName)}.`, "ok");
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
    dev_actor_delay: getFloat(els.devActorDelay, 0, 30, 1),
    dev_actor_disable_states: getValue(els.devActorDisableStates),
    dev_actor_distance: actorDistance,
    dev_actor_enable_states: getValue(els.devActorEnableStates),
    dev_actor_include_non_generated: Boolean(els.devActorIncludeNonGenerated && els.devActorIncludeNonGenerated.checked),
    dev_actor_no_activate: Boolean(els.devActorNoActivate && els.devActorNoActivate.checked),
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
    dev_ai_z_offset: actorZOffset,
    dev_logo_actor: getValue(els.devLogoActor) || "barrel",
    dev_logo_distance: getFloat(els.devLogoDistance, 0, 30000, 2500),
    dev_logo_height: getFloat(els.devLogoHeight, 0, 10000, 750),
    dev_logo_include_non_generated: Boolean(els.devLogoIncludeNonGenerated && els.devLogoIncludeNonGenerated.checked),
    dev_logo_scale: getFloat(els.devLogoScale, 0.01, 20, 0.45),
    dev_logo_spacing: getFloat(els.devLogoSpacing, 1, 1000, 70),
    dev_logo_text: normalizedDevLogoText()
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
  if (action === "dev_spawner_barrel_logo" && !normalizedDevLogoText()) {
    setOutput(els.devSpawnerOutput, "Enter one or more Barrel Logo text lines before running the command.");
    setLine(els.devSpawnerWarning, "Barrel Logo text is required.", "warning");
    return;
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

function currentTabLabel() {
  const active = document.querySelector(".tab-bar [data-tab].active");
  return active ? active.textContent.trim() : "unknown";
}

function reportField(label, value) {
  const text = String(value || "").trim();
  return `## ${label}\n${text || "_Not provided._"}`;
}

function redactReportText(value) {
  return String(value || "")
    .replace(BASE85_RE, "[redacted serial]")
    .replace(/[A-Z]:\\Users\\[^\\\r\n]+/gi, "C:\\Users\\[redacted]")
    .replace(/"name"\s*:\s*"[^"]+"/gi, '"name":"[redacted]"')
    .replace(/selected_player"\s*:\s*"[^"]*"/gi, 'selected_player":"[redacted]"');
}

function safeReportTitle() {
  const title = getValue(els.reportTitle).replace(/\s+/g, " ").trim();
  return title || (getValue(els.reportKind) === "feature" ? "Feature request" : "Bug report");
}

async function collectReportDiagnostics() {
  const lines = [];
  const versionInfo = state.versionInfo || await refreshVersionInfo() || {};
  lines.push(`App version: ${versionInfo.appVersion || "unknown"}`);
  lines.push(`Package version: ${versionInfo.packageVersion || "unknown"}`);
  lines.push(`SDK mod version: ${versionInfo.sdkmodVersion || "unknown"}`);
  lines.push(`Resources version: ${versionInfo.resourcesVersion || "unknown"}`);
  lines.push(`Electron: ${versionInfo.electronVersion || "unknown"}`);
  lines.push(`Platform: ${versionInfo.platform || "unknown"} ${versionInfo.osRelease || ""}`.trim());
  lines.push(`Packaged: ${versionInfo.packaged === true ? "yes" : "no"}`);
  lines.push(`Current tab: ${currentTabLabel()}`);

  try {
    const bridge = await window.msbt.bridgeRequest({ method: "GET", path: "/status", timeoutMs: 4000 });
    const status = bridge && bridge.data ? bridge.data : bridge;
    const diagnostics = status && status.diagnostics ? status.diagnostics : {};
    lines.push(`Bridge online: ${status && status.ok ? "yes" : "no"}`);
    lines.push(`Players loaded: ${Array.isArray(status && status.players) ? status.players.length : 0}`);
    lines.push(`Bridge queue: ${status && Number.isFinite(Number(status.queue)) ? status.queue : "unknown"}`);
    lines.push(`ActorScriptDeployer available: ${diagnostics.actor_script_deployer_available === true ? "yes" : "no"}`);
    lines.push(`BLImGui available: ${diagnostics.blimgui_available === true ? "yes" : "no"}`);
    lines.push(`unrealsdk: ${diagnostics.unrealsdk_version || "unknown"}`);
    lines.push(`pyunrealsdk: ${diagnostics.pyunrealsdk_version || "unknown"}`);
  } catch (error) {
    lines.push(`Bridge status: unavailable (${error.message || error})`);
  }

  try {
    const log = await window.msbt.readSdkLogTail({ lines: 80 });
    if (log && log.ok && log.text) {
      lines.push("");
      lines.push("Recent filtered SDK log lines:");
      lines.push(redactReportText(log.text).slice(-6000));
    }
  } catch (error) {
    lines.push(`Recent SDK log lines unavailable: ${error.message || error}`);
  }

  return redactReportText(lines.join("\n"));
}

async function buildReportPreview() {
  const kind = getValue(els.reportKind) === "feature" ? "Feature request" : "Bug report";
  const parts = [
    `# ${safeReportTitle()}`,
    `Type: ${kind}`,
    "",
    reportField("Description", getValue(els.reportDescription)),
    reportField("Reproduction Steps", getValue(els.reportSteps)),
    reportField("Expected Behavior", getValue(els.reportExpected)),
    reportField("Actual Behavior", getValue(els.reportActual)),
    reportField("Optional Notes", getValue(els.reportNotes))
  ];

  if (els.reportIncludeDiagnostics && els.reportIncludeDiagnostics.checked) {
    parts.push("## Redacted Diagnostics");
    parts.push(await collectReportDiagnostics());
  }

  const report = redactReportText(parts.join("\n\n")).slice(0, 24000);
  state.reportPreviewText = report;
  setOutput(els.reportPreview, report);
  setLine(els.reportStatus, "Report preview refreshed.", "ok");
  return report;
}

async function copyReportPreview() {
  const report = state.reportPreviewText || await buildReportPreview();
  await navigator.clipboard.writeText(report);
  setLine(els.reportStatus, "Report copied.", "ok");
}

async function saveReportPreview() {
  const report = state.reportPreviewText || await buildReportPreview();
  if (!window.msbt || typeof window.msbt.saveReportFile !== "function") {
    setLine(els.reportStatus, "Save is not available in this build.", "bad");
    return;
  }
  const result = await window.msbt.saveReportFile(report);
  setLine(els.reportStatus, result && result.message ? result.message : "Save finished.", result && result.ok ? "ok" : "warning");
}

async function openReportIssue() {
  const report = state.reportPreviewText || await buildReportPreview();
  const kind = getValue(els.reportKind) === "feature" ? "feature" : "bug";
  const url = new URL("https://github.com/funkyoushift/MattsSDKBoostingTools/issues/new");
  url.searchParams.set("title", safeReportTitle());
  url.searchParams.set("body", report.slice(0, 8000));
  url.searchParams.set("labels", kind === "feature" ? "enhancement" : "bug");
  await window.msbt.openExternal(url.toString());
  setLine(els.reportStatus, "Opened a GitHub issue draft. Review it, attach screenshots/logs if needed, then click Submit new issue on GitHub.", "ok");
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
    button.addEventListener("click", () => runBoostActionButton(button));
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
  if (els.movementTargetSelect) {
    els.movementTargetSelect.addEventListener("change", () => setTarget(els.movementTargetSelect.value));
  }
  if (els.movementSavePresetBtn) {
    els.movementSavePresetBtn.addEventListener("click", () => saveMovementSettings());
  }
  if (els.movementLoadSavedBtn) {
    els.movementLoadSavedBtn.addEventListener("click", () => loadSavedMovementPresetIntoControls());
  }
  if (els.movementAutoApplySaved) {
    els.movementAutoApplySaved.addEventListener("change", () => saveMovementSettings(
      els.movementAutoApplySaved.checked
        ? "Movement preset saved. Auto apply is enabled."
        : "Movement preset saved. Auto apply is disabled."
    ));
  }
  document.querySelectorAll("[data-movement-action]").forEach((button) => {
    button.addEventListener("click", () => runMovementAction(button.dataset.movementAction));
  });
  document.querySelectorAll("[data-movement-teleport-slot]").forEach((button) => {
    button.addEventListener("click", () => runMovementAction("movement_teleport_to_slot", {
      slot: Math.max(0, Math.min(3, parseInt(button.dataset.movementTeleportSlot, 10) || 0))
    }));
  });
  rarityControls().forEach(({ input }) => {
    if (input) input.addEventListener("input", updateRarityValueLabels);
  });
  updateRarityValueLabels();
  if (els.raritySavePresetBtn) {
    els.raritySavePresetBtn.addEventListener("click", () => saveRaritySettings());
  }
  if (els.rarityLoadPresetBtn) {
    els.rarityLoadPresetBtn.addEventListener("click", loadSavedRarityPresetIntoControls);
  }
  if (els.rarityRememberPreset) {
    els.rarityRememberPreset.addEventListener("change", () => saveRaritySettings(
      els.rarityRememberPreset.checked
        ? "Rarity preset saved. It will load into the sliders on startup, but will not apply until you click Apply."
        : "Rarity preset saved. Startup loading is off; sliders will start at vanilla unless you load the preset."
    ));
  }
  document.querySelectorAll("[data-rarity-action]").forEach((button) => {
    button.addEventListener("click", () => runRarityAction(button.dataset.rarityAction));
  });

  els.serialToolsConvertBtn.addEventListener("click", convertSerialTools);
  els.serialToolsClearBtn.addEventListener("click", clearSerialTools);
  els.serialToolsInput.addEventListener("input", scheduleSerialToolsAutoConvert);
  els.copyDeserializedBtn.addEventListener("click", () => copyText(els.serialToolsDeserialized.value, els.serialToolsStatus, "Deserialized output"));
  els.copyBreakdownBtn.addEventListener("click", () => copyText(els.serialToolsBreakdown.value, els.serialToolsStatus, "Parts breakdown"));
  els.copySerializedBtn.addEventListener("click", () => copyText(els.serialToolsSerialized.value, els.serialToolsStatus, "@U serialized output"));

  els.bookmarkSearch.addEventListener("input", renderBookmarks);
  els.bookmarkGroupFilter.addEventListener("change", renderBookmarks);
  els.bookmarkNewBtn.addEventListener("click", clearBookmarkForm);
  els.bookmarkImportBtn.addEventListener("click", importBookmarkFromSerialTools);
  els.bookmarkSaveBtn.addEventListener("click", saveBookmark);
  els.bookmarkDuplicateBtn.addEventListener("click", duplicateBookmark);
  els.bookmarkDeleteBtn.addEventListener("click", deleteBookmark);
  els.bookmarkSelectAllBtn.addEventListener("click", selectAllVisibleBookmarks);
  els.bookmarkClearSelectedBtn.addEventListener("click", clearBookmarkSelection);
  els.bookmarkCopySelectedBtn.addEventListener("click", copySelectedBookmarkSerials);
  els.bookmarkValidateBtn.addEventListener("click", validateBookmarkSerial);
  els.bookmarkCopyBtn.addEventListener("click", copyBookmarkSerial);
  els.bookmarkSerial.addEventListener("input", () => invalidateBookmarkConfirmation());
  els.bookmarkTargetSelect.addEventListener("change", () => setTarget(els.bookmarkTargetSelect.value));
  els.bookmarkSetTargetBtn.addEventListener("click", () => setTarget(els.bookmarkTargetSelect.value));
  els.bookmarkRefreshPlayersBtn.addEventListener("click", bridgeStatus);
  document.querySelectorAll("[data-bookmark-send-mode]").forEach((button) => {
    button.addEventListener("click", () => sendBookmarkSerial(button.dataset.bookmarkSendMode));
  });

  els.bl4ReloadBtn.addEventListener("click", loadBl4Catalog);
  els.bl4RefreshGzoBtn.addEventListener("click", refreshBl4GzoCatalog);
  els.bl4SearchBtn.addEventListener("click", applyBl4Search);
  els.bl4SearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      applyBl4Search();
    }
  });
  [
    els.bl4ListingFilter,
    els.bl4TypeFilter,
    els.bl4ManufacturerFilter,
    els.bl4RarityFilter,
    els.bl4CreatorFilter,
    els.bl4MattmabFilter
  ].forEach((selectNode) => {
    if (selectNode) selectNode.addEventListener("change", renderBl4Codes);
  });
  document.querySelectorAll("[data-bl4-result-filter]").forEach((button) => {
    button.addEventListener("click", () => setBl4ResultFilter(button.dataset.bl4ResultFilter));
  });
  els.bl4SelectAllBtn.addEventListener("click", selectAllBl4Visible);
  els.bl4ClearSelectionBtn.addEventListener("click", clearBl4Selection);
  els.bl4CopySelectedBtn.addEventListener("click", copySelectedBl4Serials);
  els.bl4CopySerialBtn.addEventListener("click", copyBl4Serial);
  els.bl4CopyBreakdownBtn.addEventListener("click", copyBl4Breakdown);
  els.bl4BookmarkBtn.addEventListener("click", bookmarkActiveBl4Code);
  els.bl4ImportSelectedBtn.addEventListener("click", importSelectedBl4Bookmarks);
  els.bl4OpenLootlemonBtn.addEventListener("click", openBl4Lootlemon);
  if (els.bl4SubmitGzoBtn) els.bl4SubmitGzoBtn.addEventListener("click", openGzoSubmitModal);
  if (els.gzoSubmitCloseBtn) els.gzoSubmitCloseBtn.addEventListener("click", closeGzoSubmitModal);
  if (els.gzoSubmitResetBtn) els.gzoSubmitResetBtn.addEventListener("click", () => {
    const row = activeBl4Entry();
    if (row) fillGzoSubmitForm(row);
  });
  if (els.gzoSubmitImage) els.gzoSubmitImage.addEventListener("change", updateGzoSubmitImagePreview);
  if (els.gzoSubmitForm) els.gzoSubmitForm.addEventListener("submit", handleGzoSubmit);
  if (els.gzoSubmitModal) {
    els.gzoSubmitModal.addEventListener("click", (event) => {
      if (event.target === els.gzoSubmitModal) closeGzoSubmitModal();
    });
  }
  els.bl4ValidateBtn.addEventListener("click", validateBl4ActiveSerial);
  els.bl4TargetSelect.addEventListener("change", () => setTarget(els.bl4TargetSelect.value));
  els.bl4SetTargetBtn.addEventListener("click", () => setTarget(els.bl4TargetSelect.value));
  els.bl4RefreshPlayersBtn.addEventListener("click", bridgeStatus);
  document.querySelectorAll("[data-bl4-send-mode]").forEach((button) => {
    button.addEventListener("click", () => sendBl4Serial(button.dataset.bl4SendMode));
  });

  els.validatorBasicBtn.addEventListener("click", validateBasic);
  els.validatorBulkBtn.addEventListener("click", validateBulk);
  els.validatorClearBtn.addEventListener("click", clearValidator);

  document.getElementById("updateBtn").addEventListener("click", checkUpdates);
  if (els.updateDownloadBtn) els.updateDownloadBtn.addEventListener("click", downloadElectronUpdate);
  if (els.updateInstallBtn) els.updateInstallBtn.addEventListener("click", installDownloadedElectronUpdate);
  if (els.boostUpdateDownloadBtn) els.boostUpdateDownloadBtn.addEventListener("click", downloadElectronUpdate);
  if (els.boostUpdateInstallBtn) els.boostUpdateInstallBtn.addEventListener("click", installDownloadedElectronUpdate);
  if (els.boostUpdateOpenInstallerBtn) {
    els.boostUpdateOpenInstallerBtn.addEventListener("click", () => {
      window.msbt.openExternal(state.latestInstallerUrl || state.latestDownloadUrl || "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest");
    });
  }
  if (els.boostUpdateOpenUpdatesBtn) {
    els.boostUpdateOpenUpdatesBtn.addEventListener("click", () => switchTab("updates"));
  }
  if (els.startupUpdateDownloadBtn) {
    els.startupUpdateDownloadBtn.addEventListener("click", () => {
      hideStartupUpdateModal();
      downloadElectronUpdate();
    });
  }
  if (els.startupUpdateInstallBtn) {
    els.startupUpdateInstallBtn.addEventListener("click", () => {
      hideStartupUpdateModal();
      installDownloadedElectronUpdate();
    });
  }
  if (els.startupUpdateInstallerBtn) {
    els.startupUpdateInstallerBtn.addEventListener("click", () => {
      hideStartupUpdateModal();
      window.msbt.openExternal(state.latestInstallerUrl || state.latestDownloadUrl || "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest");
    });
  }
  if (els.startupUpdateUpdatesTabBtn) {
    els.startupUpdateUpdatesTabBtn.addEventListener("click", () => {
      hideStartupUpdateModal();
      switchTab("updates");
    });
  }
  if (els.startupUpdateDismissBtn) {
    els.startupUpdateDismissBtn.addEventListener("click", hideStartupUpdateModal);
  }
  if (els.reportPreviewBtn) els.reportPreviewBtn.addEventListener("click", buildReportPreview);
  if (els.reportCopyBtn) els.reportCopyBtn.addEventListener("click", copyReportPreview);
  if (els.reportSaveBtn) els.reportSaveBtn.addEventListener("click", saveReportPreview);
  if (els.reportGithubBtn) els.reportGithubBtn.addEventListener("click", openReportIssue);
  [
    els.reportKind,
    els.reportTitle,
    els.reportDescription,
    els.reportSteps,
    els.reportExpected,
    els.reportActual,
    els.reportNotes,
    els.reportIncludeDiagnostics
  ].forEach((node) => {
    if (node) node.addEventListener("input", () => {
      state.reportPreviewText = "";
      setLine(els.reportStatus, "Report changed. Refresh preview before sharing.", "warning");
    });
  });
  document.getElementById("downloadBtn").addEventListener("click", () => window.msbt.openExternal(state.latestDownloadUrl));
  const manualZipBtn = document.getElementById("manualZipBtn");
  if (manualZipBtn) manualZipBtn.addEventListener("click", () => window.msbt.openExternal(state.manualZipDownloadUrl));
  if (els.savedDataRefreshBtn) els.savedDataRefreshBtn.addEventListener("click", refreshSavedDataInfo);
  if (els.savedDataOpenBtn) els.savedDataOpenBtn.addEventListener("click", openSavedDataFolder);
  if (els.savedDataBackupBtn) els.savedDataBackupBtn.addEventListener("click", exportSavedDataBackup);
  if (els.appOpacity) {
    els.appOpacity.addEventListener("input", queueWindowOpacitySave);
    els.appOpacity.addEventListener("change", saveWindowOpacity);
  }
  const detectSdkModsBtn = document.getElementById("detectSdkModsBtn");
  if (detectSdkModsBtn) detectSdkModsBtn.addEventListener("click", detectSdkModsFolder);
  const browseSdkModsBtn = document.getElementById("browseSdkModsBtn");
  if (browseSdkModsBtn) browseSdkModsBtn.addEventListener("click", browseSdkModsFolder);
  const installSdkModBtn = document.getElementById("installSdkModBtn");
  if (installSdkModBtn) installSdkModBtn.addEventListener("click", installBundledSdkMod);
  document.getElementById("repoBtn").addEventListener("click", () => {
    window.msbt.openExternal("https://github.com/funkyoushift/MattsSDKBoostingTools");
  });
  [
    ["streamlabsBtn", "https://streamlabs.com/funkyoushift/tip"],
    ["mattmabKofiBtn", "https://ko-fi.com/mattmab"],
    ["twitchBtn", "https://www.twitch.tv/funkyoushift/"],
    ["youtubeBtn", "https://www.youtube.com/@Funkyoushift"]
  ].forEach(([buttonId, url]) => {
    const button = document.getElementById(buttonId);
    if (button) button.addEventListener("click", () => window.msbt.openExternal(url));
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
    updateSelectedItemPoolsFromList();
    updateItemPoolSummary();
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
  if (els.devLogoUseSelectedBtn) {
    els.devLogoUseSelectedBtn.addEventListener("click", useSelectedDevActorForLogo);
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
  updateDevperkToggleButtons();
  if (window.msbt && typeof window.msbt.onUpdateState === "function") {
    window.msbt.onUpdateState(renderUpdateState);
  }
  await loadWindowSettings();
  await refreshVersionInfo();
  await refreshSavedDataInfo();
  syncDevSpawnerAdvancedControls();
  await Promise.all([loadItemPools(), loadTravelResources(), loadDevSpawnerCatalog(), loadDevSpawnerFavorites(), loadSerialBookmarks(), loadBl4Catalog(), loadMovementSettings(), loadRaritySettings()]);
  await bridgeStatus();
  startBridgeStatusPolling();
  await checkUpdates({ startup: true });
}

init();
