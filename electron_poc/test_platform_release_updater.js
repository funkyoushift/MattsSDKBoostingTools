'use strict';
const assert=require('assert/strict');
const fs=require('fs/promises');
const os=require('os');
const path=require('path');
const {createHash}=require('crypto');
const {execFile}=require('child_process');
const exec=require('util').promisify(execFile);
const {releaseInfo,asManifest,downloadVerified,HANDOFF_SCRIPT,LinuxReleaseUpdater}=require('./platform_release_updater');
const payload=Buffer.from('verified release');
const digest='sha256:'+createHash('sha256').update(payload).digest('hex');
const version='2.40.0',tag='v'+version;
const names=[`MSBT-Installer-${tag}.exe`,`MSBT-Portable-${tag}-win-x64.zip`,`MSBT-Installer-${tag}-linux-x64.AppImage`,`MSBT-Portable-${tag}-linux-x64.tar.gz`];
const assets=names.map(name=>({name,digest,size:payload.length,browser_download_url:`https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/${tag}/${name}`}));
const release={tag_name:tag,assets};
(async()=>{
  assert.equal(releaseInfo(release,'win32').selected.name,names[0]);
  assert.equal(releaseInfo(release,'linux',true).selected.name,names[2]);
  const linux=releaseInfo(release,'linux',false);
  assert.equal(linux.selected.name,names[3]);
  assert(asManifest(linux).electron_installer_download_url.endsWith('.AppImage'));
  assert.throws(()=>releaseInfo({...release,assets:assets.slice(0,2)},'linux'),/exactly one/);
  assert.throws(()=>releaseInfo({...release,prerelease:true},'linux'),/stable/);
  assert.throws(()=>releaseInfo({...release,assets:assets.map(a=>({...a,browser_download_url:'https://evil.invalid/file'}))},'linux'),/Invalid GitHub/);
  const temp=await fs.mkdtemp(path.join(os.tmpdir(),'msbt-updater-'));
  try{
    const fetcher=async()=>({ok:true,body:(async function*(){yield payload;})()});
    const output=await downloadVerified(assets[2],temp,{fetcher});
    assert.equal(await fs.readFile(output,'utf8'),payload.toString());
    await assert.rejects(downloadVerified({...assets[2],digest:'sha256:'+'0'.repeat(64)},temp,{fetcher}),/verification failed/);
    await assert.rejects(downloadVerified({...assets[2],size:1},temp,{fetcher}),/exceeds/);
    const app={getVersion:()=> '2.39.10',getPath:()=>temp,quit:()=>{throw Error('must not quit during check');}};
    const updater=new LinuxReleaseUpdater({app,isNewer:(a,b)=>a!==b,fetcher:async()=>({ok:true,json:async()=>release}),appImage:true});
    const events=[];updater.on('update-available',info=>events.push(info));
    await updater.checkForUpdates();assert.equal(events[0].selected.name,names[2]);
    // Run the real detached handoff script against disposable installation fixtures.
    const runner=path.join(temp,'handoff.sh');await fs.writeFile(runner,HANDOFF_SCRIPT);
    const target=path.join(temp,'portable'),stage=path.join(temp,'stage'),backup=path.join(temp,'previous');
    for(const dir of [target,stage])await fs.mkdir(dir);
    await fs.writeFile(path.join(target,'old'),'old');
    await fs.writeFile(path.join(stage,'msbt'),'#!/bin/sh\necho updated > "$(dirname "$0")/launched"\n',{mode:0o755});
    await exec('/bin/sh',[runner,'2147483647',target,stage,backup,path.join(target,'msbt')]);
    assert.equal(await fs.readFile(path.join(target,'launched'),'utf8'),'updated\n');
    assert.equal(await fs.readFile(path.join(backup,'old'),'utf8'),'old');
    // A failed stage rename restores the old installation at its original path.
    const previous2=path.join(temp,'previous2');
    await assert.rejects(exec('/bin/sh',[runner,'2147483647',target,path.join(temp,'missing'),previous2,path.join(target,'msbt')]));
    assert.equal(await fs.readFile(path.join(target,'launched'),'utf8'),'updated\n');
    await assert.rejects(fs.access(previous2));
    // AppImage replacements retain the original executable path and executable backup.
    const image=path.join(temp,'MSBT.AppImage'),next=path.join(temp,'next.AppImage');
    await fs.writeFile(image,'#!/bin/sh\nexit 0\n',{mode:0o755});
    await fs.writeFile(next,'#!/bin/sh\nexit 0\n',{mode:0o755});
    await exec('/bin/sh',[runner,'2147483647',image,next,image+'.previous',image]);
    await fs.access(image);await fs.access(image+'.previous');
    // Failed launch rolls back to the known previous launcher at the same path.
    const bad=path.join(temp,'bad.AppImage');await fs.writeFile(bad,'#!/bin/sh\nexit 3\n',{mode:0o755});
    await exec('/bin/sh',[runner,'2147483647',image,bad,image+'.previous2',image]);
    assert.match(await fs.readFile(image,'utf8'),/exit 0/);
  }finally{await fs.rm(temp,{recursive:true,force:true});}
  console.log('PASS platform selection, GitHub URL/digest guards, verified download, stable-path portable/AppImage activation and rollback');
})().catch(error=>{console.error(error);process.exitCode=1;});
