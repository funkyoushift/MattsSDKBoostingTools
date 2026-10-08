"use strict";
const {app,BrowserWindow}=require("electron");
const assert=require("node:assert/strict"),path=require("node:path");
app.whenReady().then(async()=>{
  const win=new BrowserWindow({show:false,webPreferences:{sandbox:false,partition:`farm-party-${process.pid}`}});
  await win.loadFile(path.join(__dirname,"renderer.html"),{query:{nosplash:"1"}});
  const result=await win.webContents.executeJavaScript(`(async()=>{
    state.players=[{index:0,name:"Host"},{index:1,name:"Guest A"},{index:2,name:"Guest B"}];
    state.hostPlayerIndex=0;state.selectedTarget="1|Guest A";
    bridgeStatus=async()=>{};
    const requests=[];
    const data={players:state.players,farming_lab:{player_targeting:true,features:Object.fromEntries(Object.entries(FARMING_LAB_FEATURES).map(([feature,definition])=>[feature,{label:definition.label,enabled:true,error:"",targets:[{label:"Guest A",index:1,enabled:true,actual_invulnerable:true,actual_locked:true,error:""}]}]))}};
    window.msbt={bridgeRequest:async request=>{requests.push(request);return {ok:true,data:request.method==="GET"?data:{ok:true,message:"Applied"}};}};
    setPublicBoostScope("selected");syncFarmingLabStatus(data);
    const selected=document.getElementById("farmingLab_god_mode").textContent;
    await runFarmingLabAction({op:"set",feature:"god_mode",enabled:true});
    setPublicBoostScope("nonhost");syncFarmingLabStatus(data);
    const mixed=document.getElementById("farmingLab_god_mode").textContent;
    await runFarmingLabAction({op:"set",feature:"no_reload",enabled:false});
    const scope=document.querySelector("[data-farming-scope]");scope.value="all";scope.dispatchEvent(new Event("change"));
    const allPickers=[...document.querySelectorAll("[data-farming-scope]")].every(select=>select.value==="all");
    await runFarmingLabAction({op:"set",feature:"glide_duration",enabled:true});
    setPublicBoostScope("local");syncFarmingLabStatus(data);
    const local=document.getElementById("farmingLab_god_mode").textContent;
    await runFarmingLabAction({op:"set",feature:"infinite_ammo",enabled:true});
    await runFarmingLabAction({op:"set",feature:"vendor_refresh",enabled:true});
    await runFarmingLabAction({op:"off"});
    return {selected,mixed,local,allPickers,pickerCount:document.querySelectorAll("[data-farming-scope]").length,posts:requests.filter(r=>r.method==="POST").map(r=>r.payload.payload),global:document.getElementById("farmingLab_vendor_refresh").textContent};
  })()`);
  assert.match(result.selected,/ON.*Guest A/);assert.match(result.mixed,/1\/2 ON/);assert.match(result.local,/OFF.*Host/);
  assert(result.allPickers);assert.equal(result.pickerCount,3);
  assert.deepEqual(result.posts,[
    {op:"set",feature:"god_mode",enabled:true,target_scope:"selected",target_player:"1|Guest A"},
    {op:"set",feature:"no_reload",enabled:false,target_scope:"nonhost"},
    {op:"set",feature:"glide_duration",enabled:true,target_scope:"all"},
    {op:"set",feature:"infinite_ammo",enabled:true,target_scope:"local"},
    {op:"set",feature:"vendor_refresh",enabled:true},{op:"off"}
  ]);
  assert.match(result.global,/Whole lobby/);
  console.log("PASS: selected/local/all/other requests, shared pickers, per-player/mixed status, global controls and all-off.");
  win.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
