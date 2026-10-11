(function(root){
  "use strict";
  async function advance(call,job,report){
    while(job?.ok && job.state === "running"){
      await new Promise(resolve=>setTimeout(resolve,50));
      job=await call("full_progress_step",{job_id:job.id});report(job);
    }
    return job;
  }
  function bind(doc,call){
    const el=id=>doc.getElementById(id);
    if(!el("fullProgressPanel") || el("fullProgressPanel").dataset.bound)return;
    el("fullProgressPanel").dataset.bound="true";
    let preview=null,job=null,busy=false;
    function update(){
      el("fullProgressStart").disabled=busy || job?.state === "running" || !preview?.allowed || !el("fullProgressAck").checked;
      el("fullProgressClose").disabled=busy || !job?.id || !["stopped","uncertain","interrupted"].includes(job.state) || !el("fullProgressAck").checked;
      el("fullProgressPreview").disabled=busy;
      el("fullProgressStop").disabled=job?.state !== "running" || !job?.id;
      el("fullProgressContinue").disabled=busy || job?.state !== "running" || !job?.ok;
    }
    function report(value){
      const lines=[value.message || value.reason || "No confirmed result."];
      if(value.players)lines.push("Players: "+value.players.join(", "));
      if(value.total)lines.push(`${value.index} / ${value.total} stages finished`);
      for(const row of value.skipped || [])lines.push("Unavailable: "+(row.title || row)+ (row.reason?" — "+row.reason:""));
      for(const row of value.blockers || [])lines.push("Blocked: "+row.title+" — "+row.reason);
      for(const row of value.results || []){
        lines.push(`${row.stage}: ${row.state} — ${row.message || ""}`);
        if(Array.isArray(row.details))for(const player of row.details)for(const skip of player.skipped || [])lines.push(`${player.player}: ${skip}`);
        if(Array.isArray(row.skipped))for(const skip of row.skipped)lines.push(`Remaining: ${skip.title || skip} — ${skip.reason || "Unavailable"}`);
        else if(row.skipped)lines.push(`${row.skipped} entries skipped`);
      }
      for(const line of value.coverage || [])lines.push(line);
      for(const line of value.limits || [])lines.push(line);
      if(value.state === "finished")lines.push("Save and quit normally, then verify progress in each player's own game.");
      el("fullProgressOutput").textContent=lines.join("\n");update();
    }
    el("fullProgressAck").addEventListener("change",update);
    el("fullProgressPreview").addEventListener("click",async()=>{
      preview=null;update();try{preview=await call("full_progress_preview",{});report(preview);}
      catch(e){report({message:e.message});}
    });
    el("fullProgressStatus").addEventListener("click",async()=>{
      try{const value=await call("full_progress_status",{});if(!busy)job=value;report(value);}
      catch(e){report({message:e.message});}
    });
    el("fullProgressClose").addEventListener("click",async()=>{
      try{job=await call("full_progress_close",{job_id:job.id,acknowledge_shared_progress:el("fullProgressAck").checked});report(job);}
      catch(e){report({message:e.message});}
    });
    el("fullProgressStart").addEventListener("click",async()=>{
      if(el("fullProgressStart").disabled)return;
      busy=true;update();
      try{
        job=await call("full_progress_start",{acknowledge_shared_progress:true});report(job);
        job=await advance(call,job,value=>{job=value;report(value);});
      }catch(e){report({message:"Result unknown: "+e.message+". Check status before retrying."});}
      finally{busy=false;preview=null;update();}
    });
    el("fullProgressContinue").addEventListener("click",async()=>{
      if(el("fullProgressContinue").disabled)return;
      busy=true;update();
      try{job=await advance(call,job,value=>{job=value;report(value);});}
      catch(e){report({message:"Result unknown: "+e.message+". Check status before continuing."});}
      finally{busy=false;preview=null;update();}
    });
    el("fullProgressStop").addEventListener("click",async()=>{
      try{const result=await call("full_progress_cancel",{job_id:job.id});if(!busy)job=result;report(result);}
      catch(e){report({message:e.message});}
    });
    update();
  }
  root.MsbtFullProgressPanel={bind,advance};
  if(typeof module!=="undefined")module.exports={bind,advance};
})(typeof window === "undefined" ? globalThis : window);
