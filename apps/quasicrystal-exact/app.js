import { setupCatalog } from './catalog-ui.js?v=live-search-workspace-v2';
import { CrystalScene } from './scene.js?v=live-search-workspace-v2';
const $ = s => document.querySelector(s);
const status = $('#status');
let selected=null,scene=null,activeSystem=null;
let liveDisplay=null,searchRunning=false,searchSummary=null,searchEpoch=0,exactSelection=false;
const texScalar = ([a,b,d]) => {
  let n = a === '0' ? '' : a;
  if(b !== '0') n += `${b.startsWith('-') || !n ? '' : '+'}${b === '1' ? '' : b === '-1' ? '-' : b}\\tau`;
  n ||= '0'; return d === '1' ? n : `\\frac{${n}}{${d}}`;
};
const typeset = e => window.MathJax?.typesetPromise?.([e]);
const texPoint=p=>`\\left(${p.map(texScalar).join(',\\;')}\\right)`;
function showPointValues(values){
  const details=$('#point-markings-details');details.hidden=!values?.length;if(!values?.length)return;
  const host=$('#point-markings-table');window.MathJax?.typesetClear?.([host]);host.replaceChildren();
  const table=document.createElement('table'),head=document.createElement('tr');
  for(const text of ['\\(p\\)','\\(m_B(p)\\)','\\(m_R(p)\\)']){const th=document.createElement('th');th.textContent=text;head.append(th);}table.append(head);
  for(const mark of values){const tr=document.createElement('tr');for(const v of [mark.point,...['black','red'].map(c=>typeof mark.components[c]==='string'?mark.components[c].split(';').map(x=>x.split(',')):mark.components[c])]){
    const td=document.createElement('td');td.textContent=Array.isArray(v)?`\\(${texPoint(v)}\\)`:JSON.stringify(v);tr.append(td);
  }table.append(tr);}host.append(table);typeset(host);
}
function showExact(vertices) {
  const sample = $('#sample'); window.MathJax?.typesetClear?.([sample]);
  sample.textContent = `\\[\\begin{aligned}${vertices.map((p,i) => `v_{${i}}&=\\left(${p.map(texScalar).join(',\\;')}\\right)`).join('\\\\')}\\end{aligned}\\]`;
  $('#sample-details').hidden = false; if($('#mathematics').open||$('#sample-details').open)typeset(sample);
}
try {
  scene = new CrystalScene($('#scene'), tile => {
    selected = tile; $('#inspector').hidden = !tile;
    if(!tile) return;
    $('#tile-kind').textContent = `${tile.kind === 'prolate' ? 'Prolate' : 'Oblate'} rhombohedron${tile.decoration?' · '+tile.decoration.hand+' handed':''}`;
    $('#inspect-exact').textContent=tile.pointValues?.length?'Exact vertices & point markings ↓':'Show exact vertices ↓';
    const target = $('#tile-data'); window.MathJax?.typesetClear?.([target]);
    target.textContent = `Axes \\((${tile.axes.join(',')})\\) · exact volume \\(${texScalar(tile.volume)}\\).`; typeset(target);
  });
  $('#spin').checked = scene.controls.autoRotate;
} catch(error) {
  $('#loading p').textContent = '3D graphics are unavailable in this browser. Exact JSON export is still available.';
  status.textContent = error.message;
}

const searchWorker=new Worker(new URL('./search-worker.js?v=live-search-workspace-v2',import.meta.url),{type:'module'});
const hasSearch=()=>activeSystem?.id==='ammann';
function searchConfig(){return {seed:Number($('#search-seed').value)||4,seedKind:$('#search-root').value,target:Number($('#search-target').value),budget:10000,markings:$('#search-rules').value,seedHand:$('#search-hand').value};}
function updateControls(){
 const supported=hasSearch(),terminal=['budget','exhausted'].includes(searchSummary?.state);
 $('#search-run').textContent=!supported?'Run search':searchRunning?'Pause':searchSummary?.state==='checkpoint'?'Continue search':'Run search';
 $('#search-run').disabled=!supported||terminal;$('#search-step').disabled=!supported||searchRunning||terminal;$('#search-reset').disabled=!supported;$('#search-export').disabled=!supported||!searchSummary;
 $('#search-run').title=supported?'Run or pause the actual search; the branch stack is preserved':'A live search engine has not been connected for this system';
}
function updateHeading(){
 const supported=hasSearch(),marked=$('#search-rules').value==='ammann';
 $('#scene').hidden=!supported;$('#catalog-unavailable').hidden=supported;$('#search-controls').hidden=!supported;$('.assembly-controls').hidden=!supported;$('#search-monitor').hidden=!supported;$('#search-live-counts').hidden=!supported;
 for(const selector of ['.stage-actions','.camera-presets','.gesture-hint'])$(selector).hidden=!supported;
 $('#loading').hidden=!supported||!!liveDisplay;
 if(supported){
  $('#scene-title').textContent=marked?'Ammann · exact tree search':'Unmarked · exact tree search';
  $('#view-heading').textContent=marked?'Face rules through point markings':'Unmarked face-to-face growth';
  $('#view-description').textContent=marked?'Black and red dots agree through exact point values. Every placement and rollback shown comes from the search.':'Bare geometry allows periodic tilings. Every placement and rollback shown comes from the search.';
  $('#regularity').textContent=marked?'Supplied rules · exact point values':'Unmarked geometric control';
  $('#marking-provenance').textContent=marked?'Supplied Ammann rules → exact point values. No learned restriction is active.':'Unmarked control. Periodic parallelotope tilings are valid in this problem.';
  $('#search-hand').disabled=!marked;$('.point-support-toggle').hidden=!marked;
  $('#geometry-badge').textContent='Exact search · approximate rendering';
 }else{
  const name=activeSystem?.name||'This system';$('#scene-title').textContent=name;
  $('#catalog-unavailable').textContent=`Live search is not connected for ${name}. The scenes on the left inspect its tiles; no search result is claimed.`;
  $('#visible-count').textContent=activeSystem?.count||'Prototype views';$('#geometry-badge').textContent='Prototype views only';status.textContent='Search unavailable for this catalog entry.';
 }
 updateControls();
}
function searchStatus(){
 if(!hasSearch()||!searchSummary)return;const s=searchSummary;
 status.textContent=s.state==='checkpoint'?`Paused at ${s.tiles} tiles with no dead frontier faces. Continue search to extend.`:s.state==='budget'?'Search budget reached. Extension remains unknown.':s.state==='exhausted'?'The current search tree is exhausted. Reset to start another configuration.':searchRunning?'Searching: trial placements, forced moves and backtracking.':!s.attempts?'Ready. Press Run search to begin.':'Search paused. Run search resumes the preserved branch stack.';
}
function resetSearch(){
 if(!hasSearch())return;exactSelection=false;showPointValues(null);scene?.select(null);liveDisplay=null;searchSummary=null;searchRunning=false;$('#loading').hidden=false;$('#loading p').textContent='Enumerating exact face attachments';updateControls();
 searchWorker.postMessage({type:'init',epoch:++searchEpoch,config:searchConfig(),delay:Number($('#search-speed').value),auto:false});
}
function selectSystem(system){
 const changed=activeSystem?.id!==system.id;activeSystem=system;
 if(!hasSearch())searchWorker.postMessage({type:'pause'});
 if(changed){scene?.select(null);if(hasSearch()&&liveDisplay&&scene){scene.mode='search';scene.updateModel(liveDisplay,true);}}
 updateHeading();searchStatus();
}
function drawTrace(trace){
 const svg=$('#search-trace');svg.replaceChildren();if(!trace.length)return;
 const max=Math.max(4,...trace.map(e=>e.depth));const NS='http://www.w3.org/2000/svg';
 const points=trace.map((e,i)=>[8+i/Math.max(1,trace.length-1)*884,66-e.depth/max*58]);
 const path=document.createElementNS(NS,'polyline');path.setAttribute('points',points.map(p=>p.join(',')).join(' '));path.setAttribute('fill','none');path.setAttribute('stroke','#729b96');path.setAttribute('stroke-width','1.5');svg.append(path);
 trace.forEach((e,i)=>{const dot=document.createElementNS(NS,'circle');dot.setAttribute('cx',points[i][0]);dot.setAttribute('cy',points[i][1]);dot.setAttribute('r',e.type==='remove'?'3.5':'2.4');dot.setAttribute('fill',e.type==='remove'?'#df8278':e.forced?'#6fc8b6':'#e9b865');svg.append(dot);});
}

searchWorker.onmessage=({data})=>{
 if(data.epoch!==undefined&&data.epoch!==searchEpoch)return;
 if(data.type==='error'){if(hasSearch()){status.textContent=data.error;$('#loading p').textContent=data.error;}return;}
 if(data.type==='export'){
  const url=URL.createObjectURL(new Blob([data.json],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='icosahedral-live-search.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);return;
 }
 if(data.type!=='snapshot')return;
 const first=!liveDisplay;liveDisplay=data.display;searchSummary=data.summary;searchRunning=data.running;
 $('#search-live-counts').textContent=`${data.summary.tiles} placed · ${data.summary.attempts} trials · ${data.summary.backtracks} backtracks`;
 for(const key of ['tiles','attempts','forced','branches','backtracks','frontier','candidates'])$(`#metric-${key}`).textContent=data.summary[key].toLocaleString();
 const event=data.event;
 $('#search-event').textContent=event.type==='remove'?'Dead end → backtracked one tile':event.type==='add'?`${event.forced?'Forced placement':'Branch trial'} · generation ${event.generation}`:event.type==='checkpoint'?'Finite checkpoint · viable frontier':event.type==='budget'?'Budget reached · result unknown':'Ready · seed tile and complete local domains';
 $('#search-marking-stats').textContent=data.summary.markingComponents?`${data.summary.markingPoints} exact support points · ${data.summary.markingComponents} assigned components · ${data.summary.eliminatedMarking} marking removals`:'No point markings assigned · geometric control';
 $('#search-graph-stats').textContent=`${data.summary.incidences} graph edges · ${data.summary.checks.toLocaleString()} exact checks · ${Math.round(data.summary.elapsedMs)} ms search`;
 drawTrace(data.trace);
 if(hasSearch()){
  if(scene){scene.mode='search';scene.updateModel(data.display,first);scene.setSearchFocus(data.nextFace,data.summary.dead>0);}
  if(data.display.tiles.length&&!exactSelection)showExact(data.display.tiles.at(-1).exact);
 }
 updateHeading();searchStatus();
};
searchWorker.onerror=()=>{status.textContent='The exact search worker could not load. Reload to retry.';};
function extendTarget(){
 if(!searchRunning&&searchSummary?.state==='checkpoint'&&Number($('#search-target').value)<=searchSummary.tiles){const next=[60,120,240,480].find(n=>n>searchSummary.tiles);if(next)$('#search-target').value=String(next);else{status.textContent='The largest demo target is reached. Reset to try another branch order.';return false;}}
 return true;
}
$('#search-run').onclick=()=>{if(!hasSearch()||!extendTarget())return;searchWorker.postMessage({type:searchRunning?'pause':'start',target:Number($('#search-target').value)});};
$('#search-step').onclick=()=>{if(hasSearch()&&extendTarget())searchWorker.postMessage({type:'step',target:Number($('#search-target').value)});};
$('#search-reset').onclick=resetSearch;$('#search-rules').onchange=()=>{updateHeading();resetSearch();};$('#search-export').onclick=()=>{if(hasSearch())searchWorker.postMessage({type:'export'});};
$('#search-speed').oninput=()=>searchWorker.postMessage({type:'speed',delay:Number($('#search-speed').value)});
let pending=false;
function updateDisplay(){
 $('#cutaway-value').textContent=`${$('#cutaway').value}%`;if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;scene?.setOptions({cutaway:Number($('#cutaway').value),prolate:$('#show-prolate').checked,oblate:$('#show-oblate').checked,edges:$('#edges').checked,pointSupport:$('#show-marking-points').checked});});
}
for(const id of ['cutaway','show-prolate','show-oblate','edges','show-marking-points'])$(`#${id}`).addEventListener('input',updateDisplay);
$('#spin').onchange=()=>{if(scene)scene.controls.autoRotate=$('#spin').checked;};
for(const b of document.querySelectorAll('[data-camera]'))b.onclick=()=>{document.querySelectorAll('[data-camera]').forEach(x=>x.classList.toggle('active',x===b));if(scene){scene.controls.autoRotate=false;scene.fit(b.dataset.camera);$('#spin').checked=false;}};
for(const b of document.querySelectorAll('[data-material]'))b.onclick=()=>{document.querySelectorAll('[data-material]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});scene?.setOptions({glass:b.dataset.material==='glass'});};
$('#reset-view').onclick=()=>scene?.fit();$('#snapshot').onclick=()=>scene?.saveImage();$('#close-inspector').onclick=()=>scene?.select(null);
$('.math-link').onclick=()=>{$('#mathematics').open=true;};
$('#inspect-exact').onclick=()=>{if(!selected)return;exactSelection=true;showExact(selected.exact);showPointValues(selected.pointValues);$('#mathematics').open=true;$('#sample-details').open=true;if(selected.pointValues?.length)$('#point-markings-details').open=true;$('#sample-details').scrollIntoView({behavior:'smooth',block:'center'});};
$('#sample-details').ontoggle=e=>{if(e.target.open)typeset($('#sample'));};
setupCatalog({onSystem:selectSystem});resetSearch();
