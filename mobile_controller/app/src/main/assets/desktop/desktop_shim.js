// Adapt the real Windows renderer to the phone's paired companion transport.
(() => {
  const bridge=parent.mobileDesktopBridge;if(!bridge)throw Error('Open Windows tools from the phone controller.');
  window.MSBT_MOBILE_WORKSPACE=true;
  const api={};
  for(const method of Object.keys(MsbtDesktopContract.methods))api[method]=(...args)=>bridge.call(method,args);
  for(const [method,channel] of Object.entries(MsbtDesktopContract.events))api[method]=callback=>bridge.on(channel,callback);
  api.getPathForFile=()=>'';
  api.focusMainWindow=async()=>({ok:true});
  api.setWindowOpacity=async()=>({ok:true,opacity:1,message:'Phone display stays fully visible.'});
  api.getWindowSettings=async()=>({ok:true,opacity:1});
  api.mattEditorUrl=async()=>({ok:true,hosted:true,url:new URL('editor/index.html?msbtShell=1',location.href).href});
  api.mattEditorOpenFile=async(kind='save')=>{
    const file=await bridge.chooseFile();if(!file)return {ok:false,canceled:true};
    const prefs=await bridge.call('loadMattEditorPrefs').catch(()=>({data:{}}));
    const result={...file,prefs:prefs.data||{},steamId:file.steamId||prefs.data?.steamId||''};
    await bridge.rememberFile(kind,result);return result;
  };
  api.mattEditorReopenFile=async(kind='save')=>{
    const file=await bridge.rememberFile(kind);
    if(!file)return bridge.call('mattEditorReopenFile',[kind]);
    return file.path.startsWith('mobile:')?file:bridge.call('$pcFiles',[{operation:'read',path:file.path}]);
  };
  api.previewSaveItems=async payload=>{
    if(payload?.retry)return bridge.call('previewSaveItems',[payload]);
    const file=await bridge.chooseFile();return file?bridge.call('previewSaveItems',[{...payload,file}]):{ok:false,canceled:true};
  };
  api.mattEditorSaveFile=async payload=>{
    if(payload?.overwrite&&/^(?:[a-z]:[\\/]|\\\\)/i.test(payload.overwritePath||''))return bridge.call('mattEditorSaveFile',[payload]);
    const name=payload?.suggestedName||payload?.overwritePath?.replace(/^mobile:/,'')||'save_encrypted.sav';
    const saved=await bridge.saveDocument(name,payload.base64,'application/octet-stream',true);
    if(saved.ok)await bridge.rememberFile(payload.kind||'save',{ok:true,name,path:'mobile:'+name,base64:payload.base64});
    return saved;
  };
  api.browseSdkMods=async()=>{const detected=await bridge.call('detectSdkMods');const selected=prompt('PC game folder or sdk_mods folder',detected.path||'');return selected?bridge.call('browseSdkMods',[selected]):{ok:false,canceled:true};};
  api.saveReportFile=text=>bridge.saveDocument('MSBT-Report.txt',String(text),'text/plain');
  api.exportUserDataBackup=async()=>{const result=await bridge.call('exportUserDataBackup');return result.download?bridge.saveDocument(result.download.name,result.download.base64,result.download.mime,true):result;};
  api.saveNativeCardScreenshot=async card=>{const result=await bridge.call('captureNativeCard',[card]);return result.ok&&result.base64?bridge.saveDocument('BL4-item-card.png',result.base64,'image/png',true):result;};
  api.openExternal=async url=>{const target=new URL(url);if(!['https:','http:'].includes(target.protocol))throw Error('Unsupported link');bridge.openExternal(target.href);return {ok:true};};
  api.openDeveloperPortal=()=>api.openExternal('https://msbt-community-library.screename53.workers.dev/portal');
  window.msbt=api;
  // Phone preferences are separate from desktop layout storage.
  localStorage.setItem('msbt.bootWelcome.dismissed.v2','1');
  localStorage.setItem('msbt.mobileAnnounce.dismissed.v2','1');
  document.addEventListener('DOMContentLoaded',()=>{
    const actions=document.querySelector('.header-main-actions');if(!actions)return;
    const options=document.createElement('details');options.className='phone-desktop-options';
    const summary=document.createElement('summary');summary.textContent='Tools & settings';options.append(summary);
    const content=document.createElement('div');content.className='phone-desktop-options-body';options.append(content);
    for(const child of [...actions.children])if(!child.classList.contains('app-finder'))content.append(child);
    const support=document.querySelector('.support-panel');if(support)content.append(support);
    actions.append(options);
    document.getElementById('boostMobileNotice')?.classList.add('hidden');
  },{once:true});
  let statusPromise=null,statusAt=0,statusResult=null;
  // Content-addressed text cache: retain large unchanged lists, never live status.
  const statusTexts=new Map();let textBytes=0,textDb=null;
  const textReady=new Promise(resolve=>{
    const opening=indexedDB.open('msbt-status-texts',1);
    opening.onupgradeneeded=()=>opening.result.createObjectStore('texts',{keyPath:'hash'});
    opening.onerror=()=>resolve();
    opening.onsuccess=()=>{
      textDb=opening.result;const read=textDb.transaction('texts').objectStore('texts').getAll();
      read.onsuccess=()=>{for(const row of read.result){statusTexts.set(row.hash,row.text);textBytes+=row.text.length*2;}trimTexts();resolve();};
      read.onerror=()=>resolve();
    };
  });
  function trimTexts(){
    while(statusTexts.size>64||textBytes>16*1024*1024){
      const hash=statusTexts.keys().next().value;textBytes-=statusTexts.get(hash).length*2;statusTexts.delete(hash);
      try{textDb?.transaction('texts','readwrite').objectStore('texts').delete(hash);}catch{}
    }
  }
  async function hydrateStatus(result){
    if(result.mobileStatus?.version!==1)return result; // Older PC companions still work.
    for(const [hash,text] of Object.entries(result.mobileStatus.texts||{})){
      const bytes=new TextEncoder().encode(text),digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(b=>b.toString(16).padStart(2,'0')).join('');
      if(digest!==hash)throw Error('Status data checksum mismatch.');
      if(!statusTexts.has(hash)){statusTexts.set(hash,text);textBytes+=text.length*2;try{textDb?.transaction('texts','readwrite').objectStore('texts').put({hash,text});}catch{}}
    }
    function restore(value){
      if(value&&typeof value==='object'&&Object.keys(value).length===1&&(value.__msbt_status_text__||value.__msbt_status_json__)){
        const text=statusTexts.get(value.__msbt_status_text__||value.__msbt_status_json__);if(text===undefined)throw Error('Status cache incomplete. Refresh the connection.');return value.__msbt_status_json__?JSON.parse(text):text;
      }
      if(Array.isArray(value))return value.map(restore);
      if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([key,item])=>[key,restore(item)]));
      return value;
    }
    const hydrated={...result,data:restore(result.data)};delete hydrated.mobileStatus;trimTexts();return hydrated;
  }
  const request=api.bridgeRequest;
  api.bridgeRequest=async args=>{
    if((args?.method||'GET')==='GET'&&args?.path==='/status'){
      if(!bridge.isOpen()&&statusResult)return statusResult;
      if(statusResult&&Date.now()-statusAt<5000)return statusResult;
      if(!statusPromise)statusPromise=textReady.then(()=>request({...args,mobileStatusHashes:[...statusTexts.keys()]})).then(hydrateStatus).then(result=>{statusAt=Date.now();statusResult=result;return result;}).finally(()=>statusPromise=null);
      return statusPromise;
    }
    statusAt=0;return request(args);
  };
})();
