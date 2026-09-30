const fs=require('fs'),path=require('path'),acorn=require('../output/languages/tooling/node_modules/acorn');
const rows=new Set();
function add(s){s=s.replace(/\s+/g,' ').trim();if(s.length>1&&/[a-zA-Z]/.test(s)&&s.length<3000&&!/^["'$]|=>|^#[# ]|[<>{}\\]|https?:\/\/|^\.[a-z]|^#[\w-]+/.test(s))rows.add(s)}
const roots=['electron_poc','mobile_controller/app/src/main/assets'];
for(const dir of roots)for(const name of fs.readdirSync(dir)){
 if(name.endsWith('.js')&&!/^(renderer|workspace|afk|remote_afk_ui|community_folders_ui|save_items_import_ui|app|mobile|panel_layout|matt_editor_page)/.test(name))continue;
 if(!/\.(js|html)$/.test(name)||/^(test_|_tmp_|ui_i18n|native_card)/.test(name))continue;
 const text=fs.readFileSync(path.join(dir,name),'utf8');
 if(name.endsWith('.html')){
  const cleaned=text.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi,'');
  for(const m of cleaned.matchAll(/>([^<>]+)</g))add(m[1].replace(/&amp;/g,'&').replace(/&nbsp;/g,' '));
  for(const m of cleaned.matchAll(/(?:placeholder|title|aria-label)="([^"]+)"/g))add(m[1].replace(/&amp;/g,'&'));
 }else{
  let ast;try{ast=acorn.parse(text,{ecmaVersion:'latest',sourceType:'script'})}catch{continue}
  function walk(n,parent){if(!n||typeof n!=='object')return;if(n.type==='TemplateLiteral' && ((parent?.type==='AssignmentExpression'&&['textContent','innerText','title'].includes(parent.left?.property?.name))||(parent?.type==='CallExpression'&&/^set.*(?:Line|Status)$|^setLine$/.test(parent.callee?.name||''))||(parent?.type==='Property'&&['body','title'].includes(parent.key?.name)))){const value=n.quasis.map((q,i)=>(q.value.cooked||'')+(i<n.expressions.length?'{'+i+'}':'')).join('');if(n.expressions.length&&n.expressions.length<6&&value.length<1200&&!/[<>\\\n]/.test(value)&&/[A-Za-z]{3}/.test(n.quasis[0].value.cooked||''))rows.add(value.replace(/\s+/g,' ').trim());}
if(n.type==='TemplateElement'){const v=n.value.cooked||'';for(const m of v.matchAll(/>([^<>]+)</g))add(m[1].replace(/&amp;/g,'&'));for(const m of v.matchAll(/(?:placeholder|title|aria-label)="([^"]+)"/g))add(m[1]);}
if(n.type==='Literal'&&typeof n.value==='string'&&(/\s/.test(n.value)||/^[A-Z][a-z]+$/.test(n.value)))add(n.value);for(const [k,v]of Object.entries(n))if(k!=='start'&&k!=='end'){if(Array.isArray(v))v.forEach(x=>walk(x,n));else if(v&&typeof v==='object')walk(v,n)}}walk(ast);
 }
}
const list=[...rows].sort();fs.writeFileSync('output/languages/english.json',JSON.stringify(list,null,2));console.log({strings:list.length,characters:list.reduce((n,s)=>n+s.length,0)});

