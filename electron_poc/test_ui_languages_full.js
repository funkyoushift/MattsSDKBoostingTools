const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');const {app,BrowserWindow}=require('electron');
app.disableHardwareAcceleration();app.on('window-all-closed',()=>{});
const locales=['en','es','fr','pt-BR','de','nl','en-AU'];
const desktopRoot=process.env.MSBT_UI_TEST_ROOT||__dirname;
app.whenReady().then(async()=>{
 for(const file of ['renderer.html','../mobile_controller/app/src/main/assets/index.html']){
  const win=new BrowserWindow({show:false,width:1200,height:900,webPreferences:{partition:'language-'+Math.random(),backgroundThrottling:false}});
  await win.loadFile(path.join(file==='renderer.html'?desktopRoot:__dirname,file),{query:{nosplash:'1'}});
  const count=await win.webContents.executeJavaScript(`Object.keys(window.MsbtLanguageCatalog).length`);assert.ok(count>2000);
  for(const locale of locales){
   const result=await win.webContents.executeJavaScript(`(async()=>{
    const lang=window.msbtI18n,check=(v,m)=>{if(!v)throw Error(m)};
    lang.setLanguage(${JSON.stringify(locale)});
    const maxButton=document.querySelector('[data-action="max_all"]');
    check(maxButton,'Max All button exists');
    check(maxButton.textContent===window.MsbtTranslateUi.text(fileMaxLabel()),'Max All label');
    function fileMaxLabel(){return ${JSON.stringify(file)}==='renderer.html'?'Max All':'MAX ALL';}
    check(maxButton.dataset.action==='max_all','Max All action unchanged');
    if(lang.language==='en-AU'){
      check(maxButton.textContent==='Boost these cunts','requested Australian label');
      check(lang.t('start')==='Fire up the AFK lobby, mate','Australian AFK labels');
      check(document.querySelector('[data-language-selector] option[value="en-AU"]').textContent==='Australian slang (explicit)','explicit opt-in label');
    } else check(!maxButton.textContent.includes('cunts'),'Australian slang isolated');
    if(lang.language==='de')check(maxButton.textContent==='Alles maximieren','Max is an action, not a literal noun');
    if(lang.language==='fr')check(window.MsbtTranslateUi.text('Apply')==='Appliquer','Apply is not a job application');
    if(lang.language==='nl')check(window.MsbtTranslateUi.text('Free For All')==='Iedereen tegen iedereen','Free For All is combat, not price');
    if(lang.language==='es')check(window.MsbtTranslateUi.text('Kick Player')==='Expulsar al jugador','Kick is removal, not physical kicking');
    if(lang.language==='pt-BR')check(window.MsbtTranslateUi.text('Spawn Leg/Epic Loot')==='Gerar itens lendários ou épicos','Leg means legendary');
    let templateChecks=0;for(const [source,values]of Object.entries(window.MsbtLanguageCatalog)){
     if(!source.includes('{0}'))continue;templateChecks++;
     const fill=s=>[0,1,2,3,4].reduce((text,i)=>text.split('{'+i+'}').join('VALUE'+i),s);
     check(window.MsbtTranslateUi.text(fill(source))===fill(lang.language==='en'?source:values[lang.language]),'template '+source);
    }
    check(templateChecks>100,'templates exercised');
    const input=document.getElementById('afkCodes')||document.getElementById('afkPool');input.value='@UCaseSensitiveCode';
    const before=[...document.querySelectorAll('input,select,textarea')].map(x=>[x,x.value,x.checked]);
    const user=document.createElement('div');user.className='saved-folder-nav';user.textContent='Saved Items';document.body.append(user);
    const log=document.createElement('pre');log.textContent='Saved Items @UCaseSensitiveCode';document.body.append(log);
    const button=document.createElement('button');button.id='languageDynamic';button.textContent='Saved Items';let clicks=0;button.onclick=()=>clicks++;document.body.append(button);
    const holder=document.createElement('label');const field=document.createElement('input');field.placeholder='Search';field.value='Saved Items';holder.append(field);document.body.append(holder);
    await new Promise(r=>setTimeout(r,20));
    check(button.textContent===window.MsbtTranslateUi.text('Saved Items'),'dynamic translated');button.click();check(clicks===1,'handler intact');
    check(user.textContent==='Saved Items','folder preserved');check(log.textContent==='Saved Items @UCaseSensitiveCode','log preserved');check(field.value==='Saved Items','input preserved');
    check(field.placeholder===window.MsbtTranslateUi.text('Search'),'placeholder translated');
    button.textContent='Refresh Status';await new Promise(r=>setTimeout(r,20));check(button.textContent===window.MsbtTranslateUi.text('Refresh Status'),'updated UI translated');check(window.MsbtTranslateUi.originalText(button)==='Refresh Status','logic reads original text');button.textContent='3 / 12 selected';await new Promise(r=>setTimeout(r,20));check(button.textContent===window.MsbtTranslateUi.text('3 / 12 selected'),'count translated');button.textContent='Refresh Status';await new Promise(r=>setTimeout(r,20));
    for(const [node,value,checked]of before){check(node.value===value&&node.checked===checked,'control values changed');}
    check(input.value==='@UCaseSensitiveCode','serial preserved');
    lang.setLanguage('en');check(button.textContent==='Refresh Status','English restored');check(field.placeholder==='Search','placeholder restored');
    lang.setLanguage(${JSON.stringify(locale)});
    user.remove();log.remove();button.remove();holder.remove();
    if(window.MsbtWorkspace?.enabled){window.MsbtWorkspace.open('serial-tools','saved');const label=document.querySelector('[data-msbt-panel="serial-bookmarks"] h2');check(label.textContent===window.MsbtTranslateUi.text('Saved Items'),'workspace translation');}
    return {lang:document.documentElement.lang};
   })()`);assert.equal(result.lang,locale);
   for(const width of [360,800,1920]){
    win.setContentSize(width,900);
    const overflow=await win.webContents.executeJavaScript(`document.documentElement.scrollWidth>innerWidth+2`);assert.equal(overflow,false,`${file} ${locale} overflow at ${width}`);
   }
  }
  win.showInactive();await win.webContents.executeJavaScript(`window.msbtI18n.setLanguage('de');document.getElementById('mobileAnnounceDismissBtn')?.click();document.getElementById('bootWelcomeCloseBtn')?.click();`);await new Promise(r=>setTimeout(r,300));const out=path.join(__dirname,'../output/languages');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,file==='renderer.html'?'desktop-german.png':'mobile-german.png'),(await win.webContents.capturePage()).toPNG());await win.reload();if(win.webContents.isLoading())await new Promise(r=>win.webContents.once('did-finish-load',r));
  assert.equal(await win.webContents.executeJavaScript(`window.msbtI18n.language`),'de');
  await win.webContents.executeJavaScript(`window.msbtI18n.setLanguage('en-AU')`);
  await win.reload();if(win.webContents.isLoading())await new Promise(r=>win.webContents.once('did-finish-load',r));
  assert.equal(await win.webContents.executeJavaScript(`window.msbtI18n.language`),'en-AU');
  assert.equal(await win.webContents.executeJavaScript(`document.querySelector('[data-action="max_all"]').textContent`),'Boost these cunts');
  win.destroy();console.log('PASS six languages plus Australian slang, context meanings, live updates, controls, data safety, layouts and reload: '+file);
 }
 for(const name of ['ui_i18n.js','ui_localization.js','ui_language_catalog.js'])assert.equal(fs.readFileSync(path.join(__dirname,name),'utf8'),fs.readFileSync(path.join(__dirname,'../mobile_controller/app/src/main/assets',name),'utf8'),'shared '+name);
 console.log('PASS desktop/mobile shared catalogs');app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});
