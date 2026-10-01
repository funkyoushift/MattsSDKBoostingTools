import contract from '../electron_poc/community_folders_contract.js';
import {portal} from './portal.js';
import {identity,allowed} from './auth.js';
import openapi from './openapi.json';
const publicColumns='id,title,creator,description,item_count,oversized_count,digest,status,created_at,reviewed_at';
const json=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const hash=async value=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(x=>x.toString(16).padStart(2,'0')).join('');
const token=request=>request.headers.get('Authorization')?.replace(/^Bearer /,'') || '';
async function body(request,max=contract.MAX_BYTES+65536) {
  if(!request.headers.get('Content-Type')?.startsWith('application/json')) throw Object.assign(Error('Expected JSON.'),{status:415});
  const reader=request.body?.getReader(); if(!reader) throw Error('Missing request body.');
  const chunks=[];let length=0;
  try { while(true) {const {done,value}=await reader.read();if(done)break;length+=value.byteLength;if(length>max) {await reader.cancel();throw Object.assign(Error('Folder exceeds sharing size.'),{status:413});}chunks.push(value);} }
  finally {reader.releaseLock();}
  const bytes=new Uint8Array(length);let at=0;for(const c of chunks){bytes.set(c,at);at+=c.length;}
  return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
function chunks(text) {
  const result=[];let at=0;
  while(at<text.length) {let end=Math.min(text.length,at+131072);if(end<text.length&&/[\uD800-\uDBFF]/.test(text[end-1]))end--;result.push(text.slice(at,end));at=end;}
  return result;
}
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const publicOrigins = new Set(['https://www.funkyoushift.com','https://funkyoushift.com','https://funkyoushift.github.io']);
export default {async fetch(request,env) {
  const path = new URL(request.url).pathname;
  const versioned = path==='/api/v1/folders' || /^\/api\/v1\/folders\/[0-9a-f-]+$/i.test(path);
  if(path==='/api/v1/openapi.json' && request.method==='GET')return Response.json(openapi,{headers:{'Access-Control-Allow-Origin':'*','Cache-Control':'public, max-age=300'}});
  if(versioned && request.method==='OPTIONS')return new Response(null,{status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, OPTIONS','Access-Control-Max-Age':'600'}});
  if(versioned && request.method!=='GET')return json({ok:false,message:'The public API is read-only.'},405);
  let routed=request;
  if(versioned){const url=new URL(request.url);url.pathname=path.slice('/api/v1'.length);routed=new Request(url,request);}
  const response = await handleRequest(routed,env);
  if(versioned && request.method==='GET') {
    const headers=new Headers(response.headers);
    headers.set('Access-Control-Allow-Origin','*');
    return new Response(response.body,{status:response.status,headers});
  }
  // Only anonymous, public folder reads can be accessed by the website.
  if(request.method==='GET' && (path==='/folders' || /^\/folders\/[0-9a-f-]+$/i.test(path)) && publicOrigins.has(request.headers.get('Origin'))) {
    const headers = new Headers(response.headers);
    headers.set('Access-Control-Allow-Origin',request.headers.get('Origin'));
    headers.set('Vary','Origin');
    return new Response(response.body,{status:response.status,headers});
  }
  return response;
}};
async function handleRequest(request,env) {
  try {
    const url=new URL(request.url),path=url.pathname;
    if(path==='/health'&&request.method==='GET') return json({ok:true,service:'MSBT community folders',version:1});
    const limiter=request.method==='GET'||path.startsWith('/portal')||path.startsWith('/review')||path.startsWith('/api/auth/')?env.READ_RATE:env.WRITE_RATE;
    if(limiter && !(await limiter.limit({key:request.headers.get('CF-Connecting-IP') || 'local'})).success) return json({ok:false,message:'Too many requests. Please wait a minute.'},429);
    const portalResult=await portal(request,env,{body,chunks});if(portalResult)return portalResult;
    const person=path.startsWith('/review')?await identity(request,env):null;
    const reviewer=allowed(person,'review');
    if(path.startsWith('/review')&&!reviewer)return json({ok:false,message:'Reviewer sign-in required.'},401);
    if(path.startsWith('/review')&&request.method!=='GET'&&request.headers.get('Origin')!==env.PUBLIC_ORIGIN)return json({ok:false,message:'Invalid request origin.'},403);
    if(request.method==='GET'&&(path==='/folders'||path==='/review')) {
      const q=(url.searchParams.get('q')||'').slice(0,100);
      const offset=Number(url.searchParams.get('offset')||0);
      if(!Number.isInteger(offset)||offset<0||offset>100000)return json({ok:false,message:'Invalid page.'},400);
      const status=reviewer?(url.searchParams.get('status')||'pending'):'approved';
      if(!['pending','approved','rejected','withdrawn'].includes(status))return json({ok:false,message:'Invalid status.'},400);
      const rows=await env.LIBRARY.prepare(`SELECT ${publicColumns}${reviewer?',review_note':''} FROM folders WHERE status=? AND (instr(lower(title),lower(?))>0 OR instr(lower(creator),lower(?))>0) ORDER BY created_at DESC,id LIMIT 26 OFFSET ?`).bind(status,q,q,offset).all();
      return json({ok:true,folders:rows.results.slice(0,25),next:rows.results.length>25?offset+25:null});
    }
    if(path==='/submissions'&&request.method==='POST') {
      const authorization=token(request);if(!/^[a-f0-9]{64}$/.test(authorization))return json({ok:false,message:'Invalid submission key.'},401);
      const input=await body(request);if(!contract.ID.test(input.id))throw Error('Invalid submission ID.');
      const folder=contract.normalize(input.folder),serialized=JSON.stringify(folder),digest=await hash(serialized),owner=await hash(authorization);
      const existing=await env.LIBRARY.prepare('SELECT owner_hash,digest,status FROM folders WHERE id=?').bind(input.id).first();
      if(existing) {
        if(existing.owner_hash!==owner||existing.digest!==digest)return json({ok:false,message:'Submission conflicts with an existing upload.'},409);
        return json({ok:true,id:input.id,status:existing.status,digest});
      }
      const pending=await env.LIBRARY.prepare("SELECT COUNT(*) AS n FROM folders WHERE status='pending'").first();
      if(pending.n>=1000)return json({ok:false,message:'Review queue is full. Please try again later.'},503);
      const commands=[env.LIBRARY.prepare("INSERT INTO folders(id,title,creator,description,item_count,oversized_count,digest,owner_hash,status,created_at) VALUES(?,?,?,?,?,?,?,?,'pending',?)").bind(input.id,folder.title,folder.creator,folder.description,folder.items.length,folder.items.filter(i=>i.serial.length>8192).length,digest,owner,new Date().toISOString())];
      chunks(serialized).forEach((content,i)=>commands.push(env.LIBRARY.prepare('INSERT INTO folder_chunks(folder_id,sequence,content) VALUES(?,?,?)').bind(input.id,i,content)));
      await env.LIBRARY.batch(commands);
      return json({ok:true,id:input.id,status:'pending',digest},201);
    }
    const match=path.match(/^\/(folders|submissions|review|share)\/([0-9a-f-]+)$/i);
    if(match && contract.ID.test(match[2])) {
      const [,kind,id]=match;
      const row=await env.LIBRARY.prepare('SELECT * FROM folders WHERE id=?').bind(id).first();
      const own=kind==='submissions'&&row && /^[a-f0-9]{64}$/.test(token(request)) && row.owner_hash===await hash(token(request));
      if(!row || (kind==='submissions'&&!own) || ((kind==='folders'||kind==='share')&&row.status!=='approved'))return json({ok:false,message:'Folder not available.'},404);
      if(kind==='review'&&request.method==='POST') {
        const input=await body(request,8192);
        if(!['approved','rejected'].includes(input.status))throw Error('Choose approve or reject.');
        if(input.digest!==row.digest)return json({ok:false,message:'Folder changed. Reload it before reviewing.'},409);
        if(row.status==='withdrawn')return json({ok:false,message:'The author withdrew this submission.'},409);
        const note=String(input.note||'').trim();if(note.length>1000)throw Error('Review note is too long.');
        const guard=crypto.randomUUID();
        await env.LIBRARY.batch([
          env.LIBRARY.prepare("INSERT INTO mutation_guard(id,passed) SELECT ?,CASE WHEN EXISTS(SELECT 1 FROM folders WHERE id=? AND digest=? AND status!='withdrawn') AND EXISTS(SELECT 1 FROM team WHERE user_id=? AND role IN ('reviewer','editor','admin','owner')) THEN 1 ELSE 0 END").bind(guard,id,input.digest,person.id),
          env.LIBRARY.prepare('UPDATE folders SET status=?,review_note=?,reviewed_at=? WHERE id=?').bind(input.status,note,new Date().toISOString(),id),
          env.LIBRARY.prepare('INSERT INTO audit(id,actor,action,target,details,created_at) VALUES(?,?,?,?,?,?)').bind(crypto.randomUUID(),person.id,input.status,id,JSON.stringify({digest:row.digest,note}),new Date().toISOString()),
          env.LIBRARY.prepare('DELETE FROM mutation_guard WHERE id=?').bind(guard)
        ]);
        return json({ok:true,status:input.status});
      }
      if(kind==='submissions'&&own&&request.method==='DELETE') {
        await env.LIBRARY.prepare("UPDATE folders SET status='withdrawn' WHERE id=?").bind(id).run();return json({ok:true,status:'withdrawn'});
      }
      if(request.method==='GET') {
        if(kind==='share') return new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${escape(row.title)} — MSBT</title><h1>${escape(row.title)}</h1><p>Submitted by ${escape(row.creator)} · ${row.item_count} items</p><p>${escape(row.description)}</p><p>Open MSBT → Bookmarks → Community folders, then paste this link to preview and import.</p><p><a href="/folders/${id}">Download folder data</a></p>`,{headers:{'Content-Type':'text/html; charset=utf-8','Content-Security-Policy':"default-src 'none'; base-uri 'none'; frame-ancestors 'none'",'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
        const stored=await env.LIBRARY.prepare('SELECT content FROM folder_chunks WHERE folder_id=? ORDER BY sequence').bind(id).all();
        const folder=JSON.parse(stored.results.map(c=>c.content).join(''));
        const {owner_hash,...metadata}=row;
        if(!own&&!reviewer)delete metadata.review_note;
        return json({ok:true,...metadata,folder});
      }
    }
    return json({ok:false,message:'Not found.'},404);
  } catch(error) {
    if(error instanceof SyntaxError || error.status || !String(error.message).match(/D1_|SQLITE|database/i))return json({ok:false,message:String(error.message).slice(0,240)},error.status||400);
    return json({ok:false,message:'The library is temporarily unavailable. Please try again.'},503);
  }
}
