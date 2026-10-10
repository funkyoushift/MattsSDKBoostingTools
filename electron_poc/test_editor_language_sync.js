const {app,BrowserWindow}=require('electron');
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
  const root=path.resolve(__dirname,'../external_app/v22_parts_codes_fixed/matt_editor');
  const server=http.createServer((req,res)=>{
    const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
    if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
    res.setHeader('Content-Type',({'.js':'application/javascript','.html':'text/html','.css':'text/css','.json':'application/json'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
  });
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
  const win=new BrowserWindow({show:false,width:1360,height:900,webPreferences:{partition:'editor-language-'+process.pid,backgroundThrottling:false}});
  win.webContents.session.webRequest.onBeforeRequest((details,callback)=>callback({cancel:!details.url.startsWith(origin)&&!details.url.startsWith('file:')&&!details.url.startsWith('data:')}));
  await win.loadFile(path.join(__dirname,'renderer.html'),{query:{nosplash:'1'}});
  await win.webContents.executeJavaScript(`msbtI18n.setLanguage('en-AU');document.getElementById('editorFrame').src=${JSON.stringify(origin+'/index.html')}`);
  let frame;
  for(let i=0;i<100;i++){
    frame=win.webContents.mainFrame.frames.find(f=>f.url.startsWith(origin));
    if(frame&&await frame.executeJavaScript("Boolean(window.msbtI18n&&window.MsbtTranslateUi)").catch(()=>false))break;
    await new Promise(r=>setTimeout(r,100));
  }
  assert(frame,'Editor frame loaded');await new Promise(r=>setTimeout(r,100));
  assert.equal(await frame.executeJavaScript('msbtI18n.language'),'en-AU','New editor inherits parent language');
  await frame.executeJavaScript(`window.protectedTest=document.createElement('div');protectedTest.innerHTML='<span class="part-name">Save</span><span class="item-name">Apply</span><select><option value="Save">Save</option></select><textarea>@UCaseSensitiveCode\\n@UCaseSensitiveCode</textarea>';document.body.append(protectedTest);window.beforeFields=[...document.querySelectorAll('input,textarea,select')].map(n=>({n,value:n.value,checked:n.checked}));`);
  for(const locale of ['es','fr','pt-BR','de','nl','en-AU','en']){
    await win.webContents.executeJavaScript(`msbtI18n.setLanguage(${JSON.stringify(locale)})`);await new Promise(r=>setTimeout(r,60));
    const result=await frame.executeJavaScript(`(()=>{MsbtTranslateUi.apply();return {language:msbtI18n.language,fieldsUnchanged:beforeFields.every(({n,value,checked})=>n.value===value&&n.checked===checked),data:protectedTest.textContent,raw:protectedTest.querySelector('textarea').value,heading:document.querySelector('#mi_itemPropertiesPanel h3').textContent,expected:MsbtTranslateUi.text('Item Properties')};})()`);
    assert.equal(result.language,locale);assert(result.fieldsUnchanged,'Language must not edit save values');assert(result.data.startsWith('SaveApplySave'),'Part/item names preserved');assert.equal(result.raw,'@UCaseSensitiveCode\n@UCaseSensitiveCode');assert(result.heading.includes(result.expected),'Editor labels translated');
  }
  // A sibling frame cannot control the editor language.
  await frame.executeJavaScript(`window.dispatchEvent(new MessageEvent('message',{data:{type:'msbt-ui-language',language:'de'},source:window}));`);
  assert.equal(await frame.executeJavaScript('msbtI18n.language'),'en');
  win.destroy();server.close();console.log('PASS cross-origin editor language handshake, all seven locales, protected names/serials/save values and message source checks.');app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});
