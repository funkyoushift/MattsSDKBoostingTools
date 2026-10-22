(function(root){
  'use strict';
  function bind(doc,{api,selection,legacyUpdate}){
    const el=id=>doc.getElementById(id);
    if(!el('missionReplayMethod'))return null;
    let status={state:'idle',active:false},pending=false;
    const saveMode=()=>el('missionReplayMethod').value==='save';
    const fogMode=()=>el('missionReplayFog')?.value||'leave';
    function update(){
      const selected=selection();
      if(el('missionReplayLock')){
        el('missionReplayLock').hidden=!status.active;
        el('missionReplayLockMessage').textContent=status.active?
          `Save-backed replay setup is ${status.state||'open'}. Mission completion and Full game are paused until you stop this setup. Any verified pre-replay backup is retained.`:'';
        el('missionReplayLockStop').disabled=pending||!status.active;
      }
      el('missionSaveReplayControls').hidden=!saveMode();
      if(saveMode()){
        el('missionPracticeBtn').textContent='Start save-backed replay';
        el('missionPracticeBtn').disabled=pending||status.active||selected.busy||selected.refreshing||!selected.ack||!selected.supported||typeof api!=='function';
        el('missionPracticeSelect').disabled=pending||status.active||selected.busy||selected.refreshing;
        el('missionPracticeStop').hidden=true;
        el('missionPracticeStatus').hidden=true;
        el('missionPracticeNote').textContent=selected.supported?
          'Solo lobby only; visitors must leave before replay. Requires a second existing character. Reloads the selected mission and map, then uses its starting waypoint or native spawn station. Generated encounters remain experimental.':
          !selected.mission?'Choose one mission above, then its beginning or a main objective. Replay requires a solo lobby and a second existing character.':
          'This starting point has no resolved native map/station or requires DLC access. You can also save a mission-state bookmark while playing a readable mission.';
        if(status.active&&['failed','uncertain','interrupted'].includes(status.state))el('missionPracticeNote').textContent=
          (status.message||'Replay needs attention.')+' Use Stop setup below to release this run before starting another. Your backup is retained.';
      }else{el('missionPracticeStop').hidden=false;el('missionPracticeStatus').hidden=false;}
      const previous=status.state==='ready'&&(status.checkpoint!==selected.checkpoint||status.mission!==selected.mission);
      el('missionSaveReplayOutput').textContent=(previous?'Previous replay setup: ':'')+(status.message||'No save-backed replay is running.');
      el('missionSaveReplayStop').disabled=pending||!status.active;
      el('missionSaveReplayBackup').disabled=!status.backupAvailable;
      el('missionSaveReplayRestore').disabled=pending||!status.backupAvailable||status.active;
      el('missionSaveReplayPicker').disabled=pending;
      el('missionReplayMethod').disabled=pending||status.active;
      if(el('missionReplayFog'))el('missionReplayFog').disabled=pending||status.active;
      if(el('missionReplayFogOptions'))el('missionReplayFogOptions').hidden=!saveMode();
      if(el('missionBookmarkSave')){
        el('missionBookmarkSave').disabled=pending||status.active||typeof api!=='function';
        el('missionBookmarkReplay').disabled=pending||status.active||!selected.ack||!el('missionBookmarkSelect').value;
      }
      if(status.active)for(const id of ['missionRunBtn','missionReopenBtn','missionObjectiveBtn','missionResetAllBtn','missionRestartLastBtn','missionReplayObjectiveBtn','fullProgressStart'])if(el(id))el(id).disabled=true;
    }
    async function run(action,payload){
      if(typeof api!=='function'){status={ok:false,message:'This desktop build does not support save-backed replay.'};update();return;}
      const wasActive=!!status.active;
      pending=true;update();
      try{
        const result=await api(action,payload||{});
        if(['start','advance','status','stop','restore'].includes(action))status=result;
        else if(!result?.ok)status={...status,message:result?.message||'The action was not confirmed.'};
      }catch(error){status={...status,message:`Result unknown: ${error.message}. Check progress before repeating.`};}
      finally{pending=false;if(wasActive!==!!status.active)legacyUpdate();else update();}
    }
    async function start(){const s=selection();if(!s.supported||!s.ack||status.active||pending)return;
      await run('start',{mission:s.mission,checkpoint:s.checkpoint,acknowledge_shared_progress:true,automatic:true,fog_mode:fogMode()});}
    el('missionSaveReplayCheck').addEventListener('click',()=>run('advance'));
    el('missionSaveReplayStop').addEventListener('click',()=>run('stop'));
    el('missionReplayLockStop')?.addEventListener('click',()=>run('stop'));
    el('missionSaveReplayPicker').addEventListener('click',()=>run('picker'));
    el('missionSaveReplayBackup').addEventListener('click',()=>run('backup'));
    el('missionSaveReplayRestore').addEventListener('click',()=>run('restore'));
    async function bookmark(action){
      if(pending||typeof api!=='function')return;
      const wasActive=!!status.active;
      pending=true;update();
      try{
        const r=await api(action,{id:el('missionBookmarkSelect').value,name:el('missionBookmarkName').value,acknowledge_shared_progress:!!selection().ack,automatic:true,...(action==='bookmark_start'?{fog_mode:fogMode()}: {})});
        if(r.bookmarks){
          const select=el('missionBookmarkSelect'),previous=select.value;select.replaceChildren();
          for(const b of r.bookmarks){const option=doc.createElement('option');option.value=b.id;option.textContent=b.name+' — '+b.mission+' ('+b.world+'; '+(b.exactLocation?'exact position':'spawn station')+')';select.append(option);}
          if([...select.options].some(o=>o.value===previous))select.value=previous;
        }
        el('missionBookmarkOutput').textContent=r.message||(r.ok?'Bookmarks refreshed.':'Bookmark action failed.');
        if(action==='bookmark_start')status=r;
      }catch(error){el('missionBookmarkOutput').textContent=error.message;}
      finally{pending=false;if(wasActive!==!!status.active)legacyUpdate();else update();}
    }
    el('missionBookmarkSave')?.addEventListener('click',()=>bookmark('bookmark_save'));
    el('missionBookmarkRefresh')?.addEventListener('click',()=>bookmark('bookmark_list'));
    el('missionBookmarkReplay')?.addEventListener('click',()=>bookmark('bookmark_start'));
    el('missionBookmarkSelect')?.addEventListener('change',update);
    el('missionReplayMethod').addEventListener('change',legacyUpdate);
    const timer=root.setInterval(()=>{if(!pending&&!doc.hidden)void run('status');},1500);
    root.addEventListener('unload',()=>root.clearInterval(timer),{once:true});
    void run('status').then(()=>{
      if(el('missionBookmarkSelect')&&typeof api==='function')return bookmark('bookmark_list');
    });
    return {update,start,active:()=>!!status.active,saveMode};
  }
  root.MsbtSaveReplayPanel={bind};
  if(typeof module!=='undefined')module.exports=root.MsbtSaveReplayPanel;
})(typeof window==='undefined'?globalThis:window);
