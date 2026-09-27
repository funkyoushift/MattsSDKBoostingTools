const assert=require('assert/strict');const path=require('path');const {app,BrowserWindow}=require('electron');
app.disableHardwareAcceleration();app.on('window-all-closed',()=>{});
app.whenReady().then(async()=>{
 for(const file of ['renderer.html','../mobile_controller/app/src/main/assets/index.html']){
  const win=new BrowserWindow({show:false,width:420,height:900,webPreferences:{sandbox:false,partition:'locale-'+Math.random()}});
  await win.loadFile(path.join(__dirname,file),{query:{nosplash:'1'}});
  const result=await win.webContents.executeJavaScript(`(()=>{
   const check=(v,m)=>{if(!v)throw Error(m)};const lang=window.msbtI18n;
   const controls=[...document.querySelectorAll('[data-afk-boost],[data-afk]')];const before=controls.map(el=>el.checked);
   const codes=document.getElementById('afkCodes')||document.getElementById('afkPool');codes.value='@UCaseSensitiveCode';
   for(const locale of lang.locales){lang.setLanguage(locale);check(document.documentElement.lang===locale,'html lang');for(const values of Object.values(lang.rows))check(values.length===lang.locales.length,'missing language');check(!lang.t('counts',{session:2,lifetime:15}).includes('{'),'placeholder');}
   for(const [locale,label] of [['de','AFK-Lobby starten'],['nl','AFK-lobby starten']]){lang.setLanguage(locale);check(document.querySelector('[data-i18n="start"]').textContent===label,'German/Dutch label');check(document.querySelector('[data-language-selector]').value===locale,'selector choice');}
   lang.setLanguage('es');check(document.querySelector('[data-i18n="start"]').textContent==='Iniciar sala AFK','Spanish label');
   check(localStorage.getItem('msbt.ui.language.v1')==='es','saved');check(codes.value==='@UCaseSensitiveCode','code modified');check(controls.every((el,i)=>el.checked===before[i]),'checkbox state lost');return true;
  })()`);assert.ok(result);win.destroy();
 }
 console.log('PASS desktop/mobile language choices, placeholders, preference persistence and unchanged serials/controls');app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});
