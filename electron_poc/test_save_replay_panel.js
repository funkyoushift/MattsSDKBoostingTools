'use strict';
const {app,BrowserWindow}=require('electron');
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
  const win=new BrowserWindow({show:false,width:1280,height:1000,webPreferences:{partition:'save-replay-ui-'+process.pid,backgroundThrottling:false}});
  await win.loadFile(path.join(__dirname,'renderer.html'),{query:{nosplash:'1'}});
  await win.webContents.insertCSS('.modal-shell, .msbt-boot-splash { display:none !important; }');
  const result=await win.webContents.executeJavaScript(`(async()=>{
    await endWalkthrough({skipped:true,quiet:true});bridgeStatus=async()=>{};
    document.getElementById('mobileAnnounceDismissBtn')?.click();
    MsbtWorkspace.open('boosting','missions');MsbtMissionPanel.showView(document,'practice');
    const el=id=>document.getElementById(id),calls=[];
    el('missionReplayMethod').value='save';
    const choices=[{index:28,title:'Kill Mudmouth',save_backed_supported:true,blocked_reason:'Legacy coverage incomplete'},
      {index:32,title:'Kill Ripper Queen',save_backed_supported:true},
      {index:31,title:'Find the lair',save_backed_supported:false}];
    const count=MsbtMissionPanel.renderPracticeChoices(document,{ok:true,choices});
    let status={ok:true,state:'idle',active:false},ack=false;
    const api=async(action,payload)=>{
      calls.push({action,payload});
      if(action==='bookmark_list'||action==='bookmark_save')return {ok:true,bookmarks:[{id:'a'.repeat(32),name:'My encounter',mission:'Synthetic mission',world:'World_P'}],message:'Bookmark saved.'};
      if(action==='bookmark_start')return status={ok:true,state:'await_other',active:true,message:'Choose another existing character.'};
      if(action==='start')return status={ok:true,state:'await_other',active:true,message:'Choose another existing character.'};
      if(action==='stop')return status={ok:true,state:'stopped',active:false,backupAvailable:true,message:'Backup retained.'};
      if(action==='restore')return status={ok:true,state:'restored',active:false,backupAvailable:true,message:'Pre-replay backup restored.'};
      return status;
    };
    const panel=MsbtSaveReplayPanel.bind(document,{api,selection:()=>({mission:'Mission_Main_Shatteredlands3',checkpoint:Number(el('missionPracticeSelect').value),supported:true,ack}),legacyUpdate:()=>panel.update()});
    await new Promise(r=>setTimeout(r,20));
    const noAck=el('missionPracticeBtn').disabled;ack=true;panel.update();
    const bookmarksLoaded=el('missionBookmarkSelect').options.length===1&&el('missionBookmarkSelect').value==='a'.repeat(32);
    const bookmarkEnabled=!el('missionBookmarkReplay').disabled;
    const enabled=!el('missionPracticeBtn').disabled&&!el('missionPracticeSelect').disabled;
    const defaultFog=el('missionReplayFog').value;
    await panel.start();
    const active={startDisabled:el('missionPracticeBtn').disabled,stopEnabled:!el('missionSaveReplayStop').disabled,
      methodLocked:el('missionReplayMethod').disabled,fogLocked:el('missionReplayFog').disabled,note:el('missionSaveReplayOutput').textContent};
    el('missionSaveReplayStop').click();await new Promise(r=>setTimeout(r,20));
    const stopped={restoreEnabled:!el('missionSaveReplayRestore').disabled,backupEnabled:!el('missionSaveReplayBackup').disabled,methodUnlocked:!el('missionReplayMethod').disabled};
    el('missionSaveReplayRestore').click();await new Promise(r=>setTimeout(r,20));
    const final=el('missionSaveReplayOutput').textContent;
    status={ok:true,state:'ready',active:false,checkpoint:28,mission:'Mission_Main_Shatteredlands3',message:'Replay ready'};
    el('missionPracticeSelect').value='32';el('missionSaveReplayCheck').click();await new Promise(r=>setTimeout(r,20));
    const previous=el('missionSaveReplayOutput').textContent;
    el('missionReplayFog').value='restore';
    el('missionBookmarkReplay').click();await new Promise(r=>setTimeout(r,20));
    const bookmarkStarted=el('missionBookmarkReplay').disabled&&el('missionBookmarkSave').disabled&&el('missionSaveReplayOutput').textContent==='Choose another existing character.';
    status={ok:false,state:'failed',active:true,backupAvailable:true,message:'Save is temporarily locked'};
    el('missionSaveReplayCheck').click();await new Promise(r=>setTimeout(r,20));
    const failureVisible=el('missionPracticeNote').textContent.includes('Save is temporarily locked')&&el('missionPracticeNote').textContent.includes('Stop setup');
    return {count,values:[...el('missionPracticeSelect').options].map(o=>o.value),noAck,enabled,active,stopped,calls,
      defaultFog,final,previous,bookmarksLoaded,bookmarkEnabled,bookmarkStarted,failureVisible,unavailable:el('missionPracticeUnavailableList').textContent};
  })()`);
  assert.equal(result.count,2);assert.deepEqual(result.values,['28','32']);assert(result.noAck&&result.enabled);
  assert.equal(result.defaultFog,'leave');
  assert.deepEqual(result.active,{startDisabled:true,stopEnabled:true,methodLocked:true,fogLocked:true,note:'Choose another existing character.'});
  assert.deepEqual(result.stopped,{restoreEnabled:true,backupEnabled:true,methodUnlocked:true});
  assert.deepEqual(result.calls.filter(c=>c.action==='start').map(c=>c.payload),[{mission:'Mission_Main_Shatteredlands3',checkpoint:28,acknowledge_shared_progress:true,automatic:true,fog_mode:'leave'}]);
  assert.equal(result.calls.find(c=>c.action==='bookmark_start').payload.fog_mode,'restore');
  assert.match(result.unavailable,/No reviewed save-backed setup/);assert.match(result.final,/restored/);
  assert.match(result.previous,/Previous replay setup/);
  assert(result.bookmarksLoaded&&result.bookmarkEnabled&&result.bookmarkStarted);
  assert(result.failureVisible);
  const dir=path.join(__dirname,'../output/testing/save-replay-ui');fs.mkdirSync(dir,{recursive:true});
  for(const width of [360,800,1280]){
    win.setContentSize(width,1000);
    const layout=await win.webContents.executeJavaScript(`(async()=>{
      MsbtMissionPanel.showView(document,'practice');
      document.getElementById('missionReplayFogOptions').scrollIntoView({block:'center'});
      await new Promise(r=>setTimeout(r,80));
      const panel=document.querySelector('[data-msbt-panel="boost-missions"]'),controls=document.getElementById('missionSaveReplayControls');
      return {fogVisible:document.getElementById('missionReplayFog').getBoundingClientRect().width>0,
        overflow:panel.scrollWidth-panel.clientWidth,controlsWidth:controls.getBoundingClientRect().width,
        buttonOverflow:[...controls.querySelectorAll('button')].some(b=>b.getBoundingClientRect().right>panel.getBoundingClientRect().right+3)};
    })()`);
    assert(layout.fogVisible&&layout.overflow<=3&&layout.controlsWidth>0&&!layout.buttonOverflow,JSON.stringify({width,...layout}));
    fs.writeFileSync(path.join(dir,'replay-'+width+'.png'),(await win.webContents.capturePage(undefined,{stayHidden:true,stayAwake:true})).toPNG());
  }
  fs.writeFileSync(path.join(dir,'receipt.json'),JSON.stringify(result,null,2));
  console.log('PASS save replay filtering, acknowledgements, steps, stop, backup restore and responsive controls; all actions stubbed');
  win.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
