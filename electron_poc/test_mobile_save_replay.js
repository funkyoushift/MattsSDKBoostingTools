'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const {createMobileDesktopApi}=require('./mobile_desktop_api');
(async()=>{
  const api=createMobileDesktopApi(),calls=[],native=[];
  const source=fs.readFileSync(require.resolve('./main.js'),'utf8');
  const offset=source.indexOf("registerDesktopHandler('app:saveReplay'");
  assert(offset>0);
  const handler=source.slice(offset,source.indexOf('\n});',offset)+4);
  vm.runInNewContext(handler,{
    registerDesktopHandler:(channel,callback)=>api.register(channel,callback),
    localSaveReplay:()=>({dispatch:async(action,payload)=>{calls.push({action,payload});return {ok:true,state:action==='start'?'await_other':'idle',active:action==='start'};}}),
    requestSaveReplay:async(action,payload)=>{native.push({action,payload});return {ok:true,loaded:true};},
  });
  const client=crypto.randomUUID(),send=async call=>{
    const result=await api.handle({client,op:'start',calls:[call]});
    assert.equal(result.ok,true);assert.equal(result.data.reply.jobs[0].state,'done');
    return result.data.reply.jobs[0].value;
  };
  const call={id:crypto.randomUUID(),method:'saveReplay',args:['start',{mission:'Mission_Main_Harmonica4',checkpoint:22,automatic:true,acknowledge_shared_progress:true}]};
  assert.equal((await send(call)).state,'await_other');await send(call);assert.equal(calls.length,1,'phone duplicate repeated replay start');
  for(const action of ['status','stop','bookmark_list','bookmark_save','bookmark_start']){
    assert.equal((await send({id:crypto.randomUUID(),method:'saveReplay',args:[action,{}]})).ok,true);
  }
  const invalid=await send({id:crypto.randomUUID(),method:'saveReplay',args:['write_save_directly',{}]});
  assert.equal(invalid.ok,false);assert.equal(calls.length,6);assert.equal(native.length,0);
  assert.equal(calls[0].payload.acknowledge_shared_progress,true);
  console.log('PASS paired phone routes replay/bookmarks through the PC transaction, preserves acknowledgement, rejects unknown actions, and deduplicates start');
})().catch(error=>{console.error(error);process.exitCode=1;});
