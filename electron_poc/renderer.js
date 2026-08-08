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
  bl4RefreshCatalogsBtn: document.getElementById("bl4RefreshCatalogsBtn"),
  bl4ReloadBtn: document.getElementById("bl4ReloadBtn"),
  bl4SearchBtn: document.getElementById("bl4SearchBtn"),
  bl4SearchInput: document.getElementById("bl4SearchInput"),
  bl4SelectAllBtn: document.getElementById("bl4SelectAllBtn"),
  bl4SerialCopies: document.getElementById("bl4SerialCopies"),
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
  boostSerialCopies: document.getElementById("boostSerialCopies"),
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
  devBossPickRows: document.getElementById("devBossPickRows"),
  devBossPickSummary: document.getElementById("devBossPickSummary"),
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
  devLogoAddLineBtn: document.getElementById("devLogoAddLineBtn"),
  devLogoLines: document.getElementById("devLogoLines"),
  devLogoRemoveLineBtn: document.getElementById("devLogoRemoveLineBtn"),
  devLogoScale: document.getElementById("devLogoScale"),
  devLogoSpacing: document.getElementById("devLogoSpacing"),
  devLogoText: document.getElementById("devLogoText"),
  devLogoUseSelectedBtn: document.getElementById("devLogoUseSelectedBtn"),
  devMyFavoriteAddBtn: document.getElementById("devMyFavoriteAddBtn"),
  devMyFavoriteLabel: document.getElementById("devMyFavoriteLabel"),
  devMyFavoriteNote: document.getElementById("devMyFavoriteNote"),
  devMyFavoriteRemoveBtn: document.getElementById("devMyFavoriteRemoveBtn"),
  devMyFavoriteRows: document.getElementById("devMyFavoriteRows"),
  devMyFavoriteSaveBtn: document.getElementById("devMyFavoriteSaveBtn"),
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
  gzoSubmitClearBtn: document.getElementById("gzoSubmitClearBtn"),
  gzoSubmitCloseBtn: document.getElementById("gzoSubmitCloseBtn"),
  gzoSubmitCopyPayloadBtn: document.getElementById("gzoSubmitCopyPayloadBtn"),
  gzoSubmitCreator: document.getElementById("gzoSubmitCreator"),
  gzoSubmitDecodeBtn: document.getElementById("gzoSubmitDecodeBtn"),
  gzoSubmitDeserialized: document.getElementById("gzoSubmitDeserialized"),
  gzoSubmitForm: document.getElementById("gzoSubmitForm"),
  gzoSubmitImage: document.getElementById("gzoSubmitImage"),
  gzoSubmitImagePreview: document.getElementById("gzoSubmitImagePreview"),
  gzoSubmitListing: document.getElementById("gzoSubmitListing"),
  gzoSubmitModal: document.getElementById("gzoSubmitModal"),
  gzoSubmitName: document.getElementById("gzoSubmitName"),
  gzoSubmitNotes: document.getElementById("gzoSubmitNotes"),
  gzoSubmitPayloadPreview: document.getElementById("gzoSubmitPayloadPreview"),
  gzoSubmitRarity: document.getElementById("gzoSubmitRarity"),
  gzoSubmitResult: document.getElementById("gzoSubmitResult"),
  gzoSubmitSendBtn: document.getElementById("gzoSubmitSendBtn"),
  gzoSubmitStatus: document.getElementById("gzoSubmitStatus"),
  gzoSubmitType: document.getElementById("gzoSubmitType"),
  gzoSubmitUseEditorBtn: document.getElementById("gzoSubmitUseEditorBtn"),
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
  bookmarkSerialCopies: document.getElementById("bookmarkSerialCopies"),
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
  invRefreshBtn: document.getElementById("invRefreshBtn"),
  invCopyAllBtn: document.getElementById("invCopyAllBtn"),
  invTargetSelect: document.getElementById("invTargetSelect"),
  invGiveTargetSelect: document.getElementById("invGiveTargetSelect"),
  invSerialCopies: document.getElementById("invSerialCopies"),
  invGiveSerialBtn: document.getElementById("invGiveSerialBtn"),
  invSortDirBtn: document.getElementById("invSortDirBtn"),
  invStatus: document.getElementById("invStatus"),
  invReading: document.getElementById("invReading"),
  invEquippedGrid: document.getElementById("invEquippedGrid"),
  invFilterCount: document.getElementById("invFilterCount"),
  invSearch: document.getElementById("invSearch"),
  invRarityFilter: document.getElementById("invRarityFilter"),
  invDamageFilter: document.getElementById("invDamageFilter"),
  invTypeFilter: document.getElementById("invTypeFilter"),
  invManufacturerFilter: document.getElementById("invManufacturerFilter"),
  invBackpackCount: document.getElementById("invBackpackCount"),
  invPrevPageBtn: document.getElementById("invPrevPageBtn"),
  invNextPageBtn: document.getElementById("invNextPageBtn"),
  invPageLabel: document.getElementById("invPageLabel"),
  invBackpackGrid: document.getElementById("invBackpackGrid"),
  invDetail: document.getElementById("invDetail"),
  invDetailTitle: document.getElementById("invDetailTitle"),
  invDetailCloseBtn: document.getElementById("invDetailCloseBtn"),
  invDetailMeta: document.getElementById("invDetailMeta"),
  invDetailSerial: document.getElementById("invDetailSerial"),
  invCopySerialBtn: document.getElementById("invCopySerialBtn"),
  invSendRewardsBtn: document.getElementById("invSendRewardsBtn"),
  invOpenToolsBtn: document.getElementById("invOpenToolsBtn"),
  invOpenEditorBtn: document.getElementById("invOpenEditorBtn"),
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
  mobileGatewaySummary: document.getElementById("mobileGatewaySummary"),
  mobileGatewayCode: document.getElementById("mobileGatewayCode"),
  mobileGatewayAddress: document.getElementById("mobileGatewayAddress"),
  mobileGatewayPort: document.getElementById("mobileGatewayPort"),
  mobileGatewayDetails: document.getElementById("mobileGatewayDetails"),
  mobileGatewayQr: document.getElementById("mobileGatewayQr"),
  mobileGatewayHostSelect: document.getElementById("mobileGatewayHostSelect"),
  mobileGatewayRefreshBtn: document.getElementById("mobileGatewayRefreshBtn"),
  mobileGatewayRotateBtn: document.getElementById("mobileGatewayRotateBtn"),
  mobileGatewayCopyBtn: document.getElementById("mobileGatewayCopyBtn"),
  mobileAnnounceModal: document.getElementById("mobileAnnounceModal"),
  mobileAnnounceQr: document.getElementById("mobileAnnounceQr"),
  mobileAnnounceDontShow: document.getElementById("mobileAnnounceDontShow"),
  mobileAnnounceDismissBtn: document.getElementById("mobileAnnounceDismissBtn"),
  mobileAnnounceOpenApkBtn: document.getElementById("mobileAnnounceOpenApkBtn"),
  mobileAnnounceOpenGatewayBtn: document.getElementById("mobileAnnounceOpenGatewayBtn"),
  mobileAnnounceOpenBtn: document.getElementById("mobileAnnounceOpenBtn"),
  boostMobileAnnounceBtn: document.getElementById("boostMobileAnnounceBtn"),
  boostMobileGatewayBtn: document.getElementById("boostMobileGatewayBtn"),
  boostMobileNotice: document.getElementById("boostMobileNotice"),
  targetSelect: document.getElementById("targetSelect"),
  targetSummary: document.getElementById("targetSummary"),
  travelMapBtn: document.getElementById("travelMapBtn"),
  travelMapList: document.getElementById("travelMapList"),
  travelMapSearch: document.getElementById("travelMapSearch"),
  travelMapSummary: document.getElementById("travelMapSummary"),
  travelFavoriteAddMapBtn: document.getElementById("travelFavoriteAddMapBtn"),
  travelFavoriteAddStationBtn: document.getElementById("travelFavoriteAddStationBtn"),
  travelFavoriteLabel: document.getElementById("travelFavoriteLabel"),
  travelFavoriteNote: document.getElementById("travelFavoriteNote"),
  travelFavoriteRemoveBtn: document.getElementById("travelFavoriteRemoveBtn"),
  travelFavoriteRows: document.getElementById("travelFavoriteRows"),
  travelFavoriteSaveBtn: document.getElementById("travelFavoriteSaveBtn"),
  travelFavoriteSummary: document.getElementById("travelFavoriteSummary"),
  travelFavoriteTravelBtn: document.getElementById("travelFavoriteTravelBtn"),
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
  dataCatalogSummary: document.getElementById("dataCatalogSummary"),
  dataCatalogDetail: document.getElementById("dataCatalogDetail"),
  bl4DataCatalogStatus: document.getElementById("bl4DataCatalogStatus"),
  refreshDataCatalogsBtn: document.getElementById("refreshDataCatalogsBtn"),
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
  bl4SearchQuery: "",
  bl4SelectedIds: new Set(),
  bridgeDiagnostics: {},
  bridgeOnline: false,
  bridgeStatusPollInFlight: false,
  bridgeStatusPollTimer: null,
  boostTargetScope: "selected",
  hostPlayerIndex: null,
  invEquipped: [],
  invBackpack: [],
  invFiltered: [],
  invSort: "recent",
  invSortDir: "desc",
  invCategory: "All",
  invPage: 0,
  invPageSize: 72,
  invSelectedKey: "",
  invSelectedEntry: null,
  invReading: "",
  invTruncated: false,
  invGiveTarget: "",
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
  devSpawnerFilteredBossPicks: [],
  devSpawnerFilteredMyFavorites: [],
  devSpawnerFilteredQuickPicks: [],
  devSpawnerMyFavorites: { version: 1, favorites: {} },
  devSpawnerSelectedActor: "",
  devSpawnerWarningAccepted: false,
  devperkToggles: { "5": false, "6": false },
  editorLoadInFlight: false,
  editorLoaded: false,
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
  quickMenuPage: 0,
  quickMenuPendingAdd: null,
  quickMenuSelectedSlot: 0,
  quickMenuSnapshot: null,
  rarityRememberOnStart: false,
  raritySavedPreset: null,
  rarityBridgeRevision: null,
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
  deferredStartupUpdateInfo: null,
  deferredMobileAnnounce: false,
  travelFavorites: { version: 1, favorites: {} },
  travelFavoriteSelectedKey: "",
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

const SDK_INSTALL_RESTART_HINT =
  "Open Updates → Install/Update SDK Mod, then fully restart Borderlands 4 so the bridge loads the new .sdkmod.";

function annotateDeliveryFailureMessage(message) {
  const text = String(message || "").trim();
  if (!text) return text;
  if (/Install\/Update SDK Mod|bundled SDK mod/i.test(text)) return text;
  if (/Base85 may be corrupt|digit 0 vs letter O|Serial resolve failed/i.test(text)) {
    return `${text} ${SDK_INSTALL_RESTART_HINT}`;
  }
  return text;
}

function compareSemver(a, b) {
  const parse = (value) => String(value || "")
    .trim()
    .split("-")[0]
    .split(".")
    .map((part) => Number(part))
    .map((part) => (Number.isFinite(part) ? part : 0));
  const left = parse(a);
  const right = parse(b);
  const len = Math.max(left.length, right.length, 3);
  for (let i = 0; i < len; i += 1) {
    const l = left[i] || 0;
    const r = right[i] || 0;
    if (l > r) return 1;
    if (l < r) return -1;
  }
  return 0;
}

async function ensureLiveSdkReady(outNode) {
  // Delivery must always proceed when the bridge is reachable. SDK version /
  // install mismatch only warns — hard-blocking left users unable to send
  // serials after an Electron-only update or before a game restart.
  if (!state.bridgeOnline) {
    const statusResult = await bridgeStatus({ quiet: true });
    const statusData = statusResult && statusResult.data ? statusResult.data : statusResult;
    if (!statusResult || !statusResult.ok || !(statusData && statusData.ok)) {
      const message = "Bridge offline. Launch Borderlands 4 with MattsSDKBoostingTools loaded, then retry delivery.";
      if (outNode) setOutput(outNode, message);
      appendActivity(message);
      return { ok: false, message };
    }
  }

  const versionInfo = state.versionInfo || (typeof refreshVersionInfo === "function" ? await refreshVersionInfo() : null) || {};
  if (sdkModNeedsAttention(versionInfo)) {
    const installed = versionInfo.installedSdkmod || {};
    const message =
      `${installed.message || "Installed SDK mod does not match this app build."} ${SDK_INSTALL_RESTART_HINT}`;
    appendActivity(message);
  }

  const diagnostics = state.bridgeDiagnostics || {};
  const runningVersion = String(diagnostics.msbt_mod_version || "").trim();
  const expectedVersion = String(versionInfo.sdkmodVersion || versionInfo.packageVersion || "").trim();
  // 1.1.5+ reports msbt_mod_version. Missing/older values usually mean the game
  // process still has a pre-fix SDK loaded — warn, but do not block delivery.
  if (expectedVersion && runningVersion && compareSemver(runningVersion, expectedVersion) < 0) {
    appendActivity(
      `In-game SDK mod may be outdated (bridge reports ${runningVersion}; app expects ${expectedVersion}). ${SDK_INSTALL_RESTART_HINT}`
    );
  } else if (expectedVersion && !runningVersion) {
    appendActivity(
      `Bridge did not report msbt_mod_version (app expects ${expectedVersion}). Delivery will still proceed. ${SDK_INSTALL_RESTART_HINT}`
    );
  }
  return { ok: true, message: "" };
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
  // Bridge may return HTTP 202 with queued:true when the game tick has not
  // drained the action yet. That is still an accepted in-game command — treat
  // it as success so the UI does not immediately retry and stack stale work.
  if (data && data.queued) return true;
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
  // Prefer the bridge action payload. The IPC wrapper is often `{ ok: true, data: { ok: false, ... } }`
  // when HTTP succeeded but the in-game handler rejected the command.
  setOutput(outNode, result && result.data !== undefined ? result.data : result);
  appendActivity(`${action}: ${resultMessage(result)}`);
  return result;
}

function quickMenuData(result) {
  return result && result.data !== undefined ? result.data : result;
}

function quickMenuNode(id) {
  return document.getElementById(id);
}

function setQuickMenuStatus(message, kind = "") {
  setLine(quickMenuNode("quickMenuStatus"), message, kind);
}

function quickMenuSlotLabel(slot) {
  if (!slot) return "+ Assign";
  const action = String(slot.action || "");
  const catalog = (state.quickMenuSnapshot && state.quickMenuSnapshot.catalog) || {};
  const metadata = catalog[action] || {};
  const mode = String(slot.label_mode || "basic");
  const custom = String(slot.custom_label || "").trim();
  if (mode === "custom" && custom) return custom;
  if (mode.startsWith("alias")) {
    const index = parseInt(mode.slice(5), 10) || 0;
    const aliases = Array.isArray(metadata.aliases) ? metadata.aliases : [];
    if (aliases[index]) return String(aliases[index]);
  }
  return String(metadata.basic || action || "Assigned");
}

function quickMenuLayout() {
  return state.quickMenuSnapshot && state.quickMenuSnapshot.layout
    ? state.quickMenuSnapshot.layout
    : null;
}

function populateQuickMenuActionSelect() {
  const select = quickMenuNode("quickMenuActionSelect");
  if (!select || !state.quickMenuSnapshot) return;
  const current = select.value;
  select.innerHTML = "";
  const actions = Array.isArray(state.quickMenuSnapshot.assignable_actions)
    ? state.quickMenuSnapshot.assignable_actions
    : [];
  actions.forEach((action) => {
    const metadata = state.quickMenuSnapshot.catalog[action] || {};
    const option = document.createElement("option");
    option.value = action;
    option.textContent = String(metadata.basic || action);
    select.appendChild(option);
  });
  if (actions.includes(current)) select.value = current;
}

function quickMenuLimits() {
  const limits = (state.quickMenuSnapshot && state.quickMenuSnapshot.limits) || {};
  const maxPages = Math.max(1, Number(limits.max_pages) || 5);
  const slotsPerPage = Math.max(1, Number(limits.slots_per_page) || 21);
  const gridCols = Math.max(1, Number(limits.grid_cols) || 3);
  return { maxPages, slotsPerPage, gridCols };
}

function selectQuickMenuSlot(slotIndex) {
  const { slotsPerPage } = quickMenuLimits();
  state.quickMenuSelectedSlot = Math.max(0, Math.min(slotsPerPage - 1, Number(slotIndex) || 0));
  const layout = quickMenuLayout();
  const slot = layout && layout.pages[state.quickMenuPage]
    ? layout.pages[state.quickMenuPage][state.quickMenuSelectedSlot]
    : null;
  const select = quickMenuNode("quickMenuActionSelect");
  const label = quickMenuNode("quickMenuCustomLabel");
  const labelFocused = Boolean(label && document.activeElement === label);
  const selectFocused = Boolean(select && document.activeElement === select);
  if (select && slot && slot.action && !selectFocused) select.value = slot.action;
  if (label && !labelFocused) label.value = slot ? String(slot.custom_label || "") : "";
  const summary = quickMenuNode("quickMenuSelectedSummary");
  if (summary) {
    summary.textContent = `Page ${state.quickMenuPage + 1}, slot ${state.quickMenuSelectedSlot + 1}: ${slot ? quickMenuSlotLabel(slot) : "empty"}`;
  }
  renderQuickMenuEditor();
}

function renderQuickMenuEditor() {
  const snapshot = state.quickMenuSnapshot;
  const layout = quickMenuLayout();
  const tabs = quickMenuNode("quickMenuPageTabs");
  const grid = quickMenuNode("quickMenuSlotGrid");
  if (!snapshot || !layout || !tabs || !grid) return;
  const { maxPages, slotsPerPage, gridCols } = quickMenuLimits();

  populateQuickMenuActionSelect();
  tabs.innerHTML = "";
  for (let pageIndex = 0; pageIndex < maxPages; pageIndex += 1) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `Page ${pageIndex + 1}`;
    button.classList.toggle("active", pageIndex === state.quickMenuPage);
    button.addEventListener("click", () => {
      state.quickMenuPage = pageIndex;
      state.quickMenuSelectedSlot = 0;
      selectQuickMenuSlot(0);
    });
    tabs.appendChild(button);
  }

  const page = Array.isArray(layout.pages[state.quickMenuPage])
    ? layout.pages[state.quickMenuPage]
    : [];
  const filled = page.filter(Boolean).length;
  const title = quickMenuNode("quickMenuPageTitle");
  const pageSummary = quickMenuNode("quickMenuPageSummary");
  if (title) title.textContent = `Page ${state.quickMenuPage + 1}`;
  if (pageSummary) pageSummary.textContent = `${filled} / ${slotsPerPage} assigned`;

  grid.style.gridTemplateColumns = `repeat(${gridCols}, minmax(110px, 1fr))`;
  grid.innerHTML = "";
  for (let slotIndex = 0; slotIndex < slotsPerPage; slotIndex += 1) {
    const slot = page[slotIndex] || null;
    const button = document.createElement("button");
    button.type = "button";
    button.className = `quick-menu-slot${slot ? "" : " empty"}${slotIndex === state.quickMenuSelectedSlot ? " selected" : ""}`;
    const strong = document.createElement("strong");
    strong.textContent = `${slotIndex + 1}. ${quickMenuSlotLabel(slot)}`;
    const detail = document.createElement("span");
    detail.textContent = slot ? String(slot.action || "") : "Empty — use + QM on other tabs";
    button.append(strong, detail);
    button.addEventListener("click", () => selectQuickMenuSlot(slotIndex));
    grid.appendChild(button);
  }
}

async function loadQuickMenuLayout({ quiet = false, preserveSelection = quiet } = {}) {
  if (!window.msbt || typeof window.msbt.bridgeRequest !== "function") return null;
  if (!quiet) setQuickMenuStatus("Loading Quick Menu from the game bridge...");
  const result = await window.msbt.bridgeRequest({
    method: "GET",
    path: "/quick_menu",
    timeoutMs: 10000
  });
  const data = quickMenuData(result);
  if (!data || data.ok !== true || !data.layout) {
    setQuickMenuStatus(resultMessage(result) || "Quick Menu bridge endpoint unavailable.", "warning");
    return null;
  }

  const labelInput = quickMenuNode("quickMenuCustomLabel");
  const actionSelect = quickMenuNode("quickMenuActionSelect");
  const editingLabel = Boolean(labelInput && document.activeElement === labelInput);
  const editingAction = Boolean(actionSelect && document.activeElement === actionSelect);
  const draftLabel = editingLabel ? String(labelInput.value || "") : null;
  const draftAction = editingAction ? String(actionSelect.value || "") : null;
  const prevPage = state.quickMenuPage;
  const prevSlot = state.quickMenuSelectedSlot;

  state.quickMenuSnapshot = data;
  const { maxPages, slotsPerPage } = quickMenuLimits();

  if (preserveSelection) {
    state.quickMenuPage = Math.max(0, Math.min(maxPages - 1, Number(prevPage) || 0));
    state.quickMenuSelectedSlot = Math.max(0, Math.min(slotsPerPage - 1, Number(prevSlot) || 0));
  } else {
    const loadedPage = Number(data.layout.page);
    state.quickMenuPage = Number.isFinite(loadedPage)
      ? Math.max(0, Math.min(maxPages - 1, loadedPage))
      : Math.max(0, Math.min(maxPages - 1, state.quickMenuPage || 0));
    state.quickMenuSelectedSlot = Math.max(0, Math.min(slotsPerPage - 1, state.quickMenuSelectedSlot || 0));
  }

  // Rebuild the grid without clobbering an in-progress label/action edit.
  if (editingLabel || editingAction) {
    renderQuickMenuEditor();
    if (editingLabel && labelInput) {
      labelInput.value = draftLabel;
      try { labelInput.focus(); } catch (_) { /* ignore */ }
    }
    if (editingAction && actionSelect && draftAction) {
      actionSelect.value = draftAction;
      try { actionSelect.focus(); } catch (_) { /* ignore */ }
    }
    const summary = quickMenuNode("quickMenuSelectedSummary");
    if (summary) {
      summary.textContent = `Page ${state.quickMenuPage + 1}, slot ${state.quickMenuSelectedSlot + 1}: editing…`;
    }
  } else {
    selectQuickMenuSlot(state.quickMenuSelectedSlot);
  }

  installQuickMenuAddButtons();
  void refreshQuickMenuPinPanel({ quiet: true });
  syncQuickMenuModulesPanel();
  if (!quiet) setQuickMenuStatus(`Loaded Quick Menu revision ${data.revision || 0}.`, "ok");
  return data;
}

function quickMenuChrome() {
  const layout = quickMenuLayout();
  return layout && layout.chrome && typeof layout.chrome === "object" ? layout.chrome : {};
}

function syncQuickMenuModulesPanel() {
  const equipped = Boolean(quickMenuChrome().rarity_panel_equipped);
  const checkbox = quickMenuNode("quickMenuRarityPanelEquip");
  const status = quickMenuNode("quickMenuModulesStatus");
  if (checkbox && document.activeElement !== checkbox) {
    checkbox.checked = equipped;
  }
  if (status) {
    status.textContent = equipped
      ? "Rarity panel: equipped on F7"
      : "Rarity panel: unequipped (hidden on F7)";
    status.className = equipped ? "status-line ok compact-note" : "status-line compact-note";
  }
}

async function setQuickMenuRarityPanelEquipped(equipped) {
  const layout = quickMenuLayout();
  if (!layout) {
    setQuickMenuStatus("Load the Quick Menu from the bridge first.", "warning");
    syncQuickMenuModulesPanel();
    return null;
  }
  const chrome = { ...quickMenuChrome(), rarity_panel_equipped: Boolean(equipped) };
  setQuickMenuStatus(equipped ? "Equipping rarity sliders on F7..." : "Unequipping rarity sliders from F7...");
  const result = await bridgeAction("quick_menu_set_layout", {
    pages: layout.pages,
    page: state.quickMenuPage,
    edit_mode: layout.edit_mode,
    drop_lock: layout.drop_lock,
    chrome
  }, 20000);
  const data = quickMenuData(result);
  if (data && data.ok && data.layout) {
    if (!state.quickMenuSnapshot) state.quickMenuSnapshot = { ok: true };
    state.quickMenuSnapshot.layout = data.layout;
    state.quickMenuSnapshot.revision = data.revision || state.quickMenuSnapshot.revision;
  }
  syncQuickMenuModulesPanel();
  setOutput(quickMenuNode("quickMenuEditorOutput"), data || result);
  setQuickMenuStatus(
    resultMessage(result) || (equipped ? "Rarity panel equipped." : "Rarity panel unequipped."),
    actionSucceeded(result) ? "ok" : "warning"
  );
  return result;
}

function formatQuickMenuCommandLine(command, emptyText) {
  if (!command || !command.action) return emptyText;
  const label = command.label || command.action;
  const payload = command.payload && typeof command.payload === "object" ? command.payload : {};
  const keys = Object.keys(payload);
  const payloadText = keys.length
    ? ` | ${keys.slice(0, 4).map((key) => `${key}=${String(payload[key]).slice(0, 28)}`).join(", ")}${keys.length > 4 ? ", …" : ""}`
    : "";
  return `${label} (${command.action})${payloadText}`;
}

async function refreshQuickMenuPinPanel({ quiet = false } = {}) {
  const lastCommandNode = quickMenuNode("quickMenuLastCommand");
  const lastDropNode = quickMenuNode("quickMenuLastDrop");
  const lockNode = quickMenuNode("quickMenuLockStatus");
  if (!lastCommandNode || !lastDropNode || !lockNode) return null;
  try {
    const result = await window.msbt.bridgeRequest({ method: "GET", path: "/status", timeoutMs: 8000 });
    const data = result && result.data && typeof result.data === "object" ? result.data : result;
    if (!data || data.ok === false) {
      if (!quiet) setQuickMenuStatus(resultMessage(result) || "Could not refresh last command.", "warning");
      return null;
    }
    state.quickMenuLastCommand = data.last_command || null;
    state.quickMenuLastDrop = data.last_drop || null;
    state.quickMenuDropLock = data.drop_player_lock || null;
    lastCommandNode.textContent = `Last command: ${formatQuickMenuCommandLine(state.quickMenuLastCommand, "none yet — run an MSBT action first.")}`;
    lastCommandNode.className = state.quickMenuLastCommand ? "status-line ok" : "status-line warning";
    lastDropNode.textContent = `Last drop: ${formatQuickMenuCommandLine(state.quickMenuLastDrop, "none yet.")}`;
    const lock = state.quickMenuDropLock || {};
    const lockOn = Boolean(lock.enabled);
    const lockWho = lock.name || (lock.index != null ? `P${Number(lock.index) + 1}` : "");
    lockNode.textContent = lockOn
      ? `Lock Player: ON${lockWho ? ` → ${lockWho}` : ""}`
      : "Lock Player: off";
    return data;
  } catch (error) {
    if (!quiet) setQuickMenuStatus(`Last-command refresh failed: ${error.message || error}`, "warning");
    return null;
  }
}

async function pinLastCommandToSelectedSlot() {
  await refreshQuickMenuPinPanel({ quiet: true });
  const command = state.quickMenuLastCommand;
  if (!command || !command.action) {
    setQuickMenuStatus("No last command to pin. Run an MSBT action first.", "warning");
    return;
  }
  const catalog = state.quickMenuSnapshot && state.quickMenuSnapshot.catalog;
  if (catalog && (!catalog[command.action] || !catalog[command.action].assignable)) {
    setQuickMenuStatus(`${command.action} is not assignable to Quick Menu.`, "warning");
    return;
  }
  const basic = catalog && catalog[command.action] ? catalog[command.action].basic : command.action;
  const label = String(command.label || basic || command.action);
  const useCustom = Boolean(label) && label !== basic && label !== command.action;
  setQuickMenuStatus(`Pinning ${label} to page ${state.quickMenuPage + 1}, slot ${state.quickMenuSelectedSlot + 1}...`);
  const result = await assignQuickMenuSlot({
    page: state.quickMenuPage,
    slot: state.quickMenuSelectedSlot,
    action: command.action,
    customLabel: useCustom ? label.slice(0, 48) : "",
    commandPayload: command.payload || {}
  });
  setOutput(quickMenuNode("quickMenuEditorOutput"), quickMenuData(result) || result);
  setQuickMenuStatus(
    actionSucceeded(result)
      ? `Pinned ${label} to page ${state.quickMenuPage + 1}, slot ${state.quickMenuSelectedSlot + 1}.`
      : (resultMessage(result) || "Pin failed."),
    actionSucceeded(result) ? "ok" : "warning"
  );
  if (actionSucceeded(result)) appendActivity(`Quick Menu: pinned last command ${command.action}.`);
}

async function repeatLastDropFromQuickMenu() {
  setQuickMenuStatus("Repeating last drop...");
  const payload = {};
  if (state.selectedTarget) payload.target_player = state.selectedTarget;
  const result = await bridgeAction("repeat_last_drop", payload, 30000);
  setOutput(quickMenuNode("quickMenuEditorOutput"), result);
  setQuickMenuStatus(resultMessage(result), actionSucceeded(result) ? "ok" : "warning");
  await refreshQuickMenuPinPanel({ quiet: true });
}

async function toggleQuickMenuDropLock() {
  await refreshQuickMenuPinPanel({ quiet: true });
  const lock = state.quickMenuDropLock || {};
  const enabling = !Boolean(lock.enabled);
  const payload = {
    enabled: enabling,
    target_player: state.selectedTarget || undefined
  };
  const result = await bridgeAction("set_drop_player_lock", payload, 15000);
  setOutput(quickMenuNode("quickMenuEditorOutput"), result);
  setQuickMenuStatus(resultMessage(result), actionSucceeded(result) ? "ok" : "warning");
  await refreshQuickMenuPinPanel({ quiet: true });
}

async function assignQuickMenuSlot({ page, slot, action, customLabel = "", commandPayload = {} }) {
  const result = await bridgeAction("quick_menu_assign_slot", {
    page,
    slot,
    action,
    label_mode: customLabel.trim() ? "custom" : "basic",
    custom_label: customLabel.trim(),
    command_payload: commandPayload
  }, 20000);
  const data = quickMenuData(result);
  if (data && data.ok && data.layout) {
    state.quickMenuSnapshot.layout = data.layout;
    state.quickMenuSnapshot.revision = data.revision || state.quickMenuSnapshot.revision;
    state.quickMenuPage = page;
    state.quickMenuSelectedSlot = slot;
    renderQuickMenuEditor();
  } else if (actionSucceeded(result)) {
    setTimeout(() => loadQuickMenuLayout({ quiet: true }), 750);
  }
  return result;
}

async function saveSelectedQuickMenuSlot() {
  const action = getValue("quickMenuActionSelect");
  if (!action) {
    setQuickMenuStatus("Choose a command first.", "warning");
    return;
  }
  const layout = quickMenuLayout();
  const existing = layout && layout.pages[state.quickMenuPage]
    ? layout.pages[state.quickMenuPage][state.quickMenuSelectedSlot]
    : null;
  const currentPayload = quickMenuPayloadFromCurrentControls(action);
  const result = await assignQuickMenuSlot({
    page: state.quickMenuPage,
    slot: state.quickMenuSelectedSlot,
    action,
    customLabel: getValue("quickMenuCustomLabel"),
    commandPayload: existing && existing.action === action
      ? (existing.payload || currentPayload)
      : currentPayload
  });
  setOutput(quickMenuNode("quickMenuEditorOutput"), quickMenuData(result));
  setQuickMenuStatus(resultMessage(result), actionSucceeded(result) ? "ok" : "warning");
}

async function clearSelectedQuickMenuSlot() {
  const result = await assignQuickMenuSlot({
    page: state.quickMenuPage,
    slot: state.quickMenuSelectedSlot,
    action: ""
  });
  setOutput(quickMenuNode("quickMenuEditorOutput"), quickMenuData(result));
  setQuickMenuStatus(resultMessage(result), actionSucceeded(result) ? "ok" : "warning");
}

async function clearCurrentQuickMenuPage() {
  if (!quickMenuLayout()) return;
  const result = await bridgeAction("quick_menu_clear_page", {
    page: state.quickMenuPage
  }, 20000);
  const data = quickMenuData(result);
  if (data && data.ok && data.layout) {
    state.quickMenuSnapshot.layout = data.layout;
    state.quickMenuSnapshot.revision = data.revision || state.quickMenuSnapshot.revision;
    renderQuickMenuEditor();
  }
  setOutput(quickMenuNode("quickMenuEditorOutput"), data || result);
  setQuickMenuStatus(resultMessage(result), actionSucceeded(result) ? "ok" : "warning");
}

function quickMenuSerialPayload() {
  return {
    serial_text: getValue(els.boostSerialText),
    serial_override_level: boolFromSelect(els.boostSerialOverride),
    serial_level: getInt(els.boostSerialLevel, 1, 60, 60)
  };
}

function quickMenuBookmarkSerialPayload() {
  const entries = typeof bookmarkSelectedEntries === "function" ? bookmarkSelectedEntries() : [];
  const serials = typeof bookmarkSerialLinesForEntries === "function"
    ? bookmarkSerialLinesForEntries(entries)
    : [];
  const copies = getInt(els.bookmarkSerialCopies, 1, 50, 1);
  const expanded = expandSerialTextCopies(serials.join("\n"), copies, "Serial Bookmarks");
  return {
    serial_text: expanded.text || "",
    serial_override_level: false,
    serial_level: 60
  };
}

function quickMenuBookmarkSerialLabel() {
  const entries = typeof bookmarkSelectedEntries === "function" ? bookmarkSelectedEntries() : [];
  if (!entries.length) return "Bookmark Serial";
  if (entries.length === 1) return String(entries[0].name || "Bookmark Serial").slice(0, 48);
  return `${entries.length} Bookmarks`.slice(0, 48);
}

function quickMenuBl4SerialPayload() {
  const rows = typeof bl4ValidSerialEntries === "function" && typeof bl4SelectedEntries === "function"
    ? bl4ValidSerialEntries(bl4SelectedEntries())
    : [];
  const serialText = rows.map((row) => String(row.serial || "").trim()).filter(Boolean).join("\n");
  const copies = getInt(els.bl4SerialCopies, 1, 50, 1);
  const expanded = expandSerialTextCopies(serialText, copies, "BL4 Codes");
  return {
    serial_text: expanded.text || "",
    serial_override_level: boolFromSelect(els.bl4OverrideLevel),
    serial_level: getInt(els.bl4DeliveryLevel, 1, 60, 60)
  };
}

function quickMenuBl4SerialLabel() {
  const rows = typeof bl4ValidSerialEntries === "function" && typeof bl4SelectedEntries === "function"
    ? bl4ValidSerialEntries(bl4SelectedEntries())
    : [];
  if (!rows.length) return "BL4 Code";
  if (rows.length === 1) return String(rows[0].name || "BL4 Code").slice(0, 48);
  return `${rows.length} BL4 Codes`.slice(0, 48);
}

function quickMenuItemPoolPayload() {
  const names = selectedItemPoolNames();
  return {
    itempool_name: names[0] || getValue(els.itempoolList) || "",
    itempool_count: getInt(els.itempoolCount, 1, 100, 1),
    itempool_level: getInt(els.itempoolLevel, 1, 60, 60)
  };
}

function quickMenuTravelMapPayload() {
  return { travel_map: state.selectedMap || getValue(els.travelMapList) || "" };
}

function quickMenuTravelStationPayload() {
  return {
    travel_station: state.selectedStation || getValue(els.travelStationList) || ""
  };
}

function itemPoolDisplayName(poolName) {
  const name = String(poolName || "").trim();
  if (!name) return "Spawn Item Pool";
  const item = (state.itemPools || []).find((entry) => {
    const id = String(entry.itempool || entry.name || "").trim();
    return id === name;
  });
  const display = item && (item.display_name || item.name);
  return String(display || name).slice(0, 48);
}

function quickMenuDevSpawnerActorName() {
  return String(
    state.devSpawnerSelectedActor
    || getValue(els.devAiName)
    || getValue(els.devActorName)
    || ""
  ).trim();
}

function quickMenuDevSpawnerLabel(action, payload = {}) {
  if (action === "dev_spawner_lostloot") return "Spawn Lost Loot";
  if (action === "dev_spawner_activate_last") return "Activate Last Spawn";
  if (action === "dev_spawner_clear") return "Clear ASD Spawns";
  const name = String(
    (payload && (payload.dev_ai_name || payload.dev_actor_name))
    || quickMenuDevSpawnerActorName()
    || ""
  ).trim();
  if (!name) return action === "dev_spawner_spawn" ? "Spawn Template" : "Spawn Actor";
  const display = devActorDisplayName(name);
  return String(display || name).slice(0, 48);
}

function quickMenuDevSpawnerPayload(action) {
  const full = typeof devSpawnerPayload === "function" ? devSpawnerPayload() : {};
  const actorName = quickMenuDevSpawnerActorName();
  if (action === "dev_spawner_spawnai") {
    return {
      dev_ai_name: actorName || full.dev_ai_name || "",
      dev_ai_count: full.dev_ai_count,
      dev_ai_distance: full.dev_ai_distance,
      dev_ai_spacing: full.dev_ai_spacing,
      dev_ai_scale: full.dev_ai_scale,
      dev_ai_z_offset: full.dev_ai_z_offset,
      dev_ai_load: full.dev_ai_load,
      dev_ai_direct_only: full.dev_ai_direct_only
    };
  }
  if (action === "dev_spawner_spawn" || action === "dev_spawner_lostloot") {
    return {
      dev_actor_name: actorName || full.dev_actor_name || "",
      dev_actor_class: full.dev_actor_class,
      dev_actor_count: full.dev_actor_count,
      dev_actor_distance: full.dev_actor_distance,
      dev_actor_spacing: full.dev_actor_spacing,
      dev_actor_scale: full.dev_actor_scale,
      dev_actor_z_offset: full.dev_actor_z_offset,
      dev_actor_delay: full.dev_actor_delay,
      dev_actor_enable_states: full.dev_actor_enable_states,
      dev_actor_disable_states: full.dev_actor_disable_states,
      dev_actor_no_activate: full.dev_actor_no_activate,
      dev_actor_include_non_generated: full.dev_actor_include_non_generated
    };
  }
  return {};
}

function quickMenuPayloadFromCurrentControls(action) {
  if (action === "give_currency") {
    return {
      currency_kind: getValue(els.currencyKind),
      amount: getInt(els.currencyAmount, 0, 2147483647, 1000000)
    };
  }
  if (action === "set_level") {
    return {
      xp_track: getValue(els.xpTrack),
      level: getInt(els.xpLevel, 1, 9999999, 60)
    };
  }
  if (action === "set_backpack_bank_selected" || action === "set_backpack_bank_all") {
    return inventoryPayload(true);
  }
  if (action === "spawn_itempool") {
    return quickMenuItemPoolPayload();
  }
  if (
    action === "give_serial_selected"
    || action === "give_serial_all"
    || action === "give_serial_nonhost"
  ) {
    return quickMenuSerialPayload();
  }
  if (action === "travel_to_map") {
    return quickMenuTravelMapPayload();
  }
  if (action === "travel_to_station") {
    return quickMenuTravelStationPayload();
  }
  if (action === "movement_apply_all") {
    return movementPayload();
  }
  if (action === "movement_set_time") {
    return {
      movement_time_dilation: getFloat(els.movementTimeDilation, 0.01, 64, 1)
    };
  }
  if (
    action === "movement_infinite_jump_selected_on"
    || action === "movement_infinite_jump_selected_off"
    || action === "movement_infinite_jump_toggle_selected"
  ) {
    const selectedTarget = getValue(els.movementTargetSelect) || state.selectedTarget;
    return { target_player: selectedTarget, infinite_jump_target: selectedTarget };
  }
  if (action === "rarity_apply") {
    return rarityPayload();
  }
  if (
    action === "dev_spawner_spawnai"
    || action === "dev_spawner_spawn"
    || action === "dev_spawner_lostloot"
  ) {
    return quickMenuDevSpawnerPayload(action);
  }
  return {};
}

function fillQuickMenuAddSelectors() {
  const pageSelect = quickMenuNode("quickMenuAddPage");
  const slotSelect = quickMenuNode("quickMenuAddSlot");
  if (!pageSelect || !slotSelect) return;
  const { maxPages, slotsPerPage } = quickMenuLimits();
  pageSelect.innerHTML = "";
  slotSelect.innerHTML = "";
  for (let index = 0; index < maxPages; index += 1) {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `Page ${index + 1}`;
    pageSelect.appendChild(option);
  }
  for (let index = 0; index < slotsPerPage; index += 1) {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `Slot ${index + 1}`;
    slotSelect.appendChild(option);
  }
}

function updateQuickMenuAddSlotsForPage() {
  const layout = quickMenuLayout();
  const pageSelect = quickMenuNode("quickMenuAddPage");
  const slotSelect = quickMenuNode("quickMenuAddSlot");
  if (!layout || !pageSelect || !slotSelect) return;
  const { maxPages } = quickMenuLimits();
  const page = Math.max(0, Math.min(maxPages - 1, parseInt(pageSelect.value, 10) || 0));
  const slots = layout.pages[page] || [];
  Array.from(slotSelect.options).forEach((option, index) => {
    option.textContent = `Slot ${index + 1}${slots[index] ? ` — replace ${quickMenuSlotLabel(slots[index])}` : " — empty"}`;
  });
  const empty = slots.findIndex((slot) => !slot);
  if (empty >= 0) slotSelect.value = String(empty);
}

function closeQuickMenuAddModal() {
  const modal = quickMenuNode("quickMenuAddModal");
  if (modal) modal.classList.add("hidden");
  state.quickMenuPendingAdd = null;
}

async function ensureQuickMenuSnapshotForPin() {
  if (state.quickMenuSnapshot && state.quickMenuSnapshot.catalog) return state.quickMenuSnapshot;
  await loadQuickMenuLayout({ quiet: true });
  return state.quickMenuSnapshot;
}

function openQuickMenuAddModal(action, commandPayload = {}, label = "") {
  void (async () => {
    const snapshot = await ensureQuickMenuSnapshotForPin();
    if (!snapshot || !snapshot.catalog || !snapshot.catalog[action]) {
      setQuickMenuStatus(
        `Quick Menu bridge is offline or ${action} is not assignable. Open ★ Quick Menu after the game is in-world.`,
        "warning"
      );
      switchTab("quick-menu");
      return;
    }
    state.quickMenuPendingAdd = { action, commandPayload: { ...commandPayload } };
    fillQuickMenuAddSelectors();
    const pageSelect = quickMenuNode("quickMenuAddPage");
    if (pageSelect) pageSelect.value = String(state.quickMenuPage);
    updateQuickMenuAddSlotsForPage();
    const title = quickMenuNode("quickMenuAddTitle");
    const description = quickMenuNode("quickMenuAddDescription");
    const custom = quickMenuNode("quickMenuAddLabel");
    const metadata = snapshot.catalog[action] || {};
    if (title) title.textContent = `Add ${label || metadata.basic || action}`;
    if (description) description.textContent = `Pin ${action} with today's settings.`;
    if (custom) custom.value = String(label || "").trim().slice(0, 48);
    setLine(quickMenuNode("quickMenuAddStatus"), "Choose a page and slot.", "");
    quickMenuNode("quickMenuAddModal").classList.remove("hidden");
  })();
}

function openSerialQuickMenuPin(source, mode) {
  const actionByMode = {
    selected: "give_serial_selected",
    all: "give_serial_all",
    nonhost: "give_serial_nonhost"
  };
  const action = actionByMode[String(mode || "selected")];
  if (!action) return;
  if (source === "bookmark") {
    const payload = quickMenuBookmarkSerialPayload();
    if (!String(payload.serial_text || "").trim()) {
      setBookmarkStatus("Select one or more bookmarks before + QM.", "warning");
      return;
    }
    openQuickMenuAddModal(action, payload, quickMenuBookmarkSerialLabel());
    return;
  }
  if (source === "bl4") {
    const payload = quickMenuBl4SerialPayload();
    if (!String(payload.serial_text || "").trim()) {
      setBl4DeliveryStatus("Select one or more BL4 codes before + QM.", "warning");
      return;
    }
    openQuickMenuAddModal(action, payload, quickMenuBl4SerialLabel());
  }
}

async function confirmQuickMenuAdd() {
  const pending = state.quickMenuPendingAdd;
  if (!pending) return;
  const { maxPages, slotsPerPage } = quickMenuLimits();
  const page = getInt("quickMenuAddPage", 0, maxPages - 1, 0);
  const slot = getInt("quickMenuAddSlot", 0, slotsPerPage - 1, 0);
  setLine(quickMenuNode("quickMenuAddStatus"), "Saving to the game bridge...");
  const result = await assignQuickMenuSlot({
    page,
    slot,
    action: pending.action,
    customLabel: getValue("quickMenuAddLabel"),
    commandPayload: pending.commandPayload
  });
  setLine(
    quickMenuNode("quickMenuAddStatus"),
    resultMessage(result),
    actionSucceeded(result) ? "ok" : "warning"
  );
  if (actionSucceeded(result)) {
    appendActivity(`Quick Menu: added ${pending.action} to page ${page + 1}, slot ${slot + 1}.`);
    state.quickMenuPage = page;
    state.quickMenuSelectedSlot = slot;
    setTimeout(() => {
      closeQuickMenuAddModal();
      switchTab("quick-menu");
      selectQuickMenuSlot(slot);
      setQuickMenuStatus(`Pinned ${pending.action} to page ${page + 1}, slot ${slot + 1}.`, "ok");
    }, 350);
  }
}

function decorateQuickMenuActionButton(button, action, payloadFactory = () => ({}), labelFactory = null) {
  if (!button || button.dataset.qmDecorated === "true") return;
  const catalog = state.quickMenuSnapshot && state.quickMenuSnapshot.catalog;
  if (!catalog || !catalog[action] || !catalog[action].assignable) return;
  button.dataset.qmDecorated = "true";
  const parent = button.parentNode;
  if (!parent) return;
  const wrapper = document.createElement("span");
  wrapper.className = "qm-action-wrap";
  parent.insertBefore(wrapper, button);
  wrapper.appendChild(button);
  const add = document.createElement("button");
  add.type = "button";
  add.className = "qm-add-button secondary";
  add.textContent = "+ QM";
  add.title = `Add ${catalog[action].basic || action} to Quick Menu`;
  add.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const payload = payloadFactory() || {};
    const suggested = typeof labelFactory === "function"
      ? labelFactory(payload)
      : (catalog[action].basic || action);
    openQuickMenuAddModal(action, payload, suggested || catalog[action].basic || action);
  });
  wrapper.appendChild(add);
}

function installQuickMenuAddButtons() {
  if (!state.quickMenuSnapshot) return;
  document.querySelectorAll("[data-action]").forEach((button) => {
    decorateQuickMenuActionButton(button, String(button.dataset.action || ""));
  });
  document.querySelectorAll("[data-movement-action]").forEach((button) => {
    const action = String(button.dataset.movementAction || "");
    if (action === "movement_apply_all") {
      decorateQuickMenuActionButton(button, action, () => movementPayload());
      return;
    }
    if (action === "movement_set_time") {
      decorateQuickMenuActionButton(button, action, () => ({
        movement_time_dilation: getFloat(els.movementTimeDilation, 0.01, 64, 1)
      }));
      return;
    }
    if (
      action === "movement_infinite_jump_selected_on"
      || action === "movement_infinite_jump_selected_off"
      || action === "movement_infinite_jump_toggle_selected"
    ) {
      decorateQuickMenuActionButton(button, action, () => {
        const selectedTarget = getValue(els.movementTargetSelect) || state.selectedTarget;
        return { target_player: selectedTarget, infinite_jump_target: selectedTarget };
      });
      return;
    }
    decorateQuickMenuActionButton(button, action);
  });
  document.querySelectorAll("[data-rarity-action]").forEach((button) => {
    const action = String(button.dataset.rarityAction || "");
    if (action === "rarity_apply") {
      decorateQuickMenuActionButton(button, action, () => rarityPayload());
      return;
    }
    decorateQuickMenuActionButton(button, action);
  });
  document.querySelectorAll("[data-boost-serial-mode]").forEach((button) => {
    const mode = String(button.dataset.boostSerialMode || "selected");
    const action = {
      selected: "give_serial_selected",
      all: "give_serial_all",
      nonhost: "give_serial_nonhost"
    }[mode];
    if (!action) return;
    decorateQuickMenuActionButton(button, action, () => quickMenuSerialPayload());
  });
  document.querySelectorAll("[data-bookmark-send-mode]").forEach((button) => {
    const mode = String(button.dataset.bookmarkSendMode || "selected");
    const action = {
      selected: "give_serial_selected",
      all: "give_serial_all",
      nonhost: "give_serial_nonhost"
    }[mode];
    if (!action) return;
    decorateQuickMenuActionButton(
      button,
      action,
      () => quickMenuBookmarkSerialPayload(),
      () => quickMenuBookmarkSerialLabel()
    );
  });
  document.querySelectorAll("[data-bl4-send-mode]").forEach((button) => {
    const mode = String(button.dataset.bl4SendMode || "selected");
    const action = {
      selected: "give_serial_selected",
      all: "give_serial_all",
      nonhost: "give_serial_nonhost"
    }[mode];
    if (!action) return;
    decorateQuickMenuActionButton(
      button,
      action,
      () => quickMenuBl4SerialPayload(),
      () => quickMenuBl4SerialLabel()
    );
  });
  decorateQuickMenuActionButton(
    quickMenuNode("giveCurrencyBtn"),
    "give_currency",
    () => ({
      currency_kind: getValue(els.currencyKind),
      amount: getInt(els.currencyAmount, 0, 2147483647, 1000000)
    })
  );
  decorateQuickMenuActionButton(
    quickMenuNode("setLevelBtn"),
    "set_level",
    () => ({
      xp_track: getValue(els.xpTrack),
      level: getInt(els.xpLevel, 1, 9999999, 60)
    })
  );
  decorateQuickMenuActionButton(
    quickMenuNode("setInventorySelectedBtn"),
    "set_backpack_bank_selected",
    () => inventoryPayload(true)
  );
  decorateQuickMenuActionButton(
    quickMenuNode("setInventoryAllBtn"),
    "set_backpack_bank_all",
    () => inventoryPayload(true)
  );
  decorateQuickMenuActionButton(quickMenuNode("kickTargetBtn"), "kick_player");
  decorateQuickMenuActionButton(
    document.getElementById("spawnItempoolBtn"),
    "spawn_itempool",
    () => quickMenuItemPoolPayload(),
    (payload) => itemPoolDisplayName(payload.itempool_name)
  );
  decorateQuickMenuActionButton(
    document.getElementById("travelMapBtn"),
    "travel_to_map",
    () => quickMenuTravelMapPayload(),
    (payload) => {
      const map = (state.maps || []).find((entry) => (entry.map || entry.map_key) === payload.travel_map);
      return map ? mapLabel(map) : (payload.travel_map || "Travel Map");
    }
  );
  decorateQuickMenuActionButton(
    document.getElementById("travelStationBtn"),
    "travel_to_station",
    () => quickMenuTravelStationPayload(),
    (payload) => {
      const station = (state.stations || []).find((entry) => {
        const id = entry.station || entry.station_name || "";
        return id === payload.travel_station;
      });
      return station ? stationLabel(station) : (payload.travel_station || "Travel Station");
    }
  );
  document.querySelectorAll("[data-dev-spawner-action]").forEach((button) => {
    const action = String(button.dataset.devSpawnerAction || "");
    if (
      action !== "dev_spawner_spawnai"
      && action !== "dev_spawner_spawn"
      && action !== "dev_spawner_lostloot"
      && action !== "dev_spawner_activate_last"
      && action !== "dev_spawner_clear"
    ) {
      return;
    }
    decorateQuickMenuActionButton(
      button,
      action,
      () => quickMenuDevSpawnerPayload(action),
      (payload) => quickMenuDevSpawnerLabel(action, payload)
    );
  });
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
  const result = PLAYER_SCOPED_BOOST_ACTIONS.has(action)
    ? await runScopedPlayerAction(action, {}, els.boostOutput, 30000)
    : await runAction(action, {}, els.boostOutput, 30000);
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

function rarityWeightsToPercentPreset(weights) {
  const preset = {};
  if (!weights || typeof weights !== "object") return preset;
  ["common", "uncommon", "rare", "epic", "legendary", "pearlescent"].forEach((key) => {
    if (!Object.prototype.hasOwnProperty.call(weights, key)) return;
    const raw = Number(weights[key]);
    if (!Number.isFinite(raw)) return;
    // Backend stores 0-1 multipliers; accept accidental 0-100 payloads too.
    const pct = raw > 1.0001 ? raw : raw * 100;
    preset[key] = Math.max(0, Math.min(100, Math.round(pct)));
  });
  return preset;
}

function syncBoostingRaritySlidersFromBridge(data, { force = false } = {}) {
  const weights = data && data.rarity_weights && typeof data.rarity_weights === "object"
    ? data.rarity_weights
    : null;
  if (!weights || !Object.keys(weights).length) return false;

  const revRaw = Number(data.rarity_revision);
  const hasRev = Number.isFinite(revRaw);
  if (!force && hasRev && state.rarityBridgeRevision != null && Number(state.rarityBridgeRevision) === revRaw) {
    return false;
  }

  const editingRarity = rarityControls().some(({ input }) => input && document.activeElement === input);
  if (editingRarity && !force) return false;

  const preset = rarityWeightsToPercentPreset(weights);
  if (!Object.keys(preset).length) return false;

  let changed = false;
  rarityControls().forEach(({ key, input, value }) => {
    if (!input || !Object.prototype.hasOwnProperty.call(preset, key)) return;
    const pct = Math.max(0, Math.min(100, Number(preset[key]) || 0));
    if (String(input.value) !== String(pct)) {
      input.value = String(pct);
      changed = true;
    }
    if (value) value.textContent = `${pct}%`;
  });
  if (hasRev) state.rarityBridgeRevision = revRaw;
  if (changed && els.rarityStatus) {
    const note = "Synced from in-game Quick Menu / bridge.";
    if (!String(els.rarityStatus.textContent || "").includes("Sending")) {
      setLine(els.rarityStatus, note, "ok");
    }
  }
  return true;
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
  // Pull canonical backend weights so Boosting matches F7 / persisted state.
  try {
    const statusResult = await window.msbt.bridgeRequest({ method: "GET", path: "/status", timeoutMs: 8000 });
    const data = statusResult && statusResult.data && typeof statusResult.data === "object"
      ? statusResult.data
      : statusResult;
    if (data && data.ok !== false) {
      syncBoostingRaritySlidersFromBridge(data, { force: true });
    }
  } catch (_) { /* ignore refresh failures */ }
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
  if (Object.prototype.hasOwnProperty.call(status, "host_player_index")) {
    const hostRaw = status.host_player_index;
    state.hostPlayerIndex = hostRaw === null || hostRaw === undefined || hostRaw === ""
      ? null
      : Number(hostRaw);
    if (!Number.isFinite(state.hostPlayerIndex)) state.hostPlayerIndex = null;
  }
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

  const fillSelect = (selectNode, preferredValue = null) => {
    if (!selectNode) return;
    const previous = preferredValue !== null && preferredValue !== undefined
      ? String(preferredValue)
      : String(selectNode.value || "");
    const fallback = String(state.selectedTarget || "");
    selectNode.innerHTML = "";
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = state.players.length ? "Choose player" : "No players loaded";
    selectNode.appendChild(blank);

    let matched = false;
    state.players.forEach((player) => {
      const option = document.createElement("option");
      option.value = playerValue(player);
      option.textContent = playerLabel(player);
      const value = String(option.value);
      if (previous && value === previous) {
        option.selected = true;
        matched = true;
      }
      selectNode.appendChild(option);
    });
    if (!matched && fallback) {
      const fallbackOption = Array.from(selectNode.options).find((option) => String(option.value) === fallback);
      if (fallbackOption) fallbackOption.selected = true;
    }
  };

  fillSelect(els.targetSelect, state.selectedTarget);
  fillSelect(els.bookmarkTargetSelect, state.selectedTarget);
  fillSelect(els.bl4TargetSelect, state.selectedTarget);
  fillSelect(els.movementTargetSelect, els.movementTargetSelect && els.movementTargetSelect.value);
  // Inventory viewing vs give-to stay independent of each other and of Boosting target.
  fillSelect(els.invTargetSelect, els.invTargetSelect && els.invTargetSelect.value);
  fillSelect(
    els.invGiveTargetSelect,
    (els.invGiveTargetSelect && els.invGiveTargetSelect.value) || state.invGiveTarget || state.selectedTarget
  );
  if (els.invGiveTargetSelect) {
    state.invGiveTarget = String(els.invGiveTargetSelect.value || "");
  }

  updateBoostTargetSummary();
  const selectedPlayer = state.players.find((player) => String(playerValue(player)) === String(state.selectedTarget));
  const text = `Selected target: ${selectedPlayer ? playerLabel(selectedPlayer) : state.selectedTarget || "none"}`;
  const kind = state.selectedTarget ? "ok" : "warning";
  setLine(els.bookmarkTargetSummary, text, kind);
  setLine(els.bl4TargetSummary, text, kind);
  setLine(els.movementStatus, text, kind);
  const viewPlayer = state.players.find(
    (player) => String(playerValue(player)) === String((els.invTargetSelect && els.invTargetSelect.value) || "")
  );
  if (els.invReading && !state.invEquipped.length && !state.invBackpack.length) {
    els.invReading.textContent = viewPlayer
      ? `Reading: ${playerLabel(viewPlayer)} (press Refresh)`
      : selectedPlayer
        ? `Reading: ${playerLabel(selectedPlayer)} (press Refresh)`
        : "Reading: none";
  }
}

const PLAYER_SCOPED_BOOST_ACTIONS = new Set([
  "max_all",
  "max_currency",
  "max_eridium",
  "max_player_level",
  "max_spec_level",
  "max_sdu"
]);

function boostScopeLabel(scope = state.boostTargetScope) {
  if (scope === "all") return "All players";
  if (scope === "nonhost") return "Non-host players";
  return "Selected player";
}

function playersForBoostScope(scope = state.boostTargetScope) {
  const list = Array.isArray(state.players) ? state.players : [];
  if (scope === "all") return list.slice();
  if (scope === "nonhost") {
    if (state.hostPlayerIndex === null || state.hostPlayerIndex === undefined) {
      return list.length > 1 ? list.slice(1) : [];
    }
    return list.filter((player) => Number(player && player.index) !== Number(state.hostPlayerIndex));
  }
  const selected = list.find((player) => String(playerValue(player)) === String(state.selectedTarget));
  return selected ? [selected] : [];
}

function updateBoostTargetSummary() {
  const selectedPlayer = state.players.find((player) => String(playerValue(player)) === String(state.selectedTarget));
  const scope = state.boostTargetScope || "selected";
  const scoped = playersForBoostScope(scope);
  let text = `Boost scope: ${boostScopeLabel(scope)}`;
  if (scope === "selected") {
    text += ` | ${selectedPlayer ? playerLabel(selectedPlayer) : state.selectedTarget || "none"}`;
  } else {
    text += ` (${scoped.length} player${scoped.length === 1 ? "" : "s"})`;
    if (selectedPlayer) text += ` | dropdown: ${playerLabel(selectedPlayer)}`;
    if (scope === "nonhost" && (state.hostPlayerIndex === null || state.hostPlayerIndex === undefined)) {
      text += " | host index unknown — using players after first as non-host fallback";
    }
  }
  const kind = scope === "selected"
    ? (state.selectedTarget ? "ok" : "warning")
    : (scoped.length ? "ok" : "warning");
  setLine(els.targetSummary, text, kind);
  document.querySelectorAll("[data-boost-scope]").forEach((button) => {
    button.classList.toggle("active-scope", button.dataset.boostScope === scope);
  });
}

function setBoostTargetScope(scope) {
  const next = String(scope || "selected").toLowerCase();
  state.boostTargetScope = next === "all" || next === "nonhost" ? next : "selected";
  updateBoostTargetSummary();
  appendActivity(`Boost target scope set to ${boostScopeLabel(state.boostTargetScope)}.`);
}

async function runScopedPlayerAction(action, payload = {}, outNode = els.boostOutput, timeoutMs = 30000) {
  const scope = state.boostTargetScope || "selected";
  if (scope === "selected") {
    const ok = await ensureSelectedTarget(outNode);
    if (!ok) return { ok: false, message: "No party player selected." };
    return runAction(action, payload, outNode, timeoutMs);
  }

  const targets = playersForBoostScope(scope);
  if (!targets.length) {
    const message = scope === "nonhost"
      ? "No non-host party players found. Refresh Status while others are loaded in."
      : "No party players found. Refresh Status first.";
    if (outNode) setOutput(outNode, message);
    appendActivity(message);
    return { ok: false, message };
  }

  const lines = [`Running ${action} for ${boostScopeLabel(scope)} (${targets.length})...`];
  if (outNode) setOutput(outNode, lines.join("\n"));
  appendActivity(lines[0]);

  let okCount = 0;
  let failCount = 0;
  for (const player of targets) {
    const label = playerLabel(player);
    const targetValue = playerValue(player);
    const setResult = await setTarget(targetValue, { keepBoostScope: true });
    if (!actionSucceeded(setResult)) {
      failCount += 1;
      lines.push(`${label}: could not set target — ${resultMessage(setResult)}`);
      continue;
    }
    const result = await runAction(action, payload, outNode, timeoutMs);
    if (actionSucceeded(result)) {
      okCount += 1;
      lines.push(`${label}: ${resultMessage(result)}`);
    } else {
      failCount += 1;
      lines.push(`${label}: FAILED — ${resultMessage(result)}`);
    }
  }

  const summary = `${action} finished for ${boostScopeLabel(scope)}: ${okCount} ok, ${failCount} failed.`;
  lines.push(summary);
  if (outNode) setOutput(outNode, lines.join("\n"));
  appendActivity(summary);
  return { ok: failCount === 0 && okCount > 0, message: summary, okCount, failCount };
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

function buildMobilePairingPayload(info, preferredHost = "") {
  const addresses = Array.isArray(info && info.lanAddresses)
    ? info.lanAddresses.map((value) => String(value || "").trim()).filter(Boolean)
    : [];
  const preferred = String(preferredHost || "").trim();
  const hosts = preferred && addresses.includes(preferred)
    ? [preferred, ...addresses.filter((address) => address !== preferred)]
    : addresses.slice();
  return {
    v: 1,
    name: String((info && info.computerName) || "").trim() || "MSBT PC",
    hosts,
    port: Number(info && info.port) > 0 ? Number(info.port) : 49775,
    code: String((info && info.pairingCode) || "").trim()
  };
}

function formatMobileGatewayDetails(info, preferredHost = "") {
  const payload = buildMobilePairingPayload(info, preferredHost);
  const addresses = payload.hosts;
  const primary = addresses[0] || "(no LAN IPv4 detected — check Wi‑Fi)";
  const lines = [
    "MSBT Mobile Gateway pairing",
    "",
    `PC name: ${payload.name}`,
    `PC address: ${primary}`,
    addresses.length > 1 ? `Other LAN IPs: ${addresses.slice(1).join(", ")}` : "",
    `Gateway port: ${payload.port}`,
    `Pairing code: ${payload.code || "------"}`,
    "",
    "Easiest: open MSBT Mobile → More → Connection Settings → Scan QR to pair.",
    "Manual: enter address, port, and pairing code, then Save → Connect / Test.",
    "Phone and PC must be on the same Wi‑Fi. Allow Windows Firewall for Node/Electron on port 49775 if prompted.",
    "Keep Borderlands 4 running with the MSBT SDK mod so live actions can reach the game bridge.",
    "",
    `QR payload: ${JSON.stringify(payload)}`
  ].filter(Boolean);
  return lines.join("\n");
}

function preferredMobileGatewayHost(info) {
  const addresses = Array.isArray(info && info.lanAddresses) ? info.lanAddresses : [];
  const selected = els.mobileGatewayHostSelect ? String(els.mobileGatewayHostSelect.value || "").trim() : "";
  if (selected && addresses.includes(selected)) return selected;
  return addresses[0] || "";
}

function fillMobileGatewayHostSelect(info) {
  if (!els.mobileGatewayHostSelect) return;
  const addresses = Array.isArray(info && info.lanAddresses) ? info.lanAddresses : [];
  const previous = String(els.mobileGatewayHostSelect.value || "").trim();
  els.mobileGatewayHostSelect.innerHTML = "";
  if (!addresses.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No LAN IPv4 detected";
    els.mobileGatewayHostSelect.appendChild(option);
    els.mobileGatewayHostSelect.disabled = true;
    return;
  }
  addresses.forEach((address, index) => {
    const option = document.createElement("option");
    option.value = address;
    option.textContent = index === 0 ? `${address} (preferred)` : address;
    els.mobileGatewayHostSelect.appendChild(option);
  });
  els.mobileGatewayHostSelect.disabled = addresses.length < 2;
  els.mobileGatewayHostSelect.value = previous && addresses.includes(previous) ? previous : addresses[0];
}

async function renderMobileGatewayQr(info, preferredHost = "") {
  if (!els.mobileGatewayQr) return;
  const payload = buildMobilePairingPayload(info, preferredHost);
  if (!payload.code || !payload.hosts.length) {
    els.mobileGatewayQr.removeAttribute("src");
    els.mobileGatewayQr.alt = "Pairing QR unavailable until a LAN address and code are ready";
    return;
  }
  if (!window.msbt || typeof window.msbt.mobileGatewayMakeQr !== "function") {
    els.mobileGatewayQr.alt = "QR generation unavailable in this build";
    return;
  }
  const result = await window.msbt.mobileGatewayMakeQr(JSON.stringify(payload));
  if (result && result.ok && result.dataUrl) {
    els.mobileGatewayQr.src = result.dataUrl;
    els.mobileGatewayQr.alt = "Scan with MSBT Mobile to pair";
  } else {
    els.mobileGatewayQr.removeAttribute("src");
    els.mobileGatewayQr.alt = (result && result.message) || "Could not render pairing QR";
  }
}

async function refreshMobileGatewayInfo() {
  if (!window.msbt || typeof window.msbt.mobileGatewayGetInfo !== "function") {
    setLine(els.mobileGatewaySummary, "Mobile gateway API unavailable in this build.", "warning");
    return null;
  }
  let info = await window.msbt.mobileGatewayGetInfo();
  if (!info || !info.enabled) {
    info = await window.msbt.mobileGatewayStart();
  }
  fillMobileGatewayHostSelect(info);
  const preferred = preferredMobileGatewayHost(info);
  const addresses = Array.isArray(info.lanAddresses) ? info.lanAddresses : [];
  const primary = preferred || addresses[0] || "";
  if (els.mobileGatewayCode) els.mobileGatewayCode.textContent = info.pairingCode || "------";
  if (els.mobileGatewayAddress) {
    els.mobileGatewayAddress.textContent = primary
      ? (addresses.length > 1 ? `${primary} (also ${addresses.filter((a) => a !== primary).join(", ")})` : primary)
      : "No LAN IPv4 detected";
  }
  if (els.mobileGatewayPort) els.mobileGatewayPort.textContent = String(info.port || 49775);
  if (els.mobileGatewayDetails) els.mobileGatewayDetails.textContent = formatMobileGatewayDetails(info, preferred);
  await renderMobileGatewayQr(info, preferred);
  if (info.enabled) {
    setLine(
      els.mobileGatewaySummary,
      `Gateway online on port ${info.port}. Scan the QR in MSBT Mobile (code ${info.pairingCode}).`,
      "ok"
    );
  } else {
    setLine(
      els.mobileGatewaySummary,
      `Gateway offline: ${info.lastError || "could not bind LAN port"}.`,
      "bad"
    );
  }
  return info;
}

async function rotateMobileGatewayCode() {
  if (!window.msbt || typeof window.msbt.mobileGatewayRotateCode !== "function") return null;
  const info = await window.msbt.mobileGatewayRotateCode();
  await refreshMobileGatewayInfo();
  appendActivity(`Mobile gateway pairing code rotated to ${info && info.pairingCode ? info.pairingCode : "new code"}.`);
  return info;
}

async function copyMobileGatewayDetails() {
  const info = await refreshMobileGatewayInfo();
  const preferred = preferredMobileGatewayHost(info || {});
  const text = els.mobileGatewayDetails
    ? els.mobileGatewayDetails.textContent
    : formatMobileGatewayDetails(info || {}, preferred);
  try {
    await navigator.clipboard.writeText(text);
    setLine(els.mobileGatewaySummary, "Pairing details copied to clipboard.", "ok");
  } catch {
    window.prompt("Copy these pairing details:", text);
  }
}

/** Phone-friendly install page (not the raw APK). Pairing uses a different QR in Mobile Gateway. */
const MOBILE_INSTALL_URL =
  "https://www.funkyoushift.com/MattsSDKBoostingTools/mobile-install.html";
const MOBILE_ANNOUNCE_DISMISS_KEY = "msbt.mobileAnnounce.dismissed.v1";

function isMobileAnnounceDismissed() {
  try {
    return localStorage.getItem(MOBILE_ANNOUNCE_DISMISS_KEY) === "1";
  } catch {
    return false;
  }
}

function setMobileAnnounceDismissed(dismissed) {
  try {
    if (dismissed) localStorage.setItem(MOBILE_ANNOUNCE_DISMISS_KEY, "1");
    else localStorage.removeItem(MOBILE_ANNOUNCE_DISMISS_KEY);
  } catch {
    /* ignore */
  }
}

async function renderMobileAnnounceQr() {
  if (!els.mobileAnnounceQr) return;
  if (!window.msbt || typeof window.msbt.mobileGatewayMakeQr !== "function") {
    els.mobileAnnounceQr.alt = "QR unavailable in this build";
    return;
  }
  const result = await window.msbt.mobileGatewayMakeQr(MOBILE_INSTALL_URL);
  if (result && result.ok && result.dataUrl) {
    els.mobileAnnounceQr.src = result.dataUrl;
    els.mobileAnnounceQr.alt = "Scan to open the MSBT Mobile install page";
  } else {
    els.mobileAnnounceQr.removeAttribute("src");
    els.mobileAnnounceQr.alt = (result && result.message) || "Could not render install QR";
  }
}

function hideMobileAnnounceModal() {
  if (els.mobileAnnounceModal) els.mobileAnnounceModal.classList.add("hidden");
}

async function showMobileAnnounceModal({ force = false } = {}) {
  if (!els.mobileAnnounceModal) return;
  if (!force && isMobileAnnounceDismissed()) return;
  if (!force && walkthroughState.active) {
    state.deferredMobileAnnounce = true;
    return;
  }
  const updateOpen =
    els.startupUpdateModal && !els.startupUpdateModal.classList.contains("hidden");
  if (!force && updateOpen) {
    state.deferredMobileAnnounce = true;
    return;
  }
  await renderMobileAnnounceQr();
  if (els.mobileAnnounceDontShow) els.mobileAnnounceDontShow.checked = false;
  els.mobileAnnounceModal.classList.remove("hidden");
}

function openMobileGatewayPanel() {
  hideMobileAnnounceModal();
  const activityTab = document.querySelector('[data-tab="activity"]');
  if (activityTab) activityTab.click();
  const panel = document.querySelector('[data-msbt-panel="mobile-gateway"]');
  if (panel) {
    requestAnimationFrame(() => {
      try {
        panel.scrollIntoView({ behavior: "smooth", block: "start" });
      } catch {
        panel.scrollIntoView();
      }
    });
  }
  void refreshMobileGatewayInfo();
}

function openMobileInstallPage() {
  const url = MOBILE_INSTALL_URL;
  if (window.msbt && typeof window.msbt.openExternal === "function") {
    window.msbt.openExternal(url);
  } else {
    window.open(url, "_blank", "noopener,noreferrer");
  }
}

function applyBridgeStatusResult(result, options = {}) {
  const data = result && result.data ? result.data : {};
  if (!result.ok || !data.ok) {
    state.bridgeOnline = false;
    state.bridgeDiagnostics = {};
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
  state.bridgeDiagnostics = data.diagnostics && typeof data.diagnostics === "object" ? data.diagnostics : {};
  renderPlayers(data);
  const playerCount = Array.isArray(data.players) ? data.players.length : 0;
  const selected = data.selected_player || "none";
  const queue = data.queue || 0;
  setLine(els.bridgeSummary, `Bridge online | players: ${playerCount} | selected: ${selected} | queue: ${queue}`, "ok");
  updateSerialDeliveryProgress(data.serial_delivery || {});
  updateSerialState();
  // Always pull rarity from the bridge so F7 live-apply moves Boosting sliders.
  syncBoostingRaritySlidersFromBridge(data);
  if (!options.quiet) appendActivity(`Bridge online | players: ${playerCount} | selected: ${selected} | queue: ${queue}`);
  return data;
}

async function bridgeStatus(options = {}) {
  if (!options.quiet) setLine(els.bridgeSummary, "Checking bridge...", "warning");
  const result = await window.msbt.bridgeRequest({ method: "GET", path: "/status" });
  if (!options.quiet) setOutput(els.statusOutput, result);
  applyBridgeStatusResult(result, options);
  await autoApplySavedMovementPresetIfNeeded();
  const quickPanel = quickMenuNode("tab-quick-menu");
  if (quickPanel && quickPanel.classList.contains("active")) {
    // Pin/lock status only on quiet polls. Full layout refresh preserves the
    // editor page + in-progress custom label (bridge layout.page is often 0).
    await refreshQuickMenuPinPanel({ quiet: true });
    if (!options.quiet) {
      await loadQuickMenuLayout({ quiet: false, preserveSelection: true });
    } else {
      const prevRev = state.quickMenuSnapshot ? Number(state.quickMenuSnapshot.revision || 0) : null;
      const layoutResult = await window.msbt.bridgeRequest({
        method: "GET",
        path: "/quick_menu",
        timeoutMs: 8000
      });
      const data = quickMenuData(layoutResult);
      const nextRev = data && data.ok ? Number(data.revision || 0) : null;
      if (data && data.ok && data.layout && (prevRev === null || nextRev !== prevRev)) {
        const labelInput = quickMenuNode("quickMenuCustomLabel");
        const actionSelect = quickMenuNode("quickMenuActionSelect");
        const editingLabel = Boolean(labelInput && document.activeElement === labelInput);
        const editingAction = Boolean(actionSelect && document.activeElement === actionSelect);
        const draftLabel = editingLabel ? String(labelInput.value || "") : null;
        const draftAction = editingAction ? String(actionSelect.value || "") : null;
        const keepPage = state.quickMenuPage;
        const keepSlot = state.quickMenuSelectedSlot;
        state.quickMenuSnapshot = data;
        state.quickMenuPage = keepPage;
        state.quickMenuSelectedSlot = keepSlot;
        renderQuickMenuEditor();
        syncQuickMenuModulesPanel();
        if (editingLabel && labelInput && draftLabel !== null) {
          labelInput.value = draftLabel;
          try { labelInput.focus(); } catch (_) { /* ignore */ }
        }
        if (editingAction && actionSelect && draftAction) {
          actionSelect.value = draftAction;
          try { actionSelect.focus(); } catch (_) { /* ignore */ }
        }
      }
    }
  }
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
  }, 1500);
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

async function setTarget(value, options = {}) {
  const target = String(value || "").trim();
  const keepBoostScope = Boolean(options && options.keepBoostScope);
  if (!keepBoostScope) {
    state.boostTargetScope = "selected";
  }
  if (!target) {
    state.selectedTarget = "";
    state.selectedTargetName = "";
    updateBoostTargetSummary();
    setLine(els.bookmarkTargetSummary, "Selected target: none", "warning");
    setLine(els.bl4TargetSummary, "Selected target: none", "warning");
    setLine(els.movementStatus, "Selected target: none", "warning");
    if (els.invReading && !state.invEquipped.length && !state.invBackpack.length) {
      els.invReading.textContent = "Reading: none";
    }
    updateSerialState();
    return null;
  }

  setLine(els.targetSummary, `Setting target ${target}...`, "warning");
  setLine(els.bookmarkTargetSummary, `Setting target ${target}...`, "warning");
  setLine(els.bl4TargetSummary, `Setting target ${target}...`, "warning");
  setLine(els.movementStatus, `Setting target ${target}...`, "warning");
  if (els.invStatus) setLine(els.invStatus, `Setting target ${target}...`, "warning");
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
    if (els.invStatus) setLine(els.invStatus, message, "bad");
    updateSerialState();
  }
  return result;
}

function firstPlayerTarget() {
  if (!state.players.length) {
    setLine(els.targetSummary, "Refresh status first; no players are loaded.", "warning");
    return;
  }
  setBoostTargetScope("selected");
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
    setLine(els.serialSummary, "Load the Mattmab editor before detecting a serial.", "warning");
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

async function loadEditor(options = {}) {
  if (!els.editorFrame) return;
  if (state.editorLoadInFlight) return;
  if (state.editorLoaded && !options.force) return;

  state.editorLoadInFlight = true;
  setOutput(els.deliveryOutput, "Starting bundled Matt editor...");
  try {
    const result = await window.msbt.mattEditorUrl();
    const url = typeof result === "string" ? result : result.url;
    const hosted = typeof result === "string" ? false : Boolean(result.hosted);
    const message = typeof result === "string" ? "Loaded raw editor file." : result.message;
    els.editorFrame.src = url;
    state.editorLoaded = true;
    setOutput(els.deliveryOutput, message || (hosted ? "Bundled Matt editor loaded." : "Editor loaded."));
    setLine(
      els.serialSummary,
      hosted
        ? "Matt editor loaded. Detect the generated @U serial, then send from Item Delivery."
        : "Raw editor fallback loaded. Save/profile conversion and delivery adapter may be unavailable.",
      hosted ? "ok" : "warning"
    );
  } catch (error) {
    state.editorLoaded = false;
    const message = error && error.message ? error.message : String(error);
    setOutput(els.deliveryOutput, `Matt editor failed to load: ${message}`);
    setLine(els.serialSummary, "Matt editor failed to load.", "bad");
  } finally {
    state.editorLoadInFlight = false;
  }
}

function expandSerialTextCopies(serialText, copies, label = "Serial delivery") {
  const n = Math.max(1, Math.min(50, Number(copies) || 1));
  const source = String(serialText || "");
  if (n <= 1) {
    const unique = serialsFromText(source);
    return { text: source, copies: 1, uniqueCount: unique.length, totalCount: unique.length };
  }
  const serials = serialsFromText(source);
  if (!serials.length) {
    return { text: source, copies: n, uniqueCount: 0, totalCount: 0 };
  }
  const text = serials.flatMap((serial) => Array.from({ length: n }, () => serial)).join("\n");
  appendActivity(`${label}: ${serials.length} serial(s) × ${n} = ${serials.length * n} total.`);
  return { text, copies: n, uniqueCount: serials.length, totalCount: serials.length * n };
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
  await sendSerialPayload(mode, serial, false, 60, els.deliveryOutput, getInt(els.editorSerialCopies, 1, 50, 1), "Matt Editor");
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
    els.boostOutput,
    getInt(els.boostSerialCopies, 1, 50, 1),
    "Serial Rewards"
  );
}

async function sendSerialPayload(mode, serialText, overrideLevel, level, outNode, copies = 1, label = "Serial delivery") {
  const expanded = expandSerialTextCopies(serialText, copies, label);
  const sdkReady = await ensureLiveSdkReady(outNode);
  if (!sdkReady.ok) {
    return { ok: false, message: sdkReady.message };
  }
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
    serial_text: expanded.text,
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

  const copies = getInt(els.bookmarkSerialCopies, 1, 50, 1);
  const expanded = expandSerialTextCopies(serials.join("\n"), copies, "Serial Bookmarks");
  const destination = mode === "selected" ? (state.selectedTarget || "selected target") : mode === "all" ? "all players" : "non-host players";
  const label = entries.length === 1 ? `"${entries[0].name || "selected bookmark"}"` : `${entries.length} bookmark row(s)`;
  const copiesNote = copies > 1 ? ` (${copies} copies each → ${expanded.totalCount} total)` : "";
  if (!window.confirm(`Deliver ${serials.length} serial(s)${copiesNote} from ${label} to ${destination}?`)) {
    setBookmarkStatus("Serial bookmark delivery cancelled.", "warning");
    return;
  }

  setBookmarkStatus(`Sending ${expanded.totalCount || serials.length} bookmarked serial(s) to ${destination}...`, "warning");
  setOutput(
    els.bookmarkOutput,
    `Sending Serial Bookmarks delivery:\nDestination: ${destination}\nBookmark rows: ${entries.length}\nUnique serials: ${serials.length}\nCopies: ${copies}\nTotal delivered: ${expanded.totalCount || serials.length}\n${entries.map((row) => `${row.name || "Untitled Serial"} | ${row.group || "Default"}`).join("\n")}`
  );
  const result = await sendSerialPayload(mode, expanded.text, false, 60, els.bookmarkOutput, 1, "Serial Bookmarks");
  if (!result) return;
  const message = actionSucceeded(result)
    ? resultMessage(result)
    : annotateDeliveryFailureMessage(resultMessage(result));
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

  return state.bl4Entries.filter((row) => {
    const termOk = terms.every((term) => bl4SearchBlob(row).includes(term));
    const listingOk = bl4ListingMatches(row, listing);
    const typeOk = type === "All" || String(row.type || "") === type;
    const manufacturerOk = manufacturer === "All" || String(row.manufacturer || "") === manufacturer;
    const rarityOk = rarity === "All" || String(row.rarity || "") === rarity;
    const creatorOk = creator === "All" || String(row.creator || "") === creator;
    const mattmabOk = bl4MattmabMatches(row, mattmab);
    return termOk && listingOk && typeOk && manufacturerOk && rarityOk && creatorOk && mattmabOk;
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
    empty.textContent = "No BL4 codes match the current filters. Use Search or loosen a dropdown filter.";
    els.bl4Cards.appendChild(empty);
    if (els.bl4CardSummary) els.bl4CardSummary.textContent = "No visible cards.";
    return;
  }

  const maxCards = 320;
  const shown = state.bl4FilteredEntries.slice(0, maxCards);
  if (els.bl4CardSummary) {
    els.bl4CardSummary.textContent = `${shown.length} of ${state.bl4FilteredEntries.length} card(s) shown; ${bl4ImageHint(shown)} Use Listing/Search to find Lootlemon or Legit codes.`;
  }

  shown.forEach((row) => {
    const id = bl4EntryId(row);
    const card = document.createElement("button");
    card.type = "button";
    card.className = `bl4-code-card${id === state.bl4ActiveId ? " active" : ""}${state.bl4SelectedIds.has(id) ? " checked" : ""}`;
    card.addEventListener("click", () => selectBl4Entry(id));

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "bl4-card-checkbox";
    checkbox.checked = state.bl4SelectedIds.has(id);
    checkbox.title = "Select for bulk actions";
    checkbox.addEventListener("click", (event) => {
      event.stopPropagation();
      if (checkbox.checked) {
        state.bl4SelectedIds.add(id);
      } else {
        state.bl4SelectedIds.delete(id);
      }
      renderBl4Codes();
    });

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
    card.append(checkbox, imageWrap, title, meta, result);
    els.bl4Cards.appendChild(card);
  });

  if (state.bl4FilteredEntries.length > maxCards) {
    const note = document.createElement("div");
    note.className = "dev-empty-row";
    note.textContent = `Showing first ${maxCards} card(s). Narrow Search or filters for more.`;
    els.bl4Cards.appendChild(note);
  }
}

function sortedUniqueText(values = []) {
  return Array.from(new Set(
    (Array.isArray(values) ? values : [])
      .map((value) => String(value || "").trim())
      .filter(Boolean)
  )).sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
}

function gzoSubmitCatalogValues(field) {
  const values = [];
  state.bl4Entries.forEach((row) => {
    if (!row) return;
    if (field === "category") {
      values.push(row.category || "");
      values.push(row.type || "");
    } else {
      values.push(row[field] || "");
    }
  });
  return sortedUniqueText(values);
}

function fillGzoSubmitSelect(selectNode, values, selectedValue = "", blankLabel = "Choose...") {
  if (!selectNode) return;
  const selected = String(selectedValue || getValue(selectNode) || "").trim();
  const options = sortedUniqueText([...(values || []), selected]);
  selectNode.innerHTML = "";
  const blank = document.createElement("option");
  blank.value = "";
  blank.textContent = blankLabel;
  selectNode.appendChild(blank);
  options.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    selectNode.appendChild(option);
  });
  selectNode.value = selected;
}

function refreshGzoSubmitDropdownOptions(row = null) {
  fillGzoSubmitSelect(els.gzoSubmitRarity, gzoSubmitCatalogValues("rarity"), row && row.rarity ? row.rarity : getValue(els.gzoSubmitRarity), "Choose rarity");
  fillGzoSubmitSelect(els.gzoSubmitType, gzoSubmitCatalogValues("type"), row && row.type ? row.type : getValue(els.gzoSubmitType), "Choose type");
  const categoryValue = row && (row.category || row.type) ? row.category || row.type : getValue(els.gzoSubmitCategory);
  fillGzoSubmitSelect(els.gzoSubmitCategory, gzoSubmitCatalogValues("category"), categoryValue, "Choose category");
}

function setGzoSubmitResult(text = "No submission sent yet.") {
  setTextValue(els.gzoSubmitResult, text);
}

function formatGzoSubmitResult(result = {}, payload = {}) {
  const lines = [
    `Submitted: ${new Date().toLocaleString()}`,
    `Endpoint: ${result.endpoint || "unknown"}`,
    `HTTP status: ${typeof result.status === "number" ? result.status : "unknown"}`,
    `Result: ${result.ok ? "success / accepted by endpoint" : "failed or rejected"}`,
    `Message: ${result.message || "No message returned."}`
  ];
  if (payload.imageName) lines.push(`Image sent: ${payload.imageName}`);
  if (result.editUrl) lines.push(`Edit URL: ${result.editUrl}`);
  if (Object.prototype.hasOwnProperty.call(result, "published")) lines.push(`Published immediately: ${result.published ? "yes" : "no"}`);
  lines.push("", "Raw API response:", pretty(result.data || result.rawText || result));
  return lines.join("\n");
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
  updateGzoSubmitPayloadPreview();
}

function gzoSubmitImageFile() {
  return els.gzoSubmitImage && els.gzoSubmitImage.files && els.gzoSubmitImage.files.length ? els.gzoSubmitImage.files[0] : null;
}

function gzoSubmitPayload() {
  const image = gzoSubmitImageFile();
  return {
    action: "submit",
    listing: getValue(els.gzoSubmitListing),
    name: getValue(els.gzoSubmitName),
    creator: getValue(els.gzoSubmitCreator),
    type: getValue(els.gzoSubmitType),
    category: getValue(els.gzoSubmitCategory),
    rarity: getValue(els.gzoSubmitRarity),
    base85: getValue(els.gzoSubmitBase85),
    deserialized: getValue(els.gzoSubmitDeserialized),
    notes: getValue(els.gzoSubmitNotes),
    image: image ? `${image.name} (${image.type || "unknown type"}, ${Math.ceil(image.size / 1024)} KB)` : ""
  };
}

function formatGzoSubmitPayloadPreview(payload) {
  const lines = [];
  for (const [key, value] of Object.entries(payload || {})) {
    const text = String(value || "").trim();
    if (!text) continue;
    lines.push(`${key}: ${text}`);
  }
  return lines.join("\n");
}

function updateGzoSubmitPayloadPreview() {
  setTextValue(els.gzoSubmitPayloadPreview, formatGzoSubmitPayloadPreview(gzoSubmitPayload()));
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
    updateGzoSubmitPayloadPreview();
    return;
  }
  state.gzoSubmitImageObjectUrl = URL.createObjectURL(file);
  const img = document.createElement("img");
  img.alt = file.name;
  img.src = state.gzoSubmitImageObjectUrl;
  const label = document.createElement("div");
  label.textContent = `${file.name} (${Math.ceil(file.size / 1024)} KB)`;
  els.gzoSubmitImagePreview.append(img, label);
  updateGzoSubmitPayloadPreview();
  setLine(els.gzoSubmitStatus, "Image attached. Submission will go to GZO Pending for developer review.", "ok");
}

function clearGzoSubmitForm() {
  refreshGzoSubmitDropdownOptions(null);
  if (els.gzoSubmitListing) els.gzoSubmitListing.value = "Modded";
  setTextValue(els.gzoSubmitName, "");
  setTextValue(els.gzoSubmitCreator, "");
  setTextValue(els.gzoSubmitType, "");
  setTextValue(els.gzoSubmitCategory, "");
  setTextValue(els.gzoSubmitRarity, "");
  setTextValue(els.gzoSubmitBase85, "");
  setTextValue(els.gzoSubmitDeserialized, "");
  setTextValue(els.gzoSubmitNotes, "");
  clearGzoSubmitImagePreview();
  updateGzoSubmitPayloadPreview();
  setGzoSubmitResult();
  setLine(els.gzoSubmitStatus, "Paste a @U Base85 code or decoded serial, then click Decode / Normalize Serial. Attach an image before submitting.", "warning");
}

function openGzoSubmitModal() {
  clearGzoSubmitForm();
  if (els.gzoSubmitModal) els.gzoSubmitModal.classList.remove("hidden");
}

function closeGzoSubmitModal() {
  if (els.gzoSubmitModal) els.gzoSubmitModal.classList.add("hidden");
}

async function normalizeGzoSubmitSerial() {
  const serialText = getValue(els.gzoSubmitBase85) || getValue(els.gzoSubmitDeserialized);
  if (!serialText) {
    setLine(els.gzoSubmitStatus, "Paste a @U Base85 code or decoded serial first.", "warning");
    return null;
  }
  if (!window.msbt || typeof window.msbt.serialToolsConvert !== "function") {
    setLine(els.gzoSubmitStatus, "Local serial converter is not available in this build.", "bad");
    return null;
  }
  setLine(els.gzoSubmitStatus, "Decoding / normalizing serial locally...", "warning");
  const result = await window.msbt.serialToolsConvert(serialText);
  const ok = String(result && result.ok).toLowerCase() === "true" || result.ok === true;
  if (!ok) {
    setGzoSubmitResult(`Serial normalize failed:\n${pretty(result || {})}`);
    setLine(els.gzoSubmitStatus, result && result.message ? result.message : "Serial normalize failed.", "bad");
    updateGzoSubmitPayloadPreview();
    return result;
  }
  const serialized = String(result.serialized || "").trim();
  const deserialized = String(result.deserialized || "").trim();
  if (serialized) setTextValue(els.gzoSubmitBase85, serialized);
  if (deserialized) setTextValue(els.gzoSubmitDeserialized, deserialized);
  setGzoSubmitResult(`Serial normalized locally:\n${pretty({
    base85: serialized,
    deserialized,
    message: result.message || "Converted successfully."
  })}`);
  updateGzoSubmitPayloadPreview();
  setLine(els.gzoSubmitStatus, "Serial normalized. Review metadata and attach an image before submitting.", "ok");
  return result;
}

async function useMattEditorSerialForGzoSubmit() {
  const found = collectEditorSerials();
  if (!found.length) {
    setLine(els.gzoSubmitStatus, "No @U serial found in the Matt Editor. Build or serialize an item first.", "warning");
    return;
  }
  setTextValue(els.gzoSubmitBase85, found[0]);
  if (found.length > 1) {
    setLine(els.gzoSubmitStatus, `Found ${found.length} editor serials; using the first one.`, "warning");
  }
  await normalizeGzoSubmitSerial();
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
  if (!getValue(els.gzoSubmitBase85).trim() && !getValue(els.gzoSubmitDeserialized).trim()) {
    missing.push("base85 or deserialized");
  }
  const image = gzoSubmitImageFile();
  if (!image) missing.push("image");
  const allowedImages = new Set(["image/png", "image/jpeg", "image/webp"]);
  const unsupportedImage = image && !allowedImages.has(String(image.type || "").toLowerCase());
  return { ok: !missing.length && !unsupportedImage, missing, unsupportedImage };
}

function gzoSubmitRequestPayload() {
  const image = gzoSubmitImageFile();
  const imagePath = image && window.msbt && typeof window.msbt.getPathForFile === "function"
    ? window.msbt.getPathForFile(image)
    : "";
  return {
    listing: getValue(els.gzoSubmitListing),
    name: getValue(els.gzoSubmitName),
    creator: getValue(els.gzoSubmitCreator),
    type: getValue(els.gzoSubmitType),
    category: getValue(els.gzoSubmitCategory),
    rarity: getValue(els.gzoSubmitRarity),
    base85: getValue(els.gzoSubmitBase85),
    deserialized: getValue(els.gzoSubmitDeserialized),
    notes: getValue(els.gzoSubmitNotes),
    imagePath,
    imageName: image ? image.name : "",
    imageType: image ? image.type : "",
    imageSize: image ? image.size : 0
  };
}

async function handleGzoSubmit(event) {
  if (event) event.preventDefault();
  if (getValue(els.gzoSubmitBase85) || getValue(els.gzoSubmitDeserialized)) {
    const normalized = await normalizeGzoSubmitSerial();
    const ok = String(normalized && normalized.ok).toLowerCase() === "true" || (normalized && normalized.ok === true);
    if (!ok) return;
  }
  updateGzoSubmitPayloadPreview();
  const check = validateGzoSubmitForm();
  if (!check.ok) {
    const missingText = check.missing.length ? `Required before submission: ${check.missing.join(", ")}.` : "";
    const typeText = check.unsupportedImage ? " Image must be PNG, JPEG, or WebP." : "";
    setLine(els.gzoSubmitStatus, `${missingText}${typeText}`, "bad");
    return;
  }
  if (!window.msbt || typeof window.msbt.submitGzoCode !== "function") {
    setLine(els.gzoSubmitStatus, "GZO submit helper is not available in this build.", "bad");
    return;
  }
  const payload = gzoSubmitRequestPayload();
  if (!payload.imagePath) {
    setLine(els.gzoSubmitStatus, "Electron could not access the selected image path. Choose the image again and retry.", "bad");
    return;
  }
  if (els.gzoSubmitSendBtn) els.gzoSubmitSendBtn.disabled = true;
  setLine(els.gzoSubmitStatus, "Submitting to GZO Pending...", "warning");
  setGzoSubmitResult("Submitting to GZO Pending...");
  try {
    const result = await window.msbt.submitGzoCode(payload);
    setGzoSubmitResult(formatGzoSubmitResult(result || {}, payload));
    if (result && result.ok) {
      const suffix = result.editUrl ? ` Edit URL: ${result.editUrl}` : "";
      setLine(els.gzoSubmitStatus, `Submitted to GZO Pending for developer review.${suffix}`, "ok");
      setBl4Status("Submitted code to GZO Pending for developer review.", "ok");
    } else {
      setLine(els.gzoSubmitStatus, result && result.message ? result.message : "GZO submission failed.", "bad");
    }
  } catch (error) {
    setGzoSubmitResult(`GZO submission failed:\n${error && error.stack ? error.stack : error}`);
    setLine(els.gzoSubmitStatus, `GZO submission failed: ${error && error.message ? error.message : error}`, "bad");
  } finally {
    if (els.gzoSubmitSendBtn) els.gzoSubmitSendBtn.disabled = false;
  }
}

async function copyGzoSubmitPayloadPreview() {
  updateGzoSubmitPayloadPreview();
  await copyText(getValue(els.gzoSubmitPayloadPreview), els.gzoSubmitStatus, "Submission preview");
}

function clearBl4Detail(message = "Select a BL4 code.") {
  state.bl4ActiveId = "";
  state.bl4ConfirmedId = "";
  state.bl4ConfirmedSerial = "";
  setOutput(els.bl4Detail, message);
  setTextValue(els.bl4Serial, "");
  setTextValue(els.bl4Breakdown, "");
  setBl4DeliveryStatus("Delivery sends checked image cards, or the active code if none are checked.", "warning");
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
  setBl4DeliveryStatus("Active code ready. Delivery sends checked image cards, or this active code if none are checked.", "warning");
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

  if (!state.bl4Entries.length) {
    clearBl4Detail("No BL4 catalog is loaded.");
    renderBl4Cards();
    return;
  }
  if (!state.bl4FilteredEntries.length) {
    clearBl4Detail("No BL4 code is visible with the current filters.");
    renderBl4Cards();
    return;
  }

  if (state.bl4ActiveId && !state.bl4FilteredEntries.some((row) => bl4EntryId(row) === state.bl4ActiveId)) {
    clearBl4Detail("The active code is hidden by the current filters.");
  }

  renderBl4Cards();

  if (!state.bl4ActiveId && state.bl4FilteredEntries.length) {
    selectBl4Entry(bl4EntryId(state.bl4FilteredEntries[0]));
  }
}

function applyBl4Search() {
  state.bl4SearchQuery = getValue(els.bl4SearchInput);
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

  const copies = getInt(els.bl4SerialCopies, 1, 50, 1);
  const expanded = expandSerialTextCopies(serialText, copies, "BL4 Codes");
  const destination = mode === "selected" ? (state.selectedTarget || "selected target") : mode === "all" ? "all players" : "non-host players";
  const label = deliveryRows.length === 1 ? `"${deliveryRows[0].name || "selected BL4 code"}"` : `${deliveryRows.length} selected BL4 codes`;
  const skipNote = skippedByOverride.length ? `\n\n${skippedByOverride.length} selected code(s) will be skipped because their level could not be changed.` : "";
  const copiesNote = copies > 1 ? `\nCopies: ${copies} each → ${expanded.totalCount} total serials.` : "";
  const confirmed = window.confirm(`Deliver ${label} to ${destination}?${copiesNote}${skipNote}`);
  if (!confirmed) {
    setBl4DeliveryStatus("BL4 delivery cancelled.", "warning");
    return;
  }

  const actionByMode = {
    selected: "give_serial_selected",
    all: "give_serial_all",
    nonhost: "give_serial_nonhost"
  };
  setBl4DeliveryStatus(`Sending ${expanded.totalCount || deliveryRows.length} BL4 serial(s) to ${destination}...`, "warning");
  setOutput(
    els.bl4Output,
    `Sending BL4 code delivery:\nAction: ${actionByMode[mode] || mode}\nDestination: ${destination}\nSelected codes: ${deliveryRows.length}\nCopies: ${copies}\nTotal delivered: ${expanded.totalCount || deliveryRows.length}\n${deliveryRows.map((row) => row.name || "Selected BL4 code").join("\n")}${skippedByOverride.length ? `\n\nSkipped by level override: ${skippedByOverride.length}` : ""}`
  );
  appendActivity(`BL4 delivery: sending ${deliveryRows.length} code(s) × ${copies} via ${mode}${skippedByOverride.length ? `; skipped ${skippedByOverride.length}` : ""}.`);

  const result = await sendSerialPayload(
    mode,
    expanded.text,
    overrideLevel,
    deliveryLevel,
    els.bl4Output,
    1,
    "BL4 Codes"
  );
  if (!result) return;
  const message = actionSucceeded(result)
    ? resultMessage(result)
    : annotateDeliveryFailureMessage(resultMessage(result));
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

function formatDataCatalogDetail(statusOrResult) {
  const data = statusOrResult || {};
  const last = data.lastRefresh || data;
  const version = last.dataVersion
    || (data.cachedManifest && data.cachedManifest.data_version_label)
    || (data.bundledManifest && data.bundledManifest.data_version_label)
    || "unknown";
  const checkedAt = last.checkedAt || "";
  const updated = Number.isFinite(last.updatedCount)
    ? last.updatedCount
    : Array.isArray(last.updated)
      ? last.updated.length
      : 0;
  const skipped = Number.isFinite(last.skippedCount)
    ? last.skippedCount
    : Array.isArray(last.skipped)
      ? last.skipped.length
      : 0;
  const failed = Number.isFinite(last.failedCount)
    ? last.failedCount
    : Array.isArray(last.failed)
      ? last.failed.length
      : 0;
  const cachedCount = Number.isFinite(data.cachedCount) ? data.cachedCount : null;
  const known = Number.isFinite(data.knownFileCount) ? data.knownFileCount : null;
  const parts = [
    `Version ${version}`,
    checkedAt ? `last check ${checkedAt}` : null,
    `updated ${updated}`,
    `unchanged ${skipped}`,
    `failed ${failed}`,
    cachedCount !== null && known !== null ? `cache ${cachedCount}/${known}` : null
  ].filter(Boolean);
  return parts.join(" · ");
}

function applyDataCatalogStatusUi(statusOrResult, options = {}) {
  const quiet = Boolean(options.quiet);
  const message = (statusOrResult && (statusOrResult.statusLine || statusOrResult.message))
    || "Data catalogs not checked yet.";
  const kind = statusOrResult && statusOrResult.ok === false
    ? "bad"
    : statusOrResult && (statusOrResult.soft || statusOrResult.offline)
      ? "warning"
      : statusOrResult && statusOrResult.ok
        ? "ok"
        : "";
  if (els.dataCatalogSummary) {
    setLine(els.dataCatalogSummary, quiet && statusOrResult && statusOrResult.ok
      ? `Startup data check: ${message}`
      : message, kind);
  }
  if (els.dataCatalogDetail) {
    els.dataCatalogDetail.textContent = formatDataCatalogDetail(statusOrResult);
  }
  if (els.bl4DataCatalogStatus) {
    els.bl4DataCatalogStatus.textContent = `Data catalogs: ${formatDataCatalogDetail(statusOrResult)}`;
  }
}

async function refreshDataCatalogStatusUi() {
  if (!window.msbt || typeof window.msbt.getDataCatalogStatus !== "function") return null;
  try {
    const status = await window.msbt.getDataCatalogStatus();
    if (status && status.ok) {
      applyDataCatalogStatusUi(status);
    }
    return status;
  } catch (error) {
    console.warn("[MSBT] data catalog status failed:", error);
    return null;
  }
}

async function refreshMsbtDataCatalogs(options = {}) {
  const fromBl4 = Boolean(options.fromBl4);
  const quiet = Boolean(options.quiet);
  if (!window.msbt || typeof window.msbt.refreshDataCatalogs !== "function") {
    const message = "Data catalog refresh is not available in this Electron build.";
    if (fromBl4) setBl4Status(message, "bad");
    if (els.dataCatalogSummary) setLine(els.dataCatalogSummary, message, "bad");
    return;
  }
  if (!quiet) {
    if (els.bl4RefreshCatalogsBtn) els.bl4RefreshCatalogsBtn.disabled = true;
    if (els.refreshDataCatalogsBtn) els.refreshDataCatalogsBtn.disabled = true;
    const pending = "Refreshing MSBT data catalogs (manifest + changed JSON)...";
    if (fromBl4) setBl4Status(pending, "warning");
    if (els.dataCatalogSummary) setLine(els.dataCatalogSummary, pending, "warning");
  }
  try {
    const result = await window.msbt.refreshDataCatalogs({ quiet, retries: 3 });
    applyDataCatalogStatusUi(result, { quiet });
    if (els.updateOutput && result) {
      els.updateOutput.textContent = JSON.stringify(
        {
          dataVersion: result.dataVersion || null,
          publishedAt: result.publishedAt || null,
          checkedAt: result.checkedAt || null,
          manifestUrl: result.manifestUrl || null,
          updated: result.updated || [],
          skipped: result.skipped || [],
          failed: result.failed || [],
          warnings: result.warnings || [],
          cacheDir: result.cacheDir || null
        },
        null,
        2
      );
    }
    if (fromBl4 && !quiet) {
      const kind = result && result.ok ? (result.soft || result.offline ? "warning" : "ok") : "bad";
      setBl4Status(result && result.message ? result.message : "Data catalog refresh finished.", kind);
      if (result && result.ok) {
        await loadBl4Catalog();
      }
    }
    await refreshDataCatalogStatusUi();
    return result;
  } catch (error) {
    const message = `Data catalog refresh failed: ${error && error.message ? error.message : error}`;
    if (fromBl4) setBl4Status(message, "bad");
    if (els.dataCatalogSummary) setLine(els.dataCatalogSummary, message, "bad");
    return { ok: false, message };
  } finally {
    if (!quiet) {
      if (els.bl4RefreshCatalogsBtn) els.bl4RefreshCatalogsBtn.disabled = false;
      if (els.refreshDataCatalogsBtn) els.refreshDataCatalogsBtn.disabled = false;
    }
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
  // Keep update chrome out of the way while any coach-mark tour is open —
  // the Boosting banner otherwise collides with the tour overlay.
  if (!notice || walkthroughState.active) {
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
  if (!walkthroughState.active && state.deferredMobileAnnounce) {
    state.deferredMobileAnnounce = false;
    window.setTimeout(() => void showMobileAnnounceModal({ force: false }), 200);
  }
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
  // Defer until the first-run / post-update tour finishes so the two modals
  // do not stack on top of each other.
  if (walkthroughState.active || shouldAutoShowMainTutorial()) {
    state.deferredStartupUpdateInfo = info;
    return;
  }
  state.startupUpdateNoticeShown = true;
  renderStartupUpdateModal(notice);
}

const DEFAULT_SDK_REQUIRED = "oak2-mod-manager v0.3";
const DEFAULT_SDK_REQUIRED_URL = "https://bl-sdk.github.io/oak2-mod-db/";

function openSdkRequiredUrl(url) {
  const target = String(url || DEFAULT_SDK_REQUIRED_URL).trim() || DEFAULT_SDK_REQUIRED_URL;
  if (window.msbt && typeof window.msbt.openExternal === "function") {
    window.msbt.openExternal(target);
  }
}

function renderVersionLineWithSdkLink(node, prefixText, sdkRequired, sdkRequiredUrl, kind = "") {
  if (!node) return;
  const requiredLabel = sdkRequired || DEFAULT_SDK_REQUIRED;
  const requiredUrl = sdkRequiredUrl || DEFAULT_SDK_REQUIRED_URL;
  node.textContent = "";
  node.classList.remove("ok", "warning", "bad");
  if (kind) node.classList.add(kind);
  node.appendChild(document.createTextNode(`${prefixText} | Requires ${requiredLabel} · `));
  const link = document.createElement("a");
  link.href = requiredUrl;
  link.className = "inline-link";
  link.textContent = "Get required SDK";
  link.title = `Open ${requiredLabel}`;
  link.addEventListener("click", (event) => {
    event.preventDefault();
    openSdkRequiredUrl(requiredUrl);
  });
  node.appendChild(link);
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
  const prefixText = parts.join(" | ");
  const required = data.sdkRequired || DEFAULT_SDK_REQUIRED;
  const requiredUrl = data.sdkRequiredUrl || DEFAULT_SDK_REQUIRED_URL;
  const kind = data.bundledSdkmod && data.bundledSdkmod.available ? "ok" : "warning";
  renderVersionLineWithSdkLink(els.appVersionLine, prefixText, required, requiredUrl);
  renderVersionLineWithSdkLink(els.versionSummary, prefixText, required, requiredUrl, kind);
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
  const confirmed = window.confirm("Restart Matt's SDK Boosting Tools now and install the downloaded update?");
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

function travelFavoritesMap() {
  const data = state.travelFavorites || {};
  return data.favorites && typeof data.favorites === "object" ? data.favorites : {};
}

function travelFavoriteKey(kind, id) {
  const safeKind = String(kind || "").trim().toLowerCase();
  const safeId = String(id || "").trim();
  if ((safeKind !== "map" && safeKind !== "station") || !safeId) return "";
  return `${safeKind}:${safeId}`;
}

function travelFavoriteEntry(key) {
  const favorites = travelFavoritesMap();
  const entry = favorites[key];
  return entry && typeof entry === "object" ? entry : null;
}

function travelFavoriteDefaultLabel(kind, id, world) {
  if (kind === "station") {
    const station = (state.travelStations || []).find((row) => String(row.station || "") === id);
    if (station) return stationLabel(station);
    return world ? `[Station] ${id} (${world})` : `[Station] ${id}`;
  }
  const map = (state.travelMaps || []).find((row) => String(row.map || "") === id);
  if (map) return mapLabel(map);
  return `[Map] ${id}`;
}

function renderTravelFavoriteControls() {
  const key = String(state.travelFavoriteSelectedKey || "").trim();
  const entry = key ? travelFavoriteEntry(key) : null;
  const hasSelection = Boolean(entry);
  if (els.travelFavoriteTravelBtn) els.travelFavoriteTravelBtn.disabled = !hasSelection;
  if (els.travelFavoriteRemoveBtn) els.travelFavoriteRemoveBtn.disabled = !hasSelection;
  if (els.travelFavoriteSaveBtn) els.travelFavoriteSaveBtn.disabled = !hasSelection;
  if (els.travelFavoriteLabel) {
    els.travelFavoriteLabel.disabled = !hasSelection;
    if (!hasSelection) els.travelFavoriteLabel.value = "";
    else if (document.activeElement !== els.travelFavoriteLabel) {
      els.travelFavoriteLabel.value = entry.label || entry.id || "";
    }
  }
  if (els.travelFavoriteNote) {
    els.travelFavoriteNote.disabled = !hasSelection;
    if (!hasSelection) els.travelFavoriteNote.value = "";
    else if (document.activeElement !== els.travelFavoriteNote) {
      els.travelFavoriteNote.value = entry.note || "";
    }
  }
}

function renderTravelFavorites() {
  if (!els.travelFavoriteRows) return;
  const favorites = travelFavoritesMap();
  const keys = Object.keys(favorites).sort((a, b) => {
    const left = favorites[a] || {};
    const right = favorites[b] || {};
    const leftLabel = String(left.label || left.id || a).toLowerCase();
    const rightLabel = String(right.label || right.id || b).toLowerCase();
    return leftLabel.localeCompare(rightLabel);
  });

  els.travelFavoriteRows.innerHTML = "";
  if (!keys.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "No travel favorites yet. Add a map or station above.";
    els.travelFavoriteRows.appendChild(empty);
    setLine(els.travelFavoriteSummary, "0 travel favorites", "warning");
    renderTravelFavoriteControls();
    return;
  }

  if (state.travelFavoriteSelectedKey && !favorites[state.travelFavoriteSelectedKey]) {
    state.travelFavoriteSelectedKey = "";
  }
  if (!state.travelFavoriteSelectedKey) {
    state.travelFavoriteSelectedKey = keys[0];
  }

  keys.forEach((key) => {
    const entry = favorites[key] || {};
    const kind = String(entry.kind || "").toLowerCase() === "station" ? "station" : "map";
    const row = document.createElement("div");
    row.className = `dev-actor-row${key === state.travelFavoriteSelectedKey ? " selected" : ""}`;

    const title = document.createElement("strong");
    title.textContent = entry.label || entry.id || key;
    const meta = document.createElement("span");
    const worldBit = kind === "station" && entry.world ? ` · ${entry.world}` : "";
    meta.textContent = `${kind}${worldBit} · ${entry.id || ""}`;
    if (entry.note) meta.textContent += ` · ${entry.note}`;

    const textWrap = document.createElement("div");
    textWrap.appendChild(title);
    textWrap.appendChild(meta);
    row.appendChild(textWrap);

    row.addEventListener("click", () => {
      state.travelFavoriteSelectedKey = key;
      renderTravelFavorites();
    });
    row.addEventListener("dblclick", () => {
      state.travelFavoriteSelectedKey = key;
      travelSelectedFavorite();
    });
    els.travelFavoriteRows.appendChild(row);
  });

  setLine(els.travelFavoriteSummary, `${keys.length} travel favorite(s)`, "ok");
  renderTravelFavoriteControls();
}

async function loadTravelFavorites() {
  if (!window.msbt || typeof window.msbt.loadTravelFavorites !== "function") {
    state.travelFavorites = { version: 1, favorites: {} };
    setLine(els.travelFavoriteSummary, "Travel favorites storage is not available in this build.", "warning");
    return;
  }
  try {
    const result = await window.msbt.loadTravelFavorites();
    if (!result || !result.ok) {
      throw new Error(result && result.message ? result.message : "Travel favorites failed to load.");
    }
    state.travelFavorites = result.data || { version: 1, favorites: {} };
    renderTravelFavorites();
    const warnings = Array.isArray(result.warnings) ? result.warnings.filter(Boolean) : [];
    if (warnings.length) setLine(els.travelFavoriteSummary, warnings[0], "warning");
  } catch (error) {
    state.travelFavorites = { version: 1, favorites: {} };
    setLine(els.travelFavoriteSummary, `Travel favorites failed to load: ${error.message || error}`, "bad");
  }
}

async function saveTravelFavorites(statusMessage) {
  if (!window.msbt || typeof window.msbt.saveTravelFavorites !== "function") {
    setLine(els.travelFavoriteSummary, "Travel favorites storage is not available in this build.", "warning");
    return false;
  }
  const result = await window.msbt.saveTravelFavorites(state.travelFavorites);
  if (!result || !result.ok) {
    setLine(
      els.travelFavoriteSummary,
      `Travel favorites failed to save: ${result && result.message ? result.message : "Unknown save error"}`,
      "bad"
    );
    return false;
  }
  state.travelFavorites = result.data || state.travelFavorites;
  const warning = Array.isArray(result.warnings) && result.warnings.length ? ` ${result.warnings[0]}` : "";
  renderTravelFavorites();
  setLine(els.travelFavoriteSummary, `${statusMessage}${warning}`, warning ? "warning" : "ok");
  return true;
}

async function addTravelFavorite(kind) {
  const safeKind = String(kind || "").trim().toLowerCase();
  let id = "";
  let world = "";
  if (safeKind === "map") {
    id = state.selectedMap || getValue(els.travelMapList);
  } else if (safeKind === "station") {
    id = state.selectedStation || getValue(els.travelStationList);
    const station = (state.travelStations || []).find((row) => String(row.station || "") === id);
    world = station ? String(station.world || "") : "";
  } else {
    setLine(els.travelFavoriteSummary, "Unknown favorite type.", "warning");
    return;
  }
  if (!id) {
    setLine(els.travelFavoriteSummary, `Select a ${safeKind} before adding it to favorites.`, "warning");
    return;
  }
  const key = travelFavoriteKey(safeKind, id);
  if (!key) {
    setLine(els.travelFavoriteSummary, `Cannot favorite invalid ${safeKind} id.`, "warning");
    return;
  }
  if (travelFavoriteEntry(key)) {
    state.travelFavoriteSelectedKey = key;
    renderTravelFavorites();
    setLine(els.travelFavoriteSummary, "Already in travel favorites.", "warning");
    return;
  }
  const now = new Date().toISOString();
  state.travelFavorites = {
    version: 1,
    favorites: {
      ...travelFavoritesMap(),
      [key]: {
        kind: safeKind,
        id,
        world,
        label: travelFavoriteDefaultLabel(safeKind, id, world),
        note: "",
        created_at: now,
        updated_at: now
      }
    }
  };
  state.travelFavoriteSelectedKey = key;
  await saveTravelFavorites(`Added ${safeKind} favorite.`);
}

async function removeSelectedTravelFavorite() {
  const key = String(state.travelFavoriteSelectedKey || "").trim();
  if (!key || !travelFavoriteEntry(key)) {
    setLine(els.travelFavoriteSummary, "Select a travel favorite first.", "warning");
    return;
  }
  const favorites = { ...travelFavoritesMap() };
  delete favorites[key];
  state.travelFavorites = { version: 1, favorites };
  state.travelFavoriteSelectedKey = "";
  await saveTravelFavorites("Removed travel favorite.");
}

async function saveSelectedTravelFavoriteMeta() {
  const key = String(state.travelFavoriteSelectedKey || "").trim();
  const entry = travelFavoriteEntry(key);
  if (!entry) {
    setLine(els.travelFavoriteSummary, "Select a travel favorite before editing it.", "warning");
    return;
  }
  const label = String(getValue(els.travelFavoriteLabel) || entry.id || "").replace(/\s+/g, " ").trim().slice(0, 160);
  const note = String(getValue(els.travelFavoriteNote) || "").replace(/\s+/g, " ").trim().slice(0, 320);
  state.travelFavorites = {
    version: 1,
    favorites: {
      ...travelFavoritesMap(),
      [key]: {
        ...entry,
        label: label || entry.id,
        note,
        updated_at: new Date().toISOString()
      }
    }
  };
  await saveTravelFavorites("Saved travel favorite label/note.");
}

async function travelSelectedFavorite() {
  const key = String(state.travelFavoriteSelectedKey || "").trim();
  const entry = travelFavoriteEntry(key);
  if (!entry) {
    setLine(els.travelFavoriteSummary, "Select a travel favorite first.", "warning");
    return;
  }
  if (entry.kind === "station") {
    await runAction("travel_to_station", { travel_station: entry.id }, els.travelOutput, 30000);
    return;
  }
  await runAction("travel_to_map", { travel_map: entry.id }, els.travelOutput, 30000);
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

function devActorMyFavoriteNote(actorName) {
  const entry = devMyFavoriteEntry(actorName);
  return String((entry && entry.note) || "").trim();
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
    source = "Example List label";
  } else if (mapped) {
    primary = mapped;
    secondary = reference ? `Reference: ${reference}` : "";
    source = "Mapped display name; reference label kept as metadata";
  } else if (!invalidReference && reference) {
    primary = reference;
    secondary = derived && devNormalizeSearch(derived) !== devNormalizeSearch(reference) ? `Derived: ${derived}` : "";
    source = "Example List label";
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
  const note = devActorMyFavoriteNote(actorName);
  const mapped = devActorDisplayName(actorName);
  const reference = devActorFavoriteLabel(actorName);
  const derived = devActorDerivedLabel(actorName);
  const primary = saved || mapped || reference || derived || actorName;
  const secondary = mapped && devNormalizeSearch(mapped) !== devNormalizeSearch(primary)
    ? `Mapped: ${mapped}`
    : reference && devNormalizeSearch(reference) !== devNormalizeSearch(primary)
      ? `Reference: ${reference}`
      : actorName;
  return { primary, secondary, note };
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

function devReferenceBossPickActors() {
  return devReferenceQuickPickActors().filter((actorName) => {
    const meta = devActorMetadata(actorName);
    return Boolean(meta.is_boss || meta.is_true_boss);
  });
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

function devFilteredReferenceBossPicks(query) {
  return devReferenceBossPickActors().filter((actorName) => {
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
  if (els.devMyFavoriteSaveBtn) {
    els.devMyFavoriteSaveBtn.disabled = !isFavorite;
  }
  if (els.devMyFavoriteLabel || els.devMyFavoriteNote) {
    const entry = isFavorite ? (devMyFavoriteEntry(actorName) || {}) : null;
    if (els.devMyFavoriteLabel) {
      els.devMyFavoriteLabel.disabled = !isFavorite;
      els.devMyFavoriteLabel.value = entry
        ? String(entry.label || actorName || "")
        : "";
      els.devMyFavoriteLabel.placeholder = isFavorite ? "Favorite display name" : "Select a favorite first";
    }
    if (els.devMyFavoriteNote) {
      els.devMyFavoriteNote.disabled = !isFavorite;
      els.devMyFavoriteNote.value = entry ? String(entry.note || "") : "";
      els.devMyFavoriteNote.placeholder = isFavorite ? "Optional personal note" : "Select a favorite first";
    }
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
  if (devActorMyFavoriteNote(actorName)) {
    els.devActorDetails.appendChild(makeDevDetailRow("My note", devActorMyFavoriteNote(actorName)));
  }

  const note = document.createElement("div");
  note.className = "dev-detail-note";
  note.textContent = "Notes come from the local actor list, not live game checks.";
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
  spawn.title = `Spawn ${actorName}`;
  spawn.addEventListener("click", (event) => {
    event.stopPropagation();
    spawnDevActor(actorName);
  });

  const actions = document.createElement("div");
  actions.className = "dev-row-actions";
  const favoriteButton = document.createElement("button");
  favoriteButton.type = "button";
  favoriteButton.className = "dev-favorite-button";
  const isFavorite = devIsMyFavorite(actorName);
  favoriteButton.textContent = isFavorite ? "Rem" : "Fav";
  favoriteButton.title = isFavorite ? "Remove from My Favorites" : "Add to My Favorites";
  favoriteButton.addEventListener("click", (event) => {
    event.stopPropagation();
    useDevActor(actorName);
    if (devIsMyFavorite(actorName)) {
      removeSelectedDevMyFavorite();
    } else {
      addSelectedDevMyFavorite();
    }
  });
  actions.appendChild(favoriteButton);

  if (isFavorite || options.rowClass === "my-favorite-row") {
    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.className = "dev-edit-button";
    editButton.textContent = "Edit";
    editButton.title = "Edit favorite label/note";
    editButton.addEventListener("click", (event) => {
      event.stopPropagation();
      useDevActor(actorName);
      renderDevActors();
      if (els.devMyFavoriteLabel) els.devMyFavoriteLabel.focus();
    });
    actions.appendChild(editButton);
  }

  const label = document.createElement("button");
  label.type = "button";
  label.className = "dev-actor-label";
  label.title = actorName;
  label.addEventListener("click", () => {
    useDevActor(actorName);
    renderDevActors();
  });

  const displayName = options.titleText || devActorDisplayName(actorName) || actorName;
  const title = document.createElement("span");
  title.className = "dev-actor-title";
  title.textContent = displayName;

  const sep = document.createElement("span");
  sep.className = "dev-actor-sep";
  sep.textContent = " | ";

  const key = document.createElement("span");
  key.className = "dev-actor-key";
  key.textContent = actorName;

  label.append(title, sep, key);

  const metaText = String(options.metaText || "").trim();
  if (metaText) {
    const meta = document.createElement("span");
    meta.className = "dev-actor-meta";
    meta.textContent = ` ${metaText}`;
    label.appendChild(meta);
  }

  row.append(spawn, actions, label);
  return row;
}

function devActorShortMeta(actorName, options = {}) {
  const parts = [];
  if (options.secondary) parts.push(options.secondary);
  if (options.bossTag) parts.push(options.bossTag);
  if (options.note) parts.push(options.note);
  const groupName = options.groupName || devActorPrimaryCategory(actorName);
  if (groupName && groupName !== "Characters") parts.push(groupName);
  return parts.filter(Boolean).join(" · ");
}

function renderDevBossPicks(query, rawQuery) {
  if (!els.devBossPickRows) return;

  const bossActors = devReferenceBossPickActors();
  state.devSpawnerFilteredBossPicks = devFilteredReferenceBossPicks(query);

  els.devBossPickRows.innerHTML = "";
  if (!bossActors.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = "No active boss character picks are packaged in the local catalog.";
    els.devBossPickRows.appendChild(empty);
  } else if (!state.devSpawnerFilteredBossPicks.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = query
      ? `No active boss character picks match "${rawQuery}". Clear Search actors to see all active boss picks.`
      : "No active boss character picks are visible.";
    els.devBossPickRows.appendChild(empty);
  } else {
    const groupNode = document.createElement("details");
    groupNode.className = "dev-actor-group";
    groupNode.open = true;
    const summary = document.createElement("summary");
    summary.textContent = `Boss Characters (${state.devSpawnerFilteredBossPicks.length})`;
    groupNode.appendChild(summary);
    state.devSpawnerFilteredBossPicks.forEach((actorName) => {
      const labelInfo = devQuickPickLabelInfo(actorName);
      const meta = devActorMetadata(actorName);
      const note = devActorMyFavoriteNote(actorName);
      groupNode.appendChild(makeDevActorRow(actorName, {
        metaText: devActorShortMeta(actorName, {
          secondary: labelInfo.secondary,
          bossTag: meta.is_true_boss ? "True boss" : (meta.is_boss ? "Boss" : ""),
          note
        }),
        rowClass: "boss-pick-row",
        titleText: labelInfo.primary
      }));
    });
    els.devBossPickRows.appendChild(groupNode);
  }

  const searchNote = query ? ` | search: "${rawQuery}"` : "";
  setLine(
    els.devBossPickSummary,
    `${state.devSpawnerFilteredBossPicks.length} shown / ${bossActors.length} active boss character picks${searchNote}`,
    state.devSpawnerFilteredBossPicks.length ? "ok" : "warning"
  );
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
    empty.textContent = "No Example List entries are packaged in the local catalog.";
    els.devQuickPickRows.appendChild(empty);
  } else if (!state.devSpawnerFilteredQuickPicks.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = query
      ? `No Example List entries match "${rawQuery}". Clear Search actors to see all packaged examples.`
      : "No Example List entries are available in the active local actor catalog.";
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
        groupNode.appendChild(makeDevActorRow(actorName, {
          groupName: group.name,
          metaText: devActorShortMeta(actorName, {
            secondary: labelInfo.secondary,
            groupName: group.name
          }),
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
    `${state.devSpawnerFilteredQuickPicks.length} shown / ${availableActors.length} available / ${favoriteCount} Example List entries${searchNote}${omittedNote}`,
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
        groupNode.appendChild(makeDevActorRow(actorName, {
          groupName: group.name,
          metaText: devActorShortMeta(actorName, {
            secondary: labelInfo.secondary,
            note: labelInfo.note,
            groupName: group.name
          }),
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
  state.devSpawnerFilteredBossPicks = devFilteredReferenceBossPicks(query);
  state.devSpawnerFilteredQuickPicks = devFilteredReferenceQuickPicks(query);
  state.devSpawnerFilteredMyFavorites = devFilteredMyFavorites(query);

  if (
    state.devSpawnerSelectedActor
    && !state.devSpawnerFilteredActors.includes(state.devSpawnerSelectedActor)
    && !state.devSpawnerFilteredBossPicks.includes(state.devSpawnerSelectedActor)
    && !state.devSpawnerFilteredMyFavorites.includes(state.devSpawnerSelectedActor)
  ) {
    clearDevActorSelection();
  }

  renderDevBossPicks(query, rawQuery);
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
        note: "",
        created_at: now,
        updated_at: now
      }
    }
  };
  await saveDevSpawnerFavorites(`Added ${devFavoriteLabelForActor(actorName)} to My Favorites.`);
}

async function editSelectedDevMyFavorite() {
  const actorName = String(state.devSpawnerSelectedActor || getValue(els.devActorName) || "").trim();
  if (!actorName || !devIsMyFavorite(actorName)) {
    setLine(els.devMyFavoriteSummary, "Select a saved favorite before editing it.", "warning");
    renderDevMyFavoriteControls();
    return;
  }
  const current = devMyFavoriteEntry(actorName) || {};
  const fallbackLabel = devFavoriteLabelForActor(actorName);
  const label = els.devMyFavoriteLabel
    ? getValue(els.devMyFavoriteLabel)
    : String(current.label || fallbackLabel || actorName);
  const note = els.devMyFavoriteNote
    ? getValue(els.devMyFavoriteNote)
    : String(current.note || "");
  const now = new Date().toISOString();
  state.devSpawnerMyFavorites = {
    version: 1,
    favorites: {
      ...devMyFavoritesMap(),
      [actorName]: {
        ...current,
        label: String(label || fallbackLabel || actorName).replace(/\s+/g, " ").trim(),
        note: String(note || "").replace(/\s+/g, " ").trim(),
        created_at: current.created_at || now,
        updated_at: now
      }
    }
  };
  await saveDevSpawnerFavorites(`Updated ${devFavoriteLabelForActor(actorName)} in My Favorites.`);
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

function devLogoLineInputs() {
  return els.devLogoLines ? Array.from(els.devLogoLines.querySelectorAll("input")) : [];
}

function addDevLogoLine(value = "") {
  if (!els.devLogoLines) return;
  const lineNumber = devLogoLineInputs().length + 1;
  const label = document.createElement("label");
  label.textContent = `Line ${lineNumber} `;
  const input = document.createElement("input");
  input.type = "text";
  input.value = value;
  label.appendChild(input);
  els.devLogoLines.appendChild(label);
  input.focus();
}

function removeDevLogoLine() {
  const inputs = devLogoLineInputs();
  if (!els.devLogoLines || inputs.length <= 1) {
    setLine(els.devSpawnerWarning, "Barrel Logo needs at least one text line.", "warning");
    return;
  }
  const lastLabel = inputs[inputs.length - 1].closest("label");
  if (lastLabel) lastLabel.remove();
}

function normalizedDevLogoText() {
  const lineInputs = devLogoLineInputs();
  const text = lineInputs.length
    ? lineInputs.map((input) => input.value).join("\n")
    : getValue(els.devLogoText);
  if (els.devLogoText) {
    els.devLogoText.value = text;
  }
  return text
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
    lines.push(`MSBT mod version (running): ${diagnostics.msbt_mod_version || "unknown"}`);
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

const INV_EQUIP_SLOTS = [
  { slot: 0, label: "Weapon 1" },
  { slot: 1, label: "Weapon 2" },
  { slot: 2, label: "Weapon 3" },
  { slot: 3, label: "Weapon 4" },
  { slot: 4, label: "Shield" },
  { slot: 5, label: "Ordnance" },
  { slot: 6, label: "Repkit" },
  { slot: 7, label: "Enhancement" },
  { slot: 8, label: "Class Mod" }
];

const INV_RARITY_RANK = {
  Pearlescent: 6,
  Legendary: 5,
  Epic: 4,
  Rare: 3,
  Uncommon: 2,
  Common: 1
};

function invEntryKey(entry, fallback = "") {
  if (!entry) return fallback;
  return String(entry.serial || "") || `${entry.label || ""}:${entry.slot}:${fallback}`;
}

function invRarityClass(rarity) {
  const key = String(rarity || "").trim().toLowerCase();
  if (!key) return "inv-rarity-unknown";
  if (key.includes("pearl")) return "inv-rarity-pearlescent";
  if (key.includes("legend")) return "inv-rarity-legendary";
  if (key.includes("epic")) return "inv-rarity-epic";
  if (key.includes("rare")) return "inv-rarity-rare";
  if (key.includes("uncommon")) return "inv-rarity-uncommon";
  if (key.includes("common")) return "inv-rarity-common";
  return "inv-rarity-unknown";
}

function invDisplayName(entry) {
  if (!entry) return "Empty";
  return String(entry.display_name || entry.summary || entry.label || "Item").trim() || "Item";
}

function invFillSelect(select, values) {
  if (!select) return;
  const current = select.value || "All";
  const unique = ["All", ...Array.from(new Set(values.filter(Boolean))).sort((a, b) => String(a).localeCompare(String(b)))];
  select.innerHTML = "";
  unique.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
  select.value = unique.includes(current) ? current : "All";
}

function invRefreshFilterOptions() {
  const pool = [...state.invEquipped, ...state.invBackpack];
  invFillSelect(els.invRarityFilter, pool.map((e) => e.rarity).filter(Boolean));
  invFillSelect(els.invDamageFilter, pool.map((e) => e.damage_type).filter(Boolean));
  invFillSelect(els.invTypeFilter, pool.map((e) => e.item_type || e.character_class).filter(Boolean));
  invFillSelect(els.invManufacturerFilter, pool.map((e) => e.manufacturer).filter(Boolean));
}

function invCompare(a, b) {
  const sort = state.invSort || "recent";
  // Ascending baseline; flipped when invSortDir === "desc" (default ↓).
  let cmp = 0;
  if (sort === "rarity") {
    const ra = INV_RARITY_RANK[String(a.rarity || "")] || 0;
    const rb = INV_RARITY_RANK[String(b.rarity || "")] || 0;
    cmp = ra - rb;
  } else if (sort === "type") {
    cmp = String(a.item_type || a.category || "").localeCompare(String(b.item_type || b.category || ""));
  } else if (sort === "level") {
    const la = Number(a.level);
    const lb = Number(b.level);
    const na = Number.isFinite(la) ? la : -1;
    const nb = Number.isFinite(lb) ? lb : -1;
    cmp = na - nb;
  } else if (sort === "manufacturer") {
    cmp = String(a.manufacturer || "").localeCompare(String(b.manufacturer || ""));
  } else {
    // recent: backpack_index ascending = older/lower index first
    const ia = Number(a.backpack_index);
    const ib = Number(b.backpack_index);
    const na = Number.isFinite(ia) ? ia : 1e9;
    const nb = Number.isFinite(ib) ? ib : 1e9;
    cmp = na - nb;
  }
  if (cmp && state.invSortDir !== "asc") cmp = -cmp;
  if (cmp) return cmp;
  return invDisplayName(a).localeCompare(invDisplayName(b));
}

function invUpdateSortDirButton() {
  if (!els.invSortDirBtn) return;
  const desc = state.invSortDir !== "asc";
  els.invSortDirBtn.textContent = desc ? "↓" : "↑";
  els.invSortDirBtn.title = desc
    ? "Sort direction: high → low (click for low → high)"
    : "Sort direction: low → high (click for high → low)";
  els.invSortDirBtn.setAttribute("aria-label", els.invSortDirBtn.title);
}

function invApplyFilters() {
  const term = String(els.invSearch && els.invSearch.value || "").trim().toLowerCase();
  const rarity = String(els.invRarityFilter && els.invRarityFilter.value || "All");
  const damage = String(els.invDamageFilter && els.invDamageFilter.value || "All");
  const type = String(els.invTypeFilter && els.invTypeFilter.value || "All");
  const manufacturer = String(els.invManufacturerFilter && els.invManufacturerFilter.value || "All");
  const category = state.invCategory || "All";
  const filtered = state.invBackpack.filter((entry) => {
    if (category !== "All" && String(entry.category || "Other") !== category) return false;
    if (rarity !== "All" && String(entry.rarity || "") !== rarity) return false;
    if (damage !== "All" && String(entry.damage_type || "") !== damage) return false;
    if (manufacturer !== "All" && String(entry.manufacturer || "") !== manufacturer) return false;
    const entryType = String(entry.item_type || entry.character_class || "");
    if (type !== "All" && entryType !== type) return false;
    if (!term) return true;
    const hay = [
      invDisplayName(entry),
      entry.label,
      entry.summary,
      entry.manufacturer,
      entry.item_type,
      entry.character_class,
      entry.category,
      entry.rarity,
      entry.damage_type,
      entry.serial,
      entry.set
    ].join(" ").toLowerCase();
    return hay.includes(term);
  });
  filtered.sort(invCompare);
  state.invFiltered = filtered;
  const maxPage = Math.max(0, Math.ceil(filtered.length / state.invPageSize) - 1);
  if (state.invPage > maxPage) state.invPage = maxPage;
  if (els.invFilterCount) els.invFilterCount.textContent = `Filter: ${filtered.length.toLocaleString()}`;
}

function invMakeCard(entry, { slotLabel = "", empty = false, equipped = false } = {}) {
  const card = document.createElement("button");
  card.type = "button";
  const rarityClass = empty ? "inv-rarity-unknown" : invRarityClass(entry && entry.rarity);
  card.className = `${equipped || empty ? "inv-slot-card" : "inv-item-card"} ${rarityClass}${empty ? " empty" : ""}`;
  if (!empty && entry && invEntryKey(entry) === state.invSelectedKey) card.classList.add("selected");
  if (slotLabel) {
    const lab = document.createElement("div");
    lab.className = "inv-slot-label";
    lab.textContent = slotLabel;
    card.appendChild(lab);
  }
  const name = document.createElement("div");
  name.className = "inv-item-name";
  name.textContent = empty ? "Empty" : invDisplayName(entry);
  card.appendChild(name);
  const meta = document.createElement("div");
  meta.className = "inv-item-meta";
  if (empty) {
    meta.textContent = "—";
  } else {
    const rarity = String(entry.rarity || "Unknown");
    const level = Number(entry.level);
    const bits = [];
    bits.push(`<span class="inv-rarity-dot"></span>${rarity}`);
    if (Number.isFinite(level) && level >= 0) bits.push(`L${level}`);
    const typeBit = String(entry.item_type || entry.character_class || entry.category || "").trim();
    if (typeBit) bits.push(typeBit);
    if (entry.manufacturer) bits.push(String(entry.manufacturer));
    if (entry.damage_type) bits.push(String(entry.damage_type));
    meta.innerHTML = bits.join(" · ");
  }
  card.appendChild(meta);
  if (!empty && entry) {
    card.addEventListener("click", () => invSelectEntry(entry));
  }
  return card;
}

function invRenderEquipped() {
  if (!els.invEquippedGrid) return;
  els.invEquippedGrid.innerHTML = "";
  const bySlot = new Map();
  state.invEquipped.forEach((entry) => {
    const slot = Number(entry.slot);
    if (Number.isFinite(slot) && slot >= 0) bySlot.set(slot, entry);
  });
  INV_EQUIP_SLOTS.forEach(({ slot, label }) => {
    const entry = bySlot.get(slot);
    const card = entry
      ? invMakeCard(entry, { slotLabel: label, equipped: true })
      : invMakeCard(null, { slotLabel: label, empty: true, equipped: true });
    els.invEquippedGrid.appendChild(card);
  });
  // Extra equipped rows (active weapon / unknown slots)
  state.invEquipped.forEach((entry) => {
    const slot = Number(entry.slot);
    if (Number.isFinite(slot) && slot >= 0 && slot <= 8) return;
    els.invEquippedGrid.appendChild(
      invMakeCard(entry, { slotLabel: entry.label || "Equipped", equipped: true })
    );
  });
}

function invRenderBackpack() {
  if (!els.invBackpackGrid) return;
  els.invBackpackGrid.innerHTML = "";
  const start = state.invPage * state.invPageSize;
  const pageItems = state.invFiltered.slice(start, start + state.invPageSize);
  if (!pageItems.length) {
    const empty = document.createElement("div");
    empty.className = "dev-empty-row";
    empty.textContent = state.invBackpack.length
      ? "No items match the current filters."
      : "No backpack items loaded yet.";
    els.invBackpackGrid.appendChild(empty);
  } else {
    pageItems.forEach((entry) => els.invBackpackGrid.appendChild(invMakeCard(entry)));
  }
  const totalPages = Math.max(1, Math.ceil(state.invFiltered.length / state.invPageSize) || 1);
  if (els.invPageLabel) {
    els.invPageLabel.textContent = `Page ${Math.min(state.invPage + 1, totalPages)} / ${totalPages}`;
  }
  if (els.invPrevPageBtn) els.invPrevPageBtn.disabled = state.invPage <= 0;
  if (els.invNextPageBtn) {
    els.invNextPageBtn.disabled = start + state.invPageSize >= state.invFiltered.length;
  }
  if (els.invBackpackCount) {
    const trunc = state.invTruncated ? " (capped)" : "";
    els.invBackpackCount.textContent =
      `${state.invFiltered.length.toLocaleString()} shown / ${state.invBackpack.length.toLocaleString()} backpack · ${state.invEquipped.length} equipped${trunc}`;
  }
}

function invRenderAll() {
  invApplyFilters();
  invRenderEquipped();
  invRenderBackpack();
}

function invSelectEntry(entry) {
  if (!entry) return;
  state.invSelectedEntry = entry;
  state.invSelectedKey = invEntryKey(entry);
  if (els.invDetail) els.invDetail.classList.remove("hidden");
  if (els.invDetailTitle) els.invDetailTitle.textContent = invDisplayName(entry);
  if (els.invDetailMeta) {
    const bits = [
      entry.label,
      entry.category,
      entry.item_type || entry.character_class,
      entry.manufacturer,
      entry.rarity,
      entry.damage_type,
      Number(entry.level) >= 0 ? `L${entry.level}` : ""
    ].filter(Boolean);
    els.invDetailMeta.textContent = bits.join(" · ");
  }
  if (els.invDetailSerial) els.invDetailSerial.value = String(entry.serial || "");
  invRenderAll();
}

function invClearDetail() {
  state.invSelectedEntry = null;
  state.invSelectedKey = "";
  if (els.invDetail) els.invDetail.classList.add("hidden");
  if (els.invDetailSerial) els.invDetailSerial.value = "";
  invRenderAll();
}

function invActionData(result) {
  return result && result.data !== undefined ? result.data : result;
}

function invEntriesFromReadResult(result) {
  const data = invActionData(result);
  if (!data || typeof data !== "object") return [];
  if (data.read_serials && Array.isArray(data.read_serials.entries)) {
    return data.read_serials.entries;
  }
  if (Array.isArray(data.entries)) return data.entries;
  return [];
}

function invNormalizeInventoryBlob(inventory) {
  if (!inventory || typeof inventory !== "object") {
    return { equipped: [], backpack: [], truncated: false };
  }
  return {
    equipped: Array.isArray(inventory.equipped) ? inventory.equipped : [],
    backpack: Array.isArray(inventory.backpack) ? inventory.backpack : [],
    truncated: Boolean(inventory.truncated)
  };
}

function invMessageLooksUnknown(message) {
  return /unknown action|unknown quick menu action/i.test(String(message || ""));
}

function invInventoryTargetPayload() {
  const target = String(
    (els.invTargetSelect && els.invTargetSelect.value) || state.selectedTarget || ""
  ).trim();
  return target ? { target_player: target } : {};
}

async function refreshInventoryFallback(targetPayload = {}) {
  // Older installed .sdkmods only expose read_equipped_serials / read_backpack_serials.
  const eqResult = await bridgeAction("read_equipped_serials", targetPayload, 60000);
  const bpResult = await bridgeAction("read_backpack_serials", targetPayload, 60000);
  const eqData = invActionData(eqResult);
  const bpData = invActionData(bpResult);
  if ((eqData && eqData.queued) || (bpData && bpData.queued)) {
    return {
      ok: true,
      data: {
        ok: true,
        queued: true,
        message:
          "Inventory read still queued — unpause in-game, then press Refresh Inventory again.",
        reading: String((eqData && eqData.reading) || (bpData && bpData.reading) || "")
      }
    };
  }
  const equipped = invEntriesFromReadResult(eqResult).filter((entry) => {
    const origin = String((entry && entry.origin) || "");
    if (origin === "backpack") return false;
    const slot = Number(entry && entry.slot);
    return origin === "equipped" || origin === "active_weapon" || (Number.isFinite(slot) && slot >= 0 && slot <= 64);
  });
  const equippedSerials = new Set(equipped.map((e) => String(e.serial || "")).filter(Boolean));
  const backpack = invEntriesFromReadResult(bpResult).filter((entry) => {
    const serial = String((entry && entry.serial) || "");
    if (serial && equippedSerials.has(serial)) return false;
    const origin = String((entry && entry.origin) || "");
    if (origin === "equipped" || origin === "active_weapon") return false;
    const slot = Number(entry && entry.slot);
    if (Number.isFinite(slot) && slot >= 0 && slot <= 64) return false;
    return true;
  });
  const eqOk = actionSucceeded(eqResult) || equipped.length > 0;
  const bpOk = actionSucceeded(bpResult) || backpack.length > 0;
  const ok = eqOk || bpOk;
  const reading = String((eqData && eqData.reading) || (bpData && bpData.reading) || "");
  const message = ok
    ? `${reading || "Inventory"}: ${equipped.length} equipped, ${backpack.length} backpack (legacy read).`
    : resultMessage(eqResult) || resultMessage(bpResult) || "Inventory refresh failed.";
  return {
    ok,
    data: {
      ok,
      message,
      reading,
      selected_player: (eqData && eqData.selected_player) || (bpData && bpData.selected_player),
      selected_player_index:
        (eqData && eqData.selected_player_index) ?? (bpData && bpData.selected_player_index),
      inventory: {
        equipped,
        backpack,
        equipped_count: equipped.length,
        backpack_count: backpack.length,
        truncated: false
      }
    }
  };
}

async function refreshInventory() {
  const targetPayload = invInventoryTargetPayload();
  const target = String(targetPayload.target_player || "").trim();
  if (target) {
    const setResult = await setTarget(target, { keepBoostScope: true });
    if (setResult && setResult.data && setResult.data.ok === false) {
      setLine(els.invStatus, resultMessage(setResult) || "Could not set inventory target.", "warning");
      return setResult;
    }
  } else if (!state.players.length) {
    setLine(els.invStatus, "Refresh Status on Boosting first, then pick a party player.", "warning");
    if (els.invReading) els.invReading.textContent = "Reading: none";
    return null;
  }

  setLine(els.invStatus, "Reading inventory from bridge...", "warning");
  if (els.invReading) {
    const selectedPlayer = state.players.find(
      (player) => String(playerValue(player)) === String(state.selectedTarget || target)
    );
    els.invReading.textContent = selectedPlayer
      ? `Reading: ${playerLabel(selectedPlayer)}…`
      : "Reading: …";
  }
  appendActivity("Inventory: refreshing...");
  let result = await bridgeAction("read_inventory", targetPayload, 60000);
  let data = invActionData(result);
  if (data && data.queued) {
    setLine(
      els.invStatus,
      resultMessage(result) ||
        "Inventory read still queued — unpause in-game, then press Refresh Inventory again.",
      "warning"
    );
    appendActivity("Inventory: queued (retry after unpause).");
    return result;
  }
  let inventory = data && data.inventory ? invNormalizeInventoryBlob(data.inventory) : null;
  const unknown = invMessageLooksUnknown(data && data.message);
  const missingShape = !inventory || (!inventory.equipped.length && !inventory.backpack.length && !actionSucceeded(result));
  if (unknown || missingShape || !(data && data.inventory)) {
    appendActivity("Inventory: falling back to read_equipped + read_backpack...");
    result = await refreshInventoryFallback(targetPayload);
    data = invActionData(result);
    inventory = data && data.inventory ? invNormalizeInventoryBlob(data.inventory) : { equipped: [], backpack: [], truncated: false };
  }
  const ok = Boolean(data && data.ok !== false) && (actionSucceeded(result) || (inventory.equipped.length + inventory.backpack.length) > 0);
  state.invEquipped = inventory.equipped;
  state.invBackpack = inventory.backpack;
  state.invTruncated = Boolean(inventory.truncated);
  state.invReading = String((data && data.reading) || "");
  state.invPage = 0;
  state.invSelectedEntry = null;
  state.invSelectedKey = "";
  if (els.invDetail) els.invDetail.classList.add("hidden");
  if (els.invReading) {
    els.invReading.textContent = state.invReading || "Reading: none";
  }
  invRefreshFilterOptions();
  invRenderAll();
  const message = resultMessage(result) || (ok ? "Inventory refreshed." : "Inventory refresh failed.");
  setLine(els.invStatus, message, ok ? "ok" : "warning");
  appendActivity(`Inventory: ${message}`);
  return result;
}

async function invCopySerial() {
  const serial = String((state.invSelectedEntry && state.invSelectedEntry.serial) || (els.invDetailSerial && els.invDetailSerial.value) || "").trim();
  if (!serial) {
    setLine(els.invStatus, "No serial selected.", "warning");
    return;
  }
  try {
    await navigator.clipboard.writeText(serial);
    setLine(els.invStatus, "Serial copied.", "ok");
  } catch (_err) {
    setLine(els.invStatus, "Clipboard write failed.", "bad");
  }
}

async function invCopyVisibleSerials() {
  const serials = state.invFiltered.map((e) => String(e.serial || "").trim()).filter((s) => s.startsWith("@U"));
  if (!serials.length) {
    setLine(els.invStatus, "No visible serials to copy.", "warning");
    return;
  }
  try {
    await navigator.clipboard.writeText(serials.join("\n"));
    setLine(els.invStatus, `Copied ${serials.length} visible serial(s).`, "ok");
  } catch (_err) {
    setLine(els.invStatus, "Clipboard write failed.", "bad");
  }
}

function invSendToSerialRewards() {
  const serial = String((state.invSelectedEntry && state.invSelectedEntry.serial) || "").trim();
  if (!serial) {
    setLine(els.invStatus, "Select an item first.", "warning");
    return;
  }
  if (els.boostSerialText) els.boostSerialText.value = serial;
  switchTab("boosting");
  setLine(els.invStatus, "Serial pasted into Serial Rewards on Boosting.", "ok");
  appendActivity("Inventory: sent serial to Serial Rewards.");
}

function invOpenInSerialTools() {
  const serial = String((state.invSelectedEntry && state.invSelectedEntry.serial) || "").trim();
  if (!serial) {
    setLine(els.invStatus, "Select an item first.", "warning");
    return;
  }
  if (els.serialToolsInput) els.serialToolsInput.value = serial;
  switchTab("serial-tools");
  void convertSerialTools();
  setLine(els.invStatus, "Opened serial in Serial Tools.", "ok");
}

function invOpenInMattEditor() {
  const serial = String((state.invSelectedEntry && state.invSelectedEntry.serial) || "").trim();
  if (!serial) {
    setLine(els.invStatus, "Select an item first.", "warning");
    return;
  }
  if (els.serialToolsInput) els.serialToolsInput.value = serial;
  if (els.boostSerialText) els.boostSerialText.value = serial;
  switchTab("matt-editor");
  setLine(els.invStatus, "Serial ready — use Matt Editor with Serial Tools / pasted @U.", "ok");
  appendActivity("Inventory: opened item toward Matt Editor.");
}

function invPlayerLabelForValue(value) {
  const target = String(value || "").trim();
  if (!target) return "none";
  const player = state.players.find((row) => String(playerValue(row)) === target);
  return player ? playerLabel(player) : target;
}

async function invGiveSerialToGame() {
  const serial = String(
    (state.invSelectedEntry && state.invSelectedEntry.serial)
    || (els.invDetailSerial && els.invDetailSerial.value)
    || ""
  ).trim();
  if (!serial || !serial.startsWith("@U")) {
    setLine(els.invStatus, "Select an item with a valid @U serial first.", "warning");
    return;
  }
  const giveTarget = String((els.invGiveTargetSelect && els.invGiveTargetSelect.value) || state.invGiveTarget || "").trim();
  if (!giveTarget) {
    setLine(els.invStatus, "Pick a Give-to player (separate from Party player / viewing).", "warning");
    return;
  }
  state.invGiveTarget = giveTarget;
  const copies = getInt(els.invSerialCopies, 1, 50, 1);
  if (els.invSerialCopies) els.invSerialCopies.value = String(copies);
  const giveLabel = invPlayerLabelForValue(giveTarget);
  const viewLabel = invPlayerLabelForValue(
    (els.invTargetSelect && els.invTargetSelect.value) || ""
  );
  setLine(
    els.invStatus,
    `Sending ${copies}× to ${giveLabel} (viewing ${viewLabel || "n/a"})...`,
    "warning"
  );
  appendActivity(`Inventory: give ${copies}× serial to ${giveLabel} (view ${viewLabel || "n/a"}).`);

  const setResult = await setTarget(giveTarget, { keepBoostScope: true });
  if (!(setResult && setResult.data && setResult.data.ok)) {
    const message = resultMessage(setResult) || "Could not set give-to player.";
    setLine(els.invStatus, message, "bad");
    return;
  }

  const result = await sendSerialPayload(
    "selected",
    serial,
    false,
    60,
    els.boostOutput,
    copies,
    "Inventory"
  );
  const ok = actionSucceeded(result);
  const message = resultMessage(result)
    || (ok
      ? (copies > 1
        ? `Queued/sent ${copies} copies to ${giveLabel}.`
        : `Queued/sent to ${giveLabel}.`)
      : "Give serial failed.");
  setLine(els.invStatus, message, ok ? "ok" : "bad");
  appendActivity(`Inventory give: ${message}`);
  return result;
}

function wireInventoryEvents() {
  if (!els.invRefreshBtn) return;
  els.invRefreshBtn.addEventListener("click", () => void refreshInventory());
  if (els.invTargetSelect) {
    els.invTargetSelect.addEventListener("change", () => {
      const value = els.invTargetSelect.value;
      void setTarget(value, { keepBoostScope: true });
      if (els.invReading && !state.invEquipped.length && !state.invBackpack.length) {
        const selectedPlayer = state.players.find(
          (player) => String(playerValue(player)) === String(value)
        );
        els.invReading.textContent = selectedPlayer
          ? `Reading: ${playerLabel(selectedPlayer)} (press Refresh)`
          : "Reading: none";
      }
    });
  }
  if (els.invGiveTargetSelect) {
    els.invGiveTargetSelect.addEventListener("change", () => {
      state.invGiveTarget = String(els.invGiveTargetSelect.value || "");
    });
  }
  if (els.invCopyAllBtn) els.invCopyAllBtn.addEventListener("click", () => void invCopyVisibleSerials());
  if (els.invPrevPageBtn) {
    els.invPrevPageBtn.addEventListener("click", () => {
      if (state.invPage > 0) {
        state.invPage -= 1;
        invRenderBackpack();
      }
    });
  }
  if (els.invNextPageBtn) {
    els.invNextPageBtn.addEventListener("click", () => {
      const maxPage = Math.max(0, Math.ceil(state.invFiltered.length / state.invPageSize) - 1);
      if (state.invPage < maxPage) {
        state.invPage += 1;
        invRenderBackpack();
      }
    });
  }
  if (els.invSortDirBtn) {
    invUpdateSortDirButton();
    els.invSortDirBtn.addEventListener("click", () => {
      state.invSortDir = state.invSortDir === "asc" ? "desc" : "asc";
      invUpdateSortDirButton();
      state.invPage = 0;
      invRenderAll();
    });
  }
  document.querySelectorAll("[data-inv-sort]").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.disabled) return;
      const next = String(button.dataset.invSort || "recent");
      state.invSort = next;
      document.querySelectorAll("[data-inv-sort]").forEach((b) => {
        b.classList.toggle("active", b === button);
      });
      state.invPage = 0;
      invRenderAll();
    });
  });
  document.querySelectorAll("[data-inv-category]").forEach((button) => {
    button.addEventListener("click", () => {
      state.invCategory = String(button.dataset.invCategory || "All");
      document.querySelectorAll("[data-inv-category]").forEach((b) => {
        b.classList.toggle("active", b === button);
      });
      state.invPage = 0;
      invRenderAll();
    });
  });
  const filterHandler = () => {
    state.invPage = 0;
    invRenderAll();
  };
  if (els.invSearch) els.invSearch.addEventListener("input", filterHandler);
  if (els.invRarityFilter) els.invRarityFilter.addEventListener("change", filterHandler);
  if (els.invDamageFilter) els.invDamageFilter.addEventListener("change", filterHandler);
  if (els.invTypeFilter) els.invTypeFilter.addEventListener("change", filterHandler);
  if (els.invManufacturerFilter) els.invManufacturerFilter.addEventListener("change", filterHandler);
  if (els.invDetailCloseBtn) els.invDetailCloseBtn.addEventListener("click", invClearDetail);
  if (els.invCopySerialBtn) els.invCopySerialBtn.addEventListener("click", () => void invCopySerial());
  if (els.invGiveSerialBtn) els.invGiveSerialBtn.addEventListener("click", () => void invGiveSerialToGame());
  if (els.invSendRewardsBtn) els.invSendRewardsBtn.addEventListener("click", invSendToSerialRewards);
  if (els.invOpenToolsBtn) els.invOpenToolsBtn.addEventListener("click", invOpenInSerialTools);
  if (els.invOpenEditorBtn) els.invOpenEditorBtn.addEventListener("click", invOpenInMattEditor);
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-bar [data-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tabId}`);
  });
  if (window.MsbtPanelLayout && typeof window.MsbtPanelLayout.onTabShown === "function") {
    window.MsbtPanelLayout.onTabShown(tabId);
  }
  if (tabId === "matt-editor") {
    void loadEditor();
  } else if (tabId === "quick-menu") {
    void loadQuickMenuLayout({ quiet: Boolean(state.quickMenuSnapshot) });
    void refreshQuickMenuPinPanel({ quiet: true });
  } else if (tabId === "inventory") {
    if (!state.invEquipped.length && !state.invBackpack.length) {
      setLine(
        els.invStatus,
        "Pick a party player, then Refresh Inventory while in-game (listen host recommended for other players).",
        "warning"
      );
    }
  } else if (tabId === "serial-tools" || tabId === "bl4-codes" || tabId === "boosting" || tabId === "movement" || tabId === "item-pool" || tabId === "dev-spawner") {
    if (state.quickMenuSnapshot) {
      installQuickMenuAddButtons();
    } else {
      void loadQuickMenuLayout({ quiet: true }).then(() => installQuickMenuAddButtons());
    }
    if (tabId === "boosting") {
      void bridgeStatus({ quiet: true });
    }
  }
}

window.switchTab = switchTab;

function wireEvents() {
  document.querySelectorAll(".tab-bar [data-tab]").forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  });

  quickMenuNode("quickMenuRefreshBtn").addEventListener("click", () => loadQuickMenuLayout({ preserveSelection: true }));
  const rarityEquip = quickMenuNode("quickMenuRarityPanelEquip");
  if (rarityEquip) {
    rarityEquip.addEventListener("change", () => {
      void setQuickMenuRarityPanelEquipped(Boolean(rarityEquip.checked));
    });
  }
  quickMenuNode("quickMenuSaveSlotBtn").addEventListener("click", saveSelectedQuickMenuSlot);
  quickMenuNode("quickMenuClearSlotBtn").addEventListener("click", clearSelectedQuickMenuSlot);
  quickMenuNode("quickMenuClearPageBtn").addEventListener("click", clearCurrentQuickMenuPage);
  quickMenuNode("quickMenuPinLastBtn").addEventListener("click", () => pinLastCommandToSelectedSlot());
  quickMenuNode("quickMenuRepeatDropBtn").addEventListener("click", () => repeatLastDropFromQuickMenu());
  quickMenuNode("quickMenuLockToggleBtn").addEventListener("click", () => toggleQuickMenuDropLock());
  quickMenuNode("quickMenuRefreshPinBtn").addEventListener("click", () => refreshQuickMenuPinPanel());
  quickMenuNode("quickMenuAddPage").addEventListener("change", updateQuickMenuAddSlotsForPage);
  quickMenuNode("quickMenuAddCloseBtn").addEventListener("click", closeQuickMenuAddModal);
  quickMenuNode("quickMenuAddConfirmBtn").addEventListener("click", confirmQuickMenuAdd);
  quickMenuNode("quickMenuAddOpenEditorBtn").addEventListener("click", () => {
    closeQuickMenuAddModal();
    switchTab("quick-menu");
  });
  quickMenuNode("quickMenuAddModal").addEventListener("click", (event) => {
    if (event.target === quickMenuNode("quickMenuAddModal")) closeQuickMenuAddModal();
  });

  document.getElementById("statusBtn").addEventListener("click", bridgeStatus);
  document.getElementById("setTargetBtn").addEventListener("click", () => setTarget(els.targetSelect.value));
  document.getElementById("firstTargetBtn").addEventListener("click", firstPlayerTarget);
  document.getElementById("targetAllPlayersBtn").addEventListener("click", () => setBoostTargetScope("all"));
  document.getElementById("targetNonHostBtn").addEventListener("click", () => setBoostTargetScope("nonhost"));
  document.getElementById("kickTargetBtn").addEventListener("click", () => runAction("kick_player", {}, els.boostOutput, 15000));
  els.targetSelect.addEventListener("change", () => setTarget(els.targetSelect.value));

  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => runBoostActionButton(button));
  });
  document.querySelectorAll("[data-boost-serial-mode]").forEach((button) => {
    button.addEventListener("click", () => sendBoostSerial(button.dataset.boostSerialMode));
  });
  const doNotClickBtn = document.getElementById("doNotClickChallengesBtn");
  if (doNotClickBtn) {
    doNotClickBtn.addEventListener("click", async (event) => {
      if (!(event.shiftKey || event.ctrlKey || event.metaKey)) {
        setOutput(els.boostOutput, "do not click");
        return;
      }
      const result = await runAction("complete_challenges_all", {}, els.boostOutput, 30000);
      appendActivity(`do not click: ${resultMessage(result)}`);
    });
  }
  document.getElementById("boostClearSerialsBtn").addEventListener("click", () => {
    els.boostSerialText.value = "";
    setOutput(els.boostOutput, "Cleared local serial input.");
    appendActivity("Cleared Boosting serial input.");
  });
  document.getElementById("setLevelBtn").addEventListener("click", () => runScopedPlayerAction("set_level", {
    xp_track: getValue(els.xpTrack),
    level: getInt(els.xpLevel, 1, 9999999, 60)
  }, els.boostOutput, 30000));
  document.getElementById("giveCurrencyBtn").addEventListener("click", () => runScopedPlayerAction("give_currency", {
    currency_kind: getValue(els.currencyKind),
    amount: getInt(els.currencyAmount, 0, 2147483647, 1000000)
  }, els.boostOutput, 30000));
  document.getElementById("setInventorySelectedBtn").addEventListener("click", async () => {
    const result = await runScopedPlayerAction("set_backpack_bank_selected", inventoryPayload(true), els.boostOutput, 30000);
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
  wireInventoryEvents();

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
  document.querySelectorAll("[data-qm-serial-source]").forEach((button) => {
    button.addEventListener("click", () => {
      openSerialQuickMenuPin(button.dataset.qmSerialSource, button.dataset.qmSerialMode);
    });
  });

  els.bl4ReloadBtn.addEventListener("click", loadBl4Catalog);
  els.bl4RefreshGzoBtn.addEventListener("click", refreshBl4GzoCatalog);
  if (els.bl4RefreshCatalogsBtn) {
    els.bl4RefreshCatalogsBtn.addEventListener("click", () => refreshMsbtDataCatalogs({ fromBl4: true }));
  }
  if (els.refreshDataCatalogsBtn) {
    els.refreshDataCatalogsBtn.addEventListener("click", () => refreshMsbtDataCatalogs({ fromBl4: false }));
  }
  if (window.msbt && typeof window.msbt.onDataCatalogProgress === "function") {
    window.msbt.onDataCatalogProgress((progress) => {
      if (!progress) return;
      const message = progress.message
        || (progress.phase === "download"
          ? `Downloading ${progress.id || "catalog"}...`
          : progress.phase === "manifest"
            ? "Fetching catalog manifest..."
            : "");
      if (!message) return;
      if (els.dataCatalogSummary) setLine(els.dataCatalogSummary, message, "warning");
      if (els.bl4DataCatalogStatus) els.bl4DataCatalogStatus.textContent = `Data catalogs: ${message}`;
    });
  }
  if (window.msbt && typeof window.msbt.onDataCatalogRefreshed === "function") {
    window.msbt.onDataCatalogRefreshed((result) => {
      applyDataCatalogStatusUi(result || {}, { quiet: Boolean(result && result.quiet) });
      refreshDataCatalogStatusUi().catch(() => {});
      applyRemoteTutorialCopy().catch(() => {});
    });
  }
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
  if (els.gzoSubmitClearBtn) els.gzoSubmitClearBtn.addEventListener("click", clearGzoSubmitForm);
  if (els.gzoSubmitDecodeBtn) els.gzoSubmitDecodeBtn.addEventListener("click", normalizeGzoSubmitSerial);
  if (els.gzoSubmitUseEditorBtn) els.gzoSubmitUseEditorBtn.addEventListener("click", useMattEditorSerialForGzoSubmit);
  [
    els.gzoSubmitListing,
    els.gzoSubmitCreator,
    els.gzoSubmitName,
    els.gzoSubmitRarity,
    els.gzoSubmitType,
    els.gzoSubmitCategory,
    els.gzoSubmitBase85,
    els.gzoSubmitDeserialized,
    els.gzoSubmitNotes
  ].forEach((node) => {
    if (!node) return;
    node.addEventListener("input", updateGzoSubmitPayloadPreview);
    node.addEventListener("change", updateGzoSubmitPayloadPreview);
  });
  if (els.gzoSubmitCopyPayloadBtn) els.gzoSubmitCopyPayloadBtn.addEventListener("click", copyGzoSubmitPayloadPreview);
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
  const supportPanel = document.querySelector("details.support-panel");
  if (supportPanel) {
    const supportCollapseMq = window.matchMedia("(max-width: 1180px)");
    const syncSupportPanelOpen = () => {
      supportPanel.open = !supportCollapseMq.matches;
    };
    syncSupportPanelOpen();
    if (typeof supportCollapseMq.addEventListener === "function") {
      supportCollapseMq.addEventListener("change", syncSupportPanelOpen);
    } else if (typeof supportCollapseMq.addListener === "function") {
      supportCollapseMq.addListener(syncSupportPanelOpen);
    }
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
    ["funkyoushiftSiteBtn", "https://www.funkyoushift.com"],
    ["gzoDiscordBtn", "https://discord.gg/4hGKAHdvp6"],
    ["gzoToolsBtn", "https://save-editor.be/GZO/"],
    ["twitchBtn", "https://www.twitch.tv/funkyoushift/"],
    ["youtubeBtn", "https://www.youtube.com/@Funkyoushift"]
  ].forEach(([buttonId, url]) => {
    const button = document.getElementById(buttonId);
    if (button) button.addEventListener("click", () => window.msbt.openExternal(url));
  });

  const loadEditorBtn = document.getElementById("loadEditorBtn");
  if (loadEditorBtn) loadEditorBtn.addEventListener("click", () => loadEditor({ force: true }));
  const reloadEditorBtn = document.getElementById("reloadEditorBtn");
  if (reloadEditorBtn) {
    reloadEditorBtn.addEventListener("click", () => {
      if (els.editorFrame && els.editorFrame.src) {
        els.editorFrame.src = els.editorFrame.src;
        return;
      }
      void loadEditor({ force: true });
    });
  }

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
  if (els.devMyFavoriteSaveBtn) {
    els.devMyFavoriteSaveBtn.addEventListener("click", editSelectedDevMyFavorite);
  }
  if (els.devLogoUseSelectedBtn) {
    els.devLogoUseSelectedBtn.addEventListener("click", useSelectedDevActorForLogo);
  }
  if (els.devLogoAddLineBtn) {
    els.devLogoAddLineBtn.addEventListener("click", () => addDevLogoLine());
  }
  if (els.devLogoRemoveLineBtn) {
    els.devLogoRemoveLineBtn.addEventListener("click", removeDevLogoLine);
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
  if (els.travelFavoriteAddMapBtn) {
    els.travelFavoriteAddMapBtn.addEventListener("click", () => addTravelFavorite("map"));
  }
  if (els.travelFavoriteAddStationBtn) {
    els.travelFavoriteAddStationBtn.addEventListener("click", () => addTravelFavorite("station"));
  }
  if (els.travelFavoriteTravelBtn) {
    els.travelFavoriteTravelBtn.addEventListener("click", travelSelectedFavorite);
  }
  if (els.travelFavoriteRemoveBtn) {
    els.travelFavoriteRemoveBtn.addEventListener("click", removeSelectedTravelFavorite);
  }
  if (els.travelFavoriteSaveBtn) {
    els.travelFavoriteSaveBtn.addEventListener("click", saveSelectedTravelFavoriteMeta);
  }

  document.getElementById("refreshActivityBtn").addEventListener("click", bridgeStatus);
  document.getElementById("clearActivityBtn").addEventListener("click", () => {
    state.activity = [];
    setOutput(els.activityOutput, "Activity starts here.");
  });
  document.getElementById("clearBridgeLogBtn").addEventListener("click", () => runAction("clear_external_log", {}, els.activityOutput, 10000));

  if (els.mobileGatewayRefreshBtn) {
    els.mobileGatewayRefreshBtn.addEventListener("click", () => void refreshMobileGatewayInfo());
  }
  if (els.mobileGatewayRotateBtn) {
    els.mobileGatewayRotateBtn.addEventListener("click", () => void rotateMobileGatewayCode());
  }
  if (els.mobileGatewayCopyBtn) {
    els.mobileGatewayCopyBtn.addEventListener("click", () => void copyMobileGatewayDetails());
  }
  if (els.mobileGatewayHostSelect) {
    els.mobileGatewayHostSelect.addEventListener("change", () => void refreshMobileGatewayInfo());
  }
  if (els.mobileAnnounceDismissBtn) {
    els.mobileAnnounceDismissBtn.addEventListener("click", () => {
      if (els.mobileAnnounceDontShow && els.mobileAnnounceDontShow.checked) {
        setMobileAnnounceDismissed(true);
      }
      hideMobileAnnounceModal();
    });
  }
  if (els.mobileAnnounceOpenApkBtn) {
    els.mobileAnnounceOpenApkBtn.addEventListener("click", openMobileInstallPage);
  }
  if (els.mobileAnnounceOpenGatewayBtn) {
    els.mobileAnnounceOpenGatewayBtn.addEventListener("click", openMobileGatewayPanel);
  }
  if (els.mobileAnnounceOpenBtn) {
    els.mobileAnnounceOpenBtn.addEventListener("click", () => void showMobileAnnounceModal({ force: true }));
  }
  if (els.boostMobileAnnounceBtn) {
    els.boostMobileAnnounceBtn.addEventListener("click", () => void showMobileAnnounceModal({ force: true }));
  }
  if (els.boostMobileGatewayBtn) {
    els.boostMobileGatewayBtn.addEventListener("click", openMobileGatewayPanel);
  }

  const walkthroughNextBtn = document.getElementById("walkthroughNextBtn");
  const walkthroughBackBtn = document.getElementById("walkthroughBackBtn");
  const walkthroughSkipBtn = document.getElementById("walkthroughSkipBtn");
  const walkthroughReplayBtn = document.getElementById("walkthroughReplayBtn");
  if (walkthroughNextBtn) walkthroughNextBtn.addEventListener("click", () => walkthroughNext());
  if (walkthroughBackBtn) walkthroughBackBtn.addEventListener("click", () => walkthroughBack());
  if (walkthroughSkipBtn) walkthroughSkipBtn.addEventListener("click", () => void endWalkthrough({ skipped: true }));
  if (walkthroughReplayBtn) walkthroughReplayBtn.addEventListener("click", () => void startMainTutorial({ force: true }));
}

/** localStorage keys for post-update / first-run main tour gating */
const TUTORIAL_LS_LAST_SEEN = "msbt.lastSeenVersion";
const TUTORIAL_LS_MAIN_SEEN = "msbt.tutorial.mainSeen";

/** Per-tab chooser entries (end of main tour + View menu helpers) */
const MAIN_TAB_CHOICES = [
  { id: "boosting", label: "Boosting" },
  { id: "serial-tools", label: "Serial Tools" },
  { id: "inventory", label: "Inventory" },
  { id: "bl4-codes", label: "BL4 Codes" },
  { id: "matt-editor", label: "Matt Editor" },
  { id: "item-pool", label: "Item Pool" },
  { id: "dev-spawner", label: "Dev Spawner" },
  { id: "map-travel", label: "Map Travel" },
  { id: "player-movement", label: "Player Movement" },
  { id: "activity", label: "Activity Log" },
  { id: "report", label: "Report" },
  { id: "updates", label: "Updates" }
];

/**
 * Structured tutorial content map.
 * Tour ids: main | layout | quick-menu-setup | tab:<tabId> (via TAB_TUTORIALS)
 */
const TUTORIAL_TOURS = {
  /** First-run / post-update: brief overview of what the app does */
  main: [
    {
      title: "Welcome to MSBT",
      body: "You need Borderlands 4 + the MSBT SDK mod (.sdkmod in the game’s sdk_mods folder) + this Electron app. Live actions also need a connected bridge — use header Refresh Status.\n\nOffline: serial convert/validate. Live (game + mod + bridge): boosting, spawns, travel, delivery.\n\nPut MattsSDKBoostingTools.sdkmod next to ActorScriptDeployer under Borderlands 4/sdk_mods/. Or use Updates → Install / Update SDK Mod.",
      tab: "boosting",
      target: "statusBtn",
      sdk: true,
      links: [
        {
          label: "Download latest release (app + .sdkmod)",
          url: "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest"
        },
        {
          label: "Open Updates tab (install SDK mod)",
          action: "updates-tab"
        }
      ]
    },
    {
      title: "Bridge & status",
      body: "Live actions need the SDK bridge. Click Refresh Status in the header — this line shows whether the bridge is up and which players are available. Offline tools (serial convert, catalogs) still work without it.",
      tab: "boosting",
      target: "bridgeSummary"
    },
    {
      title: "Boosting",
      body: "This is the main live lobby tab. Pick a target player (or All / Non-Host), then use Quick Max, UVH, rarity weights, XP, currency, backpack/bank size, helpers, cheats, and serial rewards. Most buttons need the bridge.",
      tab: "boosting",
      targetSel: "#tab-boosting [data-msbt-panel='boost-target']",
      revealPanels: ["boost-target", "boost-quick-max"]
    },
    {
      title: "Serial Tools",
      body: "Paste a @U or decoded serial → Convert to decode parts and rebuild @U (works offline). Validate serials, save keepers as Bookmarks (named groups), then Deliver Selected / All / Non-Host when the bridge is connected.",
      tab: "serial-tools",
      targetSel: "#tab-serial-tools [data-msbt-panel='serial-tools-main']"
    },
    {
      title: "Map Travel",
      body: "Jump to a map or travel station while the game is running. Select a map, then a station when you can — station travel is usually safer. Save places you reuse under Travel Favorites.",
      tab: "map-travel",
      targetSel: "#tab-map-travel [data-msbt-panel='travel-main']"
    },
    {
      title: "Player Movement",
      body: "Tune speed, jump, gravity, Infinite Jump, glide/dash, and world helpers. Sliders only change the form until you press Apply Now (bridge required). Save presets if you switch styles often.",
      tab: "player-movement",
      targetSel: "#tab-player-movement [data-msbt-panel='move-presets']"
    },
    {
      title: "Quick Menu",
      body: "In Borderlands 4, open the in-game Quick Menu (F7) for an action dock (no BLImGui). This ★ Quick Menu tab is the desktop editor for that dock: Refresh From Game, click a slot, pick a command, Save Slot. Pin common actions with + QM so you stay in-game.",
      tab: "quick-menu",
      targetSel: "#tab-quick-menu .section-heading"
    },
    {
      title: "Updates",
      body: "Check Electron app and SDK mod versions here. Download Electron updates, or Install / Update SDK Mod into your Borderlands 4 sdk_mods folder. Fully restart the game after any SDK change.",
      tab: "updates",
      targetSel: "#tab-updates [data-msbt-panel='updates-main']",
      sdk: true
    },
    {
      title: "Activity Log",
      body: "Recent app and bridge messages appear here. If a button seems to do nothing, check this log first. Clear Local Log when it gets noisy; copy useful lines before opening Report.",
      tab: "activity",
      targetSel: "#tab-activity [data-msbt-panel='activity-log']"
    },
    {
      title: "Arrange your layout",
      body: "Every tab has a layout toolbar: drag panels by the title bar, stack by dropping center-on-center, Compact to tidy, Reset for defaults. Full editor tour is on the next screen — or View → Layout walkthrough anytime.",
      tab: "boosting",
      targetSel: "#tab-boosting .msbt-layout-toolbar"
    },
    {
      title: "What would you like to do now?",
      body: "Pick a full deep-dive or a short per-tab walkthrough. After each one you’ll return here so you can take another. Tap I’m done when you’re finished. Replay anytime from View, Quick Menu → App Walkthrough, or each tab’s Walkthrough button.\n\nQuick Menu setup covers the ★ Quick Menu tab and in-game dock — there is no separate QM-tab-only tour.",
      tab: "boosting",
      type: "choices"
    }
  ],

  /** Full layout editor tour (always reachable) */
  layout: [
    {
      title: "Layout toolbar",
      body: "Every main tab has a layout bar: Panels (show/hide), Compact, Reset layout, and Walkthrough. Arrangements save per tab in this profile.",
      tab: "boosting",
      targetSel: "#tab-boosting .msbt-layout-toolbar"
    },
    {
      title: "Drag, overlap, click to front",
      body: "Drag a panel by its title bar. Panels may overlap while you arrange. Click a panel to bring it to the front. Resize from edges or the corner handle.",
      tab: "boosting",
      targetSel: "#tab-boosting [data-msbt-panel='boost-target']"
    },
    {
      title: "Stack panels (center drop)",
      body: "Drop a panel onto the center of another (dashed highlight) to stack them as tabs inside one frame. Switch with the stack tab buttons.",
      tab: "boosting",
      targetSel: "#tab-boosting .msbt-layout-hint"
    },
    {
      title: "Detach a stacked panel",
      body: "Drag a stack tab's name outward to detach that panel, or use ⧉ on the active stack tab.",
      tab: "boosting",
      targetSel: "#tab-boosting .msbt-layout-toolbar"
    },
    {
      title: "Compact and Reset",
      body: "Compact packs panels, fills gaps, and clears overlaps. Reset layout restores that tab's default arrangement.",
      tab: "boosting",
      targetSel: "#tab-boosting .msbt-layout-toolbar-actions"
    },
    {
      title: "Restore hidden panels",
      body: "Collapse/hide from panel chrome, then restore from the toolbar Panels menu or View → Panels (checkbox list for the active tab).",
      tab: "boosting",
      targetSel: "#tab-boosting .msbt-panels-menu"
    },
    {
      title: "View — text size & tabs",
      body: "Header View menu: content text size (A− / A+ / slider, 85%–140%), show/hide or reorder main nav tabs, and walkthrough shortcuts (Layout / Quick Menu setup / App overview).",
      tab: "boosting",
      targetSel: "[data-msbt-view-menu]"
    }
  ],

  /** Full Quick Menu setup tour (always reachable; also launched from ★ Quick Menu Walkthrough) */
  "quick-menu-setup": [
    {
      title: "In-game Quick Menu (F7)",
      body: "With the MSBT SDK mod loaded, open the in-game Quick Menu (F7) in Borderlands 4 — a right-docked action panel. No BLImGui required. F7 also closes it; Close F7 works from the header.",
      tab: "quick-menu",
      targetSel: "#tab-quick-menu .section-heading"
    },
    {
      title: "Esc, F6, dock chrome",
      body: "Esc closes Quick Menu modals (release-gated so pause is not stolen). F6 unstuck restores GameOnly mouse/look if UI capture sticks. On the dock: MOVE places it, THEME cycles looks, −/+ resizes.",
      tab: "quick-menu",
      target: "quickMenuStatus"
    },
    {
      title: "Pages, slots, INV",
      body: "Up to 5 pages × 21 slots (3×7). Page tabs switch sets of actions. The INV tab browses live inventory in-game (same idea as the Electron Inventory tab).",
      tab: "quick-menu",
      targetSel: "#tab-quick-menu [data-msbt-panel='qm-slots']"
    },
    {
      title: "Electron editor",
      body: "This tab edits the live layout: Refresh From Game loads current pages; click a slot, pick a command, optional custom label, then Save Slot. Clear Current Page wipes the active page.",
      tab: "quick-menu",
      target: "quickMenuRefreshBtn"
    },
    {
      title: "Pin with + QM",
      body: "On Boosting, Movement, Serial Tools, BL4, Item Pool, Travel, and more, gold + QM buttons capture the action with current values into a slot. Pin Last Command (on the Quick Menu tab) works after you run something once.",
      tab: "boosting",
      targetSel: "#tab-boosting .qm-add-button",
      targetSelFallback: "#tab-boosting [data-msbt-panel='boost-helpers']"
    },
    {
      title: "Modules & rarity",
      body: "Optional F7 Panel Modules (e.g. rarity weight sliders) keep Apply / Reset / Leg Only / Pearl Only on the dock. Unequip to keep the action grid compact. Sliders stay in sync with Boosting.",
      tab: "quick-menu",
      targetSel: "#tab-quick-menu [data-msbt-panel='qm-modules']"
    },
    {
      title: "Travel closes Quick Menu",
      body: "Map or station travel closes the in-game Quick Menu first so input is not stuck during the world change. Prefer station travel when you can. Electron Map Travel and pinned travel actions share that path.",
      tab: "map-travel",
      targetSel: "#tab-map-travel [data-msbt-panel='travel-main']"
    },
    {
      title: "Desktop complements the dock",
      body: "Use Electron for heavy browsing (catalogs, inventory filters, spawner search). Pin the few actions you need mid-fight onto the in-game Quick Menu (F7) so you stay in-game. Replay this tour anytime from View → Quick Menu walkthrough or the ★ Quick Menu Walkthrough button.",
      tab: "quick-menu",
      targetSel: "#tab-quick-menu .section-heading"
    }
  ]
};

/** Post-update / first-run tour steps */
const MAIN_TUTORIAL_STEPS = TUTORIAL_TOURS.main;

async function applyRemoteTutorialCopy() {
  try {
    if (!window.msbt || typeof window.msbt.getTutorialCopy !== "function") return;
    const result = await window.msbt.getTutorialCopy();
    if (!result || !result.ok || !result.data) return;
    const tours = result.data.tours || {};
    let applied = 0;
    for (const [tourId, patches] of Object.entries(tours)) {
      const steps = TUTORIAL_TOURS[tourId];
      if (!Array.isArray(steps) || !Array.isArray(patches)) continue;
      for (const patch of patches) {
        if (!patch || typeof patch !== "object") continue;
        const idx = Number(patch.index);
        if (!Number.isInteger(idx) || idx < 0 || !steps[idx]) continue;
        // Allowlist: title/body text only — never target selectors, links, or actions from remote JSON.
        if (typeof patch.title === "string" && patch.title.trim()) {
          steps[idx].title = patch.title;
          applied += 1;
        }
        if (typeof patch.body === "string" && patch.body.trim()) {
          steps[idx].body = patch.body;
          applied += 1;
        }
      }
    }
    if (applied > 0 && typeof appendActivity === "function") {
      appendActivity(`Applied ${applied} tutorial copy overlay(s) from ${result.source || "cache"}.`);
    }
  } catch (error) {
    // Soft-fail: keep bundled walkthrough copy.
    console.warn("tutorial copy overlay skipped", error);
  }
}

/** Per-tab tips (Walkthrough button on each layout toolbar) */
const TAB_TUTORIALS = {
  boosting: [
    {
      title: "Target & bridge",
      body: "Refresh Status (header) until the bridge is green. Choose a party player, or Target All / Non-Host for Quick Max, XP, Currency, and backpack/bank Set Selected. Kick uses the selected player.",
      tab: "boosting",
      targetSel: "#tab-boosting [data-msbt-panel='boost-target']",
      revealPanels: ["boost-target"]
    },
    {
      title: "Quick Max & UVH",
      body: "Quick Max one-shots cash, eridium, level 60, spec 701, SDUs, or Max All. UVH Booster runs lobby challenge tiers 1–N (or Run All 1–7); Cancel stops a queued run.",
      tab: "boosting",
      targetSel: "#tab-boosting [data-msbt-panel='boost-quick-max']",
      revealPanels: ["boost-quick-max", "boost-uvh"]
    },
    {
      title: "Rarity drop weights",
      body: "Sliders are % of vanilla weight (0 removes that rarity). Apply pushes to the game; presets only change the UI until Apply. Optional Remember on startup loads sliders without applying.",
      tab: "boosting",
      targetSel: "#tab-boosting [data-msbt-panel='boost-rarity']",
      revealPanels: ["boost-rarity"]
    },
    {
      title: "Experience",
      body: "Pick XP track + target level, then Set Level or Max Player Level / Spec 701. Needs bridge + target.",
      tab: "boosting",
      targetSel: "#tab-boosting [data-msbt-panel='boost-xp']",
      revealPanels: ["boost-xp"]
    },
    {
      title: "Currency & backpack / bank",
      body: "Currency: kind + amount, Give / Max. Backpack / Bank Size: set numbers, Set Selected or Apply to All Party; auto checkbox keeps re-applying as players load.",
      tab: "boosting",
      targetSel: "#tab-boosting [data-msbt-panel='boost-currency']",
      revealPanels: ["boost-currency", "boost-inventory"]
    },
    {
      title: "Serial Rewards",
      body: "Paste @U serials, optional level override + copies, then Give Selected / All / Non-Host. Delivery needs the bridge; progress shows in the top Serial Delivery bar.",
      tab: "boosting",
      targetSel: "#tab-boosting [data-msbt-panel='boost-serial']",
      revealPanels: ["boost-serial"]
    },
    {
      title: "Helpers, cheats, + QM",
      body: "Quick Helpers: Pull Loot / Super Dash. Cheats panel covers ammo, demigod, chests, shinies, debug cam, etc. Gold + QM beside supported buttons pins that action into the in-game Quick Menu (F7) with current values.",
      tab: "boosting",
      targetSel: "#tab-boosting [data-msbt-panel='boost-helpers']",
      revealPanels: ["boost-helpers", "boost-cheats"]
    },
    {
      title: "Layout tip",
      body: "Panels are rearrangeable — stack Target with Quick Max, Compact when messy. See View → Layout walkthrough for the full editor tour.",
      tab: "boosting",
      targetSel: "#tab-boosting .msbt-layout-toolbar"
    }
  ],
  "serial-tools": [
    {
      title: "Convert & decode",
      body: "Paste a @U or decoded serial → Convert. Copy Deserialized, Parts Breakdown, or rebuilt @U. No bridge required for convert/decode.",
      tab: "serial-tools",
      targetSel: "#tab-serial-tools [data-msbt-panel='serial-tools-main']"
    },
    {
      title: "Bookmarks",
      body: "Save named serials in groups. Search/filter, check rows or whole folders, Copy Selected, then Deliver Selected / All / Non-Host (bridge + target required).",
      tab: "serial-tools",
      targetSel: "#tab-serial-tools [data-msbt-panel='serial-bookmarks']"
    },
    {
      title: "Validate",
      body: "Details → Validate / Confirm Active checks the open bookmark. The Validator panel does basic or bulk line-by-line checks locally.",
      tab: "serial-tools",
      targetSel: "#tab-serial-tools [data-msbt-panel='serial-validator']"
    },
    {
      title: "Delivery & + QM",
      body: "Set Serial Bookmarks Target and Copies before Deliver. + QM Selected/All/Non-Host pins checked serials into the in-game Quick Menu (F7). Watch the top Serial Delivery progress bar during live gives.",
      tab: "serial-tools",
      target: "bookmarkQmSelectedBtn"
    },
    {
      title: "Layout tip",
      body: "Stack Convert + Bookmarks for a tighter workspace — View → Layout walkthrough covers drag/stack/Compact.",
      tab: "serial-tools",
      targetSel: "#tab-serial-tools .msbt-layout-toolbar"
    }
  ],
  inventory: [
    {
      title: "Load a player's bags",
      body: "Pick Party player (P1–P4 / Boosting target), then Refresh Inventory while in-game. Listen host works best for reading other players. Bridge required.",
      tab: "inventory",
      target: "invRefreshBtn"
    },
    {
      title: "Browse & filter",
      body: "Equipped strip on top; backpack grid below. Sort (Recent/Rarity/Type/Level/Manufacturer), category chips, and Filter (search, rarity, damage, type, manufacturer).",
      tab: "inventory",
      targetSel: "#tab-inventory .inv-toolbar"
    },
    {
      title: "Item detail & give",
      body: "Click an equipped or backpack item to open this detail strip (serial + meta). Give to is separate from the viewing player — set recipient + Multiplier, then Send to Game.",
      tab: "inventory",
      targetSel: "#invDetail .inv-give-row",
      revealInvDetail: true
    },
    {
      title: "Send elsewhere",
      body: "From the open item detail: Copy Serial, Send to Serial Rewards (Boosting paste), Open in Serial Tools, or Open Matt Editor.",
      tab: "inventory",
      targetSel: "#invDetail .button-row.wrap",
      revealInvDetail: true
    },
    {
      title: "Capacity note",
      body: "Backpack/bank size lives on Boosting → Backpack / Bank Size (not this tab). The in-game Quick Menu (F7) also has an INV tab with the same live inventory idea.",
      tab: "inventory",
      targetSel: "#tab-inventory [data-msbt-panel='inv-main']"
    }
  ],
  "bl4-codes": [
    {
      title: "Browse offline",
      body: "Load Catalog / Refresh GZO, then filter by search, manufacturer, listing, rarity, type, creator, Mattmab result. Image cards load from GZO when available.",
      tab: "bl4-codes",
      targetSel: "#tab-bl4-codes [data-msbt-panel='bl4-main']"
    },
    {
      title: "Select & inspect",
      body: "Check cards or click one for Details (serial + parts). Copy, Bookmark This, Import Selected To Bookmarks, or Validate / Confirm Active.",
      tab: "bl4-codes",
      target: "bl4ValidateBtn"
    },
    {
      title: "Delivery panel",
      body: "Right-side Delivery stays visible while you scroll. Set Target, optional level override + copies, then Deliver Selected / All / Non-Host (bridge required).",
      tab: "bl4-codes",
      targetSel: "#tab-bl4-codes [data-msbt-panel='bl4-delivery']"
    },
    {
      title: "+ QM & submit",
      body: "+ QM pins checked/active codes into the in-game Quick Menu (F7). Submit Your Code to GZO opens the submit flow (serial normalize + required screenshot).",
      tab: "bl4-codes",
      target: "bl4SubmitGzoBtn"
    }
  ],
  "matt-editor": [
    {
      title: "Matt Editor",
      body: "A full save editor and item creator. Press Load Editor to open it — build or edit items and saves here.",
      tab: "matt-editor",
      target: "loadEditorBtn"
    },
    {
      title: "Support Mattmab",
      body: "If Matt Editor helps you, consider supporting Mattmab on Ko-fi. The button below opens his page in your browser.",
      tab: "matt-editor",
      target: "loadEditorBtn",
      links: [
        {
          label: "Support Mattmab on Ko-fi",
          url: "https://ko-fi.com/mattmab"
        }
      ]
    }
  ],
  "item-pool": [
    {
      title: "Find pools",
      body: "Search and Category filter the list. Multi-select rows (Ctrl/Shift click). Set Level (1–60) and Quantity.",
      tab: "item-pool",
      target: "itempoolSearch"
    },
    {
      title: "Spawn near you",
      body: "Spawn Selected Item Pool(s) drops loot near the local player through the bridge. Watch the result pre below the buttons.",
      tab: "item-pool",
      target: "spawnItempoolBtn"
    },
    {
      title: "+ QM pin",
      body: "When the Quick Menu catalog is loaded, the gold + QM beside Spawn Selected pins that pool spawn (with level/count) into an in-game Quick Menu slot.",
      tab: "item-pool",
      targetSel: "#tab-item-pool .qm-add-button",
      targetSelFallback: "#spawnItempoolBtn"
    },
    {
      title: "Layout tip",
      body: "Single-panel tab — Compact/Reset still help if you resize oddly. See Layout walkthrough for shared editor habits.",
      tab: "item-pool",
      targetSel: "#tab-item-pool .msbt-layout-toolbar"
    }
  ],
  "dev-spawner": [
    {
      title: "Pick an actor",
      body: "Actor Browser: search, Categories, Active Boss Chars, My Favorites, then Actor Results. Selecting a row fills Selected Actor and the spawn name field.",
      tab: "dev-spawner",
      targetSel: "#tab-dev-spawner [data-msbt-panel='dev-browser']"
    },
    {
      title: "Spawn settings",
      body: "Standard Spawning: Distance, +Z, Count, Spacing, Scale, Target/List Limit. Spawn Selected Actor sends via Actor Script Deployer (ASD).",
      tab: "dev-spawner",
      targetSel: "#tab-dev-spawner [data-msbt-panel='dev-spawn']"
    },
    {
      title: "Setup / Inspect & clear",
      body: "ASD Status, Cache, Diagnostics, Probe, Template Spawn, Lost Loot, etc. After heavy spawning use Clear ASD Spawns. The SDK also auto-clears each spawn batch after ~60s.",
      tab: "dev-spawner",
      targetSel: "#tab-dev-spawner [data-msbt-panel='dev-setup']"
    },
    {
      title: "Favorites & barrel logo",
      body: "Add Selected to My Favorites with optional label/note. Barrel Logo spells text with actors — Run Barrel Logo / Use Selected from the logo panel.",
      tab: "dev-spawner",
      targetSel: "#tab-dev-spawner [data-msbt-panel='dev-barrel']"
    },
    {
      title: "Layout tip",
      body: "Stack Standard Spawning with Setup / Inspect for a tighter workspace. View → Layout walkthrough for drag/stack details.",
      tab: "dev-spawner",
      targetSel: "#tab-dev-spawner .msbt-layout-toolbar"
    }
  ],
  "map-travel": [
    {
      title: "Maps then stations",
      body: "Select a map (search works), then pick a travel station filtered to that map — or enable Show all travel stations. Prefer station travel when you can.",
      tab: "map-travel",
      targetSel: "#tab-map-travel [data-msbt-panel='travel-main']"
    },
    {
      title: "Travel buttons",
      body: "Travel to Selected Map / Station needs the bridge. Travel Favorites hold maps or stations in one list — Travel Favorite uses the saved type.",
      tab: "map-travel",
      target: "travelStationBtn"
    },
    {
      title: "Favorites workflow",
      body: "Add Map/Station to Favorites, rename Label/Note, Save Label/Note, Remove Favorite. + QM can pin map/station travel when the catalog is loaded.",
      tab: "map-travel",
      targetSel: "#tab-map-travel [data-msbt-panel='travel-favorites']"
    },
    {
      title: "Quick Menu note",
      body: "Travel closes the in-game Quick Menu (F7) first so mouse/look are not stuck across the load. Safe to travel from Electron or a pinned Quick Menu travel action.",
      tab: "map-travel",
      target: "travelOutput"
    }
  ],
  "player-movement": [
    {
      title: "Apply is what counts",
      body: "Sliders/fields are UI-only until Apply Now (or any Apply Movement Settings). Save/Load Preset and Fast/Moon/etc. only change the form until you apply through the bridge.",
      tab: "player-movement",
      targetSel: "#tab-player-movement [data-msbt-panel='move-presets']"
    },
    {
      title: "Speed, jump, gravity",
      body: "Speed Scale / Walk speed; JumpGoal height (optional per sprint/double/slide); Gravity Scale. Extreme values can feel bad — Reset Defaults restores the form.",
      tab: "player-movement",
      targetSel: "#tab-player-movement [data-msbt-panel='move-speed']"
    },
    {
      title: "Infinite Jump",
      body: "All ON/OFF for the party, or Selected ON/OFF/Toggle for one player. Needs bridge + player list. Useful with travel; leave OFF if you want vanilla jump.",
      tab: "player-movement",
      targetSel: "#tab-player-movement [data-msbt-panel='move-infjump']"
    },
    {
      title: "Wall, glide, world",
      body: "Wall/Step, Glide/Dash/Vault (optional zero vault costs), Time Dilation, Noclip, No Target, Pull Loot, Super Dash, Delete Ground Items. + QM pins supported helpers to the in-game Quick Menu (F7).",
      tab: "player-movement",
      targetSel: "#tab-player-movement [data-msbt-panel='move-world']"
    },
    {
      title: "Teleport party",
      body: "Teleport Selected Player → To P1–P4 moves the movement-target player to that party slot pawn.",
      tab: "player-movement",
      targetSel: "#tab-player-movement [data-msbt-panel='move-teleport']"
    },
    {
      title: "Layout tip",
      body: "Stack presets with Infinite Jump if you tweak often. Full layout tour: View → Layout walkthrough.",
      tab: "player-movement",
      targetSel: "#tab-player-movement .msbt-layout-toolbar"
    }
  ],
  activity: [
    {
      title: "Activity Log",
      body: "Chronological app messages (actions, tour starts, errors). Clear Local Log when noisy. Useful to copy context before Report.",
      tab: "activity",
      targetSel: "#tab-activity [data-msbt-panel='activity-log']"
    },
    {
      title: "Bridge raw status",
      body: "Refresh Status hits the SDK bridge and dumps raw status here. Clear Bridge Markers clears bridge-side log markers when supported.",
      tab: "activity",
      targetSel: "#tab-activity [data-msbt-panel='activity-bridge']"
    },
    {
      title: "When to use it",
      body: "If a button “does nothing,” check Activity + Bridge Raw first — offline bridge vs action failure looks different here than in the game.",
      tab: "activity",
      target: "refreshActivityBtn"
    }
  ],
  report: [
    {
      title: "Fill the form",
      body: "Bug or Feature, Title, Description, Steps, Expected/Actual, optional Notes. Keep titles short; steps numbered.",
      tab: "report",
      targetSel: "#tab-report [data-msbt-panel='report-form']"
    },
    {
      title: "Diagnostics & preview",
      body: "Include redacted app/bridge diagnostics (on by default). Refresh Preview, then Copy or Save Report locally.",
      tab: "report",
      targetSel: "#tab-report [data-msbt-panel='report-preview']"
    },
    {
      title: "Submit on GitHub",
      body: "Submit Issue to Developer on GitHub opens a prefilled draft for the MSBT repo — attach screenshots/logs there before posting.",
      tab: "report",
      target: "reportGithubBtn",
      targetSel: "#reportGithubBtn"
    }
  ],
  updates: [
    {
      title: "Version cards",
      body: "Shows Electron app current/latest, bundled SDK mod version, and detected installed .sdkmod path. Check Updates from the header anytime.",
      tab: "updates",
      targetSel: "#tab-updates [data-msbt-panel='updates-main']",
      sdk: true
    },
    {
      title: "Electron update",
      body: "Download Electron Update, then Restart / Install, or open the installer / manual ZIP from GitHub Releases.",
      tab: "updates",
      target: "updateDownloadBtn"
    },
    {
      title: "SDK mod install",
      body: "Detect or browse your Borderlands 4 sdk_mods folder, then Install / Update SDK Mod (MSBT + ActorScriptDeployer for Dev Spawner). Fully restart the game afterward.",
      tab: "updates",
      targetSel: "#tab-updates [data-msbt-panel='updates-sdk']"
    },
    {
      title: "Saved data / backups",
      body: "Bookmarks, favorites, presets, and window size live outside the install folder. Export Settings Backup before major upgrades if you want an extra copy.",
      tab: "updates",
      targetSel: "#tab-updates [data-msbt-panel='updates-saved']"
    }
  ]
};

const walkthroughState = {
  active: false,
  step: 0,
  mode: "main", // "main" | "layout" | "quick-menu-setup" | "tab"
  steps: MAIN_TUTORIAL_STEPS,
  tabId: null,
  dontShowAgain: false,
  /** When true, finishing/skipping a nested tour reopens the main chooser. */
  chooserSession: false,
  _spotlightTimer: null,
  _spotlightToken: 0,
  _repositionBound: false,
  _revealedInvDetail: false,
  _didRevealPanels: false
};

function walkthroughNodes() {
  return {
    modal: document.getElementById("walkthroughModal"),
    title: document.getElementById("walkthroughTitle"),
    body: document.getElementById("walkthroughBody"),
    links: document.getElementById("walkthroughLinks"),
    sdkNote: document.getElementById("walkthroughSdkNote"),
    dontShow: document.getElementById("walkthroughDontShow"),
    dontShowRow: document.getElementById("walkthroughDontShowRow"),
    choices: document.getElementById("walkthroughChoices"),
    progress: document.getElementById("walkthroughProgress"),
    spotlight: document.getElementById("walkthroughSpotlight"),
    back: document.getElementById("walkthroughBackBtn"),
    next: document.getElementById("walkthroughNextBtn"),
    skip: document.getElementById("walkthroughSkipBtn")
  };
}

function mainTourChoicesStepIndex() {
  const steps = TUTORIAL_TOURS.main;
  const idx = steps.findIndex((row) => row && row.type === "choices");
  return idx >= 0 ? idx : Math.max(0, steps.length - 1);
}

/** Reopen the post-overview chooser without ending the keep-offering session. */
function reopenMainChooser() {
  walkthroughState.mode = "main";
  walkthroughState.tabId = null;
  walkthroughState.steps = TUTORIAL_TOURS.main;
  walkthroughState.step = mainTourChoicesStepIndex();
  walkthroughState.chooserSession = true;
  walkthroughState.active = true;
  suppressTourCollidingChrome();
  const nodes = walkthroughNodes();
  if (nodes.modal) nodes.modal.classList.remove("hidden");
  renderWalkthroughStep();
}

function walkthroughModeLabel() {
  if (walkthroughState.mode === "layout") return "Layout editor";
  if (walkthroughState.mode === "quick-menu-setup") return "Quick Menu setup";
  if (walkthroughState.mode === "tab") {
    const id = walkthroughState.tabId;
    const entry = MAIN_TAB_CHOICES.find((row) => row.id === id);
    return entry ? `${entry.label} tips` : "Tab tips";
  }
  return "App tour";
}

function currentAppVersionString() {
  const info = state.versionInfo || {};
  return String(info.appVersion || info.packageVersion || "0.0.0").trim() || "0.0.0";
}

function readTutorialLocal(key) {
  try {
    return String(localStorage.getItem(key) || "").trim();
  } catch {
    return "";
  }
}

function writeTutorialLocal(key, value) {
  try {
    localStorage.setItem(key, String(value || ""));
  } catch {
    /* ignore quota / private mode */
  }
}

function markMainTutorialSeen(version) {
  const ver = String(version || currentAppVersionString());
  writeTutorialLocal(TUTORIAL_LS_LAST_SEEN, ver);
  writeTutorialLocal(TUTORIAL_LS_MAIN_SEEN, ver);
}

function shouldAutoShowMainTutorial() {
  const current = currentAppVersionString();
  const lastSeen = readTutorialLocal(TUTORIAL_LS_LAST_SEEN);
  const mainSeen = readTutorialLocal(TUTORIAL_LS_MAIN_SEEN);
  // First install / first run in this profile
  if (!lastSeen) return true;
  // Updated since last marked version
  if (lastSeen !== current) return true;
  // Same version already completed/skipped
  if (mainSeen === current) return false;
  return false;
}

function clearWalkthroughSpotlight() {
  const { spotlight } = walkthroughNodes();
  if (!spotlight) return;
  spotlight.hidden = true;
  spotlight.style.top = "0px";
  spotlight.style.left = "0px";
  spotlight.style.width = "0px";
  spotlight.style.height = "0px";
}

function suppressTourCollidingChrome() {
  walkthroughState.hidStartupUpdateModal = Boolean(
    els.startupUpdateModal && !els.startupUpdateModal.classList.contains("hidden")
  );
  if (els.boostUpdateNotice) els.boostUpdateNotice.classList.add("hidden");
  hideStartupUpdateModal();
  hideMobileAnnounceModal();
}

function restoreTourCollidingChrome() {
  const info = state.versionInfo
    ? { ...state.versionInfo, updateState: state.latestUpdateState }
    : null;
  if (info) renderBoostUpdateNotice(info);
  let showedUpdateModal = false;
  const deferred = state.deferredStartupUpdateInfo;
  if (deferred) {
    state.deferredStartupUpdateInfo = null;
    maybeShowStartupUpdateModal(deferred);
    walkthroughState.hidStartupUpdateModal = false;
    showedUpdateModal = Boolean(
      els.startupUpdateModal && !els.startupUpdateModal.classList.contains("hidden")
    );
  } else if (walkthroughState.hidStartupUpdateModal) {
    walkthroughState.hidStartupUpdateModal = false;
    const notice = info ? updateNoticeInfo(info) : null;
    if (notice) {
      renderStartupUpdateModal(notice);
      showedUpdateModal = true;
    }
  }
  // Prefer update modal first; show mobile announce shortly after (or immediately if no update UI).
  const delayMs = showedUpdateModal ? 500 : 250;
  state.deferredMobileAnnounce = false;
  window.setTimeout(() => void showMobileAnnounceModal({ force: false }), delayMs);
}

function clearWalkthroughLinks() {
  const { links } = walkthroughNodes();
  if (!links) return;
  links.innerHTML = "";
  links.classList.add("hidden");
}

function renderWalkthroughLinks(step) {
  const { links } = walkthroughNodes();
  if (!links) return;
  const rows = Array.isArray(step && step.links) ? step.links : [];
  links.innerHTML = "";
  if (!rows.length) {
    links.classList.add("hidden");
    return;
  }
  links.classList.remove("hidden");
  rows.forEach((row) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = row.action === "updates-tab" ? "secondary" : "";
    btn.textContent = row.label || "Open link";
    btn.addEventListener("click", () => {
      if (row.action === "updates-tab") {
        switchTab("updates");
        return;
      }
      const url = String(row.url || state.latestInstallerUrl || state.latestDownloadUrl || "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest").trim();
      if (window.msbt && typeof window.msbt.openExternal === "function") {
        window.msbt.openExternal(url);
      }
    });
    links.appendChild(btn);
  });
}

function resolveWalkthroughTarget(step) {
  if (!step) return null;
  if (step.target) {
    const byId = document.getElementById(step.target);
    if (byId) return byId;
  }
  if (step.targetSel) {
    const node = document.querySelector(step.targetSel);
    if (node) return node;
  }
  if (step.targetSelFallback) {
    const fallback = document.querySelector(step.targetSelFallback);
    if (fallback) return fallback;
  }
  return null;
}

function walkthroughCardNode() {
  return document.querySelector("#walkthroughModal .walkthrough-modal");
}

function clampWalkthroughNumber(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function resetWalkthroughCardPosition() {
  const card = walkthroughCardNode();
  if (!card) return;
  card.classList.remove("walkthrough-modal-anchored", "walkthrough-modal-centered");
  card.style.top = "";
  card.style.left = "";
  card.style.right = "";
  card.style.bottom = "";
  card.style.transform = "";
}

function centerWalkthroughCard() {
  const card = walkthroughCardNode();
  if (!card) return;
  card.classList.remove("walkthrough-modal-anchored");
  card.classList.add("walkthrough-modal-centered");
  // Clear inline coords so CSS top/left/transform centering wins cleanly.
  card.style.top = "";
  card.style.left = "";
  card.style.right = "";
  card.style.bottom = "";
  card.style.transform = "";
}

function rectsOverlap(a, b, pad = 10) {
  return !(
    a.right + pad < b.left
    || a.left - pad > b.right
    || a.bottom + pad < b.top
    || a.top - pad > b.bottom
  );
}

/** Overlap area of card box vs highlight; pad expands the highlight only. */
function rectOverlapArea(cardBox, highlight, pad = 0) {
  const left = Math.max(cardBox.left, highlight.left - pad);
  const right = Math.min(cardBox.right, highlight.right + pad);
  const top = Math.max(cardBox.top, highlight.top - pad);
  const bottom = Math.min(cardBox.bottom, highlight.bottom + pad);
  const w = right - left;
  const h = bottom - top;
  if (w <= 0 || h <= 0) return 0;
  return w * h;
}

function walkthroughViewportSize() {
  return {
    vw: window.innerWidth || document.documentElement.clientWidth || 1200,
    vh: window.innerHeight || document.documentElement.clientHeight || 800
  };
}

/** Apply anchored position with no leftover centered translate. */
function applyWalkthroughCardAnchor(card, left, top) {
  if (!card) return;
  card.classList.remove("walkthrough-modal-centered");
  card.classList.add("walkthrough-modal-anchored");
  card.style.right = "auto";
  card.style.bottom = "auto";
  card.style.transform = "none";
  card.style.top = `${Math.round(top)}px`;
  card.style.left = `${Math.round(left)}px`;
}

/**
 * Measure coach-card size while anchored. Avoids getBoundingClientRect while
 * still under centered translate(-50%,-50%), which under-reports and then pins
 * only the footer into a viewport corner.
 */
function measureWalkthroughCardSize(card, gap) {
  const { vw, vh } = walkthroughViewportSize();
  const maxW = Math.max(160, vw - gap * 2);
  const maxH = Math.max(120, Math.min(vh - gap * 2, 640));
  // Park at a known origin so offsetWidth/Height match final chrome.
  applyWalkthroughCardAnchor(card, gap, gap);
  const cw = Math.min(Math.max(card.offsetWidth || card.getBoundingClientRect().width || 440, 160), maxW);
  const ch = Math.min(Math.max(card.offsetHeight || card.getBoundingClientRect().height || 280, 120), maxH);
  return { cw, ch, vw, vh, maxW, maxH };
}

function clampWalkthroughCardBox(left, top, cw, ch, gap, vw, vh) {
  const maxLeft = Math.max(gap, vw - cw - gap);
  const maxTop = Math.max(gap, vh - ch - gap);
  return {
    left: clampWalkthroughNumber(left, gap, maxLeft),
    top: clampWalkthroughNumber(top, gap, maxTop)
  };
}

function walkthroughCardFullyOnScreen(box, gap, vw, vh) {
  return (
    box.left >= gap - 1
    && box.top >= gap - 1
    && box.right <= vw - gap + 1
    && box.bottom <= vh - gap + 1
  );
}

function placeWalkthroughCardAwayFrom(target) {
  const card = walkthroughCardNode();
  if (!card) return;
  if (!target) {
    centerWalkthroughCard();
    return;
  }
  const gap = 16;
  const highlight = target.getBoundingClientRect();
  // Zero-size / off-DOM targets (e.g. still-hidden panels) — keep card centered.
  if (highlight.width < 8 || highlight.height < 8) {
    centerWalkthroughCard();
    return;
  }

  const { cw, ch, vw, vh } = measureWalkthroughCardSize(card, gap);
  // Huge targets leave no free band — prefer a readable centered card over a clipped corner.
  const highlightArea = Math.max(1, highlight.width * highlight.height);
  const viewArea = Math.max(1, vw * vh);
  if (highlightArea > viewArea * 0.55 || (cw * ch) > viewArea * 0.45) {
    centerWalkthroughCard();
    return;
  }

  const highlightBox = {
    left: highlight.left,
    top: highlight.top,
    right: highlight.right,
    bottom: highlight.bottom
  };
  const candidates = [
    { top: highlight.bottom + gap, left: highlight.left }, // below
    { top: highlight.top - ch - gap, left: highlight.left }, // above
    { top: highlight.top, left: highlight.right + gap }, // right
    { top: highlight.top, left: highlight.left - cw - gap }, // left
    { top: highlight.bottom + gap, left: vw - cw - gap }, // below-right
    { top: vh - ch - gap, left: gap }, // bottom-left
    { top: gap, left: vw - cw - gap }, // top-right
    { top: vh - ch - gap, left: vw - cw - gap } // bottom-right
  ];

  let best = null;
  let bestOverlap = Infinity;
  let bestFullyOn = false;
  for (const raw of candidates) {
    const clamped = clampWalkthroughCardBox(raw.left, raw.top, cw, ch, gap, vw, vh);
    const box = {
      left: clamped.left,
      top: clamped.top,
      right: clamped.left + cw,
      bottom: clamped.top + ch
    };
    const fullyOn = walkthroughCardFullyOnScreen(box, gap, vw, vh);
    const overlap = rectOverlapArea(box, highlightBox, 12);
    if (overlap === 0 && fullyOn) {
      best = clamped;
      bestFullyOn = true;
      break;
    }
    // Prefer fully on-screen placements; among those, least highlight overlap.
    if (fullyOn && !bestFullyOn) {
      bestFullyOn = true;
      bestOverlap = overlap;
      best = clamped;
      continue;
    }
    if (fullyOn === bestFullyOn && overlap < bestOverlap) {
      bestOverlap = overlap;
      best = clamped;
    }
  }

  if (!best || !bestFullyOn) {
    // No safe side placement — keep the whole card readable.
    centerWalkthroughCard();
    return;
  }

  applyWalkthroughCardAnchor(card, best.left, best.top);

  // Second pass: layout can grow after width switch; re-clamp so footer stays in view.
  const live = card.getBoundingClientRect();
  const liveW = Math.min(Math.max(live.width || cw, 160), Math.max(160, vw - gap * 2));
  const liveH = Math.min(Math.max(live.height || ch, 120), Math.max(120, Math.min(vh - gap * 2, 640)));
  const adjusted = clampWalkthroughCardBox(live.left, live.top, liveW, liveH, gap, vw, vh);
  if (Math.abs(adjusted.left - live.left) > 1 || Math.abs(adjusted.top - live.top) > 1) {
    applyWalkthroughCardAnchor(card, adjusted.left, adjusted.top);
  }
  const finalBox = card.getBoundingClientRect();
  if (!walkthroughCardFullyOnScreen(
    { left: finalBox.left, top: finalBox.top, right: finalBox.right, bottom: finalBox.bottom },
    gap,
    vw,
    vh
  )) {
    centerWalkthroughCard();
  }
}

function activateWalkthroughStackPanel(panel) {
  if (!panel) return;
  const stack = panel.closest(".msbt-stack");
  if (!stack) return;
  const panelId = panel.getAttribute("data-msbt-panel");
  if (!panelId) return;
  if (panel.classList.contains("msbt-stack-active")) return;
  const escaped = (typeof CSS !== "undefined" && CSS.escape) ? CSS.escape(panelId) : panelId;
  const tabBtn = stack.querySelector(`[data-panel-id="${escaped}"]`);
  if (tabBtn && typeof tabBtn.click === "function") {
    tabBtn.click();
  }
}

function walkthroughLayoutTabEl(step) {
  if (!step || !step.tab) return null;
  const id = String(step.tab);
  return document.querySelector(`[data-msbt-layout-tab="${id}"]`) || document.getElementById(`tab-${id}`);
}

function panelIdFromWalkthroughSelector(sel) {
  const text = String(sel || "");
  const match = text.match(/data-msbt-panel\s*=\s*['"]([^'"]+)['"]/i);
  return match ? match[1] : "";
}

/** Unhide / expand a layout panel so tour spotlights are not 0×0. */
function ensureWalkthroughPanelVisible(tabEl, panelId) {
  const id = String(panelId || "").trim();
  if (!tabEl || !id) return false;
  const escaped = (typeof CSS !== "undefined" && CSS.escape) ? CSS.escape(id) : id;
  let panel = tabEl.querySelector(`[data-msbt-panel="${escaped}"]`);
  if (!panel) return false;
  let changed = false;
  const inStash = Boolean(panel.closest(".msbt-panel-stash"));
  const hidden = panel.classList.contains("msbt-panel-hidden") || inStash;
  if (hidden) {
    if (window.MsbtPanelLayout && typeof window.MsbtPanelLayout.showPanel === "function") {
      window.MsbtPanelLayout.showPanel(tabEl, id);
    } else {
      panel.classList.remove("msbt-panel-hidden");
    }
    changed = true;
    panel = tabEl.querySelector(`[data-msbt-panel="${escaped}"]`) || panel;
  }
  if (panel && panel.classList.contains("msbt-panel-collapsed")) {
    const collapseBtn = panel.querySelector(".msbt-panel-collapse");
    if (collapseBtn && typeof collapseBtn.click === "function") {
      collapseBtn.click();
    } else {
      panel.classList.remove("msbt-panel-collapsed");
    }
    changed = true;
  }
  return changed;
}

function collectWalkthroughRevealPanelIds(step) {
  const ids = [];
  const seen = new Set();
  const push = (raw) => {
    const id = String(raw || "").trim();
    if (!id || seen.has(id)) return;
    seen.add(id);
    ids.push(id);
  };
  if (Array.isArray(step && step.revealPanels)) {
    step.revealPanels.forEach(push);
  }
  push(panelIdFromWalkthroughSelector(step && step.targetSel));
  push(panelIdFromWalkthroughSelector(step && step.targetSelFallback));
  const target = resolveWalkthroughTarget(step);
  if (target) {
    const panel = target.closest("[data-msbt-panel]")
      || (target.hasAttribute && target.hasAttribute("data-msbt-panel") ? target : null);
    if (panel) push(panel.getAttribute("data-msbt-panel"));
  }
  return ids;
}

function prepareWalkthroughTarget(step) {
  if (!step) return;
  walkthroughState._didRevealPanels = false;
  if (step.revealInvDetail) {
    const detail = document.getElementById("invDetail");
    if (detail) {
      detail.classList.remove("hidden");
      walkthroughState._revealedInvDetail = true;
      const title = document.getElementById("invDetailTitle");
      if (title && (!String(title.textContent || "").trim() || title.textContent === "Item")) {
        title.textContent = "Selected item detail";
      }
      const meta = document.getElementById("invDetailMeta");
      if (meta && !String(meta.textContent || "").trim()) {
        meta.textContent = "Opens when you click an equipped or backpack item. Tour preview shown so the controls are visible.";
      }
    }
  } else if (walkthroughState._revealedInvDetail) {
    // Leave detail open if the user already had items; only hide when we opened a blank preview.
    const meta = document.getElementById("invDetailMeta");
    const serial = document.getElementById("invDetailSerial");
    const isPreview = meta && /Tour preview/i.test(String(meta.textContent || ""));
    const emptySerial = !serial || !String(serial.value || "").trim();
    if (isPreview && emptySerial) {
      const detail = document.getElementById("invDetail");
      if (detail) detail.classList.add("hidden");
    }
    walkthroughState._revealedInvDetail = false;
  }

  // Restore layout panels hidden via Panels menu / View → Panels so spotlights work.
  const tabEl = walkthroughLayoutTabEl(step);
  if (tabEl) {
    let revealed = false;
    collectWalkthroughRevealPanelIds(step).forEach((panelId) => {
      if (ensureWalkthroughPanelVisible(tabEl, panelId)) revealed = true;
    });
    walkthroughState._didRevealPanels = revealed;
  }
}

function scrollWalkthroughTargetIntoView(target) {
  if (!target || typeof target.scrollIntoView !== "function") return;
  const panel = target.closest("[data-msbt-panel]") || (target.hasAttribute && target.hasAttribute("data-msbt-panel") ? target : null);
  activateWalkthroughStackPanel(panel);
  try {
    target.scrollIntoView({ block: "center", inline: "nearest", behavior: "smooth" });
  } catch {
    try {
      target.scrollIntoView(true);
    } catch {
      /* ignore */
    }
  }
  const shell = document.querySelector(".tab-shell");
  if (shell && typeof shell.getBoundingClientRect === "function") {
    const shellRect = shell.getBoundingClientRect();
    const rect = target.getBoundingClientRect();
    if (rect.top < shellRect.top || rect.bottom > shellRect.bottom) {
      const delta = rect.top - shellRect.top - shellRect.height / 2 + rect.height / 2;
      shell.scrollTop += delta;
    }
  }
}

function applyWalkthroughSpotlightRect(target) {
  const { spotlight } = walkthroughNodes();
  if (!spotlight) return;
  if (!target) {
    clearWalkthroughSpotlight();
    return;
  }
  const rect = target.getBoundingClientRect();
  const pad = 8;
  const width = Math.max(36, rect.width + pad * 2);
  const height = Math.max(36, rect.height + pad * 2);
  spotlight.hidden = false;
  spotlight.style.top = `${Math.max(0, rect.top - pad)}px`;
  spotlight.style.left = `${Math.max(0, rect.left - pad)}px`;
  spotlight.style.width = `${width}px`;
  spotlight.style.height = `${height}px`;
}

function placeWalkthroughSpotlight(step, { skipScroll = false } = {}) {
  const { spotlight } = walkthroughNodes();
  if (!spotlight) return;
  if (walkthroughState._spotlightTimer) {
    window.clearTimeout(walkthroughState._spotlightTimer);
    walkthroughState._spotlightTimer = null;
  }
  prepareWalkthroughTarget(step);
  const target = resolveWalkthroughTarget(step);
  if (!target) {
    clearWalkthroughSpotlight();
    centerWalkthroughCard();
    return;
  }
  const token = ++walkthroughState._spotlightToken;
  const settleMs = skipScroll
    ? 40
    : (walkthroughState._didRevealPanels ? 520 : 320);
  if (!skipScroll) {
    // After unhiding into the grid, wait one frame so scroll sees real geometry.
    if (walkthroughState._didRevealPanels) {
      window.requestAnimationFrame(() => {
        if (token !== walkthroughState._spotlightToken || !walkthroughState.active) return;
        scrollWalkthroughTargetIntoView(resolveWalkthroughTarget(step) || target);
      });
    } else {
      scrollWalkthroughTargetIntoView(target);
    }
  }
  const finish = () => {
    if (token !== walkthroughState._spotlightToken || !walkthroughState.active) return;
    const live = resolveWalkthroughTarget(step) || target;
    applyWalkthroughSpotlightRect(live);
    placeWalkthroughCardAwayFrom(live);
  };
  // Smooth scroll + tab/layout paint: reposition after scroll settles.
  finish();
  walkthroughState._spotlightTimer = window.setTimeout(finish, settleMs);
}

function bindWalkthroughReposition() {
  if (walkthroughState._repositionBound) return;
  walkthroughState._repositionBound = true;
  const handler = () => {
    if (!walkthroughState.active) return;
    const steps = currentWalkthroughSteps();
    const step = steps[walkthroughState.step];
    if (!step || step.type === "choices") return;
    placeWalkthroughSpotlight(step, { skipScroll: true });
  };
  window.addEventListener("resize", handler);
  const shell = document.querySelector(".tab-shell");
  if (shell) shell.addEventListener("scroll", handler, { passive: true });
  walkthroughState._repositionHandler = handler;
}

async function refreshWalkthroughSdkNote() {
  const { sdkNote } = walkthroughNodes();
  if (!sdkNote) return;
  sdkNote.classList.add("hidden");
  sdkNote.textContent = "";
  try {
    const detection = window.msbt && typeof window.msbt.detectSdkMods === "function"
      ? await window.msbt.detectSdkMods()
      : null;
    const required = DEFAULT_SDK_REQUIRED;
    const url = DEFAULT_SDK_REQUIRED_URL;
    let message = `Required: ${required}.`;
    if (!detection || detection.ok === false) {
      message += " Could not verify your SDK install yet — open Updates and install oak2-mod-manager v0.3 if needed.";
      sdkNote.textContent = message;
      sdkNote.classList.remove("hidden");
      return;
    }
    const hasOak = Boolean(detection.oak2Present || detection.hasOak2 || detection.sdkPresent);
    const msbtInstalled = Boolean(detection.msbtInstalled || detection.hasMsbt);
    if (!hasOak) {
      message += ` oak2-mod-manager was not detected. Install from ${url}`;
      sdkNote.textContent = message;
      sdkNote.classList.remove("hidden");
      return;
    }
    if (!msbtInstalled) {
      message += " MSBT .sdkmod is not installed yet — use Updates → Install / Update SDK Mod.";
      sdkNote.textContent = message;
      sdkNote.classList.remove("hidden");
      return;
    }
    sdkNote.textContent = `${message} SDK mod detected.`;
    sdkNote.classList.remove("hidden");
  } catch {
    sdkNote.textContent = `Required: ${DEFAULT_SDK_REQUIRED}. Open Updates if you still need to install SDK tools.`;
    sdkNote.classList.remove("hidden");
  }
}

function clearWalkthroughChoices() {
  const { choices } = walkthroughNodes();
  if (!choices) return;
  choices.innerHTML = "";
  choices.classList.add("hidden");
}

function appendWalkthroughChoiceButton(host, { label, className, onClick }) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = className || "secondary";
  btn.textContent = label;
  btn.addEventListener("click", onClick);
  host.appendChild(btn);
  return btn;
}

function launchWalkthroughAfterMainChoice(starter) {
  walkthroughState.chooserSession = true;
  void endWalkthrough({ skipped: false, quiet: true }).then(() => {
    starter({ fromChooser: true });
  });
}

function renderWalkthroughChoices() {
  const { choices, next } = walkthroughNodes();
  if (!choices) return;
  choices.innerHTML = "";
  choices.classList.remove("hidden");
  centerWalkthroughCard();

  const deep = document.createElement("div");
  deep.className = "walkthrough-choice-group";
  const deepHead = document.createElement("div");
  deepHead.className = "walkthrough-choice-heading";
  deepHead.textContent = "Full walkthroughs";
  deep.appendChild(deepHead);
  appendWalkthroughChoiceButton(deep, {
    label: "Layout editor",
    className: "secondary walkthrough-choice-featured",
    onClick: () => launchWalkthroughAfterMainChoice((opts) => startLayoutTutorial({ force: true, ...opts }))
  });
  appendWalkthroughChoiceButton(deep, {
    label: "Quick Menu setup",
    className: "secondary walkthrough-choice-featured",
    onClick: () => launchWalkthroughAfterMainChoice((opts) => startQuickMenuSetupTutorial({ force: true, ...opts }))
  });
  choices.appendChild(deep);

  const tabs = document.createElement("div");
  tabs.className = "walkthrough-choice-group";
  const tabsHead = document.createElement("div");
  tabsHead.className = "walkthrough-choice-heading";
  tabsHead.textContent = "Per-tab walkthroughs";
  tabs.appendChild(tabsHead);
  MAIN_TAB_CHOICES.forEach((entry) => {
    appendWalkthroughChoiceButton(tabs, {
      label: entry.label,
      className: "secondary",
      onClick: () => launchWalkthroughAfterMainChoice((opts) => startTabTutorial(entry.id, opts))
    });
  });
  choices.appendChild(tabs);

  // Single "I'm done" lives on the footer Skip button (see renderWalkthroughStep).
  if (next) {
    next.disabled = true;
    next.textContent = "Pick above";
  }
}

function currentWalkthroughSteps() {
  return Array.isArray(walkthroughState.steps) && walkthroughState.steps.length
    ? walkthroughState.steps
    : MAIN_TUTORIAL_STEPS;
}

function renderWalkthroughStep() {
  const nodes = walkthroughNodes();
  if (!nodes.modal) return;
  bindWalkthroughReposition();
  const steps = currentWalkthroughSteps();
  const step = steps[walkthroughState.step] || steps[0];
  if (step.tab) switchTab(step.tab);
  if (nodes.title) nodes.title.textContent = step.title;
  if (nodes.body) {
    nodes.body.textContent = step.body || "";
    nodes.body.style.whiteSpace = String(step.body || "").includes("\n") ? "pre-line" : "";
  }
  renderWalkthroughLinks(step);
  if (nodes.progress) {
    nodes.progress.textContent = `${walkthroughModeLabel()} · ${walkthroughState.step + 1} / ${steps.length}`;
  }
  if (nodes.back) nodes.back.disabled = walkthroughState.step <= 0;
  const isChoices = step.type === "choices";
  if (isChoices && walkthroughState.mode === "main") {
    walkthroughState.chooserSession = true;
  }
  if (nodes.dontShowRow) {
    // Show on main overview steps and the end chooser (not on nested tours).
    const showDont = walkthroughState.mode === "main";
    nodes.dontShowRow.classList.toggle("hidden", !showDont);
  }
  if (nodes.skip) {
    if (isChoices) nodes.skip.textContent = "I'm done";
    else if (walkthroughState.chooserSession && walkthroughState.mode !== "main") {
      nodes.skip.textContent = "Back to chooser";
    } else {
      nodes.skip.textContent = "Skip";
    }
  }
  if (isChoices) {
    renderWalkthroughChoices();
    clearWalkthroughSpotlight();
    centerWalkthroughCard();
  } else {
    clearWalkthroughChoices();
    // Keep card visible while scroll/spotlight settle.
    centerWalkthroughCard();
    if (nodes.next) {
      nodes.next.disabled = false;
      nodes.next.textContent = walkthroughState.step >= steps.length - 1 ? "Finish" : "Next";
    }
    window.setTimeout(() => placeWalkthroughSpotlight(step), 80);
  }
  if (step.sdk) void refreshWalkthroughSdkNote();
  else if (nodes.sdkNote) nodes.sdkNote.classList.add("hidden");
}

async function persistWalkthroughSettings(extra = {}) {
  if (!window.msbt || typeof window.msbt.saveWalkthroughSettings !== "function") return;
  const nodes = walkthroughNodes();
  const dontShowAgain = Boolean(extra.dontShowAgain ?? (nodes.dontShow && nodes.dontShow.checked) ?? walkthroughState.dontShowAgain);
  walkthroughState.dontShowAgain = dontShowAgain;
  await window.msbt.saveWalkthroughSettings({
    dismissed: Boolean(extra.dismissed),
    dontShowAgain
  });
}

async function endWalkthrough({ skipped = false, quiet = false } = {}) {
  const wasMain = walkthroughState.mode === "main";
  const nodes = walkthroughNodes();
  const suppressUntilUpdate = Boolean(nodes.dontShow && nodes.dontShow.checked);
  const launchingNested = quiet && wasMain && walkthroughState.chooserSession;

  // Nested tour started from the App tour chooser: keep offering more.
  if (!wasMain && walkthroughState.chooserSession) {
    const label = walkthroughModeLabel();
    clearWalkthroughSpotlight();
    clearWalkthroughChoices();
    clearWalkthroughLinks();
    appendActivity(skipped ? `${label} skipped — back to chooser.` : `${label} finished — back to chooser.`);
    reopenMainChooser();
    return;
  }

  if (!launchingNested) {
    walkthroughState.chooserSession = false;
  }

  walkthroughState.active = false;
  if (nodes.modal) nodes.modal.classList.add("hidden");
  clearWalkthroughSpotlight();
  clearWalkthroughChoices();
  clearWalkthroughLinks();
  resetWalkthroughCardPosition();
  if (walkthroughState._spotlightTimer) {
    window.clearTimeout(walkthroughState._spotlightTimer);
    walkthroughState._spotlightTimer = null;
  }
  // Quiet end chains into another tour — keep update chrome suppressed.
  if (!quiet) restoreTourCollidingChrome();
  if (wasMain) {
    markMainTutorialSeen(currentAppVersionString());
    await persistWalkthroughSettings({
      dismissed: true,
      dontShowAgain: suppressUntilUpdate
    });
    if (!quiet) {
      appendActivity(skipped ? "App walkthrough skipped." : "App walkthrough finished.");
    }
  } else if (!quiet) {
    const label = walkthroughModeLabel();
    appendActivity(skipped ? `${label} skipped.` : `${label} finished.`);
  }
}

function walkthroughNext() {
  const steps = currentWalkthroughSteps();
  const step = steps[walkthroughState.step];
  if (step && step.type === "choices") return;
  if (walkthroughState.step >= steps.length - 1) {
    void endWalkthrough({ skipped: false });
    return;
  }
  walkthroughState.step += 1;
  renderWalkthroughStep();
}

function walkthroughBack() {
  if (walkthroughState.step <= 0) return;
  walkthroughState.step -= 1;
  renderWalkthroughStep();
}

function openWalkthroughModal() {
  const nodes = walkthroughNodes();
  if (!nodes.modal) return false;
  walkthroughState.active = true;
  suppressTourCollidingChrome();
  if (nodes.dontShow) nodes.dontShow.checked = false;
  nodes.modal.classList.remove("hidden");
  renderWalkthroughStep();
  return true;
}

function beginNamedTour(mode, steps, { force = false, activity = "" } = {}) {
  walkthroughState.mode = mode;
  walkthroughState.tabId = mode === "tab" ? walkthroughState.tabId : null;
  walkthroughState.steps = steps;
  walkthroughState.step = 0;
  if (!openWalkthroughModal()) return false;
  if (force && activity) appendActivity(activity);
  return true;
}

async function startMainTutorial({ force = false } = {}) {
  walkthroughState.chooserSession = false;
  beginNamedTour("main", TUTORIAL_TOURS.main, {
    force,
    activity: "App walkthrough started."
  });
}

function startLayoutTutorial({ force = true, fromChooser = false } = {}) {
  if (!fromChooser) walkthroughState.chooserSession = false;
  beginNamedTour("layout", TUTORIAL_TOURS.layout, {
    force,
    activity: "Layout editor walkthrough started."
  });
}

function startQuickMenuSetupTutorial({ force = true, fromChooser = false } = {}) {
  if (!fromChooser) walkthroughState.chooserSession = false;
  beginNamedTour("quick-menu-setup", TUTORIAL_TOURS["quick-menu-setup"], {
    force,
    activity: "Quick Menu setup walkthrough started."
  });
}

function startTabTutorial(tabId, { fromChooser = false } = {}) {
  const id = String(tabId || "").trim();
  // ★ Quick Menu Walkthrough launches the full QM setup tour (no redundant tab-only tour).
  if (id === "quick-menu") {
    startQuickMenuSetupTutorial({ force: true, fromChooser });
    return;
  }
  const steps = TAB_TUTORIALS[id];
  if (!steps || !steps.length) {
    appendActivity(`No walkthrough for tab "${id}" yet.`);
    return;
  }
  if (!fromChooser) walkthroughState.chooserSession = false;
  walkthroughState.tabId = id;
  beginNamedTour("tab", steps, {
    force: true,
    activity: `Tab walkthrough: ${id}`
  });
}

/** Hook used by panel layout Walkthrough buttons / View menu */
window.msbtStartTabTutorial = startTabTutorial;
window.msbtStartMainTutorial = startMainTutorial;
window.msbtStartLayoutTutorial = startLayoutTutorial;
window.msbtStartQuickMenuSetupTutorial = startQuickMenuSetupTutorial;

/** Dev helper: clear gating keys then force main tour */
window.msbtResetTutorials = function msbtResetTutorials() {
  try {
    localStorage.removeItem(TUTORIAL_LS_LAST_SEEN);
    localStorage.removeItem(TUTORIAL_LS_MAIN_SEEN);
  } catch {
    /* ignore */
  }
  void startMainTutorial({ force: true });
};

async function startWalkthrough({ force = false } = {}) {
  return startMainTutorial({ force });
}

async function maybeStartWalkthrough() {
  // Ensure version info is available for gating
  if (!state.versionInfo) {
    try {
      await refreshVersionInfo();
    } catch {
      /* continue with fallback version */
    }
  }
  if (!shouldAutoShowMainTutorial()) return;
  await startMainTutorial({ force: false });
}

async function init() {
  wireEvents();
  try {
    if (window.MsbtPanelLayout && typeof window.MsbtPanelLayout.initViewChrome === "function") {
      window.MsbtPanelLayout.initViewChrome();
    }
    if (window.MsbtPanelLayout && typeof window.MsbtPanelLayout.initAll === "function") {
      window.MsbtPanelLayout.initAll();
    }
  } catch (error) {
    console.error("[MSBT] panel layout bootstrap failed:", error);
  }
  updateDevperkToggleButtons();
  if (window.msbt && typeof window.msbt.onUpdateState === "function") {
    window.msbt.onUpdateState(renderUpdateState);
  }
  // Keep catalog / resource loading resilient: one failed IPC must not leave
  // Dev Spawner lists stuck on "Loading...".
  try {
    await loadWindowSettings();
  } catch (error) {
    console.warn("[MSBT] window settings load failed:", error);
  }
  try {
    await refreshVersionInfo();
  } catch (error) {
    console.warn("[MSBT] version info load failed:", error);
  }
  try {
    await refreshSavedDataInfo();
  } catch (error) {
    console.warn("[MSBT] saved data info load failed:", error);
  }
  syncDevSpawnerAdvancedControls();
  await Promise.all([
    loadItemPools().catch((error) => console.warn("[MSBT] item pools load failed:", error)),
    loadTravelResources().catch((error) => console.warn("[MSBT] travel resources load failed:", error)),
    loadTravelFavorites().catch((error) => console.warn("[MSBT] travel favorites load failed:", error)),
    loadDevSpawnerCatalog().catch((error) => console.warn("[MSBT] dev spawner catalog load failed:", error)),
    loadDevSpawnerFavorites().catch((error) => console.warn("[MSBT] dev spawner favorites load failed:", error)),
    loadSerialBookmarks().catch((error) => console.warn("[MSBT] serial bookmarks load failed:", error)),
    loadBl4Catalog().catch((error) => console.warn("[MSBT] BL4 catalog load failed:", error)),
    loadMovementSettings().catch((error) => console.warn("[MSBT] movement settings load failed:", error)),
    loadRaritySettings().catch((error) => console.warn("[MSBT] rarity settings load failed:", error))
  ]);
  try {
    await bridgeStatus();
  } catch (error) {
    console.warn("[MSBT] bridge status failed:", error);
  }
  try {
    await refreshMobileGatewayInfo();
  } catch (error) {
    console.warn("[MSBT] mobile gateway info failed:", error);
  }
  try {
    await loadQuickMenuLayout({ quiet: true });
  } catch (error) {
    console.warn("[MSBT] quick menu layout load failed:", error);
  }
  startBridgeStatusPolling();
  try {
    await refreshDataCatalogStatusUi();
  } catch (error) {
    console.warn("[MSBT] data catalog status failed:", error);
  }
  try {
    await applyRemoteTutorialCopy();
  } catch (error) {
    console.warn("[MSBT] tutorial copy overlay failed:", error);
  }
  try {
    await checkUpdates({ startup: true });
  } catch (error) {
    console.warn("[MSBT] update check failed:", error);
  }
  try {
    await maybeStartWalkthrough();
  } catch (error) {
    console.warn("[MSBT] walkthrough start failed:", error);
  }
  if (!walkthroughState.active) {
    try {
      await showMobileAnnounceModal({ force: false });
    } catch (error) {
      console.warn("[MSBT] mobile announce failed:", error);
    }
  } else {
    state.deferredMobileAnnounce = true;
  }
}

init();
