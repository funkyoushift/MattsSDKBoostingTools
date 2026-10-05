const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { app, BrowserWindow } = require('electron');
const timeout = setTimeout(() => { console.error('Credits check timed out'); app.exit(1); }, 20000);
app.whenReady().then(async () => {
  const classic = process.env.MSBT_CREDITS_CLASSIC === '1';
  const win = new BrowserWindow({ show: false, width: classic ? 980 : 1280, height: 800, webPreferences: { partition: 'credits-check', contextIsolation: true, backgroundThrottling: false, offscreen: true } });
  await win.loadFile(path.join(__dirname, 'renderer.html'), { query: { nosplash: '1', workspace: classic ? 'classic' : 'default' } });
  await new Promise(resolve => setTimeout(resolve, 900));
  const result = await win.webContents.executeJavaScript(`(() => {
    const splash = document.getElementById("msbtBootSplash"); if (splash) splash.style.display = "none";
    const opened = [];
    window.msbt = { openExternal: url => opened.push(url) };
    document.querySelector('.tab-bar [data-tab="credits"]').click();
    const tab = document.getElementById('tab-credits');
    const link = tab.querySelector('[data-credit-link]');
    link.click();
    const details = tab.querySelector('details'); details.open = true;
    const notices = details.querySelector('pre').textContent;
    details.open = false;
    return { active: tab.classList.contains('active'), opened, expected: link.href,
      width: tab.getBoundingClientRect().width, height: tab.getBoundingClientRect().height,
      names: tab.innerText, notices,
      sidebar: !!document.querySelector('#workspaceNavigation [data-workspace-tab="credits"]'),
      duplicateIds: [...document.querySelectorAll('[id]')].map(e=>e.id).filter((id,i,all)=>all.indexOf(id)!==i) };
  })()`);
  assert(result.active, 'Credits tab opens');
  if (!classic) assert(result.sidebar, 'Credits is available in workspace navigation');
  assert(result.width > 300 && result.height > 100, 'Credits has usable dimensions');
  assert.deepStrictEqual(result.opened, [result.expected], 'Links use system browser bridge');
  for (const name of ['Mattmab', 'Squ1ggs', 'Azalea', 'Pyrex', 'Bonk Utilities', 'apple1417', 'Ynot', 'Funk’s Borderlands Trading Hub']) assert(result.names.includes(name), name);
  assert.strictEqual(result.notices, fs.readFileSync(path.join(__dirname,'../docs/THIRD_PARTY_NOTICES.txt'),'utf8').replace(/\r\n/g, '\n'), 'Notices available verbatim offline');
  assert.deepStrictEqual(result.duplicateIds, [], 'No duplicate IDs');
  await new Promise(resolve => setTimeout(resolve, 1100));
  await win.webContents.executeJavaScript('endWalkthrough({ skipped: true, quiet: true }); switchTab("credits");');
  await new Promise(resolve => setTimeout(resolve, 1100));
  assert(await win.webContents.executeJavaScript('document.getElementById("tab-credits").classList.contains("active")'), "Credits remains selected");
  if (process.env.MSBT_CREDITS_SCREENSHOT) fs.writeFileSync(process.env.MSBT_CREDITS_SCREENSHOT, (await win.webContents.capturePage()).toPNG());
  console.log('PASS Credits navigation, browser links, contributors, offline notices and layout');
  clearTimeout(timeout); app.exit(0);
}).catch(error => { console.error(error); clearTimeout(timeout); app.exit(1); });
