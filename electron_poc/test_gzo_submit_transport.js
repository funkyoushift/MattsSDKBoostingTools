"use strict";
const assert=require("node:assert/strict"), fs=require("node:fs"), path=require("node:path"), vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"main.js"),"utf8");
const region=source.slice(source.indexOf("function normalizeGzoField("),source.indexOf('ipcMain.handle("app:submitGzoCode"'));
let reply, requests=[];
const context=vm.createContext({fs:require("node:fs/promises"),path,Buffer,Blob,FormData,AbortController,setTimeout,clearTimeout,
  CODES_API:"https://example.invalid/never-contacted",fetch:async(endpoint,options)=>{requests.push({endpoint,options});if(reply instanceof Error)throw reply;return reply;}});
vm.runInContext(region,context);
const payload={listing:"Legit",name:"Test card",creator:"Test",category:"Order",type:"Shield",rarity:"Pearl",dlc:"Stone Demon",deserialized:"300, 0, 1, 60| 2, 1|| {1}|",notes:"Fixture only",imageType:"image/png",imageBase64:"iVBORw0KGgo=",imageName:"fixture.png"};
async function run(){
  assert.equal((await context.submitGzoCode({})).ok,false);
  assert.equal(requests.length,0);
  reply=new Response(JSON.stringify({success:true,editUrl:"https://example.invalid/edit",published:false}));
  const accepted=await context.submitGzoCode(payload);
  assert.equal(accepted.ok,true);
  assert.equal(accepted.editUrl,"https://example.invalid/edit");
  const form=requests[0].options.body;
  for(const key of ["listing","name","creator","category","type","rarity","dlc","deserialized","notes"])assert.equal(form.get(key),payload[key]);
  assert.equal(form.get("action"),"submit");assert.equal(form.get("image").type,"image/png");
  for(const response of [new Response("<html>upstream error</html>"),new Response("{}"),new Response('{"success":false,"message":"Rejected"}'),new Response('{"success":true}',{status:503})]){
    reply=response;assert.equal((await context.submitGzoCode(payload)).ok,false);
  }
  reply=new Error("offline");assert.equal((await context.submitGzoCode(payload)).ok,false);
  console.log("PASS GZO submit transport: fields, PNG, explicit acceptance, HTTP/API failures and network errors; no external writes");
}
run().catch(error=>{console.error(error);process.exitCode=1;});
