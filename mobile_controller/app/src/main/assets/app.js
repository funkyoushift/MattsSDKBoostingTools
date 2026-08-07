const $=(id)=>document.getElementById(id);
const $$=(selector)=>[...document.querySelectorAll(selector)];
const STORE={connection:'msbt.mobile.connection.v1',bookmarks:'msbt.mobile.bookmarks.v1',movement:'msbt.mobile.movement.v1',quick:'msbt.mobile.quick.v1',activity:'msbt.mobile.activity.v1',target:'msbt.mobile.target.v1'};
const PLAYER_SCOPED=new Set(['max_all','max_currency','max_eridium','max_player_level','max_spec_level','max_sdu','give_currency','set_level','give_serial_selected','set_backpack_bank_selected','shiny_selected','movement_apply_all','movement_infinite_jump_selected_on','movement_infinite_jump_selected_off','movement_infinite_jump_toggle_selected','movement_teleport_to_slot','read_inventory','read_equipped_serials','read_backpack_serials']);
const state={online:false,bridgeOnline:false,codes:[],filteredCodes:[],selectedCodes:new Set(),activeQuickPage:0,quick:null,bookmarks:[],connection:{},activity:[],players:[],selectedTarget:'',pollTimer:null,busy:false,inventory:{equipped:[],backpack:[],selected:null},travel:{maps:[],stations:[],mode:'map',selected:null},pools:{rows:[],selected:null}};
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
const write=(key,value)=>localStorage.setItem(key,JSON.stringify(value));
const now=()=>new Date().toISOString();
const esc=(value)=>String(value??'').replace(/[&<>"']/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const text=(value)=>String(value??'').trim();
const compact=(value)=>text(value).toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,'');
const validSerial=(value)=>/^@U[!-~]+$/.test(text(value));
const intValue=(value,fallback=0)=>{const n=Number.parseInt(String(value??'').trim(),10);return Number.isFinite(n)?n:fallback};

function logActivity(message){state.activity.unshift({at:now(),message});state.activity=state.activity.slice(0,100);write(STORE.activity,state.activity);renderActivity();$('recentResult').textContent=message}
function setLiveEnabled(){
  $$('[data-live]').forEach((button)=>button.disabled=!state.online||state.busy);
  $$('[data-live-optional]').forEach((button)=>button.disabled=!state.online||state.busy);
  ['invRefresh','invEquipped','invBackpack'].forEach((id)=>{const el=$(id);if(el)el.disabled=!state.online||state.busy});
  const travelGo=$('travelGo');if(travelGo)travelGo.disabled=!state.online||state.busy||!state.travel.selected;
  const poolSpawn=$('poolSpawn');if(poolSpawn)poolSpawn.disabled=!state.online||state.busy||!state.pools.selected;
}
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
function openPanel(panelId,{scroll=true}={}){
  const panel=$(panelId);
  if(!panel)return false;
  const screen=panel.closest('.screen');
  if(screen&&screen.dataset.screen){
    $$('[data-nav]').forEach((nav)=>nav.classList.toggle('active',nav.dataset.nav===screen.dataset.screen));
    $$('.screen').forEach((node)=>node.classList.toggle('active',node===screen));
  }
  panel.classList.remove('hidden');
  if(scroll){
    requestAnimationFrame(()=>{try{panel.scrollIntoView({behavior:'smooth',block:'start'})}catch{panel.scrollIntoView()}});
  }
  return true;
}
$$('[data-open-panel]').forEach((button)=>button.addEventListener('click',()=>{
  const panelId=button.dataset.openPanel;
  const panel=$(panelId);
  if(!panel)return;
  // If already visible on the active screen, allow toggle closed; otherwise always open + navigate.
  const screen=panel.closest('.screen');
  const onActiveScreen=Boolean(screen&&screen.classList.contains('active'));
  if(onActiveScreen&&!panel.classList.contains('hidden')){
    panel.classList.add('hidden');
    return;
  }
  openPanel(panelId);
}));

function normalizeListingValue(raw,source,classification,tags){
  const sourceKey=compact(source);
  if(sourceKey==='lootlemon')return 'Lootlemon';
  let listing=text(raw?.listing||raw?.targetListing||raw?.destination||raw?.bucket||raw?.folder||raw?.legitOrModded||raw?.list);
  let key=compact(listing);
  // Custom Static is not a listing category on mobile — remap via classification/tags.
  if(!key||key==='custom_static'||key==='gzo'||key==='msbt_custom'||key==='custom'){
    const classKey=compact(classification||raw?.classification||raw?.legitOrModded);
    if(classKey==='modded')return 'Modded';
    if(classKey==='legit')return 'Legit';
    const tagKeys=(tags||[]).map(compact);
    if(tagKeys.includes('modded'))return 'Modded';
    if(tagKeys.includes('legit'))return 'Legit';
    return '';
  }
  if(key==='modded')return 'Modded';
  if(key==='legit')return 'Legit';
  if(key==='lootlemon')return 'Lootlemon';
  if(listing==='Modded'||listing==='Legit'||listing==='Lootlemon')return listing;
  return '';
}
function normalizeCode(raw,source){
  const serial=text(raw?.serial||raw?.code||raw?.base85||raw?.Base85||raw?.value);
  if(!validSerial(serial))return null;
  const name=text(raw?.name||raw?.title||raw?.label||raw?.displayName||raw?.itemName)||`${source} Serial`;
  const type=text(raw?.type||raw?.itemType||raw?.category||raw?.item_category||raw?.gear_type);
  const tags=Array.isArray(raw?.tags)?raw.tags.map(text):text(raw?.tags).split(/[;,|]/).map(text).filter(Boolean);
  const classification=text(raw?.classification||raw?.legitOrModded);
  const listing=normalizeListingValue(raw,source,classification,tags);
  // Selection/filter identity must be unique per serial. GZO catalog `id` values
  // collide across many Modded rows, which made Select All under-count (~433 vs ~600+).
  return {id:`${compact(source)}:${serial.toLowerCase()}`,name,serial,source,type,category:text(raw?.category||raw?.group||type),manufacturer:text(raw?.manufacturer||raw?.maker||raw?.mfr),rarity:text(raw?.rarity||raw?.quality),creator:text(raw?.creator||raw?.author||raw?.creatorName),classification,listing,image:text(raw?.image_url||raw?.imageUrl||raw?.image||raw?.thumbnail||raw?.screenshot||raw?.picture),url:text(raw?.url||raw?.websiteUrl||raw?.lootlemon_url||raw?.link),tags};
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
function populateSelect(id,values,label){const select=$(id);if(!select)return;const current=select.value;select.innerHTML=`<option value="">${label}</option>`;[...new Set(values.map(text).filter(Boolean))].sort((a,b)=>a.localeCompare(b)).forEach(value=>{const o=document.createElement('option');o.value=value;o.textContent=value;select.appendChild(o)});if([...select.options].some(opt=>opt.value===current))select.value=current}
function listingMatches(row,wanted){
  if(!wanted)return true;
  const key=wanted.toLowerCase();
  const tags=Array.isArray(row.tags)?row.tags.map(t=>String(t).toLowerCase()):[];
  return [row.listing,row.classification,row.source].some(item=>String(item||'').toLowerCase()===key)
    || tags.includes(key)
    || (key==='modded'&&(String(row.classification||'').toLowerCase()==='modded'||tags.includes('modded')))
    || (key==='legit'&&(String(row.classification||'').toLowerCase()==='legit'||tags.includes('legit')))
    || (key==='lootlemon'&&(String(row.source||'').toLowerCase()==='lootlemon'||String(row.listing||'').toLowerCase()==='lootlemon'));
}
function populateFilters(){
  // Listing options stay fixed: Modded / Legit / Lootlemon (never Custom Static).
  populateSelect('creatorFilter',state.codes.map(x=>x.creator),'All creators');
  populateSelect('sourceFilter',state.codes.map(x=>x.source),'All sources');
  populateSelect('typeFilter',state.codes.flatMap(x=>[x.type,x.category]),'All types');
  populateSelect('manufacturerFilter',state.codes.map(x=>x.manufacturer),'All manufacturers');
  populateSelect('rarityFilter',state.codes.map(x=>x.rarity),'All rarities');
}
function filterCodes(){
  const q=text($('codeSearch').value).toLowerCase();
  const listing=text($('listingFilter')&&$('listingFilter').value);
  const creator=text($('creatorFilter')&&$('creatorFilter').value);
  const src=$('sourceFilter').value,type=$('typeFilter').value,mfr=$('manufacturerFilter').value,rarity=$('rarityFilter').value;
  state.filteredCodes=state.codes.filter(row=>{
    const blob=[row.name,row.source,row.type,row.category,row.manufacturer,row.rarity,row.creator,row.listing,row.classification,...row.tags].join(' ').toLowerCase();
    return(!q||blob.includes(q))
      &&listingMatches(row,listing)
      &&(!creator||row.creator===creator)
      &&(!src||row.source===src)
      &&(!type||row.type===type||row.category===type)
      &&(!mfr||row.manufacturer===mfr)
      &&(!rarity||row.rarity===rarity);
  });
  renderCodes();
}
function renderCodes(){const list=$('codeList');list.innerHTML='';state.filteredCodes.slice(0,300).forEach(row=>{const selected=state.selectedCodes.has(row.id);const card=document.createElement('div');card.className=`code-card${selected?' selected':''}`;const image=row.image?`<img src="${esc(row.image)}" alt="" loading="lazy" onerror="this.parentElement.textContent='BL4'">`:'BL4';card.innerHTML=`<input type="checkbox" ${selected?'checked':''} aria-label="Select ${esc(row.name)}"><span class="code-thumb">${image}</span><span><strong>${esc(row.name)}</strong><br><small>${esc([row.listing||row.source,row.type||row.category,row.manufacturer,row.rarity,row.creator].filter(Boolean).join(' · '))}</small></span><button type="button">›</button>`;card.querySelector('input').addEventListener('change',e=>{if(e.target.checked)state.selectedCodes.add(row.id);else state.selectedCodes.delete(row.id);renderCodes();updateSelectionSummary()});card.querySelector('button').addEventListener('click',()=>showCodeDetail(row));list.appendChild(card)});if(state.filteredCodes.length>300){const p=document.createElement('small');p.className='muted';p.textContent=`Showing first 300 of ${state.filteredCodes.length}. Refine filters to narrow results.`;list.appendChild(p)}if(!state.filteredCodes.length)list.innerHTML='<div class="card"><p>No matching codes.</p></div>';updateSelectionSummary()}
function showCodeDetail(row){const details=[row.name,row.listing||row.source,row.source,row.type||row.category,row.manufacturer,row.rarity,row.creator,row.serial].filter(Boolean).join('\n');alert(details)}
function updateSelectionSummary(){
  const filtered=state.filteredCodes.length;
  const selected=state.selectedCodes.size;
  $('selectionSummary').textContent=filtered?`${selected} selected · ${filtered.toLocaleString()} filtered`:`${selected} selected`;
}
$('codeSearch').addEventListener('input',filterCodes);['listingFilter','creatorFilter','sourceFilter','typeFilter','manufacturerFilter','rarityFilter'].forEach(id=>{const el=$(id);if(el)el.addEventListener('change',filterCodes)});
$('selectAllCodes').addEventListener('click',()=>{state.filteredCodes.forEach(row=>state.selectedCodes.add(row.id));renderCodes()});$('clearCodeSelection').addEventListener('click',()=>{state.selectedCodes.clear();renderCodes()});
$('refreshCodes').addEventListener('click',async()=>{await loadCatalogs();logActivity('Reloaded the bundled BL4 Codes cache. Online GZO refresh will use the same screen once PC/network sync is enabled.')});

function initBookmarks(){state.bookmarks=read(STORE.bookmarks,[]);renderBookmarks()}
function renderBookmarks(){const q=text($('bookmarkSearch').value).toLowerCase(),rows=$('bookmarkRows');rows.innerHTML='';state.bookmarks.filter(b=>!q||`${b.name} ${b.group} ${b.serial}`.toLowerCase().includes(q)).forEach(b=>{const button=document.createElement('button');button.textContent=`${b.name||'Unnamed'}${b.group?` · ${b.group}`:''}`;button.addEventListener('click',()=>{$('bookmarkName').value=b.name||'';$('bookmarkGroup').value=b.group||'';$('bookmarkSerial').value=b.serial||'';$('bookmarkSerial').dataset.id=b.id});rows.appendChild(button)});if(!rows.children.length)rows.innerHTML='<small class="muted">No saved serial bookmarks.</small>'}
async function pullDesktopBookmarks({quiet=false}={}){
  if(!state.online){if(!quiet)alert('Connect to desktop MSBT first.');return false}
  try{
    const result=await gatewayFetch('/mobile/bookmarks',{timeoutMs:60000});
    if(!result.ok)throw new Error((result.data&&result.data.message)||`HTTP ${result.status}`);
    const rows=Array.isArray(result.data&&result.data.bookmarks)?result.data.bookmarks:[];
    state.bookmarks=rows.map((b)=>({id:b.id||`pc-${compact(b.serial||Date.now())}`,name:text(b.name)||'Unnamed',group:text(b.group)||'Default',serial:text(b.serial),created_at:b.created_at||now(),updated_at:b.updated_at||now(),metadata:b.metadata||{}})).filter((b)=>validSerial(b.serial));
    write(STORE.bookmarks,state.bookmarks);
    renderBookmarks();
    const message=`Pulled ${state.bookmarks.length} serial bookmark(s) from desktop MSBT.`;
    if($('bookmarkStatus'))$('bookmarkStatus').textContent=message;
    if(!quiet)logActivity(message);
    return true;
  }catch(error){
    const message=error&&error.message?error.message:String(error);
    if($('bookmarkStatus'))$('bookmarkStatus').textContent=`Pull failed: ${message}`;
    if(!quiet){logActivity(`Bookmark pull failed: ${message}`);alert(message)}
    return false;
  }
}
$('bookmarkSearch').addEventListener('input',renderBookmarks);$('saveBookmark').addEventListener('click',()=>{const serial=text($('bookmarkSerial').value);if(!validSerial(serial)){alert('Bookmark serial must be one valid @U serial.');return}const id=$('bookmarkSerial').dataset.id||`mobile-${Date.now()}`;const existing=state.bookmarks.find(b=>b.id===id);const record={...(existing||{}),id,name:text($('bookmarkName').value)||'Unnamed',group:text($('bookmarkGroup').value),serial,created_at:existing?.created_at||now(),updated_at:now(),metadata:existing?.metadata||{}};state.bookmarks=state.bookmarks.filter(b=>b.id!==id);state.bookmarks.push(record);write(STORE.bookmarks,state.bookmarks);$('bookmarkSerial').dataset.id=id;renderBookmarks();logActivity(`Saved serial bookmark: ${record.name}`)});$('deleteBookmark').addEventListener('click',()=>{const id=$('bookmarkSerial').dataset.id;if(!id)return;state.bookmarks=state.bookmarks.filter(b=>b.id!==id);write(STORE.bookmarks,state.bookmarks);$('bookmarkSerial').dataset.id='';$('bookmarkName').value='';$('bookmarkGroup').value='';$('bookmarkSerial').value='';renderBookmarks();logActivity('Deleted serial bookmark.')});
const pullDesktopBookmarksBtn=$('pullDesktopBookmarks');
if(pullDesktopBookmarksBtn)pullDesktopBookmarksBtn.addEventListener('click',()=>void pullDesktopBookmarks());
const bookmarkUseBoostBtn=$('bookmarkUseBoost');
if(bookmarkUseBoostBtn)bookmarkUseBoostBtn.addEventListener('click',()=>{
  const serial=text($('bookmarkSerial').value);
  if(!validSerial(serial)){alert('Pick or enter a valid @U serial first.');return}
  $('boostSerialText').value=serial;
  boostConfirmed='';
  $('boostSerialStatus').textContent='Loaded from bookmark — validate/confirm before send.';
  $$('[data-nav]').forEach((nav)=>nav.classList.toggle('active',nav.dataset.nav==='boost'));
  $$('.screen').forEach((node)=>node.classList.toggle('active',node.dataset.screen==='boost'));
  window.scrollTo(0,0);
  logActivity('Loaded bookmark serial into Boost sender.');
});

let boostConfirmed='';$('boostValidate').addEventListener('click',()=>{const serials=text($('boostSerialText').value).split(/\s+/).filter(Boolean);const ok=serials.length>0&&serials.every(validSerial);$('boostSerialStatus').textContent=ok?`${serials.length} valid @U serial(s).`:'Serial text contains an invalid value.'});$('boostConfirm').addEventListener('click',()=>{const value=text($('boostSerialText').value);const serials=value.split(/\s+/).filter(Boolean);if(!serials.length||!serials.every(validSerial)){alert('Validate the @U serials first.');return}boostConfirmed=value;$('boostSerialStatus').textContent='Confirmed for delivery. Editing the serials will invalidate confirmation.'});$('boostSerialText').addEventListener('input',()=>{if(boostConfirmed&&text($('boostSerialText').value)!==boostConfirmed){boostConfirmed='';$('boostSerialStatus').textContent='Serial changed; confirmation cleared.'}});

const MOVEMENT_DEFAULT={speedScale:'1.00',walkSpeed:'600',jumpHeight:'198',gravityScale:'1.00',stepHeight:'45',floorAngle:'44.8',floorZ:'0.71',glideSpeed:'1200',glideBoost:'0',glideAirControl:'0.60',dashSpeed:'2500',timeDilation:'1.00',sprintJumpGoal:'198',doubleJumpGoal:'198',slideJumpGoal:'198',individualJumpGoals:false,zeroVaultOnApply:false};
function loadMovement(){const preset={...MOVEMENT_DEFAULT,...read(STORE.movement,{})};$$('[data-movement]').forEach(el=>{const key=el.dataset.movement;if(el.type==='checkbox')el.checked=!!preset[key];else el.value=preset[key]??''})}
$('saveMovement').addEventListener('click',()=>{const preset={};$$('[data-movement]').forEach(el=>preset[el.dataset.movement]=el.type==='checkbox'?el.checked:text(el.value));write(STORE.movement,preset);$('movementStatus').textContent='Preset saved locally. It will remain available offline.';logActivity('Saved movement preset locally.')});

function defaultQuick(){return{version:1,baseRevision:'',localRevision:now(),dirty:false,pages:Array.from({length:5},(_,page)=>({name:`Page ${page+1}`,slots:Array.from({length:21},(_,index)=>({slot:index+1,commandId:'',label:`Slot ${index+1}`,payload:null,renamed:false}))}))}}
function loadQuick(){state.quick={...defaultQuick(),...read(STORE.quick,defaultQuick())};if(!Array.isArray(state.quick.pages)||!state.quick.pages.length)state.quick=defaultQuick();renderQuick()}
function saveQuick(){state.quick.localRevision=now();state.quick.dirty=true;write(STORE.quick,state.quick);$('quickSyncStatus').textContent='Offline changes saved on this phone. They will not be discarded when a PC connects.';$('quickResolve').disabled=true}
function mapBridgeQuickMenu(snapshot){
  const layout=snapshot&&snapshot.layout?snapshot.layout:{};
  const catalog=snapshot&&snapshot.catalog?snapshot.catalog:{};
  const rawPages=Array.isArray(layout.pages)?layout.pages:[];
  const pages=Array.from({length:5},(_,pageIndex)=>{
    const raw=rawPages[pageIndex];
    const slotsSource=Array.isArray(raw)?raw:(raw&&Array.isArray(raw.slots)?raw.slots:[]);
    return{
      name:`Page ${pageIndex+1}`,
      slots:Array.from({length:21},(_,slotIndex)=>{
        const slot=slotsSource[slotIndex]||null;
        const action=text(slot&&slot.action);
        if(!action)return{slot:slotIndex+1,commandId:'',label:`Slot ${slotIndex+1}`,payload:null,renamed:false};
        const custom=text(slot.custom_label);
        const basic=text(catalog[action]&&catalog[action].basic)||action;
        return{slot:slotIndex+1,commandId:action,label:custom||basic,payload:slot.payload&&typeof slot.payload==='object'?slot.payload:{},renamed:Boolean(custom)};
      })
    };
  });
  return{version:Number(snapshot&&snapshot.version)||1,baseRevision:String(layout.revision||snapshot.revision||now()),localRevision:now(),dirty:false,pages};
}
async function pullQuickMenuFromPc({quiet=false}={}){
  if(!state.online){if(!quiet)alert('Connect to desktop MSBT first.');return false}
  try{
    const result=await gatewayFetch('/quick_menu',{timeoutMs:12000});
    if(result.status===502)throw new Error('Game bridge offline. Launch Borderlands 4 with MSBT for live Quick Menu.');
    if(!result.ok)throw new Error((result.data&&result.data.message)||`HTTP ${result.status}`);
    const remote=mapBridgeQuickMenu(result.data||{});
    if(state.quick&&state.quick.dirty){
      resolveQuickConflict(remote);
      if(!quiet)logActivity('Quick Menu pulled from PC; local dirty layout needs conflict choice.');
      return true;
    }
    state.quick=remote;
    write(STORE.quick,state.quick);
    renderQuick();
    $('quickSyncStatus').textContent=`Loaded live Quick Menu from PC (revision ${state.quick.baseRevision||'n/a'}).`;
    if(!quiet)logActivity('Pulled live Quick Menu layout from PC.');
    return true;
  }catch(error){
    const message=error&&error.message?error.message:String(error);
    $('quickSyncStatus').textContent=`Quick Menu pull failed: ${message}`;
    if(!quiet){logActivity(`Quick Menu pull failed: ${message}`);alert(message)}
    return false;
  }
}
function renderQuick(){const pages=$('quickPages');pages.innerHTML='';state.quick.pages.forEach((page,i)=>{const b=document.createElement('button');b.textContent=`${i+1}`;b.classList.toggle('active',i===state.activeQuickPage);b.addEventListener('click',()=>{state.activeQuickPage=i;renderQuick()});pages.appendChild(b)});$('quickPageLabel').textContent=`Page ${state.activeQuickPage+1} / ${state.quick.pages.length}`;const grid=$('quickGrid');grid.innerHTML='';state.quick.pages[state.activeQuickPage].slots.forEach(slot=>{const b=document.createElement('button');b.textContent=slot.label||`Slot ${slot.slot}`;if(slot.renamed)b.classList.add('dirty');if(!slot.commandId)b.classList.add('empty');b.addEventListener('click',()=>void activateQuickSlot(slot));grid.appendChild(b)})}
async function activateQuickSlot(slot){
  if(state.online&&slot.commandId){
    const fakeButton={dataset:{action:slot.commandId},_quickPayload:slot.payload||{}};
    await runLiveAction(fakeButton);
    return;
  }
  const label=prompt(slot.commandId?'Rename Quick Menu label':`Empty slot ${slot.slot}. Connect and Pull From PC to load the live F7 menu, or set a local label.`,slot.label||`Slot ${slot.slot}`);
  if(label===null)return;
  slot.label=text(label)||`Slot ${slot.slot}`;
  slot.renamed=true;
  saveQuick();
  renderQuick();
}
const quickPullPcBtn=$('quickPullPc');
if(quickPullPcBtn)quickPullPcBtn.addEventListener('click',()=>void pullQuickMenuFromPc());
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
    if(state.bridgeOnline){
      void pullQuickMenuFromPc({quiet:true});
      void pullDesktopBookmarks({quiet:true});
    }
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
    movement_floor_z:Number(preset.floorZ||0.71),
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
  if(action==='set_backpack_bank_selected'||action==='set_backpack_bank_all')return{backpack_size:intValue($('boostBackpackSize').value,999),bank_size:intValue($('boostBankSize').value,1500)};
  if(action==='movement_apply_all')return movementPayload();
  if(action==='movement_set_time'){
    const preset={};$$('[data-movement]').forEach(el=>preset[el.dataset.movement]=el.type==='checkbox'?el.checked:text(el.value));
    return{movement_time_dilation:Number(preset.timeDilation||1)};
  }
  if(action==='movement_teleport_to_slot'){
    return{slot:Math.max(0,Math.min(3,intValue(button&&button.dataset.slot,0))),target_player:state.selectedTarget};
  }
  if(action==='movement_infinite_jump_selected_on'||action==='movement_infinite_jump_selected_off'||action==='movement_infinite_jump_toggle_selected'){
    return{target_player:state.selectedTarget,infinite_jump_target:state.selectedTarget};
  }
  if(action==='travel_to_map'){
    const map=state.travel.selected&&state.travel.selected.map;
    if(!map)throw new Error('Select a travel map first.');
    return{travel_map:map};
  }
  if(action==='travel_to_station'){
    const station=state.travel.selected&&state.travel.selected.station;
    if(!station)throw new Error('Select a travel station first.');
    return{travel_station:station};
  }
  if(action==='spawn_itempool'){
    const name=state.pools.selected&&(state.pools.selected.itempool||state.pools.selected.name);
    if(!name)throw new Error('Select an item pool first.');
    return{itempool_name:name,level:intValue($('poolLevel').value,60),count:intValue($('poolCount').value,1)};
  }
  if(button&&button._quickPayload&&typeof button._quickPayload==='object')return{...button._quickPayload};
  if(action==='give_serial_selected'||action==='give_serial_all'||action==='give_serial_nonhost'){
    const fromCodes=button&&button.dataset.serialSource==='codes';
    const fromBookmark=button&&button.dataset.serialSource==='bookmark';
    let serialText='';
    let copies=1;
    if(fromBookmark){
      serialText=text($('bookmarkSerial').value);
      if(!validSerial(serialText))throw new Error('Pick a bookmark serial first.');
      copies=1;
    }else if(fromCodes){
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
$('copyFeedbackTemplate').addEventListener('click',async()=>{const template=`MSBT MOBILE BETA FEEDBACK\n\nPhone make/model:\nAndroid version:\nMSBT Mobile version: 0.1.0-beta.6\nDesktop MSBT version (if connected):\n\nScreen/feature:\nWhat I expected:\nWhat happened:\nSteps to reproduce:\nDoes it happen every time? Yes / No / Sometimes\n\nScreenshots attached: Yes / No\nAnything else:`;try{await navigator.clipboard.writeText(template);alert('Feedback template copied. Send it with screenshots directly to FunkYouSHiFT in Discord DMs.')}catch{prompt('Copy this feedback template:',template)}});

function invEntryLabel(entry){
  return text(entry&&(entry.summary||entry.label||entry.name||entry.slot_name))||'Item';
}
function invAllRows(){
  return [...(state.inventory.equipped||[]).map((e)=>({...e,_bucket:'equipped'})),...(state.inventory.backpack||[]).map((e)=>({...e,_bucket:'backpack'}))];
}
function renderInventory(){
  const rows=$('invRows');if(!rows)return;
  const q=text($('invSearch')&&$('invSearch').value).toLowerCase();
  const list=invAllRows().filter((e)=>!q||`${invEntryLabel(e)} ${e.serial||''} ${e._bucket}`.toLowerCase().includes(q));
  rows.innerHTML='';
  list.slice(0,400).forEach((entry,index)=>{
    const button=document.createElement('button');
    const serial=text(entry.serial);
    button.textContent=`[${entry._bucket==='equipped'?'EQ':'BP'}] ${invEntryLabel(entry)}`;
    button.title=serial;
    button.className=state.inventory.selected&&state.inventory.selected.serial===serial?'selected':'';
    button.addEventListener('click',()=>{
      state.inventory.selected=entry;
      const use=$('invUseBoost');const bm=$('invSaveBookmark');
      if(use)use.disabled=!validSerial(serial);
      if(bm)bm.disabled=!validSerial(serial);
      renderInventory();
    });
    rows.appendChild(button);
  });
  if(!rows.children.length)rows.innerHTML='<small class="muted">No inventory rows. Refresh while in-game (listen host works best).</small>';
  if(list.length>400){
    const more=document.createElement('small');
    more.className='muted';
    more.textContent=`Showing 400 of ${list.length}. Refine the filter to narrow.`;
    rows.appendChild(more);
  }
}
async function ensureInventoryTarget(){
  const target=text($('boostTarget').value)||state.selectedTarget;
  if(!target)throw new Error('Select a target player on Boost first (Connect while in-game).');
  state.selectedTarget=target;
  const setResult=await gatewayAction('set_target_player',{target_player:target},10000);
  if(!setResult.ok)throw new Error((setResult.data&&(setResult.data.message||setResult.data.error))||'Could not set target player.');
  return target;
}
function applyInventoryResult(data,fallbackEquipped,fallbackBackpack){
  const inventory=data&&data.inventory?data.inventory:null;
  let equipped=inventory&&Array.isArray(inventory.equipped)?inventory.equipped:(fallbackEquipped||[]);
  let backpack=inventory&&Array.isArray(inventory.backpack)?inventory.backpack:(fallbackBackpack||[]);
  if((!equipped.length&&!backpack.length)&&data&&data.read_serials&&Array.isArray(data.read_serials.entries)){
    const entries=data.read_serials.entries;
    equipped=entries.filter((e)=>{const o=text(e.origin);return o==='equipped'||o==='active_weapon'||(Number.isFinite(Number(e.slot))&&Number(e.slot)>=0&&Number(e.slot)<=64)});
    const eqSet=new Set(equipped.map((e)=>text(e.serial)).filter(Boolean));
    backpack=entries.filter((e)=>!eqSet.has(text(e.serial)));
  }
  state.inventory={equipped,backpack,selected:null};
  const use=$('invUseBoost');const bm=$('invSaveBookmark');
  if(use)use.disabled=true;if(bm)bm.disabled=true;
  renderInventory();
  const message=(data&&data.message)||`Inventory: ${equipped.length} equipped, ${backpack.length} backpack.`;
  if($('invStatus'))$('invStatus').textContent=message;
  logActivity(message);
}
async function refreshInventory(mode='all'){
  if(!state.online){alert('Connect to desktop MSBT first.');return}
  if(state.busy)return;
  state.busy=true;setLiveEnabled();
  if($('invStatus'))$('invStatus').textContent='Reading inventory…';
  try{
    const target=await ensureInventoryTarget();
    const payload={target_player:target};
    if(mode==='equipped'){
      const result=await gatewayAction('read_equipped_serials',payload,60000);
      if(!result.ok&&!(result.data&&result.data.read_serials))throw new Error((result.data&&result.data.message)||'Equipped read failed.');
      const entries=(result.data&&result.data.read_serials&&result.data.read_serials.entries)||[];
      applyInventoryResult({...(result.data||{}),message:(result.data&&result.data.message)||`Equipped: ${entries.length}`},entries,[]);
      return;
    }
    if(mode==='backpack'){
      const result=await gatewayAction('read_backpack_serials',payload,60000);
      if(!result.ok&&!(result.data&&result.data.read_serials))throw new Error((result.data&&result.data.message)||'Backpack read failed.');
      const entries=(result.data&&result.data.read_serials&&result.data.read_serials.entries)||[];
      applyInventoryResult({...(result.data||{}),message:(result.data&&result.data.message)||`Backpack: ${entries.length}`},[],entries);
      return;
    }
    let result=await gatewayAction('read_inventory',payload,60000);
    let data=result.data||{};
    if(data.queued)throw new Error(data.message||'Inventory still queued — unpause in-game, then retry.');
    const unknown=/unknown action|unknown quick menu action/i.test(String(data.message||''));
    if((!result.ok&&unknown)||(result.ok&&!data.inventory)){
      const eq=await gatewayAction('read_equipped_serials',payload,60000);
      const bp=await gatewayAction('read_backpack_serials',payload,60000);
      const eqEntries=(eq.data&&eq.data.read_serials&&eq.data.read_serials.entries)||[];
      const bpEntries=(bp.data&&bp.data.read_serials&&bp.data.read_serials.entries)||[];
      applyInventoryResult({
        ok:true,
        message:`Inventory: ${eqEntries.length} equipped, ${bpEntries.length} backpack (legacy read).`,
        inventory:{equipped:eqEntries,backpack:bpEntries}
      });
      return;
    }
    if(!result.ok&&!(data.inventory&&((data.inventory.equipped||[]).length||(data.inventory.backpack||[]).length))){
      throw new Error(data.message||'Inventory refresh failed.');
    }
    applyInventoryResult(data);
  }catch(error){
    const message=error&&error.message?error.message:String(error);
    if($('invStatus'))$('invStatus').textContent=message;
    logActivity(`Inventory failed: ${message}`);
    alert(message);
  }finally{state.busy=false;setLiveEnabled()}
}
if($('invSearch'))$('invSearch').addEventListener('input',renderInventory);
if($('invRefresh'))$('invRefresh').addEventListener('click',()=>void refreshInventory('all'));
if($('invEquipped'))$('invEquipped').addEventListener('click',()=>void refreshInventory('equipped'));
if($('invBackpack'))$('invBackpack').addEventListener('click',()=>void refreshInventory('backpack'));
if($('invUseBoost'))$('invUseBoost').addEventListener('click',()=>{
  const serial=text(state.inventory.selected&&state.inventory.selected.serial);
  if(!validSerial(serial))return;
  $('boostSerialText').value=serial;boostConfirmed='';
  $('boostSerialStatus').textContent='Loaded from inventory — validate/confirm before send.';
  $$('[data-nav]').forEach((nav)=>nav.classList.toggle('active',nav.dataset.nav==='boost'));
  $$('.screen').forEach((node)=>node.classList.toggle('active',node.dataset.screen==='boost'));
  window.scrollTo(0,0);
});
if($('invSaveBookmark'))$('invSaveBookmark').addEventListener('click',()=>{
  const entry=state.inventory.selected;const serial=text(entry&&entry.serial);
  if(!validSerial(serial))return;
  const id=`inv-${compact(serial)}`;
  const record={id,name:invEntryLabel(entry),group:'Inventory',serial,created_at:now(),updated_at:now(),metadata:{}};
  state.bookmarks=state.bookmarks.filter((b)=>b.id!==id);state.bookmarks.push(record);
  write(STORE.bookmarks,state.bookmarks);renderBookmarks();
  $('bookmarkName').value=record.name;$('bookmarkGroup').value=record.group;$('bookmarkSerial').value=serial;$('bookmarkSerial').dataset.id=id;
  if($('invStatus'))$('invStatus').textContent=`Bookmarked ${record.name}.`;
  logActivity(`Bookmarked inventory serial: ${record.name}`);
});

function renderTravel(){
  const rows=$('travelRows');if(!rows)return;
  const mode=text($('travelMode')&&$('travelMode').value)||'map';
  state.travel.mode=mode;
  const q=text($('travelSearch')&&$('travelSearch').value).toLowerCase();
  const source=mode==='station'?state.travel.stations:state.travel.maps;
  const filtered=source.filter((row)=>{
    const hay=`${row.display_name||''} ${row.map||''} ${row.station||''} ${row.world||''} ${row.category||''}`.toLowerCase();
    return !q||hay.includes(q);
  }).slice(0,250);
  rows.innerHTML='';
  filtered.forEach((row)=>{
    const id=mode==='station'?row.station:row.map;
    const button=document.createElement('button');
    button.textContent=mode==='station'
      ? `${row.display_name||row.station_name||row.station}${row.world?` · ${row.world}`:''}`
      : `${row.display_name||row.map}${row.category?` · ${row.category}`:''}`;
    button.className=state.travel.selected&&((mode==='station'?state.travel.selected.station:state.travel.selected.map)===id)?'selected':'';
    button.addEventListener('click',()=>{
      state.travel.selected=row;
      const go=$('travelGo');
      if(go){
        go.dataset.action=mode==='station'?'travel_to_station':'travel_to_map';
        go.disabled=!state.online||state.busy;
      }
      if($('travelStatus'))$('travelStatus').textContent=`Selected: ${button.textContent}`;
      renderTravel();
    });
    rows.appendChild(button);
  });
  if(!rows.children.length)rows.innerHTML='<small class="muted">No travel entries match.</small>';
}
async function loadTravelCatalog(){
  try{
    const [mapsRaw,stationsRaw]=await Promise.all([
      readBundledAssetText('travelmaps_flat.json'),
      readBundledAssetText('travelstations.json')
    ]);
    const mapsJson=JSON.parse(mapsRaw);
    const stationsJson=JSON.parse(stationsRaw);
    state.travel.maps=Array.isArray(mapsJson.maps)?mapsJson.maps:[];
    state.travel.stations=Array.isArray(stationsJson.stations)?stationsJson.stations:[];
    if($('travelStatus'))$('travelStatus').textContent=`${state.travel.maps.length} maps · ${state.travel.stations.length} stations`;
    renderTravel();
  }catch(error){
    if($('travelStatus'))$('travelStatus').textContent=`Travel catalog unavailable: ${error&&error.message?error.message:error}`;
    if($('travelRows'))$('travelRows').innerHTML='<small class="muted">Travel catalog failed to load.</small>';
  }
}
if($('travelMode'))$('travelMode').addEventListener('change',()=>{state.travel.selected=null;setLiveEnabled();renderTravel()});
if($('travelSearch'))$('travelSearch').addEventListener('input',renderTravel);

function renderPools(){
  const rows=$('poolRows');if(!rows)return;
  const q=text($('poolSearch')&&$('poolSearch').value).toLowerCase();
  const filtered=state.pools.rows.filter((row)=>{
    const hay=`${row.display_name||''} ${row.itempool||''} ${row.category||''}`.toLowerCase();
    return !q||hay.includes(q);
  }).slice(0,300);
  rows.innerHTML='';
  filtered.forEach((row)=>{
    const button=document.createElement('button');
    button.textContent=`${row.display_name||row.itempool}${row.category?` · ${row.category}`:''}`;
    button.className=state.pools.selected&&state.pools.selected.itempool===row.itempool?'selected':'';
    button.addEventListener('click',()=>{
      state.pools.selected=row;
      const spawn=$('poolSpawn');
      if(spawn)spawn.disabled=!state.online||state.busy;
      if($('poolStatus'))$('poolStatus').textContent=`Selected: ${row.display_name||row.itempool}`;
      renderPools();
    });
    rows.appendChild(button);
  });
  if(!rows.children.length)rows.innerHTML='<small class="muted">No item pools match.</small>';
}
async function loadPoolCatalog(){
  try{
    const raw=await readBundledAssetText('item_pools.json');
    const json=JSON.parse(raw);
    state.pools.rows=Array.isArray(json)?json:(Array.isArray(json.pools)?json.pools:[]);
    if($('poolStatus'))$('poolStatus').textContent=`${state.pools.rows.length} item pools loaded`;
    renderPools();
  }catch(error){
    if($('poolStatus'))$('poolStatus').textContent=`Item pools unavailable: ${error&&error.message?error.message:error}`;
    if($('poolRows'))$('poolRows').innerHTML='<small class="muted">Item pool catalog failed to load.</small>';
  }
}
if($('poolSearch'))$('poolSearch').addEventListener('input',renderPools);

$$('[data-live]').forEach(button=>button.addEventListener('click',()=>void runLiveAction(button)));

state.activity=read(STORE.activity,[]);setLiveEnabled();initBookmarks();loadMovement();loadQuick();loadConnection();renderActivity();loadCatalogs();loadTravelCatalog();loadPoolCatalog();
if(text(state.connection.address)&&text(state.connection.pairingCode))void connectGateway({quiet:true});
