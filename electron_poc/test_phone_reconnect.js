const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
let callbacks=[],failed=true,reads=0,shows=0;
const state={connection:{remote:{v:3,relay:'https://msbt-afk-relay.screename53.workers.dev',room:'a'.repeat(64),token:'b'.repeat(64),key:'c'.repeat(64)}}};
let requestId;
const context={state,crypto:{randomUUID:()=>String(++reads)},msbtRemoteCrypto:{seal:async(_k,v)=>{requestId=v.id;return {}},open:async()=>({id:requestId,result:{ok:true,data:{ok:true}}})},AbortController,fetch:async()=>{if(failed)throw Error('offline');return {ok:true,json:async()=>({})}},setTimeout:(fn,ms)=>{if(ms===5000)callbacks.push(fn);return fn},clearTimeout:fn=>{callbacks=callbacks.filter(v=>v!==fn)},applyStatus:()=>{},startStatusPolling:()=>{},stopStatusPolling:()=>{},updateConnectionChrome:()=>{},showScreen:()=>{shows++},$:()=>({}),window:{addEventListener:()=>{}},document:{addEventListener:()=>{}},STORE:{connection:'x'},write:()=>{}};
vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'../mobile_controller/app/src/main/assets/remote.js'),'utf8'),context);
(async()=>{
 const remote=context.window.mobileRemote;
 assert.equal(await remote.connect(),false);assert.equal(callbacks.length,1);
 failed=false;callbacks.shift()();await new Promise(r=>setImmediate(r));assert.equal(state.online,true);assert.equal(shows,0);assert.equal(reads,2);
 remote.scheduleReconnect();remote.suspend();assert.equal(callbacks.length,0);
 await remote.connect();assert.equal(shows,1);
 console.log('PASS phone read-only reconnect, no navigation on automatic retry, explicit disconnect cancellation.');
})().catch(e=>{console.error(e);process.exitCode=1});
