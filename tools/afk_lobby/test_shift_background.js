const fs = require('fs'), vm = require('vm'), assert = require('assert');
const source = fs.readFileSync(__dirname + '/shift_background.js', 'utf8');
function fixture(direct) {
 let tasks = [], requests = [], running = true, reviewed = true, endpoint = {port:7777,instance:'one',start_token:'05'.repeat(16)};
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
 const window={document:{head,documentElement:{style:{transform:'untouched'}},getElementById:id=>id==='body_container'?{style}:id==='msbt-shift-float-bar'?bar:null,createElement:()=>({})},ShiftFriendAutomation:{isRunning:()=>running,startAutoAccept:()=>{running=true},stopAutoAccept:()=>{running=false}},ShiftMiniPanel:{protectionReady:()=>reviewed,backgroundBridge:()=>endpoint},setTimeout:f=>{tasks.push(f);return f;},clearTimeout:f=>{tasks=tasks.filter(x=>x!==f);}};
 const ctx={window,document:window.document,XMLHttpRequest:XHR,Uint8Array,Number,JSON};vm.runInNewContext(source,ctx);
 return {window,head,bar,requests,props,style,start(){const ok=window.MsbtShiftBackground.start();if(ok){assert(tasks.length);tasks.shift()();}return ok;},run(){assert(tasks.length);tasks.shift()();},set running(v){running=v},set reviewed(v){reviewed=v},set endpoint(v){endpoint=v}};
}
{
 const f=fixture(); f.run(); assert.equal(f.bar.button.textContent,'Play while accepting');
 f.reviewed=false;
 f.running=false;assert(f.start());assert(f.window.ShiftFriendAutomation.isRunning());const start=f.requests[0];assert.deepEqual(start.body,{mode:'start',token:'05'.repeat(16)});assert.equal(start.headers['X-MSBT-Shift-Instance'],'one');
 assert.equal(f.start(),false);start.respond('pending');f.run();const hb=f.requests[1];assert.equal(hb.body.mode,'heartbeat');hb.respond('active');assert.equal(f.props.opacity.value,'1');assert.equal(f.props.transform.value,'scale(0.04)');assert.equal(f.props['transform-origin'].value,'top left');assert.equal(f.bar.style.transform,'scale(0.04)');assert.match(f.head.children[0].textContent,/#body_container#body_container/);assert.equal(f.window.document.documentElement.style.transform,'untouched');
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
