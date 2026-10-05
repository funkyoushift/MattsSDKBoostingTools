'use strict';
const fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');
const {app,BrowserWindow,protocol}=require('electron'),native=require('../electron_poc/native_card_protocol');
app.setPath('userData',path.resolve(__dirname,'../output/firmware-audit-profile'));
native.registerNativeCardSchemes(protocol);app.on('window-all-closed',()=>{});
app.whenReady().then(async()=>{
 const widgets=new Map();for(const name of await fs.readdir(process.argv[2])){if(!/^[a-f0-9]{64}\.json$/.test(name))continue;const file=path.join(process.argv[2],name),data=JSON.parse(await fs.readFile(file,'utf8')),time=(await fs.stat(file)).mtimeMs;if(!widgets.has(data.serial)||widgets.get(data.serial).time<time)widgets.set(data.serial,{widget:data.widget,time});}
 const samples=new Map();let bearing=0;for(const {widget:w} of widgets.values())if(w.FirmwareVisible){bearing++;assert.ok(w.firmware?.label&&w.FirmwareIdent,'Visible firmware must identify its type');samples.set(w.FirmwareIdent,w);}
 native.installNativeCardProtocol(protocol);const win=new BrowserWindow({show:false,webPreferences:{sandbox:true,offscreen:true}});await win.loadURL('msbt-card://inventory/card.html');
 const results=[],failures=[];for(const w of samples.values()){
  try {
  const model=require('../electron_poc/native_widget_card_model').fromNativeWidget(w,{allowMissingArtwork:true});
  const view=await win.webContents.executeJavaScript(`(async()=>{const r=await renderNativeCard(${JSON.stringify(model)},templates);const n=document.querySelector('.firmware_name_cntr'),icon=document.querySelector('.firmware_icon.icon_bkg');return {errors:r.errors,name:n?.textContent,visible:!!n?.getBoundingClientRect().height,icon:icon?getComputedStyle(icon).backgroundImage:''};})()`);
  assert.deepEqual(view.errors,[]);assert.equal(view.name,w.firmware.label);assert.equal(view.visible,true);assert.ok(view.icon&&view.icon!=='none','Firmware icon missing: '+w.FirmwareIdent);results.push({name:view.name,ident:w.FirmwareIdent});
  } catch(error) {failures.push({name:w.Name,firmware:w.firmware.label,message:error.message});}
 }
 const result={ok:!failures.length,unique_cached_items:widgets.size,firmware_bearing:bearing,firmware_types:results.length,results,failures,evidence:'Cached game widget identity and actual browser-rendered name/icon; not an equipped-loadout test'};
 await fs.writeFile(process.argv[3],JSON.stringify(result,null,2));console.log(JSON.stringify(result));win.destroy();app.exit(failures.length?1:0);
}).catch(error=>{console.error(error);app.exit(1);});
