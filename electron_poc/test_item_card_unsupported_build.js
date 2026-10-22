const {app,BrowserWindow}=require('electron');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
  const win=new BrowserWindow({show:false});
  await win.loadURL('data:text/html,<body></body>');
  await win.webContents.executeJavaScript(fs.readFileSync(path.join(__dirname,'item_card_view.js'),'utf8'));
  const result=await win.webContents.executeJavaScript(`(async()=>{
    const results=[];
    for(const profile of ['steam-26007962','epic-6d531d91']){
      window.msbt={itemCardImages:async()=>({items:[]}),nativeItemPreview:async()=>({ok:false,message:"RuntimeError('Game cards are not supported by this game build ("+profile+")')"})};
      const host=document.createElement('div');document.body.append(host);
      let names=0;host.addEventListener('msbt-card-name',()=>names++);
      const serial='@UMixedCaseAbCd<original>';
      MSBTItemCards.show(host,{serial});await host.cardRequest;
      results.push({profile,serial:host.querySelector('code')?.textContent,text:host.textContent,images:host.querySelectorAll('img').length,markup:host.querySelectorAll('original').length,names});
    }
    return results;
  })()`);
  for(const row of result){
    assert.equal(row.serial,'@UMixedCaseAbCd<original>');
    assert.match(row.text,/stats have not been generated/);
    assert.doesNotMatch(row.text,/RuntimeError/);
    assert.equal(row.images+row.markup+row.names,0);
  }
  console.log('Unsupported Steam/Epic card serial fallback passed');
  win.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1)});
