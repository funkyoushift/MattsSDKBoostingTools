const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const {createRemoteAfk}=require('./remote_afk');
const envelope=require('./remote_crypto');
(async()=>{
 const relay=process.env.MSBT_TEST_RELAY||'http://127.0.0.1:8787';let stored=null,calls=[];
 const host=createRemoteAfk({relay,load:async()=>stored,save:async c=>{stored=c;},bridge:async(route,payload)=>{calls.push({route,payload});return {ok:true,status:200,data:{ok:true,name:'Test PC',afk_lobby:{enabled:payload?.action==='afk_lobby_start'},last_command:{secret:'must not escape'}}};}});
 try {
  await host.start();for(let i=0;i<50&&!host.info().connected;i++)await new Promise(r=>setTimeout(r,100));assert.ok(host.info().connected,JSON.stringify(host.info()));
  const pairing=host.pairing();assert.ok(!('owner' in pairing));
  const request=async req=>{const packet=await envelope.seal(pairing.key,req,pairing.room+':request');const r=await fetch(`${relay}/room/${pairing.room}/request`,{method:'POST',headers:{Authorization:`Bearer ${pairing.token}`,'Content-Type':'application/json'},body:JSON.stringify(packet)});assert.equal(r.status,200);const reply=await envelope.open(pairing.key,await r.json(),pairing.room+':response');assert.equal(reply.id,req.id);return reply.result;};
  const req={id:crypto.randomUUID(),time:Date.now(),route:'/status'};let result=await request(req);assert.equal(result.ok,true);assert.equal(result.data.last_command,undefined);
  result=await request(req);assert.equal(result.ok,false);assert.equal(calls.length,1);
  result=await request({id:crypto.randomUUID(),time:Date.now(),route:'/action',payload:{action:'empty_backpack'}});assert.equal(result.ok,false);assert.equal(calls.length,1);
  result=await request({id:crypto.randomUUID(),time:Date.now(),route:'/action',payload:{action:'afk_lobby_start',payload:{loot:true,codes:'@UTest'}}});assert.equal(result.data.afk_lobby.enabled,true);
  const tampered=await envelope.seal(pairing.key,{hello:'world'},'request');await assert.rejects(envelope.open(pairing.key,tampered,'response'));
  const unauth=await fetch(`${relay}/room/${pairing.room}/request`,{method:'POST',headers:{Authorization:'Bearer '+'0'.repeat(64)},body:'{}'});assert.equal(unauth.status,401);
  await host.stop();const revoked=await fetch(`${relay}/room/${pairing.room}/request`,{method:'POST',headers:{Authorization:`Bearer ${pairing.token}`},body:'{}'});assert.equal(revoked.status,401);assert.equal(stored,null);
  console.log('PASS encrypted relay, AFK allowlist, replay prevention, secret filtering, authentication, revocation');
 } finally {host.shutdown();}
})().catch(e=>{console.error(e);process.exitCode=1;});
