'use strict';
// Run with Electron. Only approved public-folder serials may enter the export.
// Reads cached native widgets and renders images locally; never calls NCS/game.
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const {app,BrowserWindow,protocol}=require('electron');
const root=path.resolve(__dirname,'..');
const native=require('../electron_poc/native_card_protocol');
const contract=require('../electron_poc/community_folders_contract');
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
native.registerNativeCardSchemes(protocol);
app.on('window-all-closed',()=>{}); // Finish manifest writes after offscreen teardown.
const [cache,output,gzoFile]=process.argv.slice(2,5).map(x=>path.resolve(x));
app.setPath('userData',path.join(output,'electron-profile'));
const api='https://msbt-community-library.screename53.workers.dev';
async function get(route){const r=await fetch(api+route,{signal:AbortSignal.timeout(60000)});if(!r.ok)throw Error('Public library HTTP '+r.status);const data=await r.json();if(!data.ok)throw Error('Public library unavailable');return data;}
app.whenReady().then(async()=>{
 if(!cache||!output||!gzoFile)throw Error('Expected cache directory, output directory, GZO index');
 const publicItems=new Map(),folderIds=new Set();let offset=0;
 do{const page=await get('/folders?limit=100&offset='+offset);for(const f of page.folders){if(folderIds.has(f.id))continue;folderIds.add(f.id);const data=await get('/folders/'+f.id);if(data.status!=='approved')throw Error('Non-public folder');const folder=contract.normalize(data.folder);if(hash(JSON.stringify(folder))!==data.digest)throw Error('Folder digest mismatch');for(const item of folder.items)publicItems.set(item.serial,true);}offset=page.next;}while(offset!==null);
 const gzo=JSON.parse(await fs.readFile(gzoFile,'utf8')).images;
 const files=await fs.readdir(path.join(cache,'widgets'));const widgets=new Map();
 for(const file of files){if(!/^[a-f0-9]{64}\.json$/.test(file))continue;const full=path.join(cache,'widgets',file),stat=await fs.stat(full);if(stat.size>16*1024*1024)continue;const r=JSON.parse(await fs.readFile(full,'utf8'));if(r.schema!=='native-standalone-widget-v1'||!publicItems.has(r.serial)||gzo[hash(r.serial)]?.url)continue;const old=widgets.get(r.serial);if(!old||stat.mtimeMs>old.time)widgets.set(r.serial,{widget:r.widget,time:stat.mtimeMs});}
 await fs.mkdir(output,{recursive:true});
 let generated=0,generationStopped=null,generationFailures={};
 try{generationFailures=JSON.parse(await fs.readFile(path.join(output,'generation-failures.json'),'utf8'));}catch(error){if(error.code!=='ENOENT')throw error;}
 if(process.argv.includes('--fill')){
  const request=async({path:route,payload})=>{const response=await fetch('http://127.0.0.1:49774'+route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:AbortSignal.timeout(20000)});if(!response.ok)throw Error('Game bridge HTTP '+response.status);return response.json();};
  const client=require('../electron_poc/native_preview_client').createNativePreviewClient({request,capture:()=>{throw Error('Data only');},cacheDirectory:cache,renderRevision:'website-data-only'});
  await client.connect();
  for(const serial of publicItems.keys()){
   if(gzo[hash(serial)]?.url||widgets.has(serial)||generationFailures[hash(serial)])continue;
   try{const result=await client.get(serial,{image:false});widgets.set(serial,{widget:result.widget,time:Date.now()});generated++;if(generated%50===0)console.log('Cached '+generated+' new game widgets');}
   catch(error){
    if(/Native serial construction failed|Widget string bounds/.test(String(error.message))){generationFailures[hash(serial)]=error.message;await fs.writeFile(path.join(output,'generation-failures.json'),JSON.stringify(generationFailures,null,2));continue;}
    generationStopped=error.message;console.log('Generation stopped: '+generationStopped);break;
   }
  }
 }
 native.installNativeCardProtocol(protocol);const capture=require('../electron_poc/native_card_capture').createNativeWidgetCapture(BrowserWindow);
 const revision=hash(Buffer.concat(await Promise.all(['native_card_adapter.js','native_card_compat.css','native_card_protocol.js','native_widget_card_model.js','native_card_capture.js','native_card_ui/manifest.json'].map(file=>fs.readFile(path.join(root,'electron_poc',file))))));
 let previous;try{previous=JSON.parse(await fs.readFile(path.join(output,'index.json'),'utf8'));}catch(error){if(error.code!=='ENOENT')throw error;}
 await fs.mkdir(path.join(output,'images'),{recursive:true});const manifest={schema:1,renderer_revision:revision,generated_at:new Date().toISOString(),images:{}},failures=[];
 const checkpoint=async()=>{const temp=path.join(output,'index.next.json');await fs.writeFile(temp,JSON.stringify(manifest));await fs.rename(temp,path.join(output,'index.json'));};
 try{for(const [serial,{widget}] of widgets){try{
  const key=hash(serial),widgetHash=hash(JSON.stringify(widget)),old=previous?.images?.[key];
  if(previous?.renderer_revision===revision&&old?.widget_hash===widgetHash&&!(process.argv.includes('--repair-warnings')&&old.warnings?.some(w=>w.startsWith('Image failed:')))&&/^cards\/images\/[a-f0-9]{64}\.png$/.test(old.url)){
   const bytes=await fs.readFile(path.join(output,old.url.slice(6)));if(hash(bytes)===path.basename(old.url,'.png')){manifest.images[key]=old;continue;}
  }
  const image=await capture.capture(widget);if(!image.ok)throw Error('Capture failed');const bytes=Buffer.from(image.base64,'base64'),digest=hash(bytes);await fs.writeFile(path.join(output,'images',digest+'.png'),bytes);manifest.images[key]={url:'cards/images/'+digest+'.png',name:widget.Name,source:'Game card',layout:image.layout,width:image.width,height:image.height,widget_hash:widgetHash,warnings:image.warnings};
 }catch(error){failures.push({serial_hash:hash(serial),message:error.message});}if((Object.keys(manifest.images).length+failures.length)%25===0){console.log('Rendered '+Object.keys(manifest.images).length+' cards');await checkpoint();}}}
 finally{await capture.close();}
 const missing=[...publicItems.keys()].filter(s=>!gzo[hash(s)]?.url&&!manifest.images[hash(s)]).map(hash);
 await checkpoint();
 const receipt={folders:folderIds.size,public_serials:publicItems.size,gzo:[...publicItems.keys()].filter(s=>gzo[hash(s)]?.url).length,generated,generationStopped,rejected_serials:Object.keys(generationFailures).length,exported:Object.keys(manifest.images).length,missing:missing.length,failures,missing_serial_hashes:missing};
 await fs.writeFile(path.join(output,'receipt.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify({...receipt,missing_serial_hashes:undefined}));app.exit(failures.length?1:0);
}).catch(error=>{console.error(error);app.exit(1);});
