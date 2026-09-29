(()=>{
 if(!window.msbt?.remoteAfkInfo)return;
 const el=id=>document.getElementById(id);let busy=false;
 async function refresh(){if(busy)return;const info=await window.msbt.remoteAfkInfo();el('remoteAfkStatus').textContent=info.connected?'Remote AFK connected. Scan the private QR with your phone.':info.enabled?(info.lastError||'Connecting to remote service; retries are automatic…'):info.lastError||'Remote access is off.';el('remoteAfkQr').hidden=!info.enabled;if(info.enabled&&!el('remoteAfkQr').getAttribute('src'))el('remoteAfkQr').src=await window.msbt.remoteAfkQr();}
 async function run(enable){if(busy)return;busy=true;el('remoteAfkEnable').disabled=true;el('remoteAfkDisable').disabled=true;
  try{const info=await (enable?window.msbt.remoteAfkStart():window.msbt.remoteAfkStop());if(info.lastError)el('remoteAfkStatus').textContent=info.lastError;if(info.enabled)el('remoteAfkQr').src=await window.msbt.remoteAfkQr();else el('remoteAfkQr').removeAttribute('src');}
  catch(e){el('remoteAfkStatus').textContent=e.message;}finally{busy=false;el('remoteAfkEnable').disabled=false;el('remoteAfkDisable').disabled=false;await refresh();}}
 el('remoteAfkEnable').onclick=()=>run(true);el('remoteAfkDisable').onclick=()=>run(false);
 void refresh();setInterval(()=>void refresh(),5000);
})();
