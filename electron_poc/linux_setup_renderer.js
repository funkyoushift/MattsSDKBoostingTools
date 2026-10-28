'use strict';
const el=id=>document.getElementById(id);
let busy=false;
function status(message,kind=''){el('status').textContent=message || '';el('status').className=kind;}
function setBusy(value){busy=value;for(const id of ['setupGame','gameRoot','browse','install','finishGame','launch'])el(id).disabled=value;}
function addGame(root,label){if(!root)return;let option=Array.from(el('gameRoot').options).find(option=>option.value===root);if(!option){option=document.createElement('option');option.value=root;option.textContent=label || root;el('gameRoot').append(option);}el('gameRoot').value=root;}
window.linuxSetup.onProgress(value=>{el('progress').hidden=false;if(Number.isFinite(value?.percent))el('progress').value=Math.max(0,Math.min(100,value.percent));else el('progress').removeAttribute('value');status(value?.message || 'Installing MSBT…');});
el('setupGame').addEventListener('change',()=>{el('gameOptions').hidden=!el('setupGame').checked;});
el('browse').addEventListener('click',async()=>{const result=await window.linuxSetup.chooseGame();if(result?.ok && !result.canceled)addGame(result.root);else if(!result?.ok)status(result.message,'error');});
async function install(retry=false){
  if(busy)return;
  if(el('setupGame').checked && !el('gameRoot').value){status('Choose the Borderlands 4 folder, or turn off game integration to install the desktop app on its own.','error');return;}
  setBusy(true);status(retry?'Finishing game setup…':'Installing MSBT…');el('progress').hidden=false;el('progress').removeAttribute('value');
  try{
    const result=await window.linuxSetup.install({gameRoot:el('gameRoot').value,setupGame:el('setupGame').checked});
    if(!result?.ok)throw Error(result?.message || 'Installation could not finish.');
    const pending=['pending','failed'].includes(result.game?.state);
    el('progress').value=100;el('progress').hidden=true;el('gameCard').hidden=true;
    el('heading').textContent=pending?'Desktop installed.':'Installation complete.';
    el('intro').textContent=pending?'The desktop app is ready. Finish game integration when Borderlands 4 is closed.':'MSBT is ready to use. Your app settings stay in place.';
    status(pending?'Game integration still needs attention.':'Installation complete.',pending?'pending':'success');
    el('install').hidden=true;el('launch').hidden=false;el('finishGame').hidden=!pending;el('result').hidden=false;
    el('resultTitle').textContent=pending?'Desktop app installed':'MSBT is installed.';
    el('resultMessage').textContent=result.message || 'Open MSBT from your applications menu whenever you need it.';
    el('gameResult').textContent=result.game?.message || (pending?'Close Borderlands 4 normally, then choose Finish game setup.':'');
    el('gameResult').className=pending?'small pending':'small';
    if(pending)el('gameResult').textContent+=' Close the game normally, then click Finish game setup.';
    setBusy(false);
  }catch(error){setBusy(false);el('progress').hidden=true;status(error.message || String(error),'error');}
}
el('install').addEventListener('click',()=>install());
el('finishGame').addEventListener('click',()=>install(true));
el('launch').addEventListener('click',async()=>{el('launch').disabled=true;try{const result=await window.linuxSetup.launch();if(!result?.ok)throw Error(result?.message || 'Could not launch MSBT.');}catch(error){el('launch').disabled=false;status(error.message || String(error),'error');}});
(async()=>{try{
  const info=await window.linuxSetup.inspect();if(info?.ok===false)throw Error(info.message);
  el('installPath').textContent=info.installRoot || info.appPath || '';
  el('version').textContent=info.version ? `Version ${info.version}` : 'MSBT for Linux';
  for(const game of info.gameCandidates || [])addGame(game.root,game.label);
  if(!info.gameCandidates?.length){el('setupGame').checked=false;el('gameOptions').hidden=true;}
  if(info.gameCandidates?.length>1)el('gameRoot').selectedIndex=0;
  el('gameStatus').textContent=info.gameRunning?'Borderlands 4 is running. Setup will leave it open; game integration will wait until it is closed.':'The game can stay closed during setup.';
  el('loading').hidden=true;el('options').hidden=false;
}catch(error){el('loading').textContent=error.message || String(error);}})();
