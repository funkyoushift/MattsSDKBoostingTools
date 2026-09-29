(() => {
  const $=id=>document.getElementById(id), panel=$('communityFoldersPanel');
  if(!panel)return;
  let busy=false,selected=null,mode='public',next=null,shown=0,endpoint='';
  const message=(text,bad=false)=>{$('communityStatus').textContent=text;$('communityStatus').className='status-line '+(bad?'bad':'ok');};
  async function call(action,payload){if(!window.msbt?.communityFolders)throw Error('Restart the updated desktop app to use community folders.');const result=await window.msbt.communityFolders(action,payload);if(!result?.ok)throw Error(result?.message||'The online library is unavailable.');return result;}
  async function run(fn){if(busy)return;busy=true;panel.setAttribute('aria-busy','true');try{await fn();}catch(e){message(e.message,true);}finally{busy=false;panel.removeAttribute('aria-busy');}}
  function folders(){
    const select=$('communitySubmitFolder'),previous=select.value;
    select.replaceChildren(new Option('Choose a folder',''),...bookmarkGroups().map(x=>new Option(x,x)));
    select.value=previous;countSubmission();
  }
  function countSubmission(){const folder=$('communitySubmitFolder').value;const count=state.bookmarks.filter(row=>folder&&bookmarkInFolder(row.group,folder)).length;$('communitySubmitCount').textContent=folder?`${count} item entries will be shared, including duplicates and subfolders.`:'Choose a folder to see its item count.';}
  function clearPreview(){selected=null;$('communityPreviewTitle').textContent='Select a folder';$('communityPreviewDescription').textContent='';$('communityPreviewCount').textContent='';$('communityPreviewItems').replaceChildren();$('communityImportBtn').disabled=true;$('communityCopyBtn').disabled=true;$('communityWithdrawBtn').hidden=true;$('communityReviewActions').hidden=true;$('communityPreviewMore').hidden=true;}
  function items(){
    const end=Math.min(shown+100,selected.folder.items.length),host=$('communityPreviewItems');
    for(const item of selected.folder.items.slice(shown,end)){const row=document.createElement('details'),title=document.createElement('summary'),code=document.createElement('pre');title.textContent=(item.folder?item.folder+' / ':'')+item.name;code.textContent=item.serial;code.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere;max-height:180px;overflow:auto';row.append(title,code);host.append(row);}
    shown=end;$('communityPreviewMore').hidden=shown>=selected.folder.items.length;
  }
  async function preview(id,source){
    clearPreview();message('Loading folder preview…');
    const data=await call(source==='review'?'reviewGet':source==='mine'?'status':'get',{id});selected={...data,source};
    $('communityPreviewTitle').textContent=data.folder.title;
    $('communityPreviewDescription').textContent=`Submitted by ${data.folder.creator}. ${data.folder.description}`;
    $('communityPreviewCount').textContent=`${data.folder.items.length} item entries · ${data.status}${data.oversized_count?` · ${data.oversized_count} oversized codes cannot currently be delivered`:''}${data.review_note?' · Review: '+data.review_note:''}`;
    $('communityDestination').value=data.folder.title;$('communityImportBtn').disabled=data.status!=='approved';$('communityCopyBtn').disabled=data.status!=='approved';
    $('communityWithdrawBtn').hidden=source!=='mine'||data.status==='withdrawn';$('communityReviewActions').hidden=source!=='review'||data.status==='withdrawn';$('communityReviewNote').value=data.review_note||'';
    shown=0;items();message('Preview loaded. Import creates a separate local copy.');
  }
  function results(rows,source){
    const host=$('communityResults');host.replaceChildren();
    if(!rows.length){host.textContent=source==='review'?'No folders in this review queue.':'No folders found.';return;}
    for(const row of rows){const button=document.createElement('button');button.type='button';button.style.cssText='display:block;width:100%;text-align:left;margin:6px 0';button.textContent=`${row.title}${row.creator?' — '+row.creator:''}${row.item_count!=null?' · '+row.item_count+' items':''}${row.status?' · '+row.status:''}`;
      button.addEventListener('click',()=>run(async()=>{if(source==='mine'&&row.status==='sending'){await call('retry',{id:row.id});}await preview(row.id,source);}));host.append(button);}
  }
  async function browse(offset=0){
    clearPreview();const data=await call(mode==='review'?'reviewList':'list',{q:$('communitySearch').value,offset});
    next=data.next;$('communityMoreBtn').hidden=next==null;results(data.folders,mode);message(`${data.folders.length} folder(s) on this page.`);
  }
  function showLibrary(active){
    panel.hidden=!active;panel.open=active;
    $('savedItemsLocalPanel').hidden=active;
    for(const id of ['bookmarkStatus','bookmarkNewBtn','bookmarkImportBtn'])$(id).hidden=active;
    $('savedItemsLocalBtn').setAttribute('aria-pressed',String(!active));
    $('communityOpenBtn').setAttribute('aria-pressed',String(active));
    if(active)folders();
  }
  $('savedItemsLocalBtn').addEventListener('click',()=>showLibrary(false));
  $('communityOpenBtn').addEventListener('click',()=>{showLibrary(true);run(async()=>{const info=await call('info');endpoint=info.endpoint;mode='public';await browse();});});
  $('savedItemsShareBtn').addEventListener('click',()=>{showLibrary(true);$('communitySubmitPanel').open=true;$('communitySubmitPanel').scrollIntoView({block:'start'});$('communitySubmitFolder').focus({preventScroll:true});});
  panel.addEventListener('toggle',()=>{if(panel.open)folders();});
  $('communitySearchBtn').addEventListener('click',()=>run(async()=>{mode='public';await browse();}));
  $('communityMoreBtn').addEventListener('click',()=>run(()=>browse(next||0)));
  $('communityLinkBtn').addEventListener('click',()=>run(()=>preview($('communityLink').value,'public')));
  $('communityPreviewMore').addEventListener('click',()=>{if(selected)items();});
  $('communityMineBtn').addEventListener('click',()=>run(async()=>{clearPreview();const data=await call('mine');next=null;$('communityMoreBtn').hidden=true;results(data.submissions,'mine');message('Select a submission to refresh its status. A sending entry can be safely retried.');}));
  $('communitySubmitFolder').addEventListener('change',()=>{countSubmission();if(!$('communitySubmitTitle').value)$('communitySubmitTitle').value=$('communitySubmitFolder').value.split('/').at(-1).trim();});
  $('communitySubmitBtn').addEventListener('click',()=>run(async()=>{
    if(!$('communitySubmitConsent').checked)throw Error('Confirm that you want to share the selected folder.');
    const folder=window.communityFolderContract.exportFolder(state.bookmarks,state.bookmarkFolders,$('communitySubmitFolder').value,{title:$('communitySubmitTitle').value,creator:$('communitySubmitCreator').value,description:$('communitySubmitDescription').value});
    message(`Submitting ${folder.items.length} entries for approval…`);const result=await call('submit',{folder});$('communitySubmitConsent').checked=false;message('Submitted for approval. It will remain private until approved. Check My submissions for status.');
  }));
  $('communityImportBtn').addEventListener('click',()=>run(async()=>{
    if(!selected||selected.status!=='approved')throw Error('Preview an approved folder first.');
    const result=await call('import',{id:selected.id,digest:selected.digest,destination:$('communityDestination').value});
    state.bookmarks=result.data.bookmarks.map(normalizeBookmarkForRenderer);state.bookmarkFolders=result.data.folders;renderBookmarks();window.dispatchEvent(new Event('msbt-bookmarks-changed'));message(`Imported ${result.imported} entries into “${result.destination}”. You can now select that folder in AFK Lobby.`);
  }));
  $('communityCopyBtn').addEventListener('click',()=>run(async()=>{if(!endpoint)endpoint=(await call('info')).endpoint;if(!selected||selected.status!=='approved')return;await navigator.clipboard.writeText(endpoint+'/share/'+selected.id);message('Share link copied.');}));
  $('communityWithdrawBtn').addEventListener('click',()=>run(async()=>{if(!selected||!window.confirm('Withdraw this submission from the online library? Existing imported copies are unaffected.'))return;await call('withdraw',{id:selected.id});await preview(selected.id,'mine');}));
  $('communityDeveloperPortal').addEventListener('click',()=>run(async()=>{const result=await window.msbt.openDeveloperPortal();if(!result.ok)throw Error(result.message);}));
  $('developerPortalHeaderBtn').addEventListener('click',async()=>{try{const result=await window.msbt.openDeveloperPortal();if(!result.ok)window.alert(result.message);}catch{window.alert('Developer portal could not open. Please restart the updated desktop app.');}});
  window.addEventListener('msbt-bookmarks-changed',folders);
  const afkButton=document.createElement('button');afkButton.type='button';afkButton.textContent='Browse community folders';afkButton.addEventListener('click',()=>{(window.MsbtWorkspace?.enabled ? window.MsbtWorkspace.open('serial-tools','saved') : switchTab('serial-tools'));$('communityOpenBtn').click();});
  $('afkBookmarkFolder')?.insertAdjacentElement('afterend',afkButton);
})();
