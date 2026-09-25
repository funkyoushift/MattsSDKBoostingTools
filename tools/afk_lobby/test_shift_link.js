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
  request.status=200; request.responseText=JSON.stringify({ok:true,auto_accept:enabled});
  request.onload(); request.onloadend();
  const report=pending.shift(); assert.equal(report.method,"POST");
  assert.equal(JSON.parse(report.body).running,running);
}
poll(false); assert.deepEqual(calls,[]);
poll(true); poll(true); assert.deepEqual(calls,["start"]);
poll(false); assert.deepEqual(calls,["start","stop"]);
console.log("PASS SHiFT link: start, no duplicate start, stop, running acknowledgements.");
