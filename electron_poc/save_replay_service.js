'use strict';
const fs=require('node:fs/promises');
const path=require('node:path');
const crypto=require('node:crypto');
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const terminal=new Set(['ready','stopped','failed','restored','interrupted']);
const messages={
  await_other:'In the game picker, choose another existing character. Your original save will only be edited after it unloads.',
  await_original:'In the game picker, select your original character. The backed-up save edit is installed.',
  await_other_refresh:'The encounter needs a character refresh. Choose another existing character once more.',
  await_original_refresh:'Select your original character again to finish loading the mission state.',
  locating:'Locating and backing up the unloaded character save…',
  travel_wait:'Waiting for the mission map to finish loading…',
  station_wait:'Checking arrival at the selected nearby respawn station…',
  station_placement_wait:'Checking the corrected respawn station arrival…',
  boundary_wait:'Checking that the game read the edited objective state…',
  boundary_refresh_wait:'Checking the objective state after the character refresh…',
  placement_initial_wait:'Checking normal movement at the recorded beginning…',
  placement_final_wait:'Checking normal movement after the character refresh…',
  placement_initial_gate:'Waiting for the recorded starting area to finish loading…',
  placement_final_gate:'Waiting for the refreshed starting area to finish loading…',
  encounter_wait:'Waiting for the selected encounter to initialize…',
  track:'Restoring the selected mission on the HUD…',
  ready:'Replay ready — experimental. The selected encounter is active; normal combat and broader mission coverage remain under test.',
  uncertain:'An action result is unknown. Check status to reconcile it; it will not be resent.',
  stopped:'Replay stopped. Applied changes and the original backup are retained.',
  restored:'The pre-replay backup is restored. Load your original character through the in-game picker.',
  interrupted:'The game session changed. Automatic replay stopped; the backup is retained.'
};

function createSaveReplayService({request,helper,codec,saveRoot,storage}) {
  let job=null,loaded=false,busy=null;
  const root=path.resolve(storage),active=path.join(root,'active.json');
  const directory=()=>path.join(root,'runs',job.id);
  async function atomic(file,data) {
    await fs.mkdir(path.dirname(file),{recursive:true});
    const temp=file+'.'+crypto.randomUUID()+'.tmp';
    const handle=await fs.open(temp,'wx');
    try {await handle.writeFile(data);await handle.sync();}finally{await handle.close();}
    // Windows readers/scanners can briefly deny replacement of the journal.
    // Retry only this identical journal rename, never a save write or game call.
    for(let attempt=0;;attempt++){
      try{await fs.rename(temp,file);break;}
      catch(error){
        if(file!==active||!['EPERM','EACCES','EBUSY'].includes(error.code)||attempt>=10)throw error;
        await sleep(100);
      }
    }
  }
  async function persist(){await atomic(active,JSON.stringify(job,null,2));}
  async function load(){
    if(loaded)return;loaded=true;
    try {if((await fs.stat(active)).size>20*1024*1024)throw Error('Replay journal is too large');
      job=JSON.parse(await fs.readFile(active,'utf8'));
      if(!/^[a-f0-9]{32}$/.test(job.id))throw Error('Invalid replay journal identity');
      if(job.phase==='locating'){
        job.phase='failed';job.error='The desktop restarted during save preparation. Close this run before starting again; any verified backup is retained.';
        await persist();
      }
    }catch(error){if(error.code!=='ENOENT')throw error;}
  }
  function view(){return job?{ok:!['failed','uncertain','interrupted'].includes(job.phase),id:job.id,
    state:job.phase,message:job.error||(job.automatic&&job.phase.startsWith('await_')?'Reloading the character automatically…':null)||(job.phase==='ready'&&['bookmark','selection'].includes(job.spec?.kind)?
      (job.placementFallback?'Mission state loaded at the native spawn station; the starting waypoint could not be safely placed. ':job.spec.section.placement==='native'?'Saved mission state loaded using the game’s respawn point. ':job.spec.kind==='selection'?'Mission state loaded at the selected section’s starting waypoint. ':'Bookmarked mission state loaded at the saved point. ')+
      'Encounter behavior remains experimental.':messages[job.phase])||'Preparing save-backed replay…',
    active:!terminal.has(job.phase)||(!job.closed&&['failed','interrupted'].includes(job.phase)),backupAvailable:!!job.backupVerified,
    saveName:job.file?path.basename(job.file):null,checkpoint:job.checkpoint,mission:job.mission,
    experimental:true,backgroundLoading:!!job.automatic}: {ok:true,state:'idle',active:false,message:'No save-backed replay is running.'};}
  async function jump(phase){job.phase=phase;job.since=Date.now();job.error=null;await persist();}
  async function python(action,yaml,spec=job?.spec){
    const r=await helper({action,yaml,spec});if(!r?.ok)throw Error(r?.message||'The local save helper failed');return r;
  }
  async function native(suffix,payload={}) {
    const r=await request('mission_save_replay_'+suffix,{id:job?.id,session:job?.session,...payload});
    if(!r?.ok)throw Error(r?.message||'The game did not confirm this replay action');return r;
  }
  async function bound(){
    const r=await native('status');
    if(job.session && (r.session!==job.session||r.pid!==job.pid)){
      await jump('interrupted');throw Error(messages.interrupted);
    }
    return r;
  }
  async function effect(action,payload,key,next) {
    if(job.pending)throw Error(messages.uncertain);
    job.pending={action,key,next};await persist();
    const r=await native(action,payload);
    if(r.ok===false)throw Error(r.message||'Replay action failed');
    job.pending=null;await jump(next);return r;
  }
  async function safeFile(file){
    const base=await fs.realpath(saveRoot),actual=await fs.realpath(file);
    const relative=path.relative(base,actual);
    if(!relative||relative.startsWith('..')||path.isAbsolute(relative)||!(await fs.lstat(file)).isFile())throw Error('Save is outside the native save folder');
    return actual;
  }
  function account(file){const a=file.split(path.sep).reverse().find(s=>/^(?:\d{17}|[a-f0-9]{32})$/i.test(s));if(!a)throw Error('Save account could not be identified');return a;}
  async function decode(file){
    file=await safeFile(file);const bytes=await fs.readFile(file);
    if(bytes.length>48*1024*1024)throw Error('Save exceeds the 48 MB limit');
    const yaml=await codec('decrypt',bytes,account(file));
    if(hash(await fs.readFile(file))!==hash(bytes))throw Object.assign(Error('The save changed while reading it'),{code:'SAVE_CHANGED'});
    return {file,bytes,yaml};
  }
  async function locate(expectedGuid=job.guid){
    const candidates=[];
    async function walk(dir,depth=0){
      if(depth>4)return;
      for(const item of await fs.readdir(dir,{withFileTypes:true})){
        if(item.isSymbolicLink())continue;
        const file=path.join(dir,item.name);
        if(item.isDirectory())await walk(file,depth+1);
        else if(item.isFile()&&/^\d+\.sav$/i.test(item.name))candidates.push(file);
        if(candidates.length>256)throw Error('Too many character saves to identify safely');
      }
    }
    await walk(saveRoot);const matches=[];
    for(const file of candidates){
      let decoded;try{decoded=await decode(file);}catch{continue;}
      // Index hint only. The full tagged-YAML parser validates every candidate.
      if(!decoded.yaml.replaceAll('-','').toLowerCase().includes(expectedGuid))continue;
      const info=await python('identity',decoded.yaml);
      if(info.guid===expectedGuid)matches.push(decoded);
    }
    if(matches.length!==1)throw Error('The original character save is missing or ambiguous; no save was edited');
    return matches[0];
  }
  async function prepareAutomatic(){
    if(job.slots){await native('loader_bind',{slots:job.slots,holding_guid:job.holdingGuid});return;}
    const original=await locate();
    const candidates=(await fs.readdir(path.dirname(original.file),{withFileTypes:true}))
      .filter(e=>e.isFile()&&/^\d+\.sav$/i.test(e.name)&&e.name!==path.basename(original.file));
    const ordered=await Promise.all(candidates.map(async e=>{const file=path.join(path.dirname(original.file),e.name);return {file,mtime:(await fs.stat(file)).mtimeMs};}));
    ordered.sort((a,b)=>b.mtime-a.mtime);
    let holding;
    for(const item of ordered){
      try{
        const decoded=await decode(item.file),identity=await python('identity',decoded.yaml);
        if(identity.guid!==job.guid){holding={...item,guid:identity.guid};break;}
      }catch{}
    }
    if(!holding)throw Error('Automatic reload needs a second existing, loadable character in the same save profile. No save was edited.');
    job.slots={original:'C_'+path.basename(original.file,'.sav'),other:'C_'+path.basename(holding.file,'.sav')};
    job.holdingGuid=holding.guid;
    await persist();
    await native('loader_bind',{slots:job.slots,holding_guid:job.holdingGuid});
  }
  async function automaticSelection(role,cycle,next){
    job.autoNext=next;await persist();
    await effect('loader_refresh',{role,cycle},`loader_refresh_${role}_${cycle}`,`auto_${role}_${cycle}`);
  }
  async function inactive(){const r=await bound();if(!r.loaded||r.guid===job.guid||(job.automatic&&r.guid!==job.holdingGuid))throw Error('The expected holding character is not loaded; the original save was not written');return r;}
  async function stage(entryRefresh=false){
    await inactive();await jump('locating');const source=await locate();await inactive();
    await sleep(350);
    if(hash(await fs.readFile(source.file))!==hash(source.bytes))throw Error('Original save is still changing; nothing was edited');
    job.file=source.file;job.account=account(source.file);const sourceHash=hash(source.bytes);
    if(!entryRefresh)job.sourceHash=sourceHash;
    await fs.mkdir(directory(),{recursive:true});
    const backupName=entryRefresh?'before-entry-refresh.sav':'before.sav';
    await fs.writeFile(path.join(directory(),backupName),source.bytes,{flag:'wx'});
    if(hash(await fs.readFile(path.join(directory(),backupName)))!==sourceHash)throw Error('The original backup could not be verified');
    job.backupVerified=true;
    await persist();
    const prepared=await python('edit',source.yaml);
    const candidate=await codec('encrypt',prepared.yaml,job.account);
    if(await codec('decrypt',candidate,job.account)!==prepared.yaml)throw Error('Edited save did not round-trip; nothing was installed');
    job.candidateHash=hash(candidate);job.preservation=prepared.receipt;
    await fs.writeFile(path.join(directory(),entryRefresh?'entry-refresh-candidate.sav':'candidate.sav'),candidate,{flag:'wx'});
    const next=entryRefresh?'open_original_refresh':'open_original';
    job.pending={action:'write',key:'write',next};await persist();
    await inactive();await safeFile(job.file);
    if(hash(await fs.readFile(job.file))!==sourceHash)throw Error('Original save changed before installation');
    await atomic(job.file,candidate);
    if(hash(await fs.readFile(job.file))!==job.candidateHash)throw Error('Installed save could not be verified');
    job.pending=null;await jump(next);
  }
  async function checkDisk(entryPending=false){
    let source;
    try{source=await decode(job.file);}catch(error){
      // Windows may deny reads while the native character reload/autosave owns
      // the file. Only this read-only verification can wait; never resend edits
      // or game actions because of a filesystem lock.
      if(['EBUSY','EACCES','EPERM'].includes(error.code))error.code='SAVE_READ_BUSY';
      throw error;
    }
    const r=await python('inspect',source.yaml);
    if(r.guid!==job.guid||(!entryPending&&(r.cursor!==job.checkpoint||r.mission_status!=='Active')))throw Error('The game restored different save progress; replay was not marked ready');
    delete job.readWaitSince;
    return r;
  }
  async function reconcile(){
    const p=job.pending;if(!p)return;
    if(p.action==='write'){
      if(job.file&&hash(await fs.readFile(await safeFile(job.file)))===job.candidateHash){job.pending=null;await jump(p.next);return;}
    }else{
      const r=await bound();
      if(p.action==='begin'&&r.lease===job.id){
        job.session=r.session;job.pid=r.pid;job.guid=r.lease_data.original_guid;job.spec={...r.lease_data.spec,force_travel:true,fog_mode:job.fogMode||'leave'};
        if(job.bookmark)job.spec={...job.spec,bookmark_snapshot:job.bookmark.snapshot};
        job.pending=null;await jump('open_other');return;
      }
      const call=r.calls?.[p.key];
      if(call?.error){job.phase='uncertain';job.error=call.error+' No automatic retry was issued; stop setup before starting again.';await persist();return;}
      if(call?.state==='returned'&&call.result?.ok===false){job.pending=null;job.phase='failed';job.error=call.result.message||'The replay action was rejected';await persist();return;}
      if(call?.state==='returned'&&call.result?.ok!==false){job.pending=null;await jump(p.next);return;}
    }
    job.phase='uncertain';job.error=messages.uncertain;await persist();
  }
  async function step(){
    await load();if(!job||terminal.has(job.phase)&&job.phase!=='uncertain')return view();
    try{
      if(job.pending){await reconcile();if(job.pending)return view();}
      const s=await bound();if(!s.loaded){job.error=s.message||'Waiting for the character to load';return view();}
      job.error=null;
      if(job.automatic&&job.holdingGuid&&![job.guid,job.holdingGuid].includes(s.guid))throw Error('An unexpected character loaded; setup stopped before further save edits.');
      if(job.phase==='open_other'){if(job.automatic){await prepareAutomatic();await automaticSelection('other',0,'await_other');}else await effect('picker',{role:'other',cycle:0},'picker_other_0','await_other');}
      else if(job.phase.startsWith('auto_')){
        if(Date.now()-job.since<1500)return view();
        const [,role,cycle]=job.phase.split('_');
        await effect('loader_select',{role,cycle:Number(cycle),slot:job.slots[role]},`loader_select_${role}_${cycle}`,job.autoNext);
      }
      else if(job.phase==='await_other'&&s.guid!==job.guid)await stage();
      else if(job.phase==='open_original'){if(job.automatic)await automaticSelection('original',0,'await_original');else await effect('picker',{role:'original',cycle:0},'picker_original_0','await_original');}
      else if(job.phase==='await_original'&&s.guid===job.guid){
        // Arrival on the DLC destination can naturally complete its opening
        // travel objective before we reach the source map. Only this preliminary
        // read permits that; the one inactive restage and final checks are strict.
        // A cross-map bookmark can complete its travel objective immediately
        // when first loaded on the old map. Restage it once on the target map.
        job.bookmarkMapRestage=job.spec.kind==='bookmark'&&s.world!==job.spec.section.world.toLowerCase();
        await checkDisk(!!job.spec.section.restore_active_objectives?.length||job.bookmarkMapRestage);await jump('travel');
      }
      else if(job.phase==='travel'){
        if(s.world===job.spec.section.world.toLowerCase()&&!job.spec.force_travel)await jump('boundary_wait');
        else await effect('travel',{},'travel','travel_wait');
      }else if(job.phase==='travel_wait'&&s.world===job.spec.section.world.toLowerCase()&&s.travel_loaded!==false){
        if(job.bookmarkMapRestage&&!job.entryRestaging){job.entryRestaging=true;await jump('open_other_refresh');}
        else await jump(job.spec.section.station_location?'station_wait':'boundary_wait');
      }
      else if(job.phase==='station_wait'){
        const r=await native('station_check');
        if(r.at_station){
          // DLC travel openings lose unmaterialized objective records if loaded
          // on another map. Restage once, inactive, after native map arrival.
          if(job.spec.section.restore_active_objectives?.length&&!job.entryRestaging){
            job.entryRestaging=true;await persist();await jump('open_other_refresh');
          }else await jump('boundary_wait');
        }
        else if(job.stationCorrectionIssued)throw Error('The character did not remain near the corrected respawn station. No placement was repeated.');
        else if(r.placement_ready){job.stationCorrectionIssued=true;await persist();await effect('station_place',{},'station_place','station_placement_wait');}
        else if(Date.now()-job.since>20000)throw Error(r.message||'The game did not arrive at the selected nearby respawn station; no unsafe placement was issued.');
      }else if(job.phase==='station_placement_wait'){
        const r=await native('station_placement_status');if(r.placement_verified)await jump('station_wait');
      }
      else if(job.phase==='boundary_wait'){
        const c=await native('check');
        if(c.boundary_ready){await checkDisk();await jump(job.spec.section.placement==='native'||job.placementFallback?'track':'placement_initial_gate');}
      }else if(job.phase==='placement_initial_gate'){
        const r=await native('placement_ready');
        if(r.placement_ready)await jump('place_initial');
        else if(job.spec.kind==='selection'&&job.spec.section.placement==='waypoint'&&
          job.spec.section.native_station_fallback===true&&Date.now()-job.since>=10000){
          // Verify the station again: a character refresh can restore a
          // different arrival. Never fallback after an uncertain teleport.
          job.placementFallback=r.message||'Starting waypoint is not safely loaded';
          await jump('station_wait');
        }
      }else if(job.phase==='place_initial')await effect('place',{cycle:0},'place_0','placement_initial_wait');
      else if(job.phase==='placement_initial_wait'){
        const r=await native('placement_status',{cycle:0});
        if(r.placement_verified)await jump(job.spec.section.refresh_after_load?'refresh':'track');
      }
      else if(job.phase==='refresh')await effect('refresh',{},'refresh','open_other_refresh');
      else if(job.phase==='open_other_refresh'){if(job.automatic)await automaticSelection('other',1,'await_other_refresh');else await effect('picker',{role:'other',cycle:1},'picker_other_1','await_other_refresh');}
      else if(job.phase==='await_other_refresh'&&s.guid!==job.guid){
        if(job.entryRestaging)await stage(true);else await jump('open_original_refresh');
      }
      else if(job.phase==='open_original_refresh'){if(job.automatic)await automaticSelection('original',1,'await_original_refresh');else await effect('picker',{role:'original',cycle:1},'picker_original_1','await_original_refresh');}
      else if(job.phase==='await_original_refresh'&&s.guid===job.guid){await checkDisk();await jump('boundary_refresh_wait');}
      else if(job.phase==='boundary_refresh_wait'){
        const c=await native('check');if(c.boundary_ready)await jump(job.spec.section.placement==='native'?'track':'placement_final_gate');
      }
      else if(job.phase==='placement_final_gate'){
        const r=await native('placement_ready');if(r.placement_ready)await jump('place_final');
        else if(job.spec.kind==='selection'&&job.spec.section.placement==='waypoint'&&
          job.spec.section.native_station_fallback===true&&Date.now()-job.since>=10000){
          job.placementFallback=r.message||'Refreshed starting waypoint is not safely loaded';
          await jump('station_wait');
        }
      }
      else if(job.phase==='place_final')await effect('place',{cycle:1},'place_1','placement_final_wait');
      else if(job.phase==='placement_final_wait'){
        const r=await native('placement_status',{cycle:1});if(r.placement_verified)await jump('track');
      }
      else if(job.phase==='track'){
        // Runtime journals this RPC and returns its receipt on later polls.
        const r=await native('track');if(r.tracked)await jump('encounter_wait');
      }else if(job.phase==='encounter_wait'){
        const r=await native('check',{encounter:true});
        if(r.boundary_ready&&r.encounter_ready){await checkDisk();await native('close');job.closed=true;await jump('ready');}
      }
      if(job.automatic&&job.phase.startsWith('await_')&&s.guid!==job.guid&&s.guid!==job.holdingGuid)throw Error('An unexpected character loaded. Setup stopped; no further save edit was issued.');
      const limit= (job.automatic&&job.phase.startsWith('await_')?30000:0)||{travel_wait:120000,boundary_wait:20000,boundary_refresh_wait:20000,
        placement_initial_gate:30000,placement_final_gate:30000,
        placement_initial_wait:12000,placement_final_wait:12000,station_placement_wait:12000,track:12000,encounter_wait:180000}[job.phase];
      if(limit&&Date.now()-job.since>limit)throw Error('Replay preparation did not settle; no action was repeated. Your backup is retained.');
      return view();
    }catch(error){
      if(['SAVE_CHANGED','SAVE_READ_BUSY'].includes(error.code)&&!job.pending&&['await_original','boundary_wait','await_original_refresh','encounter_wait'].includes(job.phase)){
        job.readWaitSince ||= Date.now();
        if(Date.now()-job.readWaitSince<10000){job.error='Waiting for the game autosave to settle…';await persist();return view();}
      }
      if(job.phase!=='interrupted'){job.phase=job.pending?'uncertain':'failed';job.error=error.message;await persist();}
      return view();
    }
  }
  async function start(payload){
    await load();if(job&&(!terminal.has(job.phase)||!job.closed))throw Error('An earlier replay needs inspection or closure');
    if(payload.acknowledge_shared_progress!==true)throw Error('Acknowledge replay changes first');
    const fogMode=payload.fog_mode??'leave';
    if(!['leave','clear','restore'].includes(fogMode))throw Error('Choose leave, clear or restore for map fog');
    job={id:crypto.randomUUID().replaceAll('-',''),mission:payload.mission,checkpoint:payload.checkpoint,phase:'starting',since:Date.now(),bookmark:payload.bookmark,automatic:payload.automatic===true,fogMode};
    job.pending={action:'begin',key:'begin',next:'open_other'};await persist();
    try {const r=await native('begin',{mission:payload.mission,checkpoint:payload.checkpoint,acknowledge_shared_progress:true,bookmark_spec:payload.bookmark?.spec});
      job.session=r.session;job.pid=r.pid;job.guid=r.guid;job.spec=payload.bookmark?{...r.spec,bookmark_snapshot:payload.bookmark.snapshot,fog_mode:fogMode}:{...r.spec,force_travel:true,fog_mode:fogMode};job.pending=null;await jump('open_other');return await step();
    }catch(error){job.phase='uncertain';job.error=error.message;await persist();return view();}
  }
  async function release(){
    try{if(job.session)await native('close');}catch{}
    const r=await native('status');if(r.lease===job.id)throw Error('Replay controls are still held; check progress before closing again');
    job.closed=true;
  }
  async function stop(){await load();if(!job)return view();await release();
    job.pending=null;await jump('stopped');return view();}
  async function restore(){
    await load();if(!job?.sourceHash)throw Error('There is no pre-replay backup');
    const s=await native('restore_guard');if(!s.loaded||s.guid===job.guid)throw Error('Choose another existing character before restoring the pre-replay save');
    if(s.lease&&s.lease!==job.id)throw Error('Another replay owns the controls');
    const source=await decode(job.file),info=await python('identity',source.yaml);
    const backup=await fs.readFile(path.join(directory(),'before.sav'));
    if(info.guid!==job.guid||hash(backup)!==job.sourceHash)throw Error('Backup or target identity differs; no restore issued');
    const b=await python('identity',await codec('decrypt',backup,job.account));if(b.guid!==job.guid)throw Error('Backup character differs');
    const current=hash(source.bytes);const fresh=await native('restore_guard');
    if(!fresh.loaded||fresh.guid===job.guid||fresh.session!==s.session||fresh.pid!==s.pid)throw Error('Character changed before restore');
    if(hash(await fs.readFile(await safeFile(job.file)))!==current)throw Error('Save changed before restore');
    await fs.writeFile(path.join(directory(),'before-restore-'+Date.now()+'.sav'),source.bytes,{flag:'wx'});
    await atomic(job.file,backup);if(hash(await fs.readFile(job.file))!==job.sourceHash)throw Error('Restore could not be verified');
    await release();job.pending=null;await jump('restored');return view();
  }
  const bookmarkDirectory=path.join(root,'bookmarks');
  async function readBookmark(id){
    if(!/^[a-f0-9]{32}$/.test(id||''))throw Error('Choose a saved bookmark');
    const file=path.join(bookmarkDirectory,id+'.json');
    if((await fs.stat(file)).size>8*1024*1024)throw Error('Bookmark is too large');
    const entry=JSON.parse(await fs.readFile(file,'utf8'));
    if(entry.id!==id||entry.spec?.kind!=='bookmark'||hash(Buffer.from(entry.snapshot))!==entry.spec.snapshot_sha256)throw Error('Bookmark contents differ; no replay started');
    return entry;
  }
  async function bookmarks(){
    await fs.mkdir(bookmarkDirectory,{recursive:true});const entries=[];
    for(const file of await fs.readdir(bookmarkDirectory)){
      if(!/^[a-f0-9]{32}\.json$/.test(file))continue;
      const b=await readBookmark(file.slice(0,-5));entries.push({id:b.id,name:b.name,mission:b.spec.title,world:b.spec.section.world,created:b.created,exactLocation:b.spec.section.placement==='exact'});
    }
    return {ok:true,bookmarks:entries.sort((a,b)=>b.created.localeCompare(a.created))};
  }
  async function saveBookmark(payload){
    await load();if(job&&(!terminal.has(job.phase)||!job.closed))throw Error('Finish or stop replay setup before bookmarking');
    const name=String(payload.name||'').trim();if(!name||name.length>80)throw Error('Name this bookmark (up to 80 characters)');
    const capture=await native('capture'),source=await locate(capture.guid);
    const result=await python('bookmark_capture',source.yaml,capture.spec);
    const fresh=await native('capture');
    const section=capture.spec.section,latest=fresh.spec.section;
    const positionChanged=section.placement!=='native'&&(!section.location||!latest.location||Math.hypot(...['x','y','z'].map(k=>latest.location[k]-section.location[k]))>10);
    if(fresh.session!==capture.session||fresh.pid!==capture.pid||fresh.guid!==capture.guid||fresh.spec.mission!==capture.spec.mission||JSON.stringify(latest.initial_objectives)!==JSON.stringify(section.initial_objectives)||latest.checkpoint!==section.checkpoint||latest.world!==section.world||latest.placement!==section.placement||positionChanged)throw Error('The character or mission changed during capture; bookmark again');
    if(hash(await fs.readFile(source.file))!==hash(source.bytes))throw Error('Autosave changed during capture; wait for it to finish and bookmark again');
    const id=crypto.randomUUID().replaceAll('-','');
    const contents=JSON.stringify({id,name,created:new Date().toISOString(),spec:result.spec,snapshot:result.snapshot},null,2);
    if(Buffer.byteLength(contents)>8*1024*1024)throw Error('Bookmark exceeds the supported size; no bookmark saved');
    await atomic(path.join(bookmarkDirectory,id+'.json'),contents);
    return {...await bookmarks(),message:section.placement==='exact'?
      'Bookmark saved with your exact position and captured mission/world state. Current equipment and levels are kept when replaying.':
      'Bookmark saved with its mission/world state and native spawn station. Update the game SDK to capture exact positions.'};
  }
  async function dispatch(action,payload={}){
    if(action==='status'){await load();return view();}
    if(busy){if(action==='advance')return busy;await busy;return dispatch(action,payload);}
    const run=(async()=>{try{
      if(action==='start')return await start(payload);
      if(action==='advance')return await step();
      if(action==='stop')return await stop();
      if(action==='restore')return await restore();
      if(action==='bookmark_list')return await bookmarks();
      if(action==='bookmark_save')return await saveBookmark(payload);
      if(action==='bookmark_start'){
        const bookmark=await readBookmark(payload.id);
        return await start({mission:bookmark.spec.mission,checkpoint:bookmark.spec.section.checkpoint,
          acknowledge_shared_progress:payload.acknowledge_shared_progress,automatic:payload.automatic,fog_mode:payload.fog_mode,bookmark});
      }
      throw Error('Unsupported replay operation');
    }catch(error){return {...view(),ok:false,message:error.message};}})();
    busy=run;try{return await run;}finally{if(busy===run)busy=null;}
  }
  return {dispatch};
}
module.exports={createSaveReplayService};
