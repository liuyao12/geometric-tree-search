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
let data,secondData,haloData,thirdData,penroseData,proofData,clusterData,regionData,clusterMarkData,complexData,starPilotData,kernelData,coarseData,multiScaleData,multiScaleStage,timer=null,currentRun,currentProof,currentProofRows;
const multiScaleCache=new Map();let multiScaleRequest=0;
const suiteTests=()=>coarseData?.semantic_tests?.passed??multiScaleData?.semantic_tests?.passed??kernelData?.semantic_tests?.passed??complexData?.semantic_tests?.passed??clusterMarkData?.semantic_tests.passed??regionData?.semantic_tests.passed??proofData.semantic_tests.passed;

function coarseElimination(){
  const d=coarseData.elimination,svg=$('coarse-elimination');svg.replaceChildren();
  const selected=$('coarse-parent').value,cw=62,left=286,top=56,rh=95;
  d.original_types.forEach((n,i)=>svgText(svg,left+i*cw+23,25,n.slice(-2),{'font-size':12,'text-anchor':'middle'}));
  d.rounds.forEach((r,j)=>{
    const y=top+j*rh,active=new Set(r.active),excluded=new Set(r.eliminated);
    svgText(svg,14,y+22,`Step ${r.round} · ${r.active.length} active types`,{'font-size':15,fill:'#23332f'});
    svgText(svg,14,y+43,`${r.eliminated.length} new checked exclusions`,{'font-size':12});
    d.original_types.forEach((n,i)=>{const x=left+i*cw,fill=excluded.has(n)?'#c97940':active.has(n)?'#6d9c83':'#e1e4da';
      const box=el('rect',{x,y,width:46,height:43,rx:5,fill,stroke:n===selected?'#834853':'none','stroke-width':3});box.append(el('title',{},`${n}; ${excluded.has(n)?'excluded in this proof step':active.has(n)?'retained at this step':'excluded earlier'}`));svg.append(box);
      svgText(svg,x+23,y+27,n.slice(-2),{'text-anchor':'middle',fill:active.has(n)?'#fffdf8':'#7a8376','font-size':13});
      if(j<d.rounds.length-1)svg.append(el('line',{x1:x+23,y1:y+51,x2:x+23,y2:y+76,stroke:'#b8c8b4','stroke-width':1.2}));
    });
  });
  $('coarse-elimination-caption').textContent='Orange: newly excluded by complete failure trees. Green: retained at that step, including every unknown. Gray: excluded by an earlier proved premise. Type numbers are identifiers. Purple outlines follow the selected shape. The last step leaves no type.';
}
function coarseView(){
  const d=coarseData,name=$('coarse-parent').value,mode=$('coarse-control').value,definitions=d.elimination.definitions,types=new Map(definitions.map(t=>[t.identity,t]));
  const round=d.elimination.rounds.find(r=>r.eliminated.includes(name)),study=mode==='reference'?d.reference:mode==='capacity'?d.capacity_control:round,r=study.results.find(r=>r.root===name),t=types.get(name),active=study.active??study.active_types;
  drawClusterValues($('coarse-prototype'),t,[],500,390);
  $('coarse-prototype-caption').textContent=`${name} · four distinct base turtles; level ${t.level}; ${t.occupancy.length} positive support points. The two child maps descend to level one. Every own and inherited marking slot is free. The earlier base-positive contact declares this shape; its base completion witness is unavailable to coarse search.`;
  let placements=r.placements,dead=null;
  if(r.status==='negative'){placements=[[name,0,[0,0,0]]];let node=r.certificate;while(node.children?.length){const c=node.children[0];placements.push(c.placement);node=c.proof;}dead=node.dead;}
  const bases=[],groups=[];placements.forEach(([n,o,tr],i)=>types.get(n).expansion.forEach(k=>{bases.push(movedBase(k,o,tr));groups.push(i);}));
  drawPatch($('coarse-proof'),bases,{points:r.required,dead,width:620,height:390,groups});
  $('coarse-proof-caption').textContent=`${mode==='elimination'?`Proof step ${round.round}`:mode==='capacity'?'Analytic capacity control':'Initial unmarked gate'} · ${active.length} active parent types · ${r.nodes} nodes, ${r.branches} branches, ${r.forced} forced moves · ${fmt(r.seconds)} s including ${fmt(r.construction_seconds)} s initial graph construction. ${r.status==='negative'?`A complete checked failure tree has ${r.independent_failure_audit.nodes} nodes. The first dead leaf is circled in red; group colors identify atomic parents.`:r.status==='unresolved'?'The cooperative budget ends with an unknown. This partial prefix is not a completion or a non-tiling proof.':'A finite root completion has checked viable exposed domains; no infinite continuation follows.'} Gold dots mark the initial parent’s completion target. Polygon drawing never decides legality.`;
  coarseElimination();
}
function coarseResults(){
  const d=coarseData,a=d.independent_audit,f=d.elimination;
  $('coarse-parent').replaceChildren(...f.original_types.map(n=>choice(n,`${n} · excluded at step ${f.eliminated_at[n]}`)));$('coarse-parent').value='coarse-parent-00';
  ['coarse-parent','coarse-control'].forEach(id=>$(id).addEventListener('change',coarseView));coarseView();
  $('coarse-finding').textContent=`All ${a.eliminated_types} parent types are ruled out from complete tilings by this joint library. The checked exclusion rounds remove four, four and five types. ${a.reference_and_elimination_failure_nodes} unmarked coarse failure-tree nodes support the induction. Every prior local assembly had a base completion, yet their combined parent library cannot tile the whole point domain. The base turtle problem remains open.`;
  const rows=[['Initial reference / step 0',d.reference],['Analytic capacity control',d.capacity_control],...f.rounds.slice(1).map(r=>[`Elimination step ${r.round}`,r])];
  rows.forEach(([label,s])=>{const counts=s.results.reduce((c,r)=>(c[r.status]=(c[r.status]||0)+1,c),{});tableRow('coarse-benchmark',[label,(s.active??s.active_types).length,`${counts.negative||0} / ${counts.unresolved||0} / ${counts.positive||0}`,fmt(s.results.reduce((n,r)=>n+r.seconds,0)),fmt(s.results.reduce((n,r)=>n+(r.independent_failure_audit?.seconds||0),0))]);});
  $('coarse-cost').textContent=`Initial unmarked gate and first audits ${fmt(d.reference.seconds)} s; separate analytic control ${fmt(d.capacity_control.seconds)} s; subsequent elimination rounds and first audits ${fmt(f.seconds)} s. Saved-data audit ${fmt(a.seconds)} s, peak audit memory ${(a.peak_audit_process_memory_bytes/1048576).toFixed(1)} MiB. Search-process peak memory was not instrumented in these initial gates; exact compiled-key counts are retained. Initial controls allow 4,000 nodes and 15 seconds per root; later rounds allow 6,000 nodes and 20 seconds. Limits are cooperative and can overshoot during complete graph updates. Timings are one sequential pass, include unresolved attempts, and compare different proved inventory contexts; they are not equal-success speed ratios. No marking or RL training is charged here because neither runs in this gate.`;
  $('coarse-audit').textContent=`Independent replay checks ${a.positive_shape_witnesses} reused base-positive shape witnesses, all ${a.states_replayed} exported coarse prefixes, ${a.reference_and_elimination_failure_nodes} reference/elimination tree nodes, ${a.analytic_failure_nodes} separate analytic tree nodes and ${a.transformed_parent_expansions} transformed expansions. It reconstructs every active-inventory premise and rejects ${a.tampered_trees_rejected} altered trees. No finite coarse completion was found. ${suiteTests()} semantic tests pass.`;
}

const choice=(value,label)=>{const o=document.createElement('option');o.value=value;o.textContent=label;return o;};
async function loadMultiScaleStage(){
  const index=Number($('multiscale-stage').value),ticket=++multiScaleRequest,decl=multiScaleData.stages[index];
  $('multiscale-values-caption').textContent='Loading this level’s full labels and actual value history…';
  ['multiscale-type','multiscale-values','multiscale-contact','multiscale-step'].forEach(id=>$(id).disabled=true);
  try{
    if(!multiScaleCache.has(index)){
      const response=await fetch(`${decl.artifact}?v=20261009-r10.1`,{cache:'no-cache'});
      if(!response.ok)throw new Error(`Level data returned ${response.status}`);
      multiScaleCache.set(index,await response.json());
    }
    if(ticket!==multiScaleRequest)return;
    multiScaleStage=multiScaleCache.get(index);
    $('multiscale-type').replaceChildren(...multiScaleStage.prototypes.map(t=>choice(t.identity,t.identity)));
    $('multiscale-values').querySelector('[value="inherited"]').disabled=index===0;
    if(index===0&&$('multiscale-values').value==='inherited')$('multiscale-values').value='final';
    $('multiscale-step').max=multiScaleStage.catalog_count;$('multiscale-step').value=multiScaleStage.catalog_count;
    $('multiscale-contact').replaceChildren(...multiScaleStage.samples.map((s,i)=>choice(i,`${i+1} · ${s.contact[0]} + ${s.contact[1]} · ${s.status}`)));
    const positive=multiScaleStage.samples.findIndex(s=>s.status==='positive'&&s.contact[0]!==s.contact[1]);
    $('multiscale-contact').value=positive<0?0:positive;
    ['multiscale-type','multiscale-values','multiscale-contact','multiscale-step'].forEach(id=>$(id).disabled=false);
    multiScaleValuesView();multiScaleContactView();
  }catch(error){if(ticket===multiScaleRequest)$('multiscale-values-caption').textContent=`Level could not be loaded: ${error.message}`;}
}
function multiScaleValuesView(){
  const d=multiScaleStage,t=d.prototypes.find(t=>t.identity===$('multiscale-type').value),mode=$('multiscale-values').value,n=Number($('multiscale-step').value),h=d.history[n-1];
  const own=d.markings[t.identity],inherited=t.marks.filter(([[p,ch]])=>ch==='cluster:1').map(([[p],v])=>[p,v]);
  const values=mode==='online'?h.values.filter(([name])=>name===t.identity).map(([,p,v])=>[p,v]):mode==='inherited'?inherited:own;
  drawClusterValues($('multiscale-values-drawing'),t,values);$('multiscale-step-value').textContent=n;
  $('multiscale-step').disabled=mode!=='online';
  $('multiscale-values-caption').textContent=mode==='online'?`After ${n} labels across this level: ${h.counts.positive||0} positive, ${h.counts.negative||0} negative, ${h.counts.unresolved||0} unknown; ${h.classes} equality classes. This prototype shows ${values.length} actual provisional values. They never filter the label oracle.`:mode==='inherited'?`${values.length} inherited level-one components from the two child maps. These colors share the child palette and stay distinct from the parent’s new channel.`:`${t.identity}: ${own.length} own-level assigned values and ${t.occupancy.length-own.length} free entries. Across this level: ${d.statistics.colors} scalar colors. Hollow points are free; zero is assigned. Polygon outlines show base constituents.`;
}
function multiScaleContactView(){
  const d=multiScaleStage,s=d.samples[Number($('multiscale-contact').value)];let placements=s.witness??s.seed_expansion,dead=null;
  if(s.status==='negative'){placements=[...s.seed_expansion];let node=s.certificate;while(node.children?.length){const c=node.children[0];placements.push(c.placement);node=c.proof;}dead=node.dead;}
  drawPatch($('multiscale-contact-drawing'),placements,{dead,width:560,height:400});
  const [a,b,o,tr]=s.contact,g=syms[o],left=new Map(d.markings[a].map(([p,v])=>[JSON.stringify(p),v]));
  const rejects=d.markings[b].some(([p,v])=>{const q=g.p.map((j,i)=>g.s*p[j]+tr[i]),k=JSON.stringify(q);return left.has(k)&&left.get(k)!==v;});
  $('multiscale-contact-caption').textContent=`${a} + ${b} · ${s.nodes} unmarked base-search nodes, ${s.branches} branches, ${s.forced} forced moves. ${s.status==='positive'?'A checked finite completion fills the original support and leaves viable exposed obligations.':s.status==='negative'?'The complete search tree fails; the red ring shows its first checked dead leaf.':'A finite cutoff leaves this contact unknown.'} The final own-level scalar values ${rejects?'exclude':'accept'} this contact. Finite viability does not imply plane continuation.`;
  if($('multiscale-values').value==='online'){$('multiscale-step').value=Number($('multiscale-contact').value)+1;multiScaleValuesView();}
}
function multiScaleRegionView(){
  const d=multiScaleData,lane=$('multiscale-lane').value,b=d.problems.find(b=>b.identity===$('multiscale-region').value),r=d.evaluation.find(r=>r.lane===lane&&r.problem===b.identity&&r.replicate===Number($('multiscale-replicate').value));
  const types=new Map(d.inventories[lane].map(t=>[t.identity,t])),owners=new Map();
  r.state.placements.forEach(([name,o,tr],i)=>types.get(name).expansion.forEach(k=>owners.set(JSON.stringify(movedBase(k,o,tr)),[i,types.get(name).level])));
  const fills=r.state.base_expansion.map(k=>{const [i,level]=owners.get(JSON.stringify(k));return level===2?'#925e82':`hsl(${i*137.508%360} 32% 56%)`;});
  drawPatch($('multiscale-region-drawing'),r.state.base_expansion,{points:b.required,width:720,height:430,fills});
  const parents=r.state.placements.filter(k=>types.get(k[0]).level===2).length;
  $('multiscale-region-caption').textContent=`${b.identity} · ${b.required.length} required points · ${r.accepted_base_tiles} base constituents in ${r.accepted_cluster_tiles} atomic tiles, including ${parents} parents (purple). Gold dots are required points. ${r.status==='finite_exact_region'?'Every required point is checked at full capacity.':`Budget-limited, ${(100*r.coverage_fraction).toFixed(1)}% of required points full; this is unknown.`} Group colors identify ownership; drawings never decide legality.`;
  $('multiscale-region-state').textContent=`${fmt(r.seconds)} s for this request, including ${fmt(r.compilation_seconds)} s of boundary filtering and inventory indexing; the total also includes fresh graph construction. ${r.nodes.toLocaleString()} nodes, ${r.branches} branches, ${r.forced} forced moves and ${r.backtracks} backtracks; ${r.attempted_base_placements} actual base-placement attempts. The peak graph has ${r.peak_candidate_nodes.toLocaleString()} candidate nodes and ${r.peak_incidences.toLocaleString()} incidences. Up-front frozen inventory and learning costs are reported below.`;
}
async function multiScaleResults(){
  const d=multiScaleData,a=d.independent_audit,[first,second]=d.stages;
  $('multiscale-finding').textContent=`Level one: ${first.catalog_count.toLocaleString()} contacts, ${first.statistics.counts.positive} finite positives and ${first.statistics.counts.negative.toLocaleString()} certified failures; shared values encode ${first.statistics.negative_rejected.toLocaleString()} failures. The new parent’s ${second.catalog_count} contacts all fail. Its own channel adds ${a.parent_new_own_exclusions} exclusions beyond inheritance. Learning a second scale exposes an unsuitable recurrent parent.`;
  d.stages.forEach((s,i)=>{const m=s.statistics;tableRow('multiscale-labels',[i+1,s.catalog_count.toLocaleString(),`${m.counts.positive||0} / ${m.counts.negative||0} / ${m.counts.unresolved||0}`,`${m.assigned} / ${m.free}`,m.negative_rejected.toLocaleString()]);});
  $('multiscale-obstruction').textContent=`All ${a.parent_only_obstruction.exhausted_contact_contexts} possible parent–parent contacts have independently checked unmarked base failure trees (${a.parent_only_obstruction.checked_base_failure_nodes} tree nodes). No complete point tiling by disjoint occurrences of this parent alone exists. This does not decide the base turtle plane problem or rule out the mixed hierarchy.`;
  $('multiscale-region').replaceChildren(...d.problems.map(b=>choice(b.identity,b.identity)));
  $('multiscale-lane').replaceChildren(...d.configuration.lanes.map(l=>choice(l,l)));$('multiscale-lane').value='GCTS+RL hierarchy';$('multiscale-region').value='core-8';
  ['multiscale-region','multiscale-lane','multiscale-replicate'].forEach(id=>$(id).addEventListener('change',multiScaleRegionView));multiScaleRegionView();
  d.configuration.lanes.forEach(l=>{const rs=d.evaluation.filter(r=>r.lane===l);tableRow('multiscale-benchmark',[l,`${rs.filter(r=>r.status==='finite_exact_region').length} / ${rs.length}`,fmt(mean(rs.map(r=>r.seconds))),rs.reduce((n,r)=>n+r.backtracks,0),rs.reduce((n,r)=>n+r.state.placements.filter(k=>k[0]==='searched-multiscale-parent').length,0)]);});
  $('multiscale-performance').textContent='RL completes all eight requests, compared with six for the unmarked hierarchy. Singleton search also completes all eight and is fastest: 1.03 s per request, versus 1.53 s with RL and 1.62 s with GCTS+RL. Inherited markings reduce this hierarchy’s backtracking; adding the parent’s new channel makes almost no further difference. Learning has not produced a practical multiscale speedup here.';
  const cold=d.representation_controls,resident=d.evaluation.filter(r=>r.lane==='unmarked hierarchy'),build=d.resident_construction.find(c=>c.first_lane==='unmarked hierarchy').seconds,total=rs=>rs.reduce((s,r)=>s+r.seconds,0),paired=cold.filter(c=>c.status==='finite_exact_region'),pairedResident=resident.filter(r=>paired.some(c=>c.problem===r.problem&&c.seed===r.seed));
  $('multiscale-resident').textContent=`The eight cold unmarked requests take ${fmt(total(cold))} s; the resident version takes ${fmt(total(resident)+build)} s including its one-time ${fmt(build)} s construction. Both finish the same six requests and leave two unknown. All ${a.identical_completed_resident_traces} completed pairs have identical states, nodes, branches, forced moves, backtracks and base attempts: ${fmt(total(paired))} s cold versus ${fmt(total(pairedResident)+build)} s resident including the full build charge. This is a representation optimization on a small batch; budget-limited traces and wall times need not match.`;
  $('multiscale-cost').textContent=`Fresh level-one labels and synthesis ${fmt(first.label_and_synthesis_seconds)} s, then ${fmt(first.independent_audit.seconds)} s pre-activation replay; level two ${fmt(second.label_and_synthesis_seconds)} s plus ${fmt(second.independent_audit.seconds)} s replay. Total two-stage learner cost ${fmt(first.seconds+second.seconds)} s. Zero-start RL training: ${d.training.episodes.filter(r=>r.status==='finite_exact_region').length} of ${d.training.episodes.length} rollouts complete, ${fmt(d.training.seconds)} s. Complete official pipeline ${fmt(d.total_seconds)} s; separate saved-data audit ${fmt(a.seconds)} s. Peak memory ${(d.peak_process_memory_bytes/1048576).toFixed(1)} MiB. Frozen inventory builds: ${d.resident_construction.map(c=>`${c.first_lane} ${fmt(c.seconds)} s`).join('; ')}. Per-request means include unknown attempts and omit these separately reported up-front costs. The cold learning cost exceeds the observed batch saving.`;
  $('multiscale-audit').textContent=`Saved-data audit checks every contact, all ${a.stages.reduce((n,s)=>n+s.negative_nodes,0).toLocaleString()} failure-tree nodes, ${a.stages.reduce((n,s)=>n+s.positive,0)} positive witnesses and ${a.stages.reduce((n,s)=>n+s.scalar_symmetry_checks,0).toLocaleString()} scalar symmetry contacts. It replays all ${a.states_replayed} exported states and ${a.base_placements_replayed} base placements; ${a.complete_states} states complete their declared targets. All ${a.geometry.evaluation_runs.length} completed patches pass exact polygon non-overlap. Omitted branches, altered poses and omitted expansions reject. ${suiteTests()} semantic tests pass, including 14 new multiscale/resident tests.`;
  $('multiscale-stage').addEventListener('change',loadMultiScaleStage);
  ['multiscale-type','multiscale-values'].forEach(id=>$(id).addEventListener('change',multiScaleValuesView));$('multiscale-step').addEventListener('input',multiScaleValuesView);$('multiscale-contact').addEventListener('change',multiScaleContactView);
  await loadMultiScaleStage();
}

function kernelView(){
  const p=kernelData.problems.find(p=>p.id===$('kernel-problem').value),r=p.runs.find(r=>r.lane===$('kernel-lane').value),svg=$('kernel-facts');svg.replaceChildren();
  const commands=r.commands??[],facts=p.declaration.formulas.map(()=>false),frames=[{facts:[...facts],rule:'initial'}],target=p.declaration.formulas.findIndex(a=>JSON.stringify(a)===JSON.stringify(p.target));
  commands.forEach(id=>{const item=p.inferences[id];facts[item.conclusion]=true;frames.push({facts:[...facts],rule:item.rule,changed:item.conclusion});});
  const cw=Math.min(54,510/facts.length),left=120,top=37,rh=29;
  facts.forEach((_,i)=>svgText(svg,left+(i+.5)*cw,20,`slot ${i}`,{'font-size':10,'text-anchor':'middle'}));
  frames.forEach((f,j)=>{svgText(svg,10,top+(j+.6)*rh,`${j} · ${f.rule}`,{'font-size':10});f.facts.forEach((v,i)=>{svg.append(el('rect',{x:left+i*cw+2,y:top+j*rh,width:cw-4,height:rh-5,rx:3,fill:v?(i===target?'#c66c3b':'#6d9c83'):'#e3e8dd',stroke:f.changed===i?'#23332f':'none','stroke-width':1.4}));svgText(svg,left+(i+.5)*cw,top+j*rh+17,v?'1':'0',{'text-anchor':'middle','font-size':12,fill:v?'#fffdf8':'#778478'});});});
  if(!r.verified)svgText(svg,120,100,'No accepting certificate within this run’s bounds.',{'font-size':13,fill:'#834853'});
  $('kernel-fact-caption').textContent=r.verified?`${commands.length} certificate commands. Each row shows the literal fact tape after a command; green slots are proved and orange marks the target. The tape symbols 0 and 1 are machine data. This view summarizes the checked computation, rather than drawing every Wang cell.`:'The search reached a finite limit. No proof or non-provability conclusion is shown; the initial fact tape remains empty in this view.';
  $('kernel-formulas').replaceChildren(...p.formulas_latex.map((a,i)=>{const e=document.createElement('p');e.textContent=`Slot ${i}: \\(${a}\\)`;return e;}));
  $('kernel-statement').textContent=`Target: \\(${p.statement}\\)`;
  $('kernel-run-caption').textContent=`${r.verified?'Checked accepting rectangle':r.status} · ${r.width} columns, ${r.height} transition rows · ${r.nodes.toLocaleString()} attempts, ${r.branches.toLocaleString()} branches, ${r.backtracks.toLocaleString()} backtracks · ${fmt(r.lane_seconds)} s including proposal construction and successful search replay. ${p.machine.states} machine states; ${p.machine.transitions} literal transitions. ${r.preferred_rectangle?'A validated learned sequence supplied preferences.':'No complete proposal was supplied.'}`;
  $('kernel-derivation').replaceChildren(...(r.display_proof??[]).map((l,i)=>{const e=document.createElement('p'),raw=r.kernel_proof[i],refs=l.rule==='mp'?` from ${raw.antecedent+1}, ${raw.implication+1}`:l.rule==='generalize'?` from ${raw.source+1}`:'';e.textContent=`${i+1}. ${l.rule}${refs}: \\(${l.formula}\\)`;return e;}));
  window.MathJax?.typesetPromise?.([$('kernel-formulas'),$('kernel-statement'),$('kernel-derivation')]).catch(()=>{});
}
function kernelResults(){
  kernelData.problems.forEach(p=>{const o=document.createElement('option');o.value=p.id;o.textContent=p.id.replaceAll('_',' ');$('kernel-problem').append(o);});
  kernelData.configuration.lanes.forEach(l=>{const o=document.createElement('option');o.value=l;o.textContent=l;$('kernel-lane').append(o);});$('kernel-lane').value='RL + standard Wang';
  ['kernel-problem','kernel-lane'].forEach(id=>$(id).addEventListener('change',kernelView));kernelView();
  const d=kernelData,a=d.independent_audit;
  $('kernel-finding').textContent=`${a.checked_rectangles} accepting rectangles replay as first-order proofs, covering ${a.point_placements_checked.toLocaleString()} exact base cells. All eight kernel rule kinds are exercised by the independently enumerated catalogs. Cold RL completes five of six assertion controls; standard Wang completes one, and the analytic marking alone completes three within matched bounds. Distribution remains budget-limited in all four lanes. These are small same-assertion controls, not a general theorem-proving speedup.`;
  d.configuration.lanes.forEach(l=>{const rs=d.problems.flatMap(p=>p.runs.filter(r=>r.lane===l));tableRow('kernel-benchmark',[l,`${rs.filter(r=>r.verified).length} / ${rs.length}`,Math.round(mean(rs.map(r=>r.nodes))).toLocaleString(),fmt(mean(rs.map(r=>r.lane_seconds)))]);});
  $('kernel-cost').textContent=`128 cold training episodes: ${d.training.success} checked proposals in ${fmt(d.training.seconds)} s. Complete pipeline ${fmt(d.total_seconds)} s; independent audit ${fmt(a.seconds)} s; peak process memory ${(d.peak_process_memory_bytes/1048576).toFixed(1)} MiB. The audit rejects ${a.tampered_certificates_rejected} altered proofs, rows and input boundaries and replays every training sequence. Table means include budget-limited attempts; they are not equal-success speed ratios. Each run has 100,000 attempts and a cooperative three-second search limit including graph construction; every rectangle has eight unknown certificate slots and 384 transition rows. All ${suiteTests()} tests pass.`;
  const c=d.arithmetic_control;$('kernel-arithmetic-control').textContent=`Separate compiler control: the previously kernel-checked \\(${c.statement}\\) derivation translates to ${c.commands.length} inference commands, ${c.machine_states} states, ${c.transitions.toLocaleString()} literal transitions and ${c.machine_steps.toLocaleString()} machine steps. Its supplied proof and witness-derived catalog are excluded from discovery and training. This verifies a round trip; it is not a new arithmetic discovery.`;
  window.MathJax?.typesetPromise?.([$('kernel-arithmetic-control')]).catch(()=>{});
}

function certifiedStarView(){
  const star=complexData.stars[Number($('complex-star').value)];
  const old=$('complex-ray').value;$('complex-ray').replaceChildren(...star.seams.map(s=>{const o=document.createElement('option');o.value=s.direction;o.textContent=`Direction ${s.direction}`;return o;}));
  if(star.seams.some(s=>String(s.direction)===old))$('complex-ray').value=old;
  drawCertifiedStar();
}
function drawCertifiedStar(){
  const star=complexData.stars[Number($('complex-star').value)],seam=star.seams.find(s=>s.direction===Number($('complex-ray').value)),svg=$('complex-star-drawing');svg.replaceChildren();
  const loops=star.corners.map(i=>complexData.corners[i].vertices.map(ringEmbed).map(([x,y])=>[x,-y])),all=loops.flat(),xs=all.map(p=>p[0]),ys=all.map(p=>p[1]);
  const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),scale=Math.min(575/(maxX-minX),345/(maxY-minY)),map=([x,y])=>[(x-(minX+maxX)/2)*scale+325,(y-(minY+maxY)/2)*scale+210];
  loops.forEach((loop,j)=>{const i=star.corners[j],selected=seam.faces.includes(i),kind=complexData.corners[i].key[0];svg.append(el('polygon',{points:loop.map(p=>map(p).join(',')).join(' '),fill:selected?'#d19163':kind==='thick'?'#6d9c83':'#91b5bd','fill-opacity':selected?.82:.48,stroke:'#476651','stroke-width':1.2}));});
  const [cx,cy]=map([0,0]);svg.append(el('circle',{cx,cy,r:scale/2,fill:'#fffdf8','fill-opacity':.2,stroke:'#347999','stroke-width':1.3,'stroke-dasharray':'4 4'}));
  for(let s=0;s<10;s++){const theta=s*Math.PI/5,[x,y]=map([.5*Math.cos(theta),-.5*Math.sin(theta)]);svg.append(el('line',{x1:cx,y1:cy,x2:x,y2:y,stroke:'#6d868d','stroke-width':.7,'stroke-dasharray':'2 3'}));const [lx,ly]=map([.31*Math.cos(theta+Math.PI/10),-.31*Math.sin(theta+Math.PI/10)]);svgText(svg,lx,ly+3,String(s),{'font-size':10,'text-anchor':'middle',fill:'#304e56'});}
  const [ex,ey]=ringEmbed(seam.endpoint),[x,y]=map([ex,-ey]);svg.append(el('line',{x1:cx,y1:cy,x2:x,y2:y,stroke:'#a3444c','stroke-width':4}));svg.append(el('circle',{cx,cy,r:3,fill:'#23332f'}));svg.append(el('circle',{cx:x,cy:y,r:4,fill:'#a3444c'}));
  $('complex-star-caption').textContent=`Star ${Number($('complex-star').value)+1} of ${complexData.stars.length} · ${star.faces} rhombs fill all ten root sectors. Numbers identify the fixed sector slots. The two orange faces share the highlighted unit edge. The dashed circle lies inside the flat root chart. Other vertices remain incomplete in this finite local example.`;
}
function fullStarPilotView(){
  const s=starPilotData.samples[Number($('star-pilot-orbit').value)];drawRhombs($('star-pilot-drawing'),s.placements,{required:s.required,fixed:s.initial.length});
  $('star-pilot-caption').textContent=`Orbit ${Number($('star-pilot-orbit').value)+1} of ${starPilotData.samples.length} · ${s.initial.length} fixed rhombs; ${s.placements.length} total · ${s.status} · ${s.counts.nodes} search nodes, ${s.counts.branches||0} branches and ${s.counts.backtracks||0} backtracks. All ${s.required.length} initial slots are full; ${s.frontier_witnesses?.length||0} exposed slots have checked candidates. Dark outlines identify the fixed star; gold dots mark its target vertices.`;
}
function penroseComplexResults(){
  const d=complexData,a=d.independent_audit,st=starPilotData,sa=st.serialization_audit;
  d.stars.forEach((s,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${i+1} · ${s.faces} rhombs`;$('complex-star').append(o);});$('complex-star').value=80;
  $('complex-star').addEventListener('change',certifiedStarView);$('complex-ray').addEventListener('change',drawCertifiedStar);certifiedStarView();
  $('complex-audit').textContent=`${a.raw_corner_aliases_checked} corner identities, ${a.full_stars_checked} full stars, ${a.radial_unit_seams_checked.toLocaleString()} unit seams and ${d.template_bounds.barycentric_triangles_checked} barycentric triangles pass exact checks. All ${a.rotation_contacts_checked.toLocaleString()} rotations replay. ${a.complete_vertices_replayed.toLocaleString()} complete vertices in 320 historical patches match the catalog; ${a.incomplete_exposed_vertices.toLocaleString()} exposed vertices remain incomplete. Finite audit ${fmt(d.audit_seconds)} s.`;
  const allPositive=(st.counts.positive||0)===st.catalog.rotation_orbits;
  $('star-pilot-finding').textContent=`Fresh higher-context pilot: ${st.catalog.rotation_orbits} rotation orbits cover all ${st.catalog.full_stars} complete root stars. ${st.counts.positive||0} positive, ${st.counts.negative||0} negative, ${st.counts.unresolved||0} unresolved. ${allPositive?'All represented stars have verified finite one-coronas. This found no failing context to encode as a new marking.':'Resolved labels refer only to the declared finite completion target.'} No marking or policy was activated.`;
  st.samples.forEach((s,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${i+1} · ${s.initial.length} fixed rhombs · ${s.status}`;$('star-pilot-orbit').append(o);});$('star-pilot-orbit').addEventListener('change',fullStarPilotView);fullStarPilotView();
  $('star-pilot-audit').textContent=`Search plus fresh catalog ${fmt(st.search_and_catalog_seconds)} s; first independent audit ${fmt(st.independent_audit.seconds)} s; complete pipeline ${fmt(st.total_seconds)} s; peak memory ${(st.peak_process_memory_bytes/1048576).toFixed(1)} MiB. Separate saved-data replay ${fmt(sa.seconds)} s checks ${sa.representative_completions_checked} representatives, ${sa.transformed_completions_checked} transformed completions and ${sa.transformed_frontier_witnesses_checked.toLocaleString()} frontier witnesses. Altered targets and omitted frontier witnesses reject. All displayed representative polygons are nonoverlapping. ${suiteTests()} semantic tests pass.`;
}

function drawClusterValues(svg,t,values,width=500,height=400){
  svg.replaceChildren();const loops=t.expansion.map(k=>verts(data.point_model.vertices,k).map(project)),points=t.occupancy.map(([p])=>project(p)),all=loops.flat().concat(points);
  const xs=all.map(p=>p[0]),ys=all.map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  const scale=Math.min((width-65)/(maxX-minX),(height-65)/(maxY-minY)),map=p=>[(p[0]-(minX+maxX)/2)*scale+width/2,(p[1]-(minY+maxY)/2)*scale+height/2],assigned=new Map(values.map(([p,v])=>[JSON.stringify(p),v]));
  loops.forEach((loop,i)=>svg.append(el('polygon',{points:loop.map(p=>map(p).join(',')).join(' '),fill:i%2?'#d19163':'#6d9c83','fill-opacity':.13,stroke:'#849a89','stroke-width':1.1})));
  t.occupancy.forEach(([p,v])=>{const [x,y]=map(project(p)),key=JSON.stringify(p),has=assigned.has(key),color=assigned.get(key);
    const circle=el('circle',{cx:x,cy:y,r:has?6.2:3.2,fill:has?`hsl(${color*137.508%360} 45% 49%)`:'#fffdf8',stroke:has?'#45604c':'#a4b39e','stroke-width':.7});
    circle.append(el('title',{},`Prototype point ${p.join(',')}; occupancy ${v}/12; ${has?`assigned scalar color ${color}`:'free entry (*)'}`));svg.append(circle);
    if(has)svgText(svg,x,y+2.6,String(color),{'font-size':7.5,fill:'#fff','text-anchor':'middle'});
  });
}
function clusterLearningView(){
  const d=clusterMarkData,final=$('cluster-learning-state').value==='final',n=Number($('cluster-learning-step').value),h=d.marking.history[n-1],s=d.labels.samples[Number($('cluster-learning-contact').value)];
  const values=final?d.marking_for_inspection_only:h.values;drawClusterValues($('cluster-learning-marking'),d.configuration.prototype,values);
  $('cluster-learning-step-value').textContent=n;
  $('cluster-learning-mark-caption').textContent=final?`Final own-level channel: ${d.marking.assigned} assigned values, ${d.marking.free} individual free entries and ${d.marking.colors} scalar colors on ${d.marking.support_points} prototype points. Hollow circles are free. Color zero is assigned. Counts refer to one prototype.`:`After ${n} labels: ${h.counts.positive||0} positive, ${h.counts.negative||0} negative, ${h.counts.unresolved||0} unresolved. All ${h.values.length} provisional values represent ${h.components} equality classes; ${h.provisional_negative_rejected} resolved negatives currently have a differing overlap. Provisional values do not filter the label oracle.`;
  let placements=s.witness||s.seed_expansion,dead=null;
  if(s.status==='negative'){placements=[...s.seed_expansion];let node=s.certificate;while(node.children?.length){const c=node.children[0];placements.push(c.placement);node=c.proof;}dead=node.dead;}
  drawPatch($('cluster-learning-corona'),placements,{dead,width:560,height:400});
  const marking=new Map(d.marking_for_inspection_only.map(([p,v])=>[JSON.stringify(p),v])),[name,o,tr]=s.second,g=syms[o];
  const conflict=d.marking_for_inspection_only.some(([p,v])=>{const q=g.p.map((j,i)=>g.s*p[j]+tr[i]),key=JSON.stringify(q);return marking.has(key)&&marking.get(key)!==v;});
  $('cluster-learning-corona-caption').textContent=`Contact ${Number($('cluster-learning-contact').value)+1} of ${d.labels.samples.length} · ${s.status==='negative'?'complete exhausted base search':'finite completion with viable exposed frontier'} · ${s.nodes} search nodes; ${s.branches} branches; ${s.forced} forced moves. ${dead?'The red ring is the first checked dead leaf.':'All original pair points are full; exposed obligations remain incomplete and viable.'} The final cluster marking ${conflict?'rejects':'accepts'} this contact.`;
}
function clusterLearningResults(){
  const d=clusterMarkData,m=d.marking,a=d.independent_audit;
  d.labels.samples.forEach((s,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${i+1} · ${s.status} · orientation ${s.second[1]}`;$('cluster-learning-contact').append(o);});
  $('cluster-learning-contact').value=10;
  $('cluster-learning-contact').addEventListener('change',()=>{if($('cluster-learning-state').value==='online')$('cluster-learning-step').value=Number($('cluster-learning-contact').value)+1;clusterLearningView();});
  $('cluster-learning-state').addEventListener('change',()=>{$('cluster-learning-step').value=$('cluster-learning-state').value==='final'?d.labels.samples.length:Number($('cluster-learning-contact').value)+1;clusterLearningView();});
  $('cluster-learning-step').addEventListener('input',()=>{$('cluster-learning-state').value='online';$('cluster-learning-contact').value=Number($('cluster-learning-step').value)-1;clusterLearningView();});
  $('cluster-learning-finding').textContent=`All ${d.labels.samples.length} contacts resolve: ${m.counts.positive} positive and ${m.counts.negative} negative. ${m.assigned} assigned point values reject ${m.negative_rejected} failures and accept every positive. All ${a.canonical_exclusions_checked} possible marking disagreements have independently checked base failure certificates. The marking is redundant for disjoint cluster decorations of complete unmarked point tilings; existence and plane coverage remain open.`;
  ['unmarked','GCTS','RL','GCTS+RL'].forEach(lane=>{const rows=d.evaluation.filter(r=>r.lane===lane);tableRow('cluster-learning-benchmark',[lane,`${rows.filter(r=>r.status==='finite_exact_region').length} / ${rows.length}`,fmt(mean(rows.map(r=>r.attempted_base_placements))),fmt(mean(rows.map(r=>r.backtracks))),fmt(mean(rows.map(r=>r.seconds)))]);});
  const base=d.evaluation.find(r=>r.problem==='free-notch-pocket'&&r.lane==='unmarked'),marked=d.evaluation.find(r=>r.problem==='free-notch-pocket'&&r.lane==='GCTS');
  $('cluster-learning-performance').textContent=`All 24 lane/target runs complete. On the notched-core/pocket target, GCTS reduces backtracks from ${base.backtracks} to ${marked.backtracks} and total time from ${fmt(base.seconds)} to ${fmt(marked.seconds)} seconds. It does not improve every target. RL is slower on both witness-free targets; many marking eliminations do not make that policy faster. One seed per target is insufficient for a stable speedup claim.`;
  $('cluster-learning-cost').textContent=`Fresh contact labels and equality synthesis ${fmt(d.labels.seconds)} s; zero-start RL training ${fmt(d.training.seconds)} s; complete pipeline ${fmt(d.total_seconds)} s; separate independent audit ${fmt(a.seconds)} s; peak process memory ${(d.peak_process_memory_bytes/1048576).toFixed(1)} MiB. All ${a.negative_proof_nodes_checked.toLocaleString()} negative-tree nodes, ${a.scalar_symmetry_contact_checks.toLocaleString()} symmetry contacts and ${a.finite_states_replayed} finite states replay. ${a.tampered_certificates_rejected} altered proofs reject. All ${a.geometry.evaluation_runs.length} displayed region patches pass exact polygon non-overlap; ${suiteTests()} semantic tests pass.`;
  const p=d.parent;drawClusterValues($('cluster-learning-parent'),p,p.marks.filter(([[point,ch]])=>ch==='cluster:1').map(([[point,ch],v])=>[point,v]),780,400);
  clusterLearningView();
}

function regionCases(){
  const movable=$('region-mode').value==='movable',select=$('region-problem');select.replaceChildren();
  const cases=movable?regionData.movable_families.map((f,i)=>({value:i,label:`Family ${i+1} · donor ${i?85002:85001}`})):regionData.problems.map(p=>({value:p.boundary.identity,label:p.boundary.identity}));
  cases.forEach(c=>{const o=document.createElement('option');o.value=c.value;o.textContent=c.label;select.append(o);});
  if(!movable)select.value='free-notch-pocket';regionUpdate();
}
function regionUpdate(){
  const movable=$('region-mode').value==='movable',lane=$('region-lane').value,select=$('region-attempt');
  $('region-attempt-label').hidden=!movable;select.replaceChildren();
  if(movable){
    const r=regionData.movable_evaluation.find(r=>String(r.family)===$('region-problem').value&&r.lane===lane);
    r.attempts.forEach((a,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${i+1} · ${a.result.status==='finite_exact_region'?'completed':'checked failure'}`;select.append(o);});select.value=r.attempts.length-1;
  }
  regionView();
}
function movedBase(key,o,tr){
  const g=syms[o],h=syms[key[0]],perm=g.p.map(i=>h.p[i]);
  return [syms.findIndex(s=>s.s===g.s*h.s&&s.p.every((v,i)=>v===perm[i])),g.p.map((j,i)=>g.s*key[1][j]+tr[i])];
}
function regionView(){
  const movable=$('region-mode').value==='movable',lane=$('region-lane').value,id=$('region-problem').value;
  let r,boundary,runs;
  if(movable){
    const family=regionData.movable_evaluation.find(r=>String(r.family)===id&&r.lane===lane),a=family.attempts[Number($('region-attempt').value)];r=a.result;
    boundary=regionData.movable_families[Number(id)].find(b=>b.identity===a.boundary);runs=regionData.movable_evaluation.filter(r=>String(r.family)===id);
  }else{r=regionData.evaluation.find(r=>r.problem===id&&r.lane===lane);boundary=regionData.problems.find(p=>p.boundary.identity===id).boundary;runs=regionData.evaluation.filter(r=>r.problem===id);}
  const fixed=new Set(boundary.owned.map(k=>JSON.stringify(k))),owners=new Map();
  r.state.placements.forEach(([name,o,tr],i)=>clusterData.types.find(t=>t.identity===name).expansion.forEach(k=>owners.set(JSON.stringify(movedBase(k,o,tr)),i)));
  const fills=r.state.base_expansion.map(k=>fixed.has(JSON.stringify(k))?'#d8dfd5':`hsl(${(owners.get(JSON.stringify(k))??0)*137.508%360} 32% 56%)`);
  drawPatch($('region-drawing'),r.state.base_expansion,{points:boundary.required,width:720,height:430,fills});
  $('region-caption').textContent=`${boundary.identity} · ${boundary.required.length} required points; ${boundary.allowed.length} envelope points; ${boundary.owned.length} fixed exterior tiles. ${r.accepted_base_tiles} new base constituents in ${r.accepted_cluster_tiles} atomic tiles. ${r.status==='finite_exact_region'?'Every required point is independently checked at full capacity.':'This boundary branch exhausts its complete finite inventory; the dead-domain certificate is independently checked.'} Drawing geometry never decides legality.`;
  const svg=$('region-timing');svg.replaceChildren();const max=Math.max(...runs.map(r=>r.seconds)),labels=['Singleton','Aggregate','Aggregate + RL'];
  runs.forEach((row,i)=>{const y=44+i*61,w=210*row.seconds/max,compiled=movable?row.attempts.reduce((s,a)=>s+a.result.compilation_seconds,0):row.compilation_seconds;
    svgText(svg,8,y-3,labels[i],{'font-size':11});svg.append(el('rect',{x:111,y:y-20,width:w,height:24,fill:'#6d9c83',rx:2}));svg.append(el('rect',{x:111,y:y-20,width:210*compiled/max,height:24,fill:'#d8dfd5',rx:2}));
    svgText(svg,111,y+20,`${fmt(row.seconds)} s total · ${fmt(compiled)} s inventory`,{'font-size':10});
  });
  $('region-state').textContent=`Selected branch: ${r.branches} branch decisions, ${r.forced} forced decisions, ${r.backtracks} backtracks, ${r.attempted_base_placements} actual base-placement attempts. The largest graph has ${r.peak_candidate_nodes.toLocaleString()} candidate nodes and ${r.peak_incidences.toLocaleString()} incidences. ${r.admissible_placements.toLocaleString()} admissible placements are retained in the complete frozen-boundary inventory.`;
  $('region-cost').textContent=`Gray is inventory compilation; green is the remaining search and replay cost. Cold policy training ${fmt(regionData.training.seconds)} s; full pilot ${fmt(regionData.total_seconds)} s; peak process memory ${(regionData.peak_process_memory_bytes/1048576).toFixed(1)} MiB. Budgets: 10,000 nodes and ten seconds per boundary member, including compilation. All timings are one run per problem and lane.`;
}
function regionResults(){
  $('region-finding').textContent='All six fixed targets and both movable families complete in all three lanes. The singleton reference is fastest on every case. RL removes backtracking on the two witness-free targets, but aggregate compilation and bookkeeping outweigh that gain. Useful cluster markings and a practical multiscale speedup remain open.';
  const a=regionData.independent_audit,training=regionData.training.episodes.filter(r=>r.status==='finite_exact_region').length;
  $('region-audit').textContent=`${a.states_replayed} exported states replay; ${a.completed_states} complete their declared targets. ${a.new_base_placements_replayed} new base placements checked; ${a.negative_tree_nodes_checked} complete failure-tree nodes replay; ${a.tampered_certificates_rejected} altered certificates reject. Six new local solution types pass ${a.transformed_expansions_checked} transformed expansion checks. The polygon audit finds no positive-area overlap in ${a.geometry.evaluation_runs.length} displayed finite patches. Separate audit ${fmt(a.seconds)} s; ${suiteTests()} semantic tests pass. Training completes ${training} of 24 rollouts.`;
  $('region-mode').addEventListener('change',regionCases);['region-problem','region-lane'].forEach(id=>$(id).addEventListener('change',regionUpdate));$('region-attempt').addEventListener('change',regionView);regionCases();
}

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
  $("cluster-tile-evidence").textContent=`${clusterData.prototype_count} types include the base singleton, 14 searched clusters and one observed parent. All ${clusterData.transformed_expansions_checked} transformed expansions replay to exact base values. Five semantic tests cover inherited level channels, zero-valued distant dependencies, complete aggregate incidence, exact snapshots, base fallback and rejected malformed hierarchies. The complete research suite now passes ${suiteTests()} tests; the boundary pilot below constructs six further parent types from searched local completions.`;
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
  $("proof-search-cost").textContent=`Cold training ${fmt(d.training.seconds)} s; generated programs ${fmt(d.problems.reduce((sum,p)=>sum+p.compile_seconds,0))} s; complete experiment ${fmt(d.total_seconds)} s; peak process memory ${(d.peak_process_memory_bytes/1048576).toFixed(1)} MiB. Separate replay ${fmt(a.seconds)} s checked ${a.checked_rectangles.length} rectangles and ${a.point_placements_checked.toLocaleString()} base placements, and rejected ${a.tampered_certificates_rejected} altered certificates/statements. Search timings include domain construction; lane totals also include proposal compilation and successful search replay. The bounded fair-driver control returns unknown after ${d.fair_bound_control.attempts} attempts. All ${suiteTests()} semantic tests pass.`;
}

function drawPatch(svg,placements,{points=[],dead=null,width=800,height=470,groups=null,fills=null}={}){
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
    const fill=fills?fills[i]:groups?`hsl(${groups[i]*137.508%360} 27% 58%)`:inversions%2?"#d19163":"#6d9c83";
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
  $("serialized-proof-caption").textContent="Both exported proof formats now replay from JSON. The logic replay uses an externally declared theory; the proof cannot nominate new axioms. Changed targets, a forged axiom, and a changed Wang input are rejected. This historical snapshot closes serialization replay. The new finite-catalog bridge also supplies an executable first-order checker; a single fixed serialized-syntax checker remains open.";
  $("core-lane").addEventListener("change",coreSeeds);$("core-seed").addEventListener("change",coreRadii);$("core-radius").addEventListener("change",coreView);
  $("grammar-library").addEventListener("change",grammarSeeds);["grammar-seed","grammar-level"].forEach(id=>$(id).addEventListener("change",grammarView));
}

const ringEmbed=p=>p.reduce((sum,c,i)=>[sum[0]+c*Math.cos(2*i*Math.PI/5),sum[1]+c*Math.sin(2*i*Math.PI/5)],[0,0]);
function drawRhombs(svg,placements,{width=740,height=430,required=[],obstruction=false,fixed=2}={}){
  svg.replaceChildren();
  const loops=placements.map(([kind,r,tr])=>penroseData.point_model.vertices[kind].map(v=>{const [x,y]=ringEmbed(v),[a,b]=ringEmbed(tr),theta=r*Math.PI/5;return [x*Math.cos(theta)-y*Math.sin(theta)+a,-(x*Math.sin(theta)+y*Math.cos(theta)+b)];}));
  const points=required.map(([v])=>ringEmbed(v)).map(([x,y])=>[x,-y]),all=loops.flat().concat(points);
  if(!all.length)return;
  const xs=all.map(p=>p[0]),ys=all.map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),scale=Math.min((width-60)/Math.max(.1,maxX-minX),(height-50)/Math.max(.1,maxY-minY));
  const map=([x,y])=>[(x-(minX+maxX)/2)*scale+width/2,(y-(minY+maxY)/2)*scale+height/2];
  loops.forEach((loop,i)=>{const [kind,r,tr]=placements[i],poly=el("polygon",{points:loop.map(p=>map(p).join(",")).join(" "),fill:obstruction?(i?"#c76b3d":"#347999"):kind==="thick"?"#6d9c83":"#d19163","fill-opacity":.64,stroke:obstruction?"#9e424a":i<fixed?"#23332f":"#476651","stroke-width":i<fixed?2:1.2});poly.append(el("title",{},`${kind}; rotation ${r}; translation ${tr.join(",")}`));svg.append(poly);});
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
  $("ring-caption").textContent=`${data.penrose.exact_pair_checks.toLocaleString()} exact multiplication/conjugation checks passed. The sector model now has a conditional analytic plane-faithfulness proof. A compatible infinite continuation and Penrose hierarchy remain open.`;
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
    const response=await fetch("iteration-001.json?v=20261009-r10.1",{cache:"no-cache"});
    if(!response.ok)throw new Error(`Snapshot returned ${response.status}`);
    data=await response.json();
    const coarseResponse=await fetch("coarse-gate-001.json?v=20261009-r10.1",{cache:"no-cache"});
    if(!coarseResponse.ok)throw new Error(`Coarse proof returned ${coarseResponse.status}`);
    coarseData=await coarseResponse.json();
    if(!coarseData.independent_audit||!coarseData.semantic_tests)throw new Error("Coarse proof replay or tests are pending.");
    coarseResults();
    const multiResponse=await fetch("multiscale-regions-001.json?v=20261009-r10.1",{cache:"no-cache"});
    if(!multiResponse.ok)throw new Error(`Multiscale snapshot returned ${multiResponse.status}`);
    multiScaleData=await multiResponse.json();
    if(!multiScaleData.independent_audit||!multiScaleData.semantic_tests)throw new Error("Multiscale replay or tests are pending.");
    if(!data.evaluation||!data.wang)throw new Error("Iteration is still running; the final checkpoint is not ready.");
    $("pair-count").textContent=data.pair_catalog.count;
    $("negative-count").textContent=data.pair_catalog.counts.negative;
    $("mark-reject-count").textContent=data.marking.negative_rejected;
    $("assigned-count").textContent=data.marking.assigned;
    $("load-status").textContent=`Iteration 01 · ${data.pair_verification.negative_proof_nodes} independent failure-tree nodes checked · all ${data.pair_catalog.count} contact labels resolved.`;
    data.pair_catalog.samples.forEach((s,i)=>{const o=document.createElement("option");o.value=i;o.textContent=`${i+1} · ${s.status} · orientation ${s.second[0]}`;$("pair").append(o);});
    selectRun();marking();pairView();benchmark();motifs();penrose();computation();
    await multiScaleResults();
    const secondResponse=await fetch("iteration-002.json?v=20261009-r10.1",{cache:"no-cache"});
    if(!secondResponse.ok)throw new Error(`Second snapshot returned ${secondResponse.status}`);
    secondData=await secondResponse.json();
    if(!secondData.total_seconds)throw new Error("Second cold run is still computing; final evidence is not ready.");
    spatialResults();proofResults();
    const haloResponse=await fetch("halo-probe-002.json?v=20261009-r10.1",{cache:"no-cache"});
    if(!haloResponse.ok)throw new Error(`Halo snapshot returned ${haloResponse.status}`);
    haloData=await haloResponse.json();haloResults();
    const thirdResponse=await fetch("iteration-003.json?v=20261009-r10.1",{cache:"no-cache"});
    if(!thirdResponse.ok)throw new Error(`Third snapshot returned ${thirdResponse.status}`);
    thirdData=await thirdResponse.json();
    if(!thirdData.independent_audit||!thirdData.evaluation_repeat)throw new Error("The third study's repeat or final audit is still pending.");
    continuationResults();
    const penroseResponse=await fetch("penrose-001.json?v=20261009-r10.1",{cache:"no-cache"});
    if(!penroseResponse.ok)throw new Error(`Penrose snapshot returned ${penroseResponse.status}`);
    penroseData=await penroseResponse.json();penroseResults();
    const proofResponse=await fetch("proof-search-001.json?v=20261009-r10.1",{cache:"no-cache"});
    if(!proofResponse.ok)throw new Error(`Proof snapshot returned ${proofResponse.status}`);
    proofData=await proofResponse.json();
    if(!proofData.independent_audit||!proofData.semantic_tests)throw new Error("Generic proof audit is pending.");
    const regionResponse=await fetch('regions-001.json?v=20261009-r10.1',{cache:'no-cache'});
    if(!regionResponse.ok)throw new Error(`Region snapshot returned ${regionResponse.status}`);
    regionData=await regionResponse.json();if(!regionData.independent_audit||!regionData.semantic_tests)throw new Error('Boundary replay or semantic tests are pending.');
    const clusterMarkResponse=await fetch('cluster-marking-001.json?v=20261009-r10.1',{cache:'no-cache'});
    if(!clusterMarkResponse.ok)throw new Error(`Cluster marking snapshot returned ${clusterMarkResponse.status}`);
    clusterMarkData=await clusterMarkResponse.json();if(!clusterMarkData.independent_audit||!clusterMarkData.semantic_tests)throw new Error('Cluster marking replay or tests are pending.');
    const complexResponse=await fetch('penrose-complex-001.json?v=20261009-r10.1',{cache:'no-cache'});
    if(!complexResponse.ok)throw new Error(`Complex audit returned ${complexResponse.status}`);
    complexData=await complexResponse.json();if(!complexData.independent_audit||!complexData.semantic_tests)throw new Error('Complex hypotheses or semantic tests are pending.');
    const starPilotResponse=await fetch('penrose-stars-001.json?v=20261009-r10.1',{cache:'no-cache'});
    if(!starPilotResponse.ok)throw new Error(`Full-star pilot returned ${starPilotResponse.status}`);
    starPilotData=await starPilotResponse.json();if(!starPilotData.serialization_audit)throw new Error('Saved full-star evidence replay is pending.');
    const kernelResponse=await fetch('kernel-machine-001.json?v=20261009-r10.1',{cache:'no-cache'});
    if(!kernelResponse.ok)throw new Error(`Kernel bridge returned ${kernelResponse.status}`);
    kernelData=await kernelResponse.json();if(!kernelData.independent_audit||!kernelData.semantic_tests)throw new Error('Kernel bridge audit or tests are pending.');
    genericProofResults();penroseComplexResults();kernelResults();
    const clusterResponse=await fetch("cluster-types-001.json?v=20261009-r10.1",{cache:"no-cache"});
    if(!clusterResponse.ok)throw new Error(`Cluster type snapshot returned ${clusterResponse.status}`);
    clusterData=await clusterResponse.json();clusterTileResults();regionResults();clusterLearningResults();
    $("load-status").textContent=`Joint coarse-library obstruction, two marking levels, authored boundary trials, first-order kernel bridge and conditional rhomb plane-faithfulness recorded · ${suiteTests()} semantic tests pass · finite certificates independently replayed.`;
    if(data.geometry_audit){const a=data.geometry_audit;$("geometry-caption").textContent=a.all_reported_patches_nonoverlapping?`An independent audit using exact triangulation and rational clipping found no positive-area polygon overlap in any of the ${a.evaluation_runs.length} displayed evaluation patches. This certifies finite non-overlap, not coverage of the plane or faithfulness of the entire point model.`:`The independent polygon audit found overlaps in some point-model patches; inspect the JSON before treating a point patch as a geometric tiling.`;}
    $("lane").addEventListener("change",selectRun);
    $("seed").addEventListener("change",()=>{currentRun=data.evaluation.find(r=>r.lane===$("lane").value&&String(r.seed)===$("seed").value);$("step").max=currentRun.placements.length;$("step").value=currentRun.placements.length;updatePatch();});
    $("step").addEventListener("input",updatePatch);
    $("pair").addEventListener("change",pairView);
    $("play").addEventListener("click",()=>{if(timer){clearInterval(timer);timer=null;$("play").textContent="Play growth";return;}$("step").value=1;updatePatch();$("play").textContent="Pause";timer=setInterval(()=>{const n=Number($("step").value)+1;if(n>currentRun.placements.length){clearInterval(timer);timer=null;$("play").textContent="Play growth";return;}$("step").value=n;updatePatch();},300);});
    $("provenance").textContent=`Started ${new Date(data.date).toLocaleString("en-US",{timeZone:"America/Los_Angeles",dateStyle:"long",timeStyle:"short"})}; third turtle study ${new Date(thirdData.date).toLocaleString("en-US",{timeZone:"America/Los_Angeles",dateStyle:"long",timeStyle:"short"})}; generic proof pilot ${new Date(proofData.date).toLocaleString("en-US",{timeZone:"America/Los_Angeles",dateStyle:"long",timeStyle:"short"})}, Pacific time. Source SHA-256 hashes, budgets, placements, proofs, training traces, explicit reuse and timing corrections are in the JSON. The rhomb faithfulness result is an analytic conditional theorem. No substitution, learned infinite continuation or Penrose hierarchy has been certified.`;
  }catch(error){$("load-status").textContent=`Experiment data could not be loaded: ${error.message}`;$("load-status").style.color="#a5343f";}
}
main();
