const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../mobile_controller/app/src/main/assets/app.js'),'utf8');
let verified=false,posts=0,pings=0;
const ctx={state:{connection:{port:'27874',pairingCode:'123456'}},gatewayBase:()=> 'http://127.0.0.1:27874',text:v=>String(v||''),ensureDeviceToken:()=> 'private-device-token',AbortController,setTimeout,clearTimeout,fetch:async(url,options)=>{
 if(url.endsWith('/mobile/ping')){pings++;assert.equal(options.headers['X-MSBT-Device'],undefined);assert.equal(options.headers['X-MSBT-Pairing-Code'],undefined);return {ok:true,status:200,text:async()=>JSON.stringify(verified?{ok:true,port:27874,direct:true,name:'MattsSDKBoostingTools external bridge',instance:'d'.repeat(32)}:{ok:true})};}
 posts++;assert.equal(options.headers['X-MSBT-Instance'],'d'.repeat(32));return {ok:true,status:200,text:async()=>'{"ok":true}'};
}};
vm.runInNewContext(source.slice(source.indexOf('function verifiedMobilePing('),source.indexOf('async function gatewayAction(')),ctx);
(async()=>{
 await assert.rejects(ctx.gatewayFetch('/action',{method:'POST',payload:{action:'test'}}));assert.equal(posts,0);
 verified=true;assert.equal((await ctx.gatewayFetch('/action',{method:'POST',payload:{action:'test'}})).ok,true);assert.equal(posts,1);assert.equal(pings,2);
 console.log('PASS phone action endpoint verification, no action or device token to unrelated discovery servers, instance guard.');
})().catch(e=>{console.error(e);process.exitCode=1});
