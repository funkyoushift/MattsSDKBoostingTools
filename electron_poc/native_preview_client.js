"use strict";
// Local trial: call connect() on each inventory refresh. Session scoping avoids
// pretending that an executable version alone identifies all hotfix/locale data.
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
const SCHEMA='native-standalone-widget-v1';
const MAX_RECORD=16*1024*1024;

function createNativePreviewClient({request,capture,cacheDirectory,renderRevision}) {
  if(typeof renderRevision!=='string'||!renderRevision)throw new Error('Renderer revision is required');
  let scope=null,tail=Promise.resolve(),connectionGeneration=0;
  const pending=new Map();
  const action=(name,payload={})=>request({method:'POST',path:'/action',payload:{action:name,payload,timeout:15},timeoutMs:20000});
  async function connect(){
    const generation=++connectionGeneration;
    let status;
    try {status=await action('native_card_preview_status');}
    catch(error){if(generation===connectionGeneration)scope=null;throw error;}
    if(generation!==connectionGeneration)throw new Error('Native preview connection was superseded');
    if(!status?.ok||!status.enabled||status.schema!==SCHEMA||!/^\w{32}$/.test(status.session||'')) {
      scope=null;
      throw new Error(status?.message||'Local native preview is not enabled');
    }
    scope=status.session;return status;
  }
  function get(serial,{image:wantImage=true}={}){
    if(!scope)return Promise.reject(new Error('Connect the native preview before requesting a card'));
    if(typeof serial!=='string'||!serial.startsWith('@U')||serial.length>8192||/[^\x20-\x7e]/.test(serial))
      return Promise.reject(new Error('Expected an exact encoded item serial'));
    const session=scope,key=hash(JSON.stringify([SCHEMA,session,renderRevision,serial]));
    const jobKey=key+(wantImage?':image':':data');
    if(pending.has(jobKey))return pending.get(jobKey);
    if(pending.size>=512)return Promise.reject(new Error('Local preview queue is full'));
    const run=async()=>{
      const assertSession=()=>{if(scope!==session)throw new Error('Native preview session changed');};
      assertSession();
      const file=path.join(cacheDirectory,key+'.json');
      // Game output does not change when only our image layout/assets change.
      const widgetFile=path.join(cacheDirectory,'widgets',hash(JSON.stringify([SCHEMA,session,serial]))+'.json');
      let record=null;
      if(!wantImage){
        try {
          if((await fs.stat(widgetFile)).size<=MAX_RECORD){
            const saved=JSON.parse(await fs.readFile(widgetFile,'utf8'));assertSession();
            if(saved.schema===SCHEMA&&saved.session===session&&saved.serial===serial&&saved.widget)
              return {...saved,renderRevision,cached:true};
          }
        } catch(error){if(!['ENOENT','SyntaxError'].includes(error.code||error.name))throw error;}
      }
      try {
        const stat=await fs.stat(file);
        if(stat.size<=MAX_RECORD){
          const cached=JSON.parse(await fs.readFile(file,'utf8'));assertSession();
          if(cached.schema===SCHEMA&&cached.session===session&&cached.serial===serial&&cached.renderRevision===renderRevision&&cached.widget){
            record=cached;
            if(!wantImage){const {image,...data}=cached;return {...data,cached:true};}
            if(cached.image?.ok&&typeof cached.image.base64==='string')return {...cached,cached:true};
          }
        }
      } catch(error){if(!['ENOENT','SyntaxError'].includes(error.code||error.name))throw error;}
      if(!record){
        try {
          if((await fs.stat(widgetFile)).size<=MAX_RECORD){
            const saved=JSON.parse(await fs.readFile(widgetFile,'utf8'));assertSession();
            if(saved.schema===SCHEMA&&saved.session===session&&saved.serial===serial&&saved.widget)
              record={...saved,renderRevision};
          }
        } catch(error){if(!['ENOENT','SyntaxError'].includes(error.code||error.name))throw error;}
      }
      if(!record){
        const reply=await action('native_card_preview',{serial});assertSession();
        if(!reply?.ok||reply.schema!==SCHEMA||reply.session!==session||reply.serial!==serial||!reply.widget)
          throw new Error(reply?.message||'Native preview response does not match this request');
        record={schema:SCHEMA,session,serial,renderRevision,widget:reply.widget};
      }
      const widgetData=JSON.stringify({schema:SCHEMA,session,serial,widget:record.widget});
      if(Buffer.byteLength(widgetData)>MAX_RECORD)throw new Error('Native card data is too large');
      await fs.mkdir(path.dirname(widgetFile),{recursive:true});
      const widgetTemporary=widgetFile+'.'+crypto.randomUUID()+'.tmp';
      try {await fs.writeFile(widgetTemporary,widgetData,{flag:'wx'});assertSession();await fs.rename(widgetTemporary,widgetFile);}
      finally {await fs.unlink(widgetTemporary).catch(error=>{if(error.code!=='ENOENT')throw error;});}
      if(wantImage){
        const image=await capture(record.widget);assertSession();
        if(!image?.ok||typeof image.base64!=='string')throw new Error('Native card image capture failed');
        record.image=image;
      }
      const data=JSON.stringify(record);
      if(Buffer.byteLength(data)>MAX_RECORD)throw new Error('Native card cache entry is too large');
      await fs.mkdir(cacheDirectory,{recursive:true});
      const temporary=file+'.'+crypto.randomUUID()+'.tmp';
      try {await fs.writeFile(temporary,data,{flag:'wx'});assertSession();await fs.rename(temporary,file);}
      finally {await fs.unlink(temporary).catch(error=>{if(error.code!=='ENOENT')throw error;});}
      if(record.image?.ok){
        const index=path.join(cacheDirectory,'snapshots',hash(JSON.stringify([SCHEMA,renderRevision,serial]))+'.json');
        await fs.mkdir(path.dirname(index),{recursive:true});
        const temp=index+'.'+crypto.randomUUID()+'.tmp';
        try{await fs.writeFile(temp,JSON.stringify({key}),{flag:'wx'});assertSession();await fs.rename(temp,index);}
        finally{await fs.unlink(temp).catch(error=>{if(error.code!=='ENOENT')throw error;});}
      }
      return {...record,cached:false};
    };
    const job=tail.then(run,run);
    tail=job.catch(()=>{});
    pending.set(jobKey,job);
    job.then(()=>pending.delete(jobKey),()=>pending.delete(jobKey));
    return job;
  }
  async function snapshot(serial){
    if(typeof serial!=='string'||!serial.startsWith('@U')||serial.length>8192)return null;
    try{
      const index=path.join(cacheDirectory,'snapshots',hash(JSON.stringify([SCHEMA,renderRevision,serial]))+'.json');
      if((await fs.stat(index)).size>256)return null;
      const {key}=JSON.parse(await fs.readFile(index,'utf8'));if(!/^[a-f0-9]{64}$/.test(key))return null;
      const file=path.join(cacheDirectory,key+'.json');if((await fs.stat(file)).size>MAX_RECORD)return null;
      const record=JSON.parse(await fs.readFile(file,'utf8'));
      if(record.serial!==serial||record.schema!==SCHEMA||record.renderRevision!==renderRevision||!record.widget||!record.image?.ok)return null;
      return {...record,cached:true,offline:true};
    }catch{return null;}
  }
  return {connect,get,snapshot};
}
module.exports={createNativePreviewClient};
