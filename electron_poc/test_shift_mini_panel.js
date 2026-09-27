// Usage: electron test_shift_mini_panel.js <extracted UX directory> <rebuilt controller>
const {app, BrowserWindow} = require('electron');
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const assert = require('assert');
app.whenReady().then(async () => {
  const ux = path.resolve(process.argv[2]);
  const controller = fs.readFileSync(process.argv[3], 'utf8');
  const fixture = path.resolve('../output/azalea-review/build/mini-panel-fixture.html');
  const html = fs.readFileSync(path.join(ux, 'dashboard.html'), 'utf8')
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace('<head>', `<head><base href="${pathToFileURL(ux + path.sep).href}">`);
  fs.writeFileSync(fixture, html);
  const win = new BrowserWindow({show:false, width:1600, height:900, webPreferences:{contextIsolation:true}});
  await win.loadFile(fixture);
  await win.webContents.executeJavaScript(fs.readFileSync(path.join(ux,'libs/jquery-3.4'),'utf8') + ';void 0;');
  await win.webContents.executeJavaScript(`
    window.engine={on:()=>{},off:()=>{},call:()=>{},trigger:()=>{}};
    window.friends_model={receivedRequestsList:[],allInvites:[]};
    window.friends_controller={showSuccessMessage:()=>{},hideSuccessMessage:()=>{}};
    for(const key of ['FRIENDS_LOAD_REQUEST_LIST_RESPONSE','FRIENDS_LOAD_REQUEST_LIST_CALL']) window[key]=key;
  `);
  const start = controller.indexOf('var ShiftFriendAutomation = (function ()');
  const end = controller.indexOf('window.ShiftMiniPanel = ShiftMiniPanel;', start) + 'window.ShiftMiniPanel = ShiftMiniPanel;'.length;
  assert(start>0 && end>start);
  assert(controller.includes('$(friends_controller.requests.ids.miniPanelToggleBtn).on("click", ShiftMiniPanel.toggle)'));
  await win.webContents.executeJavaScript(controller.slice(start,end) + ';void 0;');
  await win.webContents.executeJavaScript(fs.readFileSync('../tools/afk_lobby/shift_float.js','utf8'));
  await new Promise(resolve=>setTimeout(resolve,900));
  const result = await win.webContents.executeJavaScript(`(() => {
    const visible=id=>{const el=document.getElementById(id);const r=el.getBoundingClientRect();return getComputedStyle(el).display!=='none' && r.width>0 && r.height>0;};
    const checks=[]; const check=(name,ok)=>{checks.push({name,ok});if(!ok)throw Error(name);};
    $('#friends_mini_panel_toggle_btn').on('click',ShiftMiniPanel.toggle);
    check('floating active',document.documentElement.classList.contains('msbt-shift-floating'));
    for(let i=0;i<2;i++) {
      ShiftMiniPanel.hide();
      document.getElementById('friends_mini_panel_toggle_btn').click();
      check('Mini Panel opens mode '+i,visible('shift_mini_panel'));
      document.getElementById('shift_mini_panel_customize_btn').click();
      check('Customize opens mode '+i,visible('shift_settings_overlay'));
      ShiftMiniPanel.setChoice('friendRequestMode','ignore');
      check('setting applies mode '+i,ShiftFriendAutomation.getSettings().friendRequestMode==='ignore');
      ShiftMiniPanel.closeSettings(false);
      check('Customize closes mode '+i,!visible('shift_settings_overlay'));
      document.getElementById('shift_mini_panel_close_btn').click();
      check('Mini Panel closes mode '+i,!visible('shift_mini_panel'));
      document.getElementById('msbt-shift-float-toggle').click();
    }
    Array.from(document.querySelectorAll('#msbt-shift-float-bar button')).find(b=>b.textContent==='Manage SHiFT').click();
    check('Manage SHiFT opens panel',visible('shift_mini_panel'));
    check('Manage preserves floating layout',document.documentElement.classList.contains('msbt-shift-floating'));
    return checks;
  })()`);
  fs.writeFileSync(path.join(path.dirname(fixture),'mini-panel-test.json'),JSON.stringify(result,null,2));
  console.log('PASS '+result.length+' Mini Panel DOM checks using actual upstream panel code, HTML and floating wrapper. Native Cohtml remains a live test.');
  win.destroy(); app.quit();
}).catch(e=>{console.error(e);app.exit(1);});

