/* Display-only source: no search, proof checking or artifact authentication. */
"use strict";
(() => {
  const modes = ["base", "fixed-whole-family-pool"];
  const names = {base:"Base", "fixed-whole-family-pool":"Fixed whole pool"};
  let readerData = null;
  const byId = id => document.getElementById(id);
  const finite = value => typeof value==="number" && Number.isFinite(value) && value>=0;
  const count = value => Number.isSafeInteger(value) && value>=0;
  function element(tag, className, text) {
    const node=document.createElement(tag);
    if (className) node.className=className;
    if (text!==undefined) node.textContent=text;
    return node;
  }
  function math(text, className) { return element("span",className,"\\("+text+"\\)"); }
  function typeset(nodes) {
    if (window.MathJax && window.MathJax.typesetPromise) window.MathJax.typesetPromise(nodes).catch(() => {});
  }
  function pin(record) {
    return record && typeof record.path==="string" && /^[a-f0-9]{64}$/.test(record.sha256) && count(record.bytes);
  }
  function localURL(url) {
    return typeof url==="string" && url.length>0 && url.length<=512 &&
      !url.startsWith("/") && !/[\\:?#]/.test(url) && !url.split("/").includes("..");
  }
  function acceptedForDisplay(lane) {
    const p=lane.proof,a=lane.replay,producer=lane.producer;
    return Boolean(p && p.ROOT_final_accepted===true && p.point_symbolic_accepted===true &&
      a.trace_accepted===true && a.job_resource_accepted===true && producer.job_resource_accepted===true &&
      pin(p.certificate_pin) && pin(p.independent_acceptance_pin) && pin(producer.result_pin) &&
      pin(producer.resource_pin) && pin(a.result_pin) && pin(a.resource_pin));
  }
  function validate(data) {
    if (!data || data.schema!=="notebook120-reader-data-v2" || data.selector!=="heldout-mixed-guard-equality" ||
      data.all_five_qualification!==false || data.new_RL_training!==false || data.native_accepted!==false ||
      data.compiler_correspondence!=="open" || !data.statement || !data.static || !data.preparation || !data.lanes ||
      JSON.stringify(data.statement.hypothesis_codes)!=="[11,42,52]" || data.statement.target_code!==54 ||
      JSON.stringify(data.statement.seed_rows)!=="[0,1,2]" || data.statement.target_row!==23) throw new Error("Display scope mismatch");
    const inventory=data.frozen_inventory;
    if (!inventory || inventory.rows!==24 || inventory.formula_values!==217 || inventory.primitive_licenses!==229 ||
      inventory.source_bodies!==171 || inventory.single_types!==171 || inventory.ordered_pair_types!==29241 ||
      inventory.complete_group_capacity!==64) throw new Error("Frozen inventory display mismatch");
    if (data.preparation.accepted===true && !pin(data.preparation.receipt_pin)) throw new Error("Preparation receipt shape missing");
    if (data.static.accepted===true && (!pin(data.static.semantic_receipt_pin) || !pin(data.static.resource_receipt_pin) ||
      data.static.resource_accepted!==true || !count(data.static.initial_candidates) || !count(data.static.complete_groups) ||
      data.static.complete_groups>64 || !count(data.static.complete_distinct_role_envelope_bytes) ||
      !finite(data.static.whole_static_tool_bound_seconds))) throw new Error("Static display receipt shape missing");
    for (const mode of modes) {
      const lane=data.lanes[mode];
      if (!lane || !lane.producer || !lane.replay || !Array.isArray(lane.rows) || lane.rows.length>24) throw new Error("Missing lane metadata");
      if (!acceptedForDisplay(lane) && lane.rows.length) throw new Error("Proof rows require exact ROOT acceptance labels and receipt pins");
      if (acceptedForDisplay(lane)) {
        if (data.static.accepted!==true || lane.rows.length!==24) throw new Error("Full accepted static context and primitive expansion required");
        const indices=new Set();
        for (const row of lane.rows) {
          if (!Number.isInteger(row.row_index) || row.row_index<0 || row.row_index>23 || indices.has(row.row_index) ||
            typeof row.formula_latex!=="string" || row.formula_latex.length>4096 ||
            typeof row.english!=="string" || row.english.length>4096 ||
            typeof row.placement_id!=="string" || typeof row.license_id!=="string" || typeof row.rule_label!=="string" ||
            !Array.isArray(row.dependencies) || row.dependencies.some(d=>!Number.isInteger(d)||d<0||d>=row.row_index) ||
            !Number.isInteger(row.formula_code) || row.formula_code<0 || row.formula_code>=217 ||
            !row.command || !Array.isArray(row.formula_ast) || !Array.isArray(row.t) || !Array.isArray(row.m) ||
            [...row.t,...row.m].some(v=>!Array.isArray(v)||v.length!==3||v.some(n=>!Number.isInteger(n)))) throw new Error("Invalid complete primitive row display");
          indices.add(row.row_index);
        }
      }
    }
    return data;
  }
  function boundary() {
    const parent=byId("row-obligations");
    for (let row=0;row<24;row++) {
      const slot=element("div","slot"+(row<3?" seed":row===23?" target":""));
      slot.append(math(String(row)));
      slot.title=row<3?"Input boundary: separately licensed hypothesis seed":row===23?
        "Input boundary: required target, not a selected proof tile":"Required row obligation, not a selected proof line";
      parent.append(slot);
    }
    typeset([parent]);
  }
  function formatted(value, kind) {
    if (kind==="count") return count(value)?String(value).replace(/\B(?=(\d{3})+(?!\d))/g,"{,}"):null;
    return finite(value)?value.toFixed(3)+"\\,\\mathrm{s}":null;
  }
  function metricCell(value, kind, missingLabel="Pending") {
    const cell=element("td"),label=formatted(value,kind);
    cell.append(label===null?element("span","pending-copy",missingLabel):math(label));
    return cell;
  }
  function artifactLink(parent,label,url) {
    if (!localURL(url)) return;
    const item=element("li"),link=element("a","",label);link.href=url;item.append(link);parent.append(item);
  }
  function checkpoint(data) {
    const prep=data.preparation,stat=data.static;
    byId("preparation-state").textContent=prep.accepted===true?"SCOPED PREPARATION ACCEPTED":prep.internal_complete===true?"INTERNAL PREPARATION COMPLETE · RESOURCE UNKNOWN":"PREPARATION PENDING / UNKNOWN";
    const prepDetail=byId("preparation-detail");
    if (prep.internal_complete===true && prep.accepted!==true && finite(prep.internal_seconds) && count(prep.internal_scoped_estimate_bytes) && finite(prep.caller_observation_seconds)) {
      prepDetail.replaceChildren(element("span","","ROOT reports internal completion in "),math(prep.internal_seconds+"\\,\\mathrm{s}"),element("span",""," with a scoped estimate of "),math(formatted(prep.internal_scoped_estimate_bytes,"count")+"\\,\\mathrm{bytes}"),element("span","",". The caller observation interval is "),math(prep.caller_observation_seconds.toFixed(3)+"\\,\\mathrm{s}"),element("span","","; the conservative bound including the declared margin exceeds the frozen preparation boundary. This interval is not worker runtime. External/resource qualification remains UNKNOWN."));
      typeset([prepDetail]);
    } else prepDetail.textContent=prep.accepted===true?
      "ROOT records a closed fresh preparation receipt. Its scope and measured interval remain separate from static audit and proof search.":
      "No accepted fresh preparation receipt is attached; status: "+String(prep.status)+".";
    byId("static-state").textContent=stat.accepted===true?"STATIC AND SCOPED RESOURCES ACCEPTED":"STATIC ACCEPTANCE PENDING / UNKNOWN";
    byId("static-detail").textContent=stat.accepted===true?
      "ROOT binds exact semantic and conditional resource receipts for this complete mixed context.":
      "Producer reports one construction with the census below. No independent static audit is activated or accepted; internal preparation and source counts do not qualify it.";
    const census=byId("static-census");
    if (stat.accepted===true) {
      census.replaceChildren();
      census.append(element("span","","Fresh complete census: "),math(formatted(stat.initial_candidates,"count")+"\\text{ initial candidates};\\quad"+stat.complete_groups+"\\text{ complete groups}."));
      census.append(element("span",""," Conditional distinct-role estimate: "),math(formatted(stat.complete_distinct_role_envelope_bytes,"count")+"\\,\\mathrm{bytes}"));
      census.append(element("span","","; static enclosing tool bound: "),math(formatted(stat.whole_static_tool_bound_seconds,"seconds")),element("span","",". Known-topology scope and separately observed finalizers remain required."));
    }
    const accepted=modes.filter(mode=>acceptedForDisplay(data.lanes[mode]));
    byId("proof-state").textContent=accepted.length?"ROOT-ACCEPTED GROUND CERTIFICATE":"DISCOVERY AND REPLAY PENDING / UNKNOWN";
    byId("proof-detail").textContent=accepted.length?
      "Accepted proof rows are available for "+accepted.map(mode=>names[mode]).join(" and ")+"; producer, replay and point/symbolic acceptance are separate records.":
      "No fully accepted mixed-context proof is attached. Actual lane statuses are shown below; no boundary tile is inferred to be a proof.";
    byId("mixed-outcome").textContent=data.preparation.accepted===false && data.preparation.internal_complete===true ? "Preparation completed internally; caller gate UNKNOWN. Both searches were not run." : modes.map(mode=>names[mode]+": "+String(data.lanes[mode].producer.status)).join("; ");
    typeset([census]);
  }
  function phaseCell(phase) {
    const cell=element("td","",phase.status.startsWith("not_activated")?"Not run":phase.status==="pending"?"Pending":String(phase.status));
    if (phase.status!=="pending" && !phase.status.startsWith("not_activated")) cell.append(element("p","small",phase.job_resource_accepted===true?"Scoped resources accepted":"Resources pending / UNKNOWN"));
    if (phase.trace_accepted===true) cell.append(element("p","small","Complete independent trace accepted"));
    return cell;
  }
  function lanes(data) {
    const table=byId("lane-table"),stats=byId("search-stats"),costs=byId("phase-costs"),evidence=byId("search-evidence");
    for (const parent of [table,stats,costs,evidence]) parent.replaceChildren();
    for (const mode of modes) {
      const lane=data.lanes[mode],row=element("tr");
      row.append(element("td","",names[mode]),phaseCell(lane.producer),phaseCell(lane.replay),element("td","",acceptedForDisplay(lane)?"Accepted ground certificate":"None accepted"));
      const performance=lane.performance,cell=element("td","",performance && performance.ROOT_complete_paired_costs_accepted===true?"ROOT complete paired costs reported":"Pending complete reconciliation; no speed ratio");
      if (performance && performance.ROOT_complete_paired_costs_accepted===true && finite(performance.complete_total_seconds)) cell.append(math(formatted(performance.complete_total_seconds,"seconds")));
      row.append(cell);table.append(row);
      const s=lane.summary||{},line=element("tr");line.append(element("td","",names[mode]));
      const notRun=lane.producer.status.startsWith("not_activated")?"Not run":"Pending";
      for (const key of ["attempts","nodes","backtracks","changed_first_choices"]) line.append(metricCell(s[key],"count",notRun));
      line.append(metricCell(s.search_seconds,"seconds",notRun));stats.append(line);
      for (const key of ["producer","replay"]) {
        const phase=lane[key],phaseMissing=phase.status.startsWith("not_activated")?"Not run":"Pending",cost=element("tr");cost.append(element("td","",names[mode]+" / "+key));
        for (const field of ["owner_complete_seconds","worker_complete_seconds","full_tool_seconds","additional_finalizer_seconds"]) cost.append(metricCell(phase[field],"seconds",phaseMissing));
        const memory=element("td"),label=formatted(phase.scoped_estimate_bytes,"count");memory.append(label===null?element("span","pending-copy",phaseMissing):math(label+"\\,\\mathrm{bytes}"));cost.append(memory);costs.append(cost);
        artifactLink(evidence,names[mode]+" / "+key+": full saved result",phase.result_url);
        artifactLink(evidence,names[mode]+" / "+key+": conditional resource receipt",phase.resource_url);
      }
      artifactLink(evidence,names[mode]+": ROOT final decision",lane.final_decision_url);
    }
    artifactLink(evidence,"Closed preparation-only UNKNOWN receipt",data.preparation.receipt_url);
    artifactLink(evidence,"ROOT final public decision",data.ROOT_decision_url);
    artifactLink(evidence,"Fresh semantic static receipt",data.static.semantic_receipt_url);
    artifactLink(evidence,"Fresh conditional static resource receipt",data.static.resource_receipt_url);
    typeset([table,stats,costs]);
  }
  function proof() {
    const parent=byId("proof-rows"),status=byId("reader-state"),badge=byId("proof-reader-badge");
    if (window.MathJax && window.MathJax.typesetClear) window.MathJax.typesetClear([parent]);
    parent.replaceChildren();
    const mode=byId("proof-lane").value,lane=readerData && readerData.lanes[mode];
    if (!lane || !acceptedForDisplay(lane)) {
      badge.textContent="NO ACCEPTED MIXED PROOF IN THIS LANE";
      status.textContent=lane && lane.producer.status==="unknown_search_budget"?
        "This lane stopped at a frozen search budget without a proof. UNKNOWN is not exhaustion. Replay acceptance, if present, validates the saved tape without supplying a missing theorem.":
        "No fully accepted mixed-context proof is attached for this lane. Boundary diagrams and source bodies do not supply returned proof rows.";
      return;
    }
    badge.textContent="ROOT-ACCEPTED GROUND CERTIFICATE";
    status.textContent="Every primitive row below is exported from the exact returned and independently accepted certificate. ROOT binds the proof and resource artifacts; the browser displays them.";
    for (const data of [...lane.rows].sort((a,b)=>a.row_index-b.row_index)) {
      const row=element("article","proof-row");row.id="proof-"+mode+"-row-"+data.row_index;
      const tile=element("div","square");tile.append(math("\\text{Row }"+data.row_index),math("\\mathsf{F}_{"+data.formula_code+"}","formula-mark"));
      for (const [x,y,value] of data.t) tile.append(math("t("+x+","+y+")="+value,"occupancy-mark"));
      tile.append(element("small","provenance-mark",data.rule_label));
      for (const [x,y,value] of data.m.filter(mark=>mark[0]===2||mark[0]===3)) tile.append(math("m("+x+","+y+")="+value,"reference-mark"));
      const prose=element("div","row-prose"),title=element("h3");title.append(math("\\text{Row }"+data.row_index));
      prose.append(title,math(data.formula_latex,"formula"),element("p","",data.english));
      prose.append(element("p","license-id","Placement: "+data.placement_id),element("p","license-id","License: "+data.license_id));
      if (data.cluster_id!==null && data.cluster_id!==undefined) prose.append(element("p","small","Cluster reference: "+String(data.cluster_id)+"; this row is its primitive expansion."));
      const deps=element("div","dependencies");deps.append(element("span","small",data.dependencies.length?"Ordered licensed dependencies: ":"No premise dependencies for this licensed row."));
      for (const index of data.dependencies) {const link=element("a","dependency");link.href="#proof-"+mode+"-row-"+index;link.append(math("\\text{Row }"+index));deps.append(link);}
      prose.append(deps);
      const details=element("details"),summary=element("summary","","Exact point values, formula syntax and licensed command");details.append(summary);
      for (const [kind,values] of [["t",data.t],["m",data.m]]) for (const [x,y,value] of values) {
        const line=element("p",kind==="t"?"occupancy-mark":x>=2?"reference-mark":"formula-mark");line.append(math(kind+"("+x+","+y+")="+value));details.append(line);
      }
      details.append(element("pre","",JSON.stringify({formula_ast:data.formula_ast,command:data.command},null,2)));prose.append(details);row.append(tile,prose);parent.append(row);
    }
    typeset([parent]);
  }
  for (const input of document.querySelectorAll("[data-layer]")) input.addEventListener("change",()=>document.body.classList.toggle("hide-"+input.dataset.layer,!input.checked));
  byId("proof-lane").addEventListener("change",proof);
  boundary();
  fetch("reader-data.json",{cache:"no-store"}).then(response=>{
    if (!response.ok) throw new Error("Display data unavailable");return response.text();
  }).then(text=>{
    if (text.length>1048576) throw new Error("Display metadata envelope exceeded");
    readerData=validate(JSON.parse(text));checkpoint(readerData);lanes(readerData);proof();
    byId("data-status").textContent="Display data loaded for the exact mixed selector. Pending fields remain pending; proof rows require ROOT acceptance and both resource receipts.";
  }).catch(()=>{
    byId("data-status").textContent="Display data is unavailable or fails its schema gate. No proof, measured cost or mixed acceptance is inferred.";
  });
})();
