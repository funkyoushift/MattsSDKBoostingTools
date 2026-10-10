"use strict";
// Real renderer, isolated settings, no preload/IPC/game connection.
const { app, BrowserWindow } = require("electron");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const win = new BrowserWindow({show:false, width:1360, height:1000, webPreferences:{partition:`navigation-${process.pid}`, backgroundThrottling:false}});
  const errors = [];
  win.webContents.on("console-message", event => {
    // Startup status has no transport in this deliberately preload-free fixture.
    if (event.level === "error" && /Uncaught/.test(event.message) && !/reading 'bridgeRequest'/.test(event.message)) errors.push(event.message);
  });
  await win.loadFile(path.join(__dirname, "renderer.html"), {query:{nosplash:"1", workspace:"classic"}});
  const originalControls = await win.webContents.executeJavaScript(`Array.from(document.querySelectorAll('button[id],input[id],select[id],textarea[id]')).map(n=>n.id)`);
  await win.loadFile(path.join(__dirname, "renderer.html"), {query:{nosplash:"1"}});
  const missingControls = await win.webContents.executeJavaScript(`${JSON.stringify(originalControls)}.filter(id=>!document.getElementById(id))`);
  assert.deepEqual(missingControls, [], "Reorganization must preserve every existing identified control");
  await win.webContents.executeJavaScript(`(async()=>{
    await endWalkthrough({skipped:true}); bridgeStatus=async()=>{};
    window.navigationActions=[]; runAction=async(...args)=>{navigationActions.push(args); return {ok:true};};
    document.getElementById('mobileAnnounceDismissBtn').click();
  })()`);
  await win.webContents.insertCSS('.modal-shell, .msbt-boot-splash { display:none !important; }');
  const result = await win.webContents.executeJavaScript(`(async()=>{
    const w=window.MsbtWorkspace;
    const routes=[['boosting','Home','overview'],...w.groups.flatMap(g=>g[1])];
    const checks=routes.map(([tab,label,section])=>{
      w.open(tab,section);
      const active=document.querySelector('.tab-panel.active');
      return {tab,section:section||'',label,active:active.id==='tab-'+tab,
        title:active.querySelector('.workspace-heading h2').textContent,
        nav:document.querySelector('.workspace-sidebar [aria-current="page"]')?.textContent};
    });
    const homes={
      max_all:'boost-max-all', reset_skills:'boost-levels', devperk_7:'boost-drops',
      devperk_3:'boost-cheats', chaos_drop_backpack:'boost-drops', devperk_4:'boost-unlocks',
      fog_of_war_clear:'travel-reveal'
    };
    const placements=Object.entries(homes).every(([action,home])=>document.querySelector('[data-action="'+action+'"]').closest('[data-msbt-panel]').dataset.msbtPanel===home);
    const controls=['thirdPersonToggleBtn','instantDropsToggleBtn','instantHoldsToggleBtn','shinyDeliverBtn','combatApplyBtn'];
    const search=controls.map(id=>{
      w.open('boosting','overview');
      const node=document.getElementById(id), p=node.closest('[data-msbt-panel]');
      w.open(p.closest('.tab-panel').id.replace('tab-','')); w.revealPanel(p);
      return {id,visible:node.getBoundingClientRect().height>0};
    });
    w.open('map-travel','locations'); w.open('boosting','players');
    document.querySelector('[aria-label="Back to previous page"]').click();
    const back=document.querySelector('.tab-panel.active .workspace-heading h2').textContent==='Saved Locations';
    w.open('boosting','overview');
    const homeHasActions=!!document.querySelector('[data-msbt-panel="boost-essentials"] [data-action]');
    const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);
    return {checks,placements,search,back,homeHasActions,duplicateIds:ids.filter((id,i)=>ids.indexOf(id)!==i),actions:navigationActions};
  })()`);
  assert(result.checks.every(r=>r.active && r.title===r.label && r.nav===r.label), JSON.stringify(result.checks));
  assert(result.placements && result.search.every(r=>r.visible) && result.back && !result.homeHasActions, JSON.stringify(result));
  assert.deepEqual(result.duplicateIds, []); assert.deepEqual(result.actions, []); assert.deepEqual(errors, []);
  for (const width of [360, 800, 1360]) {
    win.setContentSize(width, 800);
    const layout = await win.webContents.executeJavaScript(`(async()=>{
      state.quickMenuSnapshot={catalog:{},layout:{pages:Array.from({length:5},()=>Array(21).fill(null))}};
      renderQuickMenuEditor(); MsbtWorkspace.open('quick-menu');
      const menu=document.querySelector('.workspace-app-menu'); menu.open=true;
      const view=document.querySelector('[data-msbt-view-menu]'); view.open=true;
      await new Promise(r=>setTimeout(r,80));
      const rect=document.querySelector('.workspace-app-menu-body').getBoundingClientRect();
      const shell=document.querySelector('.tab-shell');
      const result={slots:document.querySelectorAll('.quick-menu-slot').length,
        overflow:shell.scrollWidth-shell.clientWidth,menuLeft:rect.left,menuRight:rect.right,viewport:innerWidth,
        viewAvailable:!!document.getElementById('viewAppOpacity')};
      menu.open=false;view.open=false;return result;
    })()`);
    assert(layout.slots === 21 && layout.overflow <= 3 && layout.menuLeft >= -1 && layout.menuRight <= layout.viewport + 1 && layout.viewAvailable, JSON.stringify({width,...layout}));
  }
  win.setContentSize(1360,1000);
  const dir = path.join(__dirname, "../output/testing/workspace-navigation"); fs.mkdirSync(dir,{recursive:true});
  // Capture every user-facing page for a visual review, including fixed-layout tools.
  for (const row of result.checks) {
    await win.webContents.executeJavaScript(`MsbtWorkspace.open(${JSON.stringify(row.tab)},${JSON.stringify(row.section)});`);
    await win.webContents.capturePage(undefined,{stayHidden:true,stayAwake:true});
    await new Promise(r=>setTimeout(r,160));
    const active = await win.webContents.executeJavaScript(`document.querySelector('.workspace-sidebar [aria-current="page"]')?.textContent`);
    assert.equal(active, row.label, "Selected page must remain stable after painting");
    await win.webContents.capturePage(undefined,{stayHidden:true,stayAwake:true});
    await new Promise(r=>setTimeout(r,80));
    fs.writeFileSync(path.join(dir,`${row.tab}-${row.section || 'main'}.png`),(await win.webContents.capturePage(undefined,{stayHidden:true,stayAwake:true})).toPNG());
  }
  fs.writeFileSync(path.join(dir,"receipt.json"),JSON.stringify(result,null,2));
  console.log(`PASS ${result.checks.length} page routes, control homes, target-return navigation, unique IDs and zero game actions. Captures: ${dir}`);
  win.destroy(); app.exit(0);
}).catch(error=>{console.error(error); app.exit(1);});
