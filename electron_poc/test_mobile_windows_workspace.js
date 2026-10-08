const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),http=require('node:http');
const {app,BrowserWindow,ipcMain}=require('electron');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'msbt-mobile-windows-'));
app.setPath('userData',path.join(temp,'profile'));app.setPath('sessionData',path.join(temp,'session'));
process.argv.push('--remote-afk-background');
const status={ok:true,started:true,name:'Fixture game',players:[{index:0,name:'Host'},{index:1,name:'Guest'}],selected_player:'Guest',selected_player_index:1,host_player_index:0,afk_lobby:{enabled:true,message:'AFK active',config:{level:true}},serial_delivery:{busy:false}};
const bridgeCalls=[];
status.serial_text='@UAbCd\n'.repeat(80000);status.last_drop={codes:status.serial_text};status.afk_lobby.config.codes=status.serial_text;
status.afk_lobby.config.guaranteed_codes=Array.from({length:4000},(_,i)=>'@UaBcD'+i+'X'.repeat(100));
require('./bridge_client').createBridgeClient=()=>({info:()=>'',request:async args=>{bridgeCalls.push(args);return {ok:true,status:200,data:args.path==='/status'?status:args.path==='/quick_menu'?{ok:true,layout:{pages:[]},catalog:{}}:{ok:true,message:'Fixture command accepted'}};}});
const originalFetch=global.fetch;global.fetch=async(url,options)=>{if(!['127.0.0.1','localhost'].includes(new URL(url).hostname))throw Error('Fixture: internet disabled');return originalFetch(url,options);};
const channels=new Set(),factory=require('./mobile_desktop_api'),create=factory.createMobileDesktopApi;let api;
factory.createMobileDesktopApi=options=>{api=create(options);const register=api.register;api.register=(channel,handler)=>{channels.add(channel);return register(channel,['app:nativeItemPreview','app:beginNativePreview','app:itemCardImages'].includes(channel)?async()=>({ok:false,message:'Fixture: native capture disabled'}):handler);};return api;};
require('./main');
for(const channel of Object.values(require('./desktop_contract').methods))assert.ok(channels.has(channel),'Desktop handler missing: '+channel);
api.registerSpecial('$echo',args=>args[0]);
const phoneStatusCalls=[];
ipcMain.handle('fixture:desktop',async(_event,body)=>{for(const call of body.calls||[])if(call.method==='bridgeRequest'&&call.args[0]?.path==='/status')phoneStatusCalls.push(call.args[0]);if(body.op==='upload')await new Promise(resolve=>setTimeout(resolve,1700));assert.ok(Buffer.byteLength(JSON.stringify(body))<1500000,'oversize phone transport request');return api.handle(body);});
const timeout=setTimeout(()=>{console.error('Windows workspace test timed out');app.exit(1)},90000);timeout.unref();
app.whenReady().then(async()=>{
  for(const win of BrowserWindow.getAllWindows())win.hide();
  const source=path.resolve(__dirname,'../mobile_controller/app/src/main/assets'),generated=path.resolve(__dirname,'../mobile_controller/app/build/generated/mobileAssets');
  const server=http.createServer((req,res)=>{
    const relative=decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/^\//,'')||'index.html';
    let file=path.join(source,relative);if(!fs.existsSync(file))file=path.join(generated,relative);
    if(!file.startsWith(source+path.sep)&&!file.startsWith(generated+path.sep)){res.writeHead(403).end();return;}
    if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}
    const types={'.js':'application/javascript','.html':'text/html','.css':'text/css','.json':'application/json','.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2'};
    res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const preload=path.join(temp,'preload.cjs');fs.writeFileSync(preload,"const {contextBridge,ipcRenderer}=require('electron');contextBridge.exposeInMainWorld('fixtureDesktop',body=>ipcRenderer.invoke('fixture:desktop',body));");
  const win=new BrowserWindow({show:false,width:480,height:960,webPreferences:{preload,sandbox:true,contextIsolation:true,partition:'windows-phone-tests'}});
  const origin=`http://127.0.0.1:${server.address().port}`;
  win.webContents.session.webRequest.onBeforeRequest({urls:['http://*/*','https://*/*']},(request,callback)=>callback({cancel:!request.url.startsWith(origin+'/')}));
  const errors=[];win.webContents.on('console-message',details=>{if(details.level==='error'&&!details.message.includes('ERR_BLOCKED_BY_CLIENT'))errors.push(details.message);});
  await win.loadURL(origin+'/index.html');
  await win.webContents.executeJavaScript(`(()=>{stopStatusPolling();window.alert=()=>{};window.confirm=()=>true;state.online=true;state.connection={};gatewayFetch=async(route,options={})=>route==='/desktop'?fixtureDesktop(options.payload):({ok:true,data:${JSON.stringify(status)}});$('openDesktopTools').click();})()`);
  let ready=false;
  for(let i=0;i<100;i++){ready=await win.webContents.executeJavaScript("Boolean($('desktopToolsFrame').contentWindow?.switchTab&&$('desktopToolsFrame').contentDocument?.querySelector('.workspace-sidebar'))");if(ready)break;await new Promise(resolve=>setTimeout(resolve,100));}
  assert.ok(ready,'Shared Windows workspace did not initialize: '+errors.join('\n'));
  const result=await win.webContents.executeJavaScript(`(async()=>{
    const f=$('desktopToolsFrame').contentWindow,check=(ok,message)=>{if(!ok)throw Error(message)};
    f.alert=()=>{};f.confirm=()=>true;
    const methods=Object.keys(f.MsbtDesktopContract.methods);check(methods.every(key=>typeof f.msbt[key]==='function'),'desktop method missing');
    check(f.getComputedStyle(f.document.getElementById('boostMobileNotice')).display==='none','phone repeats Windows mobile setup banner');
    check(f.getComputedStyle(f.document.getElementById('mobileAnnounceModal')).display==='none','phone repeats Android install dialog');
    const tabs=[...f.document.querySelectorAll('.tab-panel[id]')].map(node=>node.id);
    for(const tab of ['boosting','inventory','bl4-codes','serial-tools','matt-editor','dev-spawner','hoard-builder','updates'])check(tabs.includes('tab-'+tab),tab+' absent');
    await f.msbt.saveSerialBookmarks({version:1,bookmarks:[{id:'mobile-test',name:'Phone case test',serial:'@UAbCd',group:'Test'}],folders:['Test']});
    const saved=await f.msbt.loadSerialBookmarks();check(saved.ok&&saved.data.bookmarks[0].serial==='@UAbCd','PC bookmarks round trip');
    const live=await f.msbt.bridgeRequest({method:'GET',path:'/status'});check(live.data.afk_lobby.enabled&&live.data.selected_player==='Guest','AFK-active target status');
    check(live.data.serial_text==='@UAbCd\\n'.repeat(80000)&&live.data.last_drop.codes===live.data.serial_text,'phone status cache lost original lists');
    check(live.data.afk_lobby.config.guaranteed_codes.length===4000,'phone array cache lost AFK configuration');
    await f.msbt.bridgeRequest({method:'GET',path:'/quick_menu'});
    const refreshed=await f.msbt.bridgeRequest({method:'GET',path:'/status'});check(refreshed.data.serial_text===live.data.serial_text,'cached list reconstruction changed data');
    const large='@UAbCd'+'X'.repeat(2200000);check(await mobileDesktopBridge.call('$echo',[large])===large,'upload was polled before being submitted');
    const batched=await Promise.all([1,2,3].map(i=>mobileDesktopBridge.call('$echo',[String(i).repeat(600000)])));check(batched.every(value=>value.length===600000),'combined calls exceeded relay limit');
    const routes=[];
    for(const tab of tabs.map(id=>id.replace(/^tab-/,''))){
      f.switchTab(tab);await new Promise(resolve=>setTimeout(resolve,100));
      routes.push({tab,width:f.innerWidth,scroll:f.document.body.scrollWidth});
      check(f.document.body.scrollWidth<=f.innerWidth+3,tab+' overflows phone width');
    }
    f.switchTab('matt-editor');await new Promise(resolve=>setTimeout(resolve,500));
    const editor=f.document.getElementById('editorFrame');check(editor.src.includes('/desktop/editor/index.html'),'bundled save editor URL');
    for(let i=0;i<80&&!editor.contentWindow.MSBT_MATT_EDITOR_ADAPTER_VERSION;i++)await new Promise(resolve=>setTimeout(resolve,100));
    check(editor.contentWindow.MSBT_MATT_EDITOR_ADAPTER_VERSION,'bundled save editor did not initialize');
    check(typeof editor.contentWindow.switchTab==='function','save editor controls missing');
    const file={ok:true,name:'remembered.yaml',path:'mobile:remembered.yaml',base64:btoa('state: {}')};
    await mobileDesktopBridge.rememberFile('save',file);check((await f.msbt.mattEditorReopenFile('save')).base64===file.base64,'phone last-file reopen');
    const cryptoResult=await mobileDesktopBridge.call('$editorFetch',[{route:'/blcrypt/api.php',method:'POST',body:JSON.stringify({command:'encrypt',steamid:'76561198894205533',yaml_content:'state: {}'}),contentType:'application/json'}]);
    check(cryptoResult.status===200&&JSON.parse(cryptoResult.body).success,'PC save codec route: '+cryptoResult.body.slice(0,150));
    const preview=await mobileDesktopBridge.call('previewSaveItems',[{retry:false,file:{name:'fixture.yaml',base64:btoa('state:\\n  inventory:\\n    items:\\n      backpack:\\n        a: {serial: \\'@Uabc\\'}\\n')}}]);
    check(preview.ok&&preview.backpack===1,'phone file import preview: '+JSON.stringify(preview));
    const committed=await f.msbt.commitSaveItems({mode:'new',folder:'Phone import'});
    check(committed.ok&&committed.imported===1,'phone file commit: '+JSON.stringify(committed));
    const after=await f.msbt.loadSerialBookmarks();check(after.data.bookmarks.some(row=>row.serial==='@Uabc'),'import preserves serial case');
    f.phoneReopenMarker='retained';mobileDesktopBridge.close();$('openDesktopTools').click();
    check($('desktopToolsFrame').contentWindow.phoneReopenMarker==='retained','returning to phone controls discarded the loaded workspace');
    return {methods:methods.length,tabs:tabs.length,routes,editor:editor.src,preview,committed};
  })()`);
  assert.equal(result.methods,76);assert.ok(result.tabs>=15);
  // These use only a temporary desktop profile and the fake game transport.
  assert.ok(bridgeCalls.every(call=>['/status','/quick_menu','/action'].includes(call.path)));
  assert.ok(phoneStatusCalls.some(call=>call.mobileStatusHashes?.length),'phone did not reuse previously downloaded lists');
  const priorCalls=phoneStatusCalls.length;
  await win.webContents.executeJavaScript("new Promise(resolve=>{const frame=$('desktopToolsFrame');frame.addEventListener('load',()=>resolve(true),{once:true});frame.contentWindow.location.reload();})");
  let restored=false;
  for(let i=0;i<80;i++){
    restored=await win.webContents.executeJavaScript("Boolean($('desktopToolsFrame').contentWindow?.msbt?.bridgeRequest)");
    if(restored)break;await new Promise(resolve=>setTimeout(resolve,100));
  }
  const reopened=await win.webContents.executeJavaScript("$('desktopToolsFrame').contentWindow.msbt.bridgeRequest({method:'GET',path:'/status'})");
  assert.equal(reopened.data.serial_text,status.serial_text,'persistent phone cache lost original data');
  assert.ok(phoneStatusCalls.slice(priorCalls).some(call=>call.mobileStatusHashes?.length),'reopened workspace did not load the phone cache');
  fs.mkdirSync(path.resolve(__dirname,'../output/mobile-windows'),{recursive:true});
  fs.writeFileSync(path.resolve(__dirname,'../output/mobile-windows/renderer-receipt.json'),JSON.stringify({result,errors},null,2));
  console.log('PASS shared Windows workspace on phone',JSON.stringify({methods:result.methods,tabs:result.tabs,routes:result.routes}));
  clearTimeout(timeout);server.close();win.destroy();for(const panel of BrowserWindow.getAllWindows())panel.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1)});
