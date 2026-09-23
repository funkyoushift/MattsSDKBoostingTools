const {app,BrowserWindow}=require('electron');const path=require('path');
app.whenReady().then(async()=>{const w=new BrowserWindow({show:false,webPreferences:{sandbox:true}});await w.loadFile(path.join(__dirname,'renderer.html'),{query:{nosplash:'1'}});await w.webContents.executeJavaScript(`(()=>{
const check=(v,m)=>{if(!v)throw Error(m)};state.pendingTargetValue='';
const d={selected_player:'Guest <safe>',selected_player_index:1,player_readback:{available:true,name:'Guest <safe>',sampled_at:Date.now()/1000,level:70,specialization:701,currencies:{Cash:0,VaultCard01_Tokens:2147483647},vault_cards:[{card:1,rank:112,active:false}]}};
renderPlayerReadback(d);const root=document.getElementById('playerReadback');
check(root.textContent.includes('2,147,483,647'),'keys missing');check(root.textContent.includes('Unavailable'),'missing values invented');check(root.textContent.includes('Inactive'),'inactive card missing');check(root.textContent.includes('Guest <safe>'),'name missing');
d.player_readback.name='Other';renderPlayerReadback(d);check(!root.textContent.includes('2,147,483,647'),'wrong player shown');
d.player_readback.name=d.selected_player;d.player_readback.sampled_at-=30;renderPlayerReadback(d);check(!root.textContent.includes('701'),'stale reading retained');renderPlayerReadback(null);check(!root.textContent.includes('701'),'offline stats retained');
})()`);console.log('PASS live player stats: keys, missing fields, identity, stale and offline handling');w.destroy();app.exit(0)}).catch(e=>{console.error(e);app.exit(1)});
