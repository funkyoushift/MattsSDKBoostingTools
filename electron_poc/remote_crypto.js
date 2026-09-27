/* Shared AES-GCM envelope. Keys never go to the relay. */
(function(root){
  const cryptoApi=typeof module==='object'?require('node:crypto').webcrypto:root.crypto;
  const hexBytes=s=>Uint8Array.from(s.match(/../g)||[],x=>parseInt(x,16));
  const encode=bytes=>{if(typeof Buffer!=='undefined')return Buffer.from(bytes).toString('base64');const data=new Uint8Array(bytes);let value='';for(let i=0;i<data.length;i+=8192)value+=String.fromCharCode(...data.subarray(i,i+8192));return btoa(value);};
  const decode=s=>typeof Buffer!=='undefined'?new Uint8Array(Buffer.from(s,'base64')):Uint8Array.from(atob(s),c=>c.charCodeAt(0));
  async function key(value){if(!/^[a-f0-9]{64}$/.test(value))throw Error('Invalid pairing key');return cryptoApi.subtle.importKey('raw',hexBytes(value),'AES-GCM',false,['encrypt','decrypt']);}
  async function seal(secret,value,context){const iv=cryptoApi.getRandomValues(new Uint8Array(12));const data=await cryptoApi.subtle.encrypt({name:'AES-GCM',iv,additionalData:new TextEncoder().encode(context)},await key(secret),new TextEncoder().encode(JSON.stringify(value)));return {iv:encode(iv),data:encode(new Uint8Array(data))};}
  async function open(secret,packet,context){if(typeof packet?.data!=='string'||packet.data.length>3*1024*1024)throw Error('Invalid encrypted reply');const iv=decode(packet.iv);if(iv.length!==12)throw Error('Invalid nonce');return JSON.parse(new TextDecoder().decode(await cryptoApi.subtle.decrypt({name:'AES-GCM',iv,additionalData:new TextEncoder().encode(context)},await key(secret),decode(packet.data))));}
  const api={seal,open};if(typeof module==='object')module.exports=api;else root.msbtRemoteCrypto=api;
})(globalThis);
