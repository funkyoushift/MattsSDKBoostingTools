'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {app,BrowserWindow,protocol}=require('electron');
const native=require('./native_card_protocol');
native.registerNativeCardSchemes(protocol);
app.whenReady().then(async()=>{
 native.installNativeCardProtocol(protocol);
 const win=new BrowserWindow({show:false,width:546,height:2048,useContentSize:true,webPreferences:{offscreen:true,sandbox:true,contextIsolation:true,nodeIntegration:false}});
 await win.loadURL('msbt-card://inventory/card.html');
 const output=path.resolve(__dirname,'../output/card-layout');fs.mkdirSync(output,{recursive:true});
 const results=[];
 for(const key of ['ordinary','draupner','ichor','classmod']){
  const widget=require('./fixtures/native_widgets/'+key+'.json');
  const before=JSON.stringify(widget);
  const model=require('./native_widget_card_model').fromNativeWidget(widget,{allowMissingArtwork:true});
  const report=await win.webContents.executeJavaScript(`(async()=>{
   const model=${JSON.stringify(model)},input=JSON.stringify(model);
   const result=await renderNativeCard(model,templates);
   const card=document.querySelector('.item_card').getBoundingClientRect();
   const sections=[...document.querySelectorAll('.msbt-expanded-stats')].map(panel=>{
     const expected=model[panel.dataset.statGroup].map(row=>{
       const el=document.createElement('div');el.innerHTML=MarkupMgr.ResolveMarkupText(safeMarkup(row.value));return el.textContent;
     });
     const actual=[...panel.querySelectorAll('.msbt-expanded-value')].map(n=>n.textContent);
     const rects=[...panel.querySelectorAll('.msbt-expanded-stat')].map(n=>{const r=n.getBoundingClientRect();return {top:r.top,bottom:r.bottom,left:r.left,right:r.right};});
     return {expected,actual,rects};
   });
   return {result,unchanged:input===JSON.stringify(model),sections,card:{left:card.left,right:card.right,bottom:card.bottom}};
  })()`);
  assert.equal(report.unchanged,true);assert.equal(JSON.stringify(widget),before);
  assert.deepEqual(report.result.errors,[]);
  assert.equal(report.result.layout,key==='ordinary'?'compact':'expanded');
  for(const section of report.sections){
   assert.deepEqual(section.actual,section.expected,'preserve every native value, order and duplicate');
   section.rects.forEach((r,i)=>{
    assert.ok(r.left>=report.card.left-1&&r.right<=report.card.right+1&&r.bottom<=report.card.bottom,'expanded rows fit card');
    if(i)assert.ok(r.top>=section.rects[i-1].bottom-1,'no row overlap');
   });
  }
  if(key!=='ordinary'){
   const compact=await win.webContents.executeJavaScript(`(async()=>{await renderNativeCard(${JSON.stringify(model)},templates,{layout:'compact'});return {notices:document.querySelectorAll('.msbt-expanded-notice').length,values:[...document.querySelectorAll('.item_card_primary_stat_value,.ic_class_mod_point_text')].map(n=>n.textContent)}})()`);
   assert.equal(compact.notices,0);assert.deepEqual(compact.values,model.primary_stat_entries.map(r=>r.value));
  }
  const captured=await require('./native_card_capture').captureNativeWidget(BrowserWindow,widget);
  assert.equal(captured.layout,report.result.layout);
  assert.equal(captured.cssHeight,Math.ceil(report.result.height),'capture measures expanded height');
  fs.writeFileSync(path.join(output,key+'-expanded.png'),Buffer.from(captured.base64,'base64'));
  results.push({key,layout:captured.layout,height:captured.cssHeight,rows:model.primary_stat_entries.length});
 }
 // Real native grenade text contains an input action. It must not discard the
 // entire card or fabricate a keyboard/controller binding when none was exported.
 const glyphWidget=require('./fixtures/native_widgets/inline-glyph.json');
 const glyphReport=await win.webContents.executeJavaScript(`(async()=>{const model=${JSON.stringify(require('./native_widget_card_model').fromNativeWidget(glyphWidget,{allowMissingArtwork:true}))};const result=await renderNativeCard(model,templates);return {result,prompt:document.querySelector('gbx-glyph')?.textContent,firmware:document.querySelector('.firmware_name_cntr')?.textContent};})()`);
 assert.deepEqual(glyphReport.result.errors,[]);assert.equal(glyphReport.prompt,'[input: action_gadget]');assert.equal(glyphReport.firmware,'Risky Boots');assert.ok(glyphReport.result.warnings.includes('Input glyph unavailable: action_gadget'));
 // User-controlled strings remain text even in the alternate markup layout.
 const safety=await win.webContents.executeJavaScript(`(async()=>{
 const model=${JSON.stringify(require('./native_widget_card_model').fromNativeWidget(require('./fixtures/native_widgets/draupner.json'),{allowMissingArtwork:true}))};
 model.primary_stat_entries[1].value='<img src=x onerror="window.injected=true">[secondary]Safe[/secondary]';
 await renderNativeCard(model,templates);
 return {images:document.querySelectorAll('.msbt-expanded-stats img').length,injected:window.injected===true,text:document.querySelector('.msbt-expanded-stats').textContent};
 })()`);
 assert.equal(safety.images,0);assert.equal(safety.injected,false);assert.ok(safety.text.includes('<img'));
 console.log(JSON.stringify({ok:true,results,safeMarkup:true}));win.destroy();app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});
