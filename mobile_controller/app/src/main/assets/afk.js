/* Uses the existing authenticated connection; no separate command service. */
(() => {
  const panel = document.getElementById('mobileAfkPanel');
  if (!panel) return;
  const boosts = {level:'Max level',spec:'Max specialization rank',sdu:'SDUs · 3225',cash:'Max cash',eridium:'Max Eridium',keys:'Max keys',challenges:'Complete challenges',uvhm:'UVHM 1–7',cosmetics:'Cosmetics + vehicle unlocks',loot:'Send loot'};
  panel.innerHTML = `<p id="afkMobileStatus">Connect to your PC to manage AFK.</p>
    <p class="muted">Runs on the PC after you disconnect. Keep Borderlands 4 open. Auto-accept requires SHiFT open.</p>
    <button id="afkPull">Load PC settings</button>
    <details id="afkOptions"><summary>Boosts and loot settings</summary><fieldset id="afkFields"><legend>Every joining guest receives</legend>
    ${Object.entries(boosts).map(([key,label])=>`<label><input type="checkbox" data-afk="${key}"> ${label}</label>`).join('')}
    <label><input type="checkbox" data-afk="auto_accept" checked> Auto-accept SHiFT friends</label>
    <label><input type="checkbox" data-afk="auto_kick"> Kick after delivery finishes</label>
    <label><input type="checkbox" data-afk="cleanup_rewards"> Clean reward loot and return original items</label>
    <p class="muted">For challenges / UVHM. Clears reward loot, sends selected serials, then returns originals. Equipment and favorite flags are not restored. Password once per session. Stacked-item backpacks are left untouched.</p>
    <label>Loot delivery<select id="afkMode"><option value="random70">Guaranteed items + random fill</option><option value="all">All items · password above 70</option></select></label>
    <label>Random delivery size<input id="afkCount" type="number" min="1" step="1" value="70"></label><p class="muted">Guaranteed items count toward this total. If they exceed it, all compatible guaranteed items still arrive. More than 70 requires the password.</p><label>Guaranteed items<textarea id="afkFixed" rows="4" placeholder="One item code per line"></textarea></label>
    <label>Random / full pool<textarea id="afkPool" rows="5" placeholder="One item code per line"></textarea></label>
    <p class="muted">Two guaranteed items leave 68 random slots. Both pools follow character class rules.</p>
    <div class="button-grid"><button data-afk-add="catalog:pool">Catalog selection → pool</button><button data-afk-add="catalog:fixed">Catalog selection → guaranteed</button><button data-afk-add="bookmarks:pool">Bookmarks → pool</button><button data-afk-add="bookmarks:fixed">Bookmarks → guaranteed</button></div></fieldset></details>
    <div class="button-grid"><button id="afkMobileStart" class="primary">Start AFK Lobby</button><button id="afkMobileStop" class="danger">Stop AFK Lobby</button><button id="afkShiftOpen">Open SHiFT</button><button id="afkShiftClose">Close SHiFT</button></div>
    <p id="afkMobileShift"></p><p id="afkMobileQueue"></p><p id="afkMobileCounts"></p><pre id="afkMobileLog" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre>
    <dialog id="afkPasswordDialog"><form method="dialog"><h3>Authorize AFK backpack / loot actions</h3><label>Password<input id="afkPassword" type="password" autocomplete="off"></label><p>Required once when starting this AFK session. Never saved on this phone.</p><button value="cancel">Cancel</button><button value="unlock">Unlock</button></form></dialog>`;
  const el = id => document.getElementById(id);
  panel.insertBefore(el('afkMobileStart').parentElement,el('afkOptions'));
  const key = 'msbt.mobile.afk.v1';
  let status = null, busy = false, initialized = false;
  const message = value => { el('afkMobileStatus').textContent = value; };
  function selection() {
    return {...Object.fromEntries([...panel.querySelectorAll('[data-afk]')].map(n=>[n.dataset.afk,n.checked])),
      loot_mode:el('afkMode').value,random_count:Number(el('afkCount').value),codes:el('afkPool').value,guaranteed_codes:el('afkFixed').value};
  }
  function apply(config) {
    panel.querySelectorAll('[data-afk]').forEach(n=>{n.checked=config[n.dataset.afk]===true;});
    el('afkCount').value=config.random_count||70;
    el('afkMode').value=config.loot_mode==='all'?'all':'random70';
    el('afkPool').value=config.codes??(config.serials||[]).join('\n');
    el('afkFixed').value=config.guaranteed_codes??(config.guaranteed_serials||[]).join('\n');
  }
  try {const saved=JSON.parse(localStorage.getItem(key)||'null');if(saved)apply(saved);} catch {}
  const save=()=>localStorage.setItem(key,JSON.stringify(selection()));
  panel.addEventListener('input',save);panel.addEventListener('change',save);
  function lock() {
    const connected=state.online&&state.bridgeOnline;
    el('afkFields').disabled=busy||Boolean(status?.enabled);
    el('afkMobileStart').disabled=busy||!connected||!status||status.enabled;
    el('afkMobileStop').disabled=busy||!connected||!status?.enabled;
    ['afkShiftOpen','afkShiftClose'].forEach(id=>{el(id).disabled=busy||!connected;});
    el('afkPull').disabled=busy||!connected||!status;
  }
  function render(data) {
    status=data?.afk_lobby||null;
    if(status?.enabled&&!initialized){apply(status.config||{});save();}
    initialized=Boolean(status);lock();
    message(status?.message||'AFK unavailable. Connect to the PC with the updated SDK mod loaded.');
    el('afkMobileShift').textContent=status?.shift_connected?`SHiFT connected · accepter ${status.shift_running?'running':'stopped'}`:'SHiFT not connected';
    el('afkMobileQueue').textContent=status?.queued?.length?`Waiting: ${status.queued.join(', ')}`:'No guests waiting';
    el('afkMobileCounts').textContent=status?.session_joins!=null?(window.msbtI18n?window.msbtI18n.t('counts',{session:status.session_joins,lifetime:status.lifetime_joins??window.msbtI18n.t('unavailable')}):`Guest joins: ${status.session_joins} this session · ${status.lifetime_joins??'unavailable'} lifetime`)+(status.counter_error?' · Lifetime count could not be saved: '+status.counter_error:''):'Join counters require the updated SDK mod.';
    el('afkMobileLog').textContent=(status?.history||[]).map(e=>`${e.name}: ${e.message}\n${(e.results||[]).map(r=>`${r.step}: ${r.ok?'OK':'FAILED'} · ${r.message}`).join('\n')}`).join('\n\n');
  }
  function password() {
    return new Promise(resolve=>{const dialog=el('afkPasswordDialog');el('afkPassword').value='';dialog.returnValue='cancel';dialog.onclose=()=>{const value=dialog.returnValue==='unlock'?el('afkPassword').value:null;el('afkPassword').value='';resolve(value);};dialog.showModal();});
  }
  async function run(action,payload={}) {
    if(busy||!state.online||!state.bridgeOnline)return;
    busy=true;lock();
    try {
      if(action==='afk_lobby_start'&&payload.cleanup_rewards&&!status?.cleanup_rewards_supported)throw Error('Update the PC SDK before using reward cleanup.');
      if(action==='afk_lobby_start'&&payload.loot&&(!status?.guaranteed_loot_supported||!status?.bulk_loot_password_required))throw Error('Update the PC SDK mod before starting loot delivery from this phone.');
      if(action==='afk_lobby_start'&&payload.loot&&payload.loot_mode==='random70'&&payload.random_count!==70&&!status?.random_count_supported)throw Error('Update the PC SDK mod before changing random delivery size.');
      save();let result=await gatewayAction(action,payload);
      if(result.data?.password_required&&['bulk_loot','backpack_cleanup'].includes(result.data.password_kind)) {
        const value=await password();if(value===null)throw Error('Start cancelled.');
        result=await gatewayAction(action,{...payload,bulk_loot_password:value,backpack_password:value});
      }
      if(!result.ok)throw Error(result.data?.message||'Command failed.');
      // A timeout/queued response is not a confirmed start or stop. Read PC state.
      const snapshot=await gatewayFetch('/status');
      if(!snapshot.ok)throw Error('Command sent; PC status could not be confirmed. Reconnect before retrying.');
      applyStatus(snapshot.data);
      if(result.data?.queued)message('Command queued on PC. Waiting for the game to process it.');
    } catch(error){message(error.message);} finally {busy=false;lock();}
  }
  el('afkPull').onclick=()=>{if(status){apply(status.config||{});save();message('Loaded the current PC lobby settings.');}};
  el('afkMobileStart').onclick=()=>run('afk_lobby_start',selection());
  el('afkMobileStop').onclick=()=>run('afk_lobby_stop');
  el('afkShiftOpen').onclick=()=>run('shift_overlay_control',{mode:'open'});
  el('afkShiftClose').onclick=()=>run('shift_overlay_control',{mode:'close'});
  panel.querySelectorAll('[data-afk-add]').forEach(button=>{button.onclick=()=>{
    if(busy||status?.enabled)return;
    const [source,destination]=button.dataset.afkAdd.split(':');
    const rows=source==='catalog'?state.codes.filter(r=>state.selectedCodes.has(r.id)):state.bookmarks.filter(r=>state.selectedBookmarks.has(r.id));
    if(!rows.length){message(`Select items in ${source==='catalog'?'BL4 Codes':'Bookmarks'} first.`);return;}
    const target=el(destination==='fixed'?'afkFixed':'afkPool');
    target.value=[target.value.trim(),...rows.map(r=>r.serial).filter(Boolean)].filter(Boolean).join('\n');
    panel.querySelector('[data-afk="loot"]').checked=true;save();message(`Added ${rows.length} selected items.`);
  };});
  window.mobileAfk={render,connectionChanged:()=>{lock();if(!state.online)message('Disconnected. The PC lobby continues running; reconnect to control it.');}};
  lock();
})();
