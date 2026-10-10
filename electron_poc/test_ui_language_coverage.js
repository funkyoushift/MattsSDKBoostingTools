// Isolated real-page inventory: no preload, IPC, or live game commands.
const {app,BrowserWindow}=require('electron');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
app.disableHardwareAcceleration();app.on('window-all-closed',()=>{});
app.whenReady().then(async()=>{
  const inventory=new Map(),routes=[];
  for(const [file,query] of [['renderer.html',{nosplash:'1'}],['renderer.html',{nosplash:'1',workspace:'classic'}],['../mobile_controller/app/src/main/assets/index.html',{}],['../external_app/v22_parts_codes_fixed/matt_editor/index.html',{}]]){
    const win=new BrowserWindow({show:false,width:1360,height:1000,webPreferences:{partition:'coverage-'+Math.random(),backgroundThrottling:false}});
    await win.loadFile(path.join(__dirname,file),{query});
    const data=await win.webContents.executeJavaScript(`(async()=>{
      const tr=window.MsbtTranslateUi,w=window.MsbtWorkspace;
      const rows=new Map();const collect=()=>tr.audit().forEach(row=>rows.set(row.source,row));collect();
      const add=source=>{source=source.replace(/\\s+/g,' ').trim();rows.set(source,{source,key:tr.catalog[source]?source:null});};
      for(const row of Object.values(window.msbtI18n.rows))add(row[0]);
      if(typeof TUTORIAL_TOURS!=='undefined')for(const steps of [...Object.values(TUTORIAL_TOURS),...Object.values(TAB_TUTORIALS)])for(const step of steps){add(step.title);if(step.body)add(step.body);}
      const routes=[];
      if(w?.enabled)for(const [tab,label,section]of [['boosting','Home','overview'],...w.groups.flatMap(g=>g[1])]){
        w.open(tab,section);await new Promise(r=>setTimeout(r,5));collect();
        routes.push({tab,label,section:section||'',australian:tr.catalog[label]?.['en-AU']||label});
      }
      if(w?.enabled)for(const lang of window.msbtI18n.locales){
        msbtI18n.setLanguage(lang);
        for(const r of routes){
          w.open(r.tab,r.section);tr.apply();
          const heading=document.querySelector('.tab-panel.active > .workspace-heading h2');
          if(heading.textContent!==tr.text(r.label))throw Error('Untranslated page heading: '+lang+' '+r.label);
          const current=document.querySelector('.workspace-sidebar [aria-current="page"]');
          if(current.textContent!==tr.text(r.label))throw Error('Untranslated navigation: '+lang+' '+r.label);
        }
      }
      return {rows:[...rows.values()],routes};
    })()`);
    data.rows.forEach(row=>inventory.set(row.source,row));routes.push(...data.routes);
    if(data.routes.length)for(const width of [360,800,1360]){
      win.setContentSize(width,900);
      const problems=await win.webContents.executeJavaScript(`(()=>{
        const problems=[];for(const lang of ['de','en-AU']){msbtI18n.setLanguage(lang);for(const [tab,label,section] of [['boosting','Home','overview'],...MsbtWorkspace.groups.flatMap(g=>g[1])]){
          MsbtWorkspace.open(tab,section);MsbtTranslateUi.apply();
          if(document.documentElement.scrollWidth>innerWidth+2)problems.push({lang,label,width:innerWidth,scrollWidth:document.documentElement.scrollWidth});
        }}return problems;
      })()`);
      assert.deepEqual(problems,[],'Translated pages must fit the window');
    }
    win.destroy();
  }
  const out=path.join(__dirname,'../output/languages');fs.mkdirSync(out,{recursive:true});
  const result={rows:[...inventory.values()],routes,missing:[...inventory.values()].filter(row=>!row.key).map(row=>row.source)};
  fs.writeFileSync(path.join(out,'coverage.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify({strings:inventory.size,routes:routes.length,missing:result.missing.length}));
  if(!process.argv.includes('--record')){
    const exempt=require('./ui_language_preserved.json');
    assert.deepEqual(result.missing.filter(s=>!Object.hasOwn(exempt,s)),[],'Untranslated app-owned text');
    assert(routes.every(r=>r.australian!==r.label),'Every workspace page needs its own Australian wording');
  }
  app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});
