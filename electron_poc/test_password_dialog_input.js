const assert = require('assert');
const path = require('path');
const fs = require('fs');
const {app, BrowserWindow} = require('electron');
setTimeout(() => { console.error('FAIL password dialog test timed out'); app.exit(1); }, 30000).unref();
if (process.env.MSBT_TEST_SOFTWARE_RENDERING === '1') app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const win = new BrowserWindow({show: true, width: Number(process.env.MSBT_TEST_WIDTH || 1100), height: 780,
    webPreferences: {partition: `password-input-${process.pid}`, backgroundThrottling: false}});
  await win.loadFile(path.join(process.env.MSBT_TEST_APP_DIR || __dirname, 'renderer.html'), {query: {nosplash: '1', workspace: process.env.MSBT_TEST_LAYOUT || 'workspace'}});
  console.log('Opening isolated delivery test');
  await win.webContents.executeJavaScript(`(() => {
    bridgeStatus = async () => {};
    window.deliveryCalls = [];
    bridgeAction = async (action, payload) => {
      window.deliveryCalls.push({action, payload});
      return {data: payload.bulk_loot_password === 'test-only-input'
        ? {ok: true, message: 'Fixture delivery accepted'}
        : {ok: false, password_required: true, password_kind: 'bulk_loot'}};
    };
    ensureLiveSdkReady = async () => ({ok: true});
    startSerialDeliveryProgressWatch = () => {};
    window.confirm = () => { throw Error('Delivery must not open an OS confirmation'); };
    const originalRequest = requestBackpackPassword;
    requestBackpackPassword = kind => (window.passwordResult = originalRequest(kind));
    if (${Boolean(process.env.MSBT_TEST_SAVED_ITEMS)}) {
      savedDeliveryEntries = () => [{name: 'Password input fixture', serial: Array(71).fill('@UTest').join('\\n')}];
      bookmarkInvalidSerialLines = () => [];
      window.savedDeliveryResult = sendBookmarkSerial('local');
      return;
    }
    if (${Boolean(process.env.MSBT_TEST_CATALOG)}) {
      switchTab('bl4-codes');
      bl4SelectedEntries = () => Array.from({length: 71}, (_, i) => ({id: String(i), name: 'Fixture', serial: '@UTest'}));
      bl4ValidSerialEntries = rows => rows;
      els.bl4OverrideLevel.value = 'false';
      window.catalogStart = sendBl4Serial('local');
      return;
    }
    window.msbtAfkRender({afk_lobby: {enabled: false, history: [],
      loot_modes: ['all', 'random70'], random_count_supported: true,
      bulk_loot_password_required: true, guaranteed_loot_supported: true}});
    document.getElementById('afkRandomCount').value = '500';
    document.getElementById('afkCodes').value = '@UTest';
    document.getElementById('afkStart').click();
  })()`);
  if (process.env.MSBT_TEST_SAVED_ITEMS) {
    const send = await win.webContents.executeJavaScript(`(() => {
      const r = document.querySelector('#savedDeliveryConfirmDialog button[type=submit]').getBoundingClientRect();
      return {x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)};
    })()`);
    win.webContents.sendInputEvent({type: 'mouseDown', ...send, button: 'left', clickCount: 1});
    win.webContents.sendInputEvent({type: 'mouseUp', ...send, button: 'left', clickCount: 1});
  }
  if (process.env.MSBT_TEST_CATALOG) {
    await win.webContents.executeJavaScript('window.catalogStart');
    await win.webContents.executeJavaScript('confirmBl4InlineDelivery()');
  }
  await new Promise(resolve => setTimeout(resolve, 300));
  const state = await win.webContents.executeJavaScript(`(() => {
    const d = document.getElementById('backpackPasswordDialog');
    return [...d.querySelectorAll('h3,label,input,button')].map(el => {
      const r = el.getBoundingClientRect(), s = getComputedStyle(el);
      return {tag: el.tagName, width: r.width, height: r.height, x: r.x, y: r.y,
        display: s.display, visibility: s.visibility, color: s.color, background: s.backgroundColor,
        hit: document.elementFromPoint(r.x+r.width/2,r.y+r.height/2) === el};
    });
  })()`);
  console.log(JSON.stringify(state));
  fs.mkdirSync(path.join(__dirname, '..', 'work'), {recursive: true});
  fs.writeFileSync(path.join(__dirname, '..', 'work', 'password-dialog.png'), (await win.webContents.capturePage()).toPNG());
  assert(state.every(el => el.width > 0 && el.height > 0), 'All password controls must be visible');
  assert(state.filter(el => ['INPUT','BUTTON'].includes(el.tag)).every(el => el.hit), 'Controls must receive pointer input');
  await win.webContents.insertText('test-only-input');
  assert(await win.webContents.executeJavaScript("document.querySelector('#backpackPasswordDialog input').value === 'test-only-input'"), 'Typing must reach password input');
  assert(await win.webContents.executeJavaScript("document.activeElement === document.querySelector('#backpackPasswordDialog input')"), 'Password input must keep focus');
  win.webContents.sendInputEvent({type: 'keyDown', keyCode: 'ESCAPE'});
  win.webContents.sendInputEvent({type: 'keyUp', keyCode: 'ESCAPE'});
  const result = await win.webContents.executeJavaScript('window.passwordResult');
  assert.strictEqual(result, null);
  assert.strictEqual(await win.webContents.executeJavaScript('window.deliveryCalls.length'), 1, 'Cancel must not resend');
  await win.webContents.executeJavaScript("window.passwordResult = requestBackpackPassword('bulk_loot'); void 0;");
  const cancel = await win.webContents.executeJavaScript(`(() => {
    const r = document.querySelector('#backpackPasswordDialog button[type=button]').getBoundingClientRect();
    return {x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)};
  })()`);
  win.webContents.sendInputEvent({type: 'mouseDown', ...cancel, button: 'left', clickCount: 1});
  win.webContents.sendInputEvent({type: 'mouseUp', ...cancel, button: 'left', clickCount: 1});
  assert.strictEqual(await win.webContents.executeJavaScript('window.passwordResult'), null);
  await win.webContents.executeJavaScript("window.authorizedResult = runAction('give_serial', {serial_text: Array(71).fill('@UTest').join('\\n')}, null); void 0;");
  await new Promise(resolve => setTimeout(resolve, 50));
  await win.webContents.insertText('test-only-input');
  const authorize = await win.webContents.executeJavaScript(`(() => {
    const r = document.querySelector('#backpackPasswordDialog button[type=submit]').getBoundingClientRect();
    return {x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)};
  })()`);
  win.webContents.sendInputEvent({type: 'mouseDown', ...authorize, button: 'left', clickCount: 1});
  win.webContents.sendInputEvent({type: 'mouseUp', ...authorize, button: 'left', clickCount: 1});
  assert(await win.webContents.executeJavaScript('(async () => (await window.authorizedResult).data.ok)()'));
  assert.strictEqual(await win.webContents.executeJavaScript('window.deliveryCalls.length'), 3, 'Authorize retries exactly once');
  assert(await win.webContents.executeJavaScript("!JSON.stringify(localStorage).includes('test-only-input')"), 'No credential storage');
  await win.webContents.executeJavaScript("window.confirmationResult = requestSavedDeliveryConfirmation('Cancel fixture delivery?'); void 0;");
  win.webContents.sendInputEvent({type: 'keyDown', keyCode: 'ESCAPE'});
  win.webContents.sendInputEvent({type: 'keyUp', keyCode: 'ESCAPE'});
  assert.strictEqual(await win.webContents.executeJavaScript('window.confirmationResult'), false);
  assert.strictEqual(await win.webContents.executeJavaScript('window.deliveryCalls.length'), 3, 'Confirmation cancellation must not send');
  console.log('PASS delivery prompt, visible controls, typing, Escape and Cancel click');
  win.destroy(); app.exit(0);
}).catch(error => {console.error(error); app.exit(1);});
