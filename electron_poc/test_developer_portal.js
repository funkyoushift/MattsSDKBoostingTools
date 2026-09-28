const {app,BrowserWindow}=require('electron');
const path=require('node:path');
app.disableHardwareAcceleration();
app.whenReady().then(async()=>{
 const win=new BrowserWindow({show:false,webPreferences:{partition:'portal-test-'+process.pid,sandbox:true}});
 await win.loadFile(path.join(__dirname,'../community_library/portal.html'));
 await win.webContents.executeJavaScript(`(async()=>{
  const check=(v,m)=>{if(!v)throw Error(m)},pause=()=>new Promise(r=>setTimeout(r,30));
  let logged=false,saved=null,assigned=null,requests=[];
  window.confirm=()=>true;
  window.fetch=async(route,options={})=>{
   requests.push(route);const body=options.body?JSON.parse(options.body):{};
   if(route==='/api/auth/sign-in/email'){logged=true;return Response.json({user:{id:'owner'}});}
   if(route==='/portal/api/me')return Response.json(logged?{ok:true,person:{id:'owner',name:'Owner',role:'owner'}}:{message:'Sign in'},{status:logged?200:401});
   if(route.startsWith('/review?'))return Response.json({ok:true,next:null,folders:[{id:'folder',title:'Test folder',creator:'Tester',item_count:2}]});
   if(route==='/review/folder')return Response.json({ok:true,id:'folder',status:'pending',digest:'hash',folder:{version:1,title:'Test folder',creator:'Tester',description:'Demo',folders:[''],items:[{name:'One',folder:'',serial:'@UOne'},{name:'Two',folder:'',serial:'@UTwo'}]}});
   if(route==='/portal/api/folders/folder'){saved=body;return Response.json({ok:true});}
   if(route==='/portal/api/team'){if(options.method==='POST'){assigned=body;return Response.json({ok:true});}return Response.json({ok:true,users:[{id:'team',name:'<img src=x>',email:'test@example.test',role:'member'}]});}
   if(route==='/api/auth/sign-out'){logged=false;return Response.json({ok:true});}
   throw Error('Unexpected '+route);
  };
  while(busy)await pause();
  $('email').value='owner@example.test';$('password').value='fixture-only-password';
  $('loginForm').dispatchEvent(new Event('submit',{cancelable:true}));await pause();
  check($('password').value==='','password cleared');check(!$('team').hidden,'owner sees team');
  $('list').querySelector('button').click();await pause();
  check($('items').querySelectorAll('.row').length===2,'item editor');
  $('items').querySelector('textarea').value='@UChanged';$('items').querySelector('textarea').dispatchEvent(new Event('input'));
  $('save').click();await pause();check(saved.folder.items[0].serial==='@UChanged','item edit submitted');check(saved.digest==='hash','optimistic edit guard');
  $('teamRefresh').click();await pause();check(!$('members').querySelector('img'),'team names treated as text');
  $('members').querySelector('select').value='editor';$('members').querySelector('button').click();await pause();check(assigned.role==='editor','role assignment');
  $('logout').click();await pause();check(!$('login').hidden&&$('team').hidden,'logout hides management');
 })()`);
 console.log('PASS developer portal: sign-in, password clearing, item edit, role controls, escaped names, sign-out');win.destroy();app.exit(0);
}).catch(e=>{console.error(e);app.exit(1)});
