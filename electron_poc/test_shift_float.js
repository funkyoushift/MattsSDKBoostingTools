const {app,BrowserWindow}=require('electron');
const fs=require('fs'),path=require('path'),assert=require('assert');
app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
 const w=new BrowserWindow({show:false,width:1280,height:800,webPreferences:{sandbox:false}});
 await w.loadURL('data:text/html,<html><head><style>body{margin:0;background:white} %23body_container{width:100vw;height:100vh;background:navy}</style></head><body><div id="body_container">SHiFT test surface</div></body></html>');
 await w.webContents.executeJavaScript(`window.running=false;window.managed=false;window.savedSize='0.7';Object.defineProperty(window,'localStorage',{value:{getItem:()=>savedSize,setItem:(k,v)=>savedSize=v}});window.ShiftMiniPanel={show:()=>managed=true};window.ShiftFriendAutomation={isRunning:()=>running,startAutoAccept:()=>running=true,stopAutoAccept:()=>running=false};void 0;`);
 await w.webContents.executeJavaScript(fs.readFileSync(path.join(__dirname,'../tools/afk_lobby/shift_float.js'),'utf8'));
 await new Promise(r=>setTimeout(r,850));
 const r=await w.webContents.executeJavaScript(`(()=>{
 const root=document.getElementById('body_container'),toggle=document.getElementById('msbt-shift-float-toggle'),accept=document.getElementById('msbt-shift-float-accept');
 const viewport=innerWidth,initial=root.getBoundingClientRect().width,transparent=getComputedStyle(document.body).backgroundColor;
 const clickSize=(name)=>{const button=document.getElementById('msbt-shift-size-'+name);button.click();return {width:root.getBoundingClientRect().width,saved:savedSize,pressed:button.getAttribute('aria-pressed')};};
 const small=clickSize('compact'),medium=clickSize('medium'),regular=clickSize('regular');
 toggle.click();const toggledCompact=root.getBoundingClientRect().width;toggle.click();const toggledFull=root.getBoundingClientRect().width;toggle.click();
 accept.click();const started=running;accept.click();const stopped=!running;accept.click();
 Array.from(document.querySelectorAll('#msbt-shift-float-bar button')).find(b=>b.textContent==='Manage SHiFT').click();
 document.getElementById('msbt-shift-float-drag').dispatchEvent(new MouseEvent('mousedown',{clientX:20,clientY:20,bubbles:true}));
 document.dispatchEvent(new MouseEvent('mousemove',{clientX:80,clientY:100,bubbles:true}));document.dispatchEvent(new MouseEvent('mouseup'));
 return {initial,small,medium,regular,viewport,transparent,started,stopped,managed,toggledCompact,toggledFull,moved:root.getBoundingClientRect().left};})()`);
 const near=(width,scale)=>assert(Math.abs(width/r.viewport-scale)<.001);
 near(r.initial,.7);near(r.small.width,.42);near(r.medium.width,.7);near(r.regular.width,1);near(r.toggledCompact,.42);near(r.toggledFull,1);
 for(const [size,value] of [[r.small,'0.42'],[r.medium,'0.7'],[r.regular,'1']]){assert.equal(size.saved,value);assert.equal(size.pressed,'true');}
 assert.equal(r.transparent,'rgba(0, 0, 0, 0)');assert(r.started);assert(r.stopped);assert(r.managed);assert(r.moved>12);
 console.log('PASS floating SHiFT: all size buttons and persistence, toggle, transparency, drag, accepter and Manage SHiFT');w.destroy();app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});


