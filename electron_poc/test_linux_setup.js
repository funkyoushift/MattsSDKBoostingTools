'use strict';
const assert=require('assert/strict'),fs=require('fs'),os=require('os'),path=require('path');
const {shouldRunSetup}=require('./linux_setup');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'msbt-setup-routing-'));
try{
  const current=path.join(root,'MSBT.AppImage');fs.writeFileSync(current,'fixture');
  const base={platform:'linux',argv:[],env:{APPIMAGE:current},home:root};
  assert.equal(shouldRunSetup(base),true);
  assert.equal(shouldRunSetup({...base,platform:'win32',argv:['--setup']}),false);
  assert.equal(shouldRunSetup({...base,env:{}}),false);
  assert.equal(shouldRunSetup({...base,argv:['--smoke','--setup']}),false);
  assert.equal(shouldRunSetup({...base,argv:['--install-sdkmods-and-exit']}),false);
  const folder=path.join(root,'.local','share','msbt');fs.mkdirSync(folder,{recursive:true});
  const receipt=path.join(folder,'install.json');
  fs.writeFileSync(receipt,JSON.stringify({schema:1,appPath:current}));
  assert.equal(shouldRunSetup(base),false);assert.equal(shouldRunSetup({...base,argv:['--setup']}),true);
  const alias=path.join(root,'alias.AppImage');fs.symlinkSync(current,alias);
  assert.equal(shouldRunSetup({...base,env:{APPIMAGE:alias}}),false);
  fs.writeFileSync(receipt,JSON.stringify({schema:1,appPath:path.join(root,'missing')}));
  assert.equal(shouldRunSetup(base),true);
  console.log('PASS setup routing: platform/smoke guards, explicit setup, valid/stale receipt and canonical image aliases');
}finally{fs.rmSync(root,{recursive:true,force:true});}
