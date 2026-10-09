"use strict";
const NS="http://www.w3.org/2000/svg";
const $=id=>document.getElementById(id);
const el=(name,attrs={},text)=>{const n=document.createElementNS(NS,name);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;return n;};
const svgText=(svg,x,y,text,attrs={})=>svg.append(el("text",{x,y,"font-size":12,fill:"#65716a",...attrs},text));
const colors=["#347999","#c76b3d","#6b8552","#925e82","#b9a55c"];
const perms=[[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];
const syms=[1,-1].flatMap(s=>perms.map(p=>({s,p})));
const project=p=>[p[0]+p[1]/2,-p[1]*Math.sqrt(3)/2];
const verts=(base,key)=>{const {s,p}=syms[key[0]],tr=key[1];return base.map(q=>p.map((i,j)=>s*q[i]+tr[j]));};
const mean=xs=>xs.length?xs.reduce((a,b)=>a+b,0)/xs.length:0;
const fmt=x=>Number(x).toFixed(x>=100?0:2);
let data,secondData,haloData,thirdData,penroseData,proofData,clusterData,timer=null,currentRun,currentProof,currentProofRows;

function clusterTileView(){
  const t=clusterData.types.find(t=>t.identity===$("cluster-tile-view").value),children=clusterData.child_expansions[t.identity];
  const groups=children?t.expansion.map(key=>children.findIndex(child=>child.some(k=>JSON.stringify(k)===JSON.stringify(key)))):null;
  const frontier=t.occupancy.filter(([p,v])=>v<12).map(([p])=>p);
  drawPatch($("cluster-tile-drawing"),t.expansion,{points:frontier,width:720,height:380,groups});
  $("cluster-tile-caption").textContent=`Level ${t.level} · ${t.identity} · ${t.expansion.length} distinct base constituents; ${t.occupancy.length} positive points; ${frontier.length} incomplete interface points. ${children?`${children.length} checked child maps; colors identify child ownership.`:"Base tiles retain their handedness colors."} Gold dots identify residual point obligations.`;
}
function clusterTileResults(){
  clusterData.types.forEach(t=>{const o=document.createElement("option");o.value=t.identity;o.textContent=`Level ${t.level} · ${t.identity} · ${t.expansion.length} base tiles`;$("cluster-tile-view").append(o);});
  $("cluster-tile-view").value='observed-parent';$("cluster-tile-view").addEventListener('change',clusterTileView);clusterTileView();
  $("cluster-tile-evidence").textContent=`${clusterData.prototype_count} types include the base singleton, 14 searched clusters and one observed parent. All ${clusterData.transformed_expansions_checked} transformed expansions replay to exact base values. Five new semantic tests cover inherited level channels, zero-valued distant dependencies, complete aggregate incidence, exact snapshots, base fallback and rejected malformed hierarchies. The complete research suite now passes ${proofData.semantic_tests.passed} tests.`;
}

const proofSymbolColor=s=>Array.isArray(s)?"#c97940":String(s).startsWith("w:")||String(s).startsWith("c:")?"#4b8068":String(s).startsWith("r:")||["p",";","X","_"].includes(s)?"#99bac1":["L","#","$","c#"].includes(s)?"#8a728b":"#e7e9de";
const wordTex=word=>word.length?`\\mathtt{${word.join("")}}`:"\\varepsilon";
function proofRowView(){
  if(!currentProofRows)return;
  const step=Number($("proof-row").value),row=currentProofRows[step],svg=$("proof-row-tape"),cell=680/row.length;
  svg.replaceChildren();$("proof-row-value").textContent=step;
  row.forEach((s,x)=>{const head=Array.isArray(s),name=head?s[2]:s,px=30+x*cell;
    svg.append(el("rect",{x:px,y:17,width:cell-2,height:43,rx:2,fill:proofSymbolColor(s)}));
    svgText(svg,px+(cell-2)/2,44,String(name),{"text-anchor":"middle",fill:head?"#fff9e8":"#24362d","font-family":"monospace","font-size":Math.min(14,cell/3)});
  });
  const head=row.findIndex(s=>Array.isArray(s));
  $("proof-row-caption").textContent=`Step ${step} of ${currentProof.height}. ${head>=0?`Head at tape cell ${head}; compiled state ${row[head][1]}.`:"No head."} Labels are literal tape-symbol identifiers.`;
  const marker=$("proof-row-marker");if(marker){marker.setAttribute("y1",22+step/currentProof.height*365);marker.setAttribute("y2",22+step/currentProof.height*365);}
}
function proofPilotView(){
  const problem=proofData.problems[Number($("proof-problem").value)],lane=$("proof-lane").value;
  currentProof=proofData.evaluation.find(r=>r.problem_id===problem.id&&r.lane===lane);currentProofRows=null;
  const svg=$("proof-machine-grid");svg.replaceChildren();$("proof-row-tape").replaceChildren();
  const math=$("word-proof");window.MathJax?.typesetClear?.([math]);
  math.textContent=currentProof.word_derivation?`\\[${currentProof.word_derivation.map(wordTex).join("\\;\\Rightarrow\\;")}\\]`:`\\[${wordTex(problem.source)}\\;\\Rightarrow_R^*\\;${wordTex(problem.target)}\\]`;
  $("proof-problem-caption").textContent=`Declared word capacity ${problem.capacity}; ${problem.certificate_length} unknown proof bytes; rectangle ${problem.width} columns by ${problem.height} rows. The generated checker has ${problem.states} states, ${problem.tape_alphabet} tape symbols, ${problem.transitions.toLocaleString()} transitions, and ${problem.tile_types.toLocaleString()} possible Wang tile types. Their domains are represented exactly by symbolic products.`;
  $("proof-row").disabled=!currentProof.verified;$("proof-row").max=problem.height;$("proof-row").value=0;$("proof-row-value").textContent="0";
  if(!currentProof.verified){
    svgText(svg,370,175,"Unknown within this search budget",{"text-anchor":"middle","font-size":21});
    svgText(svg,370,215,`${currentProof.nodes.toLocaleString()} attempted placements · ${fmt(currentProof.lane_seconds)} seconds`,{"text-anchor":"middle"});
    $("proof-grid-caption").textContent="No proof rectangle was found within the declared bounds. This does not refute the assertion.";$("proof-row-caption").textContent="Choose a successful lane to inspect a certificate.";
  }else{
    const c=currentProof.certificate,types=c.tile_types_used,symbols=c.symbols,w=660/problem.width,h=365/problem.height;
    currentProofRows=[c.initial.map(id=>symbols[id]),...c.grid.map(row=>row.map(id=>symbols[types[id][3]]))];
    c.grid.forEach((row,y)=>row.forEach((id,x)=>{
      const s=symbols[types[id][3]],rect=el("rect",{x:52+x*w,y:22+y*h,width:w-.45,height:h-.12,fill:proofSymbolColor(s)});
      svg.append(rect);
    }));
    svgText(svg,52,14,"Input at top · machine time runs down",{"font-size":11});
    svgText(svg,52,412,`Accepting row · ${problem.width*problem.height} checked base tile placements`,{"font-size":11});
    svg.append(el("line",{id:"proof-row-marker",x1:46,x2:718,y1:22,y2:22,stroke:"#834853","stroke-width":2}));
    $("proof-grid-caption").textContent=`${lane}: independently replayed word rules, machine transitions, point sums and all marking agreements. ${currentProof.nodes.toLocaleString()} tried placements; ${currentProof.forced.toLocaleString()} forced; ${currentProof.branches.toLocaleString()} branches; ${fmt(currentProof.lane_seconds)} total seconds including proposal construction. The packed certificate uses ${types.length} distinct tile types.`;
    proofRowView();
  }
  if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise([math]).catch(()=>{});
}
function genericProofResults(){
  const d=proofData;
  d.problems.forEach(p=>{const o=document.createElement("option");o.value=p.id;o.textContent=`Problem ${p.id+1} · source length ${p.source.length}`;$("proof-problem").append(o);});
  d.configuration.lanes.forEach(lane=>{const o=document.createElement("option");o.value=lane;o.textContent=lane;$("proof-lane").append(o);});
  $("proof-lane").value="RL + standard Wang";
  ["proof-problem","proof-lane"].forEach(id=>$(id).addEventListener("change",proofPilotView));
  $("proof-row").addEventListener("input",proofRowView);proofPilotView();
  const summary=d.configuration.lanes.map(lane=>{const rs=d.evaluation.filter(r=>r.lane===lane),success=rs.filter(r=>r.verified).length;
    tableRow("proof-search-benchmark",[lane,`${success} / ${rs.length}`,Math.round(mean(rs.map(r=>r.nodes))).toLocaleString(),fmt(mean(rs.map(r=>r.branches))),fmt(mean(rs.map(r=>r.lane_seconds)))]);return {lane,success};});
  const standard=summary.find(s=>s.lane==="standard Wang"),analytic=summary.find(s=>s.lane==="analytic GCTS"),rl=summary.find(s=>s.lane==="RL + standard Wang");
  $("proof-search-finding").textContent=`Cold training checked ${d.training.success} of ${d.training.episodes.length} proposals. On the three shorter held-out sources, learned proposals found ${rl.success} checked proofs; standard Wang found ${standard.success} and the analytic marking alone found ${analytic.success}. Each rectangle has the same 100,000-placement and five-second bounds in every lane. The analytic marking adds propagation work and does not improve the learned lane here. These tiny same-theory examples establish an executable path, not a general theorem-proving speedup.`;
  const a=d.independent_audit;
  $("proof-search-cost").textContent=`Cold training ${fmt(d.training.seconds)} s; generated programs ${fmt(d.problems.reduce((sum,p)=>sum+p.compile_seconds,0))} s; complete experiment ${fmt(d.total_seconds)} s; peak process memory ${(d.peak_process_memory_bytes/1048576).toFixed(1)} MiB. Separate replay ${fmt(a.seconds)} s checked ${a.checked_rectangles.length} rectangles and ${a.point_placements_checked.toLocaleString()} base placements, and rejected ${a.tampered_certificates_rejected} altered certificates/statements. Search timings include domain construction; lane totals also include proposal compilation and successful search replay. The bounded fair-driver control returns unknown after ${d.fair_bound_control.attempts} attempts. All ${d.semantic_tests.passed} semantic tests pass.`;
}

function drawPatch(svg,placements,{points=[],dead=null,width=800,height=470,groups=null}={}){
  svg.replaceChildren();
  const loops=placements.map(key=>verts(data.point_model.vertices,key).map(project));
  const projectedPoints=points.map(p=>project(p));
  const all=loops.flat().concat(projectedPoints,dead?[project(dead)]:[]);
  if(!all.length)return;
  const xs=all.map(p=>p[0]),ys=all.map(p=>p[1]);
  const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  const scale=Math.min((width-60)/Math.max(1,maxX-minX),(height-60)/Math.max(1,maxY-minY));
  const map=([x,y])=>[(x-(minX+maxX)/2)*scale+width/2,(y-(minY+maxY)/2)*scale+height/2];
  const bounds=[Math.floor(minX)-1,Math.ceil(maxX)+1,Math.floor(minY)-1,Math.ceil(maxY)+1];
  if(placements.length<15){
    for(let x=bounds[0]-10;x<=bounds[1]+10;x++)for(let y=bounds[2]-10;y<=bounds[3]+10;y++){
      const [a,b]=map(project([x,y,-x-y]));
      if(a>12&&a<width-12&&b>12&&b<height-12)svg.append(el("circle",{cx:a,cy:b,r:1,fill:"#b8c8b4"}));
    }
  }
  loops.forEach((loop,i)=>{
    const o=placements[i][0],p=syms[o].p;
    const inversions=Number(p[0]>p[1])+Number(p[0]>p[2])+Number(p[1]>p[2]);
    const fill=groups?`hsl(${groups[i]*137.508%360} 27% 58%)`:inversions%2?"#d19163":"#6d9c83";
    const shape=el("polygon",{points:loop.map(p=>map(p).join(",")).join(" "),fill,"fill-opacity":.72,stroke:"#345648","stroke-width":1.1,"stroke-linejoin":"round"});
    shape.append(el("title",{},`Base placement ${i+1}; orientation ${o}; translation ${placements[i][1].join(",")}`));
    svg.append(shape);
  });
  projectedPoints.forEach(p=>{const [x,y]=map(p);svg.append(el("circle",{cx:x,cy:y,r:2.3,fill:"#c79343"}));});
  if(dead){const [x,y]=map(project(dead));svg.append(el("circle",{cx:x,cy:y,r:9,fill:"none",stroke:"#b53741","stroke-width":3}));svg.append(el("circle",{cx:x,cy:y,r:3,fill:"#b53741"}));}
}

function spatialView(){
  const h=secondData.hierarchies.samples.find(h=>String(h.seed)===$("hierarchy-seed").value);
  if(!h){$("hierarchy-caption").textContent="No successful evaluation patch is available for hierarchy inspection.";return;}
  const level=h.levels[Number($("hierarchy-level").value)],groups=[];
  level.groups.forEach((g,i)=>g.base_ids.forEach(k=>groups[k]=i));
  drawPatch($("hierarchy-view"),h.placements,{width:760,height:470,groups});
  $("hierarchy-caption").textContent=`Seed ${h.seed}: ${h.base_tiles} base tiles in ${level.groups.length} groups at level ${level.level}. Every base placement occurs exactly once; aggregate point interfaces are replayed independently. The learned first-level library groups ${h.first_level_motif_tiles} of these tiles; residual singletons remain available.`;
}
function spatialType(){
  const m=secondData.spatial_library.motifs[Number($("spatial-type").value)];
  if(!m)return;
  drawPatch($("spatial-interface"),m.expansion,{points:m.interface.frontier.map(p=>p[0]),width:350,height:290});
  $("spatial-caption").textContent=`Type ${m.id+1}: ${m.expansion.length} base tiles, ${m.count} occurrences across ${m.donor_seeds.length} training donors. ${m.interface.frontier.length} residual point obligations, ${m.interface.completed_points} completed points, and ${m.interface.marking.length} assigned marking points.`;
}
function spatialResults(){
  const d=secondData,library=d.spatial_library,stats=library.statistics;
  d.hierarchies.samples.forEach(h=>{const o=document.createElement("option");o.value=h.seed;o.textContent=String(h.seed);$("hierarchy-seed").append(o);});
  library.motifs.forEach((m,i)=>{const o=document.createElement("option");o.value=i;o.textContent=`${m.id+1} · ${m.expansion.length} tiles · ${m.count} occurrences`;$("spatial-type").append(o);});
  spatialView();spatialType();
  ["hierarchy-seed","hierarchy-level"].forEach(id=>$(id).addEventListener("change",spatialView));
  $("spatial-type").addEventListener("change",spatialType);
  const donorCount=library.donors.filter(r=>r.status==="consistent_finite_patch").length;
  const extra=d.training.episodes.reduce((s,r)=>s+r.sequence_extra_moves,0);
  const summary=[];
  for(const lane of ["baseline","GCTS","RL","GCTS+RL"]){
    const rs=d.evaluation.filter(r=>r.lane===lane),success=rs.filter(r=>r.status==="consistent_finite_patch").length;
    summary.push({lane,rs,success,time:mean(rs.map(r=>r.seconds))});
    const tr=document.createElement("tr");
    [lane,`${success} / ${rs.length}`,fmt(mean(rs.map(r=>r.tiles))),fmt(mean(rs.map(r=>r.branches))),fmt(mean(rs.map(r=>r.seconds))),rs.reduce((s,r)=>s+(r.metrics.cluster_validation_attempts||0),0).toLocaleString()].forEach(v=>{const td=document.createElement("td");td.textContent=v;tr.append(td);});
    $("spatial-benchmark").append(tr);
  }
  const gcts=summary.find(s=>s.lane==="GCTS"),both=summary.find(s=>s.lane==="GCTS+RL");
  $("spatial-summary").textContent=`${donorCount} of ${library.donors.length} cold donor searches reached 64 tiles. ${stats.connected_subsets.toLocaleString()} connected subsets yielded ${stats.distinct_shapes.toLocaleString()} symmetry-normalized shapes; ${stats.recurrent_shapes.toLocaleString()} occurred in at least two donors, and ${stats.selected_types} types entered the frozen proposal library. ${d.training.updates} RL updates executed ${extra} extra continuation moves. At the 64-tile evaluation target, GCTS reaches ${gcts.success} starts in ${fmt(gcts.time)} seconds on average and GCTS+RL reaches ${both.success} in ${fmt(both.time)} seconds. ${both.success>=gcts.success&&both.time<gcts.time?"This pilot shows a per-search improvement; the construction and learning costs below remain additional.":"The spatial RL pilot has not shown an acceleration over GCTS alone."}`;
  $("spatial-cost").textContent=`Cold labeling ${fmt(d.pair_labels.seconds)} s; independent certificate replay ${fmt(d.pair_verification.seconds)} s; donor search ${fmt(library.donors.reduce((s,r)=>s+r.seconds,0))} s; motif extraction ${fmt(library.seconds)} s; spatial RL training ${fmt(d.training.seconds)} s; hierarchy inspection ${fmt(d.hierarchies.seconds)} s. Total ${fmt(d.total_seconds)} s; peak process memory ${(d.peak_process_memory_bytes/1048576).toFixed(1)} MiB. All lanes use the same three fixed starts, target, scheduler, and declared budgets. ${d.independent_audit?`A separate ${fmt(d.independent_audit.seconds)}-second audit checked all ${d.independent_audit.independent_interfaces} interfaces and ${d.independent_audit.checked_group_levels} group levels, rejected tampered interface and child data, and found no polygon overlaps in the displayed evaluation and donor patches.`:"Independent post-run audit pending."}`;
}
function proofResults(){
  const d=secondData.logic,w=secondData.wang_certificate_search;
  $("logic-statement").textContent=`\\[${d.statement}\\]`;
  $("logic-caption").textContent=`${d.rewrite_steps} discovered rewrites; ${d.proof.length} checked Hilbert lines. The checker rejects a modified conclusion. This is a certificate relative to the two registered addition axioms, not a full arithmetic theory or a general search benchmark.`;
  const axioms=document.createElement("p");axioms.textContent=d.axioms.map(a=>`\\(${a}\\)`).join("; ");$("logic-proof").append(axioms);
  d.display_proof.forEach((line,i)=>{const p=document.createElement("p"),raw=d.proof[i];const refs=raw.rule==="mp"?` from lines ${raw.antecedent+1} and ${raw.implication+1}`:"";p.textContent=`${i+1}. ${line.rule}${refs}: \\(${line.formula}\\)`;$("logic-proof").append(p);});
  const svg=$("certificate-tape"),rows=w.rows;
  if(rows){
    const cell=44,left=128,initial=w.initial,equal=initial.indexOf("=");
    [initial,initial,rows[rows.length-1]].forEach((row,i)=>{
      const y=15+i*62;svgText(svg,8,y+26,["Unknown input","Found input","Accepting row"][i],{fill:"#d8e5d3","font-size":11});
      row.forEach((s,j)=>{const x=left+j*cell,unknown=j>equal&&j<=equal+w.unknown_bottom_cells,isHead=Array.isArray(s);svg.append(el("rect",{x,y,width:cell-2,height:38,rx:3,fill:unknown?"#ce965f":"#476551",stroke:unknown?"#edd0a1":"#66846a"}));svgText(svg,x+21,y+25,i===0&&unknown?"?":String(isHead?s[2]:s),{"text-anchor":"middle",fill:"#fff6e7","font-size":15});});
    });
  }
  $("certificate-caption").textContent=w.verified?`The point search chose the unary certificate ${w.certificate.length} symbols long in a rectangle with ${w.width} columns and ${w.height} transition rows. ${w.tile_types.toLocaleString()} tile types; ${w.nodes.toLocaleString()} search nodes; ${fmt(w.seconds)} seconds. Independent operational TM replay, exact point marking checks, and an arithmetic count pass; a changed input is rejected.`:`Certificate search: ${w.status}. No accepting proof is claimed.`;
  if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise([$("logic-statement"),$("logic-proof")]).catch(()=>{});
}
function haloResults(){
  const d=haloData,svg=$("halo-marking"),assigned=new Map(d.snapshot_for_inspection_only.map(([p,v])=>[p.join(","),v]));
  const support=new Map();
  for(const [p] of data.point_model.occupancy)for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++){
    const z=-x-y;if(Math.max(Math.abs(x),Math.abs(y),Math.abs(z))>1)continue;
    const q=[p[0]+x,p[1]+y,p[2]+z];support.set(q.join(","),q);
  }
  const loop=data.point_model.vertices.map(project),ps=[...support.values()],all=loop.concat(ps.map(project));
  const xs=all.map(p=>p[0]),ys=all.map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  const scale=Math.min(380/(maxX-minX),290/(maxY-minY));
  const map=([x,y])=>[(x-(minX+maxX)/2)*scale+220,(y-(minY+maxY)/2)*scale+168];
  svg.append(el("polygon",{points:loop.map(p=>map(p).join(",")).join(" "),fill:"#eef1e7",stroke:"#8b9c85","stroke-width":2}));
  for(const p of ps){const [x,y]=map(project(p)),v=assigned.get(p.join(","));const dot=el("circle",{cx:x,cy:y,r:v===undefined?3.5:5.5,fill:v===undefined?"#fffdf8":colors[v%colors.length],stroke:"#fffdf8","stroke-width":1.4});dot.append(el("title",{},`Point ${p.join(",")}; marking ${v===undefined?"free":v}`));svg.append(dot);}
  const s=d.marking_summary,a=d.independent_validation;
  $("halo-caption").textContent=`${s.assigned} assigned values, ${s.free} free entries, ${s.colors} equality classes. The radius-one hypothesis accepts every original positive contact and rejects ${s.negative_rejected} of ${s.negatives} original failures. ${d.additional_disagreeing_contacts} further capacity-legal disagreements lie outside that catalog. All ${d.counts.negative||0} additional unmarked searches exhausted; ${d.counts.unresolved||0} remain unresolved.`;
  $("halo-validation").textContent=a?`Independent verification checked ${a.negative_proof_nodes.toLocaleString()} failure-tree nodes for all ${a.canonical_rejected_contacts.toLocaleString()} excluded contacts, plus ${a.transformed_exclusion_checks.toLocaleString()} transformed exclusions. Label probe ${fmt(d.seconds)} s; separate validation ${fmt(a.seconds)} s. The radius-one marking is now certified redundant for complete unmarked point-model tilings. It was not used in the iteration-02 benchmarks.`:"Independent negative-proof replay is still pending. This hypothesis remains inactive and is not yet certified redundant.";
}

function tableRow(body,values){
  const row=document.createElement("tr");
  values.forEach(value=>{const td=document.createElement("td");td.textContent=String(value);row.append(td);});
  $(body).append(row);
}
function coreSeeds(){
  const runs=thirdData.core_coverage.filter(r=>r.lane===$("core-lane").value),old=$("core-seed").value;
  $("core-seed").replaceChildren(...runs.map(r=>{const o=document.createElement("option");o.value=r.seed;o.textContent=String(r.seed);return o;}));
  if(runs.some(r=>String(r.seed)===old))$("core-seed").value=old;
  coreRadii();
}
function coreRadii(){
  const run=thirdData.core_coverage.find(r=>r.lane===$("core-lane").value&&String(r.seed)===$("core-seed").value),old=$("core-radius").value;
  $("core-radius").replaceChildren(...run.checkpoints.map((c,i)=>{const o=document.createElement("option");o.value=i;o.textContent=`Radius ${c.radius} · ${c.required_core_points} points`;return o;}));
  $("core-radius").value=run.checkpoints.some((_,i)=>String(i)===old)?old:String(run.checkpoints.length-1);
  coreView();
}
function coreView(){
  const run=thirdData.core_coverage.find(r=>r.lane===$("core-lane").value&&String(r.seed)===$("core-seed").value),c=run.checkpoints[Number($("core-radius").value)];
  if(!c){$("core-caption").textContent="No complete checkpoint was reached within this run's budget.";return;}
  const points=[];
  for(let x=-c.radius;x<=c.radius;x++)for(let y=-c.radius;y<=c.radius;y++)if(Math.max(Math.abs(x),Math.abs(y),Math.abs(x+y))<=c.radius)points.push([x,y,-x-y]);
  drawPatch($("core-view"),c.placements,{width:760,height:460,points});
  $("core-caption").textContent=`${run.lane} · seed ${run.seed} · ${c.tiles} base tiles fill all ${c.required_core_points} required points at radius ${c.radius}. ${c.frontier_points} exposed obligations remain; their full candidate domains pass independent replay. The complete run made ${run.core_activations} core activations, including retried transactions, and ${run.backtracks} backtracks.`;
}
function grammarSeeds(){
  const samples=thirdData.grammar_inspection[$("grammar-library").value].samples,old=$("grammar-seed").value;
  $("grammar-seed").replaceChildren(...samples.map(s=>{const o=document.createElement("option");o.value=s.seed;o.textContent=String(s.seed);return o;}));
  if(samples.some(s=>String(s.seed)===old))$("grammar-seed").value=old;
  grammarView();
}
function grammarView(){
  const name=$("grammar-library").value,g=thirdData.grammar_inspection[name],h=g.samples.find(h=>String(h.seed)===$("grammar-seed").value),level=h?.levels[Number($("grammar-level").value)];
  if(!level)return;
  const groups=[];level.groups.forEach((group,i)=>group.base_ids.forEach(k=>groups[k]=i));
  drawPatch($("grammar-view"),h.placements,{width:760,height:430,groups});
  $("grammar-caption").textContent=`Seed ${h.seed}: ${h.placements.length} base placements partition into ${level.groups.length} groups at level ${level.level}. Each base identity occurs once; summed point interfaces and child relations pass a separate checker. Colors distinguish groups.`;
  const boundary=g.classifiers.boundary,hull=g.classifiers.hull;
  $("grammar-finding").textContent=`${name==="frequency"?"Frequency control":"Diversity and rarity grouping"}: ${boundary.type_count} abstract boundary types and ${hull.type_count} hull types. ${boundary.types_with_growing_instances} boundary types and ${hull.types_with_growing_instances} hull types occur at three distinct base-tile counts. ${hull.parent_types_with_multiple_child_patterns} hull parent types have multiple observed child patterns. No stationary recursive rule was inferred.`;
}
function continuationResults(){
  const d=thirdData,lanes=[...new Set(d.core_coverage.map(r=>r.lane))];
  lanes.forEach(lane=>{const o=document.createElement("option");o.value=lane;o.textContent=lane;$("core-lane").append(o);const rs=d.core_coverage.filter(r=>r.lane===lane);tableRow("core-benchmark",[lane,`${rs.filter(r=>r.status==="consistent_finite_patch_with_core_coverage").length} / ${rs.length}`,fmt(mean(rs.map(r=>r.tiles))),fmt(mean(rs.map(r=>r.branches))),fmt(mean(rs.map(r=>r.seconds)))]);});
  $("core-lane").value="exterior GCTS";coreSeeds();grammarSeeds();
  const complete=d.core_coverage.filter(r=>r.status==="consistent_finite_patch_with_core_coverage").length;
  $("core-finding").textContent=`All ${complete} of ${d.core_coverage.length} matched starts completed four nested cores through radius 12, which has 469 lattice points. These patches contain ${Math.min(...d.core_coverage.map(r=>r.tiles))}–${Math.max(...d.core_coverage.map(r=>r.tiles))} base tiles. This target asks for covered obligations, so its results differ from a tile-count growth milestone.`;
  const library=d.spatial_libraries,ds=library.diversity.statistics;
  const successful=library.donors.filter(r=>r.status==="consistent_finite_patch").length,extra=d.training.episodes.reduce((sum,r)=>sum+r.sequence_extra_moves,0);
  $("diversity-finding").textContent=`${successful} of ${library.donors.length} fresh donor searches reached 96 tiles. The frequency control chose ${library.frequency.motifs.length} motifs. The invariant size/handedness-balance bins chose ${ds.selected_types}, including ${ds.mixed_handed_types} mixed-handed types. Their source patches were searched, never supplied as known tilings. ${d.training.updates} policy updates executed ${extra} extra sequence moves.`;
  const mixed=library.diversity.motifs.find(m=>m.category[1]>0);
  if(mixed)drawPatch($("diversity-motif"),mixed.expansion,{width:350,height:270,points:mixed.interface.frontier.map(p=>p[0])});
  const summaries=[...new Set(d.evaluation.map(r=>r.lane))].map(lane=>{const rs=d.evaluation.filter(r=>r.lane===lane),success=rs.filter(r=>r.status==="consistent_finite_patch").length;tableRow("continuation-benchmark",[lane,`${success} / ${rs.length}`,fmt(mean(rs.map(r=>r.tiles))),fmt(mean(rs.map(r=>r.branches))),fmt(mean(rs.map(r=>r.seconds))),rs.reduce((sum,r)=>sum+(r.metrics.cluster_validation_attempts||0),0).toLocaleString()]);return {lane,success,time:mean(rs.map(r=>r.seconds))};});
  const gcts=summaries.find(s=>s.lane==="exterior GCTS"),both=summaries.find(s=>s.lane==="exterior GCTS+RL");
  $("continuation-finding").textContent=`The exterior marking reaches ${gcts.success} of three 128-tile targets; the combined policy reaches ${both.success}. RL macro validation and ordering remain costly, and this study has not demonstrated an acceleration. Budget-limited prefixes are unknown, never non-tiling results. The no-RL lanes also keep complete base-placement search.`;
  const historical=d.reuse.compact_learning_seconds+d.reuse.exterior_additional_probe_seconds+d.reuse.exterior_independent_validation_seconds,a=d.independent_audit;
  $("continuation-cost").textContent=`Historical reused marking construction and replay: ${fmt(historical)} s. Fresh donors: ${fmt(library.donors.reduce((sum,r)=>sum+r.seconds,0))} s; library extraction: ${fmt(library.seconds)} s; grouping inspection: ${fmt(d.grammar_inspection.seconds)} s; RL training: ${fmt(d.training.seconds)} s. New pipeline including the timing repeat: ${fmt(d.total_seconds)} s; separate audit ${fmt(a?.seconds||0)} s; peak process memory ${(d.peak_process_memory_bytes/1048576).toFixed(1)} MiB. The original tile-count pass overlapped another research job and was replaced by sequential searches; both passes and their costs remain in the JSON. ${a?`The independent audit checked ${a.interfaces} interfaces, ${a.hierarchy_levels} partition levels, successful checkpoint coverage and exposed frontiers; all ${a.geometry.evaluation_runs.length} final/donor patches passed exact polygon non-overlap checks.`:"Final audit pending."}`;
  $("serialized-proof-caption").textContent="Both exported proof formats now replay from JSON. The logic replay uses an externally declared theory; the proof cannot nominate new axioms. Changed targets, a forged axiom, and a changed Wang input are rejected. This closes serialization replay, while the kernel-to-machine compiler remains open.";
  $("core-lane").addEventListener("change",coreSeeds);$("core-seed").addEventListener("change",coreRadii);$("core-radius").addEventListener("change",coreView);
  $("grammar-library").addEventListener("change",grammarSeeds);["grammar-seed","grammar-level"].forEach(id=>$(id).addEventListener("change",grammarView));
}

const ringEmbed=p=>p.reduce((sum,c,i)=>[sum[0]+c*Math.cos(2*i*Math.PI/5),sum[1]+c*Math.sin(2*i*Math.PI/5)],[0,0]);
function drawRhombs(svg,placements,{width=740,height=430,required=[],obstruction=false}={}){
  svg.replaceChildren();
  const loops=placements.map(([kind,r,tr])=>penroseData.point_model.vertices[kind].map(v=>{const [x,y]=ringEmbed(v),[a,b]=ringEmbed(tr),theta=r*Math.PI/5;return [x*Math.cos(theta)-y*Math.sin(theta)+a,-(x*Math.sin(theta)+y*Math.cos(theta)+b)];}));
  const points=required.map(([v])=>ringEmbed(v)).map(([x,y])=>[x,-y]),all=loops.flat().concat(points);
  if(!all.length)return;
  const xs=all.map(p=>p[0]),ys=all.map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),scale=Math.min((width-60)/Math.max(.1,maxX-minX),(height-50)/Math.max(.1,maxY-minY));
  const map=([x,y])=>[(x-(minX+maxX)/2)*scale+width/2,(y-(minY+maxY)/2)*scale+height/2];
  loops.forEach((loop,i)=>{const [kind,r,tr]=placements[i],poly=el("polygon",{points:loop.map(p=>map(p).join(",")).join(" "),fill:obstruction?(i?"#c76b3d":"#347999"):kind==="thick"?"#6d9c83":"#d19163","fill-opacity":.64,stroke:obstruction?"#9e424a":i<2?"#23332f":"#476651","stroke-width":i<2?2:1.2});poly.append(el("title",{},`${kind}; rotation ${r}; translation ${tr.join(",")}`));svg.append(poly);});
  const seen=new Set();points.forEach(p=>{const id=p.join(",");if(seen.has(id))return;seen.add(id);const [x,y]=map(p);svg.append(el("circle",{cx:x,cy:y,r:4,fill:"#ce9b3f",stroke:"#fffdf8","stroke-width":1.2}));});
}
function rhombView(){
  const s=penroseData.pair_labels.samples[Number($("rhomb-contact").value)];
  drawRhombs($("rhomb-star"),s.placements,{required:s.required_points});
  $("rhomb-caption").textContent=`${s.root_kind} root · contact ${Number($("rhomb-contact").value)+1} · ${s.tiles} rhombs · ${s.nodes} search nodes. All ${s.required_points.length} initial sector slots are filled; ${s.frontier_points} exposed slots remain viable under independent complete re-enumeration. Gold dots mark initial vertices; darker outlines identify the fixed pair. Exact polygon audit found ${s.independent_polygon_overlaps?.length||0} overlapping pairs.`;
}
function penroseResults(){
  const d=penroseData,m=d.marking,a=d.independent_audit;
  d.pair_labels.samples.forEach((s,i)=>{const o=document.createElement("option");o.value=i;o.textContent=`${i+1} · ${s.root_kind} + ${s.second[0]} · ${s.status}`;$("rhomb-contact").append(o);});
  rhombView();drawRhombs($("dense-obstruction"),d.dense_support_obstruction.placements,{width:430,height:300,obstruction:true});
  $("penrose-finding").textContent=`160 capacity-legal transformed contacts for each root prototype: ${d.pair_labels.counts.positive||0} positive, ${d.pair_labels.counts.negative||0} negative, ${d.pair_labels.counts.unresolved||0} unresolved. Every resolved label enters equality synthesis. The final equality state has ${m.history.at(-1).components} class; ${m.assigned} of ${m.support_slots} slots are assigned and ${m.free} remain free. The resulting GCTS lane is therefore identical to the unmarked lane.`;
  $("penrose-audit").textContent=`All ${a.positive_witnesses} pair completions pass independent occupancy, initial-star coverage, and exposed-frontier checks. Exact algebraic polygon tests checked ${a.polygon_pairs_checked.toLocaleString()} pairs and found overlap in ${a.patches_with_polygon_overlap} patches. Cold search ${fmt(d.pair_labels.seconds)} s; independent audit ${fmt(a.seconds)} s; total ${fmt(d.total_seconds)} s; peak memory ${(d.peak_process_memory_bytes/1048576).toFixed(1)} MiB. Alias placements are retained as distinct inventory identities; this count is not a count of geometric orbits.`;
  $("ring-caption").textContent=`${data.penrose.exact_pair_checks.toLocaleString()} exact multiplication/conjugation checks passed. The new pilot below adds unmarked vertex-sector contact search; a faithful plane model and Penrose hierarchy remain open.`;
  $("rhomb-contact").addEventListener("change",rhombView);
}

function selectRun(){
  const lane=$("lane").value;
  const runs=data.evaluation.filter(r=>r.lane===lane);
  const old=$("seed").value;
  $("seed").replaceChildren(...runs.map(r=>{const o=document.createElement("option");o.value=r.seed;o.textContent=String(r.seed);return o;}));
  if(runs.some(r=>String(r.seed)===old))$("seed").value=old;
  currentRun=runs.find(r=>String(r.seed)===String($("seed").value))||runs[0];
  $("step").max=currentRun.placements.length;$("step").value=currentRun.placements.length;
  updatePatch();
}
function updatePatch(){
  const n=Number($("step").value);
  drawPatch($("patch"),currentRun.placements.slice(0,n));
  $("step-count").textContent=`${n} / ${currentRun.placements.length}`;
  $("patch-status").textContent=currentRun.status==="consistent_finite_patch"?"Verified finite growth checkpoint":currentRun.status==="unknown_budget"?"Best viable prefix · budget limited":"Growth goal exhausted · finite prefix";
  $("patch-caption").textContent=`${currentRun.lane} · ${currentRun.tiles} base tiles · ${currentRun.branches} branches · ${currentRun.forced} forced moves · ${currentRun.backtracks} backtracks · ${fmt(currentRun.seconds)} seconds. ${currentRun.frontier_points} frontier points; ${currentRun.candidate_nodes} shared candidates at this checkpoint.`;
}
function marking(){
  const svg=$("marking"),snapshot=data.marking.snapshot_for_inspection_only;
  const assignments=new Map(snapshot.map(([p,v])=>[p.join(","),v]));
  const loop=data.point_model.vertices.map(project),points=data.point_model.occupancy.map(([p])=>project(p));
  const all=loop.concat(points),xs=all.map(p=>p[0]),ys=all.map(p=>p[1]);
  const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  const scale=Math.min(330/(maxX-minX),305/(maxY-minY));
  const map=([x,y])=>[(x-(minX+maxX)/2)*scale+195,(y-(minY+maxY)/2)*scale+168];
  svg.append(el("polygon",{points:loop.map(p=>map(p).join(",")).join(" "),fill:"#eef1e7",stroke:"#8b9c85","stroke-width":2}));
  data.point_model.occupancy.forEach(([p,w])=>{const [x,y]=map(project(p)),v=assignments.get(p.join(","));const n=el("circle",{cx:x,cy:y,r:v===undefined?4.5:7.5,fill:v===undefined?"#fffdf8":colors[v%colors.length],stroke:v===undefined?"#a9b5a3":"white","stroke-width":1.8});n.append(el("title",{},`Point ${p.join(",")}; occupancy ${w} integer units; marking ${v===undefined?"free":v}`));svg.append(n);});
  svgText(svg,24,347,`${data.marking.colors} equality classes · ${data.marking.free} free prototype entries`);
  $("marking-caption").textContent=`${data.marking.positive_accepted} / ${data.marking.positives} positive contacts accepted. ${data.marking.negative_rejected} / ${data.marking.negatives} certified failures rejected. ${data.marking.redundancy_checks?.transformed_contact_checks||3648} transformed contacts checked.`;
}
function pairView(){
  const index=Number($("pair").value),s=data.pair_catalog.samples[index];
  let placements=[[0,[0,0,0]],s.second],dead=null;
  if(s.status==="positive")placements=s.witness;
  else if(s.certificate){let node=s.certificate;while(node.children?.length){const child=node.children[0];placements.push(child.placement);node=child.proof;}dead=node.dead;}
  drawPatch($("pair-view"),placements,{dead,width:640,height:350});
  $("pair-outcome").textContent=s.status==="positive"?"Witnessed one-corona completion":s.status==="negative"?"Certified exhausted extension":"Unresolved · no exclusion learned";
  $("pair-detail").textContent=`Contact ${index+1} of ${data.pair_catalog.count}. Search inspected ${s.nodes} nodes, with ${s.branches} branch decisions, ${s.forced} forced moves, and ${s.backtracks} backtracks. ${dead?"The red ring marks a frontier point with no legal candidate in the first proof leaf.":"Every initial pair point reaches full capacity; the exposed frontier remains viable."}`;
}
function benchmark(){
  const svg=$("benchmark-chart"),lanes=["baseline","GCTS","RL","GCTS+RL"];
  const summaries=lanes.map(lane=>{const rs=data.evaluation.filter(r=>r.lane===lane);return {lane,rs,time:mean(rs.map(r=>r.seconds)),success:rs.filter(r=>r.status==="consistent_finite_patch").length};});
  const max=Math.max(1,...summaries.map(s=>s.time))*1.1;
  svgText(svg,170,28,"Mean search time · seconds",{"font-size":13,fill:"#23332f"});
  svgText(svg,745,28,`Verified target patches · ${data.config.target} base tiles`,{"font-size":13,fill:"#23332f"});
  for(let i=0;i<=4;i++){const x=170+i*470/4;svg.append(el("line",{x1:x,y1:43,x2:x,y2:251,stroke:"#d9ded5"}));svgText(svg,x,274,fmt(max*i/4),{"text-anchor":"middle","font-size":10});}
  summaries.forEach((s,i)=>{
    const y=60+i*50;
    svgText(svg,12,y+20,s.lane,{fill:"#23332f","font-size":14});
    svg.append(el("rect",{x:170,y,width:470*s.time/max,height:28,rx:3,fill:colors[i]}));
    svgText(svg,180+470*s.time/max,y+19,fmt(s.time),{"font-size":11});
    for(let j=0;j<s.rs.length;j++)svg.append(el("circle",{cx:765+j*28,cy:y+14,r:8,fill:j<s.success?"#276a53":"#e2ded2"}));
    svgText(svg,780+s.rs.length*28,y+19,`${s.success}/${s.rs.length}`,{"font-size":12});
    const row=document.createElement("tr");
    [s.lane,`${s.success} / ${s.rs.length}`,fmt(mean(s.rs.map(r=>r.tiles))),fmt(mean(s.rs.map(r=>r.nodes))),fmt(mean(s.rs.map(r=>r.branches))),fmt(mean(s.rs.map(r=>r.backtracks))),fmt(s.time)].forEach(v=>{const td=document.createElement("td");td.textContent=v;row.append(td);});$("benchmark-body").append(row);
  });
  const donorSeconds=data.cluster_library.donors.reduce((s,r)=>s+r.seconds,0);
  const [base,gcts,rl,both]=summaries;
  $("benchmark-finding").textContent=`The pilot reaches the growth target on ${base.success} of ${base.rs.length} starts in the baseline and ${gcts.success} of ${gcts.rs.length} with GCTS. GCTS lowers mean search time from ${fmt(base.time)} to ${fmt(gcts.time)} seconds; its cold learning and verification cost is much larger than that per-search saving. RL reaches ${rl.success} starts and GCTS+RL reaches ${both.success}; the combined policy takes ${fmt(both.time)} seconds on average. This RL prototype has not demonstrated a speedup over GCTS alone.`;
  $("cost-caption").textContent=`Cold pair labeling: ${fmt(data.pair_catalog.seconds)} s. Independent certificate replay: ${fmt(data.pair_verification.seconds)} s. Single-move training: ${fmt(data.single_training.seconds)} s. Cluster donor search: ${fmt(donorSeconds)} s. Sequence RL training: ${fmt(data.cluster_training.seconds)} s. Cold pipeline: ${fmt(data.total_seconds)} s. Separate exact geometry audit: ${fmt(data.geometry_audit?.seconds||0)} s. Peak process resident memory ${(data.peak_process_memory_bytes/1048576).toFixed(1)} MiB.`;
}
function motifs(){
  const library=data.cluster_library.motifs;
  const extra=data.cluster_training.episodes.reduce((s,r)=>s+r.sequence_extra_moves,0);
  $("cluster-caption").textContent=`${library.length} inspected sequence motifs were mined from ${data.cluster_library.donors.filter(r=>r.status==="consistent_finite_patch").length} successful donor patches. ${data.cluster_training.updates} on-policy updates trained sequence selection; ${extra} continuation moves actually executed beyond a proposal's first tile during training.`;
  for(const m of library.slice(0,3)){const svg=el("svg",{viewBox:"0 0 230 180",role:"img","aria-label":`Learned sequence of ${m.expansion.length} placements`});drawPatch(svg,m.expansion,{width:230,height:180});$("motif-strip").append(svg);}
  $("inflation-results").textContent=data.inflation_controls.map(r=>`Scale ${r.scale}: ${r.status==="exhausted_finite_self_inflation"?"exhausted finite self-inflation test":r.status.replaceAll("_"," ")} (${r.nodes} search nodes).`).join(" ");
}
function penrose(){
  const svg=$("rhombs"),z={re:Math.cos(2*Math.PI/5),im:Math.sin(2*Math.PI/5)};
  const embed=p=>p.reduce((s,c,i)=>[s[0]+c*Math.cos(i*2*Math.PI/5),s[1]+c*Math.sin(i*2*Math.PI/5)],[0,0]);
  Object.entries(data.penrose.rhombs).forEach(([name,tile],i)=>{
    const loop=tile.vertices.map(embed),xs=loop.map(p=>p[0]),ys=loop.map(p=>p[1]);
    const cx=120+i*240,cy=85,scale=76;
    const mx=(Math.min(...xs)+Math.max(...xs))/2,my=(Math.min(...ys)+Math.max(...ys))/2;
    svg.append(el("polygon",{points:loop.map(([x,y])=>`${cx+(x-mx)*scale},${cy-(y-my)*scale}`).join(" "),fill:colors[i],"fill-opacity":.75,stroke:"#476651","stroke-width":1.5}));
    svgText(svg,cx,172,`${name} · unmarked`,{"text-anchor":"middle","font-size":12});
  });
  $("ring-caption").textContent=`${data.penrose.exact_pair_checks.toLocaleString()} exact multiplication/conjugation checks passed. Unmarked rhomb contact search is recorded in the separate pilot below.`;
}
function computation(){
  const svg=$("computation"),rows=data.wang.rows,cell=66,left=120;
  rows.forEach((row,i)=>{
    const y=195-i*73;
    svgText(svg,16,y+25,i===0?"Start":i===rows.length-1?"Accept":`Step ${i}`,{fill:"#d8e5d3","font-size":13});
    row.forEach((s,j)=>{
      const head=Array.isArray(s),x=left+j*cell;
      svg.append(el("rect",{x,y,width:cell-3,height:43,rx:3,fill:head?"#ce965f":"#476551",stroke:head?"#edd0a1":"#66846a","stroke-width":1}));
      svgText(svg,x+31,y+26,String(head?s[2]:s),{"text-anchor":"middle",fill:"#fff6e7","font-size":17});
      if(head)svgText(svg,x+31,y-7,s[1],{"text-anchor":"middle",fill:"#e2bf8e","font-size":10});
      if(i<rows.length-1)svg.append(el("line",{x1:x+31,y1:y-10,x2:x+31,y2:y-27,stroke:"#779a78","stroke-width":1}));
    });
  });
  $("wang-caption").textContent=`${data.wang.tile_types} compiled tile types. A ${rows[0].length}-column, ${rows.length-1}-step accepting rectangle was searched and independently verified. The tampered acceptance certificate was rejected. This is a computation demonstration, not yet a theorem prover.`;
}
async function main(){
  try{
    const response=await fetch("iteration-001.json?v=20261009-r4.2",{cache:"no-cache"});
    if(!response.ok)throw new Error(`Snapshot returned ${response.status}`);
    data=await response.json();
    if(!data.evaluation||!data.wang)throw new Error("Iteration is still running; the final checkpoint is not ready.");
    $("pair-count").textContent=data.pair_catalog.count;
    $("negative-count").textContent=data.pair_catalog.counts.negative;
    $("mark-reject-count").textContent=data.marking.negative_rejected;
    $("assigned-count").textContent=data.marking.assigned;
    $("load-status").textContent=`Iteration 01 · ${data.pair_verification.negative_proof_nodes} independent failure-tree nodes checked · all ${data.pair_catalog.count} contact labels resolved.`;
    data.pair_catalog.samples.forEach((s,i)=>{const o=document.createElement("option");o.value=i;o.textContent=`${i+1} · ${s.status} · orientation ${s.second[0]}`;$("pair").append(o);});
    selectRun();marking();pairView();benchmark();motifs();penrose();computation();
    const secondResponse=await fetch("iteration-002.json?v=20261009-r4.2",{cache:"no-cache"});
    if(!secondResponse.ok)throw new Error(`Second snapshot returned ${secondResponse.status}`);
    secondData=await secondResponse.json();
    if(!secondData.total_seconds)throw new Error("Second cold run is still computing; final evidence is not ready.");
    spatialResults();proofResults();
    const haloResponse=await fetch("halo-probe-002.json?v=20261009-r4.2",{cache:"no-cache"});
    if(!haloResponse.ok)throw new Error(`Halo snapshot returned ${haloResponse.status}`);
    haloData=await haloResponse.json();haloResults();
    const thirdResponse=await fetch("iteration-003.json?v=20261009-r4.2",{cache:"no-cache"});
    if(!thirdResponse.ok)throw new Error(`Third snapshot returned ${thirdResponse.status}`);
    thirdData=await thirdResponse.json();
    if(!thirdData.independent_audit||!thirdData.evaluation_repeat)throw new Error("The third study's repeat or final audit is still pending.");
    continuationResults();
    const penroseResponse=await fetch("penrose-001.json?v=20261009-r4.2",{cache:"no-cache"});
    if(!penroseResponse.ok)throw new Error(`Penrose snapshot returned ${penroseResponse.status}`);
    penroseData=await penroseResponse.json();penroseResults();
    const proofResponse=await fetch("proof-search-001.json?v=20261009-r4.2",{cache:"no-cache"});
    if(!proofResponse.ok)throw new Error(`Proof snapshot returned ${proofResponse.status}`);
    proofData=await proofResponse.json();
    if(!proofData.independent_audit||!proofData.semantic_tests)throw new Error("Generic proof audit is pending.");
    genericProofResults();
    const clusterResponse=await fetch("cluster-types-001.json?v=20261009-r4.2",{cache:"no-cache"});
    if(!clusterResponse.ok)throw new Error(`Cluster type snapshot returned ${clusterResponse.status}`);
    clusterData=await clusterResponse.json();clusterTileResults();
    $("load-status").textContent=`Three turtle studies, a cold rhomb pilot, and generic word-proof search recorded · ${proofData.semantic_tests.passed} semantic tests pass · finite certificates independently replayed.`;
    if(data.geometry_audit){const a=data.geometry_audit;$("geometry-caption").textContent=a.all_reported_patches_nonoverlapping?`An independent audit using exact triangulation and rational clipping found no positive-area polygon overlap in any of the ${a.evaluation_runs.length} displayed evaluation patches. This certifies finite non-overlap, not coverage of the plane or faithfulness of the entire point model.`:`The independent polygon audit found overlaps in some point-model patches; inspect the JSON before treating a point patch as a geometric tiling.`;}
    $("lane").addEventListener("change",selectRun);
    $("seed").addEventListener("change",()=>{currentRun=data.evaluation.find(r=>r.lane===$("lane").value&&String(r.seed)===$("seed").value);$("step").max=currentRun.placements.length;$("step").value=currentRun.placements.length;updatePatch();});
    $("step").addEventListener("input",updatePatch);
    $("pair").addEventListener("change",pairView);
    $("play").addEventListener("click",()=>{if(timer){clearInterval(timer);timer=null;$("play").textContent="Play growth";return;}$("step").value=1;updatePatch();$("play").textContent="Pause";timer=setInterval(()=>{const n=Number($("step").value)+1;if(n>currentRun.placements.length){clearInterval(timer);timer=null;$("play").textContent="Play growth";return;}$("step").value=n;updatePatch();},300);});
    $("provenance").textContent=`Started ${new Date(data.date).toLocaleString("en-US",{timeZone:"America/Los_Angeles",dateStyle:"long",timeStyle:"short"})}; third turtle study ${new Date(thirdData.date).toLocaleString("en-US",{timeZone:"America/Los_Angeles",dateStyle:"long",timeStyle:"short"})}; generic proof pilot ${new Date(proofData.date).toLocaleString("en-US",{timeZone:"America/Los_Angeles",dateStyle:"long",timeStyle:"short"})}, Pacific time. Source SHA-256 hashes, budgets, placements, proofs, training traces, explicit marking reuse, and the timing correction are in the JSON. No substitution or plane-tiling proof has been produced.`;
  }catch(error){$("load-status").textContent=`Experiment data could not be loaded: ${error.message}`;$("load-status").style.color="#a5343f";}
}
main();
