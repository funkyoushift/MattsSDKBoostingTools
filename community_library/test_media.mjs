import {test} from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';import vm from 'node:vm';import {webcrypto} from 'node:crypto';
test('GZO screenshot lookup is exact and case-sensitive',async()=>{const source=await fs.readFile(new URL('./media-client.txt',import.meta.url),'utf8');const serial='@UAbCdEf',key=Buffer.from(await webcrypto.subtle.digest('SHA-256',new TextEncoder().encode(serial))).toString('hex');let requests=0;const context=vm.createContext({crypto:webcrypto,TextEncoder,URL,AbortSignal,location:{href:'https://example.test/community/'},fetch:async()=>{requests++;return {ok:true,json:async()=>({images:{[key]:{url:'https://save-editor.be/test.jpg',name:'Source label'}}})};}});vm.runInContext(source,context);assert.equal((await context.CommunityImages.match(serial)).name,'Source label');assert.equal(await context.CommunityImages.match('@Uabcdef'),undefined);assert.equal(await context.CommunityImages.match(serial+'X'),undefined);assert.equal(requests,1);});

import clientModule from '../electron_poc/community_folders_client.js';
import contract from '../electron_poc/community_folders_contract.js';
import crypto from 'node:crypto';
test('desktop uses exact GZO titles and trusted images without changing canonical folder',async()=>{
 const folder=contract.normalize({version:1,title:'Fixture',creator:'Tester',items:[{name:'Saved label',serial:'@UAbCd',folder:''},{name:'Keep label',serial:'@Uabcd',folder:''}]});
 const key=crypto.createHash('sha256').update(folder.items[0].serial).digest('hex');
 const data={ok:true,folder,digest:crypto.createHash('sha256').update(JSON.stringify(folder)).digest('hex'),item_details:{[key]:{title:'GZO title',title_source:'GZO',image_url:'https://save-editor.be/GZO/test.png',image_source:'GZO exact code match'}}};
 const client=clientModule.createCommunityClient({userData:'.',safeStorage:{},fetcher:async()=>Response.json(data)});
 const result=await client.dispatch('get',{id:crypto.randomUUID()});
 assert.equal(result.folder.items[0].name,'Saved label');assert.equal(result.presentations[0].title,'GZO title');assert.equal(result.presentations[1],null);assert.equal(result.presentations[0].image_url,data.item_details[key].image_url);
 data.item_details[key].image_url='https://untrusted.test/screenshot.jpg';assert.equal((await client.dispatch('get',{id:crypto.randomUUID()})).presentations[0].image_url,'');
 data.folder.items[0].serial='@UChanged';await assert.rejects(client.dispatch('get',{id:crypto.randomUUID()}),/integrity/);
});
