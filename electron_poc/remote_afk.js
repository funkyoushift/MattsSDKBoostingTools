const crypto=require('node:crypto');
const WebSocket=require('ws');
const envelope=require('./remote_crypto');
const RELAY='https://msbt-afk-relay.screename53.workers.dev';
const ALLOWED=new Set(['afk_lobby_start','afk_lobby_stop','shift_overlay_control']);
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const secret=()=>crypto.randomBytes(32).toString('hex');
const valid=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
function createRemoteAfk({load,save,bridge,relay=RELAY,onChange=()=>{},fetchImpl=(...args)=>fetch(...args),
  retryMs=5000,heartbeatMs=25000,heartbeatTimeoutMs=65000,renewMs=6*60*60*1000}) {
  let config=null,socket=null,timer=null,heartbeat=null,renewal=null,pendingFetch=null;
  let enabled=false,generation=0,intent=0,lastError='',operation=Promise.resolve();
  const seen=new Map();
  const info=()=>({enabled,connected:socket?.readyState===WebSocket.OPEN,lastError});
  const changed=()=>{try{onChange(info());}catch(error){lastError=error.message;}};
  const serial=fn=>(operation=operation.then(fn,fn));
  async function server(active,route,body,signal){
    const r=await fetchImpl(`${relay}/room/${active.room}/${route}`,{method:'POST',headers:{Authorization:`Bearer ${active.owner}`,'Content-Type':'application/json'},body:JSON.stringify(body||{}),signal:signal||AbortSignal.timeout(10000)});
    if(!r.ok)throw Error(`Remote service unavailable (${r.status}); retrying automatically`);
  }
  async function dispatch(request){
    if(!request||typeof request.id!=='string'||request.id.length>64||!Number.isFinite(request.time)||Math.abs(Date.now()-request.time)>45000)throw Error('Expired request');
    for(const [id,time] of seen)if(time<Date.now()-90000)seen.delete(id);
    if(seen.has(request.id))throw Error('Request already processed; refresh status');
    seen.set(request.id,Date.now());
    if(request.route==='/status'){
      const result=await bridge('/status'),d=result.data||{};
      return {ok:result.ok,status:result.status,data:{ok:d.ok,name:d.name,started:d.started,message:d.message,players:d.players,afk_lobby:d.afk_lobby}};
    }
    if(request.route!=='/action'||!ALLOWED.has(request.payload?.action))throw Error('Remote access is limited to AFK Lobby');
    const payload=request.payload.payload||{};
    if(request.payload.action==='shift_overlay_control'&&!['open','close'].includes(payload.mode))throw Error('Unsupported SHiFT command');
    return bridge('/action',{action:request.payload.action,payload,timeout:8});
  }
  function cancelConnection(){
    clearTimeout(timer);clearInterval(heartbeat);clearTimeout(renewal);
    timer=heartbeat=renewal=null;pendingFetch?.abort();pendingFetch=null;
    const old=socket;socket=null;old?.terminate();
  }
  function retry(epoch){if(enabled&&epoch===generation){clearTimeout(timer);timer=setTimeout(()=>void connect(epoch),retryMs);}}
  async function connect(epoch){
    if(!enabled||epoch!==generation)return;
    const active=config;
    try{
      const controller=new AbortController();pendingFetch=controller;
      const deadline=setTimeout(()=>controller.abort(),10000);
      try{await server(active,'register',{phoneHash:hash(active.phone)},controller.signal);}
      finally{clearTimeout(deadline);if(pendingFetch===controller)pendingFetch=null;}
      if(!enabled||epoch!==generation)return;
      // Re-register the SAME credentials before reconnecting, including after lease expiry.
      const url=new URL(`/room/${active.room}/host`,relay);url.protocol=url.protocol==='https:'?'wss:':'ws:';
      const ws=new WebSocket(url.toString(),{headers:{Authorization:`Bearer ${active.owner}`},maxPayload:3*1024*1024,handshakeTimeout:10000});
      socket=ws;let lastPong=Date.now();
      ws.on('open',()=>{
        if(!enabled||epoch!==generation){ws.terminate();return;}
        lastError='';changed();
        heartbeat=setInterval(()=>{if(Date.now()-lastPong>heartbeatTimeoutMs){ws.terminate();return;}if(ws.readyState===WebSocket.OPEN)ws.send('{"type":"ping"}');},heartbeatMs);
        renewal=setTimeout(reconnect,renewMs); // Renew before the relay's seven-day expiry.
      });
      ws.on('message',async raw=>{
        if(!enabled||epoch!==generation)return;
        try{const m=JSON.parse(raw);if(m.type==='pong'){lastPong=Date.now();return;}
          const req=await envelope.open(active.key,m.packet,active.room+':request');
          if(!enabled||epoch!==generation)return;
          let result;try{result=await dispatch(req);}catch(e){result={ok:false,status:400,data:{ok:false,message:e.message}};}
          const packet=await envelope.seal(active.key,{id:req.id,result},active.room+':response');
          if(enabled&&epoch===generation&&ws.readyState===WebSocket.OPEN)ws.send(JSON.stringify({id:m.id,packet}));
        }catch{lastError='Rejected an invalid remote request';changed();}
      });
      ws.on('unexpected-response',(_req,response)=>{response.resume();ws.terminate();});
      ws.on('error',()=>{if(enabled&&epoch===generation){lastError='Remote connection lost; reconnecting automatically';changed();}});
      ws.on('close',()=>{if(epoch!==generation)return;clearInterval(heartbeat);clearTimeout(renewal);socket=null;changed();retry(epoch);});
    }catch(error){if(enabled&&epoch===generation){lastError=error.message;changed();retry(epoch);}}
  }
  function reconnect(){if(!enabled)return;++generation;cancelConnection();void connect(generation);}
  function start({restoreOnly=false}={}){const requested=intent;return serial(async()=>{
    if(requested!==intent)return info();
    if(enabled)return info();config=await load();
    if(requested!==intent||(!config&&restoreOnly))return info();
    if(!config){const owner=secret();config={owner,room:hash(owner),phone:secret(),key:secret()};await save(config);}
    if(!['owner','room','phone','key'].every(k=>valid(config[k]))||hash(config.owner)!==config.room)throw Error('Saved pairing is invalid. Disable remote access, then enable it to pair again.');
    if(requested!==intent)return info();
    enabled=true;lastError='';changed();reconnect();return info();
  });}
  function stop(){
    ++intent;enabled=false;++generation;cancelConnection();changed();
    return serial(async()=>{
      enabled=false;++generation;cancelConnection();
      const old=config||await load();config=null;seen.clear();await save(null);lastError='';changed();
      if(old)try{await server(old,'revoke');}catch{lastError='Access disabled on this PC. Relay unavailable; the old pairing cannot control this PC.';changed();}
      return info();
    });
  }
  function pairing(){if(!enabled||!config)throw Error('Enable remote AFK first');return {v:3,relay,room:config.room,token:config.phone,key:config.key,name:'Borderlands 4 Modding Tools Remote AFK'};}
  function shutdown(){++intent;enabled=false;++generation;cancelConnection();}
  return {start,restore:()=>start({restoreOnly:true}),stop,info,pairing,shutdown,reconnect,dispatch};
}
module.exports={createRemoteAfk,RELAY};
