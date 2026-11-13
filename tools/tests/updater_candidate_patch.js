'use strict';
// CI-only diagnostic: append one replacement module to the existing ASAR data.
// Existing file payloads, unpacked metadata and every other entry remain intact.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function patchArchive(archive, source) {
  const old=fs.readFileSync(archive), replacement=fs.readFileSync(source);
  const headerSize=old.readUInt32LE(4), jsonSize=old.readUInt32LE(12);
  if(jsonSize<2 || jsonSize>32*1024*1024 || headerSize+8>old.length)throw Error('Invalid ASAR header');
  const header=JSON.parse(old.subarray(16,16+jsonSize).toString('utf8'));
  const beforeHeader=JSON.parse(JSON.stringify(header));
  const payload=old.subarray(8+headerSize);
  function contents(entry){if(!entry || entry.unpacked || entry.link)throw Error('Expected packed ordinary entry');const start=Number(entry.offset),end=start+entry.size;if(!Number.isSafeInteger(start)||start<0||end>payload.length)throw Error('Invalid entry bounds');return payload.subarray(start,end);}
  const pkg=JSON.parse(contents(header.files['package.json']).toString());
  if(pkg.version!=='2.41.1')throw Error('Diagnostic baseline must remain version 2.41.1');
  const entry=header.files['platform_release_updater.js'];
  const originalModule=contents(entry);
  if(!originalModule.toString().includes('class WindowsReleaseUpdater') || !replacement.toString().includes('class WindowsReleaseUpdater'))throw Error('Expected updater module absent');
  const blockSize=entry.integrity?.blockSize || 4*1024*1024;
  if(!Number.isSafeInteger(blockSize)||blockSize<1||blockSize>64*1024*1024)throw Error('Invalid integrity block size');
  const blocks=[];for(let i=0;i<replacement.length;i+=blockSize)blocks.push(sha(replacement.subarray(i,i+blockSize)));
  entry.offset=String(payload.length);entry.size=replacement.length;
  entry.integrity={algorithm:'SHA256',hash:sha(replacement),blockSize,blocks};
  const oldEntry=beforeHeader.files['platform_release_updater.js'];
  beforeHeader.files['platform_release_updater.js']=JSON.parse(JSON.stringify(entry));
  if(JSON.stringify(beforeHeader)!==JSON.stringify(header))throw Error('Unrelated ASAR metadata changed');
  const json=Buffer.from(JSON.stringify(header)), padded=(json.length+3)&~3;
  const pickle=Buffer.alloc(8+padded);pickle.writeUInt32LE(4+padded,0);pickle.writeUInt32LE(json.length,4);json.copy(pickle,8);
  const size=Buffer.alloc(8);size.writeUInt32LE(4,0);size.writeUInt32LE(pickle.length,4);
  const result=Buffer.concat([size,pickle,payload,replacement]);
  if(!result.subarray(8+pickle.length,8+pickle.length+payload.length).equals(payload))throw Error('Original ASAR payload changed');
  const temporary=archive+'.candidate-handoff.tmp';fs.writeFileSync(temporary,result,{flag:'wx'});fs.renameSync(temporary,archive);
  return {classification:'modified-candidate-handoff',baselineVersion:pkg.version,archiveBeforeSha256:sha(old),archiveAfterSha256:sha(result),originalModuleSha256:sha(originalModule),candidateModuleSha256:sha(replacement),source:path.resolve(source),originalEntry:oldEntry,replacementEntry:entry,preservedOriginalPayloadBytes:payload.length,qualification:'Modified diagnostic client; not an unmodified published-client pass'};
}
module.exports={patchArchive};
if(require.main===module){
  if(process.env.GITHUB_ACTIONS!=='true'||process.env.RUNNER_OS!=='Windows'||!process.env.RUNNER_TEMP)throw Error('Disposable GitHub Windows runner required');
  const [archive,source,output]=process.argv.slice(2);
  const relative=path.relative(path.resolve(process.env.RUNNER_TEMP),path.resolve(archive));
  if(!relative||relative.startsWith('..')||path.isAbsolute(relative))throw Error('Archive must be inside RUNNER_TEMP');
  const result=patchArchive(archive,source);
  result.sourceCommit=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim();
  fs.writeFileSync(output,JSON.stringify(result,null,2));
}
