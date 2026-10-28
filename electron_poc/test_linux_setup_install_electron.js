'use strict';
// Run after tools/build_linux.py. Installs the actual packaged AppImage only
// into a temporary HOME; no game integration, system package install or live
// user shortcuts are touched. Launch uses the installed wrapper in smoke mode.
const assert=require('assert/strict');
const fs=require('fs/promises');
const path=require('path');
const os=require('os');
const {execFile}=require('child_process');
const execute=require('util').promisify(execFile);
const {app}=require('electron');
const {runSetup}=require('./linux_setup');
const {createService,locations}=require('./linux_setup_service');
const root=path.resolve(__dirname,'..');
let temp;
(async()=>{
  temp=await fs.mkdtemp(path.join(os.tmpdir(),'msbt-real-installer-'));
  process.env.HOME=path.join(temp,'home');await fs.mkdir(process.env.HOME);
  process.env.XDG_CONFIG_HOME=path.join(temp,'config');app.setPath('userData',path.join(temp,'userdata'));
  process.env.XDG_DATA_HOME=path.join(temp,'data');
  const version=JSON.parse(await fs.readFile(path.join(__dirname,'package.json'),'utf8')).version;
  const resources=path.join(root,'dist_linux/linux-unpacked/resources');
  const imagePath=path.join(root,`dist_linux/MSBT-Installer-v${version}-linux-x64.AppImage`);
  const service=createService();
  const launch=async({home})=>{
    const dirs=locations(home);const receipt=JSON.parse(await fs.readFile(dirs.receipt));
    assert.equal(receipt.version,version);assert.equal(receipt.game.state,'skipped');
    await fs.access(dirs.desktop);await fs.access(dirs.setupDesktop);
    const env={...process.env,HOME:home};delete env.APPIMAGE;delete env.APPDIR;delete env.MSBT_PYTHON;
    const result=await execute(dirs.launcher,['--smoke'],{env,timeout:60000,maxBuffer:4*1024*1024});
    const smoke=JSON.parse(result.stdout.split('\n').find(line=>line.trim().startsWith('{')));
    assert.equal(smoke.ok,true);assert.equal(smoke.appVersion,version);assert.equal(smoke.packaged,true);
    console.log('PASS actual installer UI -> real AppImage copy/receipt/menu entries -> installed launcher and bundled runtime smoke; temporary HOME only');
    await fs.rm(temp,{recursive:true,force:true});
  };
  const win=await runSetup({service:{...service,launchInstalled:async options=>{
    try{return await launch(options);}catch(error){console.error(error);app.exit(1);throw error;}
  }},resources,imagePath,home:process.env.HOME});
  const evaluate=code=>win.webContents.executeJavaScript(code);
  async function waitFor(code){for(let i=0;i<300;i++){if(await evaluate(code))return;await new Promise(r=>setTimeout(r,100));}throw Error('Installer UI timed out: '+code);}
  await waitFor('document.getElementById("options").hidden === false');
  assert.equal(await evaluate('document.getElementById("setupGame").checked'),false,'No detected game should default to desktop-only setup');
  await evaluate('document.getElementById("install").click()');
  await waitFor('document.getElementById("launch").hidden === false');
  assert.match(await evaluate('document.getElementById("heading").textContent'),/complete/i);
  await fs.writeFile(path.join(root,'dist_unified','real-installer-success.png'),(await win.webContents.capturePage()).toPNG());
  await evaluate('document.getElementById("launch").click()');
})().catch(async error=>{console.error(error);if(temp)await fs.rm(temp,{recursive:true,force:true}).catch(()=>{});app.exit(1);});
setTimeout(()=>{console.error('Real installer launch did not complete');app.exit(1);},120000).unref();
