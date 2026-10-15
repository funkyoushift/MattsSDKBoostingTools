"use strict";
const {app,BrowserWindow}=require('electron');
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
  const win=new BrowserWindow({show:false,width:1280,height:1000,webPreferences:{partition:'mission-views-'+process.pid,backgroundThrottling:false}});
  await win.loadFile(path.join(__dirname,'renderer.html'),{query:{nosplash:'1'}});
  await win.webContents.insertCSS('.modal-shell, .msbt-boot-splash { display:none !important; }');
  const result=await win.webContents.executeJavaScript(`(async()=>{
    await endWalkthrough({skipped:true,quiet:true});bridgeStatus=async()=>{};
    document.getElementById('mobileAnnounceDismissBtn')?.click();
    const actions=[];runAction=async(...args)=>{actions.push(args);return {ok:true};};
    MsbtWorkspace.open('boosting','missions');
    const byId=id=>document.getElementById(id),visible=id=>byId(id).getBoundingClientRect().height>0;
    const views={complete:'missionRunBtn',practice:'missionPracticeSelect',full:'fullProgressStart'};
    if(document.querySelector('[data-mission-view-button="replay"]'))throw Error('Duplicate replay navigation');
    if(byId('missionSort').value!=='playthrough')throw Error('Playthrough order must be the default');
    if(!MsbtMissionPlaythrough.Mission_Main_Cowbell4)throw Error('Missing DLC ordering');
    const notice=document.querySelector('.mission-experimental-note');
    const experimental={notice:notice.textContent,accent:getComputedStyle(notice).borderLeftColor,
      runLabel:byId('fullProgressStart').textContent};
    const navigation=[];
    for(const [name,id] of Object.entries(views)){
      document.querySelector('[data-mission-view-button="'+name+'"]').click();
      if(name==='practice'&&byId('missionNamesLabel').hidden)throw Error('Mission list must be visible on entering replay');
      navigation.push({name,visible:visible(id),othersHidden:Object.entries(views).filter(([v])=>v!==name).every(([,n])=>!visible(n))});
    }
    const anchor={map:'Harmonica_P',objective:'GoToMiningCamp',location:{x:1,y:2,z:3}};
    byId('missionReplayMethod').value='live';
    const choices=[{index:0,title:'Mission beginning',blocked_reason:'Preceding completion location is not resolved'},
      {index:2,title:'Kill Tediore forces',anchor},{index:3,title:'Find the big score',anchor}];
    MsbtMissionPanel.showView(document,'practice');
    const render=preview=>MsbtMissionPanel.renderPracticeChoices(document,preview,'3');
    const count=render({ok:true,choices});
    const mixed={count,selected:byId('missionPracticeSelect').value,
      values:[...byId('missionPracticeSelect').options].map(o=>o.value),reason:byId('missionPracticeUnavailableList').textContent};
    render({ok:true,choices:choices.map(c=>({...c,blocked_reason:'Missing access'}))});
    const none={options:byId('missionPracticeSelect').options.length,value:byId('missionPracticeSelect').value,
      label:byId('missionPracticeSelect').selectedOptions[0].textContent};
    render(null);
    const cleared=byId('missionPracticeUnavailable').hidden && !byId('missionPracticeUnavailableList').children.length;
    const finder=[];
    for(const [name,id] of Object.entries(views)){
      MsbtMissionPanel.showView(document,'complete');
      MsbtMissionPanel.revealControl(byId(id));finder.push({name,visible:visible(id)});
    }
    render({ok:true,choices});MsbtMissionPanel.showView(document,'practice');
    return {navigation,mixed,none,cleared,finder,actions,experimental};
  })()`);
  assert(result.navigation.every(r=>r.visible&&r.othersHidden),JSON.stringify(result.navigation));
  assert.deepEqual(result.mixed.values,['2','3']);assert.equal(result.mixed.selected,'3');
  assert.match(result.mixed.reason,/Preceding completion location/);
  assert.deepEqual(result.none,{options:1,value:'',label:'No checkpoint locations available'});
  assert(result.cleared&&result.finder.every(r=>r.visible));assert.deepEqual(result.actions,[]);
  assert.match(result.experimental.notice,/Experimental mission tools/);
  assert.match(result.experimental.notice,/may not progress/);
  assert.equal(result.experimental.accent,'rgb(244, 188, 92)');
  assert.equal(result.experimental.runLabel,'Run full game progress');
  const cancellation=await win.webContents.executeJavaScript(`(async()=>{
    const doc=document.implementation.createHTMLDocument('Bound mission regression');
    doc.body.innerHTML=document.body.innerHTML;
    const el=id=>doc.getElementById(id),calls=[];
    el('missionScope').value='current';el('missionSharedAck').checked=true;el('missionReplayMethod').value='live';
    let practice={ok:true,state:'idle'},releaseStep,stepStarted=false;
    const call=async(action,payload)=>{
      calls.push({action,payload});
      if(action==='mission_status')return {ok:true,id:'old-completed',state:'completed'};
      if(action==='mission_preview')return {ok:true,selection_scope:'current',max_batch:10,missions:[{name:'test',title:'Test',state:'completed',category:'story'}]};
      if(action==='mission_practice_preview')return {ok:true,preview_id:'preview',mission:'test',choices:[{index:2,title:'Checkpoint',anchor:{map:'Test_P',objective:'step'}}]};
      if(action==='mission_practice_status')return practice;
      if(action==='mission_practice_start')return practice={ok:true,id:'active-practice',state:'running'};
      if(action==='mission_practice_step'){stepStarted=true;await new Promise(r=>releaseStep=r);return practice;}
      if(action==='mission_practice_cancel')return practice={ok:true,id:'active-practice',state:'cancelled'};
      throw new Error('Unexpected action '+action);
    };
    MsbtMissionPanel.bind(doc,call,()=>null);
    const until=async(test)=>{for(let i=0;i<200&&!test();i++)await new Promise(r=>setTimeout(r,5));if(!test())throw new Error('Timed out waiting for bound panel');};
    await until(()=>!el('missionPracticeBtn').disabled);
    MsbtMissionPanel.showView(doc,'practice');
    el('missionCampaignFilter').value='all';el('missionCampaignFilter').dispatchEvent(new Event('change'));
    await until(()=>el('missionNames').options.length>0);
    el('missionNames').value='test';el('missionNames').dispatchEvent(new Event('change'));
    await until(()=>!el('missionPracticeBtn').disabled);
    el('missionPracticeBtn').click();
    await until(()=>stepStarted);
    MsbtMissionPanel.showView(doc,'complete');
    const during={disabled:el('missionCancelBtn').disabled,text:el('missionCancelBtn').textContent,
      hidden:!!el('missionCancelBtn').closest('[hidden]')};
    el('missionCancelBtn').click();
    await until(()=>practice.state==='cancelled');releaseStep();
    await until(()=>el('missionCancelBtn').disabled);
    return {during,cancel:calls.filter(c=>c.action.endsWith('_cancel')),
      steps:calls.filter(c=>c.action==='mission_practice_step').length};
  })()`);
  assert.deepEqual(cancellation.during,{disabled:false,text:'Stop replay setup',hidden:false});
  assert.deepEqual(cancellation.cancel,[{action:'mission_practice_cancel',payload:{job_id:'active-practice'}}]);
  assert.equal(cancellation.steps,1);
  result.cancellation=cancellation;
  const recovery=await win.webContents.executeJavaScript(`(async()=>{
    const cases=[];
    for(const placement of [true,false]) {
      const doc=document.implementation.createHTMLDocument('Movement recovery');doc.body.innerHTML=document.body.innerHTML;
      const el=id=>doc.getElementById(id),calls=[];
      let status={ok:false,id:'failed-placement',state:'uncertain',completion_context:placement?{placement:{state:'stopped'}}:{}};
      const call=async(action,payload)=>{
        calls.push({action,payload});
        if(action==='mission_status')return status;
        if(action==='mission_practice_status')return {ok:true,state:'idle'};
        if(action==='mission_preview')return {ok:true,selection_scope:'current',max_batch:1,missions:[]};
        if(action==='mission_cancel')return status={...status,state:'running',completion_context:{placement:{stop_state:'cancelled'}}};
        if(action==='mission_step')return status={ok:false,id:status.id,state:'cancelled',message:'Movement restored; remaining steps cancelled.'};
        return {ok:true};
      };
      MsbtMissionPanel.bind(doc,call,()=>null);
      await new Promise(r=>setTimeout(r,30));
      const before={disabled:el('missionCancelBtn').disabled,label:el('missionCancelBtn').textContent};
      if(placement){
        el('missionCancelBtn').click();
        for(let i=0;i<200&&status.state!=='cancelled';i++)await new Promise(r=>setTimeout(r,5));
        await new Promise(r=>setTimeout(r,10));
      }
      cases.push({placement,before,state:status.state,disabledAfter:el('missionCancelBtn').disabled,
        mutations:calls.filter(c=>['mission_cancel','mission_step','mission_start','mission_resume'].includes(c.action))});
    }
    return cases;
  })()`);
  assert.deepEqual(recovery[0].before,{disabled:false,label:'Restore player movement'});
  assert.equal(recovery[0].state,'cancelled');assert(recovery[0].disabledAfter);
  assert.deepEqual(recovery[0].mutations.map(c=>c.action),['mission_cancel','mission_step']);
  assert(recovery[1].before.disabled);assert.deepEqual(recovery[1].mutations,[]);
  result.recovery=recovery;
  const race=await win.webContents.executeJavaScript(`(async()=>{
    const results=[];
    for(const entry of ['missionResumeBtn','missionRecoverBtn']){
    const doc=document.implementation.createHTMLDocument('Deferred movement recovery');doc.body.innerHTML=document.body.innerHTML;
    const el=id=>doc.getElementById(id),calls=[];el('missionSharedAck').checked=true;
    let status={ok:true,id:'deferred-cleanup',state:entry==='missionRecoverBtn'?'uncertain':'running'},releaseStep,releaseCancel,steps=0;
    const call=async(action,payload)=>{
      calls.push(action);
      if(action==='mission_status')return status;
      if(action==='mission_preview')return {ok:true,selection_scope:'current',max_batch:1,missions:[]};
      if(action==='mission_practice_status')return {ok:true,state:'idle'};
      if(action==='mission_recover')return status={...status,state:'running'};
      if(action==='mission_cancel'){await new Promise(r=>releaseCancel=r);return status={...status,ok:false,state:'running',completion_context:{placement:{stop_state:'cancelled'}}};}
      if(action==='mission_step'){
        if(++steps===1){await new Promise(r=>releaseStep=r);return status={...status,ok:false,state:'uncertain',completion_context:{placement:{state:'stopped'}}};}
        return status={...status,ok:false,state:'cancelled'};
      }
      return {ok:true};
    };
    const until=async(test)=>{for(let i=0;i<200&&!test();i++)await new Promise(r=>setTimeout(r,5));if(!test())throw Error('Deferred cleanup test timed out '+JSON.stringify({entry,status,steps,calls,disabled:el(entry).disabled}));};
    MsbtMissionPanel.bind(doc,call,()=>null);await until(()=>!el(entry).disabled);
    el(entry).click();await until(()=>releaseStep);
    el('missionCancelBtn').click();await until(()=>releaseCancel);
    releaseStep();await until(()=>status.state==='uncertain');await new Promise(r=>setTimeout(r,20));
    releaseCancel();await until(()=>status.state==='cancelled');await new Promise(r=>setTimeout(r,20));
    results.push({entry,state:status.state,disabled:el('missionCancelBtn').disabled,steps,cancels:calls.filter(a=>a==='mission_cancel').length});
    }
    return results;
  })()`);
  for(const row of race)assert.deepEqual(row,{entry:row.entry,state:'cancelled',disabled:true,steps:2,cancels:1});
  result.recoveryRace=race;
  const objectiveStop=await win.webContents.executeJavaScript(`(async()=>{
    const doc=document.implementation.createHTMLDocument('Objective stop receipt');doc.body.innerHTML=document.body.innerHTML;
    const el=id=>doc.getElementById(id),calls=[];el('missionSharedAck').checked=true;
    let status={ok:true,id:'selected-objective',state:'running',coordinated:true};
    const call=async(action,payload)=>{
      calls.push({action,payload});
      if(action==='mission_objective_status')return status;
      if(action==='mission_status'||action==='mission_practice_status')return {ok:true,state:'idle'};
      if(action==='mission_preview')return {ok:true,max_batch:1,selection_scope:'current',missions:[]};
      if(action==='mission_objective_cancel'){
        status={...status,ok:false,state:'uncertain'};
        return {ok:false,message:'Lost cancellation response'};
      }
      return {ok:true};
    };
    MsbtMissionPanel.bind(doc,call,()=>null);
    for(let i=0;i<100&&el('missionCancelBtn').disabled;i++)await new Promise(r=>setTimeout(r,5));
    el('missionCancelBtn').click();await new Promise(r=>setTimeout(r,30));
    return {cancel:calls.filter(r=>r.action==='mission_objective_cancel'),
      reconciled:calls.filter(r=>r.action==='mission_objective_status').length,
      canRecover:!el('missionRecoverBtn').disabled,canClose:!el('missionCloseBtn').disabled};
  })()`);
  assert.deepEqual(objectiveStop.cancel,[{action:'mission_objective_cancel',payload:{job_id:'selected-objective'}}]);
  assert(objectiveStop.reconciled>=2&&objectiveStop.canRecover&&objectiveStop.canClose);
  result.objectiveStop=objectiveStop;
  const statusRefresh=await win.webContents.executeJavaScript(`(async()=>{
    const doc=document.implementation.createHTMLDocument('Externally finished objective');doc.body.innerHTML=document.body.innerHTML;
    const el=id=>doc.getElementById(id),calls=[];
    let status={ok:true,id:'external-objective',state:'running',coordinated:true};
    const call=async(action,payload)=>{
      calls.push(action);
      if(action==='mission_objective_status')return status;
      if(action==='mission_status'||action==='mission_practice_status')return {ok:true,state:'idle'};
      if(action==='mission_preview')return {ok:true,max_batch:1,selection_scope:'current',missions:[]};
      return {ok:true};
    };
    const until=async(test)=>{for(let i=0;i<200&&!test();i++)await new Promise(r=>setTimeout(r,5));if(!test())throw Error('Status refresh timed out');};
    MsbtMissionPanel.bind(doc,call,()=>null);await until(()=>!el('missionCancelBtn').disabled);
    await new Promise(r=>setTimeout(r,30));
    status={ok:false,message:'Connection lost'};
    el('missionPreviewBtn').click();await new Promise(r=>setTimeout(r,30));
    const retained=!el('missionCancelBtn').disabled;
    status={ok:true,id:'external-objective',state:'completed',coordinated:true};
    el('missionPreviewBtn').click();await until(()=>el('missionCancelBtn').disabled);
    return {retained,stopDisabled:el('missionCancelBtn').disabled,continueDisabled:el('missionResumeBtn').disabled,
      mutations:calls.filter(a=>!a.endsWith('_status')&&a!=='mission_preview')};
  })()`);
  assert.deepEqual(statusRefresh,{retained:true,stopDisabled:true,continueDisabled:true,mutations:[]});
  result.statusRefresh=statusRefresh;
  const dialogue=await win.webContents.executeJavaScript(`(async()=>{
    const doc=document.implementation.createHTMLDocument('Dialogue toggle');doc.body.innerHTML=document.body.innerHTML;
    const el=id=>doc.getElementById(id),calls=[];let enabled=false;
    const call=async(action,payload)=>{
      if(action==='quick_menu_action'){
        calls.push(payload.action);
        if(payload.action==='dialogue_skip_toggle')enabled=!enabled;
        return {ok:true,enabled,message:enabled?'Dialogue skip is on.':'Dialogue skip is off.'};
      }
      if(action.endsWith('_status'))return {ok:true,state:'idle'};
      if(action==='mission_preview')return {ok:true,missions:[]};
      return {ok:false};
    };
    MsbtMissionPanel.bind(doc,call,()=>null);
    const until=async(test)=>{for(let i=0;i<100&&!test();i++)await new Promise(r=>setTimeout(r,5));if(!test())throw Error('Dialogue UI timed out');};
    el('dialogueSkipToggle').click();await until(()=>el('dialogueSkipToggle').getAttribute('aria-pressed')==='true');
    el('dialogueSkipStatus').click();await until(()=>calls.length===2&&!el('dialogueSkipToggle').disabled);
    el('dialogueSkipToggle').click();await until(()=>el('dialogueSkipToggle').getAttribute('aria-pressed')==='false');
    return {calls,label:el('dialogueSkipToggle').textContent,note:el('dialogueSkipNote').textContent};
  })()`);
  assert.deepEqual(dialogue.calls,['dialogue_skip_toggle','dialogue_skip_status','dialogue_skip_toggle']);
  assert.equal(dialogue.label,'Dialogue skip: off');assert.match(dialogue.note,/off/);
  result.dialogue=dialogue;
  const replaySelection=await win.webContents.executeJavaScript(`(async()=>{
    const doc=document.implementation.createHTMLDocument('Replay campaign selection');doc.body.innerHTML=document.body.innerHTML;
    const el=id=>doc.getElementById(id),requests=[];
    const story=Object.keys(MsbtMissionPlaythrough).filter(n=>MsbtMissionPlaythrough[n].campaign==='story').slice(0,2);
    const dlc=Object.keys(MsbtMissionPlaythrough).find(n=>MsbtMissionPlaythrough[n].campaign!=='story');
    const rows=[...story,dlc].map((name,i)=>({name,title:'Mission '+i,state:'completed',category:i===2?'dlc':'story'}));
    const call=async(action,payload)=>{
      if(action.endsWith('_status'))return {ok:true,state:'idle'};
      if(action==='mission_preview')return {ok:true,selection_scope:payload.scope,max_batch:10,missions:payload.scope==='all'?rows:rows.filter(r=>payload.missions?.includes(r.name))};
      if(action==='mission_practice_preview'){requests.push(payload.missions);return {ok:true,mission:payload.missions[0],choices:[{index:2,title:'Replay section',save_backed_supported:true}]};}
      return {ok:true};
    };
    const until=async(test)=>{for(let i=0;i<200&&!test();i++)await new Promise(r=>setTimeout(r,5));if(!test())throw Error('Selection refresh timed out');};
    MsbtMissionPanel.bind(doc,call,()=>null);MsbtMissionPanel.showView(doc,'practice');
    await until(()=>el('missionNames').options.length===2);
    const choose=async name=>{const before=requests.length;el('missionNames').value=name;el('missionNames').dispatchEvent(new Event('change'));await until(()=>requests.length>before);await until(()=>el('missionPracticeSelect').value==='2');};
    await choose(story[0]);await choose(story[1]);
    const replaced=el('missionSelectionCount').textContent;
    el('missionCampaignFilter').value=MsbtMissionPlaythrough[dlc].campaign;el('missionCampaignFilter').dispatchEvent(new Event('change'));
    await until(()=>el('missionPracticeSelect').value==='');
    const cleared=el('missionSelectionCount').textContent;
    await choose(dlc);
    const resumed={count:el('missionSelectionCount').textContent,request:requests.at(-1),objective:el('missionPracticeSelect').value};
    MsbtMissionPanel.showView(doc,'complete');
    el('missionCampaignFilter').value='story';el('missionCampaignFilter').dispatchEvent(new Event('change'));
    el('missionNames').value=story[0];el('missionNames').dispatchEvent(new Event('change'));
    await until(()=>el('missionSelectionCount').textContent.includes('2 selected'));
    const bulk=el('missionSelectionCount').textContent;
    return {replaced,cleared,resumed,bulk,dlc};
  })()`);
  assert.match(replaySelection.replaced,/1 selected/);assert.doesNotMatch(replaySelection.replaced,/hidden/);
  assert.match(replaySelection.cleared,/0 selected/);
  assert.deepEqual(replaySelection.resumed.request,[replaySelection.dlc]);assert.equal(replaySelection.resumed.objective,'2');
  assert.match(replaySelection.bulk,/2 selected.*1 hidden/);
  result.replaySelection=replaySelection;
  const dir=path.join(__dirname,'../output/testing/mission-views');fs.mkdirSync(dir,{recursive:true});
  for(const width of [360,800,1280]){
    win.setContentSize(width,1000);
    const layout=await win.webContents.executeJavaScript(`(async()=>{
      await new Promise(r=>setTimeout(r,80));
      const panel=document.querySelector('[data-msbt-panel="boost-missions"]');
      return {overflow:panel.scrollWidth-panel.clientWidth,selectWidth:document.getElementById('missionPracticeSelect').getBoundingClientRect().width};
    })()`);
    assert(layout.overflow<=3&&layout.selectWidth>0,JSON.stringify({width,...layout}));
    fs.writeFileSync(path.join(dir,'practice-'+width+'.png'),(await win.webContents.capturePage(undefined,{stayHidden:true,stayAwake:true})).toPNG());
  }
  fs.writeFileSync(path.join(dir,'receipt.json'),JSON.stringify(result,null,2));
  console.log('PASS mission task views, checkpoint picker, finder reveal, responsive sizes and bound practice cancellation across views; all actions stubbed');
  win.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
