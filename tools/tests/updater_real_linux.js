'use strict';
/** Disposable Ubuntu 22.04 diagnostic, Node >=24. Run under xvfb-run with xdotool.
 * No app/feed patches; no sandbox bypass; real published IPC only.
 * node tools/tests/updater_real_linux.js OUTPUT_DIRECTORY
 */
const fs = require('node:fs/promises');
const path = require('node:path');
const {createHash} = require('node:crypto');
const {spawn, execFile} = require('node:child_process');
const {promisify} = require('node:util');
const run = promisify(execFile);
const {pipeline} = require('node:stream/promises');
const {Readable} = require('node:stream');
const {connect} = require('./updater_cdp');
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const repo = 'funkyoushift/MattsSDKBoostingTools';
const report = {schema:1, kind:'native-packaged-updater-diagnostic', liveGame:false, publicationReady:false, cases:[]};
let output, root;
const check = (value, message) => {if (!value) throw Error(message);};
async function hash(file) {const h=createHash('sha256');for await(const chunk of require('node:fs').createReadStream(file))h.update(chunk);return h.digest('hex');}
async function api(route) {
  const response=await fetch(`https://api.github.com/repos/${repo}/releases/${route}`,{headers:{Accept:'application/vnd.github+json',...(process.env.GH_TOKEN?{Authorization:`Bearer ${process.env.GH_TOKEN}`}:{})},signal:AbortSignal.timeout(60000)});
  check(response.ok, `GitHub API ${route}: ${response.status}`);return response.json();
}
async function download(release, name) {
  const asset=release.assets.find(a=>a.name===name);check(asset && /^sha256:[a-f0-9]{64}$/i.test(asset.digest||''),`Missing API SHA256: ${name}`);
  const file=path.join(root,name), response=await fetch(asset.url,{headers:{Accept:'application/octet-stream',...(process.env.GH_TOKEN?{Authorization:`Bearer ${process.env.GH_TOKEN}`}:{})},signal:AbortSignal.timeout(30*60*1000)});
  check(response.ok && response.body,`Asset download ${name}: ${response.status}`);
  await pipeline(Readable.fromWeb(response.body),require('node:fs').createWriteStream(file,{flags:'wx'}));
  const sha256=await hash(file);check((await fs.stat(file)).size===asset.size && `sha256:${sha256}`===asset.digest.toLowerCase(),`Size/hash mismatch ${name}`);
  report.assets.push({name,size:asset.size,sha256,assetId:asset.id,url:asset.url});return file;
}
function environment(home) {
  const env={...process.env,HOME:home,XDG_CONFIG_HOME:path.join(home,'.config'),XDG_DATA_HOME:path.join(home,'.local/share'),XDG_CACHE_HOME:path.join(home,'.cache'),XDG_STATE_HOME:path.join(home,'.local/state'),XDG_RUNTIME_DIR:path.join(home,'runtime'),APPIMAGE_EXTRACT_AND_RUN:'1'};
  for(const key of ['APPIMAGE','APPDIR','MSBT_PYTHON','MSBT_SAVE_ROOT','STEAM_COMPAT_DATA_PATH','WINEPREFIX','LD_LIBRARY_PATH','LD_PRELOAD','ELECTRON_RUN_AS_NODE','NODE_OPTIONS']) delete env[key];
  return env;
}
async function processes(home) {
  const found=[];
  for(const pid of await fs.readdir('/proc')) if(/^\d+$/.test(pid)) try {
    const env=(await fs.readFile(`/proc/${pid}/environ`,'utf8')).split('\0');
    if(!env.includes(`HOME=${home}`))continue;
    const exe=await fs.readlink(`/proc/${pid}/exe`),args=(await fs.readFile(`/proc/${pid}/cmdline`,'utf8')).split('\0').filter(Boolean);
    if(path.basename(exe).startsWith('MattsSDKBoostingTools') && !args.some(a=>a.startsWith('--type='))) found.push({pid:Number(pid),exe,args,environment:env.filter(v=>/^(APPIMAGE|APPDIR|LD_LIBRARY_PATH|XDG_DATA_DIRS|MSBT_PYTHON)=/.test(v))});
  }catch{}
  return found;
}
// Send the ordinary WM_DELETE_WINDOW protocol directly; Xvfb needs no window manager.
const X11_CLOSE = `import ctypes,sys
x=ctypes.CDLL('libX11.so.6')
x.XOpenDisplay.argtypes=[ctypes.c_char_p];x.XOpenDisplay.restype=ctypes.c_void_p
x.XInternAtom.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_int];x.XInternAtom.restype=ctypes.c_ulong
class Data(ctypes.Union): _fields_=[('b',ctypes.c_char*20),('s',ctypes.c_short*10),('l',ctypes.c_long*5)]
class Message(ctypes.Structure): _fields_=[('type',ctypes.c_int),('serial',ctypes.c_ulong),('send_event',ctypes.c_int),('display',ctypes.c_void_p),('window',ctypes.c_ulong),('message_type',ctypes.c_ulong),('format',ctypes.c_int),('data',Data)]
class Event(ctypes.Union): _fields_=[('client',Message),('pad',ctypes.c_long*24)]
x.XSendEvent.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_long,ctypes.POINTER(Event)]
x.XFlush.argtypes=[ctypes.c_void_p];x.XCloseDisplay.argtypes=[ctypes.c_void_p]
d=x.XOpenDisplay(None)
if not d: raise RuntimeError('No X display')
w=int(sys.argv[1]);e=Event();e.client.type=33;e.client.display=d;e.client.window=w;e.client.message_type=x.XInternAtom(d,b'WM_PROTOCOLS',0);e.client.format=32;e.client.data.l[0]=x.XInternAtom(d,b'WM_DELETE_WINDOW',0)
x.XSendEvent(d,w,0,0,ctypes.byref(e));x.XFlush(d);x.XCloseDisplay(d)
`;
async function closeOwned(home) {
  for(const proc of await processes(home)) {
    let windows=[];try {windows=(await run('xdotool',['search','--pid',String(proc.pid)])).stdout.trim().split('\n').filter(Boolean);}catch{}
    for(const window of windows) await run('python3',['-c',X11_CLOSE,window]).catch(()=>{});
  }
  for(let n=0;n<30;n++){if(!(await processes(home)).length)return;await pause(1000);}
  check(!(await processes(home)).length,'Owned desktop did not exit after normal WM_DELETE_WINDOW close; no force-kill issued');
}
async function launch(file, args, env, port, record) {
  const log=await fs.open(path.join(output,`${record.kind}-${record.launches++}.log`),'w');
  const child=spawn(file,[...args,`--remote-debugging-address=127.0.0.1`,`--remote-debugging-port=${port}`],{env,cwd:env.HOME,stdio:['ignore',log.fd,log.fd]});
  child.on('error',error=>{record.launchError=String(error);});child.on('exit',(code,signal)=>{record.lastExit={code,signal};});
  await log.close();return child;
}
async function trial(kind, oldFile, newFile, port) {
  const record={kind,launches:0,ok:false,stages:[]};report.cases.push(record);
  const home=path.join(root,kind,'home');await fs.mkdir(path.join(home,'runtime'),{recursive:true,mode:0o700});
  const env=environment(home);let cdp;
  const stage=async(name,expression)=>{const value=await cdp.evaluate(expression,35*60*1000);record.stages.push({name,value});await persist();return value;};
  try {
    let launcher,launchArgs=[];
    if(kind==='appimage') {
      await fs.chmod(oldFile,0o755);await launch(oldFile,['--appimage-extract-and-run'],env,port,record);
      cdp=await connect(port,{pageFilter:t=>t.type==='page' && t.url.includes('linux_setup')});
      const installed=await stage('actual-desktop-setup',`window.linuxSetup.install({setupGame:false,gameRoot:''})`);check(installed.ok,JSON.stringify(installed));
      launcher=installed.appPath;record.desktopLauncher=installed.launcherPath;
      await cdp.closeBrowser();cdp.close();cdp=null;await closeOwned(home);launchArgs=['--appimage-extract-and-run'];
    } else {
      const destination=path.join(root,kind,'application');await fs.mkdir(destination,{recursive:true});
      await run('tar',['-xzf',oldFile,'-C',destination]);const entries=await fs.readdir(destination);check(entries.length===1,'Unexpected portable archive root');
      launcher=path.join(destination,entries[0],'msbt');
    }
    record.launcher=launcher;await launch(launcher,launchArgs,env,port,record);cdp=await connect(port);
    const version=await stage('old-runtime-version','window.msbt.getVersionInfo()');check(version.appVersion==='2.41.1',`Old runtime is not 2.41.1: ${JSON.stringify(version)}`);
    const data=await stage('user-data','window.msbt.getUserDataInfo()');check(path.resolve(data.path).startsWith(home+path.sep),'UserData escaped isolated HOME');
    await stage('seed-preference',`localStorage.setItem('msbt-upgrade-test-preference','preserve-2411-to-2412');localStorage.getItem('msbt-upgrade-test-preference')`);
    check((await stage('seed-bookmark',`window.msbt.saveSerialBookmarks({version:1,bookmarks:[{id:'updater-fixture',name:'Upgrade preservation fixture',group:'Updater test',serial:'TEST_ONLY_NOT_A_GAME_SERIAL',created_at:'2026-01-01T00:00:00.000Z',updated_at:'2026-01-01T00:00:00.000Z'}],folders:[]})`)).ok,'Bookmark seed failed');
    check((await stage('seed-editor-prefs',`window.msbt.saveMattEditorPrefs({version:1,steamId:'updater-fixture'})`)).ok,'Prefs seed failed');
    const sentinels=[path.join(data.path,'serial_bookmarks.json'),path.join(data.path,'matt_editor_prefs.json'),path.join(data.path,'updater-preserve-sentinel.json'),path.join(home,'fixture-game','Saved','SaveGames','fixture-only.sav')];
    await fs.writeFile(sentinels[2],'{"fixture":true,"value":"unchanged"}\n');await fs.mkdir(path.dirname(sentinels[3]),{recursive:true});await fs.writeFile(sentinels[3],'TEST ONLY: no real game save\n');
    record.before=Object.fromEntries(await Promise.all(sentinels.map(async file=>[file,await hash(file)])));
    const checkResult=await stage('real-check','window.msbt.checkUpdates()');check(checkResult.ok && checkResult.remote?.package_version==='2.41.2','Public latest check must resolve exactly 2.41.2');
    const selected=checkResult.updater?.updateInfo?.selected; if(selected)check(selected.name.includes(kind==='appimage'?'.AppImage':'.tar.gz'),'Wrong update asset route');
    const downloaded=await stage('real-download','window.msbt.downloadUpdate()');check(downloaded.ok,`Published updater download failed: ${JSON.stringify(downloaded)}`);
    await stage('real-install-request',`window.__trialInstall=null;window.msbt.installDownloadedUpdate().then(r=>window.__trialInstall=r).catch(e=>window.__trialInstall={ok:false,error:String(e)});'requested'`);
    let restarted=[],disconnected=false;
    for(let n=0;n<120;n++) {await pause(1000);if(!disconnected)try{const result=await cdp.evaluate('window.__trialInstall',3000);if(result?.ok===false)throw Error(JSON.stringify(result));}catch(error){if(String(error).includes('"ok":false'))throw error;disconnected=true;}
      restarted=await processes(home);if(restarted.length && restarted.every(p=>!p.args.includes(`--remote-debugging-port=${port}`)))break;
    }
    record.automaticHandoffProcesses=restarted;check(restarted.length && restarted.every(p=>!p.args.includes(`--remote-debugging-port=${port}`)),'No automatic restarted desktop observed');
    record.automaticHandoffRuntimeVersion='UNVERIFIED: released handoff does not retain CDP arguments';
    if(kind==='appimage')check(restarted.some(p=>p.environment.includes(`APPIMAGE=${launcher}`)),'Automatic AppImage process APPIMAGE does not match stable launcher');
    if(kind==='appimage')check(await hash(launcher)===await hash(newFile),'Stable AppImage launcher does not match published 2.41.2 bytes');
    else {
      check(restarted.some(p=>p.exe===path.join(path.dirname(launcher),'MattsSDKBoostingTools')),'Portable handoff changed installation path');
      const reference=path.join(root,kind,'published-reference');await fs.mkdir(reference,{recursive:true});await run('tar',['-xzf',newFile,'-C',reference]);
      const roots=await fs.readdir(reference);check(roots.length===1,'Unexpected new portable root');
      for(const relative of ['MattsSDKBoostingTools','resources/app.asar'])check(await hash(path.join(path.dirname(launcher),relative))===await hash(path.join(reference,roots[0],relative)),`Updated portable payload differs from published asset: ${relative}`);
    }
    cdp.close();cdp=null;await closeOwned(home);
    await launch(launcher,launchArgs,env,port,record);cdp=await connect(port);
    const current=await stage('second-restart-runtime','window.msbt.getVersionInfo()');check(current.appVersion==='2.41.2','Second restart runtime is not 2.41.2');
    const currentData=await stage('second-restart-user-data','window.msbt.getUserDataInfo()');check(currentData.path===data.path,'UserData path changed');
    check(await stage('preserved-preference',`localStorage.getItem('msbt-upgrade-test-preference')`)==='preserve-2411-to-2412','LocalStorage preference changed');
    check(JSON.stringify(await stage('preserved-bookmarks','window.msbt.loadSerialBookmarks()')).includes('updater-fixture'),'Bookmark missing');
    record.after=Object.fromEntries(await Promise.all(sentinels.map(async file=>[file,await hash(file)])));check(JSON.stringify(record.before)===JSON.stringify(record.after),'Seeded file bytes changed');
    await cdp.closeBrowser();cdp.close();cdp=null;await closeOwned(home);record.ok=true;
  } catch(error) {record.error=String(error.stack||error);}
  finally {if(cdp){await cdp.closeBrowser();cdp.close();}await closeOwned(home).catch(error=>{record.cleanupError=String(error);record.ok=false;});await persist();}
}
async function persist(){await fs.writeFile(path.join(output,'linux-real-updater.json'),JSON.stringify(report,null,2)+'\n');}
(async()=>{
  check(process.platform==='linux' && process.arch==='x64' && process.getuid()!==0,'Native non-root Linux x64 required');
  check(process.env.GITHUB_ACTIONS==='true' && process.env.RUNNER_TEMP && process.env.DISPLAY,'Disposable GitHub runner under Xvfb required');
  const osRelease=await fs.readFile('/etc/os-release','utf8');check(/^VERSION_ID="22.04"$/m.test(osRelease),'Ubuntu 22.04 required');
  output=path.resolve(process.argv[2]||path.join(process.env.RUNNER_TEMP,'msbt-real-updater-report'));await fs.mkdir(output,{recursive:true});
  root=await fs.mkdtemp(path.join(path.resolve(process.env.RUNNER_TEMP),'msbt-real-linux-'));report.workspace=root;report.assets=[];report.osRelease=osRelease;report.node=process.version;report.sourceCommit=(await run('git',['rev-parse','HEAD'])).stdout.trim();report.runUrl=process.env.GITHUB_SERVER_URL && process.env.GITHUB_REPOSITORY && process.env.GITHUB_RUN_ID ? `${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}` : null;
  const old=await api('tags/v2.41.1'),latest=await api('latest');check(old.tag_name==='v2.41.1' && latest.tag_name==='v2.41.2' && !latest.draft && !latest.prerelease,'Published latest is not stable v2.41.2');
  report.releaseIds={old:old.id,latest:latest.id};
  for(const [kind,suffix,prefix] of [['portable','tar.gz','Portable'],['appimage','AppImage','Installer']]) {
    try {
      const before=await download(old,`MSBT-${prefix}-v2.41.1-linux-x64.${suffix}`),after=await download(latest,`MSBT-${prefix}-v2.41.2-linux-x64.${suffix}`);
      await trial(kind,before,after,kind==='portable'?19341:19342);
    } catch(error){report.cases.push({kind,ok:false,error:String(error.stack||error)});await persist();}
  }
  report.ok=report.cases.length===2 && report.cases.every(c=>c.ok);await persist();if(!report.ok)process.exitCode=1;
})().catch(async error=>{report.ok=false;report.error=String(error.stack||error);if(output)await persist();console.error(report.error);process.exitCode=1;});
