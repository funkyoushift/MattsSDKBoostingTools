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
  function renderPracticeChoices(doc, preview, previous = "") {
    const select = doc.getElementById("missionPracticeSelect");
    const details = doc.getElementById("missionPracticeUnavailable");
    const list = doc.getElementById("missionPracticeUnavailableList");
    const choices = preview?.ok ? preview.choices || [] : [];
    const saveMode=doc.getElementById('missionReplayMethod')?.value==='save';
    const reason=row=>saveMode?(row.save_backed_reason||(!row.save_backed_supported?'No reviewed save-backed setup for this section':null)):row.blocked_reason;
    const available = choices.filter(row => !reason(row));
    const blocked = choices.filter(row => reason(row));
    select.replaceChildren();
    for (const row of available) {
      const option = doc.createElement("option");
      option.value = String(row.index); option.textContent = `${available.indexOf(row) + 1}. ${row.title}${row.index>0 || row.anchor?.recorded ? " — Experimental" : ""}`;
      if(row.index>0 || row.anchor?.recorded)option.className="mission-experimental-option";
      select.append(option);
    }
    if (!available.length) {
      const option = doc.createElement("option"); option.value = "";
      option.textContent = choices.length ? "No checkpoint locations available" : "Choose one mission first";
      select.append(option);
    } else if (available.some(row => String(row.index) === previous)) select.value = previous;
    details.hidden = !blocked.length;
    doc.getElementById("missionPracticeUnavailableSummary").textContent = `${blocked.length} unavailable starting points`;
    list.replaceChildren();
    for (const row of blocked) {
      const item = doc.createElement("li");
      item.textContent = `${row.index + 1}. ${row.title}: ${reason(row) || "Completion location is not resolved"}`;
      list.append(item);
    }
    return available.length;
  }
  function showView(doc, name) {
    if(name==='replay')name='practice';
    if (!["complete", "practice", "replay", "full"].includes(name)) return;
    doc.querySelectorAll("[data-mission-views]").forEach(node => {
      node.hidden = !node.dataset.missionViews.split(" ").includes(name);
    });
    doc.querySelectorAll("[data-mission-view-button]").forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.missionViewButton === name));
    });
    doc.dispatchEvent(new root.CustomEvent("msbt-mission-view",{detail:name}));
  }
  function revealControl(node) {
    const view = node?.closest("[data-mission-views]");
    if (view) showView(node.ownerDocument, view.dataset.missionViews.split(" ")[0]);
  }
  function bind(doc, call, getTarget) {
    doc.querySelectorAll("[data-mission-view-button]").forEach(button => {
      button.addEventListener("click", () => showView(doc, button.dataset.missionViewButton));
    });
    root.MsbtFullProgressPanel?.bind(doc, call);
    const el = id => doc.getElementById(id);
    async function dialogueSkip(action) {
      const button = el("dialogueSkipToggle");
      if (!button) return;
      button.disabled = true;
      try {
        const result = await call("quick_menu_action", {action});
        if (typeof result?.enabled === "boolean") {
          button.setAttribute("aria-pressed", String(result.enabled));
          button.textContent = `Dialogue skip: ${result.enabled ? "on" : "off"}`;
        }
        el("dialogueSkipNote").textContent = result?.message || "Dialogue skip status unavailable. Check again before toggling.";
      } catch (error) {
        el("dialogueSkipNote").textContent = `Dialogue skip result unknown: ${error.message}. Check status before toggling again.`;
      } finally { button.disabled = false; }
    }
    el("dialogueSkipToggle")?.addEventListener("click", () => dialogueSkip("dialogue_skip_toggle"));
    el("dialogueSkipStatus")?.addEventListener("click", () => dialogueSkip("dialogue_skip_status"));
    const output = el("missionOutput");
    let job = null, busy = false, stopped = false, preview = null, activeOperation = null;
    let missionPump = null, cancelling = false;
    async function pumpMission() {
      if (missionPump) return missionPump;
      update();
      const pending=advance(call, job, () => stopped, next => {job=next;report(next);update();});
      missionPump=pending;
      try {return await pending;} finally {if(missionPump===pending)missionPump=null;}
    }
    let objectivePreview = null;
    let practicePreview = null, practiceJob = null, practiceStopped = false;
    let saveReplayPanel=null;
    let lastObjective = null, objectiveStopped = false;
    let refreshing = false, refreshVersion = 0;
    let catalogRows = [];
    const selectedNames = new Set();
    let replayFiltersInitialized=false;
    const playthrough=root.MsbtMissionPlaythrough||{};
    const campaignFilter=el('missionCampaignFilter');
    if(campaignFilter){
      const labels=new Map();
      for(const info of Object.values(playthrough))labels.set(info.campaign,info.label.replace(/ \d+$/,''));
      for(const [key,label] of labels){const option=doc.createElement('option');option.value=key;option.textContent=label;campaignFilter.append(option);}
    }
    doc.addEventListener("msbt-mission-view",event=>{
      const single=["practice","replay"].includes(event.detail);
      if(single&&!replayFiltersInitialized&&campaignFilter){
        campaignFilter.value='story';el('missionTypeFilter').value='all';el('missionStateFilter').value='all';
        replayFiltersInitialized=true;
      }
      if(el('missionCampaignLabel'))el('missionCampaignLabel').hidden=!single;
      el("missionNames").multiple=!single;
      for(const option of el("missionScope").options)option.hidden=single && !["current","named"].includes(option.value);
      let changed=false;
      if(single && selectedNames.size>1){
        const retained=[...selectedNames][0];selectedNames.clear();selectedNames.add(retained);renderNames();changed=true;
      }
      if(single && el("missionScope").value!=="named"){
        el("missionScope").value="named";changed=true;
      }
      if(single){
        const before=[...selectedNames].join('|');renderNames();
        if(before!==[...selectedNames].join('|'))changed=true;
      }
      el('missionNamesLabel').hidden=el('missionScope').value!=='named';
      el('missionScope').closest('label').hidden=single;
      if(changed)void refresh();
    });
    const stateLabel = row => ({completed:"Completed", active:"In progress", accepted:"Accepted",
      available:"Not started — available", locked:"Not started — locked", failed:"Failed", None:"Not started", null:"Not started",
      unavailable:"Unavailable — status unknown"})[row.state] || "Status unknown";
    function renderNames() {
      const search = el("missionNameSearch").value.trim().toLocaleLowerCase();
      const state = el("missionStateFilter").value, type = el("missionTypeFilter").value;
      const rows = catalogRows.filter(row => (!search || row.title.toLocaleLowerCase().includes(search)) &&
        (!campaignFilter||campaignFilter.value==='all'||playthrough[row.name]?.campaign===campaignFilter.value) &&
        (type === "all" || row.category === type) && (state === "all" ||
          (state === "progress" ? ["active","accepted"].includes(row.state) :
          state === "not_started" ? ["available","locked","None",null].includes(row.state) :
          state === "unavailable" ? !["active","accepted","available","locked","completed","failed","None",null].includes(row.state) : row.state === state)));
      const sort = el("missionSort").value;
      rows.sort((a,b) => (sort === "status" ? stateLabel(a).localeCompare(stateLabel(b)) :
        sort === "type" ? a.category.localeCompare(b.category) :
        sort === "playthrough" ? (playthrough[a.name]?.rank??100000)-(playthrough[b.name]?.rank??100000) : 0) || a.title.localeCompare(b.title));
      if(!el('missionNames').multiple){
        const visible=new Set(rows.map(row=>row.name));
        for(const name of selectedNames)if(!visible.has(name))selectedNames.delete(name);
      }
      el("missionNames").replaceChildren();
      for (const row of rows) {
        const option = doc.createElement("option");
        const sequence=playthrough[row.name];
        option.value=row.name; option.textContent=`${sequence?sequence.label+' · ':''}${row.title} — ${stateLabel(row)}${sequence?.parallel?' · parallel route':''} (${row.category})`;
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
      if (value?.excluded?.length) output.textContent += `\n${value.excluded.length} repeatable or unused mission entries excluded from automatic completion.`;
      if (remaining.length) output.textContent += "\nRemaining: " + remaining.map(m => `${m.title}: ${m.state || "prerequisites unavailable"}`).join("; ");
      if (value?.deferred?.length) output.textContent += "\nDeferred (not completed): " + value.deferred.map(m => `${m.title}: ${m.reason}${m.blocking_players?.length ? " — players without access: " + m.blocking_players.join(", ") : ""}`).join("; ");
      if (value?.remaining_completed?.length) output.textContent += "\nStill completed after reset: " + value.remaining_completed.map(m => m.title).join("; ");
      if (value?.total && !onlyUnavailable) output.textContent += `\n${value.verified_count ?? value.index ?? 0} / ${value.total} ${value.unit || "missions"} verified in this lobby.`;
    }
    function update() {
      const objectiveActive = lastObjective?.coordinated && lastObjective?.id && ["running","uncertain","stopped","interrupted"].includes(lastObjective.state);
      const eligible = preview?.ok && runnable().length > 0 && runnable().length <= preview.max_batch;
      const resetting = runnable().some(m => m.resets_host_completion);
      el("missionRunBtn").textContent = ["map_locations", "travel_stations", "travel_requirements"].includes(el("missionScope").value) ? "Apply map / travel changes" : el("missionScope").value === "bounty" ? "Complete bounty" : el("missionScope").value === "challenge_credit" ? "Repair mission credit" : "Complete missions";
      el("missionRunBtn").disabled = busy || !eligible || !el("missionSharedAck").checked || (resetting && !el("missionResetCompleted").checked);
      el("missionResumeBtn").disabled = busy || !job?.id || !(job.state === "running" || (job.state === "stopped" && !(job?.pending?.length > 0 && splitCoverage(job.pending).remaining.length === 0) && (["accept", "complete"].includes(job?.phase) || (job?.dynamic && job?.phase === "prepare")) && (job?.operation_scope || "missions") === "missions"));
      const practiceActive = activeOperation === "practice" || (!busy && practiceJob?.id && ["running","uncertain","stopped"].includes(practiceJob.state));
      const placementRecovery = job?.completion_context?.placement && ["uncertain","stopped"].includes(job.state);
      el("missionCancelBtn").textContent = objectiveActive ? "Stop objective setup" : practiceActive ? "Stop replay setup" : placementRecovery ? "Restore player movement" : "Stop run";
      el("missionCancelBtn").disabled = objectiveActive ? cancelling || lastObjective.state==="interrupted" : practiceActive ? !practiceJob?.id :
        cancelling || (busy && activeOperation !== "mission") || !job?.id || (job.state !== "running" && !placementRecovery);
      const recoverable = !busy && job?.id && !job.closed && ["uncertain", "stopped", "interrupted"].includes(job.state);
      el("missionRecoverBtn").disabled = !recoverable || job.state === "interrupted" || !el("missionSharedAck").checked;
      el("missionCloseBtn").disabled = !recoverable || !el("missionSharedAck").checked;
      if (objectiveActive) {
        el("missionResumeBtn").disabled=busy || lastObjective.state!=="running";
        el("missionRecoverBtn").disabled=busy || lastObjective.state==="interrupted" || !el("missionSharedAck").checked;
        el("missionCloseBtn").disabled=busy || !el("missionSharedAck").checked;
      }
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
      const choice=practicePreview?.choices?.find(row=>String(row.index)===el("missionPracticeSelect").value);
      el("missionPracticeBtn").textContent=practiceJob?.state==="running"?"Continue replay setup":choice?.beginning?"Replay mission":"Replay from selected objective";
      el("missionPracticeBtn").disabled=busy || refreshing || !el("missionSharedAck").checked ||
        (practiceJob?.state!=="running" && (!practicePreview?.ok || !choice || choice.blocked_reason));
      el("missionPracticeStop").disabled=!practiceJob?.id || !["running","uncertain","stopped"].includes(practiceJob.state);
      el("missionPracticeSelect").disabled=busy || refreshing || !practicePreview?.choices?.some(row=>!row.blocked_reason);
      el("missionPracticeNote").textContent=choice?.blocked_reason || (choice?.anchor?.recorded ?
        `Recorded beginning: ${choice.anchor.map}. Resets progress and reloads the area. Replay gameplay is still experimental; placement requires a loaded, walkable surface.` : choice?.beginning ?
        "Restart this mission at its normal opening. The whole lobby travels together; character rewards are retained." : choice?.anchor ?
        `Start: ${choice.anchor.map}, where ${choice.anchor.objective.replaceAll("_"," ")} finishes. Moves everyone together.` :
        choice ? "Replay activates this objective and prepares its mission area. Follow the mission waypoint when no precise jump location is available." :
        refreshing ? "Reading checkpoint locations…" : practicePreview?.ok ?
        "No starting point is ready. Open unavailable starting points below for the reason." :
        practicePreview?.message || "Choose one mission to see its available starting points.");
      el("missionResetOption").hidden = !resetting;
      saveReplayPanel?.update();
      if (refreshing) for (const id of ["missionRunBtn","missionReopenBtn","missionObjectiveBtn"]) el(id).disabled=true;
      if (objectiveActive) for (const id of ["missionRunBtn","missionReopenBtn","missionObjectiveBtn","missionReplayObjectiveBtn","missionRestartLastBtn","missionResetAllBtn","missionPracticeBtn"]) el(id).disabled=true;
      if (practiceActive || (!busy && job?.state==="running")) {
        for(const id of ["missionRunBtn","missionReopenBtn","missionObjectiveBtn","missionReplayObjectiveBtn","missionRestartLastBtn","missionResetAllBtn"])el(id).disabled=true;
        if(!practiceActive)el("missionPracticeBtn").disabled=true;
      }
      el("missionActionHint").textContent = refreshing ? "Reading current mission progress…" : busy ? "Run in progress. You can stop remaining work below." :
        !preview?.ok ? "Choose a mission to see available actions." : !el("missionSharedAck").checked ? "Check Allow changes to shared lobby progress to enable actions." :
        resetting && !el("missionResetCompleted").checked ? "This selection includes completed missions. Reopen one to play it again, or enable Include completed missions to complete them for guests." :
        "Complete objective advances only the selected step. Complete mission finishes it. Reopen makes it playable again.";
    }
    async function syncStatuses() {
      const actions=["mission_status","mission_objective_status","mission_practice_status"];
      const before=[job,lastObjective,practiceJob].map(value=>`${value?.id||""}:${value?.state||""}`).join("|");
      const results=await Promise.allSettled(actions.map(action=>call(action,{})));
      if(busy)return false;
      const valid=result=>result.status==="fulfilled" && result.value?.state && (result.value.id || result.value.state==="idle");
      if(valid(results[0]))job=results[0].value;
      if(valid(results[1]))lastObjective=results[1].value;
      if(valid(results[2]))practiceJob=results[2].value;
      update();
      return before!==[job,lastObjective,practiceJob].map(value=>`${value?.id||""}:${value?.state||""}`).join("|");
    }
    async function refresh() {
      const version = ++refreshVersion;
      const previousPractice = {mission:practicePreview?.mission, value:el("missionPracticeSelect").value};
      refreshing=true;
      preview = null; objectivePreview=null; practicePreview=null;
      el("missionObjectiveSelect").replaceChildren(); renderPracticeChoices(doc,null); update();
      const scope = el("missionScope").value;
      try {
        await syncStatuses();
        if(version!==refreshVersion)return;
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
        output.textContent = category() ? `${preview.missions.length} catalog entries: ${runnable().length} queued, including locked missions to recheck as progress unlocks them; ${preview.excluded_total} repeatable or unused entries excluded from automatic completion.` : `${runnable().length} entries ready; ${preview.missions.length - runnable().length} unavailable entries will be skipped. Review shared-progress options before running.`;
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
        if (preview.missions.length===1 && ["named","current"].includes(scope)) {
          const nextPractice=await call("mission_practice_preview",{scope,missions:scope==="named"?names:undefined});
          if(version !== refreshVersion)return;
          practicePreview=nextPractice;
          renderPracticeChoices(doc,practicePreview,previousPractice.mission===practicePreview?.mission ? previousPractice.value : "");
        }
      } catch (error) { output.textContent = `Could not connect to the mission action: ${error.message}`; }
      finally { if(version === refreshVersion) {refreshing=false;update();} }
    }
    el("missionPreviewBtn").addEventListener("click", refresh);
    el("missionObjectiveSelect").addEventListener("change",update);
    el("missionPracticeSelect").addEventListener("change",update);
    async function refreshPracticeStatus() {
      try{practiceJob=await call("mission_practice_status",{});if(practiceJob?.id)report(practiceJob);update();}
      catch(error){output.textContent=error.message;}
    }
    el("missionPracticeStatus").addEventListener("click",refreshPracticeStatus);
    void refreshPracticeStatus();
    el("missionPracticeBtn").addEventListener("click",async()=>{
      if(el("missionPracticeBtn").disabled)return;
      if(saveReplayPanel?.saveMode()){await saveReplayPanel.start();return;}
      busy=true;activeOperation="practice";practiceStopped=false;update();
      try {
        const retained=await call("mission_practice_status",{});
        if(retained?.id && ["running","uncertain","stopped"].includes(retained.state))practiceJob=retained;
        else practiceJob=await call("mission_practice_start",{preview_id:practicePreview.preview_id,
          checkpoint:Number(el("missionPracticeSelect").value),acknowledge_shared_progress:el("missionSharedAck").checked});
        report(practiceJob);update();
        practiceJob=await root.MsbtFullProgressPanel.advance(call,practiceJob,next=>{practiceJob=next;report(next);update();},
          {step:"mission_practice_step",status:"mission_practice_status",stopped:()=>practiceStopped});
        if(practiceJob?.state==="completed")await refresh();
        report(practiceJob);
      }catch(error){output.textContent=`Replay setup result unconfirmed: ${error.message}. Read status before repeating it.`; await refreshPracticeStatus();}
      finally{busy=false;activeOperation=null;update();}
    });
    async function stopPractice(){
      if (!practiceJob?.id) return;
      practiceStopped=true;
      try{practiceJob=await call("mission_practice_cancel",{job_id:practiceJob.id});report(practiceJob);update();}
      catch(error){output.textContent=error.message;}
    }
    el("missionPracticeStop").addEventListener("click",stopPractice);
    async function settleObjective(result) {
      if(result?.coordinated) {
        lastObjective=result;report(result);update();
        return root.MsbtFullProgressPanel.advance(call,result,next=>{lastObjective=next;report(next);update();},
          {step:"mission_objective_step",status:"mission_objective_status",stopped:()=>objectiveStopped});
      }
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
      busy=true;activeOperation="objective";objectiveStopped=false;update();
      try {
        const result=await call("mission_objective_complete",{preview_id:objectivePreview.preview_id,
          objective_token:el("missionObjectiveSelect").value,acknowledge_shared_progress:el("missionSharedAck").checked});
        lastObjective=await settleObjective(result);objectivePreview=null;
        if(lastObjective?.ok) await refresh();
        report(lastObjective);
      } catch(error) {output.textContent=`Objective result unconfirmed: ${error.message}. Check objective status.`;}
      finally {busy=false;activeOperation=null;update();}
    });
    el("missionObjectiveStatusBtn").addEventListener("click",async()=>{
      try {lastObjective=await call("mission_objective_status",{});report(lastObjective);update();}catch(error){output.textContent=error.message;}
    });
    el("missionReplayObjectiveBtn").addEventListener("click",async()=>{
      if(el("missionReplayObjectiveBtn").disabled)return;
      busy=true;activeOperation="objective";objectiveStopped=false;update();
      try {
        lastObjective=await call("mission_objective_replay",{acknowledge_shared_progress:el("missionSharedAck").checked});
        objectivePreview=null;
        lastObjective=await settleObjective(lastObjective);
        if(lastObjective?.ok) await refresh();
        report(lastObjective);
      }catch(error){output.textContent=`Replay result unconfirmed: ${error.message}. Check last objective before trying another action.`;}
      finally{busy=false;activeOperation=null;update();}
    });
    for(const [button,mode] of [["missionRestartLastBtn","reopen"],["missionResetAllBtn","reset_completed"]]) {
      el(button).addEventListener("click",async()=>{
        if(el(button).disabled)return;
        busy=true;activeOperation="mission";stopped=false;update();
        try {
          const target=getTarget();
          job=await call("mission_start",{scope:mode==="reopen"?"named":"all",mode,
            missions:mode==="reopen"?[lastObjective.mission]:undefined,
            reset_completed:true,acknowledge_shared_progress:el("missionSharedAck").checked,
            target_scope:target?"selected":"local",target_player:target||undefined});
          report(job);
          job=await pumpMission();
        }catch(error){output.textContent=`Result unconfirmed: ${error.message}. Check job status.`;}
        finally{busy=false;activeOperation=null;preview=null;objectivePreview=null;lastObjective=null;update();}
      });
    }
    el("missionScope").addEventListener("change", () => {
      preview = null; el("missionNamesLabel").hidden = el("missionScope").value !== "named"; update(); void refresh();
    });
    function selectionChanged() { preview=null; objectivePreview=null; el("missionObjectiveSelect").replaceChildren(); renderNames(); update(); void refresh(); }
    el("missionNames").addEventListener("change", () => {
      if(!el('missionNames').multiple)selectedNames.clear();
      for (const option of el("missionNames").options) {
        if(option.selected) selectedNames.add(option.value); else selectedNames.delete(option.value);
      }
      selectionChanged();
    });
    el("missionClearSelectionBtn").addEventListener("click",()=>{selectedNames.clear();selectionChanged();});
    function filterChanged(){
      const before=[...selectedNames].join('|');renderNames();
      if(before!==[...selectedNames].join('|'))selectionChanged();
    }
    el("missionNameSearch").addEventListener("input",filterChanged);
    for(const id of ["missionStateFilter","missionTypeFilter","missionSort"]) el(id).addEventListener("change",filterChanged);
    campaignFilter?.addEventListener('change',filterChanged);
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
        if(lastObjective?.coordinated && ["running","uncertain","stopped","interrupted"].includes(lastObjective.state)) {
          busy=true;activeOperation="objective";objectiveStopped=false;update();
          try {
            lastObjective=await call("mission_objective_recover",{job_id:lastObjective.id,mode,
              acknowledge_shared_progress:el("missionSharedAck").checked});
            if(mode==="continue")lastObjective=await settleObjective(lastObjective);
            report(lastObjective);
          }catch(error){output.textContent=`Objective recovery not confirmed: ${error.message}. Check objective status.`;}
          finally{busy=false;activeOperation=null;update();}
          return;
        }
        busy = true;activeOperation="mission"; stopped = false; update();
        try {
          const target = getTarget();
          const result = await call("mission_recover", {job_id:job.id, mode,
            acknowledge_shared_progress:el("missionSharedAck").checked,
            target_scope:target ? "selected" : "local", target_player:target || undefined});
          if (!result.ok) { report(result); return; }
          job=result; report(job);
          if (mode === "continue") job=await pumpMission();
        } catch (error) { output.textContent = `Recovery not confirmed: ${error.message}. Check job status.`; }
        finally { busy=false;activeOperation=null;preview=null;update(); }
      });
    }
    el("missionRunBtn").addEventListener("click", async () => {
      if (el("missionRunBtn").disabled) return;
      busy = true;activeOperation="mission"; stopped = false; update();
      try {
        const target = getTarget();
        job = await call("mission_start", { scope: preview.selection_scope === "bounty" ? "bounty" : category() ? preview.selection_scope : ["map_locations", "travel_stations", "travel_requirements"].includes(preview.scope) ? preview.scope : "named", missions: runnable().map(m => m.name),
          target_scope: target ? "selected" : "local", target_player: target || undefined,
          acknowledge_shared_progress: el("missionSharedAck").checked, reset_completed: el("missionResetCompleted").checked });
        report(job); update();
        job = await pumpMission();
      } catch (error) { stopped = true; output.textContent = `Result not confirmed: ${error.message}. Check job status before retrying.`; }
      finally { busy = false;activeOperation=null; preview = null; update(); }
    });
    el("missionReopenBtn").addEventListener("click", async () => {
      if (el("missionReopenBtn").disabled) return;
      busy = true;activeOperation="mission"; stopped = false; update();
      try {
        const target = getTarget();
        job = await call("mission_start", {scope:"named", mode:"reopen",
          missions:preview.missions.map(m=>m.name), reset_completed:true,
          acknowledge_shared_progress:el("missionSharedAck").checked,
          target_scope:target ? "selected" : "local", target_player:target || undefined});
        report(job);
        job = await pumpMission();
      } catch(error) { output.textContent = `Reopen result unconfirmed: ${error.message}. Check job status.`; }
      finally { busy=false;activeOperation=null;preview=null;objectivePreview=null;update(); }
    });
    el("missionResumeBtn").addEventListener("click", async () => {
      if (el("missionResumeBtn").disabled) return;
      if(lastObjective?.coordinated && lastObjective.state==="running") {
        busy=true;activeOperation="objective";objectiveStopped=false;update();
        try{lastObjective=await settleObjective(await call("mission_objective_status",{}));report(lastObjective);}
        finally{busy=false;activeOperation=null;update();}
        return;
      }
      busy = true;activeOperation="mission"; stopped = false; update();
      try {
        const current = await call("mission_status", {});
        if(current?.id !== job.id){report({message:"Could not recover this batch status; try again when connected."});return;}
        job=current;
        if(job.state === "stopped") job = await call("mission_resume", {job_id: job.id});
        report(job);
        job = await pumpMission();
      } catch (error) { stopped = true; output.textContent = `Result not confirmed: ${error.message}. Check job status.`; }
      finally { busy = false;activeOperation=null; preview = null; update(); }
    });
    el("missionCancelBtn").addEventListener("click", async () => {
      if (el("missionCancelBtn").disabled) return;
      if(lastObjective?.coordinated && ["running","uncertain","stopped"].includes(lastObjective.state)) {
        objectiveStopped=true;cancelling=true;update();
        try {
          const ident=lastObjective.id;
          let result=await call("mission_objective_cancel",{job_id:ident});
          if(result?.id!==ident)result=await call("mission_objective_status",{});
          if(result?.id!==ident)throw new Error("This objective's stop could not be confirmed. Its recovery record is retained.");
          lastObjective=result;report(lastObjective);
          if(lastObjective.state==="running" && lastObjective.completion_context?.placement?.stop_state)
            lastObjective=await root.MsbtFullProgressPanel.advance(call,lastObjective,next=>{lastObjective=next;report(next);},
              {step:"mission_objective_step",status:"mission_objective_status"});
        }catch(error){output.textContent=`Objective stop not confirmed: ${error.message}. Check objective status.`;}
        finally{cancelling=false;update();}
        return;
      }
      if (activeOperation === "practice" || (!busy && practiceJob?.id && ["running","uncertain","stopped"].includes(practiceJob.state))) {
        await stopPractice(); return;
      }
      let ownsPump = !busy;
      cancelling=true;
      if (ownsPump) { busy=true; activeOperation="mission"; }
      update();
      try { const result = await call("mission_cancel", { job_id: job.id });
        // Cancellation/cleanup can be confirmed with ok:false because it did
        // not finish the requested mission. Keep its matched state receipt.
        if (result.id === job.id && result.state) { stopped = result.state !== "running"; job = result; }
        report(result); update();
        if (result.id === job.id && result.state === "running" && result.completion_context?.placement?.stop_state) {
          // An in-flight step may finish the old pump while Stop is awaiting
          // its receipt. Join that pump, then reconcile before owning cleanup.
          if (missionPump) await missionPump;
          const current=await call("mission_status",{});
          if(current.id!==result.id)throw new Error("Cleanup job identity changed");
          job=current;report(job);
          if(job.state==="running" && job.completion_context?.placement?.stop_state) {
            ownsPump=true;busy=true;activeOperation="mission";stopped=false;update();
            job=await pumpMission();
          }
        }
      }
      catch (error) { output.textContent = `Cancellation not confirmed: ${error.message}. Check job status.`; }
      finally { cancelling=false;if (ownsPump) {busy=false;activeOperation=null;} update(); }
    });
    update();
    void call("mission_objective_status",{}).then(result=>{if(!busy){lastObjective=result;update();}}).catch(()=>{});
    void call("mission_status", {}).then(result=>{if(!busy){job=result;report(result);update();}}).catch(()=>{}).finally(()=>{if(!busy)void refresh();});
    saveReplayPanel=root.MsbtSaveReplayPanel?.bind(doc,{
      api:root.msbt?.saveReplay,
      selection:()=>({mission:practicePreview?.mission,checkpoint:Number(el('missionPracticeSelect').value),
        supported:practicePreview?.choices?.some(c=>String(c.index)===el('missionPracticeSelect').value&&c.save_backed_supported&&!c.save_backed_reason),
        ack:el('missionSharedAck').checked,busy,refreshing}),
      legacyUpdate:()=>{renderPracticeChoices(doc,practicePreview,el('missionPracticeSelect').value);update();}
    });
    let syncing=false;
    const statusTimer=root.setInterval(async()=>{
      if(syncing || busy || refreshing || doc.hidden || !el("missionToolViews").getClientRects().length ||
          ![job,lastObjective,practiceJob].some(value=>value?.id && value.state==="running"))return;
      syncing=true;
      try{if(await syncStatuses())await refresh();}finally{syncing=false;}
    },1500);
    root.addEventListener("unload",()=>root.clearInterval(statusTimer),{once:true});
  }
  root.MsbtMissionPanel = { bind, advance, splitCoverage, renderPracticeChoices, showView, revealControl };
  if (typeof module !== "undefined") module.exports = root.MsbtMissionPanel;
})(typeof window === "undefined" ? globalThis : window);
