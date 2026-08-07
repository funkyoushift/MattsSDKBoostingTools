const $=(id)=>document.getElementById(id);
const $$=(selector)=>[...document.querySelectorAll(selector)];
const STORE={connection:'msbt.mobile.connection.v1',bookmarks:'msbt.mobile.bookmarks.v1',movement:'msbt.mobile.movement.v1',quick:'msbt.mobile.quick.v1',activity:'msbt.mobile.activity.v1',target:'msbt.mobile.target.v1',updateDismiss:'msbt.mobile.updateDismiss.v1'};
const PLAYER_SCOPED=new Set(['max_all','max_currency','max_eridium','max_player_level','max_spec_level','max_sdu','give_currency','set_level','give_serial_selected','set_backpack_bank_selected','shiny_selected','movement_apply_all','movement_infinite_jump_selected_on','movement_infinite_jump_selected_off','movement_infinite_jump_toggle_selected','movement_teleport_to_slot','read_inventory','read_equipped_serials','read_backpack_serials']);
const FALLBACK_APP_VERSION='0.1.0-beta.15';
const state={online:false,bridgeOnline:false,codes:[],filteredCodes:[],selectedCodes:new Set(),activeQuickPage:0,quick:null,bookmarks:[],selectedBookmarks:new Set(),movementPicks:new Set(),connection:{},activity:[],players:[],selectedTarget:'',pollTimer:null,busy:false,inventory:{equipped:[],backpack:[],selected:null,selectedIds:new Set()},travel:{maps:[],stations:[],selectedMap:null,selectedStation:null,showAllStations:false},pools:{rows:[],selected:null},dev:{categories:{},actors:[],filtered:[],category:'All',selected:'',page:0,pageSize:80,warningAccepted:false},update:{currentVersion:FALLBACK_APP_VERSION,availableVersion:'',apkUrl:'',updateAvailable:false,checking:false,lastMessage:''}};
const DEV_NEED_ACTOR=new Set(['dev_spawner_spawnai','dev_spawner_probeai','dev_spawner_cache','dev_spawner_spawn','dev_spawner_targets']);
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
  $$('[data-live]').forEach((button)=>{
    if(button.hasAttribute('data-dev-risk')){
      // Unlock after in-app risk accept. Online is enforced when the action runs.
      button.disabled=!state.dev.warningAccepted||state.busy;
    }else{
      button.disabled=!state.online||state.busy;
    }
  });
  $$('[data-live-optional]').forEach((button)=>button.disabled=!state.online||state.busy);
  ['invRefresh','invEquipped','invBackpack'].forEach((id)=>{const el=$(id);if(el)el.disabled=!state.online||state.busy});
  const travelMapGo=$('travelMapGo');if(travelMapGo)travelMapGo.disabled=!state.online||state.busy||!(state.travel.selectedMap&&state.travel.selectedMap.map);
  const travelStationGo=$('travelStationGo');if(travelStationGo)travelStationGo.disabled=!state.online||state.busy||!(state.travel.selectedStation&&state.travel.selectedStation.station);
  const poolSpawn=$('poolSpawn');if(poolSpawn)poolSpawn.disabled=!state.online||state.busy||!state.pools.selected;
  const invSend=$('invSendSelected');if(invSend)invSend.disabled=!state.online||state.busy||!state.inventory.selectedIds.size;
  const runMove=$('runSelectedMovement');if(runMove)runMove.disabled=!state.online||state.busy||!state.movementPicks.size;
  const riskCheck=$('devRiskCheck');
  if(riskCheck){
    riskCheck.disabled=state.dev.warningAccepted;
    if(state.dev.warningAccepted)riskCheck.checked=true;
  }
  const accept=$('devAcceptRisk');
  if(accept){
    accept.disabled=state.dev.warningAccepted;
    accept.textContent=state.dev.warningAccepted?'Dev Spawner Enabled':'Enable Dev Spawner This Session';
  }
  const riskStatus=$('devRiskStatus');
  if(riskStatus){
    if(!state.dev.warningAccepted)riskStatus.textContent='Check the box, then tap Enable. Spawn actions also need a live PC connection.';
    else if(!state.online)riskStatus.textContent='Enabled. Connect to desktop MSBT to fire spawn actions (buttons are tappable).';
    else riskStatus.textContent='Enabled and connected. Spawn actions are ready.';
  }
}
function playerValue(player){const index=player&&player.index;const name=player&&player.name?String(player.name):'';if(index===null||index===undefined||index==='')return name;return name?`${index}|${name}`:String(index)}
function playerLabel(player){const index=player&&player.index;const name=player&&player.name?String(player.name):'';if(index===null||index===undefined||index==='')return name||'Unknown player';return `${index} | ${name||'Unknown player'}`}
function resolveTargetValue(value,players){
  const raw=text(value);
  if(!raw)return '';
  const list=Array.isArray(players)?players:[];
  if(!list.length)return raw;
  const exact=list.find((player)=>playerValue(player)===raw);
  if(exact)return playerValue(exact);
  const name=raw.includes('|')?raw.split('|').slice(1).join('|'):raw;
  const byName=list.find((player)=>String(player.name||'')===name);
  if(byName)return playerValue(byName);
  const indexPart=raw.includes('|')?raw.split('|')[0]:raw;
  const byIndex=list.find((player)=>String(player.index)===String(indexPart));
  if(byIndex)return playerValue(byIndex);
  return '';
}
function targetDisplay(value){
  const resolved=resolveTargetValue(value,state.players)||text(value);
  if(!resolved)return 'None';
  const player=state.players.find((row)=>playerValue(row)===resolved);
  return player?playerLabel(player):resolved;
}
function currentTarget(){
  return text(state.selectedTarget)||text($('boostTarget')&&$('boostTarget').value)||text($('controlTarget')&&$('controlTarget').value)||'';
}
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
  $('targetSummary').textContent=targetDisplay(state.selectedTarget);
  setLiveEnabled();
}

$$('[data-nav]').forEach((button)=>button.addEventListener('click',()=>{ $$('[data-nav]').forEach(x=>x.classList.remove('active'));button.classList.add('active');$$('.screen').forEach(screen=>screen.classList.toggle('active',screen.dataset.screen===button.dataset.nav));window.scrollTo(0,0)}));
function openPanel(panelId,{scroll=true}={}){
  const panel=$(panelId);
  if(!panel)return false;
  if(panelId==='aboutPanel'){
    syncAboutVersion();
    requestUpdateCheck({quiet:false,reason:'about',forceBanner:true});
  }
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

function initBookmarks(){state.bookmarks=read(STORE.bookmarks,[]);state.selectedBookmarks=new Set();renderBookmarks()}
function filteredBookmarks(){
  const q=text($('bookmarkSearch')&&$('bookmarkSearch').value).toLowerCase();
  return state.bookmarks.filter(b=>!q||`${b.name} ${b.group} ${b.serial}`.toLowerCase().includes(q));
}
function renderBookmarks(){
  const rows=$('bookmarkRows');if(!rows)return;
  const list=filteredBookmarks();
  rows.innerHTML='';
  list.forEach(b=>{
    const button=document.createElement('button');
    const selected=state.selectedBookmarks.has(b.id);
    button.className=selected?'selected':'';
    button.textContent=`${selected?'✓ ':''}${b.name||'Unnamed'}${b.group?` · ${b.group}`:''}`;
    button.addEventListener('click',()=>{
      if(state.selectedBookmarks.has(b.id))state.selectedBookmarks.delete(b.id);else state.selectedBookmarks.add(b.id);
      $('bookmarkName').value=b.name||'';$('bookmarkGroup').value=b.group||'';$('bookmarkSerial').value=b.serial||'';$('bookmarkSerial').dataset.id=b.id;
      renderBookmarks();
    });
    rows.appendChild(button);
  });
  if(!rows.children.length)rows.innerHTML='<small class="muted">No saved serial bookmarks.</small>';
  if($('bookmarkSelectionSummary'))$('bookmarkSelectionSummary').textContent=`${state.selectedBookmarks.size} selected · ${list.length} shown`;
}
async function pullDesktopBookmarks({quiet=false}={}){
  if(!state.online){if(!quiet)alert('Connect to desktop MSBT first.');return false}
  try{
    const result=await gatewayFetch('/mobile/bookmarks',{timeoutMs:60000});
    if(!result.ok)throw new Error((result.data&&result.data.message)||`HTTP ${result.status}`);
    const rows=Array.isArray(result.data&&result.data.bookmarks)?result.data.bookmarks:[];
    state.bookmarks=rows.map((b)=>({id:b.id||`pc-${compact(b.serial||Date.now())}`,name:text(b.name)||'Unnamed',group:text(b.group)||'Default',serial:text(b.serial),created_at:b.created_at||now(),updated_at:b.updated_at||now(),metadata:b.metadata||{}})).filter((b)=>validSerial(b.serial));
    state.selectedBookmarks=new Set();
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
$('bookmarkSearch').addEventListener('input',renderBookmarks);$('saveBookmark').addEventListener('click',()=>{const serial=text($('bookmarkSerial').value);if(!validSerial(serial)){alert('Bookmark serial must be one valid @U serial.');return}const id=$('bookmarkSerial').dataset.id||`mobile-${Date.now()}`;const existing=state.bookmarks.find(b=>b.id===id);const record={...(existing||{}),id,name:text($('bookmarkName').value)||'Unnamed',group:text($('bookmarkGroup').value),serial,created_at:existing?.created_at||now(),updated_at:now(),metadata:existing?.metadata||{}};state.bookmarks=state.bookmarks.filter(b=>b.id!==id);state.bookmarks.push(record);write(STORE.bookmarks,state.bookmarks);$('bookmarkSerial').dataset.id=id;renderBookmarks();logActivity(`Saved serial bookmark: ${record.name}`)});$('deleteBookmark').addEventListener('click',()=>{const id=$('bookmarkSerial').dataset.id;if(!id)return;state.bookmarks=state.bookmarks.filter(b=>b.id!==id);state.selectedBookmarks.delete(id);write(STORE.bookmarks,state.bookmarks);$('bookmarkSerial').dataset.id='';$('bookmarkName').value='';$('bookmarkGroup').value='';$('bookmarkSerial').value='';renderBookmarks();logActivity('Deleted serial bookmark.')});
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
if($('bookmarkClearSelection'))$('bookmarkClearSelection').addEventListener('click',()=>{state.selectedBookmarks=new Set();renderBookmarks()});

let boostConfirmed='';$('boostValidate').addEventListener('click',()=>{const serials=text($('boostSerialText').value).split(/\s+/).filter(Boolean);const ok=serials.length>0&&serials.every(validSerial);$('boostSerialStatus').textContent=ok?`${serials.length} valid @U serial(s).`:'Serial text contains an invalid value.'});$('boostConfirm').addEventListener('click',()=>{const value=text($('boostSerialText').value);const serials=value.split(/\s+/).filter(Boolean);if(!serials.length||!serials.every(validSerial)){alert('Validate the @U serials first.');return}boostConfirmed=value;$('boostSerialStatus').textContent='Confirmed for delivery. Editing the serials will invalidate confirmation.'});$('boostSerialText').addEventListener('input',()=>{if(boostConfirmed&&text($('boostSerialText').value)!==boostConfirmed){boostConfirmed='';$('boostSerialStatus').textContent='Serial changed; confirmation cleared.'}});

const MOVEMENT_DEFAULT={speedScale:'1.00',walkSpeed:'600',jumpHeight:'198',gravityScale:'1.00',stepHeight:'45',floorAngle:'44.8',floorZ:'0.71',glideSpeed:'1200',glideBoost:'0',glideAirControl:'0.60',dashSpeed:'2500',timeDilation:'1.00',sprintJumpGoal:'198',doubleJumpGoal:'198',slideJumpGoal:'198',individualJumpGoals:false,zeroVaultOnApply:false};
function loadMovement(){const preset={...MOVEMENT_DEFAULT,...read(STORE.movement,{})};$$('[data-movement]').forEach(el=>{const key=el.dataset.movement;if(el.type==='checkbox')el.checked=!!preset[key];else el.value=preset[key]??''});refreshMovementPicks()}
function movementPickKey(button){return `${text(button.dataset.action)}|${text(button.dataset.slot)}`}
function refreshMovementPicks(){
  $$('[data-movement-pick]').forEach((button)=>{
    button.classList.toggle('picked',state.movementPicks.has(movementPickKey(button)));
  });
  setLiveEnabled();
}
$$('[data-movement-pick]').forEach((button)=>{
  button.addEventListener('contextmenu',(event)=>{
    event.preventDefault();
    const key=movementPickKey(button);
    if(state.movementPicks.has(key))state.movementPicks.delete(key);else state.movementPicks.add(key);
    refreshMovementPicks();
  });
  button.addEventListener('long-press',()=>{});
});
// Tap-hold alternative: double-tap toggles pick; normal click still fires via data-live.
$$('[data-movement-pick]').forEach((button)=>{
  let lastTap=0;
  button.addEventListener('click',(event)=>{
    const nowTs=Date.now();
    if(nowTs-lastTap<320){
      event.preventDefault();
      event.stopImmediatePropagation();
      const key=movementPickKey(button);
      if(state.movementPicks.has(key))state.movementPicks.delete(key);else state.movementPicks.add(key);
      refreshMovementPicks();
      if($('movementStatus'))$('movementStatus').textContent=`${state.movementPicks.size} movement action(s) selected. Tap Run Selected, or single-tap to fire one.`;
    }
    lastTap=nowTs;
  },true);
});
if($('saveMovement'))$('saveMovement').addEventListener('click',()=>{const preset={};$$('[data-movement]').forEach(el=>preset[el.dataset.movement]=el.type==='checkbox'?el.checked:text(el.value));write(STORE.movement,preset);$('movementStatus').textContent='Preset saved locally. It will remain available offline.';logActivity('Saved movement preset locally.')});
if($('runSelectedMovement'))$('runSelectedMovement').addEventListener('click',async()=>{
  if(!state.movementPicks.size){alert('Double-tap actions to select them, then Run Selected.');return}
  const buttons=$$('[data-movement-pick]').filter((button)=>state.movementPicks.has(movementPickKey(button)));
  for(const button of buttons)await runLiveAction(button);
});

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
    try{
      const fakeButton={dataset:{action:slot.commandId},_quickPayload:slot.payload&&typeof slot.payload==='object'?slot.payload:{}};
      await runLiveAction(fakeButton);
    }catch(error){
      const message=error&&error.message?error.message:String(error);
      logActivity(`Quick Menu failed: ${message}`);
      alert(message);
    }
    return;
  }
  if(!state.online&&slot.commandId){
    alert('Connect to desktop MSBT first, then tap the Quick Menu slot to fire it.');
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
  const preferred=resolveTargetValue(state.selectedTarget,state.players)||text(state.selectedTarget);
  const options=state.players.length
    ? `<option value="">Choose player</option>${state.players.map((player)=>{const value=playerValue(player);return `<option value="${esc(value)}">${esc(playerLabel(player))}</option>`}).join('')}`
    : '<option value="">No players loaded</option>';
  $$('.player-target').forEach((select)=>{
    select.innerHTML=options;
    select.disabled=!state.online||!state.players.length;
    if(preferred&&[...select.options].some((opt)=>opt.value===preferred))select.value=preferred;
    else select.value='';
  });
  if(state.players.length){
    const matched=resolveTargetValue(preferred,state.players);
    state.selectedTarget=matched||'';
  }
  if(state.selectedTarget)write(STORE.target,{target:state.selectedTarget});
  $('targetSummary').textContent=targetDisplay(state.selectedTarget);
}
let targetPushTimer=null;
async function pushSelectedTarget({quiet=true}={}){
  const target=currentTarget();
  if(!target||!state.online)return false;
  try{
    const setResult=await gatewayAction('set_target_player',{target_player:target},10000);
    if(!setResult.ok){
      const message=(setResult.data&&(setResult.data.message||setResult.data.error))||'Could not set target player.';
      if(!quiet)alert(message);
      return false;
    }
    return true;
  }catch(error){
    if(!quiet)alert(error&&error.message?error.message:String(error));
    return false;
  }
}
function onTargetSelectChange(select){
  state.selectedTarget=text(select&&select.value);
  write(STORE.target,{target:state.selectedTarget});
  fillPlayerSelects();
  updateConnectionChrome();
  if(targetPushTimer)window.clearTimeout(targetPushTimer);
  targetPushTimer=window.setTimeout(()=>{void pushSelectedTarget({quiet:true})},150);
}
$$('.player-target').forEach((select)=>{
  select.addEventListener('change',()=>onTargetSelectChange(select));
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
  const statusValue=data&&data.selected_player
    ? (data.selected_player_index!==null&&data.selected_player_index!==undefined&&data.selected_player_index!==''
      ? `${data.selected_player_index}|${data.selected_player}`
      : String(data.selected_player))
    : '';
  const fromStatus=resolveTargetValue(statusValue,state.players);
  const saved=read(STORE.target,{});
  // Prefer the phone's current/saved pick so status polls do not wipe Boost/Control selection.
  let next=resolveTargetValue(state.selectedTarget,state.players);
  if(!next)next=resolveTargetValue(saved.target,state.players);
  if(!next)next=fromStatus;
  if(state.players.length)state.selectedTarget=next||'';
  else if(text(saved.target))state.selectedTarget=text(saved.target);
  fillPlayerSelects();
  updateConnectionChrome();
}

async function connectGateway({quiet=false, hostCandidates=null}={}){
  state.connection={name:text($('pcName').value)||state.connection.name||'',address:text($('pcAddress').value)||state.connection.address||'',port:text($('pcPort').value)||state.connection.port||'49775',pairingCode:text($('pairingCode').value)||state.connection.pairingCode||'',updated_at:now()};
  write(STORE.connection,state.connection);
  if(!text(state.connection.address)||!text(state.connection.pairingCode)){
    state.online=false;state.bridgeOnline=false;updateConnectionChrome();
    const message='Save a PC address and pairing code first.';
    $('connectionStatus').textContent=message;
    if(!quiet)alert(message);
    return false;
  }
  const hosts=[];
  const pushHost=(value)=>{const host=text(value);if(host&&!hosts.includes(host))hosts.push(host)};
  if(Array.isArray(hostCandidates))hostCandidates.forEach(pushHost);
  pushHost(state.connection.address);
  if(Array.isArray(state.connection.hosts))state.connection.hosts.forEach(pushHost);
  let lastError='Could not reach desktop MSBT gateway.';
  for(let i=0;i<hosts.length;i+=1){
    const host=hosts[i];
    state.connection.address=host;
    if($('pcAddress'))$('pcAddress').value=host;
    write(STORE.connection,state.connection);
    try{
      const ping=await gatewayFetch('/mobile/ping',{requirePairing:false,timeoutMs:5000});
      if(!ping.ok&&ping.status)throw new Error((ping.data&&ping.data.message)||'Gateway ping failed.');
      const status=await gatewayFetch('/status',{timeoutMs:8000});
      if(status.status===401)throw new Error('Invalid pairing code. Scan the QR again or copy the current code from desktop MSBT → Activity → Mobile Gateway.');
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
      requestUpdateCheck({quiet:true,reason:'connect'});
      return true;
    }catch(error){
      lastError=error&&error.message?error.message:String(error);
      if(i<hosts.length-1){
        $('connectionStatus').textContent=`Trying next PC address (${hosts[i+1]})…`;
        continue;
      }
    }
  }
  state.online=false;state.bridgeOnline=false;state.players=[];fillPlayerSelects();updateConnectionChrome();stopStatusPolling();
  $('connectionStatus').textContent=lastError;
  if(!quiet){logActivity(`Connect failed: ${lastError}`);alert(lastError)}
  return false;
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
function saveConnectionFields(extra={}){
  state.connection={
    name:text($('pcName').value),
    address:text($('pcAddress').value),
    port:text($('pcPort').value)||'49775',
    pairingCode:text($('pairingCode').value),
    hosts:Array.isArray(extra.hosts)?extra.hosts:(Array.isArray(state.connection.hosts)?state.connection.hosts:[]),
    updated_at:now()
  };
  write(STORE.connection,state.connection);
  updateConnectionChrome();
}
$('saveConnection').addEventListener('click',()=>{
  saveConnectionFields();
  $('connectionStatus').textContent=state.connection.address?`Setup saved for ${state.connection.address}:${state.connection.port}. Tap Connect / Test.`:'Enter a PC address to complete setup.';
  logActivity('Saved PC connection setup.');
});
$('testConnection').addEventListener('click',()=>void connectGateway({hostCandidates:state.connection.hosts}));
$('disconnectConnection').addEventListener('click',disconnectGateway);

const qrScanState={stream:null,raf:0,active:false};
function setQrScanStatus(message){if($('qrScanStatus'))$('qrScanStatus').textContent=message}
function stopQrScanner({closeDialog=true}={}){
  qrScanState.active=false;
  if(qrScanState.raf){cancelAnimationFrame(qrScanState.raf);qrScanState.raf=0}
  const video=$('qrScanVideo');
  if(qrScanState.stream){
    qrScanState.stream.getTracks().forEach((track)=>track.stop());
    qrScanState.stream=null;
  }
  if(video)video.srcObject=null;
  const dialog=$('qrScanDialog');
  if(closeDialog&&dialog&&dialog.open)dialog.close();
}
function parsePairingPayload(raw){
  const value=text(raw);
  if(!value)throw new Error('Empty QR code.');
  let data=null;
  try{data=JSON.parse(value)}catch{
    // Accept pasted JSON wrapped in extra text.
    const start=value.indexOf('{');
    const end=value.lastIndexOf('}');
    if(start>=0&&end>start){
      try{data=JSON.parse(value.slice(start,end+1))}catch{data=null}
    }
  }
  if(!data||typeof data!=='object')throw new Error('QR is not an MSBT pairing code.');
  if(Number(data.v)!==1)throw new Error('Unsupported pairing QR version. Update MSBT Mobile.');
  const hosts=Array.isArray(data.hosts)
    ? data.hosts.map((host)=>text(host)).filter(Boolean)
    : [text(data.host||data.address)].filter(Boolean);
  const code=text(data.code||data.pairingCode);
  const port=text(data.port)||'49775';
  if(!hosts.length)throw new Error('Pairing QR is missing a PC address.');
  if(!code)throw new Error('Pairing QR is missing the pairing code.');
  return{
    v:1,
    name:text(data.name)||'MSBT PC',
    hosts,
    port,
    code
  };
}
async function applyPairingPayload(payload){
  if($('pcName'))$('pcName').value=payload.name||'';
  if($('pcAddress'))$('pcAddress').value=payload.hosts[0]||'';
  if($('pcPort'))$('pcPort').value=payload.port||'49775';
  if($('pairingCode'))$('pairingCode').value=payload.code||'';
  saveConnectionFields({hosts:payload.hosts});
  $('connectionStatus').textContent=`QR paired setup for ${payload.hosts[0]}:${payload.port}. Connecting…`;
  logActivity(`QR pairing loaded for ${payload.name||payload.hosts[0]}.`);
  return connectGateway({quiet:false,hostCandidates:payload.hosts});
}
function scanQrFrame(){
  if(!qrScanState.active)return;
  const video=$('qrScanVideo');
  const canvas=$('qrScanCanvas');
  if(!video||!canvas||typeof jsQR!=='function'){
    setQrScanStatus('QR scanner library missing in this build.');
    return;
  }
  if(video.readyState>=2){
    const width=video.videoWidth||640;
    const height=video.videoHeight||480;
    if(width&&height){
      canvas.width=width;
      canvas.height=height;
      const ctx=canvas.getContext('2d',{willReadFrequently:true});
      ctx.drawImage(video,0,0,width,height);
      const image=ctx.getImageData(0,0,width,height);
      const result=jsQR(image.data,image.width,image.height,{inversionAttempts:'dontInvert'});
      if(result&&result.data){
        try{
          const payload=parsePairingPayload(result.data);
          stopQrScanner();
          void applyPairingPayload(payload);
          return;
        }catch(error){
          setQrScanStatus(error&&error.message?error.message:'Could not read pairing QR.');
        }
      }
    }
  }
  qrScanState.raf=requestAnimationFrame(scanQrFrame);
}
function waitForCameraPermission(){
  return new Promise((resolve)=>{
    const native=window.MSBTAssets;
    if(native&&typeof native.hasCameraPermission==='function'&&native.hasCameraPermission()){
      resolve(true);
      return;
    }
    let settled=false;
    const finish=(granted)=>{
      if(settled)return;
      settled=true;
      window.__msbtCameraPermission=null;
      resolve(Boolean(granted));
    };
    window.__msbtCameraPermission=finish;
    if(native&&typeof native.requestCameraPermission==='function'){
      native.requestCameraPermission();
      window.setTimeout(()=>finish(native.hasCameraPermission&&native.hasCameraPermission()),12000);
      return;
    }
    // Browser/emulator fallback: getUserMedia will prompt itself.
    finish(true);
  });
}
async function startQrScanner(){
  openPanel('connectionPanel');
  const dialog=$('qrScanDialog');
  if(!dialog){alert('QR scanner UI missing.');return}
  if(typeof jsQR!=='function'){
    alert('QR scanner library failed to load. Use manual setup or reinstall the beta.');
    return;
  }
  setQrScanStatus('Requesting camera permission…');
  if(!dialog.open)dialog.showModal();
  const allowed=await waitForCameraPermission();
  if(!allowed){
    setQrScanStatus('Camera permission denied. Enable Camera for MSBT Mobile, or enter pairing details manually.');
    return;
  }
  try{
    stopQrScanner({closeDialog:false});
    qrScanState.active=true;
    if(!dialog.open)dialog.showModal();
    setQrScanStatus('Starting camera…');
    const stream=await navigator.mediaDevices.getUserMedia({
      audio:false,
      video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}}
    });
    qrScanState.stream=stream;
    const video=$('qrScanVideo');
    video.srcObject=stream;
    await video.play();
    setQrScanStatus('Point at the MSBT Mobile Gateway QR…');
    qrScanState.raf=requestAnimationFrame(scanQrFrame);
  }catch(error){
    stopQrScanner();
    const message=error&&error.message?error.message:String(error);
    alert(`Could not open camera: ${message}`);
    $('connectionStatus').textContent=`Camera unavailable: ${message}`;
  }
}
if($('scanPairingQr'))$('scanPairingQr').addEventListener('click',()=>void startQrScanner());
if($('qrScanCancel'))$('qrScanCancel').addEventListener('click',()=>{stopQrScanner();$('connectionStatus').textContent='QR scan cancelled.'});
if($('qrScanDialog'))$('qrScanDialog').addEventListener('close',()=>{if(qrScanState.active)stopQrScanner()});

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
    target_player:currentTarget(),
    infinite_jump_target:currentTarget()
  };
}
function buildActionPayload(action,button){
  // Quick Menu slots carry their own payload — prefer it over live form fields.
  if(button&&button._quickPayload&&typeof button._quickPayload==='object'&&Object.keys(button._quickPayload).length){
    return{...button._quickPayload};
  }
  if(action==='give_currency')return{currency_kind:text($('boostCurrencyKind').value)||'cash',amount:intValue($('boostCurrencyAmount').value,1000000)};
  if(action==='set_level')return{xp_track:text($('boostXpTrack').value)||'player',level:intValue($('boostXpLevel').value,60)};
  if(action==='set_backpack_bank_selected'||action==='set_backpack_bank_all')return{backpack_size:intValue($('boostBackpackSize').value,999),bank_size:intValue($('boostBankSize').value,1500)};
  if(action==='movement_apply_all')return movementPayload();
  if(action==='movement_set_time'){
    const preset={};$$('[data-movement]').forEach(el=>preset[el.dataset.movement]=el.type==='checkbox'?el.checked:text(el.value));
    return{movement_time_dilation:Number(preset.timeDilation||1)};
  }
  if(action==='movement_teleport_to_slot'){
    const slotAttr=button&&button.dataset?button.dataset.slot:undefined;
    return{slot:Math.max(0,Math.min(3,intValue(slotAttr,0))),target_player:currentTarget()};
  }
  if(action==='movement_infinite_jump_selected_on'||action==='movement_infinite_jump_selected_off'||action==='movement_infinite_jump_toggle_selected'){
    return{target_player:currentTarget(),infinite_jump_target:currentTarget()};
  }
  if(action==='travel_to_map'){
    const map=state.travel.selectedMap&&state.travel.selectedMap.map;
    if(!map)throw new Error('Select a travel map first.');
    return{travel_map:map,target_player:currentTarget()};
  }
  if(action==='travel_to_station'){
    const station=state.travel.selectedStation&&state.travel.selectedStation.station;
    if(!station)throw new Error('Select a travel station first.');
    return{travel_station:station,target_player:currentTarget()};
  }
  if(action==='spawn_itempool'){
    const name=state.pools.selected&&(state.pools.selected.itempool||state.pools.selected.name);
    if(!name)throw new Error('Select an item pool first.');
    return{itempool_name:name,level:intValue($('poolLevel').value,60),count:intValue($('poolCount').value,1),target_player:currentTarget()};
  }
  if(action&&action.startsWith('dev_spawner_'))return buildDevSpawnerPayload(action);
  if(action==='give_serial_selected'||action==='give_serial_all'||action==='give_serial_nonhost'){
    const fromCodes=button&&button.dataset&&button.dataset.serialSource==='codes';
    const fromBookmark=button&&button.dataset&&button.dataset.serialSource==='bookmark';
    const fromInventory=button&&button.dataset&&button.dataset.serialSource==='inventory';
    let serialText='';
    let copies=1;
    if(fromInventory){
      const serials=invAllRows().filter((row)=>state.inventory.selectedIds.has(invRowId(row))).map((row)=>text(row.serial)).filter(validSerial);
      if(!serials.length)throw new Error('Select one or more inventory serials first.');
      serialText=serials.join(' ');
    }else if(fromBookmark){
      const selected=state.bookmarks.filter((b)=>state.selectedBookmarks.has(b.id)&&validSerial(b.serial));
      if(selected.length)serialText=selected.map((b)=>b.serial).join(' ');
      else{
        serialText=text($('bookmarkSerial').value);
        if(!validSerial(serialText))throw new Error('Select bookmark(s) or enter one @U serial first.');
      }
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
      serial_level:intValue($('boostSerialLevel').value,60),
      target_player:currentTarget()
    };
  }
  return{};
}
function buttonHasDataAttr(button,name){
  if(!button)return false;
  if(typeof button.hasAttribute==='function')return button.hasAttribute(name);
  if(!button.dataset||typeof button.dataset!=='object')return false;
  const key=String(name||'').replace(/^data-/,'').replace(/-([a-z])/g,(_,c)=>c.toUpperCase());
  return button.dataset[key]!=null&&button.dataset[key]!==false&&button.dataset[key]!=='false';
}
async function runLiveAction(button){
  const action=text(button&&button.dataset&&button.dataset.action);
  if(!action){alert('This control is not wired for live actions yet.');return}
  if(!state.online){alert('Connect to desktop MSBT first (More → Connection Settings).');return}
  if(buttonHasDataAttr(button,'data-dev-risk')&&!state.dev.warningAccepted){
    alert('Enable Dev Spawner This Session first (Spawn tab).');
    return;
  }
  if(state.busy)return;
  state.busy=true;setLiveEnabled();
  try{
    if(PLAYER_SCOPED.has(action)){
      const target=currentTarget();
      if(!target)throw new Error('Select a target player first. Tap Connect while in-game to load the party list.');
      state.selectedTarget=target;
      write(STORE.target,{target});
      fillPlayerSelects();
      const setResult=await gatewayAction('set_target_player',{target_player:target},10000);
      if(!setResult.ok)throw new Error((setResult.data&&(setResult.data.message||setResult.data.error))||'Could not set target player.');
    }else if(currentTarget()&&(action==='travel_to_map'||action==='travel_to_station'||action==='spawn_itempool'||action==='give_serial_all'||action==='give_serial_nonhost')){
      await pushSelectedTarget({quiet:true});
    }
    const payload=buildActionPayload(action,button);
    const result=await gatewayAction(action,payload,45000);
    const message=(result.data&&(result.data.message||result.data.error))||(result.ok?`${action} sent.`:`${action} failed.`);
    logActivity(`${action}: ${message}`);
    if($('devSpawnerOutput')&&action.startsWith('dev_spawner_'))$('devSpawnerOutput').textContent=typeof result.data==='object'?JSON.stringify(result.data,null,2):message;
    if(!result.ok)alert(message);
    else if(action==='refresh_players'||PLAYER_SCOPED.has(action)){
      try{const status=await gatewayFetch('/status',{timeoutMs:8000});applyStatus(status.data||{})}catch{/* keep prior status */}
    }
  }catch(error){
    const message=error&&error.message?error.message:String(error);
    logActivity(`${action||'live action'} failed: ${message}`);
    if($('devSpawnerOutput')&&action&&action.startsWith('dev_spawner_'))$('devSpawnerOutput').textContent=message;
    alert(message);
  }finally{state.busy=false;setLiveEnabled()}
}

function renderActivity(){const rows=$('activityRows');if(!rows)return;if(!state.activity.length){rows.innerHTML='<small class="muted">No activity yet.</small>';return}rows.innerHTML=state.activity.slice(0,30).map(item=>`<div><small class="muted">${esc(new Date(item.at).toLocaleString())}</small><br>${esc(item.message)}</div>`).join('')}
$('copyFeedbackTemplate').addEventListener('click',async()=>{const template=`MSBT MOBILE BETA FEEDBACK\n\nPhone make/model:\nAndroid version:\nMSBT Mobile version: ${state.update.currentVersion||FALLBACK_APP_VERSION}\nDesktop MSBT version (if connected):\n\nScreen/feature:\nWhat I expected:\nWhat happened:\nSteps to reproduce:\nDoes it happen every time? Yes / No / Sometimes\n\nScreenshots attached: Yes / No\nAnything else:`;try{await navigator.clipboard.writeText(template);alert('Feedback template copied. Send it with screenshots directly to FunkYouSHiFT in Discord DMs.')}catch{prompt('Copy this feedback template:',template)}});

function appVersionFromNative(){
  try{
    if(window.MSBTAssets&&typeof MSBTAssets.getAppVersion==='function'){
      const value=text(MSBTAssets.getAppVersion());
      if(value)return value;
    }
  }catch{/* WebView bridge unavailable in browser preview */}
  return FALLBACK_APP_VERSION;
}
function syncAboutVersion(){
  state.update.currentVersion=appVersionFromNative();
  if($('aboutVersion'))$('aboutVersion').textContent=state.update.currentVersion;
}
function setAboutUpdateStatus(message){
  state.update.lastMessage=message||'';
  if($('aboutUpdateStatus'))$('aboutUpdateStatus').textContent=state.update.lastMessage||'Update check idle.';
}
function showUpdateBanner(show){
  const banner=$('updateBanner');
  if(!banner)return;
  banner.classList.toggle('hidden',!show);
  if(!show)return;
  if($('updateBannerText')){
    $('updateBannerText').textContent=`Open beta ${state.update.availableVersion} is available (you have ${state.update.currentVersion}).`;
  }
  if($('updateBannerMeta')){
    $('updateBannerMeta').textContent='Download installs over this app and keeps local pairing data.';
  }
}
function renderUpdateUi({forceBanner=false}={}){
  syncAboutVersion();
  const installAbout=$('aboutInstallUpdateBtn');
  if(installAbout)installAbout.classList.toggle('hidden',!state.update.updateAvailable);
  if(!state.update.updateAvailable){
    showUpdateBanner(false);
    return;
  }
  const dismissed=read(STORE.updateDismiss,{});
  const dismissedFor=text(dismissed.version);
  const hideBanner=!forceBanner&&dismissedFor&&dismissedFor===text(state.update.availableVersion);
  showUpdateBanner(!hideBanner);
  setAboutUpdateStatus(`Update available: ${state.update.availableVersion} (current ${state.update.currentVersion}).`);
}
function requestUpdateCheck({quiet=true,reason='manual',forceBanner=false}={}){
  if(!(window.MSBTAssets&&typeof MSBTAssets.checkForUpdate==='function')){
    if(!quiet)setAboutUpdateStatus('Update checks need the Android app build.');
    return;
  }
  if(state.update.checking){
    if(!quiet)setAboutUpdateStatus('Checking for updates…');
    return;
  }
  state.update.checking=true;
  state.update._forceBanner=Boolean(forceBanner)||reason==='manual'||reason==='about';
  if(!quiet||reason==='about')setAboutUpdateStatus('Checking for updates…');
  try{MSBTAssets.checkForUpdate()}catch(error){
    state.update.checking=false;
    if(!quiet)setAboutUpdateStatus(error&&error.message?error.message:String(error));
  }
}
function startUpdateInstall(){
  const url=text(state.update.apkUrl);
  if(!(window.MSBTAssets&&typeof MSBTAssets.downloadAndInstallUpdate==='function')){
    if(url&&window.MSBTAssets&&typeof MSBTAssets.openExternalUrl==='function'){
      MSBTAssets.openExternalUrl(url);
      return;
    }
    alert('In-app install is only available in the Android APK build.');
    return;
  }
  setAboutUpdateStatus('Starting download…');
  try{MSBTAssets.downloadAndInstallUpdate(url)}catch(error){
    setAboutUpdateStatus(error&&error.message?error.message:String(error));
  }
}
window.__msbtUpdateCheck=(payload)=>{
  state.update.checking=false;
  const data=payload&&typeof payload==='object'?payload:{};
  if(!data.ok){
    if(data.offline){
      setAboutUpdateStatus('Update check skipped (offline or unreachable).');
      return;
    }
    setAboutUpdateStatus(text(data.message)||'Update check failed.');
    return;
  }
  if(data.currentVersion)state.update.currentVersion=text(data.currentVersion);
  state.update.availableVersion=text(data.availableVersion);
  state.update.apkUrl=text(data.apkVersionedUrl)||text(data.apkUrl);
  state.update.updateAvailable=Boolean(data.updateAvailable);
  syncAboutVersion();
  if(state.update.updateAvailable){
    renderUpdateUi({forceBanner:Boolean(state.update._forceBanner)});
    if(state.update._forceBanner)logActivity(`Update available: ${state.update.availableVersion}`);
  }else{
    showUpdateBanner(false);
    if($('aboutInstallUpdateBtn'))$('aboutInstallUpdateBtn').classList.add('hidden');
    setAboutUpdateStatus(`You are on the latest open beta (${state.update.currentVersion}).`);
  }
  state.update._forceBanner=false;
};
window.__msbtUpdateProgress=(payload)=>{
  const data=payload&&typeof payload==='object'?payload:{};
  const phase=text(data.phase);
  const message=text(data.message)||phase||'Update progress';
  setAboutUpdateStatus(message);
  if(phase==='error'||phase==='need_permission'){
    logActivity(`Update: ${message}`);
    if(phase==='error')alert(message);
  }
};
if($('updateLaterBtn'))$('updateLaterBtn').addEventListener('click',()=>{
  if(state.update.availableVersion)write(STORE.updateDismiss,{version:state.update.availableVersion,at:now()});
  showUpdateBanner(false);
});
if($('updateInstallBtn'))$('updateInstallBtn').addEventListener('click',startUpdateInstall);
if($('checkUpdatesBtn'))$('checkUpdatesBtn').addEventListener('click',()=>requestUpdateCheck({quiet:false,reason:'manual',forceBanner:true}));
if($('aboutInstallUpdateBtn'))$('aboutInstallUpdateBtn').addEventListener('click',startUpdateInstall);

function invEntryLabel(entry){
  return text(entry&&(entry.summary||entry.label||entry.name||entry.slot_name))||'Item';
}
function invRowId(entry){
  return text(entry&&entry.serial)||`${entry&&entry._bucket}:${invEntryLabel(entry)}`;
}
function invAllRows(){
  return [...(state.inventory.equipped||[]).map((e)=>({...e,_bucket:'equipped'})),...(state.inventory.backpack||[]).map((e)=>({...e,_bucket:'backpack'}))];
}
function filteredInventoryRows(){
  const q=text($('invSearch')&&$('invSearch').value).toLowerCase();
  return invAllRows().filter((e)=>!q||`${invEntryLabel(e)} ${e.serial||''} ${e._bucket}`.toLowerCase().includes(q));
}
function renderInventory(){
  const rows=$('invRows');if(!rows)return;
  const list=filteredInventoryRows();
  rows.innerHTML='';
  list.slice(0,400).forEach((entry)=>{
    const button=document.createElement('button');
    const serial=text(entry.serial);
    const id=invRowId(entry);
    const selected=state.inventory.selectedIds.has(id);
    button.className=selected?'selected':'';
    button.textContent=`${selected?'✓ ':''}[${entry._bucket==='equipped'?'EQ':'BP'}] ${invEntryLabel(entry)}`;
    button.title=serial;
    button.addEventListener('click',()=>{
      if(state.inventory.selectedIds.has(id))state.inventory.selectedIds.delete(id);
      else state.inventory.selectedIds.add(id);
      state.inventory.selected=entry;
      const use=$('invUseBoost');const bm=$('invSaveBookmark');
      if(use)use.disabled=!validSerial(serial);
      if(bm)bm.disabled=!validSerial(serial);
      renderInventory();
      setLiveEnabled();
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
  if($('invSelectionSummary'))$('invSelectionSummary').textContent=`${state.inventory.selectedIds.size} selected · ${list.length} shown`;
}
async function ensureInventoryTarget(){
  const target=currentTarget();
  if(!target)throw new Error('Select a target player first (Boost / Control target). Connect while in-game to load the party list.');
  state.selectedTarget=target;
  write(STORE.target,{target});
  fillPlayerSelects();
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
  state.inventory={equipped,backpack,selected:null,selectedIds:new Set()};
  const use=$('invUseBoost');const bm=$('invSaveBookmark');
  if(use)use.disabled=true;if(bm)bm.disabled=true;
  renderInventory();
  setLiveEnabled();
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
if($('invClearSelection'))$('invClearSelection').addEventListener('click',()=>{state.inventory.selectedIds=new Set();renderInventory();setLiveEnabled()});

function travelMapKey(map){return text(map&&(map.map||map.map_key))}
function travelWorldKey(map){return text(map&&(map.map||map.world||'')).toLowerCase()}
function renderTravelMaps(){
  const rows=$('travelMapRows');if(!rows)return;
  const q=text($('travelMapSearch')&&$('travelMapSearch').value).toLowerCase();
  const list=state.travel.maps.filter((row)=>{
    const hay=`${row.display_name||''} ${row.map||''} ${row.category||''}`.toLowerCase();
    return !q||hay.includes(q);
  }).slice(0,250);
  rows.innerHTML='';
  list.forEach((row)=>{
    const button=document.createElement('button');
    const selected=state.travel.selectedMap&&travelMapKey(state.travel.selectedMap)===travelMapKey(row);
    button.className=selected?'selected':'';
    button.textContent=`${row.display_name||row.map}${row.category?` · ${row.category}`:''}`;
    button.addEventListener('click',()=>{
      state.travel.selectedMap=row;
      state.travel.selectedStation=null;
      renderTravelMaps();
      renderTravelStations();
      setLiveEnabled();
      if($('travelStatus'))$('travelStatus').textContent=`Map: ${button.textContent}`;
    });
    rows.appendChild(button);
  });
  if(!rows.children.length)rows.innerHTML='<small class="muted">No maps match.</small>';
  if($('travelMapSummary'))$('travelMapSummary').textContent=`${list.length} maps shown · ${state.travel.maps.length} total`;
}
function renderTravelStations(){
  const rows=$('travelStationRows');if(!rows)return;
  const q=text($('travelStationSearch')&&$('travelStationSearch').value).toLowerCase();
  const showAll=Boolean($('travelShowAllStations')&&$('travelShowAllStations').checked);
  state.travel.showAllStations=showAll;
  const world=state.travel.selectedMap?travelWorldKey(state.travel.selectedMap):'';
  let list=state.travel.stations;
  if(!showAll){
    if(!world){
      rows.innerHTML='<small class="muted">Select a map to filter stations, or enable Show all travel stations.</small>';
      if($('travelStationSummary'))$('travelStationSummary').textContent='Select a map to filter stations.';
      return;
    }
    list=list.filter((row)=>text(row.world||'').toLowerCase()===world||text(row.station||'').toLowerCase().startsWith(world));
  }
  list=list.filter((row)=>{
    const hay=`${row.display_name||''} ${row.station||''} ${row.world||''} ${row.category||''} ${row.station_name||''}`.toLowerCase();
    return !q||hay.includes(q);
  }).slice(0,300);
  rows.innerHTML='';
  list.forEach((row)=>{
    const button=document.createElement('button');
    const selected=state.travel.selectedStation&&state.travel.selectedStation.station===row.station;
    button.className=selected?'selected':'';
    button.textContent=`${row.display_name||row.station_name||row.station}${row.world?` · ${row.world}`:''}`;
    button.addEventListener('click',()=>{
      state.travel.selectedStation=row;
      renderTravelStations();
      setLiveEnabled();
      if($('travelStatus'))$('travelStatus').textContent=`Station: ${button.textContent}`;
    });
    rows.appendChild(button);
  });
  if(!rows.children.length)rows.innerHTML='<small class="muted">No stations match.</small>';
  if($('travelStationSummary'))$('travelStationSummary').textContent=`${list.length} stations shown${showAll?' (all maps)':world?` for ${state.travel.selectedMap.display_name||state.travel.selectedMap.map}`:''}`;
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
    renderTravelMaps();
    renderTravelStations();
  }catch(error){
    if($('travelStatus'))$('travelStatus').textContent=`Travel catalog unavailable: ${error&&error.message?error.message:error}`;
    if($('travelMapRows'))$('travelMapRows').innerHTML='<small class="muted">Travel catalog failed to load.</small>';
  }
}
if($('travelMapSearch'))$('travelMapSearch').addEventListener('input',renderTravelMaps);
if($('travelStationSearch'))$('travelStationSearch').addEventListener('input',renderTravelStations);
if($('travelShowAllStations'))$('travelShowAllStations').addEventListener('change',()=>{renderTravelStations();setLiveEnabled()});

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

function floatValue(value,fallback=0){const n=Number.parseFloat(String(value??'').trim());return Number.isFinite(n)?n:fallback}
function buildDevSpawnerPayload(action){
  const distance=floatValue($('devActorDistance')&&$('devActorDistance').value,350);
  const spacing=floatValue($('devActorSpacing')&&$('devActorSpacing').value,125);
  const scale=floatValue($('devActorScale')&&$('devActorScale').value,1);
  const zOffset=floatValue($('devActorZOffset')&&$('devActorZOffset').value,0);
  const count=intValue($('devActorCount')&&$('devActorCount').value,1);
  const actor=text($('devAiName')&&$('devAiName').value)||state.dev.selected;
  if(DEV_NEED_ACTOR.has(action)&&!actor)throw new Error('Select an actor from the browser first.');
  if(action==='dev_spawner_barrel_logo'){
    const lines=[text($('devLogoLine1')&&$('devLogoLine1').value),text($('devLogoLine2')&&$('devLogoLine2').value),text($('devLogoLine3')&&$('devLogoLine3').value)].filter(Boolean);
    if(!lines.length)throw new Error('Enter Barrel Logo text lines first.');
  }
  return{
    dev_actor_name:actor,
    dev_actor_class:text($('devActorClass')&&$('devActorClass').value),
    dev_actor_count:count,
    dev_actor_delay:floatValue($('devActorDelay')&&$('devActorDelay').value,1),
    dev_actor_disable_states:text($('devActorDisableStates')&&$('devActorDisableStates').value),
    dev_actor_distance:distance,
    dev_actor_enable_states:text($('devActorEnableStates')&&$('devActorEnableStates').value),
    dev_actor_include_non_generated:Boolean($('devActorIncludeNonGenerated')&&$('devActorIncludeNonGenerated').checked),
    dev_actor_no_activate:Boolean($('devActorNoActivate')&&$('devActorNoActivate').checked),
    dev_actor_scale:scale,
    dev_actor_spacing:spacing,
    dev_actor_target_limit:intValue($('devActorTargetLimit')&&$('devActorTargetLimit').value,20),
    dev_actor_z_offset:zOffset,
    dev_ai_name:actor,
    dev_ai_class:'',
    dev_ai_count:count,
    dev_ai_cache_index:0,
    dev_ai_cache_limit:10,
    dev_ai_advanced_spawn:true,
    dev_ai_direct_only:false,
    dev_ai_distance:distance,
    dev_ai_load:'',
    dev_ai_scale:scale,
    dev_ai_spacing:spacing,
    dev_ai_z_offset:zOffset,
    dev_logo_actor:text($('devLogoActor')&&$('devLogoActor').value)||'barrel',
    dev_logo_distance:floatValue($('devLogoDistance')&&$('devLogoDistance').value,2500),
    dev_logo_height:floatValue($('devLogoHeight')&&$('devLogoHeight').value,750),
    dev_logo_include_non_generated:Boolean($('devLogoIncludeNonGenerated')&&$('devLogoIncludeNonGenerated').checked),
    dev_logo_scale:floatValue($('devLogoScale')&&$('devLogoScale').value,0.45),
    dev_logo_spacing:floatValue($('devLogoSpacing')&&$('devLogoSpacing').value,70),
    dev_logo_text:[text($('devLogoLine1')&&$('devLogoLine1').value),text($('devLogoLine2')&&$('devLogoLine2').value),text($('devLogoLine3')&&$('devLogoLine3').value)].filter(Boolean).join('|')
  };
}
function renderDevActors(){
  const rows=$('devActorRows');if(!rows)return;
  const start=state.dev.page*state.dev.pageSize;
  const page=state.dev.filtered.slice(start,start+state.dev.pageSize);
  rows.innerHTML='';
  page.forEach((name)=>{
    const button=document.createElement('button');
    button.className=state.dev.selected===name?'selected':'';
    button.textContent=name;
    button.addEventListener('click',()=>{
      state.dev.selected=name;
      if($('devAiName'))$('devAiName').value=name;
      renderDevActors();
    });
    rows.appendChild(button);
  });
  if(!rows.children.length)rows.innerHTML='<small class="muted">No actors match.</small>';
  const total=state.dev.filtered.length;
  if($('devActorSummary'))$('devActorSummary').textContent=`${total.toLocaleString()} actors · page ${state.dev.page+1}/${Math.max(1,Math.ceil(total/state.dev.pageSize)||1)}`;
}
function filterDevActors(){
  const q=text($('devActorSearch')&&$('devActorSearch').value).toLowerCase();
  const cat=text($('devActorCategory')&&$('devActorCategory').value)||'All';
  state.dev.category=cat;
  const source=Array.isArray(state.dev.categories[cat])?state.dev.categories[cat]:(state.dev.categories.All||[]);
  state.dev.filtered=source.filter((name)=>!q||String(name).toLowerCase().includes(q));
  state.dev.page=0;
  renderDevActors();
}
async function loadDevCatalog(){
  try{
    const raw=await readBundledAssetText('dev_spawner_catalog.json');
    const json=JSON.parse(raw);
    state.dev.categories=json.categories&&typeof json.categories==='object'?json.categories:{All:[]};
    const select=$('devActorCategory');
    if(select){
      const current=select.value||'All';
      select.innerHTML='';
      Object.keys(state.dev.categories).sort((a,b)=>a.localeCompare(b)).forEach((key)=>{
        const opt=document.createElement('option');
        opt.value=key;opt.textContent=`${key} (${(state.dev.categories[key]||[]).length})`;
        select.appendChild(opt);
      });
      if([...select.options].some((o)=>o.value===current))select.value=current;
      else select.value='All';
    }
    filterDevActors();
  }catch(error){
    if($('devActorSummary'))$('devActorSummary').textContent=`Actor catalog unavailable: ${error&&error.message?error.message:error}`;
  }
}
if($('devAcceptRisk'))$('devAcceptRisk').addEventListener('click',()=>{
  if(state.dev.warningAccepted)return;
  const checked=Boolean($('devRiskCheck')&&$('devRiskCheck').checked);
  if(!checked){
    alert('Check “I understand the risk” first, then tap Enable.');
    return;
  }
  state.dev.warningAccepted=true;
  setLiveEnabled();
  const msg=state.online
    ? 'Dev Spawner enabled. Spawn / Barrel Logo actions are unlocked.'
    : 'Dev Spawner enabled. Connect to desktop MSBT before firing spawn actions.';
  if($('devSpawnerOutput'))$('devSpawnerOutput').textContent=msg;
  logActivity(msg);
});
if($('devActorSearch'))$('devActorSearch').addEventListener('input',filterDevActors);
if($('devActorCategory'))$('devActorCategory').addEventListener('change',filterDevActors);
if($('devPrevPage'))$('devPrevPage').addEventListener('click',()=>{if(state.dev.page>0){state.dev.page-=1;renderDevActors()}});
if($('devNextPage'))$('devNextPage').addEventListener('click',()=>{const max=Math.max(0,Math.ceil(state.dev.filtered.length/state.dev.pageSize)-1);if(state.dev.page<max){state.dev.page+=1;renderDevActors()}});
if($('devLogoUseSelected'))$('devLogoUseSelected').addEventListener('click',()=>{
  const actor=text($('devAiName')&&$('devAiName').value)||state.dev.selected;
  if(!actor){alert('Select an actor first.');return}
  if($('devLogoActor'))$('devLogoActor').value=actor;
});

$$('[data-collapse-panel]').forEach((button)=>{
  button.addEventListener('click',()=>{
    const panel=$(button.dataset.collapsePanel);
    if(panel)panel.classList.add('hidden');
  });
});
$$('[data-select-all]').forEach((button)=>{
  button.addEventListener('click',()=>{
    const kind=button.dataset.selectAll;
    if(kind==='bookmarks'){
      filteredBookmarks().forEach((b)=>state.selectedBookmarks.add(b.id));
      renderBookmarks();
    }else if(kind==='inventory'){
      filteredInventoryRows().forEach((row)=>state.inventory.selectedIds.add(invRowId(row)));
      renderInventory();
      setLiveEnabled();
    }else if(kind==='movement'){
      $$('[data-movement-pick]').forEach((el)=>state.movementPicks.add(movementPickKey(el)));
      refreshMovementPicks();
      if($('movementStatus'))$('movementStatus').textContent=`${state.movementPicks.size} movement action(s) selected. Tap Run Selected Actions.`;
    }
  });
});

$$('[data-live]').forEach(button=>button.addEventListener('click',()=>void runLiveAction(button)));

state.activity=read(STORE.activity,[]);setLiveEnabled();initBookmarks();loadMovement();loadQuick();loadConnection();renderActivity();loadCatalogs();loadTravelCatalog();loadPoolCatalog();loadDevCatalog();
syncAboutVersion();
requestUpdateCheck({quiet:true,reason:'launch'});
if(text(state.connection.address)&&text(state.connection.pairingCode))void connectGateway({quiet:true});
