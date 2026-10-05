const {app,BrowserWindow}=require('electron');
const assert=require('node:assert/strict'),path=require('node:path');
app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
 const win=new BrowserWindow({show:false,width:1600,height:1000,webPreferences:{partition:'card-views-'+process.pid}});
 // No external image or API calls in this test.
 const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6LksAAAAASUVORK5CYII=','base64');
 await win.webContents.session.protocol.handle('https',()=>new Response(png,{headers:{'Content-Type':'image/png'}}));
 await win.loadFile(path.join(__dirname,'renderer.html'),{query:{nosplash:'1'}});
 const result=await win.webContents.executeJavaScript(`(async()=>{
  const check=(v,m)=>{if(!v)throw Error(m);};
  let native=[],lookups=[];
  window.msbt={...(window.msbt||{}),itemCardImages:async serials=>{lookups.push(...serials);return {items:serials.filter(s=>s==='@UGzo').map(serial=>({serial,image:'https://save-editor.be/GZO/known.png',itemCard:{name:'GZO name'}}))};},
    nativeItemPreview:async serial=>{native.push(serial);return {ok:true,widget:{Name:'Native '+serial},image:{ok:true,base64:${JSON.stringify(png.toString('base64'))}}};}};
  const wait=async fn=>{for(let i=0;i<150;i++){if(fn())return;await new Promise(r=>setTimeout(r,20));}throw Error('Timed out waiting for card');};
  const host=document.createElement('div');document.body.prepend(host);
  const hash=async serial=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(serial))),x=>x.toString(16).padStart(2,'0')).join('');
  const uploaded=document.createElement('div');host.append(uploaded);
  fillBl4ItemCard(uploaded,{serial:'@UUpload',image_url:'https://msbt-community-library.screename53.workers.dev/images/abcdef-1234',image_serial_hash:await hash('@UUpload')});
  await wait(()=>uploaded.querySelector('img'));check(native.length===0&&lookups.length===0,'upload must bypass GZO and native');
  const gzo=document.createElement('div'),gzoTitle=document.createElement('span');host.append(gzo,gzoTitle);
  bindSavedCardTitle(gzo,gzoTitle,{serial:'@UGzo',name:'Old GZO label'});fillBl4ItemCard(gzo,{serial:'@UGzo'});
  await wait(()=>gzo.querySelector('img'));check(native.length===0,'GZO must bypass native');
  check(gzoTitle.textContent==='Old GZO label','GZO items retain their existing saved title');
  check(gzoTitle.title.includes('Old GZO label'),'GZO keeps original label available');
  const generated=document.createElement('div');host.append(generated);fillBl4ItemCard(generated,{serial:'@UUnknown'});
  await wait(()=>generated.querySelector('img'));check(native.includes('@UUnknown'),'unknown uses native');
  // Real shared lazy tile used by both local saved folders and Community Folders.
  const community=savedItemCard({serial:'@UCommunity',source:'Community folder'});host.append(community);
  savedCardObserver.unobserve(community);savedCardPending.set('@UCommunity',[{host:community}]);await flushSavedCards();
  await wait(()=>community.querySelector('img'));check(native.includes('@UCommunity'),'community screenshot absence must generate');
  // Saved names follow the actual resolved card without rewriting source data.
  const original={id:'name-test',serial:'@UNameTest',name:'Old saved label',group:'Creator folder'};
  const before=JSON.stringify(original);
  state.bookmarks=[original];els.bookmarkSearch.value='';state.bookmarkFilterGroup='All';els.bookmarkGroupFilter.value='All';
  renderBookmarks();
  const namedMedia=document.querySelector('#bookmarkRows .saved-item-card');
  savedCardObserver.unobserve(namedMedia);savedCardPending.set(original.serial,[{host:namedMedia}]);await flushSavedCards();
  const namedTitle=document.querySelector('#bookmarkRows .bookmark-title');
  await wait(()=>namedTitle.textContent.includes('Native @UNameTest'));
  check(namedTitle.title.includes(original.name),'original label remains in tooltip');
  check(JSON.stringify(original)===before,'card name must not rewrite saved data');
  check(bookmarkSearchText(original).includes('native @unametest')&&bookmarkSearchText(original).includes('old saved label'),'search includes resolved and saved names');
  namedMedia.dispatchEvent(new CustomEvent('msbt-card-name',{detail:{serial:'@Unametest',name:'Wrong case item',source:'Game card'}}));
  check(namedTitle.textContent.includes('Native @UNameTest'),'another serial must not rename this tile');
  renderBookmarks();
  check(document.querySelector('#bookmarkRows .bookmark-title').textContent.includes('Native @UNameTest'),'resolved name survives rerender');
  const mismatch=document.createElement('div');host.append(mismatch);fillBl4ItemCard(mismatch,{serial:'@UDifferent',image_url:'https://msbt-community-library.screename53.workers.dev/images/abcdef-1234',image_serial_hash:await hash('@UUpload')});
  await wait(()=>mismatch.querySelector('img'));check(native.includes('@UDifferent'),'mismatched upload must not be reused');
  const stale=document.createElement('div');host.append(stale);fillBl4ItemCard(stale,{serial:'@UOld'});fillBl4ItemCard(stale,{serial:'@UGzo'});
  await wait(()=>stale.querySelector('img'));check(stale.querySelectorAll('img').length===1&&stale.querySelector('img').alt==='GZO name','changed host must ignore old response');
  for(const id of ['boostSerialText','serialToolsSerialized','validatorBasicInput','validatorBulkInput','bl4Serial'])
    check(document.getElementById(id).nextElementSibling.classList.contains('serial-card-previews'),'missing preview '+id);
  check(document.querySelector('#tab-matt-editor .serial-card-previews'),'editor preview');
  let switches=0;
  window.msbt.nativeItemPreview=async(serial,wantImage,layout)=>{switches++;return {ok:true,serial,session:'same-session',widget:{Name:'Expanded'},image:{ok:true,layout:layout==='compact'?'compact':'expanded',base64:${JSON.stringify(png.toString('base64'))}}};};
  const expanded=document.createElement('div');host.append(expanded);fillBl4ItemCard(expanded,{serial:'@UExpanded'});
  await wait(()=>expanded.querySelector('.item-card-layout-toggle'));
  const toggle=expanded.querySelector('.item-card-layout-toggle');
  let bubbled=false;expanded.addEventListener('click',()=>{bubbled=true});
  toggle.click();await wait(()=>toggle.textContent==='Expanded layout');
  check(expanded.querySelectorAll('img').length===1&&!bubbled,'layout switch must replace image without selecting item');
  toggle.click();await wait(()=>toggle.textContent==='Compact layout');
  check(switches===2,'repeat layout toggle must reuse both cached images');
  check(expanded.querySelectorAll('img').length===1&&expanded.textContent.includes('expanded layout'),'expanded image restored');
  window.msbt.nativeItemPreview=async()=>({ok:false,message:"RuntimeError('New game cards require a solo session; existing screenshots remain available')"});
  const unavailable=document.createElement('div');host.append(unavailable);fillBl4ItemCard(unavailable,{serial:'@UUncached'});
  await wait(()=>unavailable.textContent.includes('No matching screenshot or cached card yet.'));
  check(!unavailable.textContent.includes('RuntimeError'),'raw solo exception leaked into card');
  return {upload:true,gzo:true,native:true,community:true,mismatch:true,stale:true,serialMenus:6,clearUnavailableMessage:true,layoutToggle:true,savedCardNames:true};
 })()`);
 assert.equal(result.community,true);console.log(JSON.stringify(result));win.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
