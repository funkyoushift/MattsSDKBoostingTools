// Usage: electron test_shift_mini_panel.js <extracted UX directory> <rebuilt controller>
const {app, BrowserWindow} = require('electron');
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const assert = require('assert');
app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const ux = path.resolve(process.argv[2]);
  const controller = fs.readFileSync(process.argv[3], 'utf8');
  const fixture = path.resolve(process.argv[4] || '../output/azalea-review/build', 'mini-panel-fixture.html');
  fs.mkdirSync(path.dirname(fixture), {recursive:true});
  const html = fs.readFileSync(path.join(ux, 'dashboard.html'), 'utf8')
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace('<head>', `<head><base href="${pathToFileURL(ux + path.sep).href}">`);
  fs.writeFileSync(fixture, html);
  const win = new BrowserWindow({show:false, width:1600, height:900, webPreferences:{contextIsolation:true,partition:'msbt-shift-test-'+process.pid}});
  const execute = win.webContents.executeJavaScript.bind(win.webContents);
  win.webContents.executeJavaScript = code => execute(`(() => {try {return eval(${JSON.stringify(code)});} catch(e) {return {testError:String(e),stack:e.stack};}})()`).then(value => {
    if(value && value.testError)throw Error(value.stack || value.testError);
    return value;
  });
  await win.loadFile(fixture);
  const jquery = fs.existsSync(path.join(ux,'libs/jquery-3.4.1.min.js')) ? 'libs/jquery-3.4.1.min.js' : 'libs/jquery-3.4';
  await win.webContents.executeJavaScript(fs.readFileSync(path.join(ux,jquery),'utf8') + ';void 0;');
  await win.webContents.executeJavaScript(`
    window.engine={on:()=>{},off:()=>{},call:()=>{},trigger:()=>{}};
    window.testShiftRequests=[];
    window.testShiftStorage={ok:true,service:'msbt-shift-storage',protocol:1,integration:'msbt-shift-20261110',instance:'a'.repeat(32),storageValid:false,storageState:'missing'};
    window.XMLHttpRequest=class {
      open(method,url){this.method=method;this.url=url;this.headers={};}
      setRequestHeader(name,value){this.headers[name]=value;}
      send(body){
        testShiftRequests.push({request:this,body:body?JSON.parse(body):null});
        if(this.method==='GET')this.respond(testShiftStorage);
      }
      respond(data){this.status=200;this.responseText=JSON.stringify(data);if(this.onload)this.onload();if(this.onloadend)this.onloadend();}
    };
    window.friends_model={receivedRequestsList:[],allInvites:[]};
    window.friends_controller={showSuccessMessage:()=>{},hideSuccessMessage:()=>{}};
    window.side_menu_controller={showSideMenu:()=>{},onFriendsClick:()=>{
      document.getElementById('body_container').style.opacity='1'; // Native dashboard show acknowledgement.
      document.getElementById('friends_container').classList.remove('hide');
      for(let el=document.getElementById('friends_container').parentElement;el;el=el.parentElement)el.classList.remove('hide');
    }};
    for(const key of ['FRIENDS_LOAD_REQUEST_LIST_RESPONSE','FRIENDS_LOAD_REQUEST_LIST_CALL']) window[key]=key;
    window.testShiftVisible=id=>{
      const el=typeof id==='string'?document.getElementById(id):id;
      if(!el)return false;
      const r=el.getBoundingClientRect();
      if(r.width<=0 || r.height<=0 || r.bottom<=0 || r.right<=0 || r.top>=innerHeight || r.left>=innerWidth)return false;
      for(let ancestor=el;ancestor;ancestor=ancestor.parentElement){
        const style=getComputedStyle(ancestor);
        if(style.display==='none' || style.visibility==='hidden' || style.visibility==='collapse' || Number(style.opacity)===0)return false;
      }
      return true;
    };
    void 0;
  `);
  const start = controller.indexOf('var ShiftFriendAutomation = (function ()');
  const end = controller.indexOf('window.ShiftMiniPanel = ShiftMiniPanel;', start) + 'window.ShiftMiniPanel = ShiftMiniPanel;'.length;
  assert(start>0 && end>start);
  assert(controller.includes('$(friends_controller.requests.ids.miniPanelToggleBtn).on("click", ShiftMiniPanel.toggle)'));
  await win.webContents.executeJavaScript(controller.slice(start,end) + ';void 0;');
  await win.webContents.executeJavaScript(fs.readFileSync('../tools/afk_lobby/shift_float.js','utf8'));
  await new Promise(resolve=>setTimeout(resolve,900));
  const result = await win.webContents.executeJavaScript(`(() => {
    const visible=window.testShiftVisible;
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
    ShiftMiniPanel.openSettings();
    ShiftMiniPanel.openProtectedList();
    check('native protected editor opens',visible('msbt_native_protection_panel'));
    const addInput=document.getElementById('shift_settings_protected_add_input');
    const search=document.getElementById('shift_settings_protected_search');
    const addButton=document.getElementById('shift_settings_protected_add_btn');
    const feedback=()=>document.getElementById('shift_settings_protected_feedback').textContent;
    const names=()=>ShiftFriendAutomation.getProtectedNames();
    check('add input precedes search',!!(addInput.compareDocumentPosition(search)&Node.DOCUMENT_POSITION_FOLLOWING));
    for(const id of [addInput.id,search.id]) {
      const label=document.querySelector('label[for="'+id+'"]');
      check('persistent label '+id,!!label && label.getBoundingClientRect().height>0);
    }
    const initialCount=names().length;
    search.value='search-is-not-a-new-name';search.dispatchEvent(new Event('input'));
    addButton.click();
    check('blank add gives feedback',feedback().includes('Enter a SHiFT'));
    check('search never adds a name',names().length===initialCount);
    addInput.value='  revcashmoney  ';addButton.click();
    check('Add inserts trimmed name',names().includes('revcashmoney'));
    check('new name visible despite previous filter',search.value==='' && document.getElementById('shift_settings_protected_list').textContent.includes('revcashmoney'));
    check('successful add has save guidance',feedback().includes('Review the list, then choose Save'));
    addInput.value='REVCASHMONEY';addButton.click();
    check('duplicate gives feedback without duplicate',feedback().includes('Already protected') && names().length===initialCount+1);
    addInput.value='keyboard-example';addInput.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));
    check('Enter adds name',names().includes('keyboard-example'));
    addInput.value='<b>literal-name</b>';addButton.click();
    check('feedback treats name as text',feedback().includes('<b>literal-name</b>') && !document.querySelector('#shift_settings_protected_feedback b'));
    check('no write before review and Save',!testShiftRequests.some(r=>r.request.method==='POST'));
    return checks;
  })()`);
  await win.webContents.executeJavaScript(`
    ShiftMiniPanel.hide();
    document.getElementById('msbt-shift-size-regular').click();
    void 0;
  `);
  await win.webContents.executeJavaScript(`new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))`);
  const captureVisibility=await win.webContents.executeJavaScript(`(() => {
    const ids=['msbt_native_protection_panel','shift_settings_protected_add_input','shift_protection_review','msbt_native_protection_save'];
    for(const id of ids)if(!testShiftVisible(id))throw Error('Capture target is not visible: '+id);
    const root=document.getElementById('body_container');
    if(document.documentElement.classList.contains('msbt-shift-floating'))throw Error('Capture retained compact layout');
    const metrics=['shift_settings_protected_add_input','shift_settings_protected_add_btn','msbt_native_protection_save'].map(id=>{
      const el=document.getElementById(id),r=el.getBoundingClientRect(),font=parseFloat(getComputedStyle(el).fontSize);
      const effectiveFont=font*r.height/el.offsetHeight;
      if(effectiveFont<14 || r.height<24)throw Error('Control is too small at Regular size: '+id+' font='+effectiveFont+' height='+r.height);
      return {id,font:effectiveFont,width:r.width,height:r.height};
    });
    return {ids,transform:getComputedStyle(root).transform,metrics};
  })()`);
  fs.writeFileSync(path.join(path.dirname(fixture),'protected-friends.png'), (await win.webContents.capturePage()).toPNG());
  await win.webContents.executeJavaScript(`
    ShiftMiniPanel.setStorageMode('sdk');
    ShiftMiniPanel.openSettings();
    ShiftMiniPanel.openProtectedList();
    ShiftMiniPanel.requestSDKSettings();
    testShiftRequests.length=0;
    ShiftMiniPanel.saveSettingsNow();
    if(testShiftRequests.some(r=>r.request.method==='POST'))throw Error('Unreviewed first-run save transmitted a write');
    var review=document.getElementById('shift_protection_review');
    if(!testShiftVisible(review))throw Error('Review control is not visible');
    review.click();
    ShiftMiniPanel.saveSettingsNow();
  `);
  await new Promise(resolve=>setTimeout(resolve,500));
  const storage = await win.webContents.executeJavaScript(`(() => {
    const writes=testShiftRequests.filter(r=>r.request.method==='POST');
    if(writes.length!==1)throw Error('Expected exactly one explicit storage write');
    const payload=writes[0].body;
    if(payload.initialize!==true || payload.reviewed!==true)throw Error('Reviewed first-run intent missing');
    if(ShiftMiniPanel.protectionReady())throw Error('Protection ready before save acknowledgement');
    testShiftStorage=Object.assign({},testShiftStorage,{protectedPlayers:payload.n,reviewed:true,storageValid:true,storageState:'valid',settings:{}});
    writes[0].request.respond(Object.assign({},testShiftStorage,{saved:true}));
    if(!ShiftMiniPanel.protectionReady())throw Error('Matching reviewed save did not enable protection');
    ShiftFriendAutomation.addProtectedName('DOM-regression-example');
    if(ShiftMiniPanel.protectionReady())throw Error('Unsaved edit left bulk removal enabled');
    if(document.getElementById('shift_protection_review').getAttribute('aria-pressed')!=='false')throw Error('Edit did not reset review');
    return {uncheckedSaveBlocked:true,reviewControlVisible:true,explicitInitialization:true,readbackRequired:true,editsResetReview:true};
  })()`);
  fs.writeFileSync(path.join(path.dirname(fixture),'mini-panel-test.json'),JSON.stringify({checks:result,storage,captureVisibility},null,2));
  console.log('PASS '+result.length+' Mini Panel DOM checks and 5 protected-list setup/save checks. Native Cohtml remains a live test.');
  win.destroy(); app.quit();
}).catch(e=>{console.error(e);app.exit(1);});

