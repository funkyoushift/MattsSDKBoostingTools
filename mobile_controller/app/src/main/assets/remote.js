(() => {
 const endpoint='https://msbt-afk-relay.screename53.workers.dev';
 const valid=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
 function validate(data){if(data.v!==3||data.relay!==endpoint||!valid(data.room)||!valid(data.token)||!valid(data.key))throw Error('Invalid remote pairing QR.');return {v:3,relay:endpoint,room:data.room,token:data.token,key:data.key,name:'Borderlands 4 Modding Tools Remote AFK'};}
 async function request(route,{payload=null,timeoutMs=40000}={}) {
   const config=validate(state.connection.remote);if(!['/status','/action'].includes(route))throw Error('Remote connection supports AFK Lobby only.');
   const id=crypto.randomUUID(),packet=await msbtRemoteCrypto.seal(config.key,{id,time:Date.now(),route,payload},config.room+':request');
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),Math.max(40000,timeoutMs));
   try {const r=await fetch(`${config.relay}/room/${config.room}/request`,{method:'POST',headers:{Authorization:`Bearer ${config.token}`,'Content-Type':'application/json'},body:JSON.stringify(packet),signal:controller.signal});
     const data=await r.json();if(!r.ok)throw Error(data.message||'Remote connection failed');
     const reply=await msbtRemoteCrypto.open(config.key,data,config.room+':response');if(reply.id!==id)throw Error('Reply does not match this request');return reply.result;
   } catch(error){if(error.name==='AbortError')throw Error('Remote request timed out. Check status before retrying.');throw error;}finally{clearTimeout(timer);}
 }
 let retryTimer=null,attempt=null,paused=false,epoch=0;
 function suspend(){paused=true;++epoch;clearTimeout(retryTimer);retryTimer=null;}
 function scheduleReconnect(){
   clearTimeout(retryTimer);
   if(paused||!state.connection.remote)return;
   retryTimer=setTimeout(()=>void connect({automatic:true}),5000);
 }
 async function connect({automatic=false}={}){
   if(!automatic)paused=false;
   if(paused||!state.connection.remote)return false;
   if(attempt)return attempt;
   clearTimeout(retryTimer);retryTimer=null;
   const active=epoch,connection=state.connection.remote;
   attempt=(async()=>{
     try {const result=await request('/status');
       if(active!==epoch||connection!==state.connection.remote)return false;
       if(!result.ok||result.data?.ok===false)throw Error(result.data?.message||'Game unavailable');
       state.online=true;applyStatus(result.data);startStatusPolling();
       if(!automatic)showScreen('afk');
       $('connectionStatus').textContent='Remote AFK connected. Keep the PC and game running.';return true;
     }catch(error){
       if(active!==epoch||connection!==state.connection.remote)return false;
       state.online=false;state.bridgeOnline=false;updateConnectionChrome();
       $('connectionStatus').textContent=error.message+' — reconnecting automatically.';
       scheduleReconnect();return false;
     }
   })();
   try{return await attempt;}finally{attempt=null;}
 }
 async function pair(data){suspend();stopStatusPolling();const remote=validate(data);state.connection={name:remote.name,address:'Remote AFK',remote};write(STORE.connection,state.connection);if(attempt)await attempt;return connect();}
 window.addEventListener('online',()=>{if(!paused&&state.connection.remote)void connect({automatic:true});});
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible'&&!paused&&state.connection.remote&&!state.online)void connect({automatic:true});});
 window.mobileRemote={validate,request,connect,pair,suspend,scheduleReconnect};
})();
