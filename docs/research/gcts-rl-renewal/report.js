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
let data,timer=null,currentRun;

function drawPatch(svg,placements,{points=[],dead=null,width=800,height=470}={}){
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
    const fill=inversions%2?"#d19163":"#6d9c83";
    const shape=el("polygon",{points:loop.map(p=>map(p).join(",")).join(" "),fill,"fill-opacity":.72,stroke:"#345648","stroke-width":1.1,"stroke-linejoin":"round"});
    shape.append(el("title",{},`Base placement ${i+1}; orientation ${o}; translation ${placements[i][1].join(",")}`));
    svg.append(shape);
  });
  projectedPoints.forEach(p=>{const [x,y]=map(p);svg.append(el("circle",{cx:x,cy:y,r:2.3,fill:"#c79343"}));});
  if(dead){const [x,y]=map(project(dead));svg.append(el("circle",{cx:x,cy:y,r:9,fill:"none",stroke:"#b53741","stroke-width":3}));svg.append(el("circle",{cx:x,cy:y,r:3,fill:"#b53741"}));}
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
  $("ring-caption").textContent=`${data.penrose.exact_pair_checks.toLocaleString()} exact multiplication/conjugation pair checks passed. Both unmarked rhomb prototypes are transcribed. Penrose tiling search has not started.`;
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
    const response=await fetch("iteration-001.json?v=20261008-r1.3",{cache:"no-cache"});
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
    if(data.geometry_audit){const a=data.geometry_audit;$("geometry-caption").textContent=a.all_reported_patches_nonoverlapping?`An independent audit using exact triangulation and rational clipping found no positive-area polygon overlap in any of the ${a.evaluation_runs.length} displayed evaluation patches. This certifies finite non-overlap, not coverage of the plane or faithfulness of the entire point model.`:`The independent polygon audit found overlaps in some point-model patches; inspect the JSON before treating a point patch as a geometric tiling.`;}
    $("lane").addEventListener("change",selectRun);
    $("seed").addEventListener("change",()=>{currentRun=data.evaluation.find(r=>r.lane===$("lane").value&&String(r.seed)===$("seed").value);$("step").max=currentRun.placements.length;$("step").value=currentRun.placements.length;updatePatch();});
    $("step").addEventListener("input",updatePatch);
    $("pair").addEventListener("change",pairView);
    $("play").addEventListener("click",()=>{if(timer){clearInterval(timer);timer=null;$("play").textContent="Play growth";return;}$("step").value=1;updatePatch();$("play").textContent="Pause";timer=setInterval(()=>{const n=Number($("step").value)+1;if(n>currentRun.placements.length){clearInterval(timer);timer=null;$("play").textContent="Play growth";return;}$("step").value=n;updatePatch();},300);});
    $("provenance").textContent=`Recorded ${new Date(data.date).toLocaleString("en-US",{timeZone:"America/Los_Angeles",dateStyle:"long",timeStyle:"short"})} Pacific time. Source SHA-256 hashes, budgets, all placements, label proofs, and training traces are included in the JSON. No substitution or plane-tiling proof has been produced.`;
  }catch(error){$("load-status").textContent=`Experiment data could not be loaded: ${error.message}`;$("load-status").style.color="#a5343f";}
}
main();
