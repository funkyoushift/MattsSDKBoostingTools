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
  context.latestUpdateState.status='downloaded';context.autoUpdater.ready=true;context.autoUpdater.info=info;
  await registered(null,'');assert.equal(context.latestUpdateState.status,'downloaded');
  // Exercise the actual updater's checking event before a rejected API fetch.
  const {WindowsReleaseUpdater}=require('./platform_release_updater');
  const real=new WindowsReleaseUpdater({app:context.app,isNewer:context.isNewerPublicVersion,fetcher:async()=>{throw Error('Actual fetch unavailable');}});
  real.info={...info};real.ready=true;context.autoUpdater=real;
  real.on('checking-for-update',()=>context.updateState({status:'checking'}));
  const retained=await registered(null,'');
  assert.equal(retained.updater.status,'downloaded');assert.equal(retained.updater.updateInfo,real.info);assert.equal(real.ready,true);
  real.ready=false;context.latestUpdateState.status='downloaded';
  assert.equal((await registered(null,'')).updater.status,'error','Invalidated receipt must not regain Install');
  // A failed older check cannot restore old metadata over a newer download.
  let rejectCheck;real.fetcher=()=>new Promise((_resolve,reject)=>{rejectCheck=reject;});
  real.ready=true;const pending=registered(null,'');
  while(!rejectCheck) await new Promise(resolve=>setImmediate(resolve));
  real.revision=(real.revision||0)+1;real.info={...info,version:'2.41.4'};real.ready=true;
  context.updateState({status:'downloaded',updateInfo:real.info});
  rejectCheck(Error('Old check failed'));await pending;
  assert.equal(context.latestUpdateState.status,'downloaded');assert.equal(context.latestUpdateState.updateInfo.version,'2.41.4');
  // A newer attempt that invalidates ready must likewise remain invalidated.
  rejectCheck=null;const invalidated=registered(null,'');
  while(!rejectCheck) await new Promise(resolve=>setImmediate(resolve));
  real.revision++;real.ready=false;context.updateState({status:'error',error:'New download failed'});
  rejectCheck(Error('Older check failed'));await invalidated;
  assert.equal(context.latestUpdateState.status,'error');assert.equal(context.latestUpdateState.error,'New download failed');
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

