"use strict";
const {app,BrowserWindow}=require("electron");
const assert=require("node:assert/strict");
const path=require("node:path");

app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
  const win=new BrowserWindow({show:false,webPreferences:{partition:"save-replay-lock-"+process.pid}});
  try{
    await win.loadFile(path.join(__dirname,"renderer.html"),{query:{nosplash:"1"}});
    const result=await win.webContents.executeJavaScript(`(async()=>{
      const doc=document.implementation.createHTMLDocument('Stale replay lock');
      doc.body.innerHTML=document.body.innerHTML;
      const el=id=>doc.getElementById(id);
      delete el('fullProgressPanel').dataset.bound;
      const until=async test=>{
        for(let i=0;i<100&&!test();i++)await new Promise(resolve=>setTimeout(resolve,5));
        if(!test())throw Error('Replay lock state did not settle');
      };
      el('missionReplayMethod').value='save';
      el('missionRunBtn').disabled=false;
      el('fullProgressAck').checked=true;
      const updateFull=MsbtFullProgressPanel.bind(doc,async action=>action==='full_progress_preview'?
        {ok:true,allowed:true,message:'Lobby ready.'}:{ok:true,state:'idle'});
      el('fullProgressPreview').click();
      await until(()=>!el('fullProgressStart').disabled);
      let saved={ok:false,state:'failed',active:true,backupAvailable:true,
        message:'Earlier setup failed; backup retained.'};
      const calls=[];
      let panel;
      const legacyUpdate=()=>{
        el('missionRunBtn').disabled=false;
        panel.update();
        updateFull();
      };
      panel=MsbtSaveReplayPanel.bind(doc,{
        api:async(action)=>{
          calls.push(action);
          if(action==='stop')saved={...saved,ok:true,state:'stopped',active:false,message:'Replay stopped.'};
          if(action==='bookmark_list')return {ok:true,bookmarks:[]};
          return saved;
        },
        selection:()=>({mission:'test',checkpoint:0,supported:true,ack:true,busy:false,refreshing:false}),
        legacyUpdate
      });
      await until(()=>!el('missionReplayLock').hidden);
      el('fullProgressPreview').click();
      await until(()=>el('fullProgressOutput').textContent==='Lobby ready.');
      const blocked={mission:el('missionRunBtn').disabled,full:el('fullProgressStart').disabled,
        notice:el('missionReplayLockMessage').textContent};
      el('missionReplayLockStop').click();
      await until(()=>el('missionReplayLock').hidden);
      return {blocked,recovered:{mission:!el('missionRunBtn').disabled,full:!el('fullProgressStart').disabled,
        backup:!el('missionSaveReplayBackup').disabled,stopDisabled:el('missionReplayLockStop').disabled},calls};
    })()`);
    assert.deepEqual([result.blocked.mission,result.blocked.full],[true,true]);
    assert.match(result.blocked.notice,/backup is retained/);
    assert.deepEqual(result.recovered,{mission:true,full:true,backup:true,stopDisabled:true});
    assert.equal(result.calls.filter(action=>action==='stop').length,1);
    assert(!result.calls.some(action=>['start','advance','restore'].includes(action)));
    console.log("PASS stale replay lock explains disabled actions and closes without replay or save restore");
  }finally{win.destroy();app.quit();}
}).catch(error=>{console.error(error);app.exit(1);});
