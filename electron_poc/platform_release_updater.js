'use strict';
const {EventEmitter} = require('events');
const fs = require('fs/promises');
const {constants} = require('fs');
const path = require('path');
const {createHash} = require('crypto');
const {spawn, execFile} = require('child_process');
const {promisify} = require('util');
const exec = promisify(execFile);
const REPOSITORY = 'funkyoushift/MattsSDKBoostingTools';
const API_URL = `https://api.github.com/repos/${REPOSITORY}/releases/latest`;

function releaseInfo(release, platform = process.platform, appImage = Boolean(process.env.APPIMAGE)) {
  if (!release || release.draft || release.prerelease || !/^v\d+\.\d+\.\d+$/.test(release.tag_name || '')) throw Error('GitHub did not return a stable versioned release.');
  const tag = release.tag_name;
  const version = tag.slice(1);
  const names = platform === 'linux'
    ? {installer:`MSBT-Installer-${tag}-linux-x64.AppImage`, portable:`MSBT-Portable-${tag}-linux-x64.tar.gz`}
    : platform === 'win32'
      ? {installer:`MSBT-Installer-${tag}.exe`, portable:`MSBT-Portable-${tag}-win-x64.zip`}
      : null;
  if (!names) throw Error('This platform has no MSBT release package.');
  const asset = name => {
    const matches = (release.assets || []).filter(row => row.name === name);
    if(matches.length !== 1) throw Error(`Release must contain exactly one ${name}.`);
    const result = matches[0];
    if(result.browser_download_url !== `https://github.com/${REPOSITORY}/releases/download/${tag}/${name}`
      || !/^sha256:[a-f0-9]{64}$/i.test(result.digest || '') || !Number.isSafeInteger(result.size) || result.size < 1 || result.size > 2*1024**3)
      throw Error(`Invalid GitHub URL, digest or size for ${name}.`);
    return result;
  };
  const installer = asset(names.installer), portable = asset(names.portable);
  const selected = platform === 'linux' && !appImage ? portable : installer;
  return {version, tag, installer, portable, selected, releaseUrl:`https://github.com/${REPOSITORY}/releases/tag/${tag}`};
}
async function fetchRelease({fetcher = fetch, platform = process.platform, appImage} = {}) {
  const response = await fetcher(API_URL,{cache:'no-store',headers:{Accept:'application/vnd.github+json'},signal:AbortSignal.timeout(30000)});
  if(!response.ok) throw Error(`GitHub release request failed (${response.status}).`);
  return releaseInfo(await response.json(),platform,appImage);
}
function asManifest(info) {
  return {package_version:info.version,app_version:info.version,electron_version:info.version,sdkmod_version:info.version,
    resources_version:info.version,release_url:info.releaseUrl,download_url:info.selected.browser_download_url,
    electron_installer_download_url:info.installer.browser_download_url,manual_zip_download_url:info.portable.browser_download_url};
}
async function downloadVerified(asset, folder, {fetcher = fetch,onProgress = ()=>{}} = {}) {
  await fs.mkdir(folder,{recursive:true});
  const staging = await fs.mkdtemp(path.join(folder,'download-'));
  const output = path.join(staging,asset.name);
  let file;
  try {
    const response = await fetcher(asset.browser_download_url,{signal:AbortSignal.timeout(30*60*1000)});
    if(!response.ok || !response.body) throw Error(`Update download failed (${response.status}).`);
    file = await fs.open(output,'wx',0o600);
    const hash = createHash('sha256'); let size = 0;
    for await(const chunk of response.body) {
      size += chunk.length;
      if(size > asset.size) throw Error('Update exceeds the declared GitHub asset size.');
      hash.update(chunk); await file.writeFile(chunk);
      onProgress({percent:100*size/asset.size,transferred:size,total:asset.size});
    }
    await file.close(); file = null;
    if(size !== asset.size || `sha256:${hash.digest('hex')}` !== asset.digest.toLowerCase()) throw Error('Update SHA-256 or size verification failed.');
    return output;
  } catch(error) { if(file) await file.close(); await fs.rm(staging,{recursive:true,force:true}); throw error; }
}

// Stage on the installation filesystem, then swap only the known application
// path after exit. The original launcher path stays stable and rollback is retained.
class LinuxReleaseUpdater extends EventEmitter {
  constructor({app,isNewer,fetcher = fetch,start = spawn,execute = exec,appImage = Boolean(process.env.APPIMAGE), executable = process.execPath, appImagePath = process.env.APPIMAGE}) {
    super();Object.assign(this,{app,isNewer,fetcher,start,execute,appImage,executable,appImagePath});this.ready=false;this.busy=false;
  }
  async checkForUpdates() {
    this.emit('checking-for-update');
    const next = await fetchRelease({fetcher:this.fetcher,platform:'linux',appImage:this.appImage});
    if(this.info?.version !== next.version) this.ready=false;
    this.info=next;
    this.emit(this.ready?'update-downloaded':this.isNewer(next.version,this.app.getVersion())?'update-available':'update-not-available',next);
    return {updateInfo:next};
  }
  async downloadUpdate() {
    if(this.busy) throw Error('An update is already downloading.');
    this.busy=true;this.ready=false;
    try {
      if(!this.info) await this.checkForUpdates();
      if(!this.isNewer(this.info.version,this.app.getVersion())) throw Error('No newer Linux release is available.');
      const folder=path.join(this.app.getPath('userData'),'updates');
      const downloaded=await downloadVerified(this.info.selected,folder,{fetcher:this.fetcher,onProgress:p=>this.emit('download-progress',p)});
      this.target=await fs.realpath(this.appImage ? this.appImagePath : path.dirname(await fs.realpath(this.executable)));
      const parent=path.dirname(this.target);
      if(parent==='/' || this.target==='/' || this.target==='/usr' || this.target==='/opt') throw Error('Unsafe Linux update installation path.');
      await fs.access(parent,constants.W_OK);
      const stageRoot=await fs.mkdtemp(path.join(parent,'.msbt-update-'));
      if(this.appImage) {
        this.stage=path.join(stageRoot,path.basename(this.target));
        await fs.copyFile(downloaded,this.stage);await fs.chmod(this.stage,0o755);this.launch=this.target;
      } else {
        await fs.access(path.join(this.target,'resources','app.asar'));
        await fs.access(path.join(this.target,'LINUX-PYTHON-PROVENANCE.json'));
        if(path.basename(this.executable)!=='MattsSDKBoostingTools') throw Error('This is not an MSBT portable application directory.');
        const entries=(await this.execute('tar',['-tzf',downloaded],{maxBuffer:16*1024*1024})).stdout.split('\n').filter(Boolean);
        const root=`MSBT-Portable-${this.info.tag}-linux-x64`;
        if(!entries.length || entries.some(name=>name.startsWith('/') || name.split('/').includes('..') || name.split('/')[0]!==root)) throw Error('Linux update archive has an unexpected layout.');
        const extracted=await fs.mkdtemp(path.join(folder,'installed-'));
        await this.execute('tar',['-xzf',downloaded,'--no-same-owner','-C',extracted],{timeout:120000});
        await fs.access(path.join(extracted,root,'msbt'));
        this.stage=path.join(stageRoot,root);await fs.rename(path.join(extracted,root),this.stage).catch(async error=>{if(error.code!=='EXDEV')throw error;await fs.cp(path.join(extracted,root),this.stage,{recursive:true});});
        this.launch=path.join(this.target,'msbt');
      }
      this.info={...this.info,installPath:this.launch};this.ready=true;
      this.emit('update-downloaded',this.info);return [this.launch];
    } finally {this.busy=false;}
  }
  async quitAndInstall() {
    if(!this.ready || !this.launch) throw Error('Download and verify the update first.');
    const folder=path.join(this.app.getPath('userData'),'updates');
    await fs.mkdir(folder,{recursive:true});
    const runner=path.join(await fs.mkdtemp(path.join(folder,'activate-')),'activate-msbt-update.sh');
    const backup=this.target+'.previous-'+Date.now();
    await fs.writeFile(runner,HANDOFF_SCRIPT,{mode:0o700});
    const env={...process.env};delete env.APPIMAGE;delete env.APPDIR;delete env.MSBT_PYTHON;delete env.ELECTRON_RUN_AS_NODE;
    await new Promise((resolve,reject)=>{
      const child=this.start('/bin/sh',[runner,String(process.pid),this.target,this.stage,backup,this.launch],{cwd:path.dirname(this.launch),env,detached:true,stdio:'ignore'});
      child.once('error',reject);child.once('spawn',()=>{child.unref();resolve();});
    });
    this.app.quit();
  }
}
const HANDOFF_SCRIPT = `#!/bin/sh
while kill -0 "$1" 2>/dev/null; do sleep 1; done
# Never overwrite a retained backup; all paths are passed as arguments.
[ ! -e "$4" ] || exit 1
mv -- "$2" "$4" || exit 1
if ! mv -- "$3" "$2"; then mv -- "$4" "$2"; exit 1; fi
"$5" || { mv -- "$2" "$2.failed-$$"; mv -- "$4" "$2"; exec "$5"; }
`;
module.exports={HANDOFF_SCRIPT,API_URL,releaseInfo,fetchRelease,asManifest,downloadVerified,LinuxReleaseUpdater};
