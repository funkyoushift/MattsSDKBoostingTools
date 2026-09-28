import {createAuth,identity,allowed} from './auth.js';
import contract from '../electron_poc/community_folders_contract.js';
import page from './portal.html';
const json=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const hash=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(x=>x.toString(16).padStart(2,'0')).join('');
export async function portal(request,env,{body,chunks}) {
  const url=new URL(request.url),route=url.pathname;
  if(route.startsWith('/api/auth/'))return createAuth(env).handler(request);
  if(route==='/portal') {const nonce=crypto.randomUUID();return new Response(page.replace('SCRIPT_NONCE',nonce),{headers:{'Content-Type':'text/html;charset=utf-8','Cache-Control':'no-store','Content-Security-Policy':`default-src 'none'; script-src 'nonce-${nonce}'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'`}});}
  if(!route.startsWith('/portal/api/'))return null;
  const person=await identity(request,env);
  if(!person)return json({ok:false,message:'Sign in to continue.'},401);
  if(request.method!=='GET'&&request.headers.get('Origin')!==env.PUBLIC_ORIGIN)return json({ok:false,message:'Invalid request origin.'},403);
  if(route==='/portal/api/me')return json({ok:true,person});
  if(!allowed(person,'review'))return json({ok:false,message:'Your account has no team access yet. Ask the owner to assign your account ID a role.'},403);
  const audit=(action,target,details)=>env.LIBRARY.prepare('INSERT INTO audit(id,actor,action,target,details,created_at) VALUES(?,?,?,?,?,?)').bind(crypto.randomUUID(),person.id,action,target,JSON.stringify(details),new Date().toISOString());
  // Each mutation checks the live permission within the same atomic D1 batch.
  const gate=(action)=>{const roles=Object.entries({review:['reviewer','editor','admin','owner'],edit:['editor','admin','owner'],delete:['admin','owner'],team:['owner']}).find(([k])=>k===action)[1];const id=crypto.randomUUID();return {id,statement:env.LIBRARY.prepare(`INSERT INTO mutation_guard(id,passed) SELECT ?,CASE WHEN EXISTS(SELECT 1 FROM team WHERE user_id=? AND role IN (${roles.map(()=>'?').join(',')})) THEN 1 ELSE 0 END`).bind(id,person.id,...roles)};};
  if(route==='/portal/api/team') {
    if(!allowed(person,'team'))return json({ok:false,message:'Only the owner can manage team access.'},403);
    if(request.method==='GET')return json({ok:true,users:(await env.LIBRARY.prepare('SELECT u.id,u.name,u.email,COALESCE(t.role,\'member\') role FROM user u LEFT JOIN team t ON t.user_id=u.id ORDER BY u.createdAt DESC LIMIT 200').all()).results});
    if(request.method==='POST') {
      const input=await body(request,8192);
      if(!['member','reviewer','editor','admin'].includes(input.role)||typeof input.id!=='string')return json({ok:false,message:'Invalid role or account.'},400);
      const target=await env.LIBRARY.prepare('SELECT u.id,t.role FROM user u LEFT JOIN team t ON t.user_id=u.id WHERE u.id=?').bind(input.id).first();
      if(!target||target.role==='owner'||input.id===person.id)return json({ok:false,message:'The owner account cannot be changed here.'},409);
      const guard=gate('team');
      await env.LIBRARY.batch([guard.statement,env.LIBRARY.prepare('DELETE FROM team WHERE user_id=? AND role!=\'owner\'').bind(input.id),...(input.role==='member'?[]:[env.LIBRARY.prepare('INSERT INTO team(user_id,role) VALUES(?,?)').bind(input.id,input.role)]),env.LIBRARY.prepare('DELETE FROM session WHERE userId=?').bind(input.id),audit('role',input.id,{role:input.role}),env.LIBRARY.prepare('DELETE FROM mutation_guard WHERE id=?').bind(guard.id)]);
      return json({ok:true});
    }
  }
  if(route==='/portal/api/audit'&&request.method==='GET')return json({ok:true,events:(await env.LIBRARY.prepare('SELECT * FROM audit ORDER BY created_at DESC LIMIT 100').all()).results});
  const match=route.match(/^\/portal\/api\/folders\/([0-9a-f-]+)$/i);
  if(match&&contract.ID.test(match[1])) {
    const id=match[1],input=await body(request),action=request.method==='DELETE'?'delete':'edit';
    if(!allowed(person,action))return json({ok:false,message:'Your role does not allow this action.'},403);
    if(!['PUT','DELETE'].includes(request.method))return json({ok:false,message:'Unsupported action.'},405);
    const row=await env.LIBRARY.prepare('SELECT * FROM folders WHERE id=?').bind(id).first();
    if(!row||row.digest!==input.digest)return json({ok:false,message:'Folder changed. Reload it before editing.'},409);
    if(row.status==='withdrawn'&&action!=='delete')return json({ok:false,message:'The author withdrew this folder.'},409);
    const guard=gate(action),versionGuard=crypto.randomUUID();
    const commands=[guard.statement,env.LIBRARY.prepare("INSERT INTO mutation_guard(id,passed) SELECT ?,CASE WHEN EXISTS(SELECT 1 FROM folders WHERE id=? AND digest=? AND (status!='withdrawn' OR ?='delete')) THEN 1 ELSE 0 END").bind(versionGuard,id,input.digest,action)];
    if(action==='delete') {
      commands.push(env.LIBRARY.prepare('DELETE FROM folder_chunks WHERE folder_id=?').bind(id),env.LIBRARY.prepare('DELETE FROM folders WHERE id=?').bind(id));
    } else {
      const folder=contract.normalize(input.folder),text=JSON.stringify(folder),digest=await hash(text);
      commands.push(env.LIBRARY.prepare("UPDATE folders SET title=?,creator=?,description=?,item_count=?,oversized_count=?,digest=?,status='pending',reviewed_at=NULL,review_note='Edited by team; needs approval' WHERE id=?").bind(folder.title,folder.creator,folder.description,folder.items.length,folder.items.filter(i=>i.serial.length>8192).length,digest,id),env.LIBRARY.prepare('DELETE FROM folder_chunks WHERE folder_id=?').bind(id));
      chunks(text).forEach((part,i)=>commands.push(env.LIBRARY.prepare('INSERT INTO folder_chunks(folder_id,sequence,content) VALUES(?,?,?)').bind(id,i,part)));
    }
    commands.push(audit(action,id,{previousDigest:row.digest,title:row.title}),env.LIBRARY.prepare('DELETE FROM mutation_guard WHERE id IN (?,?)').bind(guard.id,versionGuard));
    await env.LIBRARY.batch(commands);return json({ok:true});
  }
  return json({ok:false,message:'Not found.'},404);
}
