const assert = require("assert");
const fs = require("fs");
const vm = require("vm");
const pending = [], timers = [], calls = [];
let running = false;
class XHR {
  open(method, url) { this.method = method; this.url = url; }
  setRequestHeader() {}
  send(body) { this.body = body; pending.push(this); }
}
const automation = {isRunning:()=>running,startAutoAccept:()=>{running=true;calls.push("start");},stopAutoAccept:()=>{running=false;calls.push("stop");}};
const context = {XMLHttpRequest:XHR,ShiftFriendAutomation:automation,window:{ShiftFriendAutomation:automation,setTimeout:fn=>timers.push(fn)}};
vm.runInNewContext("var previousDashboardArray = []\n" + fs.readFileSync(require("path").join(__dirname,"shift_link.js"),"utf8"),context);
function poll(enabled) {
  timers.shift()(); const request = pending.shift();
  assert.equal(request.method,"GET");
  request.status=200; request.responseText=JSON.stringify({ok:true,auto_accept:enabled,service:"msbt-sdk-bridge",instance:"a".repeat(32)});
  request.onload(); request.onloadend();
  const report=pending.shift(); assert.equal(report.method,"POST");
  assert.equal(JSON.parse(report.body).running,running);
}
poll(false); assert.deepEqual(calls,[]);
poll(true); poll(true); assert.deepEqual(calls,["start"]);
poll(false); assert.deepEqual(calls,["start","stop"]);
console.log("PASS SHiFT link: start, no duplicate start, stop, running acknowledgements.");

timers.shift()(); const unrelated=pending.shift();unrelated.status=200;unrelated.responseText=JSON.stringify({ok:true,auto_accept:true});unrelated.onload();unrelated.onloadend();assert.equal(pending.length,0);
timers.shift()();const fallback=pending.shift();assert.ok(fallback.url.includes(':27874/'));fallback.onloadend();
timers.shift()();assert.ok(pending.shift().url.includes(':27875/'));
console.log('PASS port rotation and no acknowledgements to unrelated servers.');

// A lost AFK bridge stops only bridge-owned automation, then can reconnect.
function lossScenario(managed) {
  const requests=[], timeouts=[], storage=new Map();let active=true, policy=false;
  class Request {
    open(method,url){this.method=method;this.url=url;}
    setRequestHeader(){}
    send(body){this.body=body;requests.push(this);}
  }
  const automation={isRunning:()=>active,startAutoAccept:()=>active=true,stopAutoAccept:()=>active=false,setAfkManaged:v=>policy=v};
  const win={ShiftFriendAutomation:automation,setTimeout:fn=>timeouts.push(fn),localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)}};
  vm.runInNewContext(fs.readFileSync(require('path').join(__dirname,'shift_link.js'),'utf8'),{window:win,ShiftFriendAutomation:automation,XMLHttpRequest:Request});
  function response(value) {
    timeouts.shift()();const r=requests.shift();
    if(value!==null){r.status=200;r.responseText=JSON.stringify({ok:true,auto_accept:value,service:'msbt-sdk-bridge',instance:'b'.repeat(32)});r.onload();requests.shift();}
    r.onloadend();
  }
  if(managed){response(true);assert(active&&policy);}
  response(null);assert.equal(active,!managed);assert.equal(policy,false);
  if(managed){response(true);assert(active&&policy);response(false);assert(!active&&!policy);assert(!storage.has('msbt_afk_managed'));}
}
lossScenario(false);lossScenario(true);
console.log('PASS lost bridge: managed automation stops, manual automation survives, reconnect and release work.');
