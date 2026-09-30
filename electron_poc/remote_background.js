"use strict";
// Only enabled remote access owns this background lifetime and login entry.
function createRemoteBackground({app,BrowserWindow,Tray,Menu,nativeImage,powerSaveBlocker,iconPath,onDisable}){
  let tray=null,blocker=null,enabled=false,quitting=false;
  function show(){for(const win of BrowserWindow.getAllWindows()){if(win.isMinimized())win.restore();win.show();win.focus();break;}}
  function update(info){
    if(enabled===info.enabled)return;
    enabled=info.enabled;
    if(app.isPackaged&&process.platform==='win32')app.setLoginItemSettings({openAtLogin:enabled,name:'MSBTRemoteAFK',path:process.execPath,args:['--remote-afk-background']});
    if(enabled){
      blocker=powerSaveBlocker.start('prevent-app-suspension');
      tray=new Tray(nativeImage.createFromPath(iconPath));
      tray.setToolTip('Borderlands 4 Modding Tools — Remote AFK');
      tray.setContextMenu(Menu.buildFromTemplate([
        {label:'Open Borderlands 4 Modding Tools',click:show},
        {label:'Disable remote access',click:()=>{show();void onDisable();}},
        {label:'Quit (remote unavailable until next launch)',click:()=>app.quit()}
      ]));
      tray.on('double-click',show);
    }else{
      if(blocker!==null){powerSaveBlocker.stop(blocker);blocker=null;}
      tray?.destroy();tray=null;
    }
  }
  // Closing the desktop must release its files for Setup, even when remote
  // access is enabled. Minimize keeps remote access running; X exits.
  function bind(win){win.on('close',event=>{if(!quitting){event.preventDefault();app.quit();}});}
  app.on('before-quit',()=>{
    quitting=true;
    if(blocker!==null){powerSaveBlocker.stop(blocker);blocker=null;}
    tray?.destroy();tray=null;
  });
  return {update,bind,show,enabled:()=>enabled};
}
module.exports={createRemoteBackground};
