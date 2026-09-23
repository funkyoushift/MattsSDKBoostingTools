"use strict";
const assert=require("node:assert/strict"),path=require("node:path"),fs=require("node:fs");
const {app,BrowserWindow}=require("electron");
app.whenReady().then(async()=>{
  const resolver=require("./serial_card_resolve").loadResolver({sourceRoot:path.resolve(__dirname,"..")});
  const human="300, 0, 1, 60| 2, 2002|| {9} {8} {246:26} {248:7} {248:16} {246:65}|";
  const card=resolver.resolveFromHuman(human);
  const win=new BrowserWindow({show:false,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false}});
  await win.loadFile(path.join(__dirname,"renderer.html"),{query:{nosplash:"1"}});
  const result=await win.webContents.executeJavaScript(`(async()=>{
    const fixture=${JSON.stringify(card)}, human=${JSON.stringify(human)};
    clearGzoSubmitForm();
    const verify=(condition,message)=>{if(!condition)throw new Error(message);};
    // Avoid external network calls and native iframe: this test exercises the
    // actual submit DOM, field mapping and async controller.
    fillBl4ItemCard=()=>{};
    window.msbt={serialToolsConvert:async value=>({ok:true,serialized:'@Ufixture',deserialized:human}),serialCardResolve:async()=>({cards:[{ok:true,card:fixture}]}),captureNativeCard:async()=>({ok:false,message:'fixture failure'})};
    els.gzoSubmitBase85.value='@Ufixture';
    await generateGzoSubmitItemCard();
    verify(els.gzoSubmitName.value===fixture.display_name,'name autofill');
    verify(els.gzoSubmitStatus.textContent.includes('Could not capture'),'capture failure must not become success');
    els.gzoSubmitName.value='My manual title';
    els.gzoSubmitDlc.value='Harmonica';
    applyGzoSubmitCardFields({...fixture,display_name:'Updated automatic title'},{overwrite:false});
    verify(els.gzoSubmitName.value==='My manual title','manual title preservation');
    verify(els.gzoSubmitDlc.value==='Harmonica','manual DLC preservation');
    let release;
    window.msbt.captureNativeCard=()=>new Promise(resolve=>{release=resolve;});
    const capture=captureGzoSubmitCardAsScreenshot();
    els.gzoSubmitBase85.value='@Uchanged';
    scheduleGzoSubmitItemCard({target:els.gzoSubmitBase85});
    clearTimeout(state.gzoSubmitCardTimer);
    release({ok:true,base64:'iVBORw0KGgo='});
    verify(await capture===false,'stale capture must be rejected');
    verify(!gzoSubmitImageFile(),'stale image must not be attached');
    verify(!els.gzoSubmitDeserialized.value,'new serial clears old decoded data');
    let finish, sent=0;
    submitGzoForm=()=>{sent++;return new Promise(resolve=>{finish=resolve;});};
    const first=handleGzoSubmit();await handleGzoSubmit();
    verify(sent===1,'double-click must not submit twice');finish();await first;
    verify(!els.gzoSubmitSendBtn.disabled,'button must recover');
    return {ok:true};
  })()`);
  assert.equal(result.ok,true);win.destroy();console.log("PASS GZO submit UI: autofill/manual edits, screenshot failure, changed serial, duplicate-submit guard");app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
