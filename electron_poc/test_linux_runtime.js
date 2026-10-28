'use strict';
const assert = require('assert/strict');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const {execFileSync} = require('child_process');
const linux = require('./linux_runtime');
const oak = require('./oak2_install');
const {selectSdkTarget} = require('./sdk_target');
(async () => {
  assert.equal(linux.pythonPaths('/src', '/res', 'linux').bundled, '/res/python/bin/python3');
  assert.equal(linux.pythonPaths('/src', '/res', 'win32').bundled, '/res/python/python.exe');
  assert(linux.steamRoots({HOME:'/home/test', XDG_DATA_HOME:'/data'}).includes('/data/Steam'));
  assert(linux.steamRoots({HOME:'/home/test'}).includes('/home/test/.var/app/com.valvesoftware.Steam/.local/share/Steam'));
  assert.equal(linux.gameArgument(['wine', '/games/Borderlands4.exe']), '/games/Borderlands4.exe');
  assert.equal(linux.gameArgument(['other', 'Borderlands4.exe.bak']), undefined);
  assert.equal(linux.gameRootFromArgument('Z:\\games\\BL4\\OakGame\\Binaries\\Win64\\Borderlands4.exe', '/'), '/games/BL4');
  assert.equal(linux.gameRootFromArgument('C:\\games\\OakGame\\Binaries\\Win64\\Borderlands4.exe', '/'), '');
  assert.throws(() => linux.replaySaveRoot({}), /MSBT_SAVE_ROOT/);
  assert.equal(linux.replaySaveRoot({MSBT_SAVE_ROOT:'/proton/save'}), '/proton/save');
  const proc = await fs.mkdtemp(path.join(os.tmpdir(), 'msbt-proc-'));
  try {
    await fs.mkdir(path.join(proc,'123'));
    await fs.writeFile(path.join(proc,'123','cmdline'), 'wine\0/games/BL4/OakGame/Binaries/Win64/Borderlands4.exe\0');
    await fs.symlink('/games/BL4',path.join(proc,'123','cwd'));
    const active = await linux.inspectGameProcesses({procRoot:proc});
    assert.equal(active.queryFailed, false);
    assert.deepEqual(active.processes, [{pid:123, gameRoot:'/games/BL4'}]);
    const unreadable = await linux.inspectGameProcesses({io:{...fs, readFile:async()=>{throw Object.assign(Error(),{code:'EACCES'});}},procRoot:proc});
    assert.equal(unreadable.queryFailed,true);
    const missing = await linux.inspectGameProcesses({procRoot:path.join(proc,'missing')});
    assert.equal(missing.queryFailed,true);
    const exited = await linux.inspectGameProcesses({io:{...fs,readFile:async()=>{throw Object.assign(Error(),{code:'ENOENT'});}},procRoot:proc});
    assert.deepEqual(exited,{processes:[],queryFailed:false});
    const ambiguous = await selectSdkTarget({candidates:['/Games/BL4/sdk_mods','/games/BL4/sdk_mods'], normalize:x=>x,valid:async()=>true,platform:'linux'});
    assert.equal(ambiguous.ok,false);
    assert.equal(ambiguous.candidates.length,2);
    await fs.mkdir(path.join(proc,'real-game'));
    await fs.symlink(path.join(proc,'real-game'),path.join(proc,'steam-alias'));
    const realSdk = path.join(proc,'real-game','sdk_mods');
    const aliasSdk = path.join(proc,'steam-alias','sdk_mods');
    const aliasSelected = await selectSdkTarget({candidates:[realSdk,aliasSdk],normalize:path.resolve,valid:async()=>true,platform:'linux'});
    assert.equal(aliasSelected.ok,true);
    assert.equal(aliasSelected.path,realSdk); // sdk_mods deliberately absent: parent must canonicalize.
    await fs.mkdir(realSdk);
    const aliasRunning = await selectSdkTarget({explicit:aliasSdk,running:[realSdk],normalize:path.resolve,valid:async()=>true,platform:'linux'});
    assert.equal(aliasRunning.runningMismatch,false);
    if(process.platform === 'linux') {
      assert(!oak.bl4GameRootCandidates({env:{HOME:'/home/test'}}).some(root=>/C:|AppData/.test(root)));
      assert(oak.bl4GameRootCandidates({env:{HOME:'/home/test'}}).some(root=>root.endsWith('/steamapps/common/Borderlands4')));

      const zip = path.join(proc,'runtime.zip');
      execFileSync(process.env.MSBT_PYTHON || 'python3',['-c','import zipfile,sys\nwith zipfile.ZipFile(sys.argv[1],"w") as z:\n z.writestr("OakGame/test", "ok")\n z.writestr("sdk_mods/test", "ok")',zip]);
      const result = await oak.extractZip(zip,path.join(proc,'extracted'));
      assert.equal(await fs.readFile(path.join(result.sdkMods,'test'),'utf8'),'ok');
    }
  } finally { await fs.rm(proc,{recursive:true,force:true}); }
  console.log('PASS Linux Python/Steam paths, Proton processes, unknown-query protection, case-sensitive targets, explicit save root and real ZIP extraction');
})().catch(error=>{console.error(error);process.exitCode=1;});
