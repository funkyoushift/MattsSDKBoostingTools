'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('linuxSetup',Object.freeze({
  inspect:()=>ipcRenderer.invoke('linuxSetup:inspect'),
  chooseGame:()=>ipcRenderer.invoke('linuxSetup:chooseGame'),
  install:options=>ipcRenderer.invoke('linuxSetup:install',{gameRoot:String(options.gameRoot || ''),setupGame:options.setupGame===true}),
  launch:()=>ipcRenderer.invoke('linuxSetup:launch'),
  onProgress:callback=>{const listener=(_event,value)=>callback(value);ipcRenderer.on('linuxSetup:progress',listener);return()=>ipcRenderer.removeListener('linuxSetup:progress',listener);}
}));
