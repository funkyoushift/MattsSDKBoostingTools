"use strict";
const assert=require("node:assert/strict"),path=require("node:path");
const {app,BrowserWindow}=require("electron");
const runtimeRoot=process.env.MSBT_CARD_PACKAGE_ROOT
  ? path.resolve(process.env.MSBT_CARD_PACKAGE_ROOT,"resources/app.asar") : __dirname;
app.whenReady().then(async()=>{
  const win=new BrowserWindow({show:false,webPreferences:{sandbox:true,partition:`roster-refresh-${process.pid}`,backgroundThrottling:false}});
  try {
    await win.loadFile(path.join(runtimeRoot,"renderer.html"),{query:{nosplash:"1"}});
    const result=await win.webContents.executeJavaScript(`(async()=>{
      const check=(ok,message)=>{if(!ok)throw new Error(message);};
      const selects=[els.targetSelect,els.boostSerialTargetSelect,els.devTargetSelect,els.bookmarkTargetSelect,els.bl4TargetSelect,els.movementTargetSelect,els.invTargetSelect,els.invGiveTargetSelect].filter(Boolean);
      document.querySelectorAll('dialog[open]').forEach(dialog=>dialog.close());
      document.body.replaceChildren(els.bl4SearchInput,els.bl4RarityFilter,...selects);
      state.bridgeFingerprints={};state.pendingTargetValue='';state.scopedRunActive=false;state.movementAutoApplyOnStart=false;
      const host={index:0,name:'Host'},guest={index:1,name:'Guest'},joiner={index:2,name:'Joined'};
      const status=(players,selected=host)=>({ok:true,data:{ok:true,snapshot_ready:true,players,host_player_index:0,selected_player:selected?.name || '',selected_player_index:selected?.index ?? null}});
      const apply=s=>applyBridgeStatusResult(s,{quiet:true});
      const roster=select=>[...select.options].map(o=>o.value);
      apply(status([host]));
      const hostOptions=selects.map(select=>select.options[1]);
      els.bl4SearchInput.value='Search stays here';els.bl4SearchInput.focus();els.bl4SearchInput.setSelectionRange(3,8);
      apply(status([host,guest]));
      check(selects.every(select=>JSON.stringify(roster(select))===JSON.stringify(['','0|Host','1|Guest'])),'join while Search focused was skipped');
      check(document.activeElement===els.bl4SearchInput && els.bl4SearchInput.selectionStart===3 && els.bl4SearchInput.selectionEnd===8,'roster update disturbed Search caret');
      check(selects.every((select,i)=>select.options[1]===hostOptions[i]),'unchanged player options were replaced');
      // An unchanged snapshot must not hide a deferred roster update or churn options.
      let mutations=0;const observer=new MutationObserver(rows=>{mutations+=rows.length;});
      selects.forEach(select=>observer.observe(select,{childList:true,subtree:true}));
      apply(status([host,guest]));await Promise.resolve();check(mutations===0,'unchanged roster rewrote option nodes');
      observer.disconnect();
      els.bl4RarityFilter.focus();apply(status([host,guest,joiner]));
      check(selects.every(select=>select.options.length===4),'join while filter focused was skipped');
      check(document.activeElement===els.bl4RarityFilter,'filter focus stolen');
      els.bl4SearchInput.focus();els.invTargetSelect.value='1|Guest';els.invGiveTargetSelect.value='2|Joined';state.invGiveTarget='2|Joined';
      const movedGuest={index:2,name:'Guest'},movedJoiner={index:1,name:'Joined'};
      apply(status([host,movedJoiner,movedGuest]));
      check(els.invTargetSelect.value==='2|Guest' && els.invGiveTargetSelect.value==='1|Joined','independent inventory targets did not follow names across index changes');
      apply(status([host,movedJoiner]));
      check(els.invTargetSelect.value==='', 'departed inventory target became another player');
      check(selects.every(select=>!roster(select).some(value=>value.endsWith('|Guest'))),'departed player remains in a dropdown');
      // A focused named-player dropdown holds a valid choice, then synchronizes
      // after focus leaves even when the following snapshot is identical.
      els.targetSelect.focus();els.targetSelect.value='0|Host';apply(status([host,movedJoiner],movedJoiner));
      check(els.targetSelect.value==='0|Host' && state.playerSelectSyncPending,'focused choice was reset or deferred sync was lost');
      els.bl4SearchInput.focus();apply(status([host,movedJoiner],movedJoiner));
      check(els.targetSelect.value==='1|Joined' && !state.playerSelectSyncPending,'identical next poll did not apply deferred selection');
      state.pendingTargetValue='0|Host';state.selectedTarget='0|Host';els.targetSelect.value='0|Host';apply(status([host,movedJoiner,guest],movedJoiner));
      check(state.selectedTarget==='0|Host' && els.targetSelect.value==='0|Host','status snapped an in-flight local target backward');
      state.pendingTargetValue='';
      // Exercise the real periodic-poll path without the live game or writes.
      const requests=[];window.msbt={bridgeRequest:async req=>{requests.push(req);throw new Error('Connection refused');}};
      await runBridgeStatusPoll();clearTimeout(state.bridgeStatusPollTimer);state.bridgeStatusPollTimer=null;
      check(!state.bridgeOnline && selects.every(select=>roster(select).join('')===''),'connection error left stale players visible');
      check(selects.every(select=>select.options[0].textContent==='No players loaded'),'offline dropdown label stale');
      window.msbt.bridgeRequest=async req=>{requests.push(req);return status([host,guest]);};
      await runBridgeStatusPoll();clearTimeout(state.bridgeStatusPollTimer);state.bridgeStatusPollTimer=null;
      check(state.bridgeOnline && selects.every(select=>roster(select).includes('1|Guest')),'reconnect did not refresh roster');
      apply(status([]));check(selects.every(select=>select.options.length===1 && !select.value),'empty session retained players');
      check(requests.every(req=>req.method==='GET' && req.path==='/status'),'roster polling issued a gameplay mutation');
      return {dropdowns:selects.length,unchangedRosterMutations:mutations,polls:requests.length};
    })()`);
    assert.equal(result.dropdowns,7);assert.equal(result.unchangedRosterMutations,0);assert.equal(result.polls,2);
    console.log("PASS player roster: join/leave/reindex during Search/filter focus, stable options/caret, independent inventory targets, deferred selection, offline/reconnect periodic polling",JSON.stringify(result));
  } finally {win.destroy();}
  app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
