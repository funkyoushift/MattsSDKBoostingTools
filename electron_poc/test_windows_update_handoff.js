'use strict';
const assert=require('assert/strict');
const fs=require('fs/promises');
const os=require('os');
const path=require('path');
const exec=require('util').promisify(require('child_process').execFile);
const {WINDOWS_HANDOFF_SCRIPT,windowsHandoffPayload}=require('./platform_release_updater');
(async()=>{
  if(process.platform!=='win32') {console.log('SKIP Windows native handoff fixture (requires Windows PowerShell/.NET)');return;}
  const temp=await fs.mkdtemp(path.join(os.tmpdir(),'msbt-win-handoff-'));
  try {
    const installer=path.join(temp,'installer.exe');
    const compile=path.join(temp,'compile.ps1');
    await fs.writeFile(compile,`$ErrorActionPreference='Stop'
Add-Type -OutputAssembly $args[0] -OutputType ConsoleApplication -TypeDefinition @'
using System;
using System.IO;
public class Probe {
  public static int Main(string[] args) {
    string exe = System.Reflection.Assembly.GetExecutingAssembly().Location;
    File.WriteAllText(exe + ".ran", Environment.CommandLine);
    return File.Exists(exe + ".fail") ? 1 : 0;
  }
}
'@
`);
    await exec('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',compile,installer]);
    const target=path.join(temp,"Custom O'Brien & $cash");await fs.mkdir(target);
    const executable=path.join(target,'MattsSDKBoostingTools.exe');await fs.copyFile(installer,executable);
    const script=path.join(temp,'handoff.ps1');await fs.writeFile(script,WINDOWS_HANDOFF_SCRIPT);
    const payload=windowsHandoffPayload({installer,executable,target,waitPid:2147483647,errorLog:path.join(temp,'error.txt')});
    // CI cannot approve UAC. Exercise the identical Start-Process/Wait/argument/
    // restart flow without its RunAs switch; unit test asserts production=true.
    payload.elevate=false;
    const invoke=()=>exec('powershell.exe',['-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',script,Buffer.from(JSON.stringify(payload)).toString('base64')],{timeout:30000});
    await invoke();
    assert((await fs.readFile(installer+'.ran','utf8')).trim().endsWith('/S /D='+target));
    for(let i=0;i<50;i++){try{await fs.access(executable+'.ran');break;}catch{await new Promise(r=>setTimeout(r,100));}}
    await fs.access(executable+'.ran');
    await fs.rm(executable+'.ran');await fs.writeFile(installer+'.fail','fail');
    await assert.rejects(invoke());
    assert.match(await fs.readFile(payload.errorLog,'utf8'),/Installer exited with code 1/);
    for(let i=0;i<50;i++){try{await fs.access(executable+'.ran');break;}catch{await new Promise(r=>setTimeout(r,100));}}
    await fs.access(executable+'.ran');
    console.log('PASS native Windows installer custom-directory handoff, final /D argument, restart and failed-install recovery (UAC switch unit-tested)');
  } finally {await fs.rm(temp,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exitCode=1;});
