const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("msbt", {
  bridgeRequest: (args) => ipcRenderer.invoke("bridge:request", args),
  checkUpdates: () => ipcRenderer.invoke("app:checkUpdates"),
  mattEditorUrl: () => ipcRenderer.invoke("app:mattEditorUrl"),
  serialToolsConvert: (text) => ipcRenderer.invoke("app:serialToolsConvert", text),
  validatorBasic: (text) => ipcRenderer.invoke("app:validatorBasic", text),
  validatorBulk: (text) => ipcRenderer.invoke("app:validatorBulk", text),
  readDevSpawnerCatalog: () => ipcRenderer.invoke("app:readDevSpawnerCatalog"),
  loadDevSpawnerFavorites: () => ipcRenderer.invoke("app:loadDevSpawnerFavorites"),
  saveDevSpawnerFavorites: (payload) => ipcRenderer.invoke("app:saveDevSpawnerFavorites", payload),
  readSdkLogTail: (options) => ipcRenderer.invoke("app:readSdkLogTail", options),
  readResourceJson: (resourceName) => ipcRenderer.invoke("app:readResourceJson", resourceName),
  openExternal: (url) => ipcRenderer.invoke("app:openExternal", url)
});
