'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');
const {createNativePreviewClient}=require('./native_preview_client');

async function setup(t){
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'msbt-preview-test-'));
  t.after(async()=>{assert.equal(path.dirname(path.resolve(dir)),path.resolve(os.tmpdir()));assert.ok(path.basename(dir).startsWith('msbt-preview-test-'));await fs.rm(dir,{recursive:true,force:true});});
  const state={session:'a'.repeat(32),builds:0,renders:0};
  const options={cacheDirectory:dir,renderRevision:'test-layout',
    request:async({payload:{action,payload}})=>{
      if(action.endsWith('_status'))return {ok:true,enabled:true,schema:'native-standalone-widget-v1',session:state.session};
      state.builds++;return {ok:true,schema:'native-standalone-widget-v1',session:state.session,serial:payload.serial,widget:{Name:'Native'}};
    },capture:async()=>{state.renders++;return {ok:true,base64:'aW1hZ2U='};}};
  return {state,options,client:createNativePreviewClient(options),dir};
}

test('offline snapshots retain exact serial and renderer identity without contacting the game',async t=>{
  const {client,options,state}=await setup(t);await client.connect();await client.get('@UCode');
  const offline=createNativePreviewClient({...options,request:async()=>{throw Error('offline');}});
  assert.equal((await offline.snapshot('@UCode')).offline,true);
  assert.equal(await offline.snapshot('@Ucode'),null);
  const changed=createNativePreviewClient({...options,renderRevision:'new-assets'});
  assert.equal(await changed.snapshot('@UCode'),null);assert.equal(state.builds,1);
});
test('500 simultaneous refresh requests produce one preview and image; new client reuses disk',async t=>{
  const {state,client,options}=await setup(t);await client.connect();
  const result=await Promise.all(Array.from({length:500},()=>client.get('@UCode')));
  assert.equal(state.builds,1);assert.equal(state.renders,1);assert.ok(result.every(r=>r.widget.Name==='Native'));
  const second=createNativePreviewClient(options);await second.connect();assert.equal((await second.get('@UCode')).cached,true);
  assert.equal(state.builds,1);assert.equal(state.renders,1);
});
test('serial case and new game sessions require separate cache entries',async t=>{
  const {state,client}=await setup(t);await client.connect();
  await client.get('@UCode');await client.get('@Ucode');state.session='b'.repeat(32);
  await client.connect();await client.get('@UCode');assert.equal(state.builds,3);
});
test('failed generation is retryable and never cached as an image',async t=>{
  const {state,options}=await setup(t);const request=options.request;let fail=true;
  options.request=async args=>args.payload.action==='native_card_preview'&&fail?{ok:false,message:'Game unavailable'}:request(args);
  const client=createNativePreviewClient(options);await client.connect();await assert.rejects(client.get('@UCode'),/Game unavailable/);
  fail=false;assert.equal((await client.get('@UCode')).cached,false);assert.equal(state.renders,1);
});
test('response for a different serial is rejected before image capture',async t=>{
  const {state,options}=await setup(t);const request=options.request;
  options.request=async args=>{const r=await request(args);if(r.serial)r.serial='@Uwrong';return r;};
  const client=createNativePreviewClient(options);await client.connect();await assert.rejects(client.get('@UCode'),/does not match/);assert.equal(state.renders,0);
});
test('inventory metadata does not render images; opening the card reuses that native result',async t=>{
  const {state,client}=await setup(t);await client.connect();
  const metadata=await client.get('@UCode',{image:false});assert.equal(metadata.widget.Name,'Native');assert.equal(state.renders,0);
  const card=await client.get('@UCode');assert.ok(card.image.ok);assert.equal(state.builds,1);assert.equal(state.renders,1);
  const cachedMetadata=await client.get('@UCode',{image:false});
  assert.equal(cachedMetadata.image,undefined,'inventory metadata must not transfer cached PNG payloads');
  assert.equal((await client.get('@UCode')).cached,true);assert.equal(state.renders,1);
});

test('a late status reply cannot restore an older game session',async t=>{
  const {options}=await setup(t);const request=options.request;const replies=[];
  options.request=args=>args.payload.action.endsWith('_status')
    ?new Promise(resolve=>replies.push(resolve)):request(args);
  const client=createNativePreviewClient(options);
  const first=client.connect();const rejected=assert.rejects(first,/superseded/);
  const second=client.connect();
  replies[1]({ok:true,enabled:true,schema:'native-standalone-widget-v1',session:'a'.repeat(32)});
  await second;
  replies[0]({ok:true,enabled:true,schema:'native-standalone-widget-v1',session:'b'.repeat(32)});
  await rejected;
  assert.equal((await client.get('@UCode')).session,'a'.repeat(32));
});

test('a game-session change during capture prevents saving the stale image',async t=>{
  const {options,state,dir}=await setup(t);let started,finish;
  const capturing=new Promise(resolve=>started=resolve);
  options.capture=async()=>{started();await new Promise(resolve=>finish=resolve);return {ok:true,base64:'aW1hZ2U='};};
  const client=createNativePreviewClient(options);await client.connect();
  const first=client.get('@UCode');const rejected=assert.rejects(first,/session changed/);
  await capturing;state.session='b'.repeat(32);await client.connect();finish();await rejected;
  assert.deepEqual((await fs.readdir(dir)).filter(name=>name.endsWith('.json')),[]);
  const saved=await fs.readdir(path.join(dir,'widgets'));
  assert.equal(saved.length,1,'validated data from the old session remains reusable only in that session');
});

test('changing renderer assets rebuilds only the image and preserves native data',async t=>{
  const {state,client,options}=await setup(t);await client.connect();await client.get('@UCode');
  const revised=createNativePreviewClient({...options,renderRevision:'new-artwork'});await revised.connect();
  await revised.get('@UCode');assert.equal(state.builds,1);assert.equal(state.renders,2);
});

test('capture failure preserves validated data so retry never rebuilds the item',async t=>{
  const {state,options}=await setup(t);let fail=true;
  const capture=options.capture;options.capture=async widget=>{if(fail)throw Error('Capture failed');return capture(widget);};
  const client=createNativePreviewClient(options);await client.connect();
  await assert.rejects(client.get('@UCode'),/Capture failed/);fail=false;
  await client.get('@UCode');assert.equal(state.builds,1);assert.equal(state.renders,1);
});
