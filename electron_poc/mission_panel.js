(function (root) {
  "use strict";
  async function advance(call, job, stopped, report) {
    return root.MsbtFullProgressPanel.advance(call,job,report,{
      step:"mission_step",status:"mission_status",stopped
    });
  }

  const unavailableNames = new Set(["Mission_Micro_BackMcCrackyPt2", "Mission_Micro_BackMcCrackyPt3"]);
  function splitCoverage(rows = []) {
    const unavailable = rows.filter(m => unavailableNames.has(m.name) && m.state === "unavailable");
    return {unavailable, remaining: rows.filter(m => !unavailable.includes(m))};
  }
  function bind(doc, call, getTarget) {
    root.MsbtFullProgressPanel?.bind(doc, call);
    const el = id => doc.getElementById(id);
    const output = el("missionOutput");
    let job = null, busy = false, stopped = false, preview = null;
    let objectivePreview = null;
    let lastObjective = null;
    let refreshing = false, refreshVersion = 0;
    let catalogRows = [];
    const selectedNames = new Set();
    const stateLabel = row => ({completed:"Completed", active:"In progress", accepted:"Accepted",
      available:"Not started — available", locked:"Not started — locked", failed:"Failed", None:"Not started", null:"Not started",
      unavailable:"Unavailable — status unknown"})[row.state] || "Status unknown";
    function renderNames() {
      const search = el("missionNameSearch").value.trim().toLocaleLowerCase();
      const state = el("missionStateFilter").value, type = el("missionTypeFilter").value;
      const rows = catalogRows.filter(row => (!search || row.title.toLocaleLowerCase().includes(search)) &&
        (type === "all" || row.category === type) && (state === "all" ||
          (state === "progress" ? ["active","accepted"].includes(row.state) :
          state === "not_started" ? ["available","locked","None",null].includes(row.state) :
          state === "unavailable" ? !["active","accepted","available","locked","completed","failed","None",null].includes(row.state) : row.state === state)));
      const sort = el("missionSort").value;
      rows.sort((a,b) => (sort === "status" ? stateLabel(a).localeCompare(stateLabel(b)) :
        sort === "type" ? a.category.localeCompare(b.category) : 0) || a.title.localeCompare(b.title));
      el("missionNames").replaceChildren();
      for (const row of rows) {
        const option = doc.createElement("option");
        option.value=row.name; option.textContent=`${row.title} — ${stateLabel(row)} (${row.category})`;
        option.selected=selectedNames.has(row.name); el("missionNames").append(option);
      }
      const hidden = [...selectedNames].filter(name => !rows.some(row => row.name === name)).length;
      el("missionSelectionCount").textContent=`${rows.length} of ${catalogRows.length} shown; ${selectedNames.size} selected${hidden ? ` (${hidden} hidden by filters — still selected)` : ""}.`;
    }
    const category = () => ["story", "sides", "dlc", "all"].includes(preview?.selection_scope);
    const runnable = () => (preview?.missions || []).filter(m => category() ? !m.excluded : !m.blocked_reason);
    function showUnavailable(rows) {
      const {unavailable} = splitCoverage(rows);
      el("missionUnavailable").hidden = !unavailable.length;
      el("missionUnavailableList").textContent = unavailable.map(m => m.title).join("\n");
    }
    function report(value) {
      const {unavailable, remaining} = splitCoverage(value?.pending || []);
      showUnavailable(value?.pending || []);
      const onlyUnavailable = value?.state === "stopped" && unavailable.length && !remaining.length;
      output.textContent = onlyUnavailable
        ? `Run finished with unavailable entries: ${value.index || 0} missions verified in this lobby. The ${unavailable.length} entries listed separately were not completed.`
        : value?.message || (value?.state === "idle" ? "No mission job is running." : "No confirmed result. Refresh status before retrying.");
      if (value?.excluded?.length) output.textContent += `\n${value.excluded.length} nonpersistent replayable definitions excluded.`;
      if (remaining.length) output.textContent += "\nRemaining: " + remaining.map(m => `${m.title}: ${m.state || "prerequisites unavailable"}`).join("; ");
      if (value?.deferred?.length) output.textContent += "\nDeferred (not completed): " + value.deferred.map(m => `${m.title}: ${m.reason}${m.blocking_players?.length ? " — players without access: " + m.blocking_players.join(", ") : ""}`).join("; ");
      if (value?.remaining_completed?.length) output.textContent += "\nStill completed after reset: " + value.remaining_completed.map(m => m.title).join("; ");
      if (value?.total && !onlyUnavailable) output.textContent += `\n${value.verified_count ?? value.index ?? 0} / ${value.total} ${value.unit || "missions"} verified in this lobby.`;
    }
    function update() {
      const eligible = preview?.ok && runnable().length > 0 && runnable().length <= preview.max_batch;
      const resetting = runnable().some(m => m.resets_host_completion);
      el("missionRunBtn").textContent = ["map_locations", "travel_stations", "travel_requirements"].includes(el("missionScope").value) ? "Apply map / travel changes" : el("missionScope").value === "bounty" ? "Complete bounty" : el("missionScope").value === "challenge_credit" ? "Repair Grassroots credit" : "Complete missions";
      el("missionRunBtn").disabled = busy || !eligible || !el("missionSharedAck").checked || (resetting && !el("missionResetCompleted").checked);
      el("missionResumeBtn").disabled = busy || !job?.id || !(job.state === "running" || (job.state === "stopped" && !(job?.pending?.length > 0 && splitCoverage(job.pending).remaining.length === 0) && (["accept", "complete"].includes(job?.phase) || (job?.dynamic && job?.phase === "prepare")) && (job?.operation_scope || "missions") === "missions"));
      el("missionCancelBtn").disabled = !busy || !job?.id;
      const recoverable = !busy && job?.id && !job.closed && ["uncertain", "stopped", "interrupted"].includes(job.state);
      el("missionRecoverBtn").disabled = !recoverable || job.state === "interrupted" || !el("missionSharedAck").checked;
      el("missionCloseBtn").disabled = !recoverable || !el("missionSharedAck").checked;
      el("missionDlcBtn").disabled = busy;
      el("missionPreviewBtn").disabled = busy;
      el("missionScope").disabled = busy;
      el("missionNames").disabled = busy;
      for (const id of ["missionNameSearch","missionStateFilter","missionTypeFilter","missionSort","missionClearSelectionBtn"]) el(id).disabled=busy;
      el("missionReopenBtn").disabled = busy || !el("missionSharedAck").checked ||
        !["named", "current"].includes(el("missionScope").value) ||
        preview?.missions?.length !== 1 || !["completed","active","accepted"].includes(preview.missions[0].state);
      el("missionRestartLastBtn").disabled=busy || !el("missionSharedAck").checked || !lastObjective?.restart_supported;
      el("missionReplayObjectiveBtn").disabled=busy || !el("missionSharedAck").checked || !lastObjective?.replay_supported;
      el("missionResetAllBtn").disabled=busy || !el("missionSharedAck").checked;
      el("missionObjectiveBtn").disabled = busy || !el("missionSharedAck").checked ||
        !objectivePreview?.ok || !el("missionObjectiveSelect").value;
      el("missionObjectiveSelect").disabled = busy;
      el("missionResetOption").hidden = !resetting;
      if (refreshing) for (const id of ["missionRunBtn","missionReopenBtn","missionObjectiveBtn"]) el(id).disabled=true;
      el("missionActionHint").textContent = refreshing ? "Reading current mission progress…" : busy ? "Run in progress. You can stop remaining work below." :
        !preview?.ok ? "Choose a mission to see available actions." : !el("missionSharedAck").checked ? "Check Allow changes to shared lobby progress to enable actions." :
        resetting && !el("missionResetCompleted").checked ? "This selection includes completed missions. Reopen one to play it again, or enable Include completed missions to complete them for guests." :
        "Complete objective advances only the selected step. Complete mission finishes it. Reopen makes it playable again.";
    }
    async function refresh() {
      const version = ++refreshVersion;
      refreshing=true;
      preview = null; objectivePreview=null; el("missionObjectiveSelect").replaceChildren(); update();
      const scope = el("missionScope").value;
      try {
        const names = [...selectedNames];
        if (scope === "named") {
          const catalog = await call("mission_preview", { scope: "all" });
          if(version !== refreshVersion) return;
          if (!catalog?.ok) { report(catalog); return; }
          catalogRows = catalog.missions;
          const type = el("missionTypeFilter").value;
          el("missionTypeFilter").replaceChildren();
          for (const value of ["all", ...new Set(catalogRows.map(row => row.category).sort())]) {
            const option=doc.createElement("option"); option.value=value;
            option.textContent=value === "all" ? "All types" : value;
            el("missionTypeFilter").append(option);
          }
          el("missionTypeFilter").value=type || "all";
          renderNames();
        }
        if (scope === "named" && !names.length) {
          output.textContent = "Choose missions. Available actions update automatically.";
          el("missionPreviewList").textContent = "No missions selected."; return;
        }
        const nextPreview = await call("mission_preview", { scope, missions: names });
        if(version !== refreshVersion) return;
        preview = nextPreview;
        if (!preview?.ok) { report(preview); el("missionPreviewList").textContent = preview?.message || "Mission preview unavailable."; return; }
        showUnavailable(preview.missions);
        el("missionPreviewList").textContent = splitCoverage(preview.missions).remaining.map(m => `${m.title}: ${m.state}${m.blocked_reason ? " — " + m.blocked_reason : m.resets_host_completion ? " — host reset required" : ""}`).join("\n");
        el("missionPreviewList").style.whiteSpace = "pre-line";
        output.textContent = category() ? `${preview.missions.length} catalog entries: ${runnable().length} queued, including locked missions to recheck as progress unlocks them; ${preview.excluded_total} nonpersistent replayable definitions excluded.` : `${runnable().length} entries ready; ${preview.missions.length - runnable().length} unavailable entries will be skipped. Review shared-progress options before running.`;
        if (preview.missions.length===1 && preview.missions[0].state==='active' && ["named","current","bounty"].includes(scope)) {
          const nextObjectives=await call("mission_objective_preview",{scope,missions:scope==='named'?names:undefined});
          if(version !== refreshVersion) return;
          objectivePreview=nextObjectives;
          if(objectivePreview?.ok) for(const row of objectivePreview.objectives) {
            const option=doc.createElement("option");option.value=row.token;option.textContent=row.title;
            el("missionObjectiveSelect").append(option);
          }
          el("missionObjectiveNote").textContent=objectivePreview?.message || "No active objective found.";
        }
      } catch (error) { output.textContent = `Could not connect to the mission action: ${error.message}`; }
      finally { if(version === refreshVersion) {refreshing=false;update();} }
    }
    el("missionPreviewBtn").addEventListener("click", refresh);
    el("missionObjectiveSelect").addEventListener("change",update);
    async function settleObjective(result) {
      // Read readiness; never repeat a completion or replay request.
      for(let attempt=0; attempt<20 && result?.id && ["running","uncertain"].includes(result.state); attempt++) {
        report(result);
        await new Promise(resolve=>root.setTimeout(resolve,250));
        const next=await call("mission_objective_status",{});
        if(next?.id !== result.id) return next;
        result=next;
      }
      return result;
    }
    el("missionObjectiveBtn").addEventListener("click",async()=>{
      if(el("missionObjectiveBtn").disabled)return;
      busy=true;update();
      try {
        const result=await call("mission_objective_complete",{preview_id:objectivePreview.preview_id,
          objective_token:el("missionObjectiveSelect").value,acknowledge_shared_progress:el("missionSharedAck").checked});
        lastObjective=await settleObjective(result);objectivePreview=null;
        if(lastObjective?.ok) await refresh();
        report(lastObjective);
      } catch(error) {output.textContent=`Objective result unconfirmed: ${error.message}. Check objective status.`;}
      finally {busy=false;update();}
    });
    el("missionObjectiveStatusBtn").addEventListener("click",async()=>{
      try {lastObjective=await call("mission_objective_status",{});report(lastObjective);update();}catch(error){output.textContent=error.message;}
    });
    el("missionReplayObjectiveBtn").addEventListener("click",async()=>{
      if(el("missionReplayObjectiveBtn").disabled)return;
      busy=true;update();
      try {
        lastObjective=await call("mission_objective_replay",{acknowledge_shared_progress:el("missionSharedAck").checked});
        objectivePreview=null;
        lastObjective=await settleObjective(lastObjective);
        if(lastObjective?.ok) await refresh();
        report(lastObjective);
      }catch(error){output.textContent=`Replay result unconfirmed: ${error.message}. Check last objective before trying another action.`;}
      finally{busy=false;update();}
    });
    for(const [button,mode] of [["missionRestartLastBtn","reopen"],["missionResetAllBtn","reset_completed"]]) {
      el(button).addEventListener("click",async()=>{
        if(el(button).disabled)return;
        busy=true;stopped=false;update();
        try {
          const target=getTarget();
          job=await call("mission_start",{scope:mode==="reopen"?"named":"all",mode,
            missions:mode==="reopen"?[lastObjective.mission]:undefined,
            reset_completed:true,acknowledge_shared_progress:el("missionSharedAck").checked,
            target_scope:target?"selected":"local",target_player:target||undefined});
          report(job);
          job=await advance(call,job,()=>stopped,next=>{job=next;report(next);update();});
        }catch(error){output.textContent=`Result unconfirmed: ${error.message}. Check job status.`;}
        finally{busy=false;preview=null;objectivePreview=null;lastObjective=null;update();}
      });
    }
    el("missionScope").addEventListener("change", () => {
      preview = null; el("missionNamesLabel").hidden = el("missionScope").value !== "named"; update(); void refresh();
    });
    function selectionChanged() { preview=null; objectivePreview=null; el("missionObjectiveSelect").replaceChildren(); renderNames(); update(); void refresh(); }
    el("missionNames").addEventListener("change", () => {
      for (const option of el("missionNames").options) {
        if(option.selected) selectedNames.add(option.value); else selectedNames.delete(option.value);
      }
      selectionChanged();
    });
    el("missionClearSelectionBtn").addEventListener("click",()=>{selectedNames.clear();selectionChanged();});
    el("missionNameSearch").addEventListener("input",renderNames);
    for(const id of ["missionStateFilter","missionTypeFilter","missionSort"]) el(id).addEventListener("change",renderNames);
    for (const id of ["missionSharedAck", "missionResetCompleted"]) el(id).addEventListener("change", update);
    el("missionStatusBtn").addEventListener("click", async () => {
      try { const result = await call("mission_status", {}); if (!busy && result?.id) job = result; report(result); update(); }
      catch (error) { output.textContent = error.message; }
    });
    el("missionDlcBtn").addEventListener("click", async () => {
      try {
        const result = await call("mission_dlc_status", {});
        output.textContent = result.ok ? result.packs.map(p => `${p.title}: ${p.allowed ? "all players have access" : p.reason}`).join("\n") + "\nPlayers listed lack access according to the game. They can enable their content or leave the lobby before you start a DLC-only run. Nobody is removed automatically." : result.message;
      } catch (error) { output.textContent = error.message; }
    });
    for (const [button, mode] of [["missionRecoverBtn", "continue"], ["missionCloseBtn", "close"]]) {
      el(button).addEventListener("click", async () => {
        if (el(button).disabled) return;
        busy = true; stopped = false; update();
        try {
          const target = getTarget();
          const result = await call("mission_recover", {job_id:job.id, mode,
            acknowledge_shared_progress:el("missionSharedAck").checked,
            target_scope:target ? "selected" : "local", target_player:target || undefined});
          if (!result.ok) { report(result); return; }
          job=result; report(job);
          if (mode === "continue") job=await advance(call,job,()=>stopped,next=>{job=next;report(next);update();});
        } catch (error) { output.textContent = `Recovery not confirmed: ${error.message}. Check job status.`; }
        finally { busy=false;preview=null;update(); }
      });
    }
    el("missionRunBtn").addEventListener("click", async () => {
      if (el("missionRunBtn").disabled) return;
      busy = true; stopped = false; update();
      try {
        const target = getTarget();
        job = await call("mission_start", { scope: preview.selection_scope === "bounty" ? "bounty" : category() ? preview.selection_scope : ["map_locations", "travel_stations", "travel_requirements"].includes(preview.scope) ? preview.scope : "named", missions: runnable().map(m => m.name),
          target_scope: target ? "selected" : "local", target_player: target || undefined,
          acknowledge_shared_progress: el("missionSharedAck").checked, reset_completed: el("missionResetCompleted").checked });
        report(job); update();
        job = await advance(call, job, () => stopped, next => { job = next; report(next); update(); });
      } catch (error) { stopped = true; output.textContent = `Result not confirmed: ${error.message}. Check job status before retrying.`; }
      finally { busy = false; preview = null; update(); }
    });
    el("missionReopenBtn").addEventListener("click", async () => {
      if (el("missionReopenBtn").disabled) return;
      busy = true; stopped = false; update();
      try {
        const target = getTarget();
        job = await call("mission_start", {scope:"named", mode:"reopen",
          missions:preview.missions.map(m=>m.name), reset_completed:true,
          acknowledge_shared_progress:el("missionSharedAck").checked,
          target_scope:target ? "selected" : "local", target_player:target || undefined});
        report(job);
        job = await advance(call, job, () => stopped, next => {job=next;report(next);update();});
      } catch(error) { output.textContent = `Reopen result unconfirmed: ${error.message}. Check job status.`; }
      finally { busy=false;preview=null;objectivePreview=null;update(); }
    });
    el("missionResumeBtn").addEventListener("click", async () => {
      if (el("missionResumeBtn").disabled) return;
      busy = true; stopped = false; update();
      try {
        const current = await call("mission_status", {});
        if(current?.id !== job.id){report({message:"Could not recover this batch status; try again when connected."});return;}
        job=current;
        if(job.state === "stopped") job = await call("mission_resume", {job_id: job.id});
        report(job);
        job = await advance(call, job, () => stopped, next => {job = next; report(next); update();});
      } catch (error) { stopped = true; output.textContent = `Result not confirmed: ${error.message}. Check job status.`; }
      finally { busy = false; preview = null; update(); }
    });
    el("missionCancelBtn").addEventListener("click", async () => {
      try { const result = await call("mission_cancel", { job_id: job.id });
        if (result.ok) stopped = result.state !== "running";
        report(result); }
      catch (error) { output.textContent = `Cancellation not confirmed: ${error.message}. Check job status.`; }
    });
    update();
    void call("mission_status", {}).then(result=>{if(!busy){job=result;report(result);update();}}).catch(()=>{}).finally(()=>{if(!busy)void refresh();});
  }
  root.MsbtMissionPanel = { bind, advance, splitCoverage };
  if (typeof module !== "undefined") module.exports = { bind, advance, splitCoverage };
})(typeof window === "undefined" ? globalThis : window);
