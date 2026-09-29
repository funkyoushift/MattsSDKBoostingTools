const assert=require('node:assert/strict'),http=require('node:http'),os=require('node:os'),path=require('node:path');
const {createBridgeClient}=require('./bridge_client');
const {createMobileGateway}=require('./mobile_gateway');
(async()=>{
 let wrongActions=0,rightActions=0,identity='a'.repeat(32);
 const wrong=http.createServer((req,res)=>{if(req.method==='POST')wrongActions++;res.end(JSON.stringify({ok:true}));});
 const right=http.createServer((req,res)=>{if(req.url==='/bridge-info')res.end(JSON.stringify({service:'msbt-sdk-bridge',protocol:1,port:right.address().port,instance:identity,started:true}));else{assert.equal(req.headers['x-msbt-instance'],identity);if(req.method==='POST')rightActions++;res.end('{"ok":true}');}});
 for(const server of [wrong,right])await new Promise(r=>server.listen(0,'0.0.0.0',r));
 const client=createBridgeClient({ports:[wrong.address().port,right.address().port],endpointFile:path.join(os.tmpdir(),'missing-msbt-discovery-test.json')});
 const gateway=createMobileGateway({port:wrong.address().port,pairingCode:'123456',requestBridge:a=>client.request(a),bridgeInfo:()=>client.info()});
 try{
   assert.equal((await client.request({method:'POST',path:'/action',payload:{action:'test'}})).ok,true);
   identity='b'.repeat(32);assert.equal((await client.request({method:'POST',path:'/action',payload:{action:'test'}})).ok,true);
   assert.equal(rightActions,2);assert.equal(wrongActions,0);
   const info=await gateway.start();assert.ok([27877,27878].includes(info.port));
   const response=await fetch(`http://127.0.0.1:${info.port}/status`,{headers:{'X-MSBT-Pairing-Code':'123456'}});
   assert.equal(response.status,200);assert.equal((await response.json()).ok,true);
   console.log('PASS occupied/unrelated primary, verified fallback, fresh instance on actions, mobile gateway fallback and shared bridge.');
 }finally{await gateway.stop();for(const server of [wrong,right])await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1});
