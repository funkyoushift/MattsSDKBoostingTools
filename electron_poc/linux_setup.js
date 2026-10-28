'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const {pathToFileURL} = require('url');
function shouldRunSetup({platform = process.platform,argv = process.argv,env = process.env,home = os.homedir(),io = fs} = {}) {
  if(platform !== 'linux' || argv.some(arg=>arg === '--smoke' || arg === '--install-sdkmods-and-exit')) return false;
  if(argv.includes('--setup')) return true;
  if(!env.APPIMAGE) return false;
  try {
    const receipt=JSON.parse(io.readFileSync(path.join(home,'.local','share','msbt','install.json'),'utf8'));
    if(receipt.schema===1 && path.isAbsolute(receipt.appPath) && io.realpathSync(receipt.appPath)===io.realpathSync(env.APPIMAGE)) return false;
  }catch{}
  return true;
}
async function runSetup({electron = require('electron'),service = require('./linux_setup_service'),resources = process.resourcesPath,imagePath = process.env.APPIMAGE,home = os.homedir()} = {}) {
  const {app,BrowserWindow,ipcMain,dialog}=electron;
  await app.whenReady();
  const win=new BrowserWindow({width:740,height:740,minWidth:620,minHeight:650,show:false,title:'Install MSBT',backgroundColor:'#0c1421',autoHideMenuBar:true,
    webPreferences:{preload:path.join(__dirname,'linux_setup_preload.js'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
  let installing=false,installed=false,retryAllowed=false;
  const documentUrl=pathToFileURL(path.join(__dirname,'linux_setup.html')).href;
  const channels=[];
  const handle=(name,fn)=>{const channel='linuxSetup:'+name;channels.push(channel);ipcMain.handle(channel,async(event,...args)=>{
    if(event.sender!==win.webContents || event.senderFrame!==win.webContents.mainFrame) throw Error('Setup request is not from the installer window.');
    try{return await fn(...args);}catch(error){return {ok:false,message:String(error.message || error)};}
  });};
  handle('inspect',()=>service.inspect({resources,imagePath,home}));
  handle('chooseGame',async()=>{
    if(installing) return {ok:false,message:'Installation is already running.'};
    const result=await dialog.showOpenDialog(win,{title:'Choose the Borderlands 4 game folder',properties:['openDirectory']});
    return result.canceled ? {ok:true,canceled:true} : {ok:true,root:result.filePaths[0]};
  });
  handle('install',async(payload)=>{
    if(installing || (installed && !retryAllowed)) return {ok:false,message:installed?'MSBT is already installed. Launch it below.':'Installation is already running.'};
    if(!payload || typeof payload.setupGame!=='boolean' || typeof payload.gameRoot!=='string' || payload.gameRoot.length>4096) throw Error('Invalid setup options.');
    installing=true;
    try{
      const result=await service.install({resources,imagePath,home,gameRoot:payload.gameRoot,setupGame:payload.setupGame,onProgress:progress=>{
        if(!win.isDestroyed())win.webContents.send('linuxSetup:progress',typeof progress==='string'?{message:progress}:progress);
      }});
      if(result?.ok){installed=true;retryAllowed=['pending','failed'].includes(result.game?.state);}
      return result;
    }finally{installing=false;}
  });
  handle('launch',async()=>{
    if(installing) return {ok:false,message:'Wait for game setup to finish before launching MSBT.'};
    if(!installed) return {ok:false,message:'Install MSBT before launching it.'};
    await service.launchInstalled({home});app.quit();return {ok:true};
  });
  win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  win.webContents.on('will-navigate',(event,url)=>{if(url!==documentUrl)event.preventDefault();});
  win.on('close',event=>{if(installing)event.preventDefault();});
  win.on('closed',()=>{for(const channel of channels)ipcMain.removeHandler(channel);app.quit();});
  await win.loadURL(documentUrl);win.show();
  return win;
}
module.exports={shouldRunSetup,runSetup};
