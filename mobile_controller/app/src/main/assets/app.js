const $=(id)=>document.getElementById(id);
const $$=(selector)=>[...document.querySelectorAll(selector)];
const STORE={connection:'msbt.mobile.connection.v1',bookmarks:'msbt.mobile.bookmarks.v1',movement:'msbt.mobile.movement.v1',quick:'msbt.mobile.quick.v1',activity:'msbt.mobile.activity.v1',target:'msbt.mobile.target.v1'};
const PLAYER_SCOPED=new Set(['max_all','max_currency','max_eridium','max_player_level','max_spec_level','max_sdu','give_currency','set_level','give_serial_selected']);
const state={online:false,bridgeOnline:false,codes:[],filteredCodes:[],selectedCodes:new Set(),activeQuickPage:0,quick:null,bookmarks:[],connection:{},activity:[],players:[],selectedTarget:'',pollTimer:null,busy:false};
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
const write=(key,value)=>localStorage.setItem(key,JSON.stringify(value));
const now=()=>new Date().toISOString();
const esc=(value)=>String(value??'').replace(/[&<>"']/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const text=(value)=>String(value??'').trim();
const compact=(value)=>text(value).toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,'');
const validSerial=(value)=>/^@U[!-~]+$/.test(text(value));
const intValue=(value,fallback=0)=>{const n=Number.parseInt(String(value??'').trim(),10);return Number.isFinite(n)?n:fallback};

function logActivity(message){state.activity.unshift({at:now(),message});state.activity=state.activity.slice(0,100);write(STORE.activity,state.activity);renderActivity();$('recentResult').textContent=message}
function setLiveEnabled(){$$('[data-live]').forEach((button)=>button.disabled=!state.online||state.busy)}
function playerValue(player){const index=player&&player.index;const name=player&&player.name?String(player.name):'';if(index===null||index===undefined||index==='')return name;return name?`${index}|${name}`:String(index)}
function playerLabel(player){const index=player&&player.index;const name=player&&player.name?String(player.name):'';if(index===null||index===undefined||index==='')return name||'Unknown player';return `${index} | ${name||'Unknown player'}`}
function gatewayBase(){const address=text(state.connection.address);const port=text(state.connection.port)||'49775';if(!address)return '';return `http://${address}:${port}`}
function updateConnectionChrome(){
  const badge=$('connectionBadge');
  const paired=Boolean(text(state.connection.address)&&text(state.connection.pairingCode));
  badge.textContent=state.online?'ONLINE':(paired?'SAVED':'OFFLINE');
  badge.className=`badge ${state.online?'online':'offline'}`;
  $('pcSummary').textContent=state.connection.name||state.connection.address||'Not paired';
  $('desktopStatus').textContent=state.online?'Gateway online':'Offline';
  $('bridgeStatus').textContent=state.bridgeOnline?'Online':(state.online?'Waiting for game':'Offline');
  $('homeStatusTitle').textContent=state.online?(state.bridgeOnline?'Connected to game':'Gateway online — start Borderlands 4'):(paired?'PC saved — tap Connect':'PC not paired');
  $('homeStatusText').textContent=state.online
    ? (state.bridgeOnline?'Live actions are enabled for this paired session.':'Desktop MSBT gateway is reachable. Launch Borderlands 4 with the MSBT SDK mod for live game actions.')
    : 'Offline tools stay usable. Live actions unlock when desktop MSBT Mobile Gateway is paired on the same Wi‑Fi.';
  $('targetSummary').textContent=state.selectedTarget||'None';
  setLiveEnabled();
}

$$('[data-nav]').forEach((button)=>button.addEventListener('click',()=>{ $$('[data-nav]').forEach(x=>x.classList.remove('active'));button.classList.add('active');$$('.screen').forEach(screen=>screen.classList.toggle('active',screen.dataset.screen===button.dataset.nav));window.scrollTo(0,0)}));
$$('[data-open-panel]').forEach((button)=>button.addEventListener('click',()=>{const panel=$(button.dataset.openPanel);if(panel)panel.classList.toggle('hidden')}));

function normalizeCode(raw,source){
  const serial=text(raw?.serial||raw?.code||raw?.base85||raw?.Base85||raw?.value);
  if(!validSerial(serial))return null;
  const name=text(raw?.name||raw?.title||raw?.label||raw?.displayName||raw?.itemName)||`${source} Serial`;
  const type=text(raw?.type||raw?.itemType||raw?.category||raw?.item_category||raw?.gear_type);
  return {id:`${source}:${compact(raw?.id||raw?.uuid||raw?.key||serial.slice(0,20))}`,name,serial,source,type,category:text(raw?.category||raw?.group||type),manufacturer:text(raw?.manufacturer||raw?.maker||raw?.mfr),rarity:text(raw?.rarity||raw?.quality),creator:text(raw?.creator||raw?.author||raw?.creatorName),listing:text(raw?.listing||raw?.targetListing||raw?.destination||source),image:text(raw?.image_url||raw?.imageUrl||raw?.image||raw?.thumbnail||raw?.screenshot||raw?.picture),url:text(raw?.url||raw?.websiteUrl||raw?.lootlemon_url||raw?.link),tags:Array.isArray(raw?.tags)?raw.tags.map(text):text(raw?.tags).split(/[;,|]/).map(text).filter(Boolean)};
}
function walkCatalog(value,source,out,seen){
  if(Array.isArray(value)){value.forEach(v=>walkCatalog(v,source,out,seen));return}
  if(!value||typeof value!=='object')return;
  const row=normalizeCode(value,source);if(row&&!seen.has(row.serial.toLowerCase())){seen.add(row.serial.toLowerCase());out.push(row)}
  Object.values(value).forEach(v=>{if(v&&typeof v==='object')walkCatalog(v,source,out,seen)});
}
async function readBundledAssetText(file){
  // Primary: relative fetch under WebViewAssetLoader https://appassets.androidplatform.net/assets/
  try{
    const response=await fetch(file);
    if(response.ok){
      const textBody=await response.text();
      if(textBody&&textBody.length)return textBody;
    }
    throw new Error(response.ok?'empty response':`HTTP ${response.status}`);
  }catch(fetchError){
    // Fallback: narrow native bridge (avoid for multi-MB GZO when fetch works).
    if(window.MSBTAssets&&typeof window.MSBTAssets.readText==='function'){
      const raw=window.MSBTAssets.readText(file);
      if(typeof raw!=='string'||!raw.length)throw new Error(`empty native asset read for ${file} (fetch: ${fetchError&&fetchError.message?fetchError.message:fetchError})`);
      let parsed=null;
      try{parsed=JSON.parse(raw)}catch{throw new Error(`native asset for ${file} is not valid JSON`)}
      if(parsed&&parsed.__msbtAssetError)throw new Error(parsed.message||`native asset error for ${file}`);
      return raw;
    }
    throw fetchError;
  }
}
async function loadCatalogFile(file,source){
  try{
    const textBody=await readBundledAssetText(file);
    const json=JSON.parse(textBody);
    const out=[];walkCatalog(json,source,out,new Set());
    return {rows:out,error:null};
  }catch(error){
    console.warn('Catalog load failed',file,error);
    return {rows:[],error:error&&error.message?error.message:String(error)};
  }
}
async function loadCatalogs(){
  $('catalogStatus').textContent='Loading bundled catalog…';
  const [gzo,lootlemon,custom]=await Promise.all([
    loadCatalogFile('MattsSDKBoostingTools_gzo_codes.json','GZO'),
    loadCatalogFile('MattsSDKBoostingTools_lootlemon_codes.json','Lootlemon'),
    loadCatalogFile('custom_bl4_codes.json','MSBT Custom')
  ]);
  const merged=[];const seen=new Set();
  [...gzo.rows,...lootlemon.rows,...custom.rows].forEach(row=>{const key=row.serial.toLowerCase();if(!seen.has(key)){seen.add(key);merged.push(row)}});
  state.codes=merged;
  populateFilters();filterCodes();
  const errors=[gzo,lootlemon,custom].map((part,i)=>part.error?`${['GZO','Lootlemon','MSBT'][i]}: ${part.error}`:null).filter(Boolean);
  if(!merged.length){
    $('catalogStatus').textContent=`Bundled catalog unavailable: ${errors.join(' · ')||'no valid @U serials found in assets'}`;
    logActivity($('catalogStatus').textContent);
    return;
  }
  const suffix=errors.length?` · warnings: ${errors.join(' · ')}`:'';
  $('catalogStatus').textContent=`${merged.length.toLocaleString()} bundled codes · GZO ${gzo.rows.length} · Lootlemon ${lootlemon.rows.length} · MSBT ${custom.rows.length}${suffix}`;
}
function populateSelect(id,values,label){const select=$(id);const current=select.value;select.innerHTML=`<option value="">${label}</option>`;[...new Set(values.map(text).filter(Boolean))].sort((a,b)=>a.localeCompare(b)).forEach(value=>{const o=document.createElement('option');o.value=value;o.textContent=value;select.appendChild(o)});select.value=current}
function populateFilters(){populateSelect('sourceFilter',state.codes.map(x=>x.source),'All sources');populateSelect('typeFilter',state.codes.flatMap(x=>[x.type,x.category]),'All types');populateSelect('manufacturerFilter',state.codes.map(x=>x.manufacturer),'All manufacturers');populateSelect('rarityFilter',state.codes.map(x=>x.rarity),'All rarities')}
function filterCodes(){const q=text($('codeSearch').value).toLowerCase(),src=$('sourceFilter').value,type=$('typeFilter').value,mfr=$('manufacturerFilter').value,rarity=$('rarityFilter').value;state.filteredCodes=state.codes.filter(row=>{const blob=[row.name,row.source,row.type,row.category,row.manufacturer,row.rarity,row.creator,row.listing,...row.tags].join(' ').toLowerCase();return(!q||blob.includes(q))&&(!src||row.source===src)&&(!type||row.type===type||row.category===type)&&(!mfr||row.manufacturer===mfr)&&(!rarity||row.rarity===rarity)});renderCodes()}
function renderCodes(){const list=$('codeList');list.innerHTML='';state.filteredCodes.slice(0,300).forEach(row=>{const selected=state.selectedCodes.has(row.id);const card=document.createElement('div');card.className=`code-card${selected?' selected':''}`;const image=row.image?`<img src="${esc(row.image)}" alt="" loading="lazy" onerror="this.parentElement.textContent='BL4'">`:'BL4';card.innerHTML=`<input type="checkbox" ${selected?'checked':''} aria-label="Select ${esc(row.name)}"><span class="code-thumb">${image}</span><span><strong>${esc(row.name)}</strong><br><small>${esc([row.source,row.type||row.category,row.manufacturer,row.rarity].filter(Boolean).join(' · '))}</small></span><button type="button">›</button>`;card.querySelector('input').addEventListener('change',e=>{if(e.target.checked)state.selectedCodes.add(row.id);else state.selectedCodes.delete(row.id);renderCodes();updateSelectionSummary()});card.querySelector('button').addEventListener('click',()=>showCodeDetail(row));list.appendChild(card)});if(state.filteredCodes.length>300){const p=document.createElement('small');p.className='muted';p.textContent=`Showing first 300 of ${state.filteredCodes.length}. Refine filters to narrow results.`;list.appendChild(p)}if(!state.filteredCodes.length)list.innerHTML='<div class="card"><p>No matching codes.</p></div>';updateSelectionSummary()}
function showCodeDetail(row){const details=[row.name,row.source,row.type||row.category,row.manufacturer,row.rarity,row.creator,row.serial].filter(Boolean).join('\n');alert(details)}
function updateSelectionSummary(){$('selectionSummary').textContent=`${state.selectedCodes.size} selected`}
$('codeSearch').addEventListener('input',filterCodes);['sourceFilter','typeFilter','manufacturerFilter','rarityFilter'].forEach(id=>$(id).addEventListener('change',filterCodes));
$('selectAllCodes').addEventListener('click',()=>{state.filteredCodes.forEach(row=>state.selectedCodes.add(row.id));renderCodes()});$('clearCodeSelection').addEventListener('click',()=>{state.selectedCodes.clear();renderCodes()});
$('refreshCodes').addEventListener('click',async()=>{await loadCatalogs();logActivity('Reloaded the bundled BL4 Codes cache. Online GZO refresh will use the same screen once PC/network sync is enabled.')});

function initBookmarks(){state.bookmarks=read(STORE.bookmarks,[]);renderBookmarks()}
function renderBookmarks(){const q=text($('bookmarkSearch').value).toLowerCase(),rows=$('bookmarkRows');rows.innerHTML='';state.bookmarks.filter(b=>!q||`${b.name} ${b.group} ${b.serial}`.toLowerCase().includes(q)).forEach(b=>{const button=document.createElement('button');button.textContent=`${b.name||'Unnamed'}${b.group?` · ${b.group}`:''}`;button.addEventListener('click',()=>{$('bookmarkName').value=b.name;$('bookmarkGroup').value=b.group;$('bookmarkSerial').value=b.serial;$('bookmarkSerial').dataset.id=b.id});rows.appendChild(button)});if(!rows.children.length)rows.innerHTML='<small class="muted">No saved serial bookmarks.</small>'}
$('bookmarkSearch').addEventListener('input',renderBookmarks);$('saveBookmark').addEventListener('click',()=>{const serial=text($('bookmarkSerial').value);if(!validSerial(serial)){alert('Bookmark serial must be one valid @U serial.');return}const id=$('bookmarkSerial').dataset.id||`mobile-${Date.now()}`;const existing=state.bookmarks.find(b=>b.id===id);const record={...(existing||{}),id,name:text($('bookmarkName').value)||'Unnamed',group:text($('bookmarkGroup').value),serial,created_at:existing?.created_at||now(),updated_at:now(),metadata:existing?.metadata||{}};state.bookmarks=state.bookmarks.filter(b=>b.id!==id);state.bookmarks.push(record);write(STORE.bookmarks,state.bookmarks);$('bookmarkSerial').dataset.id=id;renderBookmarks();logActivity(`Saved serial bookmark: ${record.name}`)});$('deleteBookmark').addEventListener('click',()=>{const id=$('bookmarkSerial').dataset.id;if(!id)return;state.bookmarks=state.bookmarks.filter(b=>b.id!==id);write(STORE.bookmarks,state.bookmarks);$('bookmarkSerial').dataset.id='';$('bookmarkName').value='';$('bookmarkGroup').value='';$('bookmarkSerial').value='';renderBookmarks();logActivity('Deleted serial bookmark.')});

let boostConfirmed='';$('boostValidate').addEventListener('click',()=>{const serials=text($('boostSerialText').value).split(/\s+/).filter(Boolean);const ok=serials.length>0&&serials.every(validSerial);$('boostSerialStatus').textContent=ok?`${serials.length} valid @U serial(s).`:'Serial text contains an invalid value.'});$('boostConfirm').addEventListener('click',()=>{const value=text($('boostSerialText').value);const serials=value.split(/\s+/).filter(Boolean);if(!serials.length||!serials.every(validSerial)){alert('Validate the @U serials first.');return}boostConfirmed=value;$('boostSerialStatus').textContent='Confirmed for delivery. Editing the serials will invalidate confirmation.'});$('boostSerialText').addEventListener('input',()=>{if(boostConfirmed&&text($('boostSerialText').value)!==boostConfirmed){boostConfirmed='';$('boostSerialStatus').textContent='Serial changed; confirmation cleared.'}});

const MOVEMENT_DEFAULT={speedScale:'1.00',walkSpeed:'600',jumpHeight:'198',gravityScale:'1.00',stepHeight:'45',floorAngle:'44.8',glideSpeed:'1200',glideBoost:'0',glideAirControl:'0.60',dashSpeed:'2500',timeDilation:'1.00',sprintJumpGoal:'198',doubleJumpGoal:'198',slideJumpGoal:'198',individualJumpGoals:false,zeroVaultOnApply:false};
function loadMovement(){const preset={...MOVEMENT_DEFAULT,...read(STORE.movement,{})};$$('[data-movement]').forEach(el=>{const key=el.dataset.movement;if(el.type==='checkbox')el.checked=!!preset[key];else el.value=preset[key]??''})}
$('saveMovement').addEventListener('click',()=>{const preset={};$$('[data-movement]').forEach(el=>preset[el.dataset.movement]=el.type==='checkbox'?el.checked:text(el.value));write(STORE.movement,preset);$('movementStatus').textContent='Preset saved locally. It will remain available offline.';logActivity('Saved movement preset locally.')});

function defaultQuick(){return{version:1,baseRevision:'',localRevision:now(),dirty:false,pages:Array.from({length:5},(_,page)=>({name:`Page ${page+1}`,slots:Array.from({length:21},(_,index)=>({slot:index+1,commandId:'',label:`Slot ${index+1}`,payload:null,renamed:false}))}))}}
function loadQuick(){state.quick={...defaultQuick(),...read(STORE.quick,defaultQuick())};if(!Array.isArray(state.quick.pages)||!state.quick.pages.length)state.quick=defaultQuick();renderQuick()}
function saveQuick(){state.quick.localRevision=now();state.quick.dirty=true;write(STORE.quick,state.quick);$('quickSyncStatus').textContent='Offline changes saved on this phone. They will not be discarded when a PC connects.';$('quickResolve').disabled=true}
function renderQuick(){const pages=$('quickPages');pages.innerHTML='';state.quick.pages.forEach((page,i)=>{const b=document.createElement('button');b.textContent=`${i+1}`;b.classList.toggle('active',i===state.activeQuickPage);b.addEventListener('click',()=>{state.activeQuickPage=i;renderQuick()});pages.appendChild(b)});$('quickPageLabel').textContent=`Page ${state.activeQuickPage+1} / ${state.quick.pages.length}`;const grid=$('quickGrid');grid.innerHTML='';state.quick.pages[state.activeQuickPage].slots.forEach(slot=>{const b=document.createElement('button');b.textContent=slot.label||`Slot ${slot.slot}`;if(slot.renamed)b.classList.add('dirty');b.addEventListener('click',()=>editQuickSlot(slot));grid.appendChild(b)})}
function editQuickSlot(slot){const label=prompt('Quick Menu label',slot.label||`Slot ${slot.slot}`);if(label===null)return;slot.label=text(label)||`Slot ${slot.slot}`;slot.renamed=true;saveQuick();renderQuick()}
$('quickAddPage').addEventListener('click',()=>{if(state.quick.pages.length>=5){alert('Quick Menu already has the full five pages.');return}const index=state.quick.pages.length;state.quick.pages.push({name:`Page ${index+1}`,slots:Array.from({length:21},(_,i)=>({slot:i+1,commandId:'',label:`Slot ${i+1}`,payload:null,renamed:false}))});saveQuick();renderQuick()});
function mergeQuickLayouts(remote,local){const result=structuredClone(remote);const remoteByCommand=new Map();result.pages.forEach((p,pi)=>p.slots.forEach((s,si)=>{if(s.commandId)remoteByCommand.set(s.commandId,{p:pi,s:si})}));local.pages.forEach(page=>page.slots.forEach(localSlot=>{if(!localSlot.commandId&&!localSlot.renamed)return;const match=localSlot.commandId?remoteByCommand.get(localSlot.commandId):null;if(match){const target=result.pages[match.p].slots[match.s];if(localSlot.renamed)target.label=localSlot.label}else if(localSlot.commandId||localSlot.renamed){let page=result.pages[result.pages.length-1];let open=page.slots.find(s=>!s.commandId);if(!open&&result.pages.length<5){page={name:`Page ${result.pages.length+1}`,slots:Array.from({length:21},(_,i)=>({slot:i+1,commandId:'',label:`Slot ${i+1}`,payload:null,renamed:false}))};result.pages.push(page);open=page.slots[0]}if(open)Object.assign(open,structuredClone(localSlot))}}));result.dirty=false;result.baseRevision=remote.localRevision||remote.baseRevision||'';result.localRevision=now();return result}
function resolveQuickConflict(remote){if(!state.quick.dirty){state.quick=remote;write(STORE.quick,state.quick);renderQuick();return}const dialog=$('quickMergeDialog');$('quickResolve').disabled=false;$('quickResolve').onclick=()=>dialog.showModal();dialog.onclose=()=>{if(dialog.returnValue==='merge')state.quick=mergeQuickLayouts(remote,state.quick);else if(dialog.returnValue==='pc')state.quick=remote;else if(dialog.returnValue==='phone'){state.quick.baseRevision=remote.localRevision||remote.baseRevision||'';state.quick.dirty=true}else return;write(STORE.quick,state.quick);renderQuick();$('quickSyncStatus').textContent=state.quick.dirty?'Phone layout kept; pending upload to PC.':'Quick Menu conflict resolved.'}}

function fillPlayerSelects(){
  const options=state.players.length
    ? state.players.map((player)=>{const value=playerValue(player);return `<option value="${esc(value)}">${esc(playerLabel(player))}</option>`}).join('')
    : '<option value="">No players loaded</option>';
  ['boostTarget','codeTarget'].forEach((id)=>{
    const select=$(id);
    if(!select)return;
    const previous=state.selectedTarget||select.value;
    select.innerHTML=options;
    select.disabled=!state.online||!state.players.length;
    if(previous&&[...select.options].some((opt)=>opt.value===previous))select.value=previous;
    else if(select.options.length){select.selectedIndex=0;state.selectedTarget=select.value}
  });
  if(state.selectedTarget)write(STORE.target,{target:state.selectedTarget});
  $('targetSummary').textContent=state.selectedTarget||'None';
}
['boostTarget','codeTarget'].forEach((id)=>{
  const select=$(id);
  if(!select)return;
  select.addEventListener('change',()=>{state.selectedTarget=select.value;write(STORE.target,{target:state.selectedTarget});fillPlayerSelects();updateConnectionChrome()});
});

async function gatewayFetch(route,{method='GET',payload=null,timeoutMs=15000,requirePairing=true}={}){
  const base=gatewayBase();
  if(!base)throw new Error('Enter a PC address first.');
  const pairingCode=text(state.connection.pairingCode);
  if(requirePairing&&!pairingCode)throw new Error('Enter the pairing code from desktop MSBT → Activity → Mobile Gateway.');
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),timeoutMs);
  try{
    const headers={'Content-Type':'application/json',Accept:'application/json'};
    if(requirePairing)headers['X-MSBT-Pairing-Code']=pairingCode;
    const response=await fetch(`${base}${route}`,{method,headers,body:payload==null?undefined:JSON.stringify(payload),signal:controller.signal});
    const raw=await response.text();
    let data={};
    try{data=raw?JSON.parse(raw):{}}catch{data={ok:response.ok,message:raw}}
    return {ok:response.ok&&data.ok!==false,status:response.status,data};
  }catch(error){
    const message=error&&error.name==='AbortError'?'Connection timed out.':'Could not reach desktop MSBT gateway. Same Wi‑Fi? Firewall allowing port 49775? Desktop app open?';
    throw new Error(message);
  }finally{clearTimeout(timer)}
}

async function gatewayAction(action,payload={},timeoutMs=30000){
  const result=await gatewayFetch('/action',{method:'POST',payload:{action,payload,timeout:Math.max(5,Math.floor(timeoutMs/1000))},timeoutMs});
  return result;
}

function applyStatus(data){
  state.bridgeOnline=Boolean(data&&data.ok!==false&&(data.started||data.players||data.name));
  state.players=Array.isArray(data&&data.players)?data.players:[];
  if(data&&data.selected_player){
    const selected=state.players.find((player)=>String(player.name||'')===String(data.selected_player)||playerValue(player)===String(data.selected_player));
    if(selected)state.selectedTarget=playerValue(selected);
  }
  if(!state.selectedTarget){
    const saved=read(STORE.target,{});
    if(saved.target)state.selectedTarget=saved.target;
  }
  fillPlayerSelects();
  updateConnectionChrome();
}

async function connectGateway({quiet=false}={}){
  state.connection={name:text($('pcName').value)||state.connection.name||'',address:text($('pcAddress').value)||state.connection.address||'',port:text($('pcPort').value)||state.connection.port||'49775',pairingCode:text($('pairingCode').value)||state.connection.pairingCode||'',updated_at:now()};
  write(STORE.connection,state.connection);
  if(!text(state.connection.address)||!text(state.connection.pairingCode)){
    state.online=false;state.bridgeOnline=false;updateConnectionChrome();
    const message='Save a PC address and pairing code first.';
    $('connectionStatus').textContent=message;
    if(!quiet)alert(message);
    return false;
  }
  try{
    const ping=await gatewayFetch('/mobile/ping',{requirePairing:false,timeoutMs:5000});
    if(!ping.ok&&ping.status)throw new Error((ping.data&&ping.data.message)||'Gateway ping failed.');
    const status=await gatewayFetch('/status',{timeoutMs:8000});
    if(status.status===401)throw new Error('Invalid pairing code. Copy the current code from desktop MSBT → Activity → Mobile Gateway.');
    if(status.status===0)throw new Error((status.data&&status.data.message)||'Could not reach desktop MSBT gateway.');
    // 502 means gateway is up but the in-game SDK bridge is offline — still a successful pair.
    if(!status.ok&&status.status!==502)throw new Error((status.data&&status.data.message)||`Gateway returned HTTP ${status.status}.`);
    state.online=true;
    applyStatus(status.status===502?{ok:false}:status.data||{});
    const message=state.bridgeOnline
      ? `Connected to ${state.connection.address}:${state.connection.port||49775}. Game bridge online (${state.players.length} player(s)).`
      : `Gateway reachable at ${state.connection.address}:${state.connection.port||49775}. Start Borderlands 4 with MSBT for live actions.`;
    $('connectionStatus').textContent=message;
    if(!quiet)logActivity(message);
    startStatusPolling();
    return true;
  }catch(error){
    state.online=false;state.bridgeOnline=false;state.players=[];fillPlayerSelects();updateConnectionChrome();stopStatusPolling();
    const message=error&&error.message?error.message:String(error);
    $('connectionStatus').textContent=message;
    if(!quiet){logActivity(`Connect failed: ${message}`);alert(message)}
    return false;
  }
}

function disconnectGateway(){
  stopStatusPolling();
  state.online=false;state.bridgeOnline=false;state.players=[];
  fillPlayerSelects();updateConnectionChrome();
  $('connectionStatus').textContent='Disconnected. Saved setup kept on this phone.';
  logActivity('Disconnected from desktop MSBT gateway.');
}

function startStatusPolling(){
  stopStatusPolling();
  state.pollTimer=window.setInterval(async()=>{
    if(!state.online||state.busy)return;
    try{
      const status=await gatewayFetch('/status',{timeoutMs:8000});
      applyStatus(status.data||{});
    }catch{
      state.online=false;state.bridgeOnline=false;updateConnectionChrome();
      $('connectionStatus').textContent='Lost gateway connection. Tap Connect / Test to retry.';
      stopStatusPolling();
    }
  },5000);
}
function stopStatusPolling(){if(state.pollTimer){window.clearInterval(state.pollTimer);state.pollTimer=null}}

function loadConnection(){
  state.connection=read(STORE.connection,{});
  const savedTarget=read(STORE.target,{});
  state.selectedTarget=savedTarget.target||'';
  $('pcName').value=state.connection.name||'';
  $('pcAddress').value=state.connection.address||'';
  $('pcPort').value=state.connection.port||'49775';
  $('pairingCode').value=state.connection.pairingCode||'';
  if(state.connection.address){
    $('connectionStatus').textContent=`Saved: ${state.connection.name||state.connection.address} · ${state.connection.address}:${state.connection.port||49775}`;
  }
  updateConnectionChrome();
}
$('saveConnection').addEventListener('click',()=>{
  state.connection={name:text($('pcName').value),address:text($('pcAddress').value),port:text($('pcPort').value)||'49775',pairingCode:text($('pairingCode').value),updated_at:now()};
  write(STORE.connection,state.connection);
  updateConnectionChrome();
  $('connectionStatus').textContent=state.connection.address?`Setup saved for ${state.connection.address}:${state.connection.port}. Tap Connect / Test.`:'Enter a PC address to complete setup.';
  logActivity('Saved PC connection setup.');
});
$('testConnection').addEventListener('click',()=>void connectGateway());
$('disconnectConnection').addEventListener('click',disconnectGateway);
const homeConnectBtn=$('homeConnectBtn');
if(homeConnectBtn)homeConnectBtn.addEventListener('click',()=>void connectGateway());

function expandSerialText(raw,copies){
  const serials=text(raw).split(/\s+/).filter(Boolean);
  const count=Math.max(1,Math.min(50,intValue(copies,1)));
  if(count<=1)return serials.join(' ');
  const expanded=[];
  for(let i=0;i<count;i+=1)expanded.push(...serials);
  return expanded.join(' ');
}
function movementPayload(){
  const preset={};$$('[data-movement]').forEach(el=>preset[el.dataset.movement]=el.type==='checkbox'?el.checked:text(el.value));
  const jump=Number(preset.jumpHeight||198);
  return{
    movement_speed_scale:Number(preset.speedScale||1),
    movement_walk_speed:Number(preset.walkSpeed||600),
    movement_jump_height:jump,
    movement_jump_velocity:jump,
    movement_gravity_scale:Number(preset.gravityScale||1),
    movement_step_height:Number(preset.stepHeight||45),
    movement_jump_count:2,
    movement_jump_off_z_factor:0.5,
    movement_floor_angle:Number(preset.floorAngle||44.8),
    movement_floor_z:0.71,
    movement_individual_jump_goals:Boolean(preset.individualJumpGoals),
    movement_sprint_jump_goal:Number(preset.sprintJumpGoal||jump),
    movement_double_jump_goal:Number(preset.doubleJumpGoal||jump),
    movement_slide_jump_goal:Number(preset.slideJumpGoal||jump),
    movement_glide_speed:Number(preset.glideSpeed||1200),
    movement_glide_boost:Number(preset.glideBoost||0),
    movement_glide_air_control:Number(preset.glideAirControl||0.6),
    movement_dash_speed:Number(preset.dashSpeed||2500),
    movement_zero_vault_on_apply:Boolean(preset.zeroVaultOnApply),
    movement_time_dilation:Number(preset.timeDilation||1),
    target_player:state.selectedTarget,
    infinite_jump_target:state.selectedTarget
  };
}
function buildActionPayload(action,button){
  if(action==='give_currency')return{currency_kind:text($('boostCurrencyKind').value)||'cash',amount:intValue($('boostCurrencyAmount').value,1000000)};
  if(action==='set_level')return{xp_track:text($('boostXpTrack').value)||'player',level:intValue($('boostXpLevel').value,60)};
  if(action==='movement_apply_all')return movementPayload();
  if(action==='give_serial_selected'||action==='give_serial_all'||action==='give_serial_nonhost'){
    const fromCodes=button&&button.dataset.serialSource==='codes';
    let serialText='';
    let copies=1;
    if(fromCodes){
      const selected=[...state.selectedCodes].map((id)=>state.codes.find((row)=>row.id===id)).filter(Boolean);
      if(!selected.length)throw new Error('Select one or more codes first.');
      serialText=selected.map((row)=>row.serial).join(' ');
      copies=intValue($('codeCopies').value,1);
    }else{
      serialText=text($('boostSerialText').value);
      if(!boostConfirmed||serialText!==boostConfirmed)throw new Error('Validate and Confirm the @U serials before sending.');
      const serials=serialText.split(/\s+/).filter(Boolean);
      if(!serials.length||!serials.every(validSerial))throw new Error('Serial text contains an invalid value.');
      copies=intValue($('boostCopies').value,1);
    }
    return{
      serial_text:expandSerialText(serialText,copies),
      serial_override_level:text($('boostOverride').value)==='yes',
      serial_level:intValue($('boostSerialLevel').value,60)
    };
  }
  return{};
}
async function runLiveAction(button){
  const action=text(button.dataset.action);
  if(!action){alert('This control is not wired for live actions yet.');return}
  if(!state.online){alert('Connect to desktop MSBT first (More → Connection Settings).');return}
  if(state.busy)return;
  state.busy=true;setLiveEnabled();
  try{
    if(PLAYER_SCOPED.has(action)){
      const target=text($('boostTarget').value)||state.selectedTarget;
      if(!target)throw new Error('Select a target player first. Tap Connect while in-game to load the party list.');
      state.selectedTarget=target;
      const setResult=await gatewayAction('set_target_player',{target_player:target},10000);
      if(!setResult.ok)throw new Error((setResult.data&&(setResult.data.message||setResult.data.error))||'Could not set target player.');
    }
    const payload=buildActionPayload(action,button);
    const result=await gatewayAction(action,payload,45000);
    const message=(result.data&&(result.data.message||result.data.error))||(result.ok?`${action} sent.`:`${action} failed.`);
    logActivity(`${action}: ${message}`);
    if(!result.ok)alert(message);
    else if(action==='refresh_players'||PLAYER_SCOPED.has(action)){
      try{const status=await gatewayFetch('/status',{timeoutMs:8000});applyStatus(status.data||{})}catch{/* keep prior status */}
    }
  }catch(error){
    const message=error&&error.message?error.message:String(error);
    logActivity(`${action||'live action'} failed: ${message}`);
    alert(message);
  }finally{state.busy=false;setLiveEnabled()}
}

function renderActivity(){const rows=$('activityRows');if(!rows)return;if(!state.activity.length){rows.innerHTML='<small class="muted">No activity yet.</small>';return}rows.innerHTML=state.activity.slice(0,30).map(item=>`<div><small class="muted">${esc(new Date(item.at).toLocaleString())}</small><br>${esc(item.message)}</div>`).join('')}
$('copyFeedbackTemplate').addEventListener('click',async()=>{const template=`MSBT MOBILE BETA FEEDBACK\n\nPhone make/model:\nAndroid version:\nMSBT Mobile version: 0.1.0-beta.2\nDesktop MSBT version (if connected):\n\nScreen/feature:\nWhat I expected:\nWhat happened:\nSteps to reproduce:\nDoes it happen every time? Yes / No / Sometimes\n\nScreenshots attached: Yes / No\nAnything else:`;try{await navigator.clipboard.writeText(template);alert('Feedback template copied. Send it with screenshots directly to FunkYouSHiFT in Discord DMs.')}catch{prompt('Copy this feedback template:',template)}});

$$('[data-live]').forEach(button=>button.addEventListener('click',()=>void runLiveAction(button)));

state.activity=read(STORE.activity,[]);setLiveEnabled();initBookmarks();loadMovement();loadQuick();loadConnection();renderActivity();loadCatalogs();
if(text(state.connection.address)&&text(state.connection.pairingCode))void connectGateway({quiet:true});
