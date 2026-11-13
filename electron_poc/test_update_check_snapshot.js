'use strict';
const assert=require('assert/strict');
const fs=require('fs');
const vm=require('vm');
const main=fs.readFileSync(__dirname+'/main.js','utf8');
const renderer=fs.readFileSync(__dirname+'/renderer.js','utf8');
const handler=main.slice(main.indexOf('registerDesktopHandler("app:checkUpdates"'),main.indexOf('registerDesktopHandler("app:downloadUpdate"'));
const check=renderer.slice(renderer.indexOf('async function checkUpdates('),renderer.indexOf('async function downloadElectronUpdate('));
(async()=>{
  let calls=0,registered;
  const info={version:'2.41.3',selected:{browser_download_url:'download'},installer:{browser_download_url:'installer'},portable:{browser_download_url:'portable'},releaseUrl:'release'};
  const context={app:{isPackaged:true,getVersion:()=> '2.41.2'},latestUpdateState:{status:'available'},
    localVersionInfo:async()=>({localManifest:{package_version:'2.41.2'},appVersion:'2.41.2',packageVersion:'2.41.2'}),
    configureAutoUpdater:()=>true,autoUpdater:{checkForUpdates:async()=>{calls++;return {updateInfo:info};}},
    fetchLatestManifest:async()=>{throw Error('Unexpected duplicate metadata fetch');},
    require:()=>({...require('./platform_release_updater')}),normalizeManifestVersion:x=>x,
    isNewerPublicVersion:(a,b)=>a.localeCompare(b,undefined,{numeric:true})>0,manifestMetadataChanged:()=>false,
    updateState:patch=>Object.assign(context.latestUpdateState,patch),registerDesktopHandler:(_name,fn)=>{registered=fn;}};
  vm.runInNewContext(handler,context);
  const result=await registered(null,'');
  assert.equal(calls,1);assert.equal(result.ok,true);assert.equal(result.remote.package_version,info.version);
  assert.equal(result.electronUpdateAvailable,true);assert.equal(result.updateAvailable,true);
  info.version='2.41.2';
  const current=await registered(null,'');assert.equal(current.electronUpdateAvailable,false);assert.equal(current.updateAvailable,false);
  info.version='2.41.3';
  context.autoUpdater.busy=true;context.latestUpdateState.status='progress';
  await registered(null,'');assert.equal(context.latestUpdateState.status,'progress');
  context.autoUpdater.busy=false;context.latestUpdateState.status='available';
  context.autoUpdater.checkForUpdates=async()=>{calls++;throw Error('GitHub temporarily unavailable');};
  const failure=await registered(null,'');
  assert.equal(failure.ok,false);assert.equal(failure.updater.status,'error');assert.match(failure.updater.error,/temporarily unavailable/);
  context.latestUpdateState.status='downloaded';
  await registered(null,'');assert.equal(context.latestUpdateState.status,'downloaded');
  context.app.isPackaged=false;
  context.fetchLatestManifest=async()=>{calls++;return {response:{ok:true},manifest:{package_version:'2.41.3'},url:'fixture'};};
  const before=calls;assert.equal((await registered(null,'')).ok,true);assert.equal(calls,before+1);
  const lines=[];
  const ui={els:{updateSummary:{},sdkModsPath:{},updateOutput:{}},state:{},refreshVersionInfo:async()=>{},
    window:{msbt:{checkUpdates:async()=>({...result,updater:{status:'error',message:'Updater failed',error:'HTTP 403'}})}},
    getValue:()=>'',setOutput:()=>{},renderVersionInfo:()=>{},renderUpdateState:s=>lines.push(s.message+' '+s.error),
    setLine:(_el,text)=>lines.push(text),maybeShowStartupUpdateModal:()=>{}};
  vm.runInNewContext(check+'\nthis.run=checkUpdates;',ui);await ui.run();
  assert.equal(lines.at(-1),'Updater failed HTTP 403');
  console.log('PASS single release snapshot, source fallback, check failure, downloaded state retention and visible updater errors');
})().catch(error=>{console.error(error);process.exitCode=1;});

