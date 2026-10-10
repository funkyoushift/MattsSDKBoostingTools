'use strict';
(function(root){
  const hosts=new WeakMap();
  let active=null,openTimer=null,closeTimer=null;
  const cancelClose=()=>clearTimeout(closeTimer);
  function close(restoreFocus=false){
    clearTimeout(openTimer);cancelClose();
    if(!active)return;
    const {panel,observer,state}=active;active=null;observer.disconnect();panel.remove();
    state.button.setAttribute('aria-expanded','false');
    if(restoreFocus&&state.button.isConnected)state.button.focus();
  }
  function laterClose(){cancelClose();closeTimer=setTimeout(()=>{if(active&&!active.pinned)close();},120);}
  function open(state,focus=false){
    clearTimeout(openTimer);cancelClose();
    if(!state.current()||!state.image.isConnected)return;
    if(active?.pinned&&!focus)return;
    if(active?.state===state&&(!focus||active.pinned))return;
    close();
    const panel=document.createElement('div');panel.className='item-card-popout';panel.setAttribute('popover','manual');
    panel.dataset.previewMode=focus?'pinned':'hover';
    panel.setAttribute('role',focus?'dialog':'tooltip');panel.setAttribute('aria-label',state.image.alt||'Full item card');
    panel.inert=!focus;
    const toolbar=document.createElement('div');toolbar.className='item-card-popout-toolbar';
    const label=document.createElement('label');label.textContent='Zoom ';
    const zoom=document.createElement('input');zoom.type='range';zoom.min='100';zoom.max='200';zoom.step='25';zoom.value='100';zoom.setAttribute('aria-label','Card zoom');
    const amount=document.createElement('output');amount.textContent='100%';label.append(zoom,amount);
    const dismiss=document.createElement('button');dismiss.type='button';dismiss.textContent='Close';dismiss.addEventListener('click',()=>close(focus));
    if(focus)toolbar.append(label,dismiss);
    else toolbar.textContent='Preview · Click View card to keep open, scroll or zoom';
    const scroll=document.createElement('div');scroll.className='item-card-popout-scroll';scroll.tabIndex=focus?0:-1;scroll.setAttribute('aria-label','Full card; scroll to read');
    const image=document.createElement('img');image.src=state.image.src;image.alt=state.image.alt;image.draggable=false;image.referrerPolicy='no-referrer';scroll.append(image);
    zoom.addEventListener('input',()=>{image.style.width=zoom.value+'%';amount.textContent=zoom.value+'%';});
    panel.append(toolbar,scroll);document.body.append(panel);
    const bounds=state.image.getBoundingClientRect(),width=Math.min(580,innerWidth-24);
    const right=bounds.right+12,left=bounds.left-width-12;
    panel.style.width=width+'px';
    panel.style.left=(right+width<=innerWidth-12?right:left>=12?left:Math.max(12,(innerWidth-width)/2))+'px';
    panel.style.top=Math.max(12,Math.min(bounds.top,innerHeight-320))+'px';
    panel.style.maxHeight=(innerHeight-parseFloat(panel.style.top)-12)+'px';
    panel.showPopover();
    panel.addEventListener('pointerenter',cancelClose);panel.addEventListener('pointerleave',laterClose);
    panel.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();close(focus);}});
    panel.addEventListener('focusout',laterClose);
    const observer=new MutationObserver(()=>{if(!state.current()||!state.image.isConnected)close();});
    observer.observe(document.body,{childList:true,subtree:true});
    active={panel,observer,state,image,pinned:focus,restoreFocus:focus};state.button.setAttribute('aria-expanded','true');
    if(focus)dismiss.focus();
  }
  function attach(host,image,current){
    let state=hosts.get(host);
    if(!state||!state.button.isConnected){
      const button=document.createElement('button');button.type='button';button.className='item-card-view-button';button.textContent='View card';
      button.setAttribute('aria-haspopup','dialog');button.setAttribute('aria-expanded','false');
      state={button,image,current};hosts.set(host,state);host.append(button);
      button.addEventListener('keydown',event=>event.stopPropagation());
      button.addEventListener('click',event=>{event.stopPropagation();open(state,true);});
    }
    state.image=image;state.current=current;image.classList.add('item-card-thumbnail');
    image.addEventListener('pointerenter',event=>{if(event.pointerType==='touch')return;cancelClose();clearTimeout(openTimer);openTimer=setTimeout(()=>open(state),220);});
    image.addEventListener('pointerleave',()=>{clearTimeout(openTimer);laterClose();});
    if(active?.state===state){active.image.src=image.src;active.image.alt=image.alt;}
  }
  root.addEventListener('resize',()=>close());
  document.addEventListener('scroll',event=>{if(active&&!active.panel.contains(event.target))close();},true);
  document.addEventListener('pointerdown',event=>{if(active&&!active.panel.contains(event.target)&&event.target!==active.state.button&&event.target!==active.state.image)close();},true);
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&active){event.preventDefault();event.stopPropagation();close(active.restoreFocus);}},true);
  root.MSBTCardPreview={attach,close};
})(window);
