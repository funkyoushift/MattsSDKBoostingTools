const path = require('path');

async function selectSdkTarget({ explicit = '', running = [], remembered = '', candidates = [], valid, normalize }) {
  const unique = values => [...new Map(values.filter(Boolean).map(value => {
    const normalized = normalize(value);
    return [normalized.toLowerCase(), normalized];
  })).values()];
  const active = unique(running);
  const selected = explicit ? normalize(explicit) : active.length === 1 ? active[0] : remembered ? normalize(remembered) : '';
  if (selected) {
    if (!await valid(selected)) return {ok:false, path:selected, message:'The selected game installation is unavailable. Choose its game folder; another installation will not be substituted.'};
    return {ok:true, path:selected, gameRoot:path.dirname(selected),
      runningMismatch:active.some(value => value.toLowerCase() !== selected.toLowerCase())};
  }
  const found = [];
  for (const candidate of unique(candidates)) if (await valid(candidate)) found.push(candidate);
  if (active.length > 1 || found.length !== 1) return {ok:false, path:'', candidates:found,
    message:found.length > 1 ? 'Multiple Borderlands 4 installations found. Choose the installation to check or update.' : 'Choose your Borderlands 4 game folder.'};
  return {ok:true, path:found[0], gameRoot:path.dirname(found[0]), runningMismatch:false};
}

function loadedSdkState({running, runtime, installed, target}) {
  if (!running) return {status:'not_running', message:'Game is closed. Installed files will load on its next start.'};
  if (target.runningMismatch) return {status:'wrong_installation', message:'The running game is a different installation from the selected folder.'};
  if (!runtime || !runtime.sha256 || !runtime.sdkmod_path) return {status:'unverified', message:'Running SDK version cannot be verified. Older SDKs do not report loaded build identity; restart after installing the bundled game files.'};
  if (runtime.sdkmod_path.replaceAll('\\','/').toLowerCase() !== String(installed.path || '').replaceAll('\\','/').toLowerCase())
    return {status:'wrong_installation', message:'The connected game loaded its SDK from a different installation.'};
  return runtime.sha256 === installed.sha256
    ? {status:'current', message:`Running SDK ${runtime.version || ''} matches the installed files.`}
    : {status:'restart_required', message:'Installed files changed after the SDK loaded. Restart Borderlands 4 to load the update.'};
}
module.exports = {selectSdkTarget, loadedSdkState};
