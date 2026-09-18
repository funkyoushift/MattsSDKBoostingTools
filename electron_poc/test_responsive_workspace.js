"use strict";
const assert = require("assert");
const path = require("path");
const fs = require("fs");
const { app, BrowserWindow } = require("electron");
const tabs = ["boosting", "quick-menu", "serial-tools", "inventory", "bl4-codes", "matt-editor", "item-pool", "dev-spawner", "hoard-builder", "map-travel", "player-movement", "combat-vehicle", "activity", "mobile-gateway", "report", "updates"];
const sizes = [[360,360],[360,480],[480,700],[640,480],[800,600],[853,720],[960,1000],[1031,617],[1280,720],[1920,1080],[2560,1440],[3840,2160]];
app.whenReady().then(async () => {
  // No preload / IPC / game bridge. Tests operate on local renderer controls only.
  const win = new BrowserWindow({show:false,width:1280,height:820,webPreferences:{partition:`workspace-test-${process.pid}`,contextIsolation:true,nodeIntegration:false,backgroundThrottling:false}});
  const failures = [], receipts = [];
  await win.loadFile(path.join(__dirname,"renderer.html"),{query:{nosplash:"1"}});
  await new Promise(r=>setTimeout(r,350));
  assert.strictEqual(await win.webContents.executeJavaScript('Boolean(window.MsbtWorkspace?.enabled && typeof window.switchTab === "function")'),true,"Workspace bootstrap");
  const catalog = JSON.parse(fs.readFileSync(path.join(__dirname, "dev_spawner_catalog.json"), "utf8"));
  await win.webContents.executeJavaScript(`state.devSpawnerCatalog=${JSON.stringify(catalog)}; populateDevSpawnerCatalog();`);
  const routes = tabs.map(tab => ({tab}));
  const sectionRoutes = await win.webContents.executeJavaScript('Object.entries(window.MsbtWorkspace.sections).flatMap(([tab, sections]) => sections.map(([section]) => ({tab, section})))');
  routes.push(...sectionRoutes);
  for (const [width,height] of sizes) {
    win.setContentSize(width,height);
    await new Promise(r=>setTimeout(r,80));
    for (const {tab, section} of routes) {
      const row = await win.webContents.executeJavaScript(`(async()=>{
        window.switchTab(${JSON.stringify(tab)});
        if (${JSON.stringify(section || "")}) window.MsbtWorkspace.open(${JSON.stringify(tab)}, ${JSON.stringify(section || "")});
        await new Promise(r=>setTimeout(r,20));
        const tab=document.getElementById('tab-'+${JSON.stringify(tab)}), shell=document.querySelector('.tab-shell');
        const rect=tab.getBoundingClientRect(),sr=shell.getBoundingClientRect();
        const primary=tab.querySelector('.dev-spawner-primary');
        const primaryBottom=primary?.getBoundingClientRect().bottom || 0;
        const verticalOverflow=primary ? Math.max(0,...Array.from(primary.children).filter(el=>el.getBoundingClientRect().height>0).map(el=>el.getBoundingClientRect().bottom-primaryBottom)) : 0;
        const overflow=Array.from(tab.querySelectorAll('*')).filter(el=>{
          const r=el.getBoundingClientRect(),s=getComputedStyle(el);
          return r.width>0 && r.height>0 && s.position!=='fixed' && r.right>sr.right+3 && !el.closest('[hidden],.hidden,.workspace-section-hidden');
        }).slice(0,5).map(el=>({id:el.id,cls:String(el.className).slice(0,65),right:Math.round(el.getBoundingClientRect().right)}));
        return {tab:${JSON.stringify(tab)},section:${JSON.stringify(section || "")},width:innerWidth,height:innerHeight,tabWidth:Math.round(rect.width),shellWidth:Math.round(sr.width),shellHeight:Math.round(sr.height),overflow:Math.round(shell.scrollWidth-shell.clientWidth),verticalOverflow:Math.round(verticalOverflow),offenders:overflow};
      })()`);
      receipts.push(row);
      if(row.overflow>3 || row.verticalOverflow>3 || row.shellHeight<100 || row.tabWidth<200) failures.push(row);
    }
  }
  const behavior = await win.webContents.executeJavaScript(`(()=>{
    const w=window.MsbtWorkspace, before=document.getElementById('giveCurrencyBtn');
    w.open('boosting','currency');
    const currencyVisible=before.getBoundingClientRect().height>0;
    const xpHidden=document.getElementById('setLevelBtn').getBoundingClientRect().height===0;
    w.open('boosting','levels');
    const xpVisible=document.getElementById('setLevelBtn').getBoundingClientRect().height>0;
    w.revealPanel(document.querySelector('[data-msbt-panel="boost-currency"]'));
    const finderReveal=before.getBoundingClientRect().height>0;
    const identity=before===document.getElementById('giveCurrencyBtn');
    const ids=Array.from(document.querySelectorAll('[id]')).map(el=>el.id);
    const duplicates=ids.filter((id,i)=>ids.indexOf(id)!==i);
    return {currencyVisible,xpHidden,xpVisible,finderReveal,identity,duplicates};
  })()`);
  assert.deepStrictEqual(behavior,{currencyVisible:true,xpHidden:true,xpVisible:true,finderReveal:true,identity:true,duplicates:[]});
  for(const width of [480,800,960]) {
    win.setContentSize(width,700);
    await win.webContents.executeJavaScript('window.MsbtPanelLayout.applyTextScale(1.4); window.MsbtWorkspace.open("boosting","all");');
    await new Promise(r=>setTimeout(r,80));
    const over=await win.webContents.executeJavaScript('document.querySelector(".tab-shell").scrollWidth-document.querySelector(".tab-shell").clientWidth');
    if(over>3) failures.push({width,scale:1.4,overflow:over});
  }
  // These are real buttons with a stubbed transport; never attach a preload here.
  const dispatch = await win.webContents.executeJavaScript(`(async()=>{
    const calls=[];
    const original=runScopedPlayerAction;
    runScopedPlayerAction=async(action,payload)=>{calls.push({action,payload});return {ok:true};};
    window.MsbtWorkspace.open('boosting','currency');
    document.getElementById('currencyKind').value='eridium';
    document.getElementById('currencyAmount').value='12345';
    document.getElementById('giveCurrencyBtn').click();
    window.MsbtWorkspace.open('boosting','levels');
    document.getElementById('xpTrack').value='player';
    document.getElementById('xpLevel').value='42';
    document.getElementById('setLevelBtn').click();
    runScopedPlayerAction=original;
    return calls;
  })()`);
  assert.deepStrictEqual(dispatch,[{action:'give_currency',payload:{currency_kind:'eridium',amount:12345}},{action:'set_level',payload:{xp_track:'player',level:42}}]);
  fs.mkdirSync(path.join(__dirname,"../output/testing"),{recursive:true});
  fs.writeFileSync(path.join(__dirname,"../output/testing/responsive-workspace-results.json"),JSON.stringify({sizes,tabs,behavior,dispatch,failures,measurements:receipts},null,2));
  await win.webContents.executeJavaScript('(async()=>{ await endWalkthrough({skipped:true}); document.getElementById("mobileAnnounceDismissBtn").click(); window.MsbtPanelLayout.applyTextScale(1); window.MsbtWorkspace.open("dev-spawner", ""); })()');
  for (const width of [480, 960]) {
    win.setContentSize(width, 800);
    await new Promise(r=>setTimeout(r,100));
    await win.webContents.insertCSS('.modal-shell { display: none !important; }');
    const capture = await win.webContents.capturePage();
    fs.writeFileSync(path.join(__dirname, `../output/testing/workspace-spawner-${width}.png`), capture.toPNG());
  }
  console.log(JSON.stringify({measurements:receipts.length,behavior,failures},null,2));
  assert.strictEqual(failures.length,0,"Responsive layout overflows; see results");
  win.destroy(); app.exit(0);
}).catch(e=>{console.error(e);app.exit(1);});
