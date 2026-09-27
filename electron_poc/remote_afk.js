const crypto=require('node:crypto');
const WebSocket=require('ws');
const envelope=require('./remote_crypto');
const RELAY='https://msbt-afk-relay.screename53.workers.dev';
const ALLOWED=new Set(['afk_lobby_start','afk_lobby_stop','shift_overlay_control']);
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const secret=()=>crypto.randomBytes(32).toString('hex');
function createRemoteAfk({load,save,bridge,relay=RELAY}){
  let config=null,socket=null,timer=null,heartbeat=null,enabled=false,generation=0,lastError='',seen=new Map();
  const info=()=>({enabled,connected:socket?.readyState===WebSocket.OPEN,lastError});
  async function server(route,body){const r=await fetch(`${relay}/room/${config.room}/${route}`,{method:'POST',headers:{Authorization:`Bearer ${config.owner}`,'Content-Type':'application/json'},body:JSON.stringify(body||{}),signal:AbortSignal.timeout(10000)});if(!r.ok)throw Error(`Remote service unavailable (${r.status})`);}
  async function dispatch(request){
    if(!request||typeof request.id!=='string'||request.id.length>64||!Number.isFinite(request.time)||Math.abs(Date.now()-request.time)>45000)throw Error('Expired request');
    for(const [id,time] of seen)if(time<Date.now()-90000)seen.delete(id);
    if(seen.has(request.id))throw Error('Request already processed; refresh status');
    seen.set(request.id,Date.now());
    if(request.route==='/status'){
      const result=await bridge('/status');const d=result.data||{};
      return {ok:result.ok,status:result.status,data:{ok:d.ok,name:d.name,started:d.started,players:d.players,afk_lobby:d.afk_lobby}};
    }
    if(request.route!=='/action'||!ALLOWED.has(request.payload?.action))throw Error('Remote access is limited to AFK Lobby');
    const payload=request.payload.payload||{};
    if(request.payload.action==='shift_overlay_control'&&!['open','close'].includes(payload.mode))throw Error('Unsupported SHiFT command');
    return bridge('/action',{action:request.payload.action,payload,timeout:8});
  }
  function connect(epoch){
    if(!enabled||epoch!==generation)return;
    const active=config;socket=new WebSocket(`${relay.replace('https:','wss:')}/room/${active.room}/host`,{headers:{Authorization:`Bearer ${active.owner}`},maxPayload:3*1024*1024});
    const ws=socket;let lastPong=Date.now();
    ws.on('open',()=>{lastError='';heartbeat=setInterval(()=>{if(Date.now()-lastPong>65000){ws.terminate();return;}if(ws.readyState===WebSocket.OPEN)ws.send('{"type":"ping"}');},25000);});
    ws.on('message',async raw=>{
      try {const m=JSON.parse(raw);if(m.type==='pong'){lastPong=Date.now();return;}
        const req=await envelope.open(active.key,m.packet,active.room+':request');
        if(!enabled||epoch!==generation)return;
        let result;try{result=await dispatch(req);}catch(e){result={ok:false,status:400,data:{ok:false,message:e.message}};}
        const packet=await envelope.seal(active.key,{id:req.id,result},active.room+':response');
        if(enabled&&epoch===generation&&ws.readyState===WebSocket.OPEN)ws.send(JSON.stringify({id:m.id,packet}));
      } catch {lastError='Rejected an invalid remote request';}
    });
    ws.on('unexpected-response',(_request,response)=>{response.resume();if(response.statusCode===401){enabled=false;generation++;lastError='Remote pairing expired. Enable remote AFK again.';}ws.terminate();});
    ws.on('error',()=>{if(enabled)lastError='Remote connection lost; reconnecting';});
    ws.on('close',()=>{clearInterval(heartbeat);if(enabled&&epoch===generation)timer=setTimeout(()=>connect(epoch),5000);});
  }
  async function start(){
    if(enabled)return info();
    config=await load();if(!config){const owner=secret();config={owner,room:hash(owner),phone:secret(),key:secret()};await save(config);}
    await server('register',{phoneHash:hash(config.phone)});enabled=true;connect(++generation);return info();
  }
  async function stop(){enabled=false;generation++;clearTimeout(timer);clearInterval(heartbeat);socket?.close();socket=null;seen.clear();
    if(config){try{await server('revoke');}catch{lastError='Local access disabled; relay unreachable. Old pairing cannot control this PC.';}}
    config=null;await save(null);return info();
  }
  function pairing(){if(!enabled||!config)throw Error('Enable remote AFK first');return {v:3,relay,room:config.room,token:config.phone,key:config.key,name:'MSBT Remote AFK'};}
  function shutdown(){enabled=false;generation++;clearTimeout(timer);clearInterval(heartbeat);socket?.close();}
  return {start,stop,info,pairing,shutdown,dispatch};
}
module.exports={createRemoteAfk,RELAY};
