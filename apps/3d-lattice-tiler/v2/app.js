import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {catalog,MODES,VERSION} from './model.js?v=2.1.0';
const $=id=>document.getElementById(id),cases=catalog();
let results={},series={},archive=[],models={},active='free',worker=null,busy=false,cancelled=false,custom=null,previewSequence=0,runConfig=null;
const labels={finite_exact:'Verified window',unknown:'Unknown',exhausted_finite:'Exhausted finite',error:'Unavailable'};
const fmt=n=>Number(n??0).toLocaleString(undefined,{maximumFractionDigits:0}),time=n=>n===undefined?'—':n<1000?`${Math.round(n)} ms`:`${(n/1000).toFixed(2)} s`;
for(const group of [...new Set(cases.map(c=>c.group))]){const opt=document.createElement('optgroup');opt.label=group;for(const c of cases.filter(c=>c.group===group)){const o=document.createElement('option');o.value=c.id;o.textContent=c.name;opt.append(o);}$('tile').append(opt);}
for(const m of MODES){const b=document.createElement('button');b.className='lane';b.style.setProperty('--lane',m.color);b.id=`lane-${m.id}`;b.addEventListener('click',()=>{active=m.id;refresh();renderPatch();});$('lanes').append(b);}

const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(35,1,.01,2000),renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));$('canvas').append(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;camera.position.set(12,10,14);
scene.add(new THREE.HemisphereLight('#d7e9ff','#354869',2.5));const light=new THREE.DirectionalLight('#ffffff',3);light.position.set(5,10,8);scene.add(light);
const geometryGroup=new THREE.Group(),pointGroup=new THREE.Group(),edgeGroup=new THREE.Group();scene.add(geometryGroup,pointGroup,edgeGroup);
let showPoints=true,showEdges=true;
function clear(group){while(group.children.length){const child=group.children[0];group.remove(child);child.geometry?.dispose();if(Array.isArray(child.material))child.material.forEach(m=>m.dispose());else child.material?.dispose();}}
function draw(model,placements,fit=false){
  if(!model)return;[geometryGroup,pointGroup,edgeGroup].forEach(clear);
  const palette=['#4fdac5','#91afff','#c1acff','#ffd18b','#80cfea','#eaadcc'];
  for(const [i,p] of placements.entries()){
    const o=model.orientations[p.oi],positions=[];
    for(const face of o.faces??[]){
      if(face.length<3)continue;
      const vertices=face.map(i=>new THREE.Vector3(...o.vertices[i])),origin=vertices[0],u=vertices[1].clone().sub(origin).normalize();
      let normal=new THREE.Vector3();for(let j=2;j<vertices.length&&normal.lengthSq()<1e-12;j++)normal.crossVectors(u,vertices[j].clone().sub(origin));
      if(normal.lengthSq()<1e-12)continue;normal.normalize();const v=new THREE.Vector3().crossVectors(normal,u);
      const contour=vertices.map(pt=>{const d=pt.clone().sub(origin);return new THREE.Vector2(d.dot(u),d.dot(v));});
      for(const triangle of THREE.ShapeUtils.triangulateShape(contour,[]))for(const j of triangle)positions.push(...o.vertices[face[j]].map((x,a)=>x+p.translation[a]));
    }
    if(positions.length){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.computeVertexNormals();geometryGroup.add(new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:palette[i%palette.length],metalness:.15,roughness:.55,side:THREE.DoubleSide,transparent:true,opacity:.72,depthWrite:false})));edgeGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(g,15),new THREE.LineBasicMaterial({color:'#0d1d2d',transparent:true,opacity:.6})));}
  }
  const totals=new Map();for(const p of placements)for(const q of model.orientations[p.oi].cells){const k=q.pos.map((x,i)=>x+p.translation[i]).join(',');totals.set(k,(totals.get(k)??0)+q.weight);}
  const positions=[],colors=[];for(const p of model.required){positions.push(...p.pos);const c=new THREE.Color(totals.get(p.pos.join(','))===model.capacity?'#4fdac5':'#ffd18b');colors.push(c.r,c.g,c.b);}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));pointGroup.add(new THREE.Points(g,new THREE.PointsMaterial({size:.095,vertexColors:true,depthTest:false,transparent:true,opacity:.95})));
  pointGroup.visible=showPoints;edgeGroup.visible=showEdges;
  $('viewMeta').textContent=`${placements.length} placements · ${model.orientations.length} orientations · capacity ${model.capacity}`;
  if(fit)fitView();
}
function fitView(){const box=new THREE.Box3().setFromObject(geometryGroup);box.expandByObject(pointGroup);if(box.isEmpty())return;const center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3()).length();controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(1,.8,1.25).normalize().multiplyScalar(Math.max(size*1.9,7)));camera.near=Math.max(.01,size/1000);camera.far=Math.max(2000,size*100);camera.updateProjectionMatrix();controls.update();}
new ResizeObserver(()=>{const r=$('canvas').getBoundingClientRect();renderer.setSize(r.width,r.height);camera.aspect=r.width/r.height;camera.updateProjectionMatrix();}).observe($('canvas'));
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
function renderPatch(fit=false){const r=results[active],model=models[active]??models.preview;if(!model)return;draw(model,r?.placements??[{oi:0,translation:[0,0,0]}],fit);$('viewTitle').textContent=r?`${MODES.find(m=>m.id===active).name} · ${labels[r.result]??'searching'}`:'Tile geometry';$('coverage').textContent=r?`${r.verification?.covered??r.covered??0} / ${model.required.length} required points complete`:'Amber points = required window';}
function config(){return {tile:$('tile').value,radius:Number($('radius').value),seed:Math.max(1,Math.floor(Number($('seed').value)||1)),mirrors:$('mirrors').checked,timeMs:Math.max(1,Math.min(120,Number($('seconds').value)||10))*1000,nodes:10000,custom};}
function lock(value){busy=value;for(const id of ['run','suite','probe','tile','radius','seconds','seed','mirrors','import'])$(id).disabled=value;$('stop').disabled=!value;$('probe').disabled=value||!!models.preview?.slab;}
function syncModelUI(model){
  const slab=!!model.slab;
  [...$('radius').options].forEach((o,i)=>{const r=i+1;o.textContent=slab?`Slab radius ${r} · ${2*(1+3*r*(r+1))} points`:`${2*r+1} × ${2*r+1} × ${2*r+1} · ${(2*r+1)**3} points`;});
  $('domainBadge').textContent=slab?`Single slab · ${model.slab.sublatticeIndex===3?'index-3 A₂':'A₂'}`:'Exact point model · Z³';
  $('targetNote').textContent=slab?'Both caps carry planar t-values. Cap interiors have t = 1 and leave the frontier immediately. Growth is lateral only.':'All required points must sum to 1. Tiles may extend beyond the window.';
  $('probe').disabled=busy||slab;
  if(slab)$('probeResults').textContent='The 3D probes apply to the historical prism model, available in the original explorer. They do not test this single slab.';
  else if($('probeResults').textContent.startsWith('The 3D probes'))$('probeResults').textContent='Not screened in this session. No aperiodicity claim.';
}
function refresh(){
  for(const m of MODES){const r=results[m.id],s=r?.stats,b=$(`lane-${m.id}`);b.classList.toggle('selected',active===m.id);b.setAttribute('aria-pressed',String(active===m.id));b.innerHTML=`<div class="lane-name">${m.name}</div><div class="lane-value">${time(s?.totalMs)}</div><div class="lane-state">${r?labels[r.result]??'Searching…':'Ready to run'}</div><div class="lane-detail"><span>${fmt(s?.branches)} branches</span><span>${fmt(s?.forced)} forced</span></div>`;}
  $('rows').innerHTML=MODES.map(m=>{const r=results[m.id],s=r?.stats;return `<tr><td style="color:${m.color}">${m.name}</td><td>${time(s?.totalMs)}</td><td>${s?fmt(s.branches):'—'}</td><td>${s?fmt(s.backtracks):'—'}</td><td>${s?fmt(s.forced):'—'}</td><td>${s?fmt(s.capacityCuts+s.lookaheadCuts):'—'}</td><td>${s?fmt(s.clusterValidated):'—'}</td><td>${r?labels[r.result]??'Running':'Not run'}</td></tr>`;}).join('');
  inspect();drawChart();$('export').disabled=!archive.length&&!Object.keys(results).length;
}
function inspect(){
  const r=results[active],s=r?.stats;
  if(!r){$('inspection').textContent='Run a comparison to inspect costs, elimination reasons and learned cluster expansions.';$('clusterList').textContent='No clusters yet.';return;}
  if(!s){$('inspection').textContent=r.message??r.reason??'No completed measurement.';$('clusterList').textContent='No clusters retained.';return;}
  const marking=r.marking;
  $('inspection').textContent=`${r.reason?`Stopped: ${r.reason}. `:''}${fmt(s.attempts)} attempted base placements; ${fmt(s.candidates)} candidate nodes and ${fmt(s.edges)} incidence edges. Preparation ${time(s.preparationMs)}, graph construction ${time(s.graphMs)}, cluster proposal / learning ${time(s.learningMs)}. Estimated graph and trail footprint ${(s.memoryEstimateBytes/1048576).toFixed(1)} MiB (not process memory). ${fmt(s.capacityCuts)} residual-capacity contradictions; ${fmt(s.lookaheadCuts)} context-local failed-move eliminations from ${fmt(s.probes)} probes. ${marking?.rank?`Vector marking rank ${marking.rank}${marking.constantFallback?' (constant resource fallback)':''}; no boundary-specific pair rules are generalized. `:''}${fmt(s.clusterProposals)} sampled clusters, ${fmt(s.clusterValidated)} validated, ${fmt(s.clusterUses)} used for ordering. These proposals never remove base alternatives.`;
  $('clusterList').textContent=r.clusters?.length?JSON.stringify(r.clusters.slice(0,5),null,2)+`\nShowing ${Math.min(5,r.clusters.length)} of ${r.clusters.length}. Export contains the full library.`:'No cluster library in this lane. Live proposals are exported at completion.';
}
function drawChart(){
  const w=800,h=130,left=35,bottom=105,maxT=Math.max(1,...Object.values(series).flat().map(p=>p[0])),target=models.preview?.required.length??27;
  let s=`<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><line x1="${left}" y1="10" x2="${left}" y2="${bottom}"/><line x1="${left}" y1="${bottom}" x2="785" y2="${bottom}"/><line x1="${left}" y1="15" x2="785" y2="15" stroke-dasharray="3 5"/><text x="0" y="19">${target}</text><text x="16" y="109">0</text><text x="35" y="126">0 s</text><text x="713" y="126">${(maxT/1000).toFixed(1)} s</text>`;
  for(const m of MODES){const pts=series[m.id]??[];if(pts.length)s+=`<polyline points="${pts.map(([t,c])=>`${left+t/maxT*750},${bottom-c/target*90}`).join(' ')}" fill="none" stroke="${m.color}" stroke-width="2"/>`;}
  $('chart').innerHTML=s+'</svg>';
}
async function preview(){
  const sequence=++previewSequence;worker?.terminate();worker=null;results={};series={};models={};custom=$('tile').value==='custom'?custom:null;
  const selected=cases.find(c=>c.id===$('tile').value);$('tileName').textContent=custom?.name??selected?.name??'Custom system';$('tileNote').textContent=custom?'Imported custom point model; exactness is checked before comparison.':selected.note;$('probeResults').textContent='Not screened in this session. No aperiodicity claim.';$('status').textContent='Preparing tile geometry…';
  [geometryGroup,pointGroup,edgeGroup].forEach(clear);$('viewMeta').textContent='Preparing exact point data';$('coverage').textContent='No run yet';$('viewTitle').textContent='Tile geometry';refresh();const w=new Worker(new URL('./worker.js?v=2.1.0',import.meta.url),{type:'module'});worker=w;
  w.onmessage=({data})=>{if(sequence!==previewSequence)return;if(data.type==='model'){models.preview=data.model;syncModelUI(data.model);refresh();renderPatch(true);$('status').textContent='Ready. Run all four methods on the same point window.';w.terminate();worker=null;}if(data.type==='error'){$('status').textContent=data.message;w.terminate();worker=null;}};w.onerror=e=>{$('status').textContent=e.message;w.terminate();worker=null;};w.postMessage({...config(),action:'preview'});
}
function runWorker(c,action='search',strategy=null){
  return new Promise(resolve=>{
    const w=new Worker(new URL('./worker.js?v=2.1.0',import.meta.url),{type:'module'});worker=w;let done=false;
    const finish=r=>{if(done)return;done=true;clearTimeout(timer);w.terminate();if(worker===w)worker=null;resolve(r);};
    // A hard watchdog includes synchronous graph construction and module startup.
    const timer=setTimeout(()=>finish({...results[c.mode],type:'result',mode:c.mode,result:'unknown',reason:'worker wall-time safety limit',config:c}),c.timeMs+15000);
    w.onmessage=({data:e})=>{
      if(e.type==='model'){models[c.mode]=e.model;models.preview=e.model;syncModelUI(e.model);return;}
      if(e.type==='progress'||e.type==='result'){results[c.mode]=e;(series[c.mode]??=[[0,0]]).push([e.stats.totalMs,e.verification?.covered??e.covered??0]);refresh();if(active===c.mode)renderPatch();}
      if(e.type==='result'||e.type==='probe'||e.type==='error')finish(e);
    };
    w.onerror=e=>finish({type:'error',message:e.message});w.postMessage({...c,action,strategy});
    w.cancel=()=>finish({...results[c.mode],type:'result',mode:c.mode,result:'unknown',reason:'cancelled',config:c});
  });
}
function verdict(){
  const base=results.free;const wins=MODES.slice(1).filter(m=>results[m.id]?.result==='finite_exact'&&base?.result==='finite_exact'&&results[m.id].stats.totalMs<base.stats.totalMs);
  if(wins.length)$('verdict').textContent=`This run: ${wins.map(m=>`${m.name} used ${(base.stats.totalMs/results[m.id].stats.totalMs).toFixed(2)}× less total time`).join('; ')} than free-range for the same verified window. Repeat across seeds and larger windows before claiming a general advantage.`;
  else if(MODES.some(m=>results[m.id]?.result==='finite_exact')&&base?.result==='unknown')$('verdict').textContent='A learning lane verified the window while free-range reached its budget. This is a completion advantage under these limits; an exact time speedup cannot be calculated from a censored baseline.';
  else $('verdict').textContent='No measured speedup established in this run. Fewer branches alone do not establish acceleration; preparation, validation and learning costs are included.';
}
async function compare(c){
  results={};series={};models={};runConfig=c;active='free';refresh();
  for(const m of MODES){if(cancelled)break;active=m.id;$('status').textContent=`${cases.find(x=>x.id===c.tile)?.name??'Custom'} · ${m.name} · cold sequential run`;const r=await runWorker({...c,mode:m.id});if(r.type==='error'){results[m.id]={result:r.kind==='resource_limit'?'unknown':'error',message:r.message};$('status').textContent=r.message;}else results[m.id]=r;refresh();renderPatch();}
  archive.push({config:c,results:structuredClone(results),series:structuredClone(series)});verdict();
}
$('run').onclick=async()=>{previewSequence++;worker?.terminate();cancelled=false;lock(true);try{await compare(config());$('status').textContent=cancelled?'Stopped. Partial evidence is available to export.':'Comparison complete. Select a method to inspect its patch.';}finally{lock(false);}};
$('suite').onclick=async()=>{previewSequence++;worker?.terminate();cancelled=false;lock(true);const c=config();try{for(const test of cases.slice(0,5)){if(cancelled)break;$('tile').value=test.id;$('tileName').textContent=test.name;$('tileNote').textContent=test.note;await compare({...c,tile:test.id,custom:null});}$('status').textContent=cancelled?'Suite stopped. Completed runs are retained.':`Research suite complete. Export contains ${archive.length} experiment(s).`;}finally{lock(false);}};
$('stop').onclick=()=>{cancelled=true;worker?.cancel?.();};
$('probe').onclick=async()=>{previewSequence++;worker?.terminate();cancelled=false;lock(true);$('probeResults').textContent='';try{for(const strategy of ['translational','isohedral']){if(cancelled)break;$('status').textContent=`Checking ${strategy} · up to 8 motif tiles`;const r=await runWorker({...config(),mode:strategy},'probe',strategy);const p=document.createElement('div');p.textContent=`${strategy}: ${r.event?.success?'certificate found':r.message??'unknown within bounds'}`;$('probeResults').append(p);archive.push({probe:strategy,config:config(),result:r});}$('status').textContent='Structural probe results are separate from the finite-window race.';}finally{lock(false);}};
$('export').onclick=()=>{const data={version:VERSION,exportedAt:new Date().toISOString(),protocol:'Exact finite point target; exported model declares the single-slab or 3D domain, weights and boundary; all target points root generation 0; sequential cold online runs; timings include preparation and verification; no held-out claim',experiments:archive,current:{config:runConfig,results,series}},url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=`lattice-v2-evidence-${Date.now()}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('import').onclick=()=>{try{const value=JSON.parse($('custom').value);if(!value||typeof value!=='object'||(!value.polycubes?.length&&!value.polyhedra?.length&&!value.figure_refs?.length))throw Error('Include polycubes, polyhedra or figure_refs.');custom=value;if(!$('tile').querySelector('option[value="custom"]')){const o=document.createElement('option');o.value='custom';o.textContent='Custom system';$('tile').append(o);}$('tile').value='custom';preview();}catch(e){$('status').textContent=`Custom system: ${e.message}`;}};
for(const id of ['tile','radius','mirrors'])$(id).onchange=()=>preview();
$('fit').onclick=fitView;$('points').onclick=()=>{showPoints=!showPoints;pointGroup.visible=showPoints;$('points').textContent=`Points ${showPoints?'on':'off'}`;$('points').setAttribute('aria-pressed',String(showPoints));};$('edges').onclick=()=>{showEdges=!showEdges;edgeGroup.visible=showEdges;$('edges').textContent=`Edges ${showEdges?'on':'off'}`;$('edges').setAttribute('aria-pressed',String(showEdges));};
refresh();preview();

fetch(new URL('./reference/summary.json',import.meta.url)).then(r=>{if(!r.ok)throw Error('Reference unavailable');return r.json();}).then(data=>{
  const probes=new Map(data.probes.map(p=>[`${p.tile}:${p.strategy}`,p]));
  $('referenceRows').innerHTML=cases.slice(0,5).map(c=>`<tr><td>${c.name}</td>${MODES.map(m=>`<td>${data.rows.filter(r=>r.tile===c.id&&r.mode===m.id&&r.result==='finite_exact').length} / 3</td>`).join('')}<td>${['translational','isohedral'].map(s=>probes.get(`${c.id}:${s}`)?.success?'Found':'Unknown').join(' / ')}</td></tr>`).join('');
  $('referenceNote').textContent='Historical v2.0 only: these half-weight 3D prism measurements do not apply to the current single-slab hat/turtle model. '+data.conclusion;
}).catch(()=>{$('referenceRows').textContent='Recorded measurements are unavailable. Live comparisons remain available.';});
