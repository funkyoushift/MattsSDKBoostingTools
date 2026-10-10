"use strict";
const {app,BrowserWindow}=require('electron');
const assert=require('node:assert/strict'),path=require('node:path');
app.whenReady().then(async()=>{
  const win=new BrowserWindow({show:false,width:1100,height:950,webPreferences:{sandbox:false,partition:`clarity-${process.pid}`}});
  for(const mode of ['workspace','classic']) {
    await win.loadFile(path.join(__dirname,'renderer.html'),{query:{nosplash:'1',workspace:mode}});
    const result=await win.webContents.executeJavaScript(`(async()=>{
      bridgeStatus=async()=>{};
      const calls=[];runAction=async(...args)=>{calls.push(args);return {ok:true,data:{ok:true,message:'Test only'}};};
      syncFarmingLabStatus({});
      const offline=Object.keys(FARMING_LAB_FEATURES).every(id=>{
        const row=document.getElementById('farmingLab_'+id);
        return row&&[...row.querySelectorAll('button')].every(b=>b.disabled)&&row.textContent.includes('Connect to the game');
      });
      syncFarmingLabStatus({farming_lab:{features:{god_mode:{label:'God Mode',enabled:false,error:''}}}});
      const partial=!document.querySelector('#farmingLab_god_mode button').disabled&&document.querySelector('#farmingLab_infinite_ammo button').disabled;
      const beforeShortcuts=calls.length;
      const shortcuts=[...document.querySelectorAll('[aria-label="Gameplay control shortcuts"] [data-open-panel]')].every(button=>{
        button.click();return document.querySelector('[data-msbt-panel="'+button.dataset.openPanel+'"]').getBoundingClientRect().height>0;
      });
      const safeShortcuts=calls.length===beforeShortcuts;
      const features=Object.fromEntries(Object.keys(FARMING_LAB_FEATURES).map(id=>[id,{label:'Old SDK label',enabled:false,error:''}]));
      syncFarmingLabStatus({farming_lab:{features}});
      const names=Object.entries(FARMING_LAB_FEATURES).every(([id,v])=>document.querySelector('#farmingLab_'+id+' strong').textContent===v.label);
      const original={catalog:{devperk_5:{basic:'Infinite Ammo',assignable:true},devperk_6:{basic:'Demigod'},farming_instant_reload_on:{basic:'Farming: Instant Reload On'}},layout:{custom:'unchanged'}};
      const normalized=normalizeQuickMenuLabels(original);
      const menuLabels=normalized.catalog.devperk_5.basic.includes('state unverified')&&normalized.catalog.devperk_6.basic.includes('state unverified')&&normalized.catalog.farming_instant_reload_on.basic==='Fast Reload On';
      const menuIdentity=original.catalog.devperk_5.basic==='Infinite Ammo'&&normalized.catalog.devperk_5.assignable&&normalized.layout===original.layout;
      state.devperkToggles={'5':true,'6':false};updateDevperkToggleButtons();
      const gameToggles=[...document.querySelectorAll('[data-devperk-toggle]')].map(b=>({text:b.textContent,advanced:!!b.closest('details'),group:b.closest('[data-msbt-panel]').dataset.msbtPanel}));
      const duplicateActions=[...document.querySelectorAll('[data-action]')].map(b=>b.dataset.action).filter((id,i,ids)=>ids.indexOf(id)!==i);
      document.getElementById('combatSticky').checked=true;
      const sticky=combatPayload().sticky;
      const inactiveSticky=document.getElementById('combatSticky').hidden&&document.getElementById('combatSticky').disabled;
      await runCombatAction('combat_tuning_reapply');
      const numericRequest=calls.at(-1);
      const oldAlias=collectAppFinderEntries().some(e=>(e.aliases||[]).includes('Turn All Farming Controls Off'));
      const featureAlias=collectAppFinderEntries().some(e=>e.id==='feature:instant_reload'&&e.aliases.includes('instant reload'));
      const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);const duplicateIds=ids.filter((id,i)=>ids.indexOf(id)!==i);
      let targetHidden=true,targetShown=true;
      if(window.MsbtWorkspace?.enabled){
        window.MsbtWorkspace.open('combat-vehicle','combat');
        targetHidden=document.querySelector('[data-msbt-panel="dev-target"]').getBoundingClientRect().height===0;
        window.MsbtWorkspace.open('combat-vehicle','chaos');
        targetShown=document.querySelector('[data-msbt-panel="dev-target"]').getBoundingClientRect().height>0;
      }
      window.switchTab('inventory');const before=calls.length;
      document.getElementById('invCharacterToolsBtn').click();await new Promise(r=>setTimeout(r,50));
      const toolsVisible=document.querySelector('[data-msbt-panel="boost-late-join"]').getBoundingClientRect().height>0;
      return {offline,partial,shortcuts,safeShortcuts,names,menuLabels,menuIdentity,gameToggles,duplicateActions,duplicateIds,sticky,inactiveSticky,numericAction:numericRequest[0],targetHidden,targetShown,toolsVisible,navigationSentAction:calls.length!==before,oldAlias,featureAlias};
    })()`);
    assert(result.names&&result.oldAlias&&result.featureAlias,JSON.stringify(result));
    assert(result.offline&&result.partial&&result.shortcuts&&result.safeShortcuts,JSON.stringify(result));
    assert(result.menuLabels&&result.menuIdentity);
    assert.deepEqual(result.duplicateActions,[]);assert.deepEqual(result.duplicateIds,[]);
    assert(result.gameToggles.every(b=>b.advanced&&b.text.includes('state unverified')));
    assert.deepEqual(result.gameToggles.map(b=>b.group),['boost-weapon-tests','combat-skill-tests']);
    assert(!result.sticky&&result.inactiveSticky);assert.equal(result.numericAction,'combat_tuning_reapply');
    assert(result.targetHidden&&result.targetShown&&result.toolsVisible&&!result.navigationSentAction,JSON.stringify(result));
    console.log('PASS '+mode+': canonical actions, distinct game toggles, honest tuning labels, target visibility, search aliases and safe character-tools navigation');
  }
  win.destroy();app.exit(0);
}).catch(e=>{console.error(e);app.exit(1);});
