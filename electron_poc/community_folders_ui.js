(() => {
  const $=id=>document.getElementById(id), panel=$('communityFoldersPanel');
  if(!panel)return;
  let busy=false,selected=null,mode='public',next=null,shown=0,endpoint='';
  let searchTimer=null,searchPending=false,activeQuery='',pageOffsets=[0];
  const checked = new Set();
  $('savedSendBtn').addEventListener('click',()=>sendBookmarkSerial($('savedSendMode').value));
  function updateSendOptions(){const named=$('savedSendMode').value==='selected';$('bookmarkTargetSelect').closest('.target-row').hidden=!named;document.querySelector('label[for=bookmarkTargetSelect]').hidden=!named;$('bookmarkTargetSummary').hidden=!named;$('bookmarkDeliveryLevel').closest('label').hidden=!$('bookmarkOverrideLevel').checked;}
  $('savedSendMode').addEventListener('change',updateSendOptions);$('bookmarkOverrideLevel').addEventListener('change',updateSendOptions);updateSendOptions();
  state.bookmarkMultiSelect=true;$('bookmarkMultiSelectToggle').checked=true;
  for(const id of ['bookmarkNewBtn','bookmarkImportBtn'])$(id).addEventListener('click',()=>{$('savedItemEditor').open=true;$('savedItemEditor').scrollIntoView({block:'nearest'});});
  window.msbtCommunitySelection = () => panel.hidden ? null : !selected || selected.status !== 'approved' ? [] : selected.folder.items.flatMap((item,index) => checked.has(index) ? [{...item,group:selected.folder.title}] : []);
  function selectionChanged(){ $('communitySelectedCount').textContent = `${checked.size} / ${selected?.folder.items.length || 0} selected`;renderSavedDeliverySelection(); }
  const message=(text,bad=false)=>{$('communityStatus').textContent=text;$('communityStatus').className='status-line '+(bad?'bad':'ok');};
  async function call(action,payload){if(!window.msbt?.communityFolders)throw Error('Restart the updated desktop app to use community folders.');const result=await window.msbt.communityFolders(action,payload);if(!result?.ok)throw Error(result?.message||'The online library is unavailable.');return result;}
  async function run(fn){if(busy)return;busy=true;panel.setAttribute('aria-busy','true');try{await fn();}catch(e){message(e.message,true);}finally{busy=false;panel.removeAttribute('aria-busy');if(searchPending){searchPending=false;search();}}}
  function search(){
    clearTimeout(searchTimer);
    if(busy){searchPending=true;return;}
    run(async()=>{mode='public';await browse();});
  }
  function folders(){
    const select=$('communitySubmitFolder'),previous=select.value;
    select.replaceChildren(new Option('Choose a folder',''),...bookmarkGroups().map(x=>new Option(x,x)));
    select.value=previous;countSubmission();
  }
  function countSubmission(){const folder=$('communitySubmitFolder').value;const count=state.bookmarks.filter(row=>folder&&bookmarkInFolder(row.group,folder)).length;$('communitySubmitCount').textContent=folder?`${count} item entries will be shared, including duplicates and subfolders.`:'Choose a folder to see its item count.';}
  function clearPreview(){$('communityPreviewCreator').textContent='';$('communityPreviewNotes').hidden=true;selected=null;checked.clear();selectionChanged();$('communityPreviewTitle').textContent='Select a folder';$('communityPreviewDescription').textContent='';$('communityPreviewCount').textContent='';discardSavedCards($('communityPreviewItems'));$('communityPreviewItems').replaceChildren();$('communityImportBtn').disabled=true;$('communityCopyBtn').disabled=true;$('communityWithdrawBtn').hidden=true;$('communityReviewActions').hidden=true;$('communityPreviewMore').hidden=true;}
  function items(){
    const end=Math.min(shown+100,selected.folder.items.length),host=$('communityPreviewItems');
    for(let index=shown;index<end;index++){
      const original=selected.folder.items[index],presentation=selected.presentations?.[index],item={...original,name:presentation?.title||original.name}, row=document.createElement('div'), label=document.createElement('label'), box=document.createElement('input'), details=document.createElement('details'), title=document.createElement('summary'), code=document.createElement('pre');
      row.className='community-item-row saved-card-tile';box.type='checkbox';box.dataset.itemIndex=String(index);box.checked=checked.has(index);box.disabled=selected.status!=='approved';
      box.addEventListener('change',()=>{box.checked?checked.add(index):checked.delete(index);selectionChanged();});
      const itemTitle=document.createElement('span');itemTitle.className='saved-card-title';
      label.append(box,itemTitle);title.textContent='Show item code';code.textContent=item.serial;
      code.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere;max-height:180px;overflow:auto';details.append(title,code);row.append(label);const media=savedItemCard({...item,source:'Community folder',image_url:presentation?.image_url||'',image_serial_hash:presentation?.serial_hash||'',image_source:presentation?.image_source||''});media.classList.add('community-item-photo');
      bindSavedCardTitle(media,itemTitle,original,item.folder?item.folder+' / ':'');
      if(presentation?.title&&!savedCardNames.has(original.serial)){itemTitle.textContent=(item.folder?item.folder+' / ':'')+presentation.title;}
      if(presentation?.title_source==='GZO exact code match'){const credit=document.createElement('small');credit.textContent='GZO title · exact code match'+(original.name!==item.name?' · Saved label: '+original.name:'');row.append(credit);}row.append(media,details);host.append(row);
    }
    shown=end;$('communityPreviewMore').hidden=shown>=selected.folder.items.length;
  }
  async function preview(id,source){
    clearPreview();message('Loading folder preview…');
    const data=await call(source==='review'?'reviewGet':source==='mine'?'status':'get',{id});selected={...data,source};
    $('communityPreviewTitle').textContent=data.folder.title;
    $('communityPreviewCreator').textContent=`Submitted by ${data.folder.creator}.`;
    $('communityPreviewDescription').textContent=data.folder.description || '';
    $('communityPreviewNotes').hidden=!data.folder.description?.trim();
    $('communityPreviewNotes').open=true;
    $('communityPreviewCount').textContent=`${data.folder.items.length} item entries · ${data.status}${data.oversized_count?` · ${data.oversized_count} oversized codes cannot currently be delivered`:''}${data.review_note?' · Review: '+data.review_note:''}`;
    $('communityDestination').value=data.folder.title;$('communityImportBtn').disabled=data.status!=='approved';$('communityCopyBtn').disabled=data.status!=='approved';
    $('communityWithdrawBtn').hidden=source!=='mine'||data.status==='withdrawn';$('communityReviewActions').hidden=source!=='review'||data.status==='withdrawn';$('communityReviewNote').value=data.review_note||'';
    shown=0;items();selectionChanged();message('Preview loaded. Import creates a separate local copy.');
  }
  function results(rows,source){
    const host=$('communityResults');host.replaceChildren();
    if(!rows.length){host.textContent=source==='review'?'No folders in this review queue.':'No folders found.';return;}
    for(const row of rows){const button=document.createElement('button');button.type='button';button.style.cssText='display:block;width:100%;text-align:left;margin:6px 0';button.textContent=`${row.title}${row.creator?' — '+row.creator:''}${row.item_count!=null?' · '+row.item_count+' items':''}${row.status?' · '+row.status:''}`;
      button.addEventListener('click',()=>run(async()=>{if(source==='mine'&&row.status==='sending'){await call('retry',{id:row.id});}await preview(row.id,source);}));host.append(button);}
  }
  async function browse(offset=0,direction='reset'){
    const query=direction==='reset'?$('communitySearch').value.trim():activeQuery;
    const data=await call(mode==='review'?'reviewList':'list',{q:query,offset});
    clearPreview();activeQuery=query;
    pageOffsets=direction==='next'?[...pageOffsets,offset]:direction==='previous'?pageOffsets.slice(0,-1):[offset];
    next=data.next;
    $('communityPagination').hidden=pageOffsets.length===1&&next==null;
    $('communityPreviousBtn').disabled=pageOffsets.length===1;
    $('communityMoreBtn').disabled=next==null;
    results(data.folders,mode);message(`${data.folders.length} folder(s) on this page.`);
  }
  function showLibrary(active){
    panel.hidden=!active;panel.open=active;
    $('savedItemsLocalPanel').hidden=active;
    for(const id of ['bookmarkStatus','bookmarkNewBtn','bookmarkImportBtn'])$(id).hidden=active;
    $('savedItemsLocalBtn').setAttribute('aria-pressed',String(!active));
    $('communityOpenBtn').setAttribute('aria-pressed',String(active));
    if(active)folders();
    renderSavedDeliverySelection();
  }
  $('savedItemsLocalBtn').addEventListener('click',()=>showLibrary(false));
  $('communityOpenBtn').addEventListener('click',()=>{showLibrary(true);run(async()=>{const info=await call('info');endpoint=info.endpoint;mode='public';await browse();});});
  $('savedItemsShareBtn').addEventListener('click',()=>{showLibrary(true);$('communitySubmitPanel').open=true;$('communitySubmitPanel').scrollIntoView({block:'start'});$('communitySubmitFolder').focus({preventScroll:true});});
  panel.addEventListener('toggle',()=>{if(panel.open)folders();});
  $('communitySearchBtn').addEventListener('click',search);
  $('communitySearch').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.isComposing){event.preventDefault();search();}});
  $('communitySearch').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(search,250);});
  $('communityMoreBtn').addEventListener('click',()=>{if(next!=null)run(()=>browse(next,'next'));});
  $('communityPreviousBtn').addEventListener('click',()=>{if(pageOffsets.length>1)run(()=>browse(pageOffsets[pageOffsets.length-2],'previous'));});
  $('communityLinkBtn').addEventListener('click',()=>run(()=>preview($('communityLink').value,'public')));
  $('communitySelectAll').addEventListener('click',()=>{if(!selected||selected.status!=='approved')return;selected.folder.items.forEach((_,i)=>checked.add(i));panel.querySelectorAll('[data-item-index]').forEach(box=>{box.checked=true;});selectionChanged();});
  $('communityClearSelection').addEventListener('click',()=>{checked.clear();panel.querySelectorAll('[data-item-index]').forEach(box=>{box.checked=false;});selectionChanged();});
  $('communityCopySelected').addEventListener('click',()=>run(async()=>{const rows=window.msbtCommunitySelection()||[];if(!rows.length)throw Error('Select items first.');await navigator.clipboard.writeText(rows.map(row=>row.serial).join('\n'));message(`Copied ${rows.length} item codes.`);}));
  $('communityPreviewMore').addEventListener('click',()=>{if(selected)items();});
  $('communityMineBtn').addEventListener('click',()=>run(async()=>{clearPreview();const data=await call('mine');next=null;pageOffsets=[0];$('communityPagination').hidden=true;results(data.submissions,'mine');message('Select a submission to refresh its status. A sending entry can be safely retried.');}));
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
  // Browse approved folders in place; reuse AFK's persistence and running-session guard.
  const afkPicker=document.createElement('details');afkPicker.id='afkCommunityPicker';
  afkPicker.innerHTML=`<summary>Community folders</summary>
    <label for="afkCommunitySearch">Search community folders</label>
    <div class="button-row wrap"><input id="afkCommunitySearch" type="search" placeholder="Folder title or creator"><button id="afkCommunitySearchBtn" type="button">Search library</button></div>
    <label for="afkCommunityFolder">Choose a community folder</label><select id="afkCommunityFolder"><option value="">Choose a folder</option></select>
    <div class="button-row wrap"><button id="afkCommunityPrevious" type="button" disabled>Previous</button><button id="afkCommunityNext" type="button" disabled>Next</button></div>
    <div class="button-row wrap"><button id="afkCommunityAdd" type="button" disabled>Add folder to loot pool</button><button id="afkCommunityGuaranteed" type="button" disabled>Add folder to guaranteed items</button></div>
    <p id="afkCommunityNote" class="muted-line" role="status">Choose a folder to copy its item codes into an AFK list. No local bookmark import is needed.</p>`;
  $('afkBookmarkFolder')?.insertAdjacentElement('afterend',afkPicker);
  let afkBusy=false,afkNext=null,afkPages=[0],afkQuery='';
  const afkNote=text=>{$('afkCommunityNote').textContent=text;};
  function afkControls(){
    for(const id of ['afkCommunitySearchBtn','afkCommunityPrevious','afkCommunityNext','afkCommunityAdd','afkCommunityGuaranteed'])$(id).disabled=afkBusy;
    $('afkCommunityPrevious').disabled=afkBusy||afkPages.length===1;
    $('afkCommunityNext').disabled=afkBusy||afkNext==null;
    $('afkCommunityAdd').disabled=$('afkCommunityGuaranteed').disabled=afkBusy||!$('afkCommunityFolder').value;
  }
  async function afkRun(fn){if(afkBusy)return;afkBusy=true;afkPicker.setAttribute('aria-busy','true');afkControls();try{await fn();}catch(error){afkNote(error.message);}finally{afkBusy=false;afkPicker.removeAttribute('aria-busy');afkControls();}}
  async function afkBrowse(direction='reset'){
    const offset=direction==='next'?afkNext:direction==='previous'?afkPages.at(-2):0;
    const query=direction==='reset'?$('afkCommunitySearch').value.trim():afkQuery;
    const data=await call('list',{q:query,offset});
    afkQuery=query;afkNext=data.next;afkPages=direction==='next'?[...afkPages,offset]:direction==='previous'?afkPages.slice(0,-1):[0];
    const select=$('afkCommunityFolder');select.replaceChildren(new Option('Choose a folder',''));
    for(const row of data.folders)select.add(new Option(`${row.title}${row.creator?' — '+row.creator:''}${row.item_count!=null?' · '+row.item_count+' items':''}`,row.id));
    afkNote(data.folders.length?'Choose a folder, then add it to the loot pool or guaranteed items.':'No folders found.');
  }
  afkPicker.addEventListener('toggle',()=>{if(afkPicker.open&&$('afkCommunityFolder').options.length===1)afkRun(()=>afkBrowse());});
  $('afkCommunitySearchBtn').addEventListener('click',()=>afkRun(()=>afkBrowse()));
  $('afkCommunitySearch').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.isComposing){event.preventDefault();afkRun(()=>afkBrowse());}});
  $('afkCommunityFolder').addEventListener('change',afkControls);
  $('afkCommunityPrevious').addEventListener('click',()=>afkRun(()=>afkBrowse('previous')));
  $('afkCommunityNext').addEventListener('click',()=>afkRun(()=>afkBrowse('next')));
  for(const [id,guaranteed] of [['afkCommunityAdd',false],['afkCommunityGuaranteed',true]])$(id).addEventListener('click',()=>afkRun(async()=>{
    const id=$('afkCommunityFolder').value;if(!id)throw Error('Choose a folder first.');
    const data=await call('get',{id});
    if(data.status!=='approved')throw Error('Only approved community folders can be added.');
    const codes=data.folder.items.map(item=>item.serial);
    if(!codes.length||codes.some(code=>typeof code!=='string'||!code.trim()))throw Error('This folder has missing item codes. Nothing added.');
    const result=window.msbtAfkAppendLoot(codes,guaranteed);
    afkNote(result.ok?`Added ${codes.length} item code(s) from “${data.folder.title}” to ${guaranteed?'guaranteed items':'the loot pool'}.`:result.message);
  }));
})();
