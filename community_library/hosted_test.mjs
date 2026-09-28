// Explicit hosted acceptance test. Only deletes its own generated account and folder IDs.
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
const origin='https://msbt-community-library.screename53.workers.dev';
const folderId=crypto.randomUUID(),ownerKey=crypto.randomBytes(32).toString('hex');
const password=crypto.randomBytes(32).toString('hex'),email=`acceptance-${crypto.randomUUID()}@example.invalid`;
let userId='',cookie='',receipt=[];
const check=(value,label)=>{assert(value,label);receipt.push(label);console.log('PASS '+label);};
async function sql(command){const file=path.join(os.tmpdir(),'msbt-hosted-'+crypto.randomUUID()+'.sql');try{await fs.writeFile(file,command);execFileSync(process.execPath,['node_modules/wrangler/bin/wrangler.js','d1','execute','msbt-community-library','--remote','--file',file],{stdio:'pipe',timeout:60000});}finally{await fs.unlink(file);}}
async function request(route,method='GET',body,secret=false){return fetch(origin+route,{method,headers:{Origin:origin,...(body?{'Content-Type':'application/json'}:{}),...(secret?{Authorization:'Bearer '+ownerKey}:cookie?{Cookie:cookie}:{})},body:body?JSON.stringify(body):undefined});}
try {
 check((await request('/health')).ok,'hosted health');
 const page=await request('/portal');check(page.ok&&page.headers.get('content-security-policy').includes("frame-ancestors 'none'"),'portal and restrictive content policy');
 const signup=await request('/api/auth/sign-up/email','POST',{email,password,name:'Temporary acceptance test'});
 check(signup.ok,'hosted account creation');const data=await signup.json();userId=data.user.id;
 assert(/^[A-Za-z0-9_-]+$/.test(userId));
 cookie=signup.headers.getSetCookie().map(x=>x.split(';')[0]).join('; ');
 check(signup.headers.getSetCookie().some(x=>/httponly/i.test(x)&&/secure/i.test(x)),'secure HttpOnly session cookie');
 check((await request('/review')).status===401,'new account has no review access');
 await sql(`INSERT INTO team(user_id,role) VALUES('${userId}','owner');`);
 check((await request('/review')).ok,'authorized account can access review queue');
 const folder={version:1,title:'TEMPORARY acceptance test - do not import',creator:'MSBT automated test',description:'Synthetic validation data, removed after test.',folders:[''],items:[{name:'Test only',folder:'',serial:'@UAcceptanceTest'}]};
 let response=await request('/submissions','POST',{id:folderId,folder},true);check(response.ok,'hosted submission');
 check((await fetch(origin+'/folders/'+folderId)).status===404,'pending contents unavailable publicly');
 let stored=await(await request('/review/'+folderId)).json();
 response=await request('/review/'+folderId,'POST',{status:'approved',digest:stored.digest,note:'Temporary acceptance test'});check(response.ok,'hosted approval');
 const published=await(await fetch(origin+'/folders/'+folderId)).json();check(published.folder.items[0].serial===folder.items[0].serial,'public download preserves exact code');
 folder.items[0].name='Edited test item';
 response=await request('/portal/api/folders/'+folderId,'PUT',{digest:stored.digest,folder});check(response.ok,'hosted item editing');
 check((await fetch(origin+'/folders/'+folderId)).status===404,'edited folder requires approval again');
 stored=await(await request('/review/'+folderId)).json();
 response=await request('/portal/api/folders/'+folderId,'DELETE',{digest:stored.digest});check(response.ok,'hosted folder deletion');
 await sql(`DELETE FROM team WHERE user_id='${userId}';`);
 check((await request('/review')).status===401,'role revocation enforced on existing session');
 await request('/api/auth/sign-out','POST',{});
 check((await request('/portal/api/me')).status===401,'hosted sign-out');
} finally {
 const cleanup=`DELETE FROM folder_chunks WHERE folder_id='${folderId}'; DELETE FROM folders WHERE id='${folderId}';`+(userId?`DELETE FROM audit WHERE actor='${userId}'; DELETE FROM team WHERE user_id='${userId}'; DELETE FROM session WHERE userId='${userId}'; DELETE FROM account WHERE userId='${userId}'; DELETE FROM user WHERE id='${userId}';`:'');
 await sql(cleanup);
 await fs.mkdir('../output/community-folders-review',{recursive:true});
 await fs.writeFile('../output/community-folders-review/hosted-receipt.json',JSON.stringify({at:new Date().toISOString(),origin,checks:receipt,testDataRemoved:true},null,2));
 console.log('Temporary hosted test data removed.');
}
