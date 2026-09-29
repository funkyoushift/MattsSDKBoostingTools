"use strict";
const assert=require('node:assert/strict'),http=require('node:http'),{WebSocketServer}=require('ws');
const {createRemoteAfk}=require('./remote_afk');
const wait=async fn=>{const deadline=Date.now()+3000;while(!fn()){if(Date.now()>deadline)throw Error('timed out');await new Promise(r=>setTimeout(r,10));}};
(async()=>{
 let registers=0,fail=false,stored=null,revokes=0;
 const host=http.createServer((req,res)=>{req.resume();if(req.url.endsWith('/register')){registers++;res.writeHead(fail?503:200).end('{}');}else{revokes++;res.end('{}');}});
 const wss=new WebSocketServer({server:host});wss.on('connection',ws=>ws.on('message',()=>ws.send('{"type":"pong"}')));
 await new Promise(r=>host.listen(0,'127.0.0.1',r));
 const options={load:async()=>stored,save:async c=>{stored=c},bridge:async()=>({ok:true,data:{ok:true}}),relay:`http://127.0.0.1:${host.address().port}`,retryMs:15,heartbeatMs:20,heartbeatTimeoutMs:100,renewMs:150};
 let client=createRemoteAfk(options);
 try{
  await client.restore();assert.equal(client.info().enabled,false);assert.equal(registers,0);
  fail=true;await client.start();await wait(()=>registers>0);assert.equal(client.info().enabled,true);const pairing=client.pairing();
  fail=false;await wait(()=>client.info().connected);const first=registers;
  await wait(()=>registers>first);await wait(()=>client.info().connected);assert.deepEqual(client.pairing(),pairing);
  client.shutdown();client=createRemoteAfk(options);await client.restore();await wait(()=>client.info().connected);assert.deepEqual(client.pairing(),pairing);
  for(const ws of wss.clients)ws.terminate();const previous=registers;await wait(()=>registers>previous);await wait(()=>client.info().connected);
  await client.stop();assert.equal(stored,null);assert.equal(client.info().enabled,false);assert.ok(revokes);
  let release;const delayed=createRemoteAfk({...options,load:()=>new Promise(r=>{release=r})});const starting=delayed.start();await wait(()=>release);delayed.shutdown();release(null);await starting;assert.equal(delayed.info().enabled,false);assert.equal(stored,null);
  console.log('PASS remote restore, offline enable/retry, renewal, same pairing after restart, socket reconnect, revoke, pending-load shutdown.');
 }finally{client.shutdown();for(const ws of wss.clients)ws.terminate();wss.close();await new Promise(r=>host.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1});
