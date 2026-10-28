'use strict';
const fs = require('fs/promises');
const path = require('path');
const os = require('os');
const {createHash, randomUUID} = require('crypto');
const {execFile, spawn} = require('child_process');
const execute = require('util').promisify(execFile);
const oak = require('./oak2_install');
const linux = require('./linux_runtime');
const {installPak} = require('./pak_install');

const digest = data => createHash('sha256').update(data).digest('hex');
const quote = value => "'" + String(value).replaceAll("'", "'\\''") + "'";
function locations(home) {
  if(!path.isAbsolute(home) || /[\r\n\0]/.test(home))throw Error('The user home directory is invalid.');
  const root = path.join(path.resolve(home), '.local', 'share', 'msbt');
  return {root, image:path.join(root,'MSBT.AppImage'), receipt:path.join(root,'install.json'),
    launcher:path.join(home,'.local','bin','msbt'), desktop:path.join(home,'.local','share','applications','msbt.desktop'),
    setupDesktop:path.join(home,'.local','share','applications','msbt-setup.desktop')};
}
async function exists(file) {try {await fs.access(file);return true;}catch(error){if(error.code==='ENOENT')return false;throw error;}}
async function isBl4Root(root) {
  try {return (await fs.stat(path.join(root,'OakGame','Binaries','Win64','Borderlands4.exe'))).isFile();}
  catch(error){if(error.code==='ENOENT')return false;throw error;}
}
async function rejectLink(file) {try {if((await fs.lstat(file)).isSymbolicLink())throw Error('Setup will not replace a symbolic link: '+file);}catch(error){if(error.code!=='ENOENT')throw error;}}
async function atomicWrite(file, data, mode=0o600) {
  await rejectLink(file);await fs.mkdir(path.dirname(file),{recursive:true});
  const temporary=file+'.incoming-'+randomUUID();
  try {await fs.writeFile(temporary,data,{flag:'wx',mode});await fs.rename(temporary,file);}
  finally {await fs.rm(temporary,{force:true});}
}
async function backup(file, folder) {
  await rejectLink(file);if(!await exists(file))return;
  await fs.mkdir(folder,{recursive:true,mode:0o700});
  const destination=path.join(folder,randomUUID()+'-'+path.basename(file));
  if((await fs.stat(file)).isDirectory())await fs.cp(file,destination,{recursive:true,dereference:false});
  else await fs.copyFile(file,destination);
}
function nativeOverride(text) {
  if(!text.startsWith('WINE REGISTRY Version 2'))throw Error('The Proton registry format is not recognized; no registry was changed.');
  const newline=text.includes('\r\n')?'\r\n':'\n';
  const heading='[Software\\\\Wine\\\\AppDefaults\\\\Borderlands4.exe\\\\DllOverrides]';
  const start=text.indexOf(heading);
  if(start<0)return text+newline+heading+newline+'"dsound"="native,builtin"'+newline;
  const end=text.indexOf(newline+'[',start+heading.length);
  const old=text.slice(start,end<0?text.length:end);
  const setting=/^"dsound"\s*=.*$/mi;
  const changed=setting.test(old)?old.replace(setting,'"dsound"="native,builtin"'):old+newline+'"dsound"="native,builtin"'+newline;
  return text.slice(0,start)+changed+(end<0?'':text.slice(end));
}
async function prefixBusy(prefix) {
  for(const name of await fs.readdir('/proc')) {
    if(!/^\d+$/.test(name))continue;
    try {
      const folder='/proc/'+name;
      if((await fs.stat(folder)).uid!==process.getuid())continue;
      const args=(await fs.readFile(folder+'/cmdline','utf8')).split('\0');
      if(!args.some(arg=>/^(wine(?:64|server)?(?:-preloader)?|proton)$/.test(path.basename(arg))))continue;
      const env=(await fs.readFile(folder+'/environ','utf8')).split('\0');
      for(const entry of env) {
        if(entry.startsWith('WINEPREFIX=') && path.resolve(entry.slice(11))===prefix)return true;
        if(entry.startsWith('STEAM_COMPAT_DATA_PATH=') && path.resolve(entry.slice(23),'pfx')===prefix)return true;
      }
    }catch(error){if(!['ENOENT','ESRCH'].includes(error.code))throw Error('Close the game and its Proton session before completing game setup.');}
  }
  return false;
}
function createService({run=execute,start=spawn,gameState=linux.inspectGameProcesses,isPrefixBusy=prefixBusy}={}) {
  async function inspect({resources,imagePath,home=os.homedir()}) {
    const dirs=locations(home);
    const manifest=JSON.parse(await fs.readFile(path.join(resources,'releases','latest.json'),'utf8'));
    const state=await gameState();const candidates=new Map();
    for(const candidate of oak.bl4GameRootCandidates({env:{...process.env,HOME:home}})) {
      if(await isBl4Root(candidate)) {
        const root=await fs.realpath(candidate);candidates.set(root,{root,label:root});
      }
    }
    return {ok:true,version:manifest.package_version,installRoot:dirs.root,appPath:dirs.image,
      gameCandidates:[...candidates.values()],gameRunning:state.queryFailed||state.processes.length>0,
      installed:await exists(dirs.receipt)};
  }
  async function checkRequirements(resources) {
    const python=path.join(resources,'python','bin','python3');
    const result=await run(python,[path.join(resources,'linux_bootstrap.py'),'--app-dir',path.dirname(resources),'--probe-only'],{timeout:30000,maxBuffer:1024*1024});
    const report=JSON.parse(result.stdout);
    if(!report.ok || report.missing?.length)throw Error(report.error || 'Desktop requirements are missing. Reopen the installer to repair them.');
    await run(python,['-c','import yaml,ssl,ctypes; assert yaml.__version__ == "6.0.3"'],{timeout:30000});
  }
  async function gameIntegration({resources,home,gameRoot,onProgress,backupRoot}) {
    if(!gameRoot)return {state:'pending',message:'The desktop app is installed. Choose the Borderlands 4 folder and run Setup again to finish game integration.'};
    const root=await fs.realpath(gameRoot);
    if(!await isBl4Root(root))throw Error('That is not a Borderlands 4 installation. Choose the main folder containing OakGame/Binaries/Win64/Borderlands4.exe.');
    const steamapps=path.dirname(path.dirname(root));
    let prefix='';
    if(path.basename(path.dirname(root))==='common' && path.basename(steamapps)==='steamapps') {
      const candidate=path.join(steamapps,'compatdata','1285190','pfx');
      if(await exists(path.join(candidate,'user.reg')))prefix=await fs.realpath(candidate);
    }
    let state=await gameState();
    if(state.queryFailed || state.processes.length)return {state:'pending',root,prefix,message:'The desktop app is installed. Close Borderlands 4 normally, then run Setup again to finish game integration. Your game was left running.'};
    const mods=path.join(root,'sdk_mods');
    for(const file of [mods,path.join(mods,'settings'),path.join(mods,'MattsSDKBoostingTools.sdkmod'),path.join(mods,'ActorScriptDeployer'),
      path.join(root,'OakGame','Content','Paks','pakchunk90-Windows_90_P.pak')])await rejectLink(file);
    if(await exists(path.join(mods,'BL4MissionSelector.sdkmod'))) {
      const selector=await oak.readModEnabledState(mods,'BL4MissionSelector');
      if(!selector.available || selector.error || selector.enabled)return {state:'pending',root,prefix,message:'Disable the standalone Mission Selector before installing the full MSBT game mod. Existing mods were preserved.'};
    }
    for(const module of ['MattsSDKBoostingTools','ActorScriptDeployer']) {
      const file=path.join(mods,'settings',module+'.json');
      if(await exists(file))JSON.parse(await fs.readFile(file,'utf8'));
    }
    if(prefix && await isPrefixBusy(prefix))return {state:'pending',root,prefix,message:'The desktop app is installed. Close this game’s Proton session before finishing game setup. No game files were changed.'};
    onProgress({message:'Installing the in-game components…',percent:70});
    const gameBackup=path.join(backupRoot,'game');
    for(const file of [path.join(mods,'MattsSDKBoostingTools.sdkmod'),path.join(mods,'ActorScriptDeployer'),
      path.join(mods,'settings','MattsSDKBoostingTools.json'),path.join(mods,'settings','ActorScriptDeployer.json')])await backup(file,gameBackup);
    const result=await oak.installOak2FromCache(path.join(locations(home).root,'cache'),root,{bundledZip:path.join(resources,'oak2','oak2-sdk.zip')});
    if(!result.ok)throw Error(result.message);
    state=await gameState();if(state.queryFailed || state.processes.length)throw Error('The game started during setup. Close it and run Setup again before replacing its mod.');
    await fs.copyFile(path.join(resources,'sdkmod','MattsSDKBoostingTools.sdkmod'),path.join(mods,'MattsSDKBoostingTools.sdkmod'));
    await fs.cp(path.join(resources,'sdkmods','ActorScriptDeployer'),path.join(mods,'ActorScriptDeployer'),{recursive:true});
    await installPak(path.join(resources,'afk_shift'),root);
    await oak.enableRequiredMods(mods);
    if(!prefix)return {state:'pending',root,message:'The game mod is installed. Run Borderlands 4 once through Steam, close it normally, then run Setup again to configure its new Proton profile. Other Wine launchers need their own prefix configuration.'};
    const runtimeNames=['vcruntime140.dll','msvcp140.dll'];
    const missing=async()=>{
      const absent=[];
      for(const name of runtimeNames) {
        const file=path.join(prefix,'drive_c','windows','system32',name);
        if(!await exists(file) || (await fs.readFile(file)).subarray(0,256).includes(Buffer.from('Wine builtin DLL')))absent.push(name);
      }
      return absent;
    };
    if((await missing()).length) {
      onProgress({message:'Setting up the Microsoft game runtime. Please follow any runtime installer prompts…',percent:85});
      const python=path.join(resources,'python','bin','python3');
      await run(python,[path.join(resources,'linux_bootstrap.py'),'--app-dir',path.dirname(resources),'--ensure-protontricks'],{timeout:20*60*1000,maxBuffer:1024*1024});
      // Interactive runtime setup: the user may review/decline its prompts.
      await run('/usr/bin/protontricks',['1285190','vcrun2022'],{timeout:30*60*1000,maxBuffer:4*1024*1024,
        env:{...process.env,HOME:home,STEAM_COMPAT_DATA_PATH:path.dirname(prefix),WINEPREFIX:prefix}});
      if((await missing()).length)return {state:'pending',root,prefix,message:'The game mod is installed, but the Microsoft runtime is still missing. Complete its setup before playing with SDK mods.'};
    }
    state=await gameState();if(state.queryFailed || state.processes.length || await isPrefixBusy(prefix))return {state:'pending',root,prefix,message:'The game mod is installed. Close the game and its Proton session, then run Setup again to finish the loader configuration.'};
    const registry=path.join(prefix,'user.reg');const old=await fs.readFile(registry,'utf8');const next=nativeOverride(old);
    if(next!==old){await backup(registry,gameBackup);await atomicWrite(registry,next,(await fs.stat(registry)).mode&0o777);}
    return {state:'installed',root,prefix,message:'The in-game mod, Proton loader and game runtime are ready. Start Borderlands 4 normally from Steam.'};
  }
  async function install({resources,imagePath,home=os.homedir(),gameRoot='',setupGame=true,onProgress=()=>{}}) {
    const dirs=locations(home);let copied=false;
    try {
      if(process.getuid?.()===0)throw Error('Run Setup as your normal desktop user. Only missing system packages need administrator approval.');
      if(!imagePath || !path.isAbsolute(imagePath))throw Error('Run the downloaded MSBT AppImage to install it.');
      const source=await fs.realpath(imagePath);const image=await fs.readFile(source);
      if(image.subarray(0,4).toString('hex')!=='7f454c46')throw Error('The installer AppImage is not a valid executable file.');
      onProgress({message:'Checking the bundled app and desktop requirements…',percent:10});await checkRequirements(resources);
      for(const relative of ['sdkmod/MattsSDKBoostingTools.sdkmod','sdkmods/ActorScriptDeployer/__init__.py','oak2/oak2-sdk.zip','afk_shift/manifest.json'])await fs.access(path.join(resources,relative));
      await rejectLink(dirs.root);await fs.mkdir(dirs.root,{recursive:true});
      const backupRoot=path.join(dirs.root,'backups',new Date().toISOString().replaceAll(':','-')+'-'+randomUUID());
      await rejectLink(dirs.image);
      const imageChanged=!await exists(dirs.image) || digest(await fs.readFile(dirs.image))!==digest(image);
      for(const file of [...(imageChanged?[dirs.image]:[]),dirs.launcher,dirs.desktop,dirs.setupDesktop,dirs.receipt])await backup(file,backupRoot);
      onProgress({message:'Installing MSBT and its bundled Python runtime…',percent:35});
      if(imageChanged)await atomicWrite(dirs.image,image,0o755);else await fs.chmod(dirs.image,0o755);
      copied=true;
      const metadata=JSON.parse(await fs.readFile(path.join(resources,'releases','latest.json'),'utf8'));
      let game={state:setupGame?'pending':'skipped',message:setupGame?'Game integration has not completed yet.':'Desktop app installed. You can run Setup again later to add game integration.'};
      const receipt={schema:1,version:metadata.package_version,appPath:dirs.image,installedAt:new Date().toISOString(),sha256:digest(image),game};
      const icon=path.join(dirs.root,'msbt.png');const iconSource=path.join(resources,'linux-setup','icon.png');
      if(await exists(iconSource))await atomicWrite(icon,await fs.readFile(iconSource),0o644);
      const desktopQuote=value=>'"'+value.replaceAll('\\','\\\\').replaceAll('"','\\"').replaceAll('$','\\$').replaceAll('`','\\`').replaceAll('%','%%')+'"';
      let saveRoot='';
      if(setupGame) {
        try {game=await gameIntegration({resources,home,gameRoot,onProgress,backupRoot});}
        catch(error){game={state:'pending',root:gameRoot,message:'Desktop installation succeeded. Game setup needs attention: '+error.message};}
      }
      if(game.prefix)saveRoot=path.join(game.prefix,'drive_c','users','steamuser','Documents','My Games','Borderlands 4','Saved','SaveGames');
      await atomicWrite(dirs.launcher,'#!/bin/sh\n'+(saveRoot?'export MSBT_SAVE_ROOT='+quote(saveRoot)+'\n':'')+'exec '+quote(dirs.image)+' "$@"\n',0o755);
      await atomicWrite(dirs.desktop,'[Desktop Entry]\nType=Application\nName=Borderlands 4 Modding Tools\nExec='+desktopQuote(dirs.launcher)+'\nIcon='+icon+'\nTerminal=false\nCategories=Utility;Game;\n',0o644);
      await atomicWrite(dirs.setupDesktop,'[Desktop Entry]\nType=Application\nName=MSBT Setup\nComment=Install or repair the app and game integration\nExec='+desktopQuote(dirs.launcher)+' --setup\nIcon='+icon+'\nTerminal=false\nCategories=Utility;Game;\n',0o644);
      receipt.game=game;await atomicWrite(dirs.receipt,JSON.stringify(receipt,null,2)+'\n');
      onProgress({message:game.state==='installed'?'MSBT and game integration are installed.':'MSBT is installed.',percent:100});
      return {ok:true,appPath:dirs.image,launcherPath:dirs.launcher,desktopPath:dirs.desktop,setupDesktopPath:dirs.setupDesktop,game,message:'Open MSBT from your applications menu. Use MSBT Setup there to finish or repair game integration.'};
    }catch(error){return {ok:false,message:(copied?'Some app files were installed, but setup could not finish. ':'')+error.message};}
  }
  async function launchInstalled({home=os.homedir()}) {
    const dirs=locations(home);await fs.access(dirs.launcher);
    const env={...process.env};for(const key of ['APPIMAGE','APPDIR','MSBT_PYTHON','ELECTRON_RUN_AS_NODE'])delete env[key];
    env.HOME=home;
    await new Promise((resolve,reject)=>{const child=start(dirs.launcher,[],{env,detached:true,stdio:'ignore',cwd:home});child.once('error',reject);child.once('spawn',()=>{child.unref();resolve();});});
  }
  return {inspect,install,launchInstalled};
}
module.exports={...createService(),createService,nativeOverride,locations,prefixBusy};
