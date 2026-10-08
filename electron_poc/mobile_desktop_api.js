"use strict";
const crypto=require('node:crypto');
const zlib=require('node:zlib');
const contract=require('./desktop_contract');
const PART_BYTES=1024*1024,MAX_BYTES=128*1024*1024,TTL=10*60*1000;
const valid=value=>typeof value==='string'&&/^[a-f0-9-]{16,64}$/.test(value);
function compactMobileStatus(result,known){
  const hashes=new Set(known.filter(value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value)).slice(0,64)),texts={};
  function visit(value){
    if(typeof value==='string'&&Buffer.byteLength(value)>32768){
      const hash=crypto.createHash('sha256').update(value).digest('hex');
      if(!hashes.has(hash))texts[hash]=value;
      return {__msbt_status_text__:hash};
    }
    if(Array.isArray(value)){
      const text=JSON.stringify(value);
      if(Buffer.byteLength(text)>32768){
        const hash=crypto.createHash('sha256').update(text).digest('hex');if(!hashes.has(hash))texts[hash]=text;
        return {__msbt_status_json__:hash};
      }
      return value.map(visit);
    }
    if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([key,item])=>[key,visit(item)]));
    return value;
  }
  return {...result,data:visit(result.data),mobileStatus:{version:1,texts}};
}
function createMobileDesktopApi({now=()=>Date.now()}={}){
  const handlers=new Map(),special=new Map(),jobs=new Map(),transfers=new Map(),uploads=new Map();
  let sequence=0;const events=[];
  const prune=()=>{for(const map of [jobs,transfers,uploads])for(const [key,row] of map)if(now()-row.time>TTL&&row.state!=='running')map.delete(key);};
  function register(channel,handler){handlers.set(channel,handler);}
  function registerSpecial(method,handler){special.set(method,handler);}
  function publish(channel,payload){if(!Object.values(contract.events).includes(channel))return;events.push({sequence:++sequence,channel,payload});if(events.length>80)events.shift();}
  const eventRows=cursor=>({cursor:sequence,events:events.filter(row=>row.sequence>Number(cursor||0))});
  async function invoke(method,args,client){
    if(!Array.isArray(args)||args.length>8)throw Error('Invalid desktop arguments');
    if(special.has(method))return special.get(method)(args,client);
    const channel=contract.methods[method];
    if(!Object.hasOwn(contract.methods,method)||!handlers.has(channel))throw Error('Unknown desktop tool');
    // Desktop and mobile import previews must not share a staged snapshot.
    const result=await handlers.get(channel)({mobile:true,sender:{id:'mobile:'+client}},...args);
    return method==='bridgeRequest'&&String(args[0]?.method||'GET').toUpperCase()==='GET'&&args[0]?.path==='/status'&&Array.isArray(args[0]?.mobileStatusHashes)
      ?compactMobileStatus(result,args[0].mobileStatusHashes):result;
  }
  function start(call,client){
    if(!call||!valid(call.id)||typeof call.method!=='string')throw Error('Invalid desktop call');
    const key=client+':'+call.id;
    if(jobs.has(key))return jobs.get(key); // A lost reply never repeats a write.
    if(jobs.size>=512)for(const [id,old] of jobs)if(old.acked){jobs.delete(id);if(jobs.size<512)break;}
    if(jobs.size>=512||[...jobs.values()].filter(j=>j.state==='running').length>=24)throw Error('Desktop tools are busy. Wait for the current operations.');
    const row={time:now(),state:'running',method:call.method};jobs.set(key,row);
    row.promise=Promise.resolve().then(()=>invoke(call.method,call.args||[],client)).then(value=>{
      const size=Buffer.byteLength(JSON.stringify(value===undefined?null:value));
      if(size>MAX_BYTES||[...jobs.values()].reduce((sum,job)=>sum+(job.size||0),0)+size>192*1024*1024)throw Error('Finish downloading the previous desktop results first. Check completed operations before retrying.');
      row.state='done';row.value=value===undefined?null:value;row.size=size;row.time=now();
    }).catch(error=>{row.state='error';row.message=String(error.message||error);row.time=now();});
    return row;
  }
  function snapshot(ids,client,cursor){return {...eventRows(cursor),jobs:ids.map(id=>{const row=jobs.get(client+':'+id);return row?{id,state:row.acked?'error':row.state,...(row.state==='done'&&!row.acked?{value:row.value}:{}),...(row.acked?{message:'This operation already completed and its result was received.'}:row.message?{message:row.message}:{})}:{id,state:'error',message:'Desktop operation receipt expired. Check the result before retrying.'};})};}
  function pack(value,client){
    const bytes=Buffer.from(JSON.stringify(value),'utf8');
    if(bytes.length<=PART_BYTES)return value;
    if(bytes.length>MAX_BYTES)throw Error('Desktop result exceeds the transfer limit');
    if(transfers.size>=8)throw Error('Finish downloading the previous desktop results first');
    const compressed=zlib.gzipSync(bytes),useCompression=compressed.length<bytes.length*0.9,wire=useCompression?compressed:bytes;
    const id=crypto.randomBytes(16).toString('hex');transfers.set(client+':'+id,{time:now(),bytes:wire});
    return {transfer:{id,parts:Math.ceil(wire.length/PART_BYTES),bytes:wire.length,decodedBytes:bytes.length,encoding:useCompression?'gzip':'identity',sha256:crypto.createHash('sha256').update(wire).digest('hex')}};
  }
  async function handle(request){
    prune();
    try{
      if(!request||!valid(request.client))throw Error('Invalid phone session');
      const client=request.client;let reply;
      if(Array.isArray(request.ack))for(const id of request.ack.slice(0,24)){
        const row=jobs.get(client+':'+id);
        if(row&&row.state!=='running'){delete row.value;delete row.promise;row.size=0;row.acked=true;}
      }
      if(request.op==='begin'){
        // A newly loaded phone page has no promises from its previous page.
        // Retain write receipts, but release abandoned downloads/results.
        for(const map of [transfers,uploads])for(const key of map.keys())if(key.startsWith(client+':'))map.delete(key);
        for(const [key,row] of jobs)if(key.startsWith(client+':')&&row.state!=='running'){
          delete row.value;delete row.promise;row.size=0;row.acked=true;
        }
        reply=eventRows(request.cursor);
      }else if(request.op==='start'){
        if(!Array.isArray(request.calls)||!request.calls.length||request.calls.length>12)throw Error('Invalid desktop batch');
        const rows=request.calls.map(call=>start(call,client));
        await Promise.race([Promise.all(rows.map(row=>row.promise)),new Promise(resolve=>setTimeout(resolve,120))]);
        reply=snapshot(request.calls.map(call=>call.id),client,request.cursor);
      }else if(request.op==='poll'){
        if(!Array.isArray(request.ids)||request.ids.length>24||request.ids.some(id=>!valid(id)))throw Error('Invalid operation receipts');
        reply=snapshot(request.ids,client,request.cursor);
      }else if(request.op==='part'){
        const row=transfers.get(client+':'+request.id),index=request.index;
        if(!row||!Number.isInteger(index)||index<0||index>=Math.ceil(row.bytes.length/PART_BYTES))throw Error('Desktop transfer expired or invalid');
        row.time=now();reply={base64:row.bytes.subarray(index*PART_BYTES,(index+1)*PART_BYTES).toString('base64')};
      }else if(request.op==='release'){
        transfers.delete(client+':'+request.id);reply={released:true};
      }else if(request.op==='upload'){
        if(!valid(request.id)||!Number.isInteger(request.parts)||request.parts<1||request.parts>128||!Number.isInteger(request.index)||request.index<0||request.index>=request.parts||typeof request.base64!=='string'||request.base64.length>Math.ceil(PART_BYTES/3)*4+4||!/^[a-f0-9]{64}$/.test(request.sha256||''))throw Error('Invalid file transfer');
        const key=client+':'+request.id;
        let row=uploads.get(key);
        if(!row){if(uploads.size>=4)throw Error('File transfer busy');row={time:now(),parts:request.parts,sha256:request.sha256,chunks:new Map()};uploads.set(key,row);}
        if(row.parts!==request.parts||row.sha256!==request.sha256)throw Error('File transfer changed');
        row.chunks.set(request.index,Buffer.from(request.base64,'base64'));row.time=now();reply={received:row.chunks.size};
      }else if(request.op==='uploadedStart'){
        const key=client+':'+request.id,row=uploads.get(key);
        if(!row||row.chunks.size!==row.parts)throw Error('File transfer incomplete');
        const bytes=Buffer.concat(Array.from({length:row.parts},(_,i)=>row.chunks.get(i)));uploads.delete(key);
        if(bytes.length>MAX_BYTES||crypto.createHash('sha256').update(bytes).digest('hex')!==row.sha256)throw Error('File transfer checksum mismatch');
        const call=JSON.parse(bytes.toString('utf8'));start(call,client);reply=snapshot([call.id],client,request.cursor);
      }else throw Error('Unknown desktop request');
      return {ok:true,status:200,data:{ok:true,reply:request.op==='part'?reply:pack(reply,client)}};
    }catch(error){return {ok:false,status:400,data:{ok:false,message:String(error.message||error)}};}
  }
  return {register,registerSpecial,publish,handle,contract};
}
module.exports={createMobileDesktopApi,PART_BYTES,compactMobileStatus};
