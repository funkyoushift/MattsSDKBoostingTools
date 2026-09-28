const assert=require('node:assert/strict');
const path=require('node:path');
const {app,BrowserWindow}=require('electron');
app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
 const win=new BrowserWindow({show:false,webPreferences:{partition:'bulk-bookmarks-'+process.pid}});
 await win.loadFile(path.join(__dirname,'renderer.html'),{query:{nosplash:'1'}});
 if (process.argv[2]) {
   const codes=require('fs').readFileSync(process.argv[2],'utf8').trim().split(/\s+/);
   await win.webContents.executeJavaScript('window.bookmarkFixture='+JSON.stringify(codes));
 }
 const result=await win.webContents.executeJavaScript(`(async()=>{
  const check=(v,m)=>{if(!v)throw Error(m)};
  window.msbt=window.msbt||{};
  window.msbt.saveSerialBookmarks=async data=>({ok:true,data:JSON.parse(JSON.stringify(data))});
  state.bookmarks=[{id:'old',name:'Old',serial:'@Uold',group:'Default'}];state.bookmarkActiveId='old';
  state.bookmarkFolders=['Builds / Vex'];renderBookmarks();
  check(els.bookmarkGroup.tagName==='SELECT','save destination is dropdown');
  els.bookmarkName.value='Starter';els.bookmarkGroup.value='Builds / Vex';
  els.bookmarkSerial.value=Array(976).fill('@UMixedCase').join('\\r\\n');
  await saveBookmark();
  check(state.bookmarks.length===977,'all entries and duplicates saved');
  check(state.bookmarks[0].serial==='@Uold','bulk paste must not replace active bookmark');
  check(state.bookmarks.slice(1).every(row=>row.group==='Builds / Vex'&&row.serial==='@UMixedCase'),'folder and code exact');
  check(new Set(state.bookmarks.map(row=>row.id)).size===977,'unique ids');
  check(els.bookmarkSerial.value==='','clear successful bulk paste');
  const count=state.bookmarks.length;
  els.bookmarkSerial.value='@Ugood\\ninvalid';await saveBookmark();check(state.bookmarks.length===count,'atomic rejection');
  els.bookmarkSerial.value='@Uone @Utwo';
  window.msbt.saveSerialBookmarks=async()=>{throw Error('Disk full')};
  await saveBookmark();check(state.bookmarks.length===count&&els.bookmarkSerial.value==='@Uone @Utwo','rollback and retain paste');
  window.msbt.saveSerialBookmarks=async data=>({ok:true,data});
  state.bookmarkActiveId='old';els.bookmarkSerial.value='@Uupdated';await saveBookmark();
  check(state.bookmarks.length===count&&state.bookmarks[0].serial==='@Uupdated','single edit preserved');
  window.msbt.serialCardResolve=async ({serials})=>({ok:true,cards:serials.map(serial=>({ok:true,serial,card:{meta_ok:serial==='@UDecoded',display_name:'Resolved Shield'}}))});
  const decodedNames=await bookmarkGeneratedTitles(['@UDecoded']);check(decodedNames[0]==='Resolved Shield','resolve uncatalogued serial name');
  state.bl4Entries=[{serial:'@UKnown',name:'Catalog Gun'}];
  state.bookmarkActiveId='';els.bookmarkName.value='';els.bookmarkSerial.value='@UKnown @UKnown @UUnknown @UUnknown';
  await saveBookmark();
  check(JSON.stringify(state.bookmarks.slice(-4).map(row=>row.name))===JSON.stringify(['Catalog Gun','Catalog Gun (2)','Saved item 1','Saved item 2']),'blank bulk names generated and unique');
  els.bookmarkName.value='';els.bookmarkSerial.value='@UUnknown';await saveBookmark();
  check(state.bookmarks.at(-1).name==='Saved item 3'&&els.bookmarkName.value==='Saved item 3','single fallback does not collide');
  check(state.bookmarks[1].name==='Starter 1','explicit existing titles preserved');
  els.bookmarkSerial.value='@UDecoded';await previewBookmarkCard();
  check(!document.getElementById('bookmarkScreenshotBtn').disabled,'resolved preview allows capture');
  check(document.getElementById('bookmarkCardHost').children.length>0,'shared inventory card rendered');
  let shot;
  window.msbt.saveNativeCardScreenshot=async card=>{shot=card;return {ok:true,path:'test.png'}};
  await saveBookmarkScreenshot();check(shot.display_name==='Resolved Shield','capture uses same resolved card');
  els.bookmarkSerial.value='@UChanged';els.bookmarkSerial.dispatchEvent(new Event('input'));
  check(document.getElementById('bookmarkScreenshotBtn').disabled,'editing code invalidates screenshot');
  state.bookmarks.push({id:'repair',name:'Saved item 999',serial:'@UDecoded',group:'Default'});
  await fillMissingBookmarkNames();check(state.bookmarks.find(row=>row.id==='repair').name.startsWith('Resolved Shield'),'repair existing placeholders');
  check(state.bookmarks[1].name==='Starter 1','repair preserves custom names');
  if(window.bookmarkFixture){
    const before=state.bookmarks.length;
    els.bookmarkName.value='Fixture';els.bookmarkSerial.value=window.bookmarkFixture.join('\\n');
    await saveBookmark();
    check(state.bookmarks.length===before+window.bookmarkFixture.length,'actual input all saved');
    check(state.bookmarks.slice(before).every((row,i)=>row.serial===window.bookmarkFixture[i]),'actual codes preserved exactly');
    check(document.getElementById('bookmarkStatus').textContent.includes('cannot be sent'),'oversized delivery warning');
  }
  return true;
 })()`);
 assert(result);win.destroy();console.log('PASS bulk bookmark paste 976 entries, duplicate preservation, atomic validation, rollback and single edit');app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});
