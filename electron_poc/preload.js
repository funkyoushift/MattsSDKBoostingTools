const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("msbt", {
  bridgeRequest: (args) => ipcRenderer.invoke("bridge:request", args),
  browseSdkMods: () => ipcRenderer.invoke("app:browseSdkMods"),
  detectSdkMods: () => ipcRenderer.invoke("app:detectSdkMods"),
  downloadUpdate: () => ipcRenderer.invoke("app:downloadUpdate"),
  getVersionInfo: () => ipcRenderer.invoke("app:getVersionInfo"),
  installSdkMod: (sdkModsPath) => ipcRenderer.invoke("app:installSdkMod", sdkModsPath),
  installDownloadedUpdate: () => ipcRenderer.invoke("app:quitAndInstallUpdate"),
  checkUpdates: () => ipcRenderer.invoke("app:checkUpdates"),
  mattEditorUrl: () => ipcRenderer.invoke("app:mattEditorUrl"),
  onUpdateState: (callback) => {
    if (typeof callback !== "function") return () => {};
    const listener = (_event, state) => callback(state);
    ipcRenderer.on("app:updateState", listener);
    return () => ipcRenderer.removeListener("app:updateState", listener);
  },
  serialToolsConvert: (text) => ipcRenderer.invoke("app:serialToolsConvert", text),
  validatorBasic: (text) => ipcRenderer.invoke("app:validatorBasic", text),
  validatorBulk: (text) => ipcRenderer.invoke("app:validatorBulk", text),
  readDevSpawnerCatalog: () => ipcRenderer.invoke("app:readDevSpawnerCatalog"),
  loadDevSpawnerFavorites: () => ipcRenderer.invoke("app:loadDevSpawnerFavorites"),
  saveDevSpawnerFavorites: (payload) => ipcRenderer.invoke("app:saveDevSpawnerFavorites", payload),
  loadSerialBookmarks: () => ipcRenderer.invoke("app:loadSerialBookmarks"),
  saveSerialBookmarks: (payload) => ipcRenderer.invoke("app:saveSerialBookmarks", payload),
  loadBl4Catalog: () => ipcRenderer.invoke("app:loadBl4Catalog"),
  bl4PartsBreakdown: (serial) => ipcRenderer.invoke("app:bl4PartsBreakdown", serial),
  readSdkLogTail: (options) => ipcRenderer.invoke("app:readSdkLogTail", options),
  readResourceJson: (resourceName) => ipcRenderer.invoke("app:readResourceJson", resourceName),
  saveReportFile: (text) => ipcRenderer.invoke("app:saveReportFile", text),
  openExternal: (url) => ipcRenderer.invoke("app:openExternal", url)
});
