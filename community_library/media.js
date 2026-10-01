import {identity,allowed} from './auth.js';
const json=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const hash=async data=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',typeof data==='string'?new TextEncoder().encode(data):data))].map(x=>x.toString(16).padStart(2,'0')).join('');
export const imageList=async(db,id)=>(await db.prepare('SELECT id,serial_hash,content_hash FROM item_images WHERE folder_id=? ORDER BY id').bind(id).all()).results;
function jpeg(bytes){if(bytes.length>524288||bytes[0]!==255||bytes[1]!==216)throw Error('Use a JPEG screenshot up to 512 KB.');let at=2,dimensions=false;while(at+4<bytes.length){if(bytes[at++]!==255)throw Error('Invalid JPEG image.');let marker=bytes[at++];while(marker===255)marker=bytes[at++];if(marker===218||marker===217)break;if(marker===216||marker===1||(marker>=208&&marker<=215))continue;const length=(bytes[at]<<8)|bytes[at+1];if(length<2||at+length>bytes.length)throw Error('Invalid JPEG image.');if([192,193,194].includes(marker)){const h=(bytes[at+3]<<8)|bytes[at+4],w=(bytes[at+5]<<8)|bytes[at+6];if(!w||!h||w>2000||h>2000)throw Error('Screenshot dimensions exceed 2000 pixels.');dimensions=true;}at+=length;}if(!dimensions)throw Error('Invalid JPEG screenshot.');}
export async function media(request,env,{body,contract}){
 const path=new URL(request.url).pathname,read=path.match(/^\/images\/([0-9a-f-]+)$/i),upload=path.match(/^\/submissions\/([0-9a-f-]+)\/images$/i);
 if(!read&&!upload)return null;
 const key=request.headers.get('Authorization')?.replace(/^Bearer /,'')||'';
 const person=await identity(request,env);
 if(read&&request.method==='GET'){
  const row=await env.LIBRARY.prepare('SELECT i.content,f.status,f.owner_hash FROM item_images i JOIN folders f ON f.id=i.folder_id WHERE i.id=?').bind(read[1]).first();
  const own=row&&/^[a-f0-9]{64}$/.test(key)&&row.owner_hash===await hash(key);
  if(!row||(row.status!=='approved'&&!own&&!allowed(person,'review')))return json({ok:false,message:'Screenshot not available.'},404);
  return new Response(new Uint8Array(row.content),{headers:{'Content-Type':'image/jpeg','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; sandbox"}});
 }
 if(!upload||request.method!=='POST')return json({ok:false,message:'Unsupported image action.'},405);
 const id=upload[1],row=await env.LIBRARY.prepare('SELECT * FROM folders WHERE id=?').bind(id).first();
 const own=row&&/^[a-f0-9]{64}$/.test(key)&&row.owner_hash===await hash(key);
 if(!row||(!own&&!allowed(person,'edit')))return json({ok:false,message:'Screenshot access denied.'},403);
 if(!own&&request.headers.get('Origin')!==env.PUBLIC_ORIGIN)return json({ok:false,message:'Invalid request origin.'},403);
 if(row.status==='withdrawn')return json({ok:false,message:'This loadout was withdrawn.'},409);
 const input=await body(request,15*1024*1024);
 if(input.digest!==row.digest)return json({ok:false,message:'Loadout changed. Reload before changing screenshots.'},409);
 if(!Array.isArray(input.images)||input.images.length>20||!Array.isArray(input.remove||[])||(input.remove||[]).length>20)throw Error('Choose up to 20 item screenshots per loadout.');
 const stored=await env.LIBRARY.prepare('SELECT content FROM folder_chunks WHERE folder_id=? ORDER BY sequence').bind(id).all();const folder=JSON.parse(stored.results.map(c=>c.content).join(''));
 const serials=new Set(folder.items.map(i=>i.serial)),old=await imageList(env.LIBRARY,id),images=[],seen=new Set();
 for(const image of input.images){if(!contract.ID.test(image.id)||!serials.has(image.serial)||typeof image.data!=='string'||image.data.length>699052)throw Error('Screenshot must belong to an exact item code in this loadout.');const serial_hash=await hash(image.serial);if(seen.has(serial_hash))throw Error('Choose one screenshot per exact item code.');seen.add(serial_hash);const bytes=Uint8Array.from(atob(image.data),c=>c.charCodeAt(0));jpeg(bytes);const content_hash=await hash(bytes);const existing=await env.LIBRARY.prepare('SELECT folder_id,serial_hash,content_hash FROM item_images WHERE id=?').bind(image.id).first();if(existing&&(existing.folder_id!==id||existing.serial_hash!==serial_hash||existing.content_hash!==content_hash))throw Error('Screenshot ID conflicts with another image.');images.push({...image,serial_hash,content_hash,bytes});}
 const remove=input.remove||[];if(remove.some(x=>!old.some(y=>y.id===x)))throw Error('Screenshot to remove is not in this loadout.');
 if(images.length&&remove.length===0&&images.every(x=>old.some(y=>y.id===x.id&&y.content_hash===x.content_hash)))return json({ok:true,media_revision:row.media_revision,images:old});
 if(input.media_revision!==row.media_revision)return json({ok:false,message:'Screenshots changed. Reload before editing.'},409);
 if(old.filter(x=>!remove.includes(x.id)&&!seen.has(x.serial_hash)).length+images.length>20)throw Error('Maximum 20 screenshots per loadout.');
 const guard=crypto.randomUUID(),commands=[env.LIBRARY.prepare("INSERT INTO mutation_guard(id,passed) SELECT ?,CASE WHEN EXISTS(SELECT 1 FROM folders WHERE id=? AND digest=? AND media_revision=? AND status!='withdrawn') AND (?=1 OR EXISTS(SELECT 1 FROM team WHERE user_id=? AND role IN ('editor','admin','owner'))) THEN 1 ELSE 0 END").bind(guard,id,row.digest,row.media_revision,own?1:0,person?.id||'')];
 for(const imageId of remove)commands.push(env.LIBRARY.prepare('DELETE FROM item_images WHERE folder_id=? AND id=?').bind(id,imageId));
 for(const image of images){commands.push(env.LIBRARY.prepare('DELETE FROM item_images WHERE folder_id=? AND serial_hash=?').bind(id,image.serial_hash),env.LIBRARY.prepare('INSERT INTO item_images(id,folder_id,serial_hash,content_hash,content,created_at) VALUES(?,?,?,?,?,?)').bind(image.id,id,image.serial_hash,image.content_hash,image.bytes.buffer,new Date().toISOString()));}
 commands.push(env.LIBRARY.prepare("UPDATE folders SET media_revision=media_revision+1,status='pending',reviewed_at=NULL,review_note='Screenshots changed; needs approval' WHERE id=?").bind(id),env.LIBRARY.prepare('INSERT INTO audit(id,actor,action,target,details,created_at) VALUES(?,?,?,?,?,?)').bind(crypto.randomUUID(),own?'submission-owner':person.id,'screenshots',id,JSON.stringify({added:images.map(x=>x.id),removed:remove}),new Date().toISOString()),env.LIBRARY.prepare('DELETE FROM mutation_guard WHERE id=?').bind(guard));
 await env.LIBRARY.batch(commands);return json({ok:true,media_revision:row.media_revision+1,images:await imageList(env.LIBRARY,id)});
}
