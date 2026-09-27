(() => {
 const endpoint='https://msbt-afk-relay.screename53.workers.dev';
 const valid=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
 function validate(data){if(data.v!==3||data.relay!==endpoint||!valid(data.room)||!valid(data.token)||!valid(data.key))throw Error('Invalid remote pairing QR.');return {v:3,relay:endpoint,room:data.room,token:data.token,key:data.key,name:'MSBT Remote AFK'};}
 async function request(route,{payload=null,timeoutMs=40000}={}) {
   const config=validate(state.connection.remote);if(!['/status','/action'].includes(route))throw Error('Remote connection supports AFK Lobby only.');
   const id=crypto.randomUUID(),packet=await msbtRemoteCrypto.seal(config.key,{id,time:Date.now(),route,payload},config.room+':request');
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),Math.max(40000,timeoutMs));
   try {const r=await fetch(`${config.relay}/room/${config.room}/request`,{method:'POST',headers:{Authorization:`Bearer ${config.token}`,'Content-Type':'application/json'},body:JSON.stringify(packet),signal:controller.signal});
     const data=await r.json();if(!r.ok)throw Error(data.message||'Remote connection failed');
     const reply=await msbtRemoteCrypto.open(config.key,data,config.room+':response');if(reply.id!==id)throw Error('Reply does not match this request');return reply.result;
   } catch(error){if(error.name==='AbortError')throw Error('Remote request timed out. Check status before retrying.');throw error;}finally{clearTimeout(timer);}
 }
 async function connect(){
   try {const result=await request('/status');if(!result.ok)throw Error(result.data?.message||'Game unavailable');state.online=true;applyStatus(result.data);startStatusPolling();showScreen('afk');$('connectionStatus').textContent='Remote AFK connected. Keep MSBT and the game running on the PC.';return true;}
   catch(error){state.online=false;state.bridgeOnline=false;updateConnectionChrome();$('connectionStatus').textContent=error.message;return false;}
 }
 async function pair(data){stopStatusPolling();const remote=validate(data);state.connection={name:remote.name,address:'Remote AFK',remote};write(STORE.connection,state.connection);return connect();}
 window.mobileRemote={validate,request,connect,pair};
})();
