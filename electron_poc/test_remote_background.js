const assert=require('node:assert/strict'),{EventEmitter}=require('node:events');
const {createRemoteBackground}=require('./remote_background');
const app=new EventEmitter();app.isPackaged=true;const logins=[];app.setLoginItemSettings=x=>logins.push(x);app.quit=()=>app.emit('before-quit');
let blockers=0,destroyed=0,hidden=0,shown=0;
class Tray extends EventEmitter{setToolTip(){}setContextMenu(){}destroy(){destroyed++}}
const win=new EventEmitter();win.hide=()=>hidden++;win.show=()=>shown++;win.focus=()=>{};win.isMinimized=()=>false;win.isDestroyed=()=>false;
const offscreen={isMinimized:()=>false,show:()=>assert.fail('An offscreen card must never be shown'),focus:()=>assert.fail('An offscreen card must never be focused')};
const bg=createRemoteBackground({app,BrowserWindow:{getAllWindows:()=>[offscreen,win]},Tray,Menu:{buildFromTemplate:x=>x},nativeImage:{createFromPath:x=>x},powerSaveBlocker:{start:()=>++blockers,stop:()=>blockers--},iconPath:'test',onDisable:()=>{}});
bg.show();assert.equal(shown,0,'No bound control panel yet');
bg.bind(win);bg.update({enabled:true});bg.update({enabled:true});assert.equal(blockers,1);
bg.show();assert.equal(shown,1);
let prevented=0;win.emit('close',{preventDefault:()=>prevented++});assert.equal(hidden,0);assert.equal(prevented,1);
assert.equal(blockers,0);assert.equal(destroyed,1);
win.emit('close',{preventDefault:()=>prevented++});assert.equal(prevented,1);
bg.update({enabled:false});assert.equal(blockers,0);assert.equal(destroyed,1);
win.emit('closed');bg.show();assert.equal(shown,1,'Never fall back to an offscreen window after main window closes');
if(process.platform==='win32'){assert.deepEqual(logins.map(x=>x.openAtLogin),[true,false]);assert.ok(logins.every(x=>x.name==='MSBTRemoteAFK'));}
console.log('PASS remote background close, single sleep blocker, explicit quit, disable cleanup, isolated login entry.');
