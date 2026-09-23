"use strict";
const assert=require("node:assert/strict"),path=require("node:path"),fs=require("node:fs");
const {app,BrowserWindow}=require("electron");
app.whenReady().then(async()=>{
  const win=new BrowserWindow({show:false,width:480,height:960,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,partition:'mobile-catalog-test'}});
  win.webContents.session.webRequest.onBeforeRequest({urls:['http://*/*','https://*/*']},(_details,callback)=>callback({cancel:true}));
  await win.loadFile(path.resolve(__dirname,'../mobile_controller/app/src/main/assets/index.html'));
  const pools=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../docs/data/item_pools.json'),'utf8'));
  const result=await win.webContents.executeJavaScript(`(()=>{
    const verify=(condition,message)=>{if(!condition)throw new Error(message);};
    state.pools.rows=${JSON.stringify(pools)};
    $('poolSearch').value='';$('poolCategory').value='';renderPools();
    verify($('poolRows').querySelectorAll('button').length===state.pools.rows.length,'all pool rows must be reachable');
    $('poolCategory').value='Pearl';renderPools();
    const pearls=$('poolRows').querySelectorAll('button').length;
    verify(pearls>=6,'all cooked Pearl pools visible');
    state.filteredCodes=Array.from({length:326},(_,id)=>({id:String(id),name:'Fixture '+id,tags:[]}));
    state.selectedCodes.clear();state.codePage=0;renderCodes();
    const first=$('codeList').querySelector('input');first.checked=true;first.dispatchEvent(new Event('change'));
    for(let page=0;page<13;page++)$('codeList').lastElementChild.lastElementChild.click();
    verify($('codeList').textContent.includes('Fixture 325'),'last code after the old 300 cap reachable');
    verify(state.selectedCodes.has('0'),'selection survives pagination');
    verify($('codeList').lastElementChild.lastElementChild.disabled,'last page stops at the end');
    return {pools:state.pools.rows.length,pearls,pages:state.codePage+1};
  })()`);
  assert.ok(result.pools>400);console.log('PASS mobile pool completeness, Pearl filter and codes pagination',JSON.stringify(result));win.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
