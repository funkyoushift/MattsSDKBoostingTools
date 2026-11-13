'use strict';
// Node 24, localhost CDP only. Invokes the released preload API unchanged.
const fs = require('node:fs');
async function connect(port, {pageFilter = t=>t.type==='page', timeout=90000}={}) {
  const deadline=Date.now()+timeout;let page;
  while(Date.now()<deadline){try{page=(await(await fetch(`http://127.0.0.1:${Number(port)}/json/list`)).json()).find(pageFilter);if(page)break;}catch{}await new Promise(r=>setTimeout(r,500));}
  if(!page)throw Error('CDP page unavailable');
  const socket=new WebSocket(page.webSocketDebuggerUrl);await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j;});
  let id=0;const pending=new Map();
  socket.onmessage=e=>{const v=JSON.parse(e.data),p=pending.get(v.id);if(p){clearTimeout(p.timer);pending.delete(v.id);v.error?p.reject(Error(JSON.stringify(v.error))):p.resolve(v.result);}};
  socket.onclose=()=>{for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error('CDP disconnected'));}pending.clear();};
  const send=(method,params={},timeoutMs=60000)=>new Promise((resolve,reject)=>{const n=++id,timer=setTimeout(()=>{pending.delete(n);reject(Error('CDP timeout '+method));},timeoutMs);pending.set(n,{resolve,reject,timer});socket.send(JSON.stringify({id:n,method,params}));});
  return {send,evaluate:async(expression,timeoutMs=60000)=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},timeoutMs);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;},close:()=>socket.close(),closeBrowser:()=>send('Browser.close').catch(()=>{})};
}
module.exports={connect};
if(require.main===module) {
const [port, mode, output] = process.argv.slice(2);
if (process.env.GITHUB_ACTIONS !== 'true' || !process.env.RUNNER_TEMP) throw Error('Disposable GitHub runner required');
const receipt = {mode, started: new Date().toISOString(), stages: []};
let socket;
const pause = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  if(mode==='diagnose') {
    // Read only existing renderer state, then detach immediately. Do not invoke
    // the updater again, close the app, or keep its quitting renderer attached.
    let client;
    try {
      client=await connect(port,{pageFilter:t=>t.type==='page'&&t.url.includes('renderer.html'),timeout:5000});
      const result=await client.evaluate(`({url:location.href,ready:document.readyState,hasResult:Object.prototype.hasOwnProperty.call(window,'__upgradeResult'),upgradeResult:window.__upgradeResult ?? null,requestedAt:window.__upgradeRequestedAt ?? null})`,3000);
      receipt.stages.push({name:'existing-handoff-state',result,at:new Date().toISOString()});
    } finally {if(client)client.close();}
    receipt.ok=true;return;
  }
  let page;
  for (let n=0;n<90;n++) {
    try { page=(await (await fetch(`http://127.0.0.1:${Number(port)}/json/list`)).json()).find(t=>t.type==='page' && t.url.includes('renderer.html')); if(page) break; } catch {}
    await pause(1000);
  }
  if (!page) throw Error('Released renderer CDP target unavailable');
  socket=new WebSocket(page.webSocketDebuggerUrl); await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j;});
  let id=0; const pending=new Map();
  socket.onclose=()=>{for(const item of pending.values()){clearTimeout(item.timer);item.reject(Error('CDP disconnected after app exit'));}pending.clear();};
  socket.onmessage=event=>{const v=JSON.parse(event.data); if(pending.has(v.id)){const {resolve,reject,timer}=pending.get(v.id);clearTimeout(timer);pending.delete(v.id);v.error?reject(Error(JSON.stringify(v.error))):resolve(v.result);}};
  const send=(method,params={},timeoutMs=90000)=>new Promise((resolve,reject)=>{const n=++id;const timer=setTimeout(()=>{pending.delete(n);reject(Error('CDP timeout: '+method));},timeoutMs);pending.set(n,{resolve,reject,timer});socket.send(JSON.stringify({id:n,method,params}));});
  const evaluate=async (expression,timeoutMs=90000)=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},timeoutMs);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
  let preloadReady=false;
  for(let n=0;n<60;n++){if(await evaluate("Boolean(window.msbt && window.msbt.getVersionInfo && window.msbt.getUserDataInfo)")){preloadReady=true;break;}await pause(500);}
  if(!preloadReady)throw Error('Released preload API unavailable');
  const stage=async(name,expression,timeoutMs=90000)=>{console.log('START',mode,name);const result=await evaluate(expression,timeoutMs);console.log('DONE',mode,name);receipt.stages.push({name,result,at:new Date().toISOString()});fs.writeFileSync(output,JSON.stringify(receipt,null,2));return result;};
  await stage('version','window.msbt.getVersionInfo()');
  await stage('userData','window.msbt.getUserDataInfo()');
  if(mode==='seed') {
    await stage('preference',`localStorage.setItem('msbt-upgrade-test-preference','preserve-2411-to-2412'); localStorage.getItem('msbt-upgrade-test-preference')`);
    await stage('bookmarks',`window.msbt.saveSerialBookmarks({version:1,bookmarks:[{id:'updater-fixture',name:'Upgrade preservation fixture',group:'Updater test',serial:'TEST_ONLY_NOT_A_GAME_SERIAL',created_at:'2026-01-01T00:00:00.000Z',updated_at:'2026-01-01T00:00:00.000Z'}],folders:[]})`);
  }
  if(mode==='verify') {
    const pref=await stage('preference',`localStorage.getItem('msbt-upgrade-test-preference')`);
    if(pref!=='preserve-2411-to-2412')throw Error('Preference not preserved');
    const bookmarks=await stage('bookmarks','window.msbt.loadSerialBookmarks()');
    if(!JSON.stringify(bookmarks).includes('updater-fixture'))throw Error('Bookmark not preserved');
  }
  if(mode==='update') {
    const check=await stage('check','window.msbt.checkUpdates()');
    if(!check.ok || check.remote?.package_version!=='2.41.2')throw Error('Public latest must be exactly 2.41.2: '+JSON.stringify(check));
    const download=await stage('download','window.msbt.downloadUpdate()',12*60*1000);
    if(!download.ok)throw Error('Released download IPC failed: '+JSON.stringify(download));
    // Start the real install call; app exit may disconnect CDP before its reply.
    await stage('handoff-request',`window.__upgradeResult=null;window.__upgradeRequestedAt=new Date().toISOString();window.msbt.installDownloadedUpdate().then(r=>window.__upgradeResult=r).catch(e=>window.__upgradeResult={error:String(e)});'requested'`);
    // A closing renderer cannot reliably answer CDP evaluation. Detach so the
    // unmodified application can exit; the parent observes installation and relaunch.
    socket.close();socket=null;

  } else await send('Browser.close').catch(()=>{});
  receipt.ok=true;
})().catch(error=>{receipt.ok=false;receipt.error=String(error.stack||error);process.exitCode=1;}).finally(()=>{receipt.finished=new Date().toISOString();fs.writeFileSync(output,JSON.stringify(receipt,null,2));if(socket)socket.close();});
}
