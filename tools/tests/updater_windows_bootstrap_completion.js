'use strict';
const fs=require('fs');const path=require('path');const os=require('os');const {spawn,execFile}=require('child_process');const {promisify}=require('util');
const {WINDOWS_BOOTSTRAP_SCRIPT}=require('../../electron_poc/platform_release_updater');
(async()=>{
 if(process.platform!=='win32')throw Error('Windows only');
 const root=path.resolve(process.argv[2]||fs.mkdtempSync(path.join(os.tmpdir(),'msbt-bootstrap-completion-')));fs.mkdirSync(root,{recursive:true});
 const results=[];
 for(const mode of ['execFile-close','spawn-exit']){
  const folder=path.join(root,mode);fs.mkdirSync(folder,{recursive:true});fs.writeFileSync(folder+'/bootstrap.ps1',WINDOWS_BOOTSTRAP_SCRIPT);
  fs.writeFileSync(folder+'/helper.ps1',"$data=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($args[0])) | ConvertFrom-Json\n'ready' | Set-Content -LiteralPath $data.readyFile\nStart-Sleep -Seconds 3\n'done' | Set-Content -LiteralPath $data.doneFile\n");
  const data={script:folder+'/helper.ps1',payload:Buffer.from(JSON.stringify({readyFile:folder+'/ready.txt',doneFile:folder+'/done.txt'})).toString('base64'),stdout:folder+'/helper.stdout.txt',stderr:folder+'/helper.stderr.txt',pidFile:folder+'/helper-pid.txt'};
  const args=['-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',folder+'/bootstrap.ps1',Buffer.from(JSON.stringify(data)).toString('base64')],start=Date.now();
  if(mode==='execFile-close')await promisify(execFile)('powershell.exe',args,{cwd:folder,windowsHide:true,timeout:10000});
  else await new Promise((resolve,reject)=>{const child=spawn('powershell.exe',args,{cwd:folder,windowsHide:true,stdio:'ignore'});child.once('error',reject);child.once('exit',(code)=>code===0?resolve():reject(Error('Bootstrap exit '+code)));});
  results.push({mode,elapsedMs:Date.now()-start,ready:fs.existsSync(folder+'/ready.txt'),helperDoneAtBootstrapCompletion:fs.existsSync(folder+'/done.txt')});
 }
 fs.writeFileSync(root+'/receipt.json',JSON.stringify({results},null,2));console.log(JSON.stringify({root,results}));
})().catch(error=>{console.error(error);process.exitCode=1;});
