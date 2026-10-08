const assert=require('node:assert/strict'),crypto=require('node:crypto');
const {createMobileDesktopApi,PART_BYTES,compactMobileStatus}=require('./mobile_desktop_api');
const contract=require('./desktop_contract');
(async()=>{
  const list='@UAbCd\n'.repeat(80000),hash=crypto.createHash('sha256').update(list).digest('hex');
  const original={ok:true,status:200,data:{serial_text:list,last_drop:{codes:list},afk_lobby:{enabled:true,config:{codes:list}},players:[{name:'Guest'}]}};
  const first=compactMobileStatus(original,[]);assert.equal(Object.keys(first.mobileStatus.texts).length,1,'duplicate lists sent more than once');
  assert.equal(first.mobileStatus.texts[hash],list);assert.equal(original.data.serial_text,list,'compaction mutated desktop result');
  const next=compactMobileStatus({...original,data:{...original.data,players:[{name:'New guest'}]}},[hash]);
  assert.equal(Object.keys(next.mobileStatus.texts).length,0);assert.ok(JSON.stringify(next).length<2000,'unchanged status still sends item lists');
  assert.equal(next.data.players[0].name,'New guest','live player changes cached');
  const changed=compactMobileStatus({data:{serial_text:list+'Changed'}},[hash]);assert.equal(Object.keys(changed.mobileStatus.texts).length,1,'changed list not transferred');
  const codes=Array.from({length:4000},(_,i)=>'@UaBcD'+i+'X'.repeat(100));
  const arrayFirst=compactMobileStatus({data:{afk_lobby:{enabled:true,config:{codes}}}},[]);
  const arrayNext=compactMobileStatus({data:{afk_lobby:{enabled:false,config:{codes}}}},Object.keys(arrayFirst.mobileStatus.texts));
  assert.ok(JSON.stringify(arrayNext).length<1000);assert.equal(arrayNext.data.afk_lobby.enabled,false);
  const api=createMobileDesktopApi(),client=crypto.randomUUID(),other=crypto.randomUUID();let writes=0;
  api.register('app:saveSerialBookmarks',async(event,value)=>{writes++;assert.equal(event.mobile,true);return {ok:true,owner:event.sender.id,value};});
  api.register('app:loadBl4Catalog',()=>({ok:true,entries:[{name:'Unicode \u2603',serial:'@UAbCd',data:'X'.repeat(2*PART_BYTES)}]}));
  const call={id:crypto.randomUUID(),method:'saveSerialBookmarks',args:[{serial:'@UAbCd'}]};
  const send=async body=>{const result=await api.handle({client,...body});assert.equal(result.ok,true,JSON.stringify(result));return result.data.reply;};
  let reply=await send({op:'start',calls:[call]});assert.equal(reply.jobs[0].value.value.serial,'@UAbCd');
  await send({op:'start',calls:[call]});assert.equal(writes,1,'retry repeated a write');
  assert.equal((await send({op:'poll',ids:[call.id]})).jobs[0].value.owner,'mobile:'+client);
  const isolated=await api.handle({client:other,op:'poll',ids:[call.id]});assert.equal(isolated.data.reply.jobs[0].state,'error');
  const bad=await send({op:'start',calls:[{id:crypto.randomUUID(),method:'__proto__',args:[]}]});assert.equal(bad.jobs[0].state,'error');
  api.publish(contract.events.onUpdateState,{status:'downloading'});reply=await send({op:'poll',ids:[]});assert.equal(reply.events[0].channel,'app:updateState');
  reply=await send({op:'start',calls:[{id:crypto.randomUUID(),method:'loadBl4Catalog',args:[]}]});assert.ok(reply.transfer);
  const parts=[];for(let index=0;index<reply.transfer.parts;index++)parts.push(Buffer.from((await send({op:'part',id:reply.transfer.id,index})).base64,'base64'));
  const bytes=Buffer.concat(parts);assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),reply.transfer.sha256);assert.equal(reply.transfer.encoding,'gzip');assert.equal(JSON.parse(require('node:zlib').gunzipSync(bytes)).jobs[0].value.entries[0].serial,'@UAbCd');
  assert.equal((await api.handle({client:other,op:'part',id:reply.transfer.id,index:0})).ok,false);
  await send({op:'release',id:reply.transfer.id});
  const uploadCall={id:crypto.randomUUID(),method:'saveSerialBookmarks',args:[{serial:'@UaBcD',text:'a'.repeat(2*PART_BYTES)}]},upload=Buffer.from(JSON.stringify(uploadCall)),sha256=crypto.createHash('sha256').update(upload).digest('hex'),count=Math.ceil(upload.length/PART_BYTES);
  for(let index=0;index<count;index++)await send({op:'upload',id:uploadCall.id,index,parts:count,sha256,base64:upload.subarray(index*PART_BYTES,(index+1)*PART_BYTES).toString('base64')});
  await send({op:'uploadedStart',id:uploadCall.id});assert.equal(writes,2);
  assert.equal((await api.handle({client,op:'upload',id:crypto.randomUUID(),index:3,parts:1,base64:'a',sha256})).ok,false);
  let finish;api.register('app:validatorBulk',()=>new Promise(resolve=>finish=resolve));
  const slow={id:crypto.randomUUID(),method:'validatorBulk',args:[]};reply=await send({op:'start',calls:[slow]});assert.equal(reply.jobs[0].state,'running');finish({ok:true});await new Promise(resolve=>setTimeout(resolve,0));assert.equal((await send({op:'poll',ids:[slow.id]})).jobs[0].state,'done');
  let ack=[];
  for(let i=0;i<540;i++){
    const next={id:crypto.randomUUID(),method:'saveSerialBookmarks',args:[{iteration:i}]};
    reply=await send({op:'start',calls:[next],ack});assert.equal(reply.jobs[0].state,'done','long session exhausted receipt history');ack=[next.id];
  }
  const countBefore=writes,last=ack[0];
  await send({op:'poll',ids:[],ack});
  reply=await send({op:'start',calls:[{id:last,method:'saveSerialBookmarks',args:[]}]});
  assert.equal(reply.jobs[0].state,'error');assert.equal(writes,countBefore,'acknowledged write repeated');
  for(let i=0;i<12;i++){
    await send({op:'begin'});
    reply=await send({op:'start',calls:[{id:crypto.randomUUID(),method:'loadBl4Catalog',args:[]}]});
    assert.ok(reply.transfer,'reopening phone workspace leaked old downloads');
  }
  console.log('PASS shared desktop method contract, per-phone previews, write deduplication, background jobs, events, exact large payloads and transfer isolation');
})().catch(error=>{console.error(error);process.exitCode=1});
