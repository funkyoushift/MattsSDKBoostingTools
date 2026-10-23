"use strict";
const assert=require('node:assert/strict');
const {advance,bind,pollDelay}=require('./full_progress_panel');
(async()=>{
  assert.equal(pollDelay({index:0}),50);
  assert.equal(pollDelay({index:8,child:{kind:"final_recheck"}}),50);
  assert.equal(pollDelay({index:1,child:{kind:"mission"}}),50);
  let calls=[];let firstStatus=true;
  const final=await advance(async(a,p)=>{calls.push([a,p]);return {ok:false,id:'job',state:'uncertain'};},{ok:true,id:'job',state:'running'},()=>{});
  assert.equal(calls.length,1);assert.equal(final.state,'uncertain');
  const nodes=new Map();
  const doc={getElementById(id){if(!nodes.has(id))nodes.set(id,{dataset:{},disabled:false,checked:false,textContent:'',events:{},addEventListener(e,fn){this.events[e]=fn;}});return nodes.get(id);}};
  calls=[];
  const call=async(a,p)=>{calls.push([a,p]);if(a==='full_progress_preview')return {ok:true,allowed:true,players:['Host','Guest'],reason:'Available content'};
    if(a==='full_progress_status'){if(firstStatus){firstStatus=false;return {ok:true,state:'idle'};}return {ok:true,id:'existing',state:'running'};}
    if(a==='full_progress_start')return {ok:true,id:'run',state:'running'};
    if(a==='full_progress_step')return {ok:true,id:p.job_id,state:'finished',index:8,total:8,message:'Review results'};
    throw Error('Unexpected action '+a);};
  bind(doc,call);
  assert.equal(doc.getElementById('fullProgressStart').disabled,true);
  await doc.getElementById('fullProgressPreview').events.click();
  assert.equal(doc.getElementById('fullProgressStart').disabled,true);
  doc.getElementById('fullProgressAck').checked=true;doc.getElementById('fullProgressAck').events.change();
  doc.getElementById('fullProgressReplaceWork').checked=true;
  assert.equal(doc.getElementById('fullProgressStart').disabled,false);
  await doc.getElementById('fullProgressStart').events.click();
  assert.deepEqual(calls.map(c=>c[0]),['full_progress_status','full_progress_preview','full_progress_start','full_progress_step']);
  assert.equal(calls[2][1].acknowledge_shared_progress,true);
  assert.equal(calls[2][1].replace_other_progress,true);
  assert.match(doc.getElementById('fullProgressOutput').textContent,/verify progress/);
  await doc.getElementById('fullProgressStatus').events.click();
  assert.equal(doc.getElementById('fullProgressContinue').disabled,false);
  assert.equal(doc.getElementById('fullProgressStop').disabled,false);
  calls=[];
  await doc.getElementById('fullProgressContinue').events.click();
  assert.deepEqual(calls,[['full_progress_status',{}],['full_progress_step',{job_id:'existing'}]]);
  assert.equal(doc.getElementById('fullProgressContinue').disabled,true);
  const verifiedNodes=new Map();let statusReply={ok:false,state:'failed',message:'Bridge unavailable'};
  const verifiedDoc={getElementById(id){if(!verifiedNodes.has(id))verifiedNodes.set(id,{dataset:{},disabled:false,checked:true,textContent:'',events:{},addEventListener(e,fn){this.events[e]=fn;}});return verifiedNodes.get(id);}};
  bind(verifiedDoc,async action=>{
    if(action==='full_progress_status')return statusReply;
    if(action==='full_progress_preview')return {ok:true,allowed:true};
    throw Error(action);
  });
  statusReply={ok:false,id:'verified-run',state:'uncertain'};
  await verifiedDoc.getElementById('fullProgressStatus').events.click();
  assert.equal(verifiedDoc.getElementById('fullProgressContinue').disabled,false);
  statusReply={ok:false,state:'failed',message:'Bridge unavailable'};
  await verifiedDoc.getElementById('fullProgressStatus').events.click();
  assert.equal(verifiedDoc.getElementById('fullProgressContinue').disabled,false);
  statusReply={ok:true,state:'idle'};
  await verifiedDoc.getElementById('fullProgressStatus').events.click();
  assert.equal(verifiedDoc.getElementById('fullProgressContinue').disabled,true);
  const recoveryNodes=new Map();
  const recoveryDoc={getElementById(id){if(!recoveryNodes.has(id))recoveryNodes.set(id,{dataset:{},disabled:false,checked:true,textContent:'',events:{},addEventListener(e,fn){this.events[e]=fn;}});return recoveryNodes.get(id);}};
  const recoveryCalls=[];
  bind(recoveryDoc,async(a,p)=>{
    recoveryCalls.push([a,p]);
    if(a==='full_progress_status')return {ok:false,id:'saved',state:'uncertain',index:3};
    if(a==='full_progress_resume')return {ok:true,id:'saved',state:'running',index:3};
    if(a==='full_progress_step')return {ok:true,id:'saved',state:'finished',index:9};
    throw Error(a);
  });
  await recoveryDoc.getElementById('fullProgressStatus').events.click();
  assert.equal(recoveryDoc.getElementById('fullProgressContinue').disabled,false);
  assert.equal(recoveryDoc.getElementById('fullProgressContinue').textContent,'Repair and continue');
  await recoveryDoc.getElementById('fullProgressContinue').events.click();
  assert.deepEqual(recoveryCalls.map(c=>c[0]),['full_progress_status','full_progress_status','full_progress_status','full_progress_resume','full_progress_step']);
  assert.equal(recoveryCalls[3][1].job_id,'saved');
  assert.equal(recoveryCalls[3][1].acknowledge_shared_progress,true);
  const stuckNodes=new Map();
  const stuckDoc={getElementById(id){if(!stuckNodes.has(id))stuckNodes.set(id,{dataset:{},disabled:false,checked:true,textContent:'',events:{},addEventListener(e,fn){this.events[e]=fn;}});return stuckNodes.get(id);}};
  const stuckCalls=[];let statusCount=0,closeCount=0,closed=false;
  bind(stuckDoc,async(a,p)=>{
    stuckCalls.push([a,p]);
    if(a==='full_progress_status')return ++statusCount===1 || closed ? {ok:true,state:'idle'} : {ok:false,id:'interrupted-run',state:'interrupted',message:'Inspect old run'};
    if(a==='full_progress_preview')return {ok:true,allowed:true};
    if(a==='full_progress_start')return {ok:false,message:'A prior full-progress run needs inspection'};
    if(a==='full_progress_close'){
      assert.equal(p.job_id,'interrupted-run');
      if(++closeCount===1)return {ok:false,message:'Child cleanup needs inspection'};
      closed=true;return {ok:true,id:p.job_id,state:'cancelled'};
    }
    throw Error(a);
  });
  await stuckDoc.getElementById('fullProgressPreview').events.click();
  stuckDoc.getElementById('fullProgressReplaceWork').checked=true;stuckDoc.getElementById('fullProgressReplaceWork').events.change();
  assert.equal(stuckDoc.getElementById('fullProgressStart').disabled,false);
  await stuckDoc.getElementById('fullProgressStart').events.click();
  assert.equal(stuckCalls.filter(([a])=>a==='full_progress_start').length,1);
  assert.equal(stuckDoc.getElementById('fullProgressStart').disabled,true);
  assert.equal(stuckDoc.getElementById('fullProgressClose').disabled,false);
  await stuckDoc.getElementById('fullProgressClose').events.click();
  assert.equal(stuckDoc.getElementById('fullProgressClose').disabled,false);
  await stuckDoc.getElementById('fullProgressClose').events.click();
  assert.equal(stuckDoc.getElementById('fullProgressClose').disabled,true);
  await stuckDoc.getElementById('fullProgressStatus').events.click();
  await stuckDoc.getElementById('fullProgressPreview').events.click();
  assert.equal(stuckDoc.getElementById('fullProgressStart').disabled,false);
  const restartNodes=new Map();const restartCalls=[];let restartStatusCount=0;
  const restartDoc={getElementById(id){if(!restartNodes.has(id))restartNodes.set(id,{dataset:{},disabled:false,checked:false,textContent:'',events:{},addEventListener(e,fn){this.events[e]=fn;}});return restartNodes.get(id);}};
  bind(restartDoc,async(a,p)=>{
    restartCalls.push([a,p]);
    if(a==='full_progress_status'){
      restartStatusCount++;
      return restartStatusCount===1 || restartStatusCount===2
        ? {ok:false,id:'stopped-run',state:'uncertain',phase:'issued'}
        : {ok:true,state:'idle'};
    }
    if(a==='full_progress_preview')return {ok:true,allowed:true,players:['Host']};
    if(a==='full_progress_close')return {ok:true,id:p.job_id,state:'cancelled'};
    if(a==='full_progress_start')return {ok:true,id:'new-run',state:'finished',message:'Completed'};
    throw Error(a);
  });
  await Promise.resolve();
  await restartDoc.getElementById('fullProgressPreview').events.click();
  restartDoc.getElementById('fullProgressAck').checked=true;
  restartDoc.getElementById('fullProgressReplaceWork').checked=true;
  restartDoc.getElementById('fullProgressReplaceWork').events.change();
  assert.equal(restartDoc.getElementById('fullProgressStart').disabled,false);
  await restartDoc.getElementById('fullProgressStart').events.click();
  assert.deepEqual(restartCalls.map(c=>c[0]),['full_progress_status','full_progress_preview','full_progress_status','full_progress_close','full_progress_status','full_progress_preview','full_progress_start']);
  assert.equal(restartCalls[3][1].job_id,'stopped-run');
  assert.equal(restartCalls[6][1].replace_other_progress,true);
  const failedCloseNodes=new Map();const failedCloseCalls=[];let failedStatusCount=0;
  const failedCloseDoc={getElementById(id){if(!failedCloseNodes.has(id))failedCloseNodes.set(id,{dataset:{},disabled:false,checked:false,textContent:'',events:{},addEventListener(e,fn){this.events[e]=fn;}});return failedCloseNodes.get(id);}};
  bind(failedCloseDoc,async(a,p)=>{
    failedCloseCalls.push([a,p]);
    if(a==='full_progress_status')return ++failedStatusCount===1
      ? {ok:false,id:'uncertain-run',state:'uncertain'} : {ok:false,id:'uncertain-run',state:'uncertain'};
    if(a==='full_progress_preview')return {ok:true,allowed:true};
    if(a==='full_progress_close')return {ok:false,id:'uncertain-run',state:'uncertain',message:'Issued work is still settling'};
    throw Error(a);
  });
  await Promise.resolve();
  await failedCloseDoc.getElementById('fullProgressPreview').events.click();
  failedCloseDoc.getElementById('fullProgressAck').checked=true;
  failedCloseDoc.getElementById('fullProgressReplaceWork').checked=true;
  failedCloseDoc.getElementById('fullProgressReplaceWork').events.change();
  await failedCloseDoc.getElementById('fullProgressStart').events.click();
  assert.equal(failedCloseCalls.filter(([a])=>a==='full_progress_close').length,1);
  assert.equal(failedCloseCalls.filter(([a])=>a==='full_progress_start').length,0);
  assert.equal(failedCloseDoc.getElementById('fullProgressContinue').disabled,false);
  console.log('PASS full-progress lobby preview, acknowledgement, sequenced run and uncertain-stop controls');
})().catch(e=>{console.error(e);process.exitCode=1;});
