const fs=require('node:fs/promises'),path=require('node:path');
function createMobileDesktopFiles({roots,readFile}){
  async function allowedRoots(){
    const result=[];
    for(const folder of await roots())try{const real=await fs.realpath(folder);if(!result.includes(real))result.push(real);}catch{}
    return result;
  }
  async function checked(file){
    const real=await fs.realpath(file),folders=await allowedRoots();
    if(!folders.some(root=>{const relative=path.relative(root,real);return relative===''||(!relative.startsWith('..')&&!path.isAbsolute(relative));}))throw Error('Choose a file inside a listed PC save folder');
    return real;
  }
  async function request(body={}){
    const folders=await allowedRoots();
    if(body.operation==='roots')return {ok:true,roots:folders.map(folder=>({name:folder,path:folder}))};
    const target=await checked(String(body.path||''));
    if(body.operation==='read')return readFile(target);
    if(body.operation!=='list')throw Error('Unknown file browser request');
    const entries=(await fs.readdir(target,{withFileTypes:true})).filter(row=>row.isDirectory()||/\.(sav|yaml|yml|txt)$/i.test(row.name)).slice(0,2000).map(row=>({name:row.name,path:path.join(target,row.name),directory:row.isDirectory()}));
    entries.sort((a,b)=>Number(b.directory)-Number(a.directory)||a.name.localeCompare(b.name));
    return {ok:true,path:target,entries};
  }
  return {request,checked};
}
module.exports={createMobileDesktopFiles};
