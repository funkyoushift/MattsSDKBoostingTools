const {app,BrowserWindow}=require('electron');
const fs=require('fs'),path=require('path'),assert=require('assert');
app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
 const w=new BrowserWindow({show:false,width:1280,height:800,webPreferences:{sandbox:false}});
 await w.loadURL('data:text/html,<html><head><style>body{margin:0;background:white} %23body_container{width:100vw;height:100vh;background:navy}</style></head><body><div id="body_container">SHiFT test surface</div></body></html>');
 await w.webContents.executeJavaScript('window.running=false;window.ShiftFriendAutomation={isRunning:()=>running,startAutoAccept:()=>running=true,stopAutoAccept:()=>running=false};void 0;');
 await w.webContents.executeJavaScript(fs.readFileSync(path.join(__dirname,'../tools/afk_lobby/shift_float.js'),'utf8'));
 await new Promise(r=>setTimeout(r,850));
 const r=await w.webContents.executeJavaScript(`(()=>{
 const root=document.getElementById('body_container'),toggle=document.getElementById('msbt-shift-float-toggle'),accept=document.getElementById('msbt-shift-float-accept');
 const small=root.getBoundingClientRect().width,viewport=innerWidth,transparent=getComputedStyle(document.body).backgroundColor;
 accept.click();const started=running;toggle.click();const full=root.getBoundingClientRect().width;toggle.click();
 document.getElementById('msbt-shift-float-drag').dispatchEvent(new MouseEvent('mousedown',{clientX:20,clientY:20,bubbles:true}));
 document.dispatchEvent(new MouseEvent('mousemove',{clientX:80,clientY:100,bubbles:true}));document.dispatchEvent(new MouseEvent('mouseup'));
 return {small,viewport,transparent,started,full,moved:root.getBoundingClientRect().left};})()`);
 assert(Math.abs(r.small/r.viewport-.42)<.001);assert.equal(r.full,r.viewport);assert.equal(r.transparent,'rgba(0, 0, 0, 0)');assert(r.started);assert(r.moved>12);
 console.log('PASS floating SHiFT: compact/full size, transparency, drag, accepter stays active');w.destroy();app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});


