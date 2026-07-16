const { contextBridge, ipcRenderer, webUtils } = require("electron");

contextBridge.exposeInMainWorld("msbt", {
  bridgeRequest: (args) => ipcRenderer.invoke("bridge:request", args),
  browseSdkMods: () => ipcRenderer.invoke("app:browseSdkMods"),
  detectSdkMods: () => ipcRenderer.invoke("app:detectSdkMods"),
  downloadUpdate: () => ipcRenderer.invoke("app:downloadUpdate"),
  getVersionInfo: () => ipcRenderer.invoke("app:getVersionInfo"),
  getWindowSettings: () => ipcRenderer.invoke("app:getWindowSettings"),
  installSdkMod: (sdkModsPath) => ipcRenderer.invoke("app:installSdkMod", sdkModsPath),
  installDownloadedUpdate: () => ipcRenderer.invoke("app:quitAndInstallUpdate"),
  checkUpdates: () => ipcRenderer.invoke("app:checkUpdates"),
  getUserDataInfo: () => ipcRenderer.invoke("app:getUserDataInfo"),
  openUserDataFolder: () => ipcRenderer.invoke("app:openUserDataFolder"),
  exportUserDataBackup: () => ipcRenderer.invoke("app:exportUserDataBackup"),
  mattEditorUrl: () => ipcRenderer.invoke("app:mattEditorUrl"),
  onUpdateState: (callback) => {
    if (typeof callback !== "function") return () => {};
    const listener = (_event, state) => callback(state);
    ipcRenderer.on("app:updateState", listener);
    return () => ipcRenderer.removeListener("app:updateState", listener);
  },
  serialToolsConvert: (text) => ipcRenderer.invoke("app:serialToolsConvert", text),
  serialDecodeCheck: (text) => ipcRenderer.invoke("app:serialDecodeCheck", text),
  validatorBasic: (text) => ipcRenderer.invoke("app:validatorBasic", text),
  validatorBulk: (text) => ipcRenderer.invoke("app:validatorBulk", text),
  readDevSpawnerCatalog: () => ipcRenderer.invoke("app:readDevSpawnerCatalog"),
  loadDevSpawnerFavorites: () => ipcRenderer.invoke("app:loadDevSpawnerFavorites"),
  saveDevSpawnerFavorites: (payload) => ipcRenderer.invoke("app:saveDevSpawnerFavorites", payload),
  loadSerialBookmarks: () => ipcRenderer.invoke("app:loadSerialBookmarks"),
  saveSerialBookmarks: (payload) => ipcRenderer.invoke("app:saveSerialBookmarks", payload),
  loadMovementSettings: () => ipcRenderer.invoke("app:loadMovementSettings"),
  saveMovementSettings: (payload) => ipcRenderer.invoke("app:saveMovementSettings", payload),
  loadRaritySettings: () => ipcRenderer.invoke("app:loadRaritySettings"),
  saveRaritySettings: (payload) => ipcRenderer.invoke("app:saveRaritySettings", payload),
  loadBl4Catalog: () => ipcRenderer.invoke("app:loadBl4Catalog"),
  refreshGzoCatalog: () => ipcRenderer.invoke("app:refreshGzoCatalog"),
  bl4PartsBreakdown: (serial) => ipcRenderer.invoke("app:bl4PartsBreakdown", serial),
  getPathForFile: (file) => {
    try {
      return webUtils && typeof webUtils.getPathForFile === "function" ? webUtils.getPathForFile(file) : "";
    } catch {
      return "";
    }
  },
  submitGzoCode: (payload) => ipcRenderer.invoke("app:submitGzoCode", payload),
  readSdkLogTail: (options) => ipcRenderer.invoke("app:readSdkLogTail", options),
  readResourceJson: (resourceName) => ipcRenderer.invoke("app:readResourceJson", resourceName),
  saveReportFile: (text) => ipcRenderer.invoke("app:saveReportFile", text),
  openExternal: (url) => ipcRenderer.invoke("app:openExternal", url),
  setWindowOpacity: (opacity) => ipcRenderer.invoke("app:setWindowOpacity", opacity)
});
