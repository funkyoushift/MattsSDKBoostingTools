"use strict";
const assert = require("assert");
const path = require("path");
const { app, BrowserWindow } = require("electron");
app.whenReady().then(async () => {
  const win = new BrowserWindow({ show:false, webPreferences:{sandbox:false,partition:`farm-lab-${process.pid}`} });
  await win.loadFile(path.join(__dirname,"renderer.html"),{query:{nosplash:"1"}});
  const result = await win.webContents.executeJavaScript(`(async () => {
    const requests=[]; let enabled=false;
    const featureGroups={
      infinite_ammo:"Weapons", no_reload:"Weapons", instant_reload:"Weapons", no_recoil:"Weapons", super_accuracy:"Weapons", rapid_fire:"Weapons", critical_hits:"Weapons",
      god_mode:"Player", skill_cooldown:"Player", skill_duration:"Player", grenade_cooldown:"Player", glide_duration:"Movement", vendor_refresh:"Vendor", legendary_roll:""
    };
    state.selectedTarget="1|Guest";
    bridgeStatus=async()=>{};
    const status=()=>({ok:true,farming_lab:{features:Object.fromEntries(Object.keys(featureGroups).map(feature=>[feature,{label:feature,enabled:feature==="no_reload"&&enabled,actual_locked:feature==="no_reload"?enabled:undefined,error:"",scope:"local player"}]))}});
    window.msbt={bridgeRequest:async request=>{
      requests.push(request);
      if(request.method==="GET")return {ok:true,data:status()};
      if(request.payload.payload.op==="set")enabled=request.payload.payload.enabled;
      if(request.payload.payload.op==="off")enabled=false;
      return {ok:true,data:{ok:true,message:"Local test applied"}};
    }};
    syncFarmingLabStatus(status());
    const groupsCorrect=Object.entries(featureGroups).every(([feature,group])=>document.getElementById("farmingLab_"+feature).parentElement.id==="farmingLab"+group+"Controls");
    const rarityFeatures=[...document.querySelectorAll("#farmingLabControls [data-farming-feature]")].map(b=>b.dataset.farmingFeature);
    let pending;const original=runFarmingLabAction;
    runFarmingLabAction=payload=>(pending=original(payload));
    const texts=[];
    for(const mode of ["true","false"]){
      pending=null;document.querySelector('[data-farming-feature="no_reload"][data-farming-enabled="'+mode+'"]').click();
      if(!pending)throw Error("Button was not wired");await pending;
      texts.push(document.getElementById("farmingLab_no_reload").textContent);
    }
    document.getElementById("farmingLabAllOff").click();await pending;
    syncFarmingLabStatus({});
    return {requests,texts,groupsCorrect,rarityFeatures,disabled:[...document.querySelectorAll("[data-farming-controls] button, [data-farming-all-off]")].every(b=>b.disabled),settings:raritySettingsPayload()};
  })()`);
  const posts=result.requests.filter(r=>r.method==="POST");
  assert.deepStrictEqual(posts.map(r=>r.payload.action),["farming_lab","farming_lab","farming_lab"]);
  assert.deepStrictEqual(posts.map(r=>r.payload.payload),[{op:"set",feature:"no_reload",enabled:true},{op:"set",feature:"no_reload",enabled:false},{op:"off"}]);
  assert.match(result.texts[0],/game lock ON/);assert.match(result.texts[1],/game lock OFF/);
  assert(result.groupsCorrect);assert(result.rarityFeatures.every(feature=>feature==="legendary_roll"));
  assert(result.disabled);assert(!Object.hasOwn(result.settings,"farming_lab"));
  console.log("PASS local controls: category placement, actual clicks, host scope, real-lock status, all-off, disconnected disabling and no persistence");
  win.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
