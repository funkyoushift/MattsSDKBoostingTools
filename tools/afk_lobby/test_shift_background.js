const fs = require('fs'), vm = require('vm'), assert = require('assert');
const source = fs.readFileSync(__dirname + '/shift_background.js', 'utf8');
function fixture(direct) {
 let now = 0, tasks = [], requests = [], running = true, reviewed = true, endpoint = {port:7777,instance:'one',start_token:'05'.repeat(16)};
 function run() { assert(tasks.length);tasks.sort((a,b)=>a.at-b.at);const task=tasks.shift();now=task.at;task.f(); }
 const props = {opacity:{value:'0.65',priority:'important'},transform:{value:'rotate(1deg)',priority:''},'transform-origin':{value:'center',priority:'important'}};
 let style = {getPropertyValue:k=>props[k] ? props[k].value : '',getPropertyPriority:k=>props[k] ? props[k].priority : '',setProperty:(k,v,p)=>props[k]={value:v,priority:p||''},removeProperty:k=>delete props[k]};
 if (direct) style = {transform:'rotate(1deg)',transformOrigin:'center',opacity:'0.65'};
 const bar = {style:{},buttons:[],appendChild(b){this.buttons.push(b);if (b.id==='msbt-shift-background-start') this.button=b;}};
 class XHR {
  constructor(){requests.push(this);this.status=200;}
  open(method,url){this.method=method;this.url=url;}
  setRequestHeader(k,v){(this.headers ||= {})[k]=v;}
  send(body){this.body=JSON.parse(body);}
  abort(){this.aborted=true;}
  respond(state, overrides={}) { const payload={service:'msbt-shift-storage',protocol:1,instance:'one',background:{available:true,state,reason:'',token:this.body.token}}; Object.assign(payload,overrides); this.responseText=JSON.stringify(payload);this.onload(); }
 }
 const head={children:[],appendChild(n){this.children.push(n);n.parentNode=this;},removeChild(n){this.children=this.children.filter(x=>x!==n);n.parentNode=null;}};
 const window={document:{head,documentElement:{style:{transform:'untouched'}},getElementById:id=>id==='body_container'?{style}:id==='msbt-shift-float-bar'?bar:null,createElement:()=>({})},ShiftFriendAutomation:{isRunning:()=>running,startAutoAccept:()=>{running=true},stopAutoAccept:()=>{running=false}},ShiftMiniPanel:{protectionReady:()=>reviewed,backgroundBridge:()=>endpoint},setTimeout:(f,delay)=>{const task={f,at:now+delay};tasks.push(task);return task;},clearTimeout:task=>{tasks=tasks.filter(x=>x!==task);}};
 const ctx={window,document:window.document,XMLHttpRequest:XHR,Uint8Array,Number,JSON};vm.runInNewContext(source,ctx);
 return {window,head,bar,requests,props,style,start(){const ok=window.MsbtShiftBackground.start();if(ok)run();return ok;},run,advance(ms){const target=now+ms;while(tasks.some(task=>task.at<=target))run();now=target;},get now(){return now;},set running(v){running=v},set reviewed(v){reviewed=v},set endpoint(v){endpoint=v}};
}
{
 const f=fixture(); f.run(); assert.equal(f.bar.button.textContent,'Play while accepting');
 f.reviewed=false;
 f.running=false;assert(f.start());assert(f.window.ShiftFriendAutomation.isRunning());const start=f.requests[0];assert.deepEqual(start.body,{mode:'start',token:'05'.repeat(16)});assert.equal(start.headers['X-MSBT-Shift-Instance'],'one');
 assert.equal(f.start(),false);start.respond('pending');f.run();const hb=f.requests[1];assert.equal(hb.body.mode,'heartbeat');hb.respond('active');assert.equal(f.props.opacity.value,'1');assert.equal(f.props.transform.value,'scale(0.04)');assert.equal(f.props['transform-origin'].value,'top left');assert.equal(f.bar.style.transform,'scale(0.04)');assert.match(f.head.children[0].textContent,/html,body\{background:transparent!important;\}/);assert.match(f.head.children[0].textContent,/#body_container#body_container/);assert.equal(f.window.document.documentElement.style.transform,'untouched');
 f.run();f.requests[2].ontimeout();assert.equal(f.props.opacity.value,'0.65');assert.equal(f.props.opacity.priority,'important');assert.equal(f.head.children.length,0);assert.deepEqual(f.props.transform,{value:'rotate(1deg)',priority:''});assert.deepEqual(f.props['transform-origin'],{value:'center',priority:'important'});assert.equal(f.window.MsbtShiftBackground.status().state,'error');
}
{
 const f=fixture();f.run();f.start();const stale=f.requests[0];f.window.MsbtShiftBackground.stop();assert(stale.aborted);stale.respond('active');assert.equal(f.props.opacity.value,'0.65');assert.equal(f.requests[1].body.mode,'stop');
}
{
 const f=fixture();f.run();f.start();f.requests[0].respond('active');f.endpoint={port:7777,instance:'other'};f.run();assert.equal(f.props.opacity.value,'0.65');assert.equal(f.requests.length,1);
}
{
 const f=fixture();f.run();f.start();f.requests[0].respond('active');f.running=false;f.run();assert.equal(f.props.opacity.value,'0.65');assert.equal(f.requests[1].body.mode,'stop');
}
{
 const f=fixture();f.run();f.start();f.requests[0].respond('active');f.run();f.requests[1].respond('foreground');assert.equal(f.props.opacity.value,'0.65');
}
{
 const f=fixture();f.run();f.endpoint=null;assert.equal(f.start(),false);assert.equal(f.requests.length,0);
}
{
 const f=fixture();f.run();f.start();f.requests[0].respond('active');f.run();f.requests[1].respond('active',{instance:'other'});assert.equal(f.props.opacity.value,'0.65');assert.equal(f.window.MsbtShiftBackground.status().state,'error');
}
{
 const f=fixture();f.run();f.start();f.requests[0].respond('active');f.reviewed=false;f.run();assert.equal(f.props.opacity.value,'1');assert.equal(f.requests[1].body.mode,'heartbeat');
}
{
 const f=fixture();f.run();f.running=false;const cmd={id:'a'.repeat(32),mode:'start'};f.window.MsbtShiftBackground.onCompanionState({command:cmd});f.run();assert.equal(f.requests.length,1);assert.equal(f.requests[0].body.mode,'start');f.window.MsbtShiftBackground.onCompanionState({command:cmd});assert.equal(f.requests.length,1);f.requests[0].respond('active');
 const stop={id:'b'.repeat(32),mode:'stop'};f.window.MsbtShiftBackground.onCompanionState({command:stop});assert.equal(f.window.ShiftFriendAutomation.isRunning(),false);assert.equal(f.props.opacity.value,'0.65');assert.equal(f.requests[1].body.mode,'stop');f.window.MsbtShiftBackground.onCompanionState({command:stop});assert.equal(f.requests.length,3);assert.equal(f.requests[2].body.mode,'ack_stop');
}
{
 const f=fixture();f.run();f.start();const pending=f.requests[0];f.window.MsbtShiftBackground.onCompanionState({command:{id:'c'.repeat(32),mode:'stop'}});assert.equal(f.requests.length,1);pending.respond('active');assert.equal(f.window.ShiftFriendAutomation.isRunning(),false);assert.equal(f.requests[1].body.mode,'stop');assert.equal(f.props.opacity.value,'0.65');
}
{
 const f=fixture();f.run();f.start();f.requests[0].respond('active');f.run();let h=f.requests[1];h.respond('active',{background:{available:true,state:'active',token:h.body.token,command:{id:'d'.repeat(32),mode:'stop'}}});assert.equal(f.window.ShiftFriendAutomation.isRunning(),false);assert.equal(f.requests[2].body.mode,'stop');assert.equal(f.props.opacity.value,'0.65');
}
{
 const f=fixture();f.run();f.start();f.requests[0].respond('active');f.window.MsbtShiftBackground.onCompanionState({state:'foreground'});assert.equal(f.window.ShiftFriendAutomation.isRunning(),true);assert.equal(f.props.opacity.value,'0.65');
}
{
 const f=fixture();f.run();f.start();f.requests[0].respond('active');f.run();
 const hb=f.requests[1];hb.status=409;hb.respond('foreground',{ok:false,background:{available:true,state:'foreground',reason:'',token:null}});
 assert.equal(f.window.MsbtShiftBackground.status().state,'foreground');
 assert.equal(f.window.MsbtShiftBackground.status().reason,'');
 assert.equal(f.props.opacity.value,'0.65');assert.equal(f.window.ShiftFriendAutomation.isRunning(),true);
}
{
 const f=fixture();f.run();f.start();f.requests[0].respond('active');f.run();
 const hb=f.requests[1];hb.status=409;hb.respond('foreground',{ok:false,instance:'wrong',background:{available:true,state:'foreground',token:null}});
 assert.equal(f.window.MsbtShiftBackground.status().state,'error');
}
{
 const f=fixture();f.run();f.running=false;f.start();f.requests[0].respond('pending');f.run();
 const hb=f.requests[1],why='Close other menus and open SHiFT with F10 before starting.';
 hb.status=409;hb.respond('error',{ok:false,terminal:'owned-error',background:{available:true,state:'error',reason:why,token:null}});
 assert.equal(f.window.MsbtShiftBackground.status().state,'error');
 assert.equal(f.window.MsbtShiftBackground.status().reason,why);
 assert.equal(f.window.ShiftFriendAutomation.isRunning(),false);
 assert.equal(f.props.opacity.value,'0.65');assert.equal(f.head.children.length,0);
}
{
 const f=fixture();f.run();f.start();f.requests[0].respond('active');f.run();
 const hb=f.requests[1];hb.status=409;hb.respond('error',{ok:false,background:{available:true,state:'error',reason:'private reason',token:null}});
 assert.equal(f.window.MsbtShiftBackground.status().reason,'Background bridge identity or response changed');
}
{
 const f=fixture();f.run();f.start();f.requests[0].respond('active');f.run();
 const hb=f.requests[1];hb.status=409;hb.respond('error',{ok:false,terminal:'owned-error',instance:'wrong',background:{available:true,state:'error',reason:'private reason',token:null}});
 assert.equal(f.window.MsbtShiftBackground.status().reason,'Background bridge identity or response changed');
}
{
 const f=fixture();f.run();f.start();f.requests[0].status=409;f.requests[0].respond('foreground',{ok:false,background:{available:true,state:'foreground',token:null}});
 assert.equal(f.window.MsbtShiftBackground.status().state,'error');
}
console.log('PASS background lease lifecycle, identity pinning, readiness, timeout and opacity restoration');

{ const f=fixture();f.run();f.endpoint={port:7777,instance:'one'};assert.equal(f.start(),false);assert.match(f.window.MsbtShiftBackground.status().reason,/token/);assert.equal(f.requests.length,0); }
{ const f=fixture();f.run();f.endpoint=null;assert.equal(f.start(),false);assert.match(f.window.MsbtShiftBackground.status().reason,/bridge/); }
console.log('PASS server nonce and explicit prerequisite errors without browser crypto');

{ const f=fixture(true);f.run();assert(f.start());f.requests[0].respond('active');assert.equal(f.style.transform,'scale(0.04)');assert.equal(f.style.transformOrigin,'top left');assert.equal(f.style.opacity,'1');f.window.MsbtShiftBackground.stop();assert.equal(f.style.transform,'rotate(1deg)');assert.equal(f.style.transformOrigin,'center');assert.equal(f.style.opacity,'0.65'); }
{ const f=fixture();f.run();f.style.setProperty=()=>{throw new Error('unsupported style')};assert.equal(f.start(),false);assert.equal(f.requests.length,0);assert.match(f.window.MsbtShiftBackground.status().reason,/unsupported style/); }
{ const f=fixture();f.run();assert(f.start());f.requests[0].respond('active');f.style.setProperty=()=>{throw new Error('later failure')};f.window.MsbtShiftBackground.stop();assert.equal(f.requests[1].body.mode,'stop'); }
console.log('PASS direct style fallback and fail-closed presentation errors');

{const f=fixture();f.run();assert(f.window.MsbtShiftBackground.start());assert.equal(f.requests.length,0);f.window.MsbtShiftBackground.stop();assert.equal(f.props.transform.value,'rotate(1deg)');}
console.log('PASS cancellable foreground paint delay');

// A failed background entry stops acceptance only if this entry started it.
for (const alreadyRunning of [false,true]) {
 const f=fixture();f.run();f.running=alreadyRunning;assert(f.start());
 f.requests[0].status=400;f.requests[0].respond('unsupported');
 assert.equal(f.window.ShiftFriendAutomation.isRunning(),alreadyRunning);
 assert.equal(f.window.MsbtShiftBackground.status().state,'error');
}
// A foreground Stop has no lease token, but must acknowledge the desktop command.
{const f=fixture();f.run();f.running=true;f.window.MsbtShiftBackground.onCompanionState({command:{id:'e'.repeat(32),mode:'stop'}});
 assert.equal(f.window.ShiftFriendAutomation.isRunning(),false);assert.equal(f.requests.length,1);assert.equal(f.requests[0].body.mode,'ack_stop');}
// Repeat start/show cycles, proving presentation and independent accepting state survive.
{const f=fixture();f.run();for(let i=0;i<20;i++){assert(f.start());f.requests[f.requests.length-1].respond('active');
 f.window.MsbtShiftBackground.onCompanionState({state:'foreground'});assert.equal(f.props.transform.value,'rotate(1deg)');
 assert.equal(f.head.children.length,0);assert.equal(f.window.ShiftFriendAutomation.isRunning(),true);}}
console.log('PASS owned-start rollback, foreground stop acknowledgement, and 20 repeated start/show cycles');

// Model the native five-second lease: only heartbeats renew an owned lease;
// repeated Start acknowledgements leave its deadline untouched. Advance real
// fake-clock time across several leases while fresh Starts beat the 1s timer.
{
 const f=fixture();f.run();const page=f.window.MsbtShiftBackground;
 assert(page.start());f.advance(149);assert.equal(f.requests.length,0);
 f.advance(1);assert.equal(f.requests.length,1);
 const ownedToken=f.requests[0].body.token;
 let deadline=null,handled=0,heartbeats=0,starts=0,stopped=false;
 function settle() {
  while(handled<f.requests.length) {
   const request=f.requests[handled++],mode=request.body.mode;
   if(mode==='ack_stop')continue;
   assert.equal(request.body.token,ownedToken);
   f.advance(20); // Responses are asynchronous, not inline with send().
   if(mode==='stop'){stopped=true;request.respond('foreground');continue;}
   assert(!stopped,'No lease traffic after Stop');
   if(deadline===null)deadline=f.now+5000;
   assert(f.now<deadline,'Native lease expired despite successful repeated Starts');
   if(mode==='heartbeat'){deadline=f.now+5000;heartbeats++;}
   else {assert.equal(mode,'start');starts++;}
   request.respond('active');
  }
 }
 settle();
 f.endpoint={port:7777,instance:'one',start_token:'06'.repeat(16)};
 for(let i=1;i<=18;i++) {
  f.advance(900);
  page.onCompanionState({command:{id:i.toString(16).padStart(32,'0'),mode:'start'}});
  settle();assert.equal(page.status().state,'active');
 }
 assert.equal(starts,19);assert.equal(heartbeats,18);
 assert(f.now>16000);assert(f.now<deadline);
 page.onCompanionState({command:{id:'e'.repeat(32),mode:'stop'}});settle();
 assert(stopped);assert.equal(f.window.ShiftFriendAutomation.isRunning(),false);
 assert.equal(page.status().state,'foreground');
 const count=f.requests.length;f.advance(6000);assert.equal(f.requests.length,count);
}
console.log('PASS elapsed-time repeated Start lease renewal and later Stop');

// New command IDs must confirm an already-owned lease rather than disappear
// into the UI start button's duplicate-start guard.
for (const nativeState of ['pending', 'active']) {
 const f=fixture();f.run();assert(f.start());f.requests[0].respond(nativeState);
 const ownedToken=f.requests[0].body.token;
 f.endpoint={port:7777,instance:'one',start_token:'06'.repeat(16)};
 const command={id:'f'.repeat(32),mode:'start'};
 f.window.MsbtShiftBackground.onCompanionState({command});
 assert.equal(f.requests.length,2);assert.deepEqual(f.requests[1].body,{mode:'start',token:ownedToken});
 f.requests[1].respond(nativeState);
 f.window.MsbtShiftBackground.onCompanionState({command});assert.equal(f.requests.length,3);
 assert.deepEqual(f.requests[2].body,{mode:'heartbeat',token:ownedToken});
 f.requests[2].respond(nativeState);
 f.run();assert.equal(f.requests.length,4);assert.equal(f.requests[3].body.mode,'heartbeat');
}
// While an existing heartbeat is in flight, rapid desktop commands supersede
// one another. The last Start must be confirmed even if no Stop was observed.
{
 const f=fixture();f.run();assert(f.start());f.requests[0].respond('active');f.run();
 const heartbeat=f.requests[1],ownedToken=heartbeat.body.token;
 for (const [i,mode] of ['stop','start','stop','start'].entries()) {
  f.window.MsbtShiftBackground.onCompanionState({command:{id:String(i+1).repeat(32),mode}});
 }
 assert.equal(f.requests.length,2);heartbeat.respond('active');
 assert.equal(f.requests.length,3);assert.deepEqual(f.requests[2].body,{mode:'start',token:ownedToken});
 assert.equal(f.window.ShiftFriendAutomation.isRunning(),true);f.requests[2].respond('active');
 assert.deepEqual(f.requests[3].body,{mode:'heartbeat',token:ownedToken});f.requests[3].respond('active');
 const stop={id:'9'.repeat(32),mode:'stop'};
 f.window.MsbtShiftBackground.onCompanionState({command:stop});
 assert.equal(f.window.ShiftFriendAutomation.isRunning(),false);
 assert.equal(f.requests[4].body.mode,'stop');assert.equal(f.requests[5].body.mode,'ack_stop');
}
console.log('PASS new-ID Start confirmation with existing lease and rapid command supersession');

// Stop supersedes renewal; a canceled or invalid confirmation cannot revive it.
for(const outcome of ['queued-stop','canceled','wrong-token','wrong-instance','not-ready']) {
 const f=fixture();f.run();assert(f.start());f.requests[0].respond('active');
 const page=f.window.MsbtShiftBackground;
 page.onCompanionState({command:{id:'8'.repeat(32),mode:'start'}});
 const confirmation=f.requests[1];
 if(outcome==='queued-stop')page.onCompanionState({command:{id:'9'.repeat(32),mode:'stop'}});
 if(outcome==='canceled'){page.stop();assert(confirmation.aborted);}
 if(outcome==='not-ready')f.running=false;
 const overrides=outcome==='wrong-token'?{background:{available:true,state:'active',token:'ff'.repeat(16)}}:outcome==='wrong-instance'?{instance:'other'}:{};
 confirmation.respond('active',overrides);
 assert(!f.requests.slice(2).some(request=>request.body.mode==='heartbeat'));
 if(outcome==='queued-stop'||outcome==='canceled') {
  assert.equal(page.status().state,'foreground');assert.equal(f.requests[2].body.mode,'stop');
  f.requests[2].respond('foreground');
 }else assert.equal(page.status().state,'error');
 const count=f.requests.length;f.advance(6000);assert.equal(f.requests.length,count);
}
console.log('PASS repeated Start renewal respects Stop, generation, identity and readiness');

// A new command during the initial paint delay is confirmed by the original
// scheduled request, without bringing native entry forward or duplicating it.
{
 const f=fixture();f.run();assert(f.window.MsbtShiftBackground.start());
 const command={id:'7'.repeat(32),mode:'start'};
 f.window.MsbtShiftBackground.onCompanionState({command});
 assert.equal(f.requests.length,0);f.run();
 assert.equal(f.requests.length,1);assert.equal(f.requests[0].body.mode,'start');
 f.requests[0].respond('active');
 f.window.MsbtShiftBackground.onCompanionState({command});assert.equal(f.requests.length,1);
 f.run();assert.equal(f.requests.length,2);assert.equal(f.requests[1].body.mode,'heartbeat');
}
console.log('PASS new-ID Start preserves the initial foreground paint delay');


// Retain never-dispatched Start intent across temporary readiness loss;
// later Stop, newer commands and terminal generations revoke that intent.
{
const f = fixture();
f.run();
assert(f.start());
f.requests[0].respond('active');
const command = {id: 'a1'.repeat(16), mode: 'start'};
f.running = false;
f.window.MsbtShiftBackground.onCompanionState({command});
assert.equal(f.requests.length, 1, 'Do not send a Start while prerequisites are unavailable');
f.running = true;
f.window.MsbtShiftBackground.onCompanionState({command});
assert.equal(f.requests.length, 2, 'A never-dispatched pending Start must not be permanently marked seen');
assert.equal(f.requests[1].body.mode, 'start');
f.requests[1].respond('active');
const count = f.requests.length;
f.window.MsbtShiftBackground.onCompanionState({command});
assert.equal(f.requests.length, count, 'A dispatched command must remain deduplicated');
console.log('PASS temporary readiness loss retains an undispatched Start for later delivery');
}

// A Stop that occurs after retaining an undispatched Start must supersede it.
// stop() is also called by the page Stop-accepting control after stopping automation.
{
  const g = fixture();
  g.run(); assert(g.start()); g.requests[0].respond('active');
  const pending = {id: 'b2'.repeat(16), mode: 'start'};
  g.running = false;
  g.window.MsbtShiftBackground.onCompanionState({command: pending});
  g.window.MsbtShiftBackground.stop();
  assert.equal(g.requests[1].body.mode, 'stop');
  g.requests[1].respond('foreground');
  assert.equal(g.window.MsbtShiftBackground.status().state, 'foreground', 'Stop must revoke an older retained Start');
  assert.equal(g.window.ShiftFriendAutomation.isRunning(), false, 'Stop must not revive acceptance');
  g.window.MsbtShiftBackground.onCompanionState({command: pending});
  assert.equal(g.window.MsbtShiftBackground.status().state, 'foreground', 'A revoked Start cannot revive through a stale poll');
  const count = g.requests.length; g.advance(6000); assert.equal(g.requests.length, count);
}
console.log('PASS Stop supersedes a retained Start and prevents late replay');

// A newer desktop Stop also revokes the retained command, even if a stale poll
// advertises the old Start after the Stop has completed.
{
  const g = fixture(); g.run(); assert(g.start()); g.requests[0].respond('active');
  const pending = {id: 'c3'.repeat(16), mode: 'start'};
  g.running = false; g.window.MsbtShiftBackground.onCompanionState({command: pending});
  g.window.MsbtShiftBackground.onCompanionState({command: {id: 'd4'.repeat(16), mode: 'stop'}});
  assert.equal(g.requests[1].body.mode, 'stop');
  g.requests[1].respond('foreground');
  g.window.MsbtShiftBackground.onCompanionState({command: pending});
  assert.equal(g.window.MsbtShiftBackground.status().state, 'foreground');
  assert.equal(g.window.ShiftFriendAutomation.isRunning(), false);
}

// Existing endpoint-change fail-closed behavior is not loosened. Ending an
// owned generation revokes its retained Start, rather than resending it later.
{
  const g = fixture(); g.run(); assert(g.start()); g.requests[0].respond('active');
  const pending = {id: 'e5'.repeat(16), mode: 'start'};
  g.running = false; g.window.MsbtShiftBackground.onCompanionState({command: pending});
  g.endpoint = {port: 7777, instance: 'other', start_token: '06'.repeat(16)};
  g.run(); assert.equal(g.window.MsbtShiftBackground.status().state, 'error');
  g.endpoint = {port: 7777, instance: 'one', start_token: '05'.repeat(16)};
  g.running = true; g.window.MsbtShiftBackground.onCompanionState({command: pending});
  assert.equal(g.window.MsbtShiftBackground.status().state, 'error');
  assert.equal(g.requests.length, 1);
}
console.log('PASS newer desktop Stop and terminal generation changes revoke retained Start');
