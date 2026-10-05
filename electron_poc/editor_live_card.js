'use strict';
(() => {
  const frame=document.getElementById('editorFrame'),page=document.getElementById('tab-matt-editor');
  const host=document.getElementById('editorLiveCard'),status=document.getElementById('editorLiveCardStatus');
  const choice=document.getElementById('editorCardChoice'),auto=document.getElementById('editorCardAuto');
  if(!frame||!host)return;
  let codes=[],selected='',timer=null,busy=false,revision=0,pending=false;
  const visible=()=>!document.hidden&&page.classList.contains('active');
  const valid=s=>typeof s==='string'&&s.length>=20&&s.length<=8192&&/^@U[0-9A-Za-z!#$%&()*+\-;<=>?@^_`{\/}~]+$/.test(s);
  function invalidate(message){
    revision++;clearTimeout(timer);pending=false;host.replaceChildren();status.textContent=message;
  }
  function schedule(){
    if(!selected||!visible())return;
    pending=true;clearTimeout(timer);timer=setTimeout(render,650);
  }
  function render(){
    timer=null;if(busy||!pending||!selected||!visible())return;
    pending=false;busy=true;
    const ticket=revision,serial=selected;
    status.textContent='Updating card…';
    window.MSBTItemCards.show(host,{serial,name:'Current editor item'});
    host.cardRequest.finally(()=>{
      busy=false;
      if(ticket===revision)status.textContent='Current editor item';
      if(pending)schedule();
    });
  }
  function receive(event){
    if(event.source!==frame.contentWindow||!event.data?.msbtEditorCard)return;
    let origin;try{origin=new URL(frame.src).origin;}catch{return;}
    if(event.origin!==origin)return;
    const values=event.data.msbtEditorCard.serials;
    if(!Array.isArray(values)||values.length>100)return;
    const next=[...new Set(values.filter(valid))];
    if(JSON.stringify(next)===JSON.stringify(codes))return;
    codes=next;
    selected=codes.length===1?codes[0]:codes.includes(selected)?selected:'';
    choice.replaceChildren(new Option('Choose one item to preview',''));
    codes.forEach((serial,i)=>choice.add(new Option('Item '+(i+1)+' · '+serial.slice(0,18)+'…',serial)));
    choice.hidden=codes.length<2;choice.value=selected;
    invalidate(!codes.length?'Build or select an item to see its card.':!selected?'Choose one item to preview.':auto.checked?'Waiting for edits to settle…':'Preview paused. Click Refresh card.');
    if(auto.checked)schedule();
  }
  window.addEventListener('message',receive);
  choice.addEventListener('change',()=>{selected=choice.value;invalidate('Waiting for edits to settle…');if(auto.checked)schedule();});
  auto.addEventListener('change',()=>{invalidate(auto.checked?'Waiting for edits to settle…':'Preview paused. Click Refresh card.');if(auto.checked)schedule();});
  document.getElementById('editorCardRefresh').addEventListener('click',()=>{invalidate(selected?'Updating card…':'Build or choose one item first.');schedule();});
  frame.addEventListener('load',()=>{codes=[];selected='';choice.hidden=true;invalidate('Build or select an item to see its card.');frame.contentWindow.postMessage({msbtEditorCardRequest:true},'*');});
  function visibilityChanged(){if(!visible()){invalidate('Preview paused while the editor is hidden.');}else if(auto.checked)schedule();}
  new MutationObserver(visibilityChanged).observe(page,{attributes:true,attributeFilter:['class']});
  document.addEventListener('visibilitychange',visibilityChanged);
})();
