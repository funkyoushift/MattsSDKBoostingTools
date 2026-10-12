const assert=require('node:assert/strict');
const panel=require('./full_progress_panel');
const scope=require('./mission_panel');
(async()=>{
 assert.equal(panel.pollDelay({}),50);
 for(const scoped of [false,true]){
  let calls=[];let count=0;
  const call=async(action,payload)=>{
   calls.push(action);
   if(action.endsWith('_status'))return {ok:true,id:'run',state:'running',index:4};
   if(++count===1)return {ok:false,cancelled:true,message:'newer command'};
   return {ok:true,id:'run',state:scoped?'completed':'finished',index:5};
  };
  const job={ok:true,id:'run',state:'running',index:4};
  const result=scoped?await scope.advance(call,job,()=>false,()=>{}):await panel.advance(call,job,()=>{});
  const prefix=scoped?'mission':'full_progress';
  assert.deepEqual(calls,[prefix+'_step',prefix+'_status',prefix+'_step']);
  assert.equal(result.index,5);
 }
 const calls=[];
 const result=await panel.advance(async action=>{calls.push(action);return {ok:false,id:'run',state:'uncertain'};},{ok:true,id:'run',state:'running'},()=>{});
 assert.equal(result.state,'uncertain');assert.deepEqual(calls,['full_progress_step']);
 console.log('PASS shared scoped/full progress polling, reconnect without restart, terminal failure');
})().catch(e=>{console.error(e);process.exitCode=1;});
