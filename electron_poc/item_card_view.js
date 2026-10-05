'use strict';
(function(root) {
  const jobs = [], images = new Map();
  let active = 0, imageTimer = null;
  const imageBatch = new Map();
  function schedule(work) {
    return new Promise((resolve,reject) => { jobs.push({work,resolve,reject}); pump(); });
  }
  function pump() {
    while(active < 8 && jobs.length) {
      const job=jobs.shift();active++;
      Promise.resolve().then(job.work).then(job.resolve,job.reject).finally(()=>{active--;pump();});
    }
  }
  function catalogImage(serial) {
    if(images.has(serial))return images.get(serial);
    const result=new Promise(resolve=>{
      imageBatch.set(serial,resolve);
      if(!imageTimer)imageTimer=setTimeout(async()=>{
        imageTimer=null;
        const batch=[...imageBatch];imageBatch.clear();
        try {
          const reply=await root.msbt.itemCardImages(batch.map(([s])=>s));
          const found=new Map((reply?.items||[]).map(item=>[item.serial,item]));
          batch.forEach(([s,done])=>done(found.get(s)||null));
        } catch { batch.forEach(([,done])=>done(null)); }
      },20);
    });
    images.set(serial,result);
    if(images.size>4000)images.delete(images.keys().next().value);
    return result;
  }
  async function screenshot(item) {
    if(!item.image_url||!item.image_serial_hash)return null;
    const url=new URL(item.image_url);
    if(url.protocol!=='https:' || !((url.hostname==='save-editor.be'&&url.pathname.startsWith('/GZO/')) ||
      (url.hostname==='msbt-community-library.screename53.workers.dev'&&/^\/images\/[0-9a-f-]+$/i.test(url.pathname))))return null;
    const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(item.serial));
    const hash=Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('');
    return hash===item.image_serial_hash?{image:url.href,source:item.image_source||'Community screenshot'}:null;
  }
  function show(host,item) {
    const marker=document.createElement('small');marker.textContent='Loading item card…';
    host.replaceChildren(marker);host.classList.remove('hidden','native-game-card');host.classList.add('bl4-item-card');
    const current=()=>host.isConnected&&host.contains(marker);
    const publishName=(name,source)=>{
      if(current()&&typeof name==='string'&&name.trim())
        host.dispatchEvent(new CustomEvent('msbt-card-name',{detail:{serial:item.serial,name:name.trim(),source}}));
    };
    const loadImage=(url,name)=>new Promise((resolve,reject)=>{
      const image=document.createElement('img');image.alt=name||item.name||'Item card';
      image.style.cssText='display:block;width:100%;height:auto';image.referrerPolicy='no-referrer';
      const timer=setTimeout(()=>{image.onload=image.onerror=null;image.src='';reject(new Error('Image timed out'));},10000);
      image.onload=()=>{clearTimeout(timer);if(current()){host.insertBefore(image,marker);root.MSBTCardPreview?.attach(host,image,current);}resolve(image);};
      image.onerror=()=>{clearTimeout(timer);reject(new Error('Image unavailable'));};image.src=url;
    });
    schedule(async()=>{
      if(!item?.serial?.startsWith('@U')||item.serial.length>8192)throw new Error('Card unavailable for this code · original preserved');
      let uploaded=null;
      try {uploaded=await screenshot(item);} catch {}
      if(!current())return;
      if(uploaded){try {await loadImage(uploaded.image);if(current())marker.textContent=uploaded.source;return;}catch {}}
      const existing=await catalogImage(item.serial);
      if(!current())return;
      if(existing?.image){try{await loadImage(existing.image,existing.itemCard?.name);if(current())marker.textContent='GZO item card';return;}catch{}}
      const reply=await root.msbt.nativeItemPreview(item.serial);
      if(!current())return;
      if(!reply?.ok||!reply.image?.base64)throw new Error(reply?.message||'Open a supported BL4 solo session to generate this card.');
      let displayed=await loadImage('data:image/png;base64,'+reply.image.base64,reply.widget.Name);
      if(!current())return;
      // A missing/unreachable GZO image may use a native fallback, but it is
      // still a catalog item and keeps its existing saved title.
      if(!existing&&!/gzo/i.test(item.image_source||''))publishName(reply.widget.Name,'Game card');
      const caption=reply.offline?'Cached game card · previous session':reply.image.warnings?.length?'Game card · some artwork unavailable':'Game card · standalone stats';
      marker.textContent=caption+(reply.image.layout==='expanded'?' · expanded layout':'');
      marker.title='Uses the game’s card builder. Equipped firmware counts and comparison context are not included.';
      if(reply.image.layout==='expanded'){
        const button=document.createElement('button');button.type='button';button.textContent='Compact layout';
        button.className='item-card-layout-toggle';
        button.title='Switch layout without changing the item. Compact text may overflow for heavily modded items.';
        let compact=null,expanded=true;
        button.addEventListener('keydown',event=>event.stopPropagation());
        button.addEventListener('click',async event=>{
          event.stopPropagation();if(button.disabled||!current())return;button.disabled=true;
          try{
            if(expanded&&!compact){
              const alternate=await root.msbt.nativeItemPreview(item.serial,true,'compact');
              if(!alternate?.ok||!alternate.image?.base64)throw new Error(alternate?.message||'Compact layout unavailable');
              // Refuse another session/item's data if the view changed while loading.
              if(alternate.serial!==reply.serial||alternate.session!==reply.session)throw new Error('Card session changed. Reopen the card to switch layouts.');
              compact=alternate.image;
            }
            if(!current())return;
            const next=await loadImage('data:image/png;base64,'+(expanded?compact:reply.image).base64,reply.widget.Name);
            if(!current())return;
            displayed.remove();displayed=next;expanded=!expanded;
            button.textContent=expanded?'Compact layout':'Expanded layout';
            marker.textContent=caption+(expanded?' · expanded layout':'');
          }catch(error){if(current())marker.textContent=error.message;}
          finally{button.disabled=false;}
        });
        host.append(button);
      }
      host.dispatchEvent(new CustomEvent('msbt-card-ready',{detail:reply}));
    }).catch(error=>{
      if(!current())return;
      marker.textContent=String(error.message).includes('New game cards require a solo session')
        ? 'No matching screenshot or cached card yet. Generate this card in a solo session.'
        : error.message;
    });
    return host;
  }
  root.MSBTItemCards={show,catalogImage,clearCatalog:()=>images.clear()};
})(window);
