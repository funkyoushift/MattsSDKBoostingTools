"use strict";
const assert = require('node:assert/strict');
require('./full_progress_panel');
const {advance,splitCoverage} = require('./mission_panel');
(async()=>{
 const unavailable={name:'Mission_Micro_BackMcCrackyPt2',title:'Setting the Mood',state:'unavailable'};
 const locked={name:'Mission_Main_Beach',state:'locked'};
 assert.deepEqual(splitCoverage([unavailable,locked]),{unavailable:[unavailable],remaining:[locked]});
 assert.equal(splitCoverage([{...unavailable,state:'active'}]).unavailable.length,0);
 assert.equal(splitCoverage([{name:'unknown',state:'unavailable'}]).remaining.length,1);

 let calls=0;
 const result=await advance(async()=>{
 const unavailable={name:'Mission_Micro_BackMcCrackyPt2',title:'Setting the Mood',state:'unavailable'};
 const locked={name:'Mission_Main_Beach',state:'locked'};
 assert.deepEqual(splitCoverage([unavailable,locked]),{unavailable:[unavailable],remaining:[locked]});
 assert.equal(splitCoverage([{...unavailable,state:'active'}]).unavailable.length,0);
 assert.equal(splitCoverage([{name:'unknown',state:'unavailable'}]).remaining.length,1);
calls++;return {ok:false,id:'x',state:'uncertain'};},{ok:true,state:'running',id:'x'},()=>false,()=>{});
 assert.equal(calls,1);assert.equal(result.state,'uncertain');
 calls=0;
 let stopped=false;
 const retained=await advance(async()=>{calls++;stopped=true;throw Error('timeout');},{ok:true,state:'running',id:'x'},()=>stopped,()=>{});
 assert.equal(calls,1);assert.equal(retained.id,'x');
 console.log('PASS mission stepping stops on failure or unknown outcome');
})().catch(error=>{console.error(error);process.exitCode=1;});
