const assert=require('assert'),path=require('path');
const {app,BrowserWindow}=require('electron');app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
 const win=new BrowserWindow({show:false,webPreferences:{sandbox:false,partition:`pw-${process.pid}`}});
 await win.loadFile(path.join(__dirname,'renderer.html'),{query:{nosplash:'1'}});
 const r=await win.webContents.executeJavaScript(`(async()=>{
 const calls=[];bridgeAction=async(action,payload)=>{calls.push({action,payload});return {data:payload.backpack_password==='funkyou'?{ok:true,message:'Applied'}:{ok:false,password_required:true,backpack_target:'guest-1',message:'Locked'}};};
 const p=runAction('chaos_empty_backpack',{},null);await new Promise(r=>setTimeout(r,20));
 let d=document.getElementById('backpackPasswordDialog');const masked=d.querySelector('input').type==='password';d.querySelector('input').value='funkyou';d.querySelector('form').dispatchEvent(new Event('submit',{cancelable:true}));const applied=await p;
 const p2=runAction('chaos_drop_backpack_targeted',{},null);await new Promise(r=>setTimeout(r,20));document.getElementById('backpackPasswordDialog').close();const cancelled=await p2;
 return {calls,masked,applied,cancelled,removed:!document.getElementById('backpackPasswordDialog'),stored:JSON.stringify(localStorage).includes('funkyou')};})()`);
 assert(r.masked&&r.removed&&!r.stored);assert.equal(r.calls.length,3);assert.equal(r.calls[1].payload.backpack_expected_target,'guest-1');assert(r.applied.data.ok);assert(!r.cancelled.ok);
 console.log('PASS password prompt, target pin, cancellation, no password storage');win.destroy();app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});
