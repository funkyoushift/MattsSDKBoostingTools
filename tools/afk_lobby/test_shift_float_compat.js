const vm=require('vm'),fs=require('fs'),assert=require('assert');
const source=fs.readFileSync(__dirname+'/shift_float.js','utf8');
const nodes={}; let intervals=0, timeouts=[];
function node(id) { return nodes[id] ||= {id,style:{},classList:{toggle(){}},setAttribute(){},appendChild(child){if(child.id)nodes[child.id]=child;},set innerHTML(v){for(const m of v.matchAll(/id="([^"]+)"/g))node(m[1]);}}; }
const root=node('body_container'), body=node('body'), head=node('head');head.appendChild=function(child){this.childStyle=child;};
const document={body,head,documentElement:node('html'),getElementById:id=>nodes[id]||null,createElement:()=>node('generated'+Math.random()),addEventListener(){}};
const window={document,innerWidth:1280,innerHeight:720,setTimeout:fn=>timeouts.push(fn),setInterval:()=>{intervals++},addEventListener(){},ShiftFriendAutomation:{isRunning:()=>false,startAutoAccept(){},stopAutoAccept(){}}};
const ctx={window,document,localStorage:{getItem:()=>null,setItem(){}},Number,Math};vm.runInNewContext(source,ctx);timeouts.shift()();
assert.equal(root.style.transform,'scale(0.42)');assert.match(head.childStyle.textContent,/transform:scale\(0.42\)!important/);assert.equal(root.style.left,'12px');assert.equal(root.style.top,'70px');assert.equal(intervals,1);
nodes['msbt-shift-size-medium'].onclick();assert.match(head.childStyle.textContent,/transform:scale\(0.7\)!important/);nodes['msbt-shift-size-regular'].onclick();assert.equal(root.style.transform,'');assert.equal(root.style.left,'');
nodes['msbt-shift-size-compact'].onclick();assert.equal(root.style.transform,'scale(0.42)');
console.log('PASS float initializes and changes size without CSSStyleDeclaration methods');
