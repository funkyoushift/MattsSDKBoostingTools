'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs/promises'),path=require('node:path'),os=require('node:os');
const crypto=require('node:crypto');
const {createSaveReplayService}=require('./save_replay_service');

async function fixture(t,{refresh=false,snapshotPadding=0,nativeBookmark=false,automatic=false,accountId='12345678901234567',encrypted=false,waypoint=false}={}){
  const base=await fs.mkdtemp(path.join(os.tmpdir(),'msbt-replay-test-'));
  t.after(async()=>{const full=await fs.realpath(base);assert.equal(path.dirname(full),await fs.realpath(os.tmpdir()));assert(path.basename(full).startsWith('msbt-replay-test-'));await fs.rm(full,{recursive:true,force:true});});
  const saveRoot=path.join(base,'saves'),storage=path.join(base,'journal');
  const account=path.join(saveRoot,accountId,'Profiles','client');await fs.mkdir(account,{recursive:true});
  const realCodec=async(command,value,id=accountId)=>{
    const payload=command==='encrypt'?{command,steamid:id,yaml_content:String(value)}:{command,steamid:id,sav_data:Buffer.from(value).toString('base64')};
    const call=require('node:child_process').spawnSync(process.execPath,[path.resolve(__dirname,'../external_app/v22_parts_codes_fixed/matt_editor_blcrypt.js')],{input:JSON.stringify(payload),encoding:'utf8'});
    assert.equal(call.status,0);const result=JSON.parse(call.stdout);assert.equal(result.success,true,result.error);
    return command==='encrypt'?Buffer.from(result.sav_data,'base64'):result.yaml_content;
  };
  const file=path.join(account,'17.sav');
  const guid='a'.repeat(32),other='c'.repeat(32);
  const source=Buffer.from(JSON.stringify({guid,name:'Synthetic character',progress:33,inventory:['@UCase','@UCase'],level:70,currency:91}));
  await fs.writeFile(file,encrypted?await realCodec('encrypt',source):source);
  const section={checkpoint:28,world:'World_P',station:'World_P.Station',refresh_after_load:refresh,location:{x:10,y:20,z:30},initial_objectives:['encounter']};
  const spec={section};
  if(waypoint){spec.kind='selection';section.placement='waypoint';section.native_station_fallback=true;}
  const r={guid,world:'world_p',session:'session-one',pid:123,lease:null,calls:{},placements:0,
    lostReturn:false,unknown:false,switchDuringEdit:false};
  if(automatic){const text=JSON.stringify({guid:other,name:'Holding character',progress:0,inventory:[],level:1,currency:0});await fs.writeFile(path.join(account,'15.sav'),encrypted?await realCodec('encrypt',text):Buffer.from(text));}
  r.automaticCalls=[];
  const request=async(action,payload={})=>{
    const op=action.replace('mission_save_replay_','');
    if(op==='capture'){
      const captured={...section};if(nativeBookmark){captured.placement='native';delete captured.location;}
      return {ok:true,guid:r.guid,session:r.session,pid:r.pid,spec:{kind:'bookmark',guid:r.guid,mission:'Mission_Test',title:'Synthetic mission',section:captured}};
    }
    if(op==='status'||op==='restore_guard')return {ok:true,loaded:true,guid:r.guid,world:r.world,session:r.session,pid:r.pid,lease:r.lease,calls:r.calls,lease_data:{original_guid:guid,spec}};
    if(op==='begin'){if(r.lease)return {ok:false,message:'Lease already held'};r.lease=payload.id;return {ok:true,guid,session:r.session,pid:r.pid,spec:payload.bookmark_spec?{...payload.bookmark_spec,force_travel:true}:spec};}
    if(payload.session!==r.session||payload.id!==r.lease)return {ok:false,message:'Session differs'};
    if(op==='close'){r.lease=null;return {ok:true};}
    if(op==='loader_bind'){r.binding=payload;return {ok:true};}
    if(op==='loader_refresh'){
      const key=`loader_refresh_${payload.role}_${payload.cycle}`;
      r.calls[key]={state:'returned',result:{ok:true}};
      if(r.loseRefresh){r.loseRefresh=false;throw Error('Refresh return lost');}
      return {ok:true};
    }
    if(op==='loader_select'){
      r.automaticCalls.push(payload.slot);
      r.guid=r.wrongAutomaticTarget?'b'.repeat(32):(payload.role==='other'?other:guid);
      r.calls[`loader_select_${payload.role}_${payload.cycle}`]={state:'returned',result:{ok:true}};
      return {ok:true};
    }
    if(op==='check')return {ok:true,boundary_ready:r.boundaryReady!==false,encounter_ready:true};
    if(op==='placement_status')return {ok:true,placement_verified:true};
    if(op==='placement_ready')return {ok:true,placement_ready:r.placementReady!==false};
    if(op==='track'){r.trackRequests=(r.trackRequests||0)+1;return {ok:true,tracked:true};}
    const key=op==='picker'?`picker_${payload.role}_${payload.cycle}`:op==='place'?`place_${payload.cycle}`:op;
    if(op==='place'){
      r.placements++;
      r.calls[key]={state:r.unknown?'issued':'returned',result:{ok:true}};
      if(r.lostReturn||r.unknown){r.lostReturn=false;throw Error('Connection lost after request');}
    }else r.calls[key]={state:'returned',result:{ok:true}};
    if(op==='travel')r.world=section.world.toLowerCase();
    return {ok:true};
  };
  const helper=async p=>{
    const data=JSON.parse(p.yaml);
    if(p.action==='identity')return {ok:true,guid:data.guid,name:data.name};
    if(p.action==='bookmark_capture'){
      const snapshot=JSON.stringify({missions:{progress:data.progress,padding:'x'.repeat(snapshotPadding)}});
      return {ok:true,spec:{...p.spec,snapshot_sha256:crypto.createHash('sha256').update(snapshot).digest('hex')},snapshot};
    }
    if(p.action==='edit'){
      if(r.switchDuringEdit)r.guid=guid;
      return {ok:true,yaml:JSON.stringify({...data,progress:28}),receipt:{preserved_unowned_data:true}};
    }
    return {ok:true,guid:data.guid,cursor:data.progress,mission_status:'Active'};
  };
  const codec=async(command,value,id)=>{
    if(command==='decrypt'&&r.autosaveDuringRead>0){r.autosaveDuringRead--;await fs.appendFile(file,' ');}
    if(encrypted)return realCodec(command,value,id);
    return command==='decrypt'?Buffer.from(value).toString():Buffer.from(value);
  };
  const make=()=>createSaveReplayService({request,helper,codec,saveRoot,storage});
  return {service:make(),make,r,guid,other,file,source,storage,spec,realCodec};
}
async function start(f){return f.service.dispatch('start',{mission:'Mission_Main_Shatteredlands3',checkpoint:28,acknowledge_shared_progress:true});}
async function reach(f,state){
  let result;
  for(let i=0;i<15;i++){result=await f.service.dispatch('advance');if(result.state===state)return result;}
  assert.fail('Did not reach '+state+': '+JSON.stringify(result));
}
async function install(f){await start(f);f.r.guid=f.other;await reach(f,'await_original');}

test('never edits the loaded character; backs up and preserves data when inactive',async t=>{
  const f=await fixture(t);const initial=await start(f);assert.equal(initial.state,'await_other');
  await f.service.dispatch('advance');assert.deepEqual(await fs.readFile(f.file),f.source);
  f.r.guid=f.other;const installed=await reach(f,'await_original');assert.equal(installed.backupAvailable,true);
  const after=JSON.parse(await fs.readFile(f.file,'utf8')),before=JSON.parse(f.source);
  assert.deepEqual(after.inventory,before.inventory);assert.equal(after.currency,before.currency);assert.equal(after.level,70);assert.equal(after.progress,28);
  f.r.guid=f.guid;const finished=await reach(f,'ready');assert.equal(finished.active,false);assert.equal(f.r.placements,1);assert.equal(f.r.lease,null);
});
test('character reselected during preparation blocks replacement',async t=>{
  const f=await fixture(t);await start(f);f.r.guid=f.other;f.r.switchDuringEdit=true;
  const result=await f.service.dispatch('advance');assert.equal(result.state,'uncertain');assert.deepEqual(await fs.readFile(f.file),f.source);
});
test('returned receipt reconciles a disconnect without repeating placement',async t=>{
  const f=await fixture(t);await install(f);f.r.guid=f.guid;f.r.lostReturn=true;
  await reach(f,'uncertain');assert.equal(f.r.placements,1);
  await reach(f,'ready');assert.equal(f.r.placements,1);
});
test('issued-only receipt never retries an uncertain placement',async t=>{
  const f=await fixture(t);await install(f);f.r.guid=f.guid;f.r.unknown=true;
  await reach(f,'uncertain');await f.service.dispatch('advance');await f.service.dispatch('advance');assert.equal(f.r.placements,1);
  const stopped=await f.service.dispatch('stop');assert.equal(stopped.state,'stopped');assert.equal(stopped.active,false);
});
test('session change stops automatic work and retains the backup',async t=>{
  const f=await fixture(t);await install(f);const candidate=await fs.readFile(f.file);
  f.r.session='new-session';f.r.pid=456;f.r.lease=null;
  const result=await f.service.dispatch('advance');assert.equal(result.state,'interrupted');assert(result.backupAvailable);
  assert.deepEqual(await fs.readFile(f.file),candidate);assert.equal(f.r.placements,0);
});
test('restore rejects an active character and restores exact backup when inactive',async t=>{
  const f=await fixture(t);await install(f);await f.service.dispatch('stop');f.r.guid=f.guid;
  const rejected=await f.service.dispatch('restore');assert.equal(rejected.ok,false);assert.equal(JSON.parse(await fs.readFile(f.file,'utf8')).progress,28);
  f.r.guid=f.other;const restored=await f.service.dispatch('restore');assert.equal(restored.state,'restored');assert.deepEqual(await fs.readFile(f.file),f.source);
});
test('desktop restart recovers pending returned receipt without placement resend',async t=>{
  const f=await fixture(t);await install(f);f.r.guid=f.guid;f.r.lostReturn=true;await reach(f,'uncertain');
  f.service=f.make();await reach(f,'ready');assert.equal(f.r.placements,1);
});
test('refresh cycle reloads without another disk edit and places only once per cycle',async t=>{
  const f=await fixture(t,{refresh:true});await install(f);const candidate=await fs.readFile(f.file);f.r.guid=f.guid;
  await reach(f,'await_other_refresh');f.r.guid=f.other;await reach(f,'await_original_refresh');
  assert.deepEqual(await fs.readFile(f.file),candidate);f.r.guid=f.guid;await reach(f,'ready');assert.equal(f.r.placements,2);
});

test('stale refreshed boundary has a deadline after the original returns',async t=>{
  const f=await fixture(t,{refresh:true});await install(f);f.r.guid=f.guid;
  await reach(f,'await_other_refresh');f.r.guid=f.other;await reach(f,'await_original_refresh');
  f.r.guid=f.guid;f.r.boundaryReady=false;await reach(f,'boundary_refresh_wait');
  const active=path.join(f.storage,'active.json'),job=JSON.parse(await fs.readFile(active,'utf8'));
  job.since=Date.now()-21000;await fs.writeFile(active,JSON.stringify(job));f.service=f.make();
  const result=await f.service.dispatch('advance');assert.equal(result.state,'failed');
  assert.match(result.message,/did not settle/);assert.equal(f.r.placements,1);
});

test('unloaded destination waits without issuing any teleport',async t=>{
  const f=await fixture(t);await install(f);f.r.guid=f.guid;f.r.placementReady=false;
  await reach(f,'placement_initial_gate');await f.service.dispatch('advance');assert.equal(f.r.placements,0);
  f.r.placementReady=true;await reach(f,'ready');assert.equal(f.r.placements,1);
});

test('autosave during verification settles without repeating an edit or native action',async t=>{
  const f=await fixture(t);await install(f);f.r.guid=f.guid;f.r.autosaveDuringRead=1;
  const state=await f.service.dispatch('advance');assert.equal(state.state,'await_original');assert.match(state.message,/autosave/);
  await reach(f,'ready');assert.equal(f.r.placements,1);
  const after=JSON.parse(await fs.readFile(f.file,'utf8'));assert.equal(after.progress,28);assert.deepEqual(after.inventory,JSON.parse(f.source).inventory);
});

test('bookmark capture is read-only and replay uses the inactive-save transaction with forced map reload',async t=>{
  const f=await fixture(t);
  const saved=await f.service.dispatch('bookmark_save',{name:'My encounter'});
  assert.equal(saved.ok,true);assert.equal(saved.bookmarks.length,1);
  assert.deepEqual(await fs.readFile(f.file),f.source);assert.equal(f.r.placements,0);
  const id=saved.bookmarks[0].id;
  const entry=JSON.parse(await fs.readFile(path.join(f.storage,'bookmarks',id+'.json'),'utf8'));
  assert(!entry.snapshot.includes('inventory'));assert(!entry.snapshot.includes('level'));
  const rejected=await f.service.dispatch('bookmark_start',{id});assert.equal(rejected.ok,false);
  const begun=await f.service.dispatch('bookmark_start',{id,acknowledge_shared_progress:true});assert.equal(begun.state,'await_other');
  f.r.guid=f.other;await reach(f,'await_original');f.r.guid=f.guid;
  const ready=await reach(f,'ready');assert.match(ready.message,/Encounter behavior remains experimental/);
  assert(f.r.calls.travel);assert.equal(f.r.placements,1);
  assert.deepEqual(JSON.parse(await fs.readFile(f.file,'utf8')).inventory,JSON.parse(f.source).inventory);
});

test('bookmark checksum mismatch blocks replay before the picker or a save edit',async t=>{
  const f=await fixture(t),saved=await f.service.dispatch('bookmark_save',{name:'Point'}),id=saved.bookmarks[0].id;
  const file=path.join(f.storage,'bookmarks',id+'.json'),entry=JSON.parse(await fs.readFile(file,'utf8'));
  entry.snapshot+='tampered';await fs.writeFile(file,JSON.stringify(entry));
  const result=await f.service.dispatch('bookmark_start',{id,acknowledge_shared_progress:true});
  assert.equal(result.ok,false);assert.match(result.message,/contents differ/);assert.equal(f.r.lease,null);
  assert.deepEqual(await fs.readFile(f.file),f.source);
});

test('large mission bookmark resumes its saved transaction after desktop restart',async t=>{
  const f=await fixture(t,{snapshotPadding:300000});
  const saved=await f.service.dispatch('bookmark_save',{name:'Larger mission history'});
  await f.service.dispatch('bookmark_start',{id:saved.bookmarks[0].id,acknowledge_shared_progress:true});
  f.r.guid=f.other;await reach(f,'await_original');
  assert((await fs.stat(path.join(f.storage,'active.json'))).size>256*1024);
  f.service=f.make();f.r.guid=f.guid;const ready=await reach(f,'ready');
  assert.equal(ready.active,false);assert.equal(f.r.placements,1);
});

test('mission-state selection reloads and tracks without coordinates, floor checks or teleport',async t=>{
  const f=await fixture(t,{nativeBookmark:true});f.r.placementReady=false;
  const saved=await f.service.dispatch('bookmark_save',{name:'Mission state only'});
  assert.equal(saved.ok,true);assert.deepEqual(await fs.readFile(f.file),f.source);
  const id=saved.bookmarks[0].id;
  const entry=JSON.parse(await fs.readFile(path.join(f.storage,'bookmarks',id+'.json'),'utf8'));
  assert.equal(entry.spec.section.placement,'native');assert.equal(entry.spec.section.location,undefined);
  await f.service.dispatch('bookmark_start',{id,acknowledge_shared_progress:true});
  f.r.guid=f.other;await reach(f,'await_original');f.r.guid=f.guid;
  const ready=await reach(f,'ready');assert.match(ready.message,/game’s respawn point/);
  assert(f.r.calls.travel);assert.equal(f.r.trackRequests,1);assert.equal(f.r.placements,0);
  assert.equal(f.r.calls.place_0,undefined);assert.equal(f.r.lease,null);
  assert.deepEqual(JSON.parse(await fs.readFile(f.file,'utf8')).inventory,JSON.parse(f.source).inventory);
});


test('automatic native swap edits only while the exact holding character is active',async t=>{
  const f=await fixture(t,{automatic:true});const originalNow=Date.now;let clock=originalNow();Date.now=()=>clock;t.after(()=>Date.now=originalNow);
  let result=await f.service.dispatch('start',{mission:'Mission_Main_Shatteredlands3',checkpoint:28,acknowledge_shared_progress:true,automatic:true});
  assert.equal(result.backgroundLoading,true);assert.deepEqual(await fs.readFile(f.file),f.source);
  for(let i=0;i<35&&result.state!=='ready';i++){clock+=2000;result=await f.service.dispatch('advance');}
  assert.equal(result.state,'ready',JSON.stringify(result));assert.deepEqual(f.r.automaticCalls,['C_15','C_17']);
  const data=JSON.parse(await fs.readFile(f.file));assert.equal(data.progress,28);assert.equal(data.level,70);assert.deepEqual(data.inventory,JSON.parse(f.source).inventory);
});

test('unexpected automatically loaded character prevents the save edit',async t=>{
  const f=await fixture(t,{automatic:true});const originalNow=Date.now;let clock=originalNow();Date.now=()=>clock;t.after(()=>Date.now=originalNow);
  f.r.wrongAutomaticTarget=true;let result=await f.service.dispatch('start',{mission:'Mission_Main_Shatteredlands3',checkpoint:28,acknowledge_shared_progress:true,automatic:true});
  for(let i=0;i<8&&!['failed','uncertain'].includes(result.state);i++){clock+=2000;result=await f.service.dispatch('advance');}
  assert.equal(result.state,'failed');assert.deepEqual(await fs.readFile(f.file),f.source);assert.deepEqual(f.r.automaticCalls,['C_15']);
});

test('lost automatic refresh receipt recovers its next phase without repeating selection',async t=>{
  const f=await fixture(t,{automatic:true});const originalNow=Date.now;let clock=originalNow();Date.now=()=>clock;t.after(()=>Date.now=originalNow);
  f.r.loseRefresh=true;let result=await f.service.dispatch('start',{mission:'Mission_Main_Shatteredlands3',checkpoint:28,acknowledge_shared_progress:true,automatic:true});
  assert.equal(result.state,'uncertain');f.service=f.make();
  for(let i=0;i<35&&result.state!=='ready';i++){clock+=2000;result=await f.service.dispatch('advance');}
  assert.equal(result.state,'ready',JSON.stringify(result));assert.deepEqual(f.r.automaticCalls,['C_15','C_17']);
});

test('generated waypoint runs placement once and reports the selected start',async t=>{
  const f=await fixture(t,{waypoint:true});await install(f);f.r.guid=f.guid;
  const ready=await reach(f,'ready');assert.match(ready.message,/starting waypoint/);
  assert.equal(f.r.placements,1);assert(f.r.calls.travel);
});

test('unsafe generated waypoint retains native station before issuing any teleport',async t=>{
  const f=await fixture(t,{waypoint:true});await install(f);f.r.guid=f.guid;f.r.placementReady=false;
  await reach(f,'placement_initial_gate');
  const active=path.join(f.storage,'active.json'),job=JSON.parse(await fs.readFile(active,'utf8'));
  job.since=Date.now()-11000;await fs.writeFile(active,JSON.stringify(job));f.service=f.make();
  const ready=await reach(f,'ready');assert.match(ready.message,/native spawn station/);
  assert.equal(f.r.placements,0);assert.equal(f.r.calls.place_0,undefined);
});

test('uncertain generated waypoint never falls back or repeats its teleport',async t=>{
  const f=await fixture(t,{waypoint:true});await install(f);f.r.guid=f.guid;f.r.unknown=true;
  await reach(f,'uncertain');await f.service.dispatch('advance');assert.equal(f.r.placements,1);
  const job=JSON.parse(await fs.readFile(path.join(f.storage,'active.json'),'utf8'));
  assert.equal(job.placementFallback,undefined);assert.equal(job.phase,'uncertain');
});

test('Epic encrypted account profile completes automatic reload and waypoint transaction',async t=>{
  const accountId='aBcDeFaBcDeFaBcD0123456789abcdef';
  const f=await fixture(t,{automatic:true,encrypted:true,accountId,waypoint:true});
  const originalNow=Date.now;let clock=originalNow();Date.now=()=>clock;t.after(()=>Date.now=originalNow);
  let result=await f.service.dispatch('start',{mission:'Mission_Main_Shatteredlands3',checkpoint:28,acknowledge_shared_progress:true,automatic:true});
  for(let i=0;i<35&&result.state!=='ready';i++){clock+=2000;result=await f.service.dispatch('advance');}
  assert.equal(result.state,'ready',JSON.stringify(result));assert.deepEqual(f.r.automaticCalls,['C_15','C_17']);
  const data=JSON.parse(await f.realCodec('decrypt',await fs.readFile(f.file)));
  assert.equal(data.progress,28);assert.deepEqual(data.inventory,JSON.parse(f.source).inventory);assert.equal(data.level,70);
  const journal=JSON.parse(await fs.readFile(path.join(f.storage,'active.json'),'utf8'));
  assert.equal(journal.account,accountId);assert.equal(f.r.placements,1);
});
