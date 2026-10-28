'use strict';
const assert=require('assert/strict');
const fs=require('fs/promises');
const path=require('path');
const os=require('os');
const {createHash}=require('crypto');
const {EventEmitter}=require('events');
const {execFile}=require('child_process');
const execute=require('util').promisify(execFile);
const {createService,nativeOverride,locations}=require('./linux_setup_service');
const hash=data=>createHash('sha256').update(data).digest('hex');
async function put(file,data){await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,data);}
async function fixture(root,name){
  const home=path.join(root,name+" Home O'Brien & $cash"),resources=path.join(root,name,'resources');
  const game=path.join(home,'.local/share/Steam/steamapps/common/Borderlands 4');
  const prefix=path.join(home,'.local/share/Steam/steamapps/compatdata/1285190/pfx');
  const image=path.join(root,name,'MSBT downloaded.AppImage');
  await put(image,Buffer.concat([Buffer.from([0x7f,0x45,0x4c,0x46]),Buffer.from('candidate-'+name)]));
  await put(path.join(resources,'releases/latest.json'),JSON.stringify({package_version:'2.40.1'}));
  await put(path.join(resources,'python/bin/python3'),'fixture python');await put(path.join(resources,'linux_bootstrap.py'),'fixture helper');
  await put(path.join(resources,'sdkmod/MattsSDKBoostingTools.sdkmod'),'new sdk');
  await put(path.join(resources,'sdkmods/ActorScriptDeployer/__init__.py'),'new asd');
  await put(path.join(resources,'linux-setup/icon.png'),'fixture icon');
  await fs.mkdir(path.join(resources,'oak2'),{recursive:true});
  await fs.copyFile(path.join(__dirname,'vendor/oak2/oak2-sdk.zip'),path.join(resources,'oak2/oak2-sdk.zip'));
  const pak=Buffer.from('fixture PAK');await put(path.join(resources,'afk_shift/pakchunk90-Windows_90_P.pak'),pak);
  await put(path.join(resources,'afk_shift/manifest.json'),JSON.stringify({sha256:hash(pak)}));
  await put(path.join(game,'OakGame/Binaries/Win64/Borderlands4.exe'),'fake game marker; never executed');
  await put(path.join(prefix,'user.reg'),'WINE REGISTRY Version 2\n\n[Other]\n"keep"="unchanged"\n');
  for(const name of ['vcruntime140.dll','msvcp140.dll'])await put(path.join(prefix,'drive_c/windows/system32',name),'MZ native runtime fixture');
  const calls=[];
  const run=async(file,args,options)=>{calls.push({file,args,options});return {stdout:args.includes('--probe-only')?JSON.stringify({ok:true,missing:[],family:'apt'}):''};};
  return {home,resources,game,prefix,image,calls,run};
}
(async()=>{
  if(process.platform!=='linux'){console.log('SKIP Linux installer filesystem tests');return;}
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'msbt-install-service-'));
  try {
    const original='WINE REGISTRY Version 2\r\n\r\n[Other]\r\n"keep"="yes"\r\n';
    const changed=nativeOverride(original);assert(changed.includes('"keep"="yes"'));assert(changed.includes('"dsound"="native,builtin"'));
    assert.equal(nativeOverride(changed),changed);assert.throws(()=>nativeOverride('bad registry'),/format/);
    assert.throws(()=>locations('/home/user\nExec=bad'),/invalid/);

    const f=await fixture(root,'desktop-only');let stateCalls=0;
    const service=createService({run:f.run,gameState:async()=>{stateCalls++;return {queryFailed:false,processes:[]};},isPrefixBusy:async()=>false});
    const before=await fs.readFile(path.join(f.prefix,'user.reg'));
    const result=await service.install({resources:f.resources,imagePath:f.image,home:f.home,setupGame:false});
    assert.equal(result.ok,true);assert.equal(result.game.state,'skipped');assert.equal(stateCalls,0);
    assert.equal(hash(await fs.readFile(result.appPath)),hash(await fs.readFile(f.image)));
    assert((await fs.stat(result.appPath)).mode&0o111);await execute('/bin/sh',['-n',result.launcherPath]);
    assert.match(await fs.readFile(result.desktopPath,'utf8'),/Exec="/);
    assert.match(await fs.readFile(result.setupDesktopPath,'utf8'),/ --setup/);
    assert.equal((await fs.readFile(path.join(f.prefix,'user.reg'))).compare(before),0);
    const receipt=JSON.parse(await fs.readFile(locations(f.home).receipt));assert.equal(receipt.schema,1);assert.equal(receipt.version,'2.40.1');
    // Repair keeps unrelated files, backs up the old image and never deletes user data.
    await put(path.join(locations(f.home).root,'keep-user-file'),'keep');
    assert((await service.install({resources:f.resources,imagePath:f.image,home:f.home,setupGame:false})).ok);
    assert.equal(await fs.readFile(path.join(locations(f.home).root,'keep-user-file'),'utf8'),'keep');
    assert((await fs.readdir(path.join(locations(f.home).root,'backups'))).length>0);

    for(const queryFailed of [false,true]) {
      const g=await fixture(root,'active-'+queryFailed);
      const blocked=createService({run:g.run,gameState:async()=>({queryFailed,processes:queryFailed?[]:[{pid:1}]}),isPrefixBusy:async()=>false});
      const installed=await blocked.install({resources:g.resources,imagePath:g.image,home:g.home,gameRoot:g.game,setupGame:true});
      assert.equal(installed.ok,true);assert.equal(installed.game.state,'pending');
      await assert.rejects(fs.access(path.join(g.game,'sdk_mods')));assert.match(await fs.readFile(installed.launcherPath,'utf8'),/MSBT_SAVE_ROOT/);
    }

    const g=await fixture(root,'full-game');
    const full=createService({run:g.run,gameState:async()=>({queryFailed:false,processes:[]}),isPrefixBusy:async()=>false});
    const integrated=await full.install({resources:g.resources,imagePath:g.image,home:g.home,gameRoot:g.game,setupGame:true});
    assert.equal(integrated.ok,true);assert.equal(integrated.game.state,'installed',integrated.game.message);
    assert.equal(await fs.readFile(path.join(g.game,'sdk_mods/MattsSDKBoostingTools.sdkmod'),'utf8'),'new sdk');
    assert.match(await fs.readFile(path.join(g.prefix,'user.reg'),'utf8'),/"dsound"="native,builtin"/);
    assert.match(await fs.readFile(path.join(g.prefix,'user.reg'),'utf8'),/unchanged/);
    assert.equal(JSON.parse(await fs.readFile(path.join(g.game,'sdk_mods/settings/MattsSDKBoostingTools.json'))).enabled,true);
    assert.equal(g.calls.filter(x=>x.file==='/usr/bin/protontricks').length,0);

    // Missing runtime/declined setup remains pending, never a ready game claim.
    await fs.rm(path.join(g.prefix,'drive_c/windows/system32/vcruntime140.dll'));
    const pending=await full.install({resources:g.resources,imagePath:g.image,home:g.home,gameRoot:g.game,setupGame:true});
    assert.equal(pending.ok,true);assert.equal(pending.game.state,'pending');
    assert(g.calls.some(x=>x.file==='/usr/bin/protontricks' && x.args.join(' ')==='1285190 vcrun2022'));
    assert.equal(g.calls.find(x=>x.file==='/usr/bin/protontricks').options.env.STEAM_COMPAT_DATA_PATH,path.dirname(g.prefix));

    const linked=await fixture(root,'linked-pak');const outside=path.join(root,'unrelated-file');await put(outside,'keep');
    const pak=path.join(linked.game,'OakGame/Content/Paks/pakchunk90-Windows_90_P.pak');await fs.mkdir(path.dirname(pak),{recursive:true});await fs.symlink(outside,pak);
    const linkService=createService({run:linked.run,gameState:async()=>({queryFailed:false,processes:[]}),isPrefixBusy:async()=>false});
    const linkResult=await linkService.install({resources:linked.resources,imagePath:linked.image,home:linked.home,gameRoot:linked.game,setupGame:true});
    assert.equal(linkResult.game.state,'pending');assert.equal(await fs.readFile(outside,'utf8'),'keep');await assert.rejects(fs.access(path.join(linked.game,'sdk_mods')));

    const wrong=await fixture(root,'wrong-game');await fs.rename(path.join(wrong.game,'OakGame/Binaries/Win64/Borderlands4.exe'),path.join(wrong.game,'OakGame/Binaries/Win64/Borderlands3.exe'));
    const wrongService=createService({run:wrong.run,gameState:async()=>({queryFailed:false,processes:[]}),isPrefixBusy:async()=>false});
    const wrongResult=await wrongService.install({resources:wrong.resources,imagePath:wrong.image,home:wrong.home,gameRoot:wrong.game,setupGame:true});
    assert.equal(wrongResult.game.state,'pending');assert.match(wrongResult.game.message,/not a Borderlands 4/);await assert.rejects(fs.access(path.join(wrong.game,'sdk_mods')));

    const protectedFixture=await fixture(root,'settings-protection');
    await put(path.join(protectedFixture.game,'sdk_mods/settings/MattsSDKBoostingTools.json'),'broken settings');
    const protectedService=createService({run:protectedFixture.run,gameState:async()=>({queryFailed:false,processes:[]}),isPrefixBusy:async()=>false});
    const protectedResult=await protectedService.install({resources:protectedFixture.resources,imagePath:protectedFixture.image,home:protectedFixture.home,gameRoot:protectedFixture.game,setupGame:true});
    assert.equal(protectedResult.game.state,'pending');assert.equal(await fs.readFile(path.join(protectedFixture.game,'sdk_mods/settings/MattsSDKBoostingTools.json'),'utf8'),'broken settings');
    await assert.rejects(fs.access(path.join(protectedFixture.game,'sdk_mods/MattsSDKBoostingTools.sdkmod')));

    const wineFixture=await fixture(root,'prefix-active');
    const busyPrefix=createService({run:wineFixture.run,gameState:async()=>({queryFailed:false,processes:[]}),isPrefixBusy:async()=>true});
    const wineResult=await busyPrefix.install({resources:wineFixture.resources,imagePath:wineFixture.image,home:wineFixture.home,gameRoot:wineFixture.game,setupGame:true});
    assert.equal(wineResult.game.state,'pending');await assert.rejects(fs.access(path.join(wineFixture.game,'sdk_mods')));

    const bad=await fixture(root,'requirements-fail');
    const rejected=createService({run:async()=>({stdout:JSON.stringify({ok:false,missing:['libgtk-3.so.0']})})});
    const failed=await rejected.install({resources:bad.resources,imagePath:bad.image,home:bad.home,setupGame:false});
    assert.equal(failed.ok,false);await assert.rejects(fs.access(locations(bad.home).receipt));
    await assert.rejects(fs.access(locations(bad.home).image));

    const launches=[];const launchService=createService({start:(file,args,options)=>{launches.push({file,args,options});const child=new EventEmitter();child.unref=()=>{};process.nextTick(()=>child.emit('spawn'));return child;}});
    await launchService.launchInstalled({home:f.home});assert.equal(launches[0].file,locations(f.home).launcher);assert.equal(launches[0].options.env.APPIMAGE,undefined);
    console.log('PASS real installer filesystem: requirements, app/shortcuts/repair backups, stopped-game SDK/Proton setup, running/unknown-game preservation, pending runtime, safe launch');
  }finally{await fs.rm(root,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exitCode=1;});
