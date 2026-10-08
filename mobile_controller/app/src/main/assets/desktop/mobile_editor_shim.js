// Route the bundled save/profile editor's existing local APIs through the PC.
(() => {
  const bridge=parent.parent.mobileDesktopBridge;
  window.MSBT_MATT_EDITOR_MODE=true;window.IS_ELECTRON_APP=true;
  window.ELECTRON_API_URL=location.origin;
  window.getLocalApiUrl=()=>'/api.php';
  window.SAVE_DESERIALIZE_API_BASE_URL='/api.php';window.SAVE_DESERIALIZE_API_FALLBACK_URL='/api.php';
  window.SERIALIZE_API_BASE_URL='/api.php';window.SERIALIZE_API_FALLBACK_URL='/api.php';window.SAVE_API_BASE_URL='/blcrypt/api.php';
  const original=window.fetch.bind(window);
  window.fetch=async(input,init={})=>{
    const raw=typeof input==='string'?input:input.url,url=new URL(raw,location.href);let route=null;
    if(url.pathname.includes('nexus_data_proxy.php'))route='/LegitItems/nexus_data_proxy.php'+url.search;
    else if(url.pathname.startsWith('/msbt/'))route=url.pathname+url.search;
    else if(url.pathname.includes('/blcrypt/')||url.pathname.endsWith('blcrypt/api.php'))route='/blcrypt/api.php'+url.search;
    else if(url.pathname.endsWith('/api.php')||url.hostname==='borderlands4-deserializer.nicnl.com')route='/api.php';
    if(!route)return original(input,init);
    let body=init.body,headers=new Headers(init.headers||(input instanceof Request?input.headers:{}));
    if(body===undefined&&input instanceof Request&&!['GET','HEAD'].includes(input.method))body=await input.clone().text();
    if(body instanceof URLSearchParams){headers.set('Content-Type','application/x-www-form-urlencoded');body=body.toString();}
    if(body instanceof FormData){const fields=new URLSearchParams();for(const [key,value] of body){if(typeof value!=='string')throw Error('Use the editor file picker to open save files.');fields.append(key,value);}body=fields.toString();headers.set('Content-Type','application/x-www-form-urlencoded');}
    const reply=await bridge.call('$editorFetch',[{route,method:init.method||(input instanceof Request?input.method:'GET'),body:body||'',contentType:headers.get('Content-Type')||'application/json'}]);
    return new Response(reply.body,{status:reply.status,headers:{'Content-Type':reply.contentType}});
  };
  window.MSBT_SELECT_EDITOR_TAB=tabId=>{if(typeof window.switchTab==='function'){window.switchTab(tabId);return true;}return false;};
})();
