const fs=require('node:fs/promises');
const path=require('node:path');
const crypto=require('node:crypto');
const contract=require('./community_folders_contract');
const DEFAULT_URL='https://msbt-community-library.screename53.workers.dev';
function createCommunityClient({userData,safeStorage,fetcher=fetch,endpoint=DEFAULT_URL}) {
  const url=new URL(endpoint);
  if(url.protocol!=='https:' && !(url.protocol==='http:'&&['127.0.0.1','localhost'].includes(url.hostname)))throw Error('Community folders require HTTPS.');
  const file=path.join(userData,'community-folder-ownership.json');
  let queue=Promise.resolve();
  const exclusive=fn=>{const next=queue.then(fn,fn);queue=next.catch(()=>{});return next;};
  const encrypt=value=>{if(!safeStorage.isEncryptionAvailable())throw Error('Windows secure storage is unavailable. Nothing was submitted.');return safeStorage.encryptString(value).toString('base64');};
  const decrypt=value=>safeStorage.decryptString(Buffer.from(value,'base64'));
  async function load(){try{return JSON.parse(await fs.readFile(file,'utf8'));}catch(e){if(e.code==='ENOENT')return {submissions:[]};throw Error('Cannot read your saved submission keys. Restore the file before submitting again.');}}
  async function save(data){await fs.mkdir(userData,{recursive:true});await fs.writeFile(file+'.tmp',JSON.stringify(data),'utf8');await fs.rename(file+'.tmp',file);}
  function id(value){if(contract.ID.test(String(value)))return value;let link;try{link=new URL(value);}catch{throw Error('Paste a community folder link or ID.');}if(link.origin!==url.origin)throw Error('This is not an MSBT community folder link.');const match=link.pathname.match(/^\/(share|folders)\/([0-9a-f-]+)$/i);if(!match||!contract.ID.test(match[2]))throw Error('Invalid folder link.');return match[2];}
  async function request(route,{method='GET',secret,body}={}) {
    const response=await fetcher(url.origin+route,{method,headers:{...(body?{'Content-Type':'application/json'}:{}),...(secret?{Authorization:'Bearer '+secret}:{})},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(60000),redirect:'error'});
    const reader=response.body.getReader(),parts=[];let bytes=0;
    try{while(true){const {done,value}=await reader.read();if(done)break;bytes+=value.length;if(bytes>contract.MAX_BYTES+262144){await reader.cancel();throw Error('The library returned an oversized response.');}parts.push(Buffer.from(value));}}finally{reader.releaseLock();}
    let data;try{data=JSON.parse(Buffer.concat(parts).toString('utf8'));}catch{throw Error('The online library did not return valid folder data.');}
    if(!response.ok||!data.ok)throw Error(data.message||`Library request failed (${response.status}).`);
    if(data.folder){data.folder=contract.normalize(data.folder);const digest=crypto.createHash('sha256').update(JSON.stringify(data.folder)).digest('hex');if(digest!==data.digest)throw Error('Folder integrity check failed. Nothing was imported.');}
    return data;
  }
  return {endpoint:url.origin,async dispatch(operation,payload={}) {
    if(operation==='list')return request('/folders?'+new URLSearchParams({q:String(payload.q||'').slice(0,100),offset:String(payload.offset||0)}));
    if(operation==='get')return request('/folders/'+id(payload.id));
    if(operation==='info'){const d=await load();return {ok:true,endpoint:url.origin};}
    if(operation==='mine'){const d=await load();return {ok:true,submissions:d.submissions.map(({secret,folder,...row})=>row)};}
    if(operation==='submit')return exclusive(async()=>{
      const folder=contract.normalize(payload.folder),d=await load();
      const digest=crypto.createHash('sha256').update(JSON.stringify(folder)).digest('hex');
      let entry=d.submissions.find(x=>x.digest===digest&&x.status==='sending');
      if(!entry){entry={id:crypto.randomUUID(),title:folder.title,digest,secret:encrypt(crypto.randomBytes(32).toString('hex')),status:'sending',folder};d.submissions.push(entry);await save(d);}
      // Persist the key and exact pending payload first: a lost response is retryable, not a duplicate upload.
      const result=await request('/submissions',{method:'POST',secret:decrypt(entry.secret),body:{id:entry.id,folder:entry.folder}});
      entry.status=result.status;delete entry.folder;await save(d);return result;
    });
    if(operation==='status'||operation==='withdraw'||operation==='retry')return exclusive(async()=>{
      const d=await load(),entry=d.submissions.find(x=>x.id===id(payload.id));if(!entry)throw Error('This PC does not have that submission key.');
      let result;
      if(operation==='retry'){
        if(!entry.folder)throw Error('This submission has already been received. Refresh its status.');
        result=await request('/submissions',{method:'POST',secret:decrypt(entry.secret),body:{id:entry.id,folder:entry.folder}});
      }else result=await request('/submissions/'+entry.id,{method:operation==='withdraw'?'DELETE':'GET',secret:decrypt(entry.secret)});
      entry.status=result.status;entry.review_note=result.review_note||'';delete entry.folder;await save(d);return result;
    });
    throw Error('Unknown community folder action.');
  }};
}
module.exports={createCommunityClient,DEFAULT_URL};
