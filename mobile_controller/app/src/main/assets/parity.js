// Desktop/mobile parity additions. All game writes use the existing action bridge.
(() => {
  const card=(screen,html)=>{const el=document.createElement('article');el.className='card';el.innerHTML=html;document.querySelector(`[data-screen="${screen}"]`).append(el);return el;};
  const boost=document.querySelector('[data-screen="boost"] .target-card');
  boost.insertAdjacentHTML('beforeend','<label>Boost scope<select id="boostScope"><option value="selected">Named player</option><option value="local">Host</option><option value="all">All players</option><option value="nonhost">Other players</option></select></label><small>Scope applies to Quick Max, Currency / XP, Set Selected capacity, Customs + Hovers, and Shiny Selected.</small>');
  const stats=card('boost','<h3>Live player stats</h3><p id="mobileReadbackStatus">Connect to read the selected player.</p><dl id="mobileReadbackValues" class="fields two"></dl><details><summary>Vault-card ranks</summary><div id="mobileReadbackCards"></div></details>');
  boost.after(stats);
  let lastStatus=null;
  window.renderMobileReadback=(data)=>{
    const snap=data?.player_readback, values=$('mobileReadbackValues'),cards=$('mobileReadbackCards');values.replaceChildren();cards.replaceChildren();
    const valid=state.online&&snap?.available&&snap.name===data.selected_player&&
      currentTarget()===`${data.selected_player_index}|${snap.name}`&&!state.pendingTarget&&
      Number.isFinite(snap.sampled_at)&&Math.abs(Date.now()/1000-snap.sampled_at)<10;
    $('mobileReadbackStatus').textContent=valid?`${snap.name} · ${new Date(snap.sampled_at*1000).toLocaleTimeString()}`:'Waiting for a current reading from the selected player.';
    if(!valid)return;
    const c=snap.currencies||{},rows=[['Level',snap.level],['Specialization',snap.specialization],['Cash',c.Cash],['Eridium',c.eridium]];
    for(let i=1;i<=5;i++)rows.push([`Vault card ${i} keys`,c[`VaultCard0${i}_Tokens`]]);
    for(const [label,value] of rows){const cell=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=Number.isFinite(value)?value.toLocaleString():'Unavailable';cell.append(dt,dd);values.append(cell);}
    for(let i=1;i<=5;i++){const row=(snap.vault_cards||[]).find(c=>c.card===i),line=document.createElement('p');line.textContent=`Card ${i}: ${Number.isFinite(row?.rank)?row.rank.toLocaleString():'Unavailable'}${row?(row.active?' · Active':' · Inactive'):''}`;cards.append(line);}
  };
  const originalStatus=applyStatus;
  applyStatus=function(data){originalStatus(data);lastStatus=data;renderMobileReadback(data);};
  setInterval(()=>renderMobileReadback(lastStatus),1000);

  const scoped=new Set(['max_all','max_currency','max_eridium','max_player_level','max_spec_level','max_sdu','give_currency','set_level','set_backpack_bank_selected','shiny_selected','devperk_4']);
  window.runParityScopedAction=async button=>{
    const action=button?.dataset?.action;if(!scoped.has(action)||button._quickPayload)return false;
    const scope=$('boostScope').value,host=lastStatus?.host_player_index??0;
    const targets=scope==='selected'?[resolveTargetValue(currentTarget(),state.players)]:state.players.filter(p=>scope==='all'||(scope==='local'?Number(p.index)===Number(host):Number(p.index)!==Number(host))).map(playerValue);
    if(!targets.length||targets.some(t=>!t)){alert('Select a current player first.');return true;}
    state.busy=true;setLiveEnabled();
    try{
      const payload=buildActionPayload(action,button);let complete=0;
      for(const target of targets){
        const fresh=await gatewayFetch('/status',{timeoutMs:10000});if(!fresh.ok)throw new Error('Cannot refresh the party.');
        const resolved=resolveTargetValue(target,fresh.data.players||[]);if(!resolved)throw new Error(`${target} left the party; stopped.`);
        const result=await gatewayAction(action,{...payload,target_player:resolved},action==='max_all'?180000:45000);
        if(!result.ok)throw new Error(result.data?.message||`${action} failed for ${resolved}`);
        complete++;logActivity(`${action}: ${resolved} completed (${complete}/${targets.length}).`);
      }
    }catch(error){logActivity(error.message);alert(error.message);}finally{state.busy=false;setLiveEnabled();}
    return true;
  };
  const helpers=card('boost','<h3>Shops & helpers</h3><small>Black Market, chest spawning and challenges require the host. Firmware Transfer opens on the host PC.</small><div class="button-grid"></div>');
  for(const [action,label] of [['spawn_black_market','Spawn Black Market'],['black_market_status','Black Market Status'],['black_market_clear_cooldown','Clear Market Cooldown'],['spawn_golden_chest','Spawn Golden Chest'],['open_firmware_transfer','Firmware Transfer'],['uvh_boost_resume','Resume UVH'],['reset_skills','Reset Host Skills']]){
    const b=document.createElement('button');b.textContent=label;b.dataset.live='';b.dataset.action=action;b.addEventListener('click',()=>runLiveAction(b));helpers.querySelector('.button-grid').append(b);
  }
  const challenge=card('boost','<h3>Challenges</h3><small>Host only. Completion permanently affects the live party; UVH is managed separately.</small><label>Category<input id="mobileChallengeCategory" value="All non-UVHM" list="mobileChallengeCategories"></label><datalist id="mobileChallengeCategories"></datalist><label>Search<input id="mobileChallengeSearch" type="search"></label><button id="mobileChallengeLoad">Load challenges</button><select id="mobileChallengeList" multiple size="6" aria-label="Challenges"></select><div class="button-grid"><button id="mobileChallengeSelected">Complete selected</button><button id="mobileChallengeCategoryGo">Complete category</button><button id="mobileChallengeAll">Complete all non-UVH</button><button id="mobileChallengeCancel">Cancel</button><button id="mobileChallengeStatus">Refresh status</button></div><details><summary>Challenge details & log</summary><pre id="mobileChallengeOutput" style="max-height:240px;overflow:auto"></pre></details>');
  const challengeCall=async(action,payload={},confirmWrite=false)=>{
    if(!state.online||state.busy)return;
    if(confirmWrite&&!confirm('Permanently complete these challenges for the live party?'))return;
    state.busy=true;setLiveEnabled();
    try{const r=await gatewayAction(action,payload);$('mobileChallengeOutput').textContent=JSON.stringify(r.data,null,2);if(!r.ok)throw new Error(r.data?.message||'Challenge action failed.');return r.data;}
    catch(e){alert(e.message);}finally{state.busy=false;setLiveEnabled();}
  };
  $('mobileChallengeLoad').onclick=async()=>{const d=await challengeCall('challenge_catalog_list',{category:$('mobileChallengeCategory').value,search:$('mobileChallengeSearch').value});if(!d)return;$('mobileChallengeList').replaceChildren();for(const row of d.entries||[]){const o=document.createElement('option');o.value=row.id;o.textContent=`${row.id} (x${row.amount||1})`;$('mobileChallengeList').append(o);}for(const name of d.categories||[]){const o=document.createElement('option');o.value=name;$('mobileChallengeCategories').append(o);}};
  $('mobileChallengeSelected').onclick=()=>{const ids=[...$('mobileChallengeList').selectedOptions].map(o=>o.value);if(ids.length)void challengeCall('complete_challenges',{challenge_ids:ids},true);};
  $('mobileChallengeCategoryGo').onclick=()=>challengeCall('complete_challenges',{category:$('mobileChallengeCategory').value},true);
  $('mobileChallengeAll').onclick=()=>challengeCall('complete_challenges_all',{},true);
  $('mobileChallengeCancel').onclick=()=>challengeCall('complete_challenges_cancel');
  $('mobileChallengeStatus').onclick=()=>challengeCall('complete_challenges_status');

  document.querySelector('[data-screen="codes"] .filter-grid').insertAdjacentHTML('beforeend','<select id="mobileDlcFilter" aria-label="Content pack"><option value="">All content packs</option></select><select id="mobileLevelFilter" aria-label="Item level"><option value="">All item levels</option></select>');
  const oldPopulate=populateFilters;
  populateFilters=function(){const helper=window.MsbtGzoCodesForm;for(const row of state.codes){if(helper)row.manufacturer=helper.rowManufacturer(row)||row.manufacturer;if(row.level==null&&row.deserialized){const m=row.deserialized.match(/^\s*-?\d+\s*,\s*-?\d+\s*,\s*-?\d+\s*,\s*(\d+)\b/);if(m)row.level=Number(m[1]);}}oldPopulate();populateSelect('mobileDlcFilter',state.codes.map(r=>helper?helper.rowDlcLabel(r):r.dlc),'All content packs');populateSelect('mobileLevelFilter',state.codes.map(r=>r.level).filter(v=>v!==null&&v!==''&&v!==undefined),'All item levels');};
  const oldFilter=filterCodes;
  filterCodes=function(){oldFilter();const dlc=$('mobileDlcFilter').value,level=$('mobileLevelFilter').value;state.filteredCodes=state.filteredCodes.filter(r=>(!dlc||(window.MsbtGzoCodesForm?MsbtGzoCodesForm.matchesDlcFilter(r,dlc):r.dlc===dlc))&&(!level||String(r.level)===level));renderCodes();};
  $('mobileDlcFilter').onchange=filterCodes;$('mobileLevelFilter').onchange=filterCodes;
  for(const id of ['listingFilter','creatorFilter','sourceFilter','typeFilter','manufacturerFilter','rarityFilter'])$(id).addEventListener('change',()=>filterCodes());
  $('codeSearch').addEventListener('input',()=>filterCodes());
  const submit=card('codes',`<details id="mobileGzoForm"><summary>Submit your code to GZO</summary><p>Use the desktop gateway for decoding and submission. Keep MSBT open on your PC. Submissions go to GZO for review.</p>
    <label>Desktop gateway pairing code<input id="gzoPairing" type="password" inputmode="numeric" autocomplete="off" placeholder="From desktop Mobile Gateway"></label>
    <label>Item code<textarea id="gzoSerial" placeholder="Paste one @U item code"></textarea></label><button id="gzoPrepare">Decode & fill details</button>
    <label>Destination<select id="gzoListing"><option value="">Choose destination</option><option>Legit</option><option>Modded</option></select></label>
    <label>Display name<input id="gzoName"></label><label>Creator name<input id="gzoCreator"></label>
    <label>Manufacturer<select id="gzoCategory"></select></label><label>Type<select id="gzoType"></select></label>
    <label>Rarity<select id="gzoRarity"></select></label><label>Content pack<select id="gzoDlc"></select></label><label>Notes<textarea id="gzoNotes"></textarea></label>
    <label>Screenshot (optional replacement)<input id="gzoImage" type="file" accept="image/png,image/jpeg,image/webp"></label><img id="gzoPreview" alt="Submission screenshot" hidden style="max-width:100%;max-height:500px;object-fit:contain">
    <p id="gzoStatus">Decode to generate an image, or attach your own screenshot.</p><button id="gzoSend">Submit to GZO</button><button id="gzoReset">Reset form</button></details>`);
  const formHelper=window.MsbtGzoCodesForm;
  const submitLink=document.createElement('button');submitLink.textContent='Submit your code to GZO';submitLink.className='primary';
  document.querySelector('[data-screen="codes"] .title-row').after(submitLink);
  submitLink.onclick=()=>{$('mobileGzoForm').open=true;submit.scrollIntoView({behavior:'smooth',block:'start'});};
  const options=(id,values)=>{const el=$(id);el.replaceChildren();for(const value of values){const o=document.createElement('option');o.value=typeof value==='object'?value.value:value;o.textContent=typeof value==='object'?(value.label||value.value):value;el.append(o);}};
  options('gzoCategory',['',...(formHelper?.manufacturerKeys()||[])]);
  options('gzoRarity',['',...(formHelper?.GZO_SUBMIT_RARITIES||[])]);
  options('gzoDlc',['',...(formHelper?.GZO_DLC_OPTIONS||[])]);
  const syncTypes=()=>options('gzoType',['',...(formHelper?.typesForManufacturer($('gzoCategory').value)||[])]);
  $('gzoCategory').onchange=syncTypes;syncTypes();
  let revision=0,preparing=false,sending=false,imageBase64='',imageType='',human='',preparedSerial='',imageRevision=0;
  const dirty=new Set();
  for(const id of ['Name','Category','Type','Rarity','Dlc','Notes']){const el=$('gzo'+id);el.addEventListener('change',()=>dirty.add(id));el.addEventListener('input',()=>dirty.add(id));}
  const showImage=()=>{const img=$('gzoPreview');img.hidden=!imageBase64;if(imageBase64)img.src=`data:${imageType};base64,${imageBase64}`;else img.removeAttribute('src');};
  $('gzoSerial').addEventListener('input',()=>{revision++;imageRevision++;imageBase64='';human='';preparedSerial='';$('gzoImage').value='';showImage();$('gzoStatus').textContent='Code changed. Decode again or attach a new image.';});
  const desktopTool=async(route,payload)=>{
    const code=$('gzoPairing').value.trim()||state.connection.pairingCode;
    if(!state.connection.address||!code)throw new Error('Enter the PC address in Connection Settings and the desktop gateway pairing code here.');
    const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),90000);
    try{const r=await fetch(`http://${state.connection.address}:49775/mobile/gzo/${route}`,{method:'POST',headers:{'Content-Type':'application/json','X-MSBT-Pairing-Code':code},body:JSON.stringify(payload),signal:abort.signal});const d=await r.json();if(!r.ok||!d.ok)throw new Error(d.message||'Desktop service failed.');return d;}
    catch(e){if(e.name==='AbortError')throw new Error('Timed out. For submission, check GZO before retrying to avoid a duplicate.');throw e;}finally{clearTimeout(timer);}
  };
  $('gzoPrepare').onclick=async()=>{
    if(preparing||sending)return;const serial=$('gzoSerial').value.trim();if(!serial){$('gzoStatus').textContent='Paste an item code first.';return;}
    const rev=revision,imgRev=imageRevision;preparing=true;$('gzoPrepare').disabled=true;
    try{const d=await desktopTool('prepare',{serial});if(rev!==revision)return;human=d.human;preparedSerial=d.serial;
      for(const [key,id] of [['name','Name'],['category','Category'],['type','Type'],['rarity','Rarity'],['dlc','Dlc'],['notes','Notes']]){
        if(dirty.has(id)||!d.fields?.[key])continue;const el=$('gzo'+id),value=d.fields[key];
        if(el.tagName==='SELECT'&&![...el.options].some(o=>o.value===value)){const o=document.createElement('option');o.value=value;o.textContent=value;el.append(o);}el.value=value;if(id==='Category')syncTypes();
      }
      if(d.capture?.ok&&imgRev===imageRevision){imageBase64=d.capture.base64;imageType='image/png';showImage();}
      $('gzoStatus').textContent=d.capture?.ok?'Details ready. Review them before submitting.':'Details ready; image capture failed. Attach your screenshot.';
    }catch(e){if(rev===revision)$('gzoStatus').textContent=e.message;}finally{preparing=false;$('gzoPrepare').disabled=false;}
  };
  $('gzoImage').onchange=async()=>{const file=$('gzoImage').files[0],rev=revision,imgRev=++imageRevision;if(!file)return;if(file.size>8*1024*1024||!['image/png','image/jpeg','image/webp'].includes(file.type)){$('gzoStatus').textContent='Choose PNG, JPEG or WebP smaller than 8 MB.';return;}const reader=new FileReader();reader.onload=()=>{if(rev!==revision||imgRev!==imageRevision)return;imageBase64=String(reader.result).split(',')[1];imageType=file.type;showImage();};reader.readAsDataURL(file);};
  $('gzoSend').onclick=async()=>{
    if(sending||preparing)return;
    const payload={base85:preparedSerial||$('gzoSerial').value.trim(),deserialized:human,imageBase64,imageType};
    for(const [key,id] of [['listing','Listing'],['name','Name'],['creator','Creator'],['category','Category'],['type','Type'],['rarity','Rarity'],['dlc','Dlc'],['notes','Notes']])payload[key]=$('gzo'+id).value.trim();
    if(!payload.listing||!payload.name||!payload.creator||!payload.base85||!imageBase64){$('gzoStatus').textContent='Choose a destination, enter name, creator and code, and attach an image.';return;}
    sending=true;for(const el of submit.querySelectorAll('input,select,textarea,button'))el.disabled=true;
    try{const d=await desktopTool('submit',payload);$('gzoStatus').textContent=d.message||'Submitted for review.';$('gzoSerial').value='';revision++;imageBase64='';human='';preparedSerial='';showImage();}
    catch(e){$('gzoStatus').textContent=e.message;}finally{sending=false;for(const el of submit.querySelectorAll('input,select,textarea,button'))el.disabled=false;}
  };
  $('gzoReset').onclick=()=>{if(sending)return;revision++;imageRevision++;dirty.clear();for(const id of ['Serial','Name','Category','Type','Rarity','Dlc','Notes','Image'])$('gzo'+id).value='';$('gzoListing').value='';imageBase64='';human='';preparedSerial='';showImage();$('gzoStatus').textContent='Ready for a new code.';};
  populateFilters();filterCodes();setLiveEnabled();
})();
