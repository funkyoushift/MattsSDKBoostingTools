const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path'),os=require('node:os');
const {createMobileDesktopFiles}=require('./mobile_desktop_files');
(async()=>{
  const temporary=await fs.mkdtemp(path.join(os.tmpdir(),'msbt-phone-files-')),root=path.join(temporary,'saves'),outside=path.join(temporary,'private.yaml');
  await fs.mkdir(root);await fs.writeFile(outside,'private');await fs.writeFile(path.join(root,'character.yaml'),'@UAbCd');await fs.writeFile(path.join(root,'other.exe'),'not a save');
  const files=createMobileDesktopFiles({roots:async()=>[root,root],readFile:async file=>({ok:true,text:await fs.readFile(file,'utf8')})});
  assert.equal((await files.request({operation:'roots'})).roots.length,1);
  assert.deepEqual((await files.request({operation:'list',path:root})).entries.map(row=>row.name),['character.yaml']);
  assert.equal((await files.request({operation:'read',path:path.join(root,'character.yaml')})).text,'@UAbCd');
  await assert.rejects(files.checked(outside),/listed PC save folder/);
  await assert.rejects(files.request({operation:'read',path:path.join(root,'..','private.yaml')}),/listed PC save folder/);
  const link=path.join(root,'escaped');await fs.symlink(temporary,link,'junction');
  await assert.rejects(files.checked(path.join(link,'private.yaml')),/listed PC save folder/);
  console.log('PASS PC save-folder browser, exact file bytes, traversal and junction escape rejection');
})().catch(error=>{console.error(error);process.exitCode=1});
