"use strict";
const assert = require("assert");
const path = require("path");
const {app,BrowserWindow} = require("electron");

app.whenReady().then(async () => {
  const win=new BrowserWindow({show:false,width:1400,height:1000,
    webPreferences:{partition:`finder-test-${process.pid}`,backgroundThrottling:false}});
  const receipts=[];
  for(const workspace of ["workspace","classic"]) {
    await win.loadFile(path.join(__dirname,"renderer.html"),{query:{nosplash:"1",workspace}});
    const result=await win.webContents.executeJavaScript(`(async()=>{
      bridgeStatus=async()=>{};
      const actions=[];runAction=(...args)=>{actions.push(args);throw Error("Search must not execute game actions");};
      const before=collectAppFinderEntries();
      const offlineFeatures=Object.keys(FARMING_LAB_FEATURES).every(feature=>before.some(e=>e.id==="feature:"+feature));
      syncFarmingLabStatus({farming_lab:{features:Object.fromEntries(Object.entries(FARMING_LAB_FEATURES).map(([id,value])=>[id,{label:value.label,enabled:false,error:""}]))}});
      const indexed=collectAppFinderEntries();
      const routes=[];
      for(const [id,value] of Object.entries(FARMING_LAB_FEATURES)) {
        window.switchTab("updates");
        document.querySelectorAll(".tab-panel details").forEach(d=>d.open=false);
        renderElectronAppFinder(value.label);
        const first=document.querySelector("#appFinderResults button");
        const exact=first?.textContent.startsWith(value.label);
        first?.click();await new Promise(r=>setTimeout(r,90));
        const node=document.getElementById("farmingLab_"+id);
        routes.push({id,exact,visible:node.getBoundingClientRect().height>0,
          flashed:node.classList.contains("app-finder-flash"),panel:node.closest("[data-msbt-panel]").dataset.msbtPanel});
      }
      const queries=["godmode","invincible","inf ammo","long press skill","skill cool down","cooldown skill","infinite glide","vendor restock","repkit cooldown","repkiit cooldown","repair kit cooldown","100% Drop Rate On","Turn All Farming Controls Off"];
      const matches=queries.map(query=>{
        renderElectronAppFinder(query);
        return {query,titles:[...document.querySelectorAll("#appFinderResults button")].map(b=>b.firstChild.textContent)};
      });
      const repair=indexed.find(e=>e.title==="Repair Kit Cooldown (s)");
      jumpElectronAppFinder(repair);await new Promise(r=>setTimeout(r,90));
      const repairVisible=document.getElementById("combatRepairCooldown").getBoundingClientRect().height>0;
      renderElectronAppFinder("unmatched-zzzzzz");
      return {offlineFeatures,routes,matches,repairVisible,actions,entryCount:indexed.length,
        emptyHidden:document.getElementById("appFinderResults").hidden};
    })()`);
    assert(result.offlineFeatures,"All 14 lab features are searchable without game status");
    assert(result.routes.every(r=>r.exact&&r.visible&&r.flashed),JSON.stringify(result.routes));
    assert(result.matches.every(m=>m.titles.length),JSON.stringify(result.matches));
    assert(result.matches.find(m=>m.query==="godmode").titles[0]==="God Mode");
    assert(result.matches.find(m=>m.query==="repkiit cooldown").titles[0]==="Repair Kit Cooldown (s)");
    assert(result.repairVisible&&result.emptyHidden);assert.deepStrictEqual(result.actions,[]);
    receipts.push({workspace,entries:result.entryCount,featureRoutes:result.routes.length,queries:result.matches.length});
  }
  console.log("PASS feature search: "+JSON.stringify(receipts));
  win.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
