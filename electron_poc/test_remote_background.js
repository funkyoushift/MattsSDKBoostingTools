const assert=require('node:assert/strict'),{EventEmitter}=require('node:events');
const {createRemoteBackground}=require('./remote_background');
const app=new EventEmitter();app.isPackaged=true;const logins=[];app.setLoginItemSettings=x=>logins.push(x);app.quit=()=>app.emit('before-quit');
let blockers=0,destroyed=0,hidden=0,shown=0;
class Tray extends EventEmitter{setToolTip(){}setContextMenu(){}destroy(){destroyed++}}
const win=new EventEmitter();win.hide=()=>hidden++;win.show=()=>shown++;win.focus=()=>{};win.isMinimized=()=>false;
const bg=createRemoteBackground({app,BrowserWindow:{getAllWindows:()=>[win]},Tray,Menu:{buildFromTemplate:x=>x},nativeImage:{createFromPath:x=>x},powerSaveBlocker:{start:()=>++blockers,stop:()=>blockers--},iconPath:'test',onDisable:()=>{}});
bg.bind(win);bg.update({enabled:true});bg.update({enabled:true});assert.equal(blockers,1);
let prevented=0;win.emit('close',{preventDefault:()=>prevented++});assert.equal(hidden,1);assert.equal(prevented,1);
bg.show();assert.equal(shown,1);app.quit();win.emit('close',{preventDefault:()=>prevented++});assert.equal(prevented,1);
bg.update({enabled:false});assert.equal(blockers,0);assert.equal(destroyed,1);
if(process.platform==='win32'){assert.deepEqual(logins.map(x=>x.openAtLogin),[true,false]);assert.ok(logins.every(x=>x.name==='MSBTRemoteAFK'));}
console.log('PASS remote background close, single sleep blocker, explicit quit, disable cleanup, isolated login entry.');
