const {app,BrowserWindow}=require('electron');
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
  const win=new BrowserWindow({show:false,width:1360,height:960,webPreferences:{partition:'workspace-tours-'+process.pid,backgroundThrottling:false}});
  await win.loadFile(path.join(__dirname,'renderer.html'),{query:{nosplash:'1'}});
  const overlay=JSON.parse(fs.readFileSync(path.join(__dirname,'../docs/data/tutorial_copy.json'),'utf8'));
  const titles=await win.webContents.executeJavaScript('TUTORIAL_TOURS.main.map(step=>step.title)');
  assert.equal(overlay.layout,'workspace');assert.equal(overlay.layout_revision,2);
  for(const patch of overlay.tours['workspace-main'])assert.equal(titles[patch.index],patch.title);
  const result=await win.webContents.executeJavaScript(`(async()=>{
    await endWalkthrough({skipped:true,quiet:true});bridgeStatus=async()=>{};
    const actions=[];runAction=async(...args)=>{actions.push(args);return {ok:true};};
    document.getElementById('mobileAnnounceDismissBtn')?.click();
    const missing=[],invisible=[],copy=[];let checked=0;
    for(const lang of ['en','de','en-AU']){
      msbtI18n.setLanguage(lang);
      for(const [name,steps]of [...Object.entries(TUTORIAL_TOURS),...Object.entries(TAB_TUTORIALS)])for(const [index,step]of steps.entries()){
        if(step.type==='choices')continue;
        switchTab(step.tab);prepareWalkthroughTarget(step);MsbtTranslateUi.apply();
        const target=resolveWalkthroughTarget(step);checked++;
        if(!target)missing.push({lang,name,index,target:step.target||step.targetSel});
        else {const r=target.getBoundingClientRect();if(r.width<1||r.height<1)invisible.push({lang,name,index,target:step.target||step.targetSel});}
      }
    }
    const mainCopy=TUTORIAL_TOURS.main.map(s=>s.body).join(' ');
    if(/hidden from the main bar|stack Target with Essentials/.test(mainCopy))copy.push('stale workspace instructions');
    const before=TUTORIAL_TOURS.main[0].body;
    window.msbt={getTutorialCopy:async()=>({ok:true,data:{tours:{main:[{index:0,body:'STALE COPY'}]}}})};
    await applyRemoteTutorialCopy();const oldOverlayRejected=TUTORIAL_TOURS.main[0].body===before;
    const originalTarget=TUTORIAL_TOURS.main[0].targetSel;
    window.msbt.getTutorialCopy=async()=>({ok:true,data:{layout:'workspace',layout_revision:2,tours:{'workspace-main':[{index:0,body:'Compatible updated guide',targetSel:'#not-allowed'}]}}});
    await applyRemoteTutorialCopy();
    if(TUTORIAL_TOURS.main[0].body!=='Compatible updated guide'||TUTORIAL_TOURS.main[0].targetSel!==originalTarget)throw Error('Revision-2 overlay or selector allowlist failed');
    TUTORIAL_TOURS.main[0].body=before;
    msbtI18n.setLanguage('en-AU');
    await startMainTutorial({force:true});
    const first=walkthroughState.step;walkthroughNext();const next=walkthroughState.step;walkthroughBack();const back=walkthroughState.step;
    await endWalkthrough({skipped:true,quiet:true});const closed=!walkthroughState.active;
    startLayoutTutorial();const replay=walkthroughState.mode==='layout';
    await endWalkthrough({skipped:true,quiet:true});
    return {checked,missing,invisible,copy,oldOverlayRejected,first,next,back,closed,replay,actions};
  })()`);
  const dir=path.join(__dirname,'../output/testing/workspace-walkthroughs');fs.mkdirSync(dir,{recursive:true});fs.writeFileSync(path.join(dir,'receipt.json'),JSON.stringify(result,null,2));
  assert.deepEqual(result.missing,[]);assert.deepEqual(result.invisible,[]);assert.deepEqual(result.copy,[]);assert(result.oldOverlayRejected&&result.closed&&result.replay);assert.equal(result.first,0);assert.equal(result.next,1);assert.equal(result.back,0);assert.deepEqual(result.actions,[]);
  console.log('PASS '+result.checked+' translated workspace tour targets; Next/Back/Skip/replay; stale overlay blocked; zero game actions.');
  win.destroy();app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});
