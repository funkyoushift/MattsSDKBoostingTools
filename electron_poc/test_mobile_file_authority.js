// Offline regression: real desktop RPC, preference store and main.js handlers,
// with only synthetic files, a temporary home and canceled desktop dialogs.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const vm = require('node:vm');
const crypto = require('node:crypto');
const {createRequire} = require('node:module');
const prefs = require('./matt_editor_prefs_store');
const {createMobileDesktopApi} = require('./mobile_desktop_api');

test('mobile file authority stays desktop-controlled', async t => {
  const home = await fs.mkdtemp(path.join(os.tmpdir(), 'msbt-file-authority-'));
  const root = path.join(home, 'Documents', 'My Games', 'Bl4', 'Saved', 'SaveGames');
  const outside = path.join(home, 'outside');
  await fs.mkdir(root, {recursive:true}); await fs.mkdir(outside);
  const insideFile = path.join(root, 'character.sav');
  const outsideFile = path.join(outside, 'private.txt');
  await fs.writeFile(insideFile, 'synthetic-save'); await fs.writeFile(outsideFile, 'synthetic-private');
  const prefsPath = prefs.prefsFilePath(home);
  await prefs.writePrefs(prefsPath, {lastSaveFile:insideFile, lastSaveFolder:root});
  const api = createMobileDesktopApi(), handlers = new Map();
  const context = vm.createContext({
    require:createRequire(__filename), Buffer, path, fs,
    os:{homedir:()=>home}, app:{getPath:()=>home},
    dialog:{showOpenDialog:async()=>({canceled:true}), showSaveDialog:async()=>({canceled:true})},
    mobileDesktopApi:api,
    mattEditorPrefsFilePath:prefs.prefsFilePath,
    readMattEditorPrefs:prefs.readPrefs, writeMattEditorPrefs:prefs.writePrefs,
    writeMobileMattEditorPrefs:prefs.writeMobilePrefs,
    normalizePathValue:prefs.normalizePathValue, allowedSaveExtension:prefs.allowedSaveExtension,
    folderFromFile:prefs.folderFromFile, steamIdFromSavePath:prefs.steamIdFromSavePath,
    registerDesktopHandler:(channel,handler)=>{handlers.set(channel,handler); api.register(channel,handler);}
  });
  const source = await fs.readFile(path.join(__dirname,'main.js'),'utf8');
  const begin = source.indexOf('const MATT_EDITOR_SAVE_MAX_BYTES =');
  const end = source.indexOf('registerDesktopHandler("app:loadBl4Catalog"',begin);
  assert(begin >= 0 && end > begin, 'Editor handler extraction must match production source');
  vm.runInContext(source.slice(begin,end),context);
  const client=crypto.randomUUID();
  async function call(method,...args) {
    const result=await api.handle({client,op:'start',calls:[{id:crypto.randomUUID(),method,args}]});
    assert.equal(result.ok,true);
    return result.data.reply.jobs[0];
  }
  const read=file=>call('$pcFiles',{operation:'read',path:file});
  const overwrite=file=>call('mattEditorSaveFile',{overwrite:true,overwritePath:file,base64:Buffer.from('synthetic-updated').toString('base64')});

  await t.test('reject path preference changes and aliases atomically',async()=>{
    for(const [field,alias] of Object.entries({sdkModsPath:'sdk_mods_path',lastSaveFile:'last_save_file',lastSaveFolder:'last_save_folder',lastProfileFile:'last_profile_file',lastProfileFolder:'last_profile_folder',lastExportFolder:'last_export_folder',lastLegitFolder:'last_legit_folder'})) {
      for(const key of [field,alias]) {
        const before=await fs.readFile(prefsPath,'utf8');
        const value=field.endsWith('File')?outsideFile:outside;
        const result=await call('saveMattEditorPrefs',{[key]:value,steamId:'76561198000000000'});
        assert.equal(result.value?.ok,false,key);
        assert.equal(await fs.readFile(prefsPath,'utf8'),before,key+' partially wrote preferences');
        assert.equal((await read(outsideFile)).state,'error',key+' expanded file authority');
        assert.equal((await overwrite(outsideFile)).state,'error',key+' expanded overwrite authority');
        assert.equal(await fs.readFile(outsideFile,'utf8'),'synthetic-private');
      }
    }
  });

  await t.test('accept unchanged desktop paths and valid account IDs',async()=>{
    const data=(await prefs.readPrefs(prefsPath)).data;
    assert.equal((await call('saveMattEditorPrefs',data)).value.ok,true);
    for(const [key,id] of [['steamId','76561198000000000'],['steam_id','0123456789abcdef0123456789abcdef'],['lastSteamEpicId','']]) {
      assert.equal((await call('saveMattEditorPrefs',{[key]:id})).value.ok,true);
      assert.equal((await prefs.readPrefs(prefsPath)).data.steamId,id);
    }
    for(const key of ['steamId','steam_id','lastSteamEpicId']) {
      for(const value of ['../../outside','C:/outside',17,{},'not-an-id']) {
        const before=await fs.readFile(prefsPath,'utf8');
        assert.equal((await call('saveMattEditorPrefs',{[key]:value})).value.ok,false);
        assert.equal(await fs.readFile(prefsPath,'utf8'),before);
      }
    }
  });

  await t.test('legitimate mobile read, reopen and overwrite remain available',async()=>{
    assert.equal((await read(insideFile)).value.base64,Buffer.from('synthetic-save').toString('base64'));
    assert.equal((await call('mattEditorReopenFile','save')).value.ok,true);
    assert.equal((await overwrite(insideFile)).value.ok,true);
    assert.equal(await fs.readFile(insideFile,'utf8'),'synthetic-updated');
    assert.equal((await call('mattEditorSaveFile',{base64:Buffer.from('cancelled').toString('base64')})).value.canceled,true);
    assert.equal(await fs.readFile(outsideFile,'utf8'),'synthetic-private');
  });

  await t.test('traversal and junction escapes cannot read or overwrite',async()=>{
    const traversal=path.join(root,path.relative(root,outsideFile));
    assert.equal((await read(traversal)).state,'error');
    assert.equal((await overwrite(traversal)).state,'error');
    const link=path.join(root,'escape');
    await fs.symlink(outside,link,'junction');
    const escaped=path.join(link,'private.txt');
    assert.equal((await read(escaped)).state,'error');
    assert.equal((await overwrite(escaped)).state,'error');
    assert.equal((await call('saveMattEditorPrefs',{lastSaveFolder:link})).value.ok,false);
    assert.equal(await fs.readFile(outsideFile,'utf8'),'synthetic-private');
  });

  await t.test('account ID never contributes a trusted root',async()=>{
    await prefs.writePrefs(prefsPath,{steamId:path.relative(root,outside)});
    const result=await call('$pcFiles',{operation:'roots'});
    assert(result.value.roots.every(row=>row.path.toLowerCase()===root.toLowerCase()));
    assert.equal((await read(outsideFile)).state,'error');
  });

  await t.test('desktop can still explicitly approve a custom save folder',async()=>{
    const result=await handlers.get('app:saveMattEditorPrefs')({mobile:false},{lastSaveFolder:outside,lastSaveFile:outsideFile,steamId:''});
    assert.equal(result.ok,true);
    assert.equal((await read(outsideFile)).value.ok,true);
    assert.equal((await call('mattEditorReopenFile','save')).value.ok,true);
  });
});
