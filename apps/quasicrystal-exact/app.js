import { CrystalScene } from './scene.js';
const $ = s => document.querySelector(s);
const generate = $('#generate'), download = $('#download'), status = $('#status');
let exportJSON = null, exportRadius = 1, selected = null, scene = null, mode = 'search';
let referenceDisplay=null,liveDisplay=null,referenceJSON=null,searchRunning=false,searchSummary=null;
const texScalar = ([a,b,d]) => {
  let n = a === '0' ? '' : a;
  if(b !== '0') n += `${b.startsWith('-') || !n ? '' : '+'}${b === '1' ? '' : b === '-1' ? '-' : b}\\tau`;
  n ||= '0'; return d === '1' ? n : `\\frac{${n}}{${d}}`;
};
const typeset = e => window.MathJax?.typesetPromise?.([e]);
function showExact(vertices) {
  const sample = $('#sample'); window.MathJax?.typesetClear?.([sample]);
  sample.textContent = `\\[\\begin{aligned}${vertices.map((p,i) => `v_{${i}}&=\\left(${p.map(texScalar).join(',\\;')}\\right)`).join('\\\\')}\\end{aligned}\\]`;
  $('#sample-details').hidden = false; if($('#mathematics').open||$('#sample-details').open)typeset(sample);
}
try {
  scene = new CrystalScene($('#scene'), tile => {
    selected = tile; $('#inspector').hidden = !tile;
    if(!tile) return;
    $('#tile-kind').textContent = `${tile.kind === 'prolate' ? 'Prolate' : 'Oblate'} rhombohedron`;
    const target = $('#tile-data'); window.MathJax?.typesetClear?.([target]);
    target.textContent = `Axes \\((${tile.axes.join(',')})\\) · exact volume \\(${texScalar(tile.volume)}\\).`; typeset(target);
  });
  $('#spin').checked = scene.controls.autoRotate;
} catch(error) {
  $('#loading p').textContent = '3D graphics are unavailable in this browser. Exact JSON export is still available.';
  status.textContent = error.message;
}
const worker = new Worker(new URL('./worker.js',import.meta.url),{type:'module'});
generate.onclick = () => {
  exportJSON = null; generate.disabled = true; download.disabled = true;
  if(mode!=='search'){$('#loading').hidden = false; $('#loading p').textContent = 'Constructing the exact patch';}
  $('#summary').replaceChildren(); $('#sample-details').hidden = true;
  if(mode!=='search')status.textContent = 'Constructing and projecting exact algebraic geometry…';
  exportRadius = Number($('#radius').value); worker.postMessage({radius:exportRadius});
};
worker.onmessage = ({data}) => {
  generate.disabled = false;
  if(!data.ok) { status.textContent = data.error; $('#loading p').textContent = data.error; return; }
  referenceJSON=data.json;referenceDisplay=data.display;if(mode!=='search')exportJSON=data.json; download.disabled = false;
  if(mode!=='search')status.textContent = 'Exact patch ready. Display controls leave the exported geometry unchanged.';
  for(const [label,value] of [['Tiles',data.count],['Prolate',data.counts.prolate],['Oblate',data.counts.oblate],['Global grid regularity',data.regular?'Certified':'Inconclusive']]) {
    const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent=label; dd.textContent=String(value); $('#summary').append(dt,dd);
  }
  if(mode!=='search'){$('#prolate-count').textContent = data.counts.prolate.toLocaleString(); $('#oblate-count').textContent = data.counts.oblate.toLocaleString();}
  $('#regularity').textContent = data.regular ? 'Exact geometry · regular grid certified' : 'Exact geometry · regularity inconclusive';
  if(mode!=='search'){showExact(data.sample.vertices);if(scene){scene.setModel(data.display);$('#loading').hidden=true;}}
  updateHeading();
};
worker.onerror = () => { generate.disabled=false; status.textContent='The construction worker could not load. Reload to retry.'; $('#loading p').textContent=status.textContent; };
const descriptions = {
  search:['Live face-to-face growth','Two undecorated shapes. Four candidates per exposed face before exact overlap and contact checks. No window or multigrid filter.','The graph checks every open face for dead ends, then forced moves, then branches at the earliest generation. A finite patch is not an infinite-tiling certificate.','Exact face-to-face tree search'],
  crystal:['Golden rhombohedra','The central connected patch from six grid directions. Click either color to inspect a tile, or reveal the interior to see how the pieces fit.','The two shapes meet face to face. Their golden rhombi reveal the structure of the assembly.','A finite icosahedral patch'],
  exploded:['Space between the pieces','Pull the assembly apart along the line from its center to each tile. Every piece retains its original shape and orientation.','Separation is a display transform. Set it to zero to return every tile to its exact placement.','Exploded assembly'],
  tiles:['Two shapes. One edge length.','Compare the elongated prolate tile with the flattened oblate tile. Both have six golden-rhombus faces and exactly the same edge length.','Both tiles are shown at the same scale. The prolate tile has the golden ratio times the volume of the oblate tile.','The golden rhombohedra'],
  window:['The hidden selection rule','In the complementary internal space, accepted vertices lie inside this rhombic triacontahedron. Gold points come from the current patch.','Thirty golden faces bound the acceptance window. Its exact supporting planes decide which integer lifts become vertices.','Internal space · acceptance window']
};
function updateHeading() {
  const [heading,description,caption,title]=descriptions[mode]; $('#view-heading').textContent=heading; $('#view-description').textContent=description; $('#caption').textContent=caption; $('#scene-title').textContent=title;
  $('.caption-index').textContent=`0${Object.keys(descriptions).indexOf(mode)+1} / 05`;
  $('#search-live-counts').hidden=mode!=='search';$('#search-controls').hidden=mode!=='search';$('#search-monitor').hidden=mode!=='search';$('.generation-controls').hidden=mode==='search';$('#fragments').parentElement.hidden=mode==='search';
  $('#regularity').textContent=mode==='search'?'Exact geometry · no added markings':'Exact geometry · regular grid certified';
  const applicable=mode==='crystal'||mode==='exploded'||mode==='search'; $('#separation').disabled=!applicable; $('#cutaway').disabled=!applicable;
  $('#show-prolate').disabled=mode==='window'; $('#show-oblate').disabled=mode==='window';
}
for(const button of document.querySelectorAll('[data-mode]')) button.onclick=()=>{
  mode=button.dataset.mode; document.querySelectorAll('[data-mode]').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',String(b===button));});
  $('#separation').value=mode==='exploded'?'35':'0'; $('#separation-value').textContent=`${$('#separation').value}%`; $('#cutaway').value='0'; $('#cutaway-value').textContent='0%';
  if(mode!=='search')searchWorker.postMessage({type:'pause'});
  if(scene){scene.options.separation=Number($('#separation').value);scene.options.cutaway=0;scene.mode=mode;const model=mode==='search'?liveDisplay:referenceDisplay;if(model){scene.setModel(model);$('#loading').hidden=true;}}
  if(mode!=='search'){exportJSON=referenceJSON;status.textContent='Constructed reference patch. This lane is separate from the undecorated live search.';}else if(searchSummary){status.textContent=searchRunning?'Searching exact face attachments.':'Search paused. Start to resume the preserved branch.';}updateHeading();
};
let pending=false;
function updateDisplay(){
  $('#separation-value').textContent=`${$('#separation').value}%`; $('#cutaway-value').textContent=`${$('#cutaway').value}%`;
  if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;scene?.setOptions({separation:Number($('#separation').value),cutaway:Number($('#cutaway').value),prolate:$('#show-prolate').checked,oblate:$('#show-oblate').checked,edges:$('#edges').checked,fragments:$('#fragments').checked});});
}
for(const id of ['separation','cutaway','show-prolate','show-oblate','edges','fragments']) $(`#${id}`).addEventListener('input',updateDisplay);
$('#spin').onchange=()=>{if(scene)scene.controls.autoRotate=$('#spin').checked;};
for(const b of document.querySelectorAll('[data-camera]')) b.onclick=()=>{
  document.querySelectorAll('[data-camera]').forEach(x=>x.classList.toggle('active',x===b));if(scene){scene.controls.autoRotate=false;scene.fit(b.dataset.camera);$('#spin').checked=false;}
};
for(const b of document.querySelectorAll('[data-material]')) b.onclick=()=>{
  document.querySelectorAll('[data-material]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});scene?.setOptions({glass:b.dataset.material==='glass'});
};
$('#reset-view').onclick=()=>scene?.fit(); $('#snapshot').onclick=()=>scene?.saveImage(); $('#close-inspector').onclick=()=>scene?.select(null);
$('.math-link').onclick=()=>{ $('#mathematics').open=true; };
$('#inspect-exact').onclick=()=>{if(!selected)return;showExact(selected.exact);$('#mathematics').open=true;$('#sample-details').open=true;$('#sample-details').scrollIntoView({behavior:'smooth',block:'center'});};
$('#sample-details').ontoggle=e=>{if(e.target.open)typeset($('#sample'));};
download.onclick=()=>{if(mode==='search'){searchWorker.postMessage({type:'export'});return;}if(!exportJSON)return;const url=URL.createObjectURL(new Blob([exportJSON],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`icosahedral-exact-radius-${exportRadius}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};



const searchWorker=new Worker(new URL('./search-worker.js',import.meta.url),{type:'module'});
function searchConfig(){return {seed:Number($('#search-seed').value)||4,seedKind:$('#search-root').value,target:Number($('#search-target').value),budget:10000};}
function resetSearch(){
  scene?.select(null);liveDisplay=null;$('#loading').hidden=false;$('#loading p').textContent='Enumerating exact face attachments';
  searchWorker.postMessage({type:'init',config:searchConfig(),delay:Number($('#search-speed').value),auto:true});
}
function drawTrace(trace){
 const svg=$('#search-trace');svg.replaceChildren();if(!trace.length)return;
 const max=Math.max(4,...trace.map(e=>e.depth));const NS='http://www.w3.org/2000/svg';
 const points=trace.map((e,i)=>[8+i/Math.max(1,trace.length-1)*884,66-e.depth/max*58]);
 const path=document.createElementNS(NS,'polyline');path.setAttribute('points',points.map(p=>p.join(',')).join(' '));path.setAttribute('fill','none');path.setAttribute('stroke','#729b96');path.setAttribute('stroke-width','1.5');svg.append(path);
 trace.forEach((e,i)=>{const dot=document.createElementNS(NS,'circle');dot.setAttribute('cx',points[i][0]);dot.setAttribute('cy',points[i][1]);dot.setAttribute('r',e.type==='remove'?'3.5':'2.4');dot.setAttribute('fill',e.type==='remove'?'#df8278':e.forced?'#6fc8b6':'#e9b865');svg.append(dot);});
}
searchWorker.onmessage=({data})=>{
 if(data.type==='error'){status.textContent=data.error;$('#loading p').textContent=data.error;return;}
 if(data.type==='export'){
  const url=URL.createObjectURL(new Blob([data.json],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='icosahedral-live-search.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);return;
 }
 if(data.type!=='snapshot')return;
 const first=!liveDisplay;liveDisplay=data.display;searchSummary=data.summary;searchRunning=data.running;
 $('#search-run').textContent=data.running?'Pause':data.summary.state==='checkpoint'?'Continue':'Start';
 $('#search-run').disabled=['budget','exhausted'].includes(data.summary.state);$('#search-step').disabled=data.running||['budget','exhausted'].includes(data.summary.state);download.disabled=false;$('#search-export').disabled=false;$('#search-live-counts').textContent=`${data.summary.tiles} tiles · ${data.summary.forced} forced · ${data.summary.branches} branches · ${data.summary.backtracks} rollbacks`;
 for(const key of ['tiles','forced','branches','backtracks','frontier','candidates'])$(`#metric-${key}`).textContent=data.summary[key].toLocaleString();
 const event=data.event;
 $('#search-event').textContent=event.type==='remove'?'Dead face → rolled back one tile':event.type==='add'?`${event.forced?'Forced placement':'Branch decision'} · generation ${event.generation}`:event.type==='checkpoint'?'Finite checkpoint · viable frontier':event.type==='budget'?'Budget reached · result unknown':'Seed tile · complete local domains';
 $('#search-graph-stats').textContent=`${data.summary.incidences} graph edges · ${Math.round(data.summary.elapsedMs)} ms search`;
 drawTrace(data.trace);
 if(mode==='search'){
  if(scene){scene.mode='search';scene.updateModel(data.display,first);scene.setSearchFocus(data.nextFace,data.summary.dead>0);$('#loading').hidden=true;}
  status.textContent=data.summary.state==='checkpoint'?`Paused at ${data.summary.tiles} tiles with no dead frontier faces. Increase the target and Continue to extend.`:data.summary.state==='budget'?'Search budget reached. Extension remains unknown.':data.running?'Searching exact face attachments. No decorations or window filter.':'Search paused. The branch stack and exact graph are preserved.';
  $('#regularity').textContent='Exact geometry · no added markings';
  if(data.display.tiles.length)showExact(data.display.tiles.at(-1).exact);
 }
 updateHeading();
};
searchWorker.onerror=()=>{status.textContent='The exact search worker could not load. Reload to retry.';};
$('#search-run').onclick=()=>{
 if(!searchRunning&&searchSummary?.state==='checkpoint'&&Number($('#search-target').value)<=searchSummary.tiles){
  const next=[60,120,240,480].find(n=>n>searchSummary.tiles);if(next)$('#search-target').value=String(next);else {status.textContent='The largest demo target is reached. Reset to try another branch order.';return;}
 }
 searchWorker.postMessage({type:searchRunning?'pause':'start',target:Number($('#search-target').value)});
};
$('#search-step').onclick=()=>searchWorker.postMessage({type:'step',target:Number($('#search-target').value)});
$('#search-reset').onclick=resetSearch;$('#search-export').onclick=()=>searchWorker.postMessage({type:'export'});
$('#search-speed').oninput=()=>searchWorker.postMessage({type:'speed',delay:Number($('#search-speed').value)});
updateHeading();resetSearch();generate.click();
