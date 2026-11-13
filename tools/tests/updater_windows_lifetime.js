'use strict';
// Disposable Windows process-lifetime experiment. No installers or application UI.
const fs=require('fs');
const path=require('path');
const os=require('os');
const {spawn}=require('child_process');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
if(process.argv[2]==='parent') {
 const folder=process.argv[3],detached=process.argv[4]==='true',ack=process.argv[5]==='true';
 const out=fs.openSync(path.join(folder,'helper.stdout.txt'),'w'),err=fs.openSync(path.join(folder,'helper.stderr.txt'),'w');
 const helper=spawn('powershell.exe',['-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',path.join(folder,'helper.ps1'),String(process.pid),folder],{cwd:folder,detached,windowsHide:true,stdio:['ignore',out,err]});
 helper.on('error',error=>fs.writeFileSync(path.join(folder,'spawn-error.txt'),String(error)));
 helper.on('exit',(code,signal)=>fs.writeFileSync(path.join(folder,'helper-exit-observed.json'),JSON.stringify({code,signal})));
 helper.on('spawn',async()=>{
  fs.writeFileSync(path.join(folder,'helper-pid.txt'),String(helper.pid));helper.unref();
  if(ack) {const deadline=Date.now()+4000;while(Date.now()<deadline&&!fs.existsSync(path.join(folder,'started.txt')))await delay(25);}
  fs.writeFileSync(path.join(folder,'parent-exiting.json'),JSON.stringify({pid:process.pid,acknowledged:fs.existsSync(path.join(folder,'started.txt')),at:new Date().toISOString()}));
  fs.closeSync(out);fs.closeSync(err);
 });
} else if(process.argv[2]==='bootstrap-parent') {
 const folder=process.argv[3];
 const payload=Buffer.from(JSON.stringify({helper:path.join(folder,'helper.ps1'),parentPid:process.pid,folder})).toString('base64');
 const out=fs.openSync(path.join(folder,'bootstrap.stdout.txt'),'w'),err=fs.openSync(path.join(folder,'bootstrap.stderr.txt'),'w');
 const bootstrap=spawn('powershell.exe',['-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',path.join(folder,'bootstrap.ps1'),payload],{cwd:folder,detached:false,windowsHide:true,stdio:['ignore',out,err]});
 bootstrap.on('error',error=>fs.writeFileSync(path.join(folder,'spawn-error.txt'),String(error)));
 bootstrap.on('exit',async(code,signal)=>{
  fs.writeFileSync(path.join(folder,'bootstrap-exit.json'),JSON.stringify({code,signal}));
  const deadline=Date.now()+4000;while(Date.now()<deadline&&!fs.existsSync(path.join(folder,'started.txt')))await delay(25);
  fs.writeFileSync(path.join(folder,'parent-exiting.json'),JSON.stringify({pid:process.pid,acknowledged:fs.existsSync(path.join(folder,'started.txt')),at:new Date().toISOString()}));
  fs.closeSync(out);fs.closeSync(err);
 });
} else {
 (async()=>{
  if(process.platform!=='win32')throw Error('Windows native lifetime experiment only');
  const root=path.resolve(process.argv[2]||path.join(os.tmpdir(),'msbt-updater-lifetime-'+Date.now()));fs.mkdirSync(root,{recursive:true});
  const results=[];
  for(const detached of [true,false])for(const ack of [false,true]) {
   const folder=path.join(root,`detached-${detached}-ack-${ack}`);fs.mkdirSync(folder,{recursive:true});
   fs.writeFileSync(path.join(folder,'helper.ps1'),`$ErrorActionPreference='Stop'\n$parentPid=[int]$args[0]\n$folder=$args[1]\ntry {\n  ('started '+$PID) | Set-Content -LiteralPath (Join-Path $folder 'started.txt')\n  Wait-Process -Id $parentPid -ErrorAction SilentlyContinue\n  'parent-exited' | Set-Content -LiteralPath (Join-Path $folder 'after-parent.txt')\n} catch {\n  ($_ | Out-String) | Set-Content -LiteralPath (Join-Path $folder 'helper-error.txt')\n  exit 1\n}\n`);
   const stdout=fs.openSync(path.join(folder,'parent.stdout.txt'),'w'),stderr=fs.openSync(path.join(folder,'parent.stderr.txt'),'w');
   const parent=spawn(process.execPath,[__filename,'parent',folder,String(detached),String(ack)],{windowsHide:true,stdio:['ignore',stdout,stderr]});
   let parentExit=null;parent.on('exit',(code,signal)=>{parentExit={code,signal};});
   const deadline=Date.now()+10000;
   while(Date.now()<deadline&&(!parentExit||!fs.existsSync(path.join(folder,'after-parent.txt'))))await delay(50);
   const read=name=>fs.existsSync(path.join(folder,name))?fs.readFileSync(path.join(folder,name),'utf8'):null;
   const pid=Number(read('helper-pid.txt'));let helperAlive=false;
   if(pid){try{process.kill(pid,0);helperAlive=true;}catch{}}
   const observedExit=read('helper-exit-observed.json');
   const helperExitCode=observedExit?JSON.parse(observedExit).code:null;
   const result={detached,ack,parentExit,helperExitCode,helperExitCodeEvidence:observedExit?'Parent observed helper exit':'Not observable after parent exit',helperPid:pid||null,helperAlive,started:read('started.txt'),afterParent:read('after-parent.txt'),parentExitReceipt:read('parent-exiting.json'),helperExitObserved:read('helper-exit-observed.json'),helperStderr:read('helper.stderr.txt'),helperError:read('helper-error.txt'),spawnError:read('spawn-error.txt')};
   // Kill only this fixture's recorded processes if the bounded case timed out.
   if(!parentExit)parent.kill();if(helperAlive){try{process.kill(pid);}catch{}}
   fs.closeSync(stdout);fs.closeSync(stderr);results.push(result);
  }
  // A PowerShell Start-Process bootstrap requests a separate hidden console.
  // Retain the four direct-spawn cases above unchanged for comparison.
  {
   const folder=path.join(root,'shell-bootstrap-ack');fs.mkdirSync(folder,{recursive:true});
   fs.copyFileSync(path.join(root,'detached-true-ack-false','helper.ps1'),path.join(folder,'helper.ps1'));
   fs.writeFileSync(path.join(folder,'bootstrap.ps1'),`$ErrorActionPreference='Stop'\n$data=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($args[0])) | ConvertFrom-Json\ntry {\n  $arguments='-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$data.helper+'" '+$data.parentPid+' "'+$data.folder+'"'\n  $inner=Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $data.folder 'helper.stdout.txt') -RedirectStandardError (Join-Path $data.folder 'helper.stderr.txt')\n  $inner.Id | Set-Content -LiteralPath (Join-Path $data.folder 'helper-pid.txt')\n} catch {\n  ($_ | Out-String) | Set-Content -LiteralPath (Join-Path $data.folder 'bootstrap-error.txt')\n  exit 1\n}\n`);
   const stdout=fs.openSync(path.join(folder,'parent.stdout.txt'),'w'),stderr=fs.openSync(path.join(folder,'parent.stderr.txt'),'w');
   const parent=spawn(process.execPath,[__filename,'bootstrap-parent',folder],{windowsHide:true,stdio:['ignore',stdout,stderr]});
   let parentExit=null;parent.on('exit',(code,signal)=>{parentExit={code,signal};});
   const deadline=Date.now()+10000;
   while(Date.now()<deadline&&(!parentExit||!fs.existsSync(path.join(folder,'after-parent.txt'))))await delay(50);
   const read=name=>fs.existsSync(path.join(folder,name))?fs.readFileSync(path.join(folder,name),'utf8'):null;
   const pid=Number(read('helper-pid.txt'));let helperAlive=false;
   if(pid){try{process.kill(pid,0);helperAlive=true;}catch{}}
   results.push({mode:'shell-bootstrap',ack:true,parentExit,bootstrapExit:read('bootstrap-exit.json'),helperPid:pid||null,helperAlive,helperExitCode:null,helperExitCodeEvidence:'Not observable after bootstrap exit',started:read('started.txt'),afterParent:read('after-parent.txt'),parentExitReceipt:read('parent-exiting.json'),helperStderr:read('helper.stderr.txt'),helperError:read('helper-error.txt'),bootstrapError:read('bootstrap-error.txt'),bootstrapStderr:read('bootstrap.stderr.txt'),spawnError:read('spawn-error.txt')});
   if(!parentExit)parent.kill();if(helperAlive){try{process.kill(pid);}catch{}}
   fs.closeSync(stdout);fs.closeSync(stderr);
  }
  fs.writeFileSync(path.join(root,'receipt.json'),JSON.stringify({platform:process.platform,node:process.version,at:new Date().toISOString(),results},null,2)+'\n');
  console.log(JSON.stringify({receipt:path.join(root,'receipt.json'),results}));
 })().catch(error=>{console.error(error);process.exitCode=1;});
}
