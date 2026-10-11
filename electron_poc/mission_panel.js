(function (root) {
  "use strict";
  async function advance(call, job, stopped, report) {
    // Never send a new step after a rejected/unknown transport result.
    while (job?.ok && job.state === "running" && !stopped()) {
      job = await call("mission_step", { job_id: job.id });
      report(job);
      if (!job?.ok || job.state !== "running") break;
      await new Promise(resolve => setTimeout(resolve, 120));
    }
    return job;
  }
  const unavailableNames = new Set(["Mission_Micro_BackMcCrackyPt2", "Mission_Micro_BackMcCrackyPt3"]);
  function splitCoverage(rows = []) {
    const unavailable = rows.filter(m => unavailableNames.has(m.name) && m.state === "unavailable");
    return {unavailable, remaining: rows.filter(m => !unavailable.includes(m))};
  }
  function bind(doc, call, getTarget) {
    const el = id => doc.getElementById(id);
    const output = el("missionOutput");
    let job = null, busy = false, stopped = false, preview = null;
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
      if (value?.total && !onlyUnavailable) output.textContent += `\n${value.index || 0} / ${value.total} ${value.unit || "missions"} verified in this lobby.`;
    }
    function update() {
      const eligible = preview?.ok && runnable().length > 0 && runnable().length <= preview.max_batch;
      const resetting = runnable().some(m => m.resets_host_completion);
      el("missionRunBtn").textContent = ["map_locations", "travel_stations", "travel_requirements"].includes(el("missionScope").value) ? "Apply map / travel changes" : "Complete missions";
      el("missionRunBtn").disabled = busy || !eligible || !el("missionSharedAck").checked || (resetting && !el("missionResetCompleted").checked);
      el("missionResumeBtn").disabled = busy || job?.state !== "stopped" || (job?.pending?.length > 0 && splitCoverage(job.pending).remaining.length === 0) || (!["accept", "complete"].includes(job?.phase) && !(job?.dynamic && job?.phase === "prepare")) || (job?.operation_scope || "missions") !== "missions";
      el("missionCancelBtn").disabled = !busy || !job?.id;
      el("missionPreviewBtn").disabled = busy;
      el("missionScope").disabled = busy;
      el("missionNames").disabled = busy;
    }
    async function refresh() {
      preview = null; update();
      const scope = el("missionScope").value;
      try {
        const names = [...el("missionNames").selectedOptions].map(o => o.value);
        if (scope === "named" && !el("missionNames").options.length) {
          const catalog = await call("mission_preview", { scope: "all" });
          if (!catalog?.ok) { report(catalog); return; }
          for (const row of catalog.missions) {
            const option = doc.createElement("option");
            option.value = row.name; option.textContent = `${row.title} (${row.category})`;
            el("missionNames").append(option);
          }
        }
        if (scope === "named" && !names.length) {
          output.textContent = "Choose missions, then refresh preview.";
          el("missionPreviewList").textContent = "No missions selected."; return;
        }
        preview = await call("mission_preview", { scope, missions: names });
        if (!preview?.ok) { report(preview); return; }
        showUnavailable(preview.missions);
        el("missionPreviewList").textContent = splitCoverage(preview.missions).remaining.map(m => `${m.title}: ${m.state}${m.blocked_reason ? " — " + m.blocked_reason : m.resets_host_completion ? " — host reset required" : ""}`).join("\n");
        el("missionPreviewList").style.whiteSpace = "pre-line";
        output.textContent = category() ? `${preview.missions.length} catalog entries: ${runnable().length} queued, including locked missions to recheck as progress unlocks them; ${preview.excluded_total} nonpersistent replayable definitions excluded.` : `${runnable().length} entries ready; ${preview.missions.length - runnable().length} unavailable entries will be skipped. Review shared-progress options before running.`;
      } catch (error) { output.textContent = `Could not connect to the mission action: ${error.message}`; }
      finally { update(); }
    }
    el("missionPreviewBtn").addEventListener("click", refresh);
    el("missionScope").addEventListener("change", () => {
      preview = null; el("missionNamesLabel").hidden = el("missionScope").value !== "named"; update(); void refresh();
    });
    el("missionNames").addEventListener("change", () => { preview = null; update(); });
    for (const id of ["missionSharedAck", "missionResetCompleted"]) el(id).addEventListener("change", update);
    el("missionStatusBtn").addEventListener("click", async () => {
      try { const result = await call("mission_status", {}); if (!busy) job = result; report(result); update(); }
      catch (error) { output.textContent = error.message; }
    });
    el("missionRunBtn").addEventListener("click", async () => {
      if (el("missionRunBtn").disabled) return;
      busy = true; stopped = false; update();
      try {
        const target = getTarget();
        job = await call("mission_start", { scope: category() ? preview.selection_scope : ["map_locations", "travel_stations", "travel_requirements"].includes(preview.scope) ? preview.scope : "named", missions: runnable().map(m => m.name),
          target_scope: target ? "selected" : "local", target_player: target || undefined,
          acknowledge_shared_progress: el("missionSharedAck").checked, reset_completed: el("missionResetCompleted").checked });
        report(job); update();
        job = await advance(call, job, () => stopped, next => { job = next; report(next); update(); });
      } catch (error) { stopped = true; output.textContent = `Result not confirmed: ${error.message}. Check job status before retrying.`; }
      finally { busy = false; preview = null; update(); }
    });
    el("missionResumeBtn").addEventListener("click", async () => {
      if (el("missionResumeBtn").disabled) return;
      busy = true; stopped = false; update();
      try {
        job = await call("mission_resume", {job_id: job.id}); report(job);
        job = await advance(call, job, () => stopped, next => {job = next; report(next); update();});
      } catch (error) { stopped = true; output.textContent = `Result not confirmed: ${error.message}. Check job status.`; }
      finally { busy = false; preview = null; update(); }
    });
    el("missionCancelBtn").addEventListener("click", async () => {
      stopped = true;
      try { report(await call("mission_cancel", { job_id: job.id })); }
      catch (error) { output.textContent = `Cancellation not confirmed: ${error.message}. Check job status.`; }
    });
    update();
  }
  root.MsbtMissionPanel = { bind, advance, splitCoverage };
  if (typeof module !== "undefined") module.exports = { bind, advance, splitCoverage };
})(typeof window === "undefined" ? globalThis : window);
