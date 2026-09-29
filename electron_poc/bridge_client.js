"use strict";
const fs=require('fs/promises'),path=require('path'),os=require('os');
const PORTS=[49774,27874,27875,27876];
const DEFAULT_FILE=path.join(process.env.LOCALAPPDATA||path.join(os.homedir(),'AppData','Local'),'MSBT','bridge-endpoint.json');
function createBridgeClient({endpointFile=DEFAULT_FILE,ports=PORTS,fetchImpl=(...args)=>fetch(...args),probeTimeoutMs=1000}={}){
  let current=null,pending=null,checked=0;
  async function probe(candidate){
    const base=`http://127.0.0.1:${candidate.port}`;
    try{
      const response=await fetchImpl(base+'/bridge-info',{signal:AbortSignal.timeout(probeTimeoutMs),redirect:'error'});
      const data=await response.json();
      if(response.ok&&data.service==='msbt-sdk-bridge'&&data.protocol===1&&data.started===true&&data.port===candidate.port&&/^[a-f0-9]{32}$/.test(data.instance)&&(!candidate.instance||data.instance===candidate.instance))return {base,instance:data.instance};
    }catch{}
    // Backward compatibility is restricted to the historical default endpoint.
    if(candidate.port===49774&&!candidate.instance)try{
      const response=await fetchImpl(base+'/status',{signal:AbortSignal.timeout(probeTimeoutMs),redirect:'error'}),data=await response.json();
      if(response.ok&&data.name==='MattsSDKBoostingTools external bridge'&&data.ok===true&&data.started===true&&data.port===49774)return {base,instance:null};
    }catch{}
    return null;
  }
  async function discover(force=false){
    if(!force&&current&&Date.now()-checked<2000)return current;
    if(pending){await pending;if(!force)return current;}
    pending=(async()=>{
      const candidates=[];
      try{const p=JSON.parse(await fs.readFile(endpointFile,'utf8'));if(p.service==='msbt-sdk-bridge'&&p.protocol===1&&p.host==='127.0.0.1'&&Number.isInteger(p.port)&&ports.includes(p.port)&&/^[a-f0-9]{32}$/.test(p.instance))candidates.push(p);}catch{}
      for(const port of ports)candidates.push({port});
      for(const candidate of candidates){const found=await probe(candidate);if(found){current=found;checked=Date.now();return found;}}
      current=null;return null;
    })();
    try{return await pending;}finally{pending=null;}
  }
  async function request({method='GET',path:route='/status',payload=null,timeoutMs=8000}={}){
    if(!/^\/(?!\/)/.test(route))return {ok:false,status:400,data:{ok:false,message:'Invalid bridge route'}};
    try{
      const endpoint=await discover(method!=='GET');
      if(!endpoint)throw Error(`No verified game bridge found on localhost ports ${ports.join(', ')}. Load Borderlands 4 with the SDK mod; see the SDK log for port reservation/bind failures.`);
      const response=await fetchImpl(endpoint.base+route,{method,redirect:'error',headers:{'Content-Type':'application/json',...(endpoint.instance?{'X-MSBT-Instance':endpoint.instance}:{})},body:payload==null?undefined:JSON.stringify(payload),signal:AbortSignal.timeout(timeoutMs)});
      const data=await response.json();
      if(response.status===401||response.status===409){current=null;checked=0;}
      return {ok:response.ok,status:response.status,data};
    }catch(error){current=null;checked=0;return {ok:false,status:0,data:{ok:false,message:`Game bridge unavailable: ${error.message}. Actions are not automatically retried; check status before retrying.`}};}
  }
  return {request,discover,info:()=>current?.base||'Not connected (automatic discovery)'};
}
module.exports={createBridgeClient,PORTS,DEFAULT_FILE};
