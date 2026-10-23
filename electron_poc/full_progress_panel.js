(function(root){
  "use strict";
  function pollDelay(job){return 50;}
  async function advance(call,job,report,options={}){
    const stepAction=options.step || "full_progress_step", statusAction=options.status || "full_progress_status";
    const stopped=options.stopped || (()=>false);
    // A cancelled mission can still own movement cleanup. Its failure flag
    // describes unfinished mission work; the explicit cleanup state is safe
    // to poll without issuing another objective.
    const canPoll=value=>value?.ok || (["mission_step","mission_objective_step"].includes(stepAction) && value?.completion_context?.placement?.stop_state);
    while(canPoll(job) && job.state === "running" && !stopped()){
      await new Promise(resolve=>setTimeout(resolve,pollDelay(job)));
      const ident=job.id;
      let next;
      try{next=await call(stepAction,{job_id:ident});}catch(e){next={message:e.message};}
      if(next?.id!==ident){
        // The request may already have executed. Read the serialized server
        // status before sending any further step; never restart the batch.
        let reconciled=false;
        for(let attempt=0;attempt<15 && !stopped();attempt++){
          report({...job,message:"Waiting for the game bridge; keeping this run's progress."});
          await new Promise(resolve=>setTimeout(resolve,1000));
          try{next=await call(statusAction,{});}catch(e){next={message:e.message};}
          if(next?.id===ident){reconciled=true;break;}
          if(next?.id)break;
        }
        if(!reconciled){
          report({...job,message:"Bridge status could not be recovered. This run is retained; use Continue run when the bridge is available."});
          return job;
        }
      }
      job=next;report(job);
    }
    return job;
  }
  function bind(doc,call){
    const el=id=>doc.getElementById(id);
    if(!el("fullProgressPanel") || el("fullProgressPanel").dataset.bound)return;
    el("fullProgressPanel").dataset.bound="true";
    let preview=null,job=null,busy=false;
    function acceptStatus(value){
      // A status error without an identity is not proof that a saved run is
      // gone. Keep its recovery controls until the backend confirms idle or
      // returns a specific run record.
      if(value?.ok===true && value.state==="idle"){
        job=null;
        return true;
      }
      if(value?.id && ["running","stopped","uncertain","interrupted","finished","partial","cancelled"].includes(value.state)){
        job=value;
        return true;
      }
      return false;
    }
    function update(){
      const replace=el("fullProgressReplaceWork")?.checked===true;
      const recoveryRun=replace && ["stopped","uncertain","interrupted"].includes(job?.state) && !!job?.id;
      el("fullProgressStart").disabled=busy || el("missionReplayLock")?.hidden===false || job?.state==="running" || (["stopped","uncertain","interrupted"].includes(job?.state) && !recoveryRun) || !preview?.allowed || !el("fullProgressAck").checked;
      el("fullProgressClose").disabled=busy || !job?.id || !["stopped","uncertain","interrupted"].includes(job.state) || !el("fullProgressAck").checked;
      el("fullProgressContinue").textContent=["stopped","uncertain"].includes(job?.state)?"Repair and continue":"Continue run";
      el("fullProgressPreview").disabled=busy;
      el("fullProgressStop").disabled=job?.state !== "running" || !job?.id;
      el("fullProgressContinue").disabled=busy || !["running","stopped","uncertain"].includes(job?.state) || !job?.id || !el("fullProgressAck").checked;
    }
    function report(value){
      const lines=[value.message || value.reason || "No confirmed result."];
      if(value.players)lines.push("Players: "+value.players.join(", "));
      if(value.available_content)lines.push("Available content for this lobby: "+(value.available_content.join(", ") || "Base game; no additional content confirmed"));
      if(value.total)lines.push(`${value.index} / ${value.total} stages finished`);
      for(const row of value.prior_uvh_cleanup || [])lines.push(`Previous ${row.kind || 'UVHM'} work stopped: ${row.message || 'Remaining work closed; applied changes kept.'}`);
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
      if(value.state === "interrupted")lines.push("This saved run cannot be resumed in this session. Close its run record after backend cleanup is confirmed, then check the lobby again before starting another run.");
      el("fullProgressOutput").textContent=lines.join("\n");update();
    }
    el("fullProgressAck").addEventListener("change",update);
    el("fullProgressReplaceWork")?.addEventListener("change",update);
    el("fullProgressPreview").addEventListener("click",async()=>{
      preview=null;update();try{preview=await call("full_progress_preview",{});report(preview);}
      catch(e){report({message:e.message});}
    });
    el("fullProgressStatus").addEventListener("click",async()=>{
      try{const value=await call("full_progress_status",{});if(!busy)acceptStatus(value);report(value);}
      catch(e){report({message:e.message});}
    });
    el("fullProgressClose").addEventListener("click",async()=>{
      try{const result=await call("full_progress_close",{job_id:job.id,acknowledge_shared_progress:el("fullProgressAck").checked});if(result?.id && result?.state){job=result;preview=null;}report(result);}
      catch(e){report({message:e.message});}
    });
    el("fullProgressStart").addEventListener("click",async()=>{
      if(el("fullProgressStart").disabled)return;
      busy=true;update();
      try{
        const replace=el("fullProgressReplaceWork")?.checked===true;
        if(replace && ["stopped","uncertain","interrupted"].includes(job?.state)){
          const previousId=job.id;
          const current=await call("full_progress_status",{});
          if(current?.id!==previousId || !acceptStatus(current) || !["stopped","uncertain","interrupted"].includes(current.state)){
            report({...current,message:"The previous run could not be verified as stopped. No new run was started."});
            return;
          }
          const closed=await call("full_progress_close",{job_id:previousId,acknowledge_shared_progress:true});
          if(closed?.ok!==true){
            job=current;
            report({...closed,message:closed?.message || "The previous run could not be safely closed. No new run was started."});
            return;
          }
          const verified=await call("full_progress_status",{});
          if(!(verified?.ok===true && verified.state==="idle")){
            acceptStatus(verified);
            report({...verified,message:"The previous run has not been confirmed closed. No new run was started."});
            return;
          }
          job=null;
          preview=await call("full_progress_preview",{});
          report(preview);
          if(!preview?.ok || !preview.allowed){
            report({...preview,message:preview?.reason || "Lobby verification failed. No new run was started."});
            return;
          }
        }
        const started=await call("full_progress_start",{acknowledge_shared_progress:true,
          replace_other_progress:replace});
        if(!started?.id || !started?.state){
          // A rejected start must not replace a recoverable run with an error
          // object that has no identifier. Read status; never resend start.
          const current=await call("full_progress_status",{});
          acceptStatus(current);
          report({...current,message:[started?.message,current?.message].filter(Boolean).join(". ")});
          return;
        }
        job=started;report(job);
        job=await advance(call,job,value=>{job=value;report(value);});
      }catch(e){report({message:"Result unknown: "+e.message+". Check status before retrying."});}
      finally{busy=false;preview=null;update();}
    });
    el("fullProgressContinue").addEventListener("click",async()=>{
      if(el("fullProgressContinue").disabled)return;
      busy=true;update();
      try{
        const current=await call("full_progress_status",{});
        if(current?.id!==job.id || !acceptStatus(current)){report({message:"Waiting for this run's verified status. Progress is retained; try Continue run when connected."});return;}
        report(job);
        if(!["running","stopped","uncertain"].includes(job.state))return;
        if(job.state !== "running"){
          const recovered=await call("full_progress_resume",{job_id:job.id,acknowledge_shared_progress:true});
          if(!recovered.ok){report(recovered);return;}
          job=recovered;report(job);
        }
        job=await advance(call,job,value=>{job=value;report(value);});
      }
      catch(e){report({message:"Result unknown: "+e.message+". Check status before continuing."});}
      finally{busy=false;preview=null;update();}
    });
    el("fullProgressStop").addEventListener("click",async()=>{
      try{const result=await call("full_progress_cancel",{job_id:job.id});if(!busy)job=result;report(result);}
      catch(e){report({message:e.message});}
    });
    update();
    call("full_progress_status",{}).then(value=>{
      if(!busy && !job && acceptStatus(value))report(value);
    }).catch(()=>{});
    return update;
  }
  root.MsbtFullProgressPanel={bind,advance,pollDelay};
  if(typeof module!=="undefined")module.exports={bind,advance,pollDelay};
})(typeof window === "undefined" ? globalThis : window);
