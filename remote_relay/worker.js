const valid = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const digest = async value => [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(x=>x.toString(16).padStart(2,'0')).join('');
const headers = {'Content-Type':'application/json','Cache-Control':'no-store','Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'Authorization, Content-Type','Access-Control-Allow-Methods':'POST, OPTIONS'};
const reply=(status,message)=>new Response(JSON.stringify({ok:false,message}),{status,headers});
async function body(request) {
  const reader=request.body?.getReader();if(!reader)throw Error('Missing body');
  const chunks=[];let size=0;
  while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>2*1024*1024){await reader.cancel();throw Error('Too large');}chunks.push(value);}
  const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}return JSON.parse(new TextDecoder().decode(bytes));
}
export default {async fetch(request,env) {
  const url=new URL(request.url);
  if(url.pathname==='/health')return new Response('MSBT AFK relay');
  if(request.method==='OPTIONS')return new Response(null,{status:204,headers});
  if(!(await env.RATE.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'})).success)return reply(429,'Too many requests');
  const match=/^\/room\/([a-f0-9]{64})\/(register|host|request|revoke)$/.exec(url.pathname);
  if(!match)return reply(404,'Not found');
  return env.ROOMS.get(env.ROOMS.idFromName(match[1])).fetch(request);
}};
export class AfkRoom {
  constructor(ctx){this.ctx=ctx;this.pending=new Map();this.rate=[];}
  async fetch(request) {
    const parts=new URL(request.url).pathname.split('/');const room=parts[2],route=parts[3];
    let input=null;
    if(request.method==='POST'){try{input=await body(request);}catch{return reply(400,'Invalid request body');}}
    const token=(request.headers.get('Authorization')||'').replace(/^Bearer /,'');
    if(!valid(token))return reply(401,'Not authorized');
    const hash=await digest(token);
    if(route==='register'||route==='host'||route==='revoke') {
      if(hash!==room)return reply(401,'Not authorized');
    } else {
      if(hash!==await this.ctx.storage.get('phone'))return reply(401,'Pairing expired or revoked');
    }
    if(route==='register'&&request.method==='POST') {
      const config=input;
      if(!config||!valid(config.phoneHash))return reply(400,'Invalid registration');
      const old=await this.ctx.storage.get('phone');
      if(old&&old!==config.phoneHash)return reply(409,'Create a new pairing');
      await this.ctx.storage.put('phone',config.phoneHash);
      await this.ctx.storage.setAlarm(Date.now()+7*86400000);
      return new Response(JSON.stringify({ok:true}),{headers});
    }
    if(route==='revoke'&&request.method==='POST'){await this.alarm();return new Response(JSON.stringify({ok:true}),{headers});}
    if(route==='host'&&request.headers.get('Upgrade')==='websocket') {
      if(!await this.ctx.storage.get('phone'))return reply(401,'Register first');
      for(const socket of this.ctx.getWebSockets('host'))socket.close(1000,'Replaced');
      const pair=new WebSocketPair();this.ctx.acceptWebSocket(pair[1],['host']);
      return new Response(null,{status:101,webSocket:pair[0]});
    }
    if(route!=='request'||request.method!=='POST')return reply(405,'Method not allowed');
    const now=Date.now();this.rate=this.rate.filter(t=>t>now-60000);
    if(this.rate.length>=60||this.pending.size>=4)return reply(429,'Too many requests');
    this.rate.push(now);
    const host=this.ctx.getWebSockets('host')[0];if(!host)return reply(503,'PC is offline. Keep MSBT open.');
    const packet=input;
    // Payload is encrypted by the phone. Only the paired desktop can decrypt it.
    if(!packet||typeof packet.iv!=='string'||typeof packet.data!=='string')return reply(400,'Invalid envelope');
    const id=crypto.randomUUID();
    return new Promise(resolve=>{
      const timer=setTimeout(()=>{this.pending.delete(id);resolve(reply(504,'PC did not reply. Check status before retrying commands.'));},35000);
      this.pending.set(id,{resolve,timer});
      try{host.send(JSON.stringify({id,packet}));}catch{clearTimeout(timer);this.pending.delete(id);resolve(reply(503,'PC disconnected'));}
    });
  }
  webSocketMessage(ws,message) {
    if(typeof message!=='string'||message.length>3*1024*1024){ws.close(1009,'Too large');return;}
    let data;try{data=JSON.parse(message);}catch{return;}
    if(data.type==='ping'){ws.send('{"type":"pong"}');return;}
    const pending=this.pending.get(data.id);if(!pending)return;
    if(!data.packet||typeof data.packet.iv!=='string'||typeof data.packet.data!=='string')return;
    clearTimeout(pending.timer);this.pending.delete(data.id);
    pending.resolve(new Response(JSON.stringify(data.packet),{headers}));
  }
  webSocketClose(ws,code,reason){for(const p of this.pending.values()){clearTimeout(p.timer);p.resolve(reply(503,'PC disconnected'));}this.pending.clear();}
  webSocketError(ws){this.webSocketClose(ws,1011,'Connection lost');}
  async alarm(){for(const socket of this.ctx.getWebSockets())socket.close(1000,'Pairing expired');await this.ctx.storage.deleteAll();}
}
