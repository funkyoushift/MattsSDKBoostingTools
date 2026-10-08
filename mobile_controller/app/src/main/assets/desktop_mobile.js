// Full Windows workspace uses the same paired connection as the quick controls.
(() => {
  const client=read('msbt.mobile.desktop.client',null)||crypto.randomUUID();write('msbt.mobile.desktop.client',client);
  let cursor=0,flushTimer=null,pollTimer=null,serial=Promise.resolve(),lastRemote=0,opened=false;
  const pending=new Map(),listeners=new Map(),acknowledged=new Set();
  const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const digest=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(b=>b.toString(16).padStart(2,'0')).join('');
  const base64=bytes=>{let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(binary);};
  const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));
  const status=message=>{const node=$('desktopToolsStatus');if(node)node.textContent=message;};
  function transport(body){
    const operation=async()=>{
      if(state.connection.remote){const wait=1250-(Date.now()-lastRemote);if(wait>0)await sleep(wait);lastRemote=Date.now();}
      const ack=[...acknowledged].slice(0,24);
      const result=await gatewayFetch('/desktop',{method:'POST',payload:{...body,client,cursor,ack},timeoutMs:40000});
      if(!result.ok||result.data?.ok===false)throw Error(result.data?.message||'Connect to the desktop Mobile Gateway or Remote connection to use Windows tools.');
      for(const id of ack)acknowledged.delete(id);
      return result.data.reply;
    };
    const result=serial.then(operation,operation);serial=result.catch(()=>{});return result;
  }
  async function unpack(reply){
    if(!reply?.transfer)return reply;
    const transfer=reply.transfer,parts=[];status('Syncing PC data…');
    for(let index=0;index<transfer.parts;index++){parts.push(decode((await transport({op:'part',id:transfer.id,index})).base64));status('Syncing PC data '+Math.round((index+1)*100/transfer.parts)+'%');}
    const bytes=new Uint8Array(parts.reduce((sum,part)=>sum+part.length,0));let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}
    if(bytes.length!==transfer.bytes||await digest(bytes)!==transfer.sha256)throw Error('Tool data checksum mismatch. Check the result before retrying.');
    await transport({op:'release',id:transfer.id});
    const decoded=transfer.encoding==='gzip'?new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()):bytes;
    if(transfer.decodedBytes&&decoded.length!==transfer.decodedBytes)throw Error('Tool data is incomplete. Check the result before retrying.');
    return JSON.parse(new TextDecoder().decode(decoded));
  }
  let exchange=Promise.resolve(),begun=false,workspaceConnection='';
  function request(body){
    const operation=async()=>unpack(await transport(body));
    const result=exchange.then(operation,operation);exchange=result.catch(()=>{});return result;
  }
  function receive(reply){
    if(!reply)return;
    for(const event of reply.events||[])for(const fn of listeners.get(event.channel)||[])try{fn(event.payload);}catch{}
    cursor=reply.cursor??cursor;
    for(const job of reply.jobs||[]){const task=pending.get(job.id);if(!task||job.state==='running')continue;pending.delete(job.id);acknowledged.add(job.id);job.state==='done'?task.resolve(job.value):task.reject(Error(job.message||'Desktop tool failed'));}
    status(state.connection.remote?'Connected remotely · AFK runs independently':'Connected to Windows companion');
    schedulePoll();
  }
  function schedulePoll(){
    clearTimeout(pollTimer);
    if(!pending.size&&!opened)return;
    pollTimer=setTimeout(async()=>{
      const ids=[...pending].filter(([,task])=>task.sent&&task.pollable).map(([id])=>id).slice(0,24);
      try{receive(await request({op:'poll',ids}));}
      catch(error){for(const id of ids){pending.get(id)?.reject(error);pending.delete(id);}status(error.message);schedulePoll();}
    },pending.size?1500:10000);
  }
  async function flush(){
    flushTimer=null;
    const tasks=[];let batchBytes=0;
    for(const entry of pending){
      if(entry[1].sent)continue;
      const bytes=new TextEncoder().encode(JSON.stringify(entry[1].call)).length;
      if(tasks.length&&(tasks.length>=12||batchBytes+bytes>1024*1024))break;
      tasks.push(entry);batchBytes+=bytes;
      if(batchBytes>1024*1024)break;
    }
    if(!tasks.length)return;
    for(const [,task] of tasks)task.sent=true;
    try{
      const large=tasks.find(([,task])=>new TextEncoder().encode(JSON.stringify(task.call)).length>1024*1024);
      if(large){
        for(const [id,task] of tasks)if(id!==large[0])task.sent=false;
        const bytes=new TextEncoder().encode(JSON.stringify(large[1].call)),hash=await digest(bytes),parts=Math.ceil(bytes.length/(1024*1024));
        if(parts>128)throw Error('This file exceeds the transfer limit.');
        status('Sending file to Windows companion…');
        for(let index=0;index<parts;index++)await transport({op:'upload',id:large[0],index,parts,sha256:hash,base64:base64(bytes.subarray(index*1024*1024,(index+1)*1024*1024))});
        const reply=await request({op:'uploadedStart',id:large[0]});large[1].pollable=true;receive(reply);
      }else{
        const reply=await request({op:'start',calls:tasks.map(([,task])=>task.call)});
        for(const [,task] of tasks)task.pollable=true;receive(reply);
      }
    }catch(error){for(const [id,task] of tasks)if(task.sent){pending.delete(id);task.reject(error);}status(error.message);}
    if([...pending.values()].some(task=>!task.sent))flushTimer=setTimeout(flush,40);
  }
  function call(method,args=[]){
    return new Promise((resolve,reject)=>{const id=crypto.randomUUID();pending.set(id,{call:{id,method,args},resolve,reject,sent:false,pollable:false});clearTimeout(flushTimer);flushTimer=setTimeout(flush,40);});
  }
  function on(channel,callback){if(!listeners.has(channel))listeners.set(channel,new Set());listeners.get(channel).add(callback);return()=>listeners.get(channel)?.delete(callback);}
  const panel=document.createElement('section');panel.className='screen';panel.dataset.screen='desktop';
  panel.innerHTML='<div class="desktop-tools-bar"><button id="desktopToolsBack">‹ Phone controls</button><span id="desktopToolsStatus">Windows companion tools</span></div><iframe id="desktopToolsFrame" title="All Windows tools"></iframe>';
  document.querySelector('main').append(panel);
  const style=document.createElement('style');style.textContent='body.desktop-tools-open>header,body.desktop-tools-open>.bottom-nav{display:none!important}body.desktop-tools-open main{padding:0!important}body.desktop-tools-open [data-screen=desktop]{position:fixed;inset:0;z-index:10000;background:#090d17;display:flex;flex-direction:column}.desktop-tools-bar{display:flex;align-items:center;gap:10px;padding:8px;background:#151f33;flex:none}.desktop-tools-bar button{min-height:42px}.desktop-tools-bar span{font-size:12px;flex:1}#desktopToolsFrame{border:0;width:100%;flex:1;min-height:0}';document.head.append(style);
  const show=showScreen;
  const safeStyle=document.createElement('style');safeStyle.textContent='body.desktop-tools-open>.chrome-top{display:none!important}body.desktop-tools-open [data-screen=desktop]{padding:0 var(--phone-safe-right,0px) var(--phone-safe-bottom,0px) var(--phone-safe-left,0px)}.desktop-tools-bar{padding-top:calc(8px + var(--phone-safe-top,env(safe-area-inset-top,0px)))}';document.head.append(safeStyle);
  showScreen=function(name,options){
    const result=show(name,options);if(!result)return result;
    opened=name==='desktop';document.body.classList.toggle('desktop-tools-open',opened);
    if(opened){
      stopStatusPolling();
      const connection=JSON.stringify({address:state.connection.address,port:state.connection.port,room:state.connection.remote?.room});
      if(workspaceConnection&&workspaceConnection!==connection){$('desktopToolsFrame').removeAttribute('src');listeners.clear();begun=false;}
      workspaceConnection=connection;
      const load=()=>{if(opened&&!$('desktopToolsFrame').getAttribute('src'))$('desktopToolsFrame').src='desktop/renderer.html';schedulePoll();};
      if(!begun){begun=true;status('Connecting to Windows companion…');request({op:'begin'}).then(receive).catch(error=>status(error.message)).finally(load);}else load();
    }
    else{if(state.online)startStatusPolling();schedulePoll();}
    return result;
  };
  $('desktopToolsBack').onclick=()=>showScreen('home');
  const entry=document.createElement('article');entry.className='card';entry.innerHTML='<p class="eyebrow">FULL TOOLSET</p><h3>All Windows tools</h3><p>Full catalog, Saved Items, community folders, save/profile editor, serial tools, diagnostics, and every Windows workspace. PC tools use your paired Windows companion.</p><button id="openDesktopTools" class="primary">Open all Windows tools</button>';
  document.querySelector('[data-screen=home]').insertBefore(entry,document.querySelector('[data-screen=home] .card'));
  $('openDesktopTools').onclick=()=>showScreen('desktop');
  const more=document.createElement('button');more.textContent='All Windows tools';more.onclick=()=>showScreen('desktop');document.querySelector('[data-screen=more]')?.prepend(more);
  const saves=new Map();
  window.__msbtDocumentSaved=result=>{const task=saves.get(result.id);if(task){saves.delete(result.id);task.resolve(result);}};
  async function saveDocument(name,contents,mime='application/octet-stream',encoded=false){
    const data=encoded?contents:base64(new TextEncoder().encode(contents));
    if(window.MSBTFiles?.saveDocument){const id=crypto.randomUUID();return new Promise(resolve=>{saves.set(id,{resolve});MSBTFiles.saveDocument(id,name,mime,data);});}
    const link=document.createElement('a'),url=URL.createObjectURL(new Blob([decode(data)],{type:mime}));link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),60000);return {ok:true,path:name};
  }
  function fileDialog(){
    return new Promise(resolve=>{
      const dialog=document.createElement('dialog');dialog.innerHTML='<h3>Choose a save or profile</h3><p>Open a file from your phone or your PC save folders.</p><div class="button-grid"><button data-phone>Phone files</button><button data-pc>PC save folders</button><button data-cancel>Cancel</button></div><div data-list></div>';
      document.body.append(dialog);dialog.showModal();let done=false;
      const finish=value=>{if(done)return;done=true;dialog.close();dialog.remove();resolve(value);};
      dialog.oncancel=()=>finish(null);dialog.querySelector('[data-cancel]').onclick=()=>finish(null);
      dialog.querySelector('[data-phone]').onclick=()=>{
        const input=document.createElement('input');input.type='file';input.accept='.sav,.yaml,.yml,.txt';
        input.onchange=async()=>{const file=input.files[0];if(!file)return;if(file.size>48*1024*1024){alert('Choose a file up to 48 MB.');return;}
          finish({ok:true,name:file.name,path:'mobile:'+file.name,folder:'',base64:base64(new Uint8Array(await file.arrayBuffer()))});};input.click();
      };
      const list=dialog.querySelector('[data-list]');
      async function browse(path){
        list.textContent='Loading PC save folders…';
        try{
          const reply=await call('$pcFiles',[{operation:path?'list':'roots',path}]);if(reply.ok===false)throw Error(reply.message);
          list.replaceChildren();if(path){const back=document.createElement('button');back.textContent='Save folders';back.onclick=()=>browse();list.append(back);}
          for(const entry of reply.entries||reply.roots||[]){const button=document.createElement('button');button.textContent=(entry.directory||!path?'Folder: ':'')+entry.name;button.style.display='block';button.style.width='100%';button.onclick=async()=>{
            if(entry.directory||!path)return browse(entry.path);
            try{const file=await call('$pcFiles',[{operation:'read',path:entry.path}]);if(file.ok===false)throw Error(file.message);finish(file);}catch(error){list.textContent=error.message;}
          };list.append(button);}if(!list.children.length)list.textContent='No save folders found on the PC. Open a file from your phone, or open a save once on Windows.';
        }catch(error){list.textContent=error.message;}
      }
      dialog.querySelector('[data-pc]').onclick=()=>browse();
    });
  }
  const rememberedFiles=new Map();
  async function rememberFile(kind,value){
    const key=kind==='profile'?'profile':'save';
    if(value)rememberedFiles.set(key,value);
    try{
      const db=await new Promise((resolve,reject)=>{const request=indexedDB.open('msbt-phone-editor-files',1);request.onupgradeneeded=()=>request.result.createObjectStore('files');request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);});
      try{return await new Promise((resolve,reject)=>{
        const transaction=db.transaction('files',value?'readwrite':'readonly'),store=transaction.objectStore('files'),request=value?store.put(value,key):store.get(key);
        transaction.oncomplete=()=>resolve(value||request.result||rememberedFiles.get(key)||null);transaction.onerror=()=>reject(transaction.error);
      });}finally{db.close();}
    }catch{return rememberedFiles.get(key)||null;}
  }
  const openExternal=url=>{if(window.MSBTFiles?.openExternal)MSBTFiles.openExternal(url);else window.open(url,'_blank');};
  window.mobileDesktopBridge={call,on,saveDocument,chooseFile:fileDialog,rememberFile,openExternal,isOpen:()=>opened,close:()=>showScreen('home')};
})();
