/* Display-only artifact reader; no proof/search/checker authority. */
"use strict";
(() => {
  const modes = ["base", "fixed-whole-family-pool"];
  const names = {base:"Base", "fixed-whole-family-pool":"Fixed whole pool"};
  let readerData = null;
  const byId = id => document.getElementById(id);
  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function math(text, className) { return element("span",className,"\\("+text+"\\)"); }
  function typeset(nodes) {
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise(nodes).catch(() => {});
    }
  }
  function boundary() {
    const parent = byId("row-obligations");
    for (let row=0; row<24; row++) {
      const slot=element("div","slot"+(row<3?" seed":row===23?" target":""));
      slot.append(math(String(row)));
      slot.title=row<3?"Input boundary: licensed hypothesis seed":row===23?"Input boundary: required target position":"Input boundary: required row position; actual selected tile shown in the reader";
      parent.append(slot);
    }
    typeset([parent]);
  }
  function pin(record) {
    return record && typeof record.path==="string" && /^[a-f0-9]{64}$/.test(record.sha256) && Number.isSafeInteger(record.bytes) && record.bytes>=0;
  }
  function acceptedForDisplay(lane) {
    const p=lane.proof, a=lane.replay, producer=lane.producer;
    return Boolean(p && p.ROOT_final_accepted===true && p.point_symbolic_accepted===true &&
      a.trace_accepted===true && a.job_resource_accepted===true && producer.job_resource_accepted===true &&
      pin(p.certificate_pin) && pin(p.independent_acceptance_pin) && pin(producer.result_pin) &&
      pin(producer.resource_pin) && pin(a.result_pin) && pin(a.resource_pin));
  }
  function validate(data) {
    if (!data || data.schema!=="notebook119-reader-data-v1" || data.selector!=="donor-repeated-guard" ||
        data.all_five_qualification!==false || data.new_RL_training!==false || !data.lanes) throw new Error("Reader metadata scope mismatch");
    for (const mode of modes) {
      const lane=data.lanes[mode];
      if (!lane || !lane.producer || !lane.replay || !Array.isArray(lane.rows) || lane.rows.length>24) throw new Error("Missing lane metadata");
      if (!acceptedForDisplay(lane) && lane.rows.length) throw new Error("Proof rows require ROOT acceptance and both resource receipts");
      if (acceptedForDisplay(lane)) {
        const indices=new Set();
        if (lane.rows.length!==24) throw new Error("Complete primitive row expansion required");
        for (const row of lane.rows) {
          if (!Number.isInteger(row.row_index) || row.row_index<0 || row.row_index>23 || indices.has(row.row_index) ||
              typeof row.formula_latex!=="string" || row.formula_latex.length>4096 || typeof row.english!=="string" || row.english.length>4096 ||
              typeof row.placement_id!=="string" || typeof row.license_id!=="string" || typeof row.rule_label!=="string" ||
              !Array.isArray(row.dependencies) || row.dependencies.some(d=>!Number.isInteger(d)||d<0||d>=row.row_index) ||
              !Number.isInteger(row.formula_code) || !row.command || !Array.isArray(row.t) || !Array.isArray(row.m) ||
              [...row.t,...row.m].some(v=>!Array.isArray(v)||v.length!==3||v.some(n=>!Number.isInteger(n)))) throw new Error("Invalid complete row display metadata");
          indices.add(row.row_index);
        }
      }
    }
    return data;
  }
  function phaseLabel(phase) {
    if (phase.status==="pending") return "Pending";
    const status=String(phase.status||"Unknown");
    return status+(phase.job_resource_accepted===true?" · scoped resources accepted":" · resources pending / UNKNOWN");
  }
  function measuredCell(phase) {
    const cell=element("td","",phaseLabel(phase));
    for (const [key,label] of [["search_seconds","\\text{Search}"],["full_tool_seconds","\\text{Full tool}"],["additional_finalizer_seconds","\\text{Extra finalizer}"]]) {
      const value=phase[key];
      if (typeof value==="number" && Number.isFinite(value) && value>=0) {
        const line=element("p","small");line.append(math(label+"\\;"+value+"\\,\\mathrm{s}"));cell.append(line);
      }
    }
    for (const [key,label] of [["attempts","\\text{Attempts}"],["events","\\text{Events}"]]) {
      const value=phase[key];
      if (Number.isSafeInteger(value) && value>=0) {const line=element("p","small");line.append(math(label+"\\;"+value));cell.append(line);}
    }
    return cell;
  }
  function lanes(data) {
    const table=byId("lane-table"); table.replaceChildren();
    for (const mode of modes) {
      const lane=data.lanes[mode], row=element("tr");
      row.append(element("td","",names[mode]),measuredCell(lane.producer),measuredCell(lane.replay),element("td","",acceptedForDisplay(lane)?"Accepted ground certificate":"None accepted"));
      const perf=lane.performance, cell=element("td","",perf && perf.ROOT_complete_paired_costs_accepted===true?"ROOT complete costs reported":"Component costs below; no speed ratio");
      if (perf && perf.ROOT_complete_paired_costs_accepted===true && typeof perf.complete_total_seconds==="number" && Number.isFinite(perf.complete_total_seconds) && perf.complete_total_seconds>=0) {
        const line=element("p","small");line.append(math(perf.complete_total_seconds+"\\,\\mathrm{s}"));cell.append(line);
      }
      row.append(cell);
      table.append(row);
    }
    typeset([table]);
    const stats=byId("search-stats"),costs=byId("phase-costs"),evidence=byId("search-evidence");
    for (const mode of modes) {
      const lane=data.lanes[mode],s=lane.summary,row=element("tr");
      row.append(element("td","",names[mode]));
      for(const value of [s.attempts,s.nodes,s.backtracks,s.changed_first_choices]){const cell=element("td");cell.append(math(String(value)));row.append(cell);}
      const timer=element("td");timer.append(math(s.search_seconds.toFixed(3)+"\\,\\mathrm{s}"));row.append(timer);stats.append(row);
      for(const key of ["producer","replay"]){
        const phase=lane[key],line=element("tr");line.append(element("td","",names[mode]+" / "+key));
        for(const value of [phase.owner_complete_seconds,phase.worker_complete_seconds,phase.full_tool_seconds,phase.additional_finalizer_seconds]){const cell=element("td");cell.append(math(value.toFixed(3)+"\\,\\mathrm{s}"));line.append(cell);}
        const memory=element("td");memory.append(math(phase.scoped_estimate_bytes.toLocaleString("en-US").replaceAll(",","{,}")+"\\,\\mathrm{bytes}"));line.append(memory);costs.append(line);
        for(const [label,url] of [["full result (gzip)",phase.result_url],["conditional resource receipt",phase.resource_url]]){const item=element("li"),link=element("a","",names[mode]+" / "+key+": "+label);link.href=url;item.append(link);evidence.append(item);}
      }
      const item=element("li"),link=element("a","",names[mode]+": ROOT final decision");link.href=mode+"-ROOT-final-decision-v1.json";item.append(link);evidence.append(item);
    }
    typeset([stats,costs]);
  }
  function proof() {
    const parent=byId("proof-rows"), status=byId("reader-state"), badge=byId("proof-reader-badge");
    if (window.MathJax && window.MathJax.typesetClear) window.MathJax.typesetClear([parent]);
    parent.replaceChildren();
    const mode=byId("proof-lane").value;
    const lane=readerData && readerData.lanes[mode];
    if (!lane || !acceptedForDisplay(lane)) {
      badge.textContent="NO ACCEPTED PROOF IN THIS LANE";
      status.textContent=lane && lane.producer.status==="unknown_search_budget"?"The base search stopped at its attempt budget without a proof. Its complete search trace passed independent replay. The result remains UNKNOWN.":"This lane has no fully accepted proof to display.";
      return;
    }
    badge.textContent="ROOT-ACCEPTED GROUND CERTIFICATE";
    status.textContent="These rows come from the exact returned primitive certificate and independently accepted artifact pins recorded by ROOT. The browser displays that evidence; it does not check the proof.";
    const rows=[...lane.rows].sort((a,b)=>a.row_index-b.row_index);
    for (const data of rows) {
      const row=element("article","proof-row");row.id="proof-"+mode+"-row-"+data.row_index;
      const tile=element("div","square");tile.append(math("\\text{Row }"+data.row_index),math("\\mathsf{F}_{"+data.formula_code+"}","formula-mark"),math("t(0,"+data.row_index+")=1","occupancy-mark"),element("small","provenance-mark",data.rule_label));
      for(const [x,y,value] of data.m.filter(mark=>mark[0]===2||mark[0]===3))tile.append(math("m("+x+","+y+")="+value,"reference-mark"));
      const prose=element("div","row-prose"), title=element("h3");title.append(math("\\text{Row }"+data.row_index));
      prose.append(title,math(data.formula_latex,"formula"),element("p","",data.english));
      prose.append(element("p","license-id","Placement: "+data.placement_id),element("p","license-id","License: "+data.license_id));
      if (data.cluster_id!==null && data.cluster_id!==undefined) prose.append(element("p","small","Cluster reference: "+String(data.cluster_id)+"; this line is its primitive expansion."));
      const deps=element("div","dependencies");deps.append(element("span","small",data.dependencies.length?"Licensed dependencies: ":"No premise dependencies recorded for this licensed row."));
      for (const index of data.dependencies) {
        const link=element("a","dependency");link.href="#proof-"+mode+"-row-"+index;link.append(math("\\text{Row }"+index));deps.append(link);
      }
      prose.append(deps);
      const details=element("details"),summary=element("summary","","Exact point values and licensed command");details.append(summary);
      for(const [kind,values] of [["t",data.t],["m",data.m]])for(const [x,y,value] of values){const line=element("p",kind==="t"?"occupancy-mark":x>=2?"reference-mark":"formula-mark");line.append(math(kind+"("+x+","+y+")="+value));details.append(line);}
      details.append(element("pre","",JSON.stringify(data.command,null,2)));prose.append(details);row.append(tile,prose);parent.append(row);
    }
    typeset([parent]);
  }
  for (const input of document.querySelectorAll("[data-layer]")) {
    input.addEventListener("change",()=>document.body.classList.toggle("hide-"+input.dataset.layer,!input.checked));
  }
  byId("proof-lane").addEventListener("change",proof);
  boundary();
  fetch("reader-data.json",{cache:"no-store"}).then(response=>{
    if (!response.ok) throw new Error("Reader data unavailable");return response.text();
  }).then(text=>{
    if (text.length>1048576) throw new Error("Reader data exceeds display metadata envelope");
    readerData=validate(JSON.parse(text));lanes(readerData);proof();
    const pending=modes.every(mode=>readerData.lanes[mode].producer.status==="pending");
    byId("data-status").textContent=pending?"Reader metadata loaded: static counts and pending lanes.":"Both cold search and replay records loaded. The cluster proof is accepted in the restricted symbolic point model; the base attempt cutoff remains UNKNOWN.";
  }).catch(()=>{
    byId("data-status").textContent="Optional reader data is unavailable or does not match the display contract. The static checkpoint above remains visible; no proof rows are inferred.";
  });
})();
