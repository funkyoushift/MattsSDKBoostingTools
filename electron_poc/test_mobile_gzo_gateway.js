const assert=require('node:assert/strict');
const {createMobileGateway}=require('./mobile_gateway');
const net=require('node:net');
(async()=>{
  const listener=net.createServer();await new Promise(resolve=>listener.listen(0,'127.0.0.1',resolve));const port=listener.address().port;await new Promise(resolve=>listener.close(resolve));
  const calls=[];
  const gateway=createMobileGateway({port,pairingCode:'test-only',prepareGzo:async p=>{calls.push(p);return{ok:true,serial:p.serial};},submitGzo:async p=>{calls.push(p);return{ok:true,message:'mock accepted'};}});
  await gateway.start();
  try{
    const url=`http://127.0.0.1:${port}/mobile/gzo/prepare`;
    let r=await fetch(url,{method:'POST',body:'{}'});assert.equal(r.status,401);assert.equal(calls.length,0);
    r=await fetch(url,{method:'POST',headers:{'X-MSBT-Pairing-Code':'test-only'},body:JSON.stringify({serial:'@UcasePreserved'})});assert.equal(r.status,200);assert.equal((await r.json()).serial,'@UcasePreserved');
    r=await fetch(url,{method:'POST',headers:{'X-MSBT-Pairing-Code':'test-only'},body:'invalid'});assert.equal(r.status,400);
    r=await fetch(url.replace('prepare','submit'),{method:'POST',headers:{'X-MSBT-Pairing-Code':'test-only'},body:'{}'});assert.equal(r.status,200);assert.equal(calls.length,2);
    console.log('PASS authenticated GZO mobile routes, malformed requests, and mock submission; no external writes');
  }finally{await gateway.stop();}
})().catch(e=>{console.error(e);process.exitCode=1;});
