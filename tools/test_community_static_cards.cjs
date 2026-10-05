'use strict';
const {app,BrowserWindow}=require('electron'),fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const site=path.resolve(process.argv[2]),exportsDir=path.resolve(process.argv[3]);
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
app.whenReady().then(async()=>{
 const index=JSON.parse(await fs.readFile(path.join(exportsDir,'index.json'),'utf8')),example=Object.values(index.images)[0];
 const imageType=example.url.endsWith('.webp')?'image/webp':'image/png';
 const png=await fs.readFile(path.join(exportsDir,example.url.replace('cards/','')));
 const win=new BrowserWindow({show:false,width:1100,height:800});let requests=[];
 await win.webContents.session.protocol.handle('https',async request=>{
  const u=new URL(request.url);requests.push({host:u.hostname,path:u.pathname,method:request.method});if(request.method!=='GET')throw Error('Unexpected write request');
  if(u.hostname==='msbt-community-library.screename53.workers.dev'&&u.pathname.startsWith('/images/'))return new Response(png,{headers:{'Content-Type':imageType}});
  if(u.hostname==='msbt-community-library.screename53.workers.dev')return Response.json({ok:true,folders:[],next:null});
  if(u.pathname.endsWith('/gzo-images.json'))return Response.json({images:{[hash('@UGzo')]:{url:'https://www.funkyoushift.com/community/test.png',name:'Existing GZO',source:'https://save-editor.be'}}});
  if(u.pathname.endsWith('/cards/index.json'))return Response.json({images:{[hash('@UNative')]:example}});
  if(/\.(png|webp)$/.test(u.pathname))return new Response(png,{headers:{'Content-Type':imageType}});
  const file=path.join(site,u.pathname==='/'?'index.html':u.pathname);return new Response(await fs.readFile(file),{headers:{'Content-Type':file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':'text/html'}});
 });
 await win.loadURL('https://www.funkyoushift.com/community/index.html');
 const result=await win.webContents.executeJavaScript(`(async()=>{
 const wait=async f=>{for(let n=0;n<100;n++){if(f())return;await new Promise(r=>setTimeout(r,25));}throw Error('Card timed out');};
 const make=()=>{const el=document.createElement('div');document.body.prepend(el);return el;};
 const native=make();let name=null;native.addEventListener('community-card-name',e=>name=e.detail.name);
 await CommunityImages.show(native,{serial:'@UNative',name:'User saved label'});await wait(()=>native.querySelector('.item-card-view-button'));
 const title=name;native.querySelector('button').click();const opened=!!document.querySelector('.item-card-popout');const zoom=document.querySelector('.item-card-popout input');zoom.value='200';zoom.dispatchEvent(new Event('input'));const zoomed=document.querySelector('.item-card-popout-scroll img').style.width==='200%';MSBTCardPreview.close();
 const gzo=make();let renamed=false;gzo.addEventListener('community-card-name',()=>renamed=true);await CommunityImages.show(gzo,{serial:'@UGzo',name:'GZO original'});await wait(()=>gzo.querySelector('button'));
 const uploaded=make();await CommunityImages.show(uploaded,{serial:'@UNative',name:'Uploaded'},[{serial_hash:await CommunityImages.hash('@UNative'),id:'abc'}],'https://msbt-community-library.screename53.workers.dev');await wait(()=>uploaded.querySelector('button'));
 const other=make();await CommunityImages.show(other,{serial:'@Unative',name:'Different code'});
 return {title,opened,zoomed,gzoRenamed:renamed,gzoSource:gzo.textContent,uploadSource:uploaded.textContent,otherImages:other.querySelectorAll('img').length};})()`);
 assert.equal(result.title,example.name);assert.equal(result.opened,true);assert.equal(result.zoomed,true);assert.equal(result.gzoRenamed,false);assert.match(result.gzoSource,/GZO screenshot/);assert.match(result.uploadSource,/Uploaded screenshot/);assert.equal(result.otherImages,0);
 assert.ok(requests.every(r=>r.method==='GET'&&!r.host.includes('ncs')));console.log(JSON.stringify({ok:true,...result,staticOnly:true}));win.destroy();app.exit(0);
}).catch(e=>{console.error(e);app.exit(1);});
