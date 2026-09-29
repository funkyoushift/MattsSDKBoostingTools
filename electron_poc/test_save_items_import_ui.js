const {app,BrowserWindow,dialog}=require('electron');const fs=require('fs'),os=require('os'),path=require('path'),assert=require('assert/strict');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'msbt-save-import-'));app.setPath('userData',temp);app.disableHardwareAcceleration();global.fetch=async()=>{throw Error('Test offline');};
const fixture=path.join(temp,'sample.yaml');fs.writeFileSync(fixture,`state:
  char_name: Test Rafa
  experience: [{type: Character, level: 70}]
  inventory:
    items:
      backpack:
        a: {serial: '@Uabc'}
        b: {serial: '@Uabc'}
      lost_loot:
        c: {serial: '@ULost'}
    equipped_inventory:
      equipped:
        d: {serial: '@Uequip'}
`);
const binary=path.join(temp,'sample.sav');
const encrypted=require('child_process').spawnSync(process.execPath,[path.resolve(__dirname,'../external_app/v22_parts_codes_fixed/matt_editor_blcrypt.js')],{env:{...process.env,ELECTRON_RUN_AS_NODE:'1'},input:JSON.stringify({command:'encrypt',steamid:'76561198894205533',yaml_content:fs.readFileSync(fixture,'utf8')}),encoding:'utf8'});
const encoded=JSON.parse(encrypted.stdout);assert.equal(encoded.success,true);fs.writeFileSync(binary,Buffer.from(encoded.sav_data||encoded.encrypted,'base64'));
let picks=0;dialog.showOpenDialog=async()=>({canceled:false,filePaths:[++picks<=2?fixture:binary]});
require('./main');
app.whenReady().then(async()=>{
 const win=BrowserWindow.getAllWindows()[0];win.hide();if(win.webContents.isLoading())await new Promise(r=>win.webContents.once('did-finish-load',r));
 const result=await win.webContents.executeJavaScript(`(async()=>{
  const check=(v,m)=>{if(!v)throw Error(m)},$=id=>document.getElementById(id);
  await loadSerialBookmarks();$('saveItemsImportOpen').click();$('saveItemsChoose').click();
  for(let i=0;i<100&&$('saveItemsChoose').disabled;i++)await new Promise(r=>setTimeout(r,20));
  check(!$('saveItemsDestination').hidden,'preview visible');check($('saveItemsPreview').textContent.includes('2 backpack + 1 equipped'),'scope');
  check($('saveItemsNew').value==='Test Rafa - Level 70','suggested folder');$('saveItemsCommit').click();
  for(let i=0;i<100&&$('saveItemsCommit').disabled;i++)await new Promise(r=>setTimeout(r,20));
  await loadSerialBookmarks();check(state.bookmarks.length===3,'saved three items');check(!state.bookmarks.some(x=>x.serial==='@ULost'),'lost loot excluded');
  $('saveItemsImportOpen').click();$('saveItemsChoose').click();for(let i=0;i<100&&$('saveItemsChoose').disabled;i++)await new Promise(r=>setTimeout(r,20));
  $('saveItemsMode').value='existing';$('saveItemsMode').dispatchEvent(new Event('change'));$('saveItemsExisting').value='Test Rafa - Level 70';$('saveItemsSkip').checked=true;$('saveItemsCommit').click();for(let i=0;i<100&&$('saveItemsCommit').disabled;i++)await new Promise(r=>setTimeout(r,20));
  await loadSerialBookmarks();check(state.bookmarks.length===3,'skip duplicates preserves existing');$('saveItemsChoose').click();for(let i=0;i<100&&$('saveItemsChoose').disabled;i++)await new Promise(r=>setTimeout(r,20));
  check(!$('saveItemsAccountRow').hidden,'encrypted file requests account');$('saveItemsAccount').value='76561198894205533';$('saveItemsDecode').click();for(let i=0;i<200&&$('saveItemsDecode').disabled;i++)await new Promise(r=>setTimeout(r,20));
  check(!$('saveItemsDestination').hidden,'encrypted save decoded locally');check($('saveItemsPreview').textContent.includes('2 backpack + 1 equipped'),'encrypted scope');return $('saveItemsPreview').textContent;
 })()`);
 assert.equal(fs.readFileSync(fixture,'utf8').includes('@ULost'),true);console.log('PASS real main/preload/UI import and disk reload: '+result);win.destroy();app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});
