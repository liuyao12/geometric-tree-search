import { setupCatalog } from './catalog-ui.js?v=gcts-learning-v2';
import { TileViewer } from './tile-viewer.js?v=gcts-learning-v2';
import { CrystalScene } from './scene.js?v=gcts-learning-v2';
const $ = s => document.querySelector(s);
const status = $('#status');
let selected=null,scene=null,activeSystem=null;
let learningData=null,learningPhase=false,learnedModel=null,savedModel=null,insetViewer=null,insetKey=null,inspectingPair=false,savedReuse=false,validatingSaved=false;
const SAVED_KEY='gcts:icosahedral-learned-runs:v1';
try{savedModel=JSON.parse(localStorage.getItem(SAVED_KEY)||'[]').at(-1)||null;}catch{}
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
 const host=$('#point-markings-table');window.MathJax?.typesetClear?.([host]);host.replaceChildren();const channels=[...new Set(values.flatMap(m=>Object.keys(m.components)))];
 const table=document.createElement('table'),head=document.createElement('tr');for(const name of ['Exact point',...channels]){const th=document.createElement('th');th.textContent=name;head.append(th);}table.append(head);
 for(const mark of values){const tr=document.createElement('tr'),point=document.createElement('td');point.textContent=`\\(${texPoint(mark.point)}\\)`;tr.append(point);for(const channel of channels){const td=document.createElement('td'),v=mark.components[channel];td.textContent=v===undefined?'*':typeof v==='string'&&v.includes(';')?`\\(${texPoint(v.split(';').map(x=>x.split(',')))}\\)`:String(v);tr.append(td);}table.append(tr);}host.append(table);typeset(host);
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

const searchWorker=new Worker(new URL('./search-worker.js?v=gcts-learning-v2',import.meta.url),{type:'module'});
const hasSearch=()=>activeSystem?.id==='ammann';
function searchConfig(){return {seed:Number($('#search-seed').value)||4,seedKind:$('#search-root').value,target:Number($('#search-target').value),budget:10000,markings:$('#search-rules').value,seedHand:$('#search-hand').value};}
function updateControls(){
 const supported=hasSearch(),terminal=learningPhase?['accepted','complete','incomplete'].includes(learningData?.state):['budget','exhausted'].includes(searchSummary?.state);
 $('#search-run').textContent=!supported?'Run search':searchRunning?'Pause':learningPhase?'Resume learning':searchSummary?.state==='checkpoint'?'Continue search':'Run search';
 $('#search-run').disabled=!supported||terminal||validatingSaved;$('#search-step').disabled=!supported||searchRunning||terminal||validatingSaved;$('#search-reset').disabled=!supported||validatingSaved;$('#search-export').disabled=!supported||!searchSummary;
 $('#learn-new').disabled=!supported||searchRunning||validatingSaved;$('#learning-launch').hidden=!supported;$('#learn-reuse').hidden=!savedModel;$('#learn-reuse').disabled=searchRunning||!supported||validatingSaved;$('#learn-continue').hidden=!learningPhase||learningData?.state!=='incomplete';$('.learn-use').hidden=!learnedModel;$('#use-learned').checked=!!learnedModel&&!learningPhase;
 $('#search-run').title=supported?'Run or pause the actual search; the branch stack is preserved':'A live search engine has not been connected for this system';
}
function updateHeading(){
 const supported=hasSearch(),marked=$('#search-rules').value==='ammann';
 $('#learning-monitor').hidden=!supported||!learningData;$('#marking-inset').hidden=!supported||!learningData;
 $('#scene').hidden=!supported;$('#catalog-unavailable').hidden=supported;$('#search-controls').hidden=!supported;$('.assembly-controls').hidden=!supported;$('#search-monitor').hidden=!supported;$('#search-live-counts').hidden=!supported;
 for(const selector of ['.stage-actions','.camera-presets','.gesture-hint'])$(selector).hidden=!supported;
 $('#loading').hidden=!supported||(!validatingSaved&&!!liveDisplay);
 if(supported){
  $('#scene-title').textContent=validatingSaved?'Validating saved marking':learningPhase?'Learning · real corona search':learnedModel?'GCTS · learned point marking':marked?'Ammann · exact tree search':'Unmarked · exact tree search';
  $('#view-heading').textContent=marked?'Face rules through point markings':'Unmarked face-to-face growth';
  $('#view-description').textContent=marked?'Black and red dots agree through exact point values. Every placement and rollback shown comes from the search.':'Bare geometry allows periodic tilings. Every placement and rollback shown comes from the search.';
  $('#regularity').textContent=validatingSaved?'Replaying saved evidence':learningPhase?'Oracle: supplied rules, no learned filter':learnedModel?'Supplied rules + frozen learned restriction':marked?'Supplied rules · exact point values':'Unmarked geometric control';
  $('#marking-provenance').textContent=validatingSaved?'Validating the saved model before any learned field is used.':learnedModel&&!learningPhase?'Learned restriction active. Point values filter the global graph; finite pair evidence does not certify infinite extension.':marked?'Supplied Ammann rules → exact point values. No learned restriction is active.':'Unmarked control. Periodic parallelotope tilings are valid in this problem.';
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
 if(!hasSearch()||!searchSummary)return;if(validatingSaved){status.textContent='Replaying saved positive witnesses, classification scores and the rotation action…';return;}if(learningPhase){status.textContent=learningData?.state==='incomplete'?'Learning is incomplete. Unresolved pairs impose no constraints; Continue learning increases the oracle budget.':learningData?.state==='complete'?'The complete catalog did not pass the marking gate. No learned restriction was activated.':searchRunning?'Learning from actual corona attempts. Provisional values do not filter this search.':'Learning paused. Resume learning preserves the current corona stack.';return;}const s=searchSummary;
 status.textContent=s.state==='checkpoint'?`Paused at ${s.tiles} tiles with no dead frontier faces. Continue search to extend.`:s.state==='budget'?'Search budget reached. Extension remains unknown.':s.state==='exhausted'?(learnedModel?'This learned restriction exhausted the rooted search. The supplied-rule problem remains unresolved. Disable the learned marking or learn another support.':'The current search tree is exhausted. Reset to start another configuration.'):searchRunning?'Searching: trial placements, forced moves and backtracking.':!s.attempts?'Ready. Press Run search to begin.':'Search paused. Run search resumes the preserved branch stack.';
}
function resetSearch(){
 if(!hasSearch())return;validatingSaved=false;learningPhase=false;inspectingPair=false;exactSelection=false;showPointValues(null);scene?.select(null);liveDisplay=null;searchSummary=null;searchRunning=false;$('#loading').hidden=false;$('#loading p').textContent='Enumerating exact face attachments';updateControls();
 searchWorker.postMessage({type:'init',epoch:++searchEpoch,config:{...searchConfig(),learnedMarking:learnedModel},delay:Number($('#search-speed').value),auto:false});
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
 if(data.type==='error'){if(validatingSaved){validatingSaved=false;learnedModel=null;$('#loading').hidden=true;updateControls();}if(hasSearch()){status.textContent=data.error;$('#loading p').textContent=data.error;}return;}
 if(data.type==='export'){
  const url=URL.createObjectURL(new Blob([data.json],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='icosahedral-live-search.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);return;
 }
 if(data.type==='pair-inspection'){inspectingPair=true;scene?.updateModel(data.display,true);$('#scene-title').textContent='Evidence pair · '+data.status;$('#search-live-counts').textContent='Inspecting two fixed tiles';if(data.preview){insetViewer??=new TileViewer($('#learned-preview'),{color:'#94ba9f'});insetViewer.setModel({...data.preview,dots:undefined});renderFieldTable(data);}$('#learning-pair-result').textContent=`${data.status} · ${data.reason} · learned field ${data.compatible?'accepts':'rejects'} this pair`;return;}
 if(data.type!=='snapshot')return;
 const wasLearning=learningPhase;learningPhase=data.phase==='learning';const first=!liveDisplay||wasLearning!==learningPhase;liveDisplay=data.display;searchSummary=data.summary;searchRunning=data.running;
 if(data.learning)renderLearning(data.learning);
 if(data.learned){validatingSaved=false;if(!learningData||learningData.model?.id!==data.learned.id){const m=learnedModel||savedModel;if(m)renderLearning({state:'accepted',model:m,marking:m,counts:m.counts,total:m.totalPairs,resolved:m.totalPairs,rows:m.evidence,preview:data.learned.preview,slots:data.learned.slots,orientation:data.learned.orientation,oracleMs:m.oracleMs||0,learningMs:m.learningMs||0,validationMs:m.validationMs||0,elapsedMs:m.trainingMs||0,attempts:m.evidence.reduce((n,r)=>n+r.attempts,0),backtracks:m.evidence.reduce((n,r)=>n+r.backtracks,0)});}$('#marking-inset-title').textContent='Frozen learned marking';$('#learning-state').textContent=savedReuse?'Validated saved marking · active in search':'Validated marking · active in search';if(savedReuse)$('#learning-reason').textContent=`Saved run revalidated in ${(data.learned.reuseMs/1000).toFixed(1)} s. Original learning counts are shown above.`;}
 $('#search-live-counts').textContent=`${data.summary.tiles} placed · ${data.summary.attempts} trials · ${data.summary.backtracks} backtracks`;
 for(const key of ['tiles','attempts','forced','branches','backtracks','frontier','candidates'])$(`#metric-${key}`).textContent=data.summary[key].toLocaleString();
 const event=data.event;
 $('#search-event').textContent=event.type==='remove'?'Dead end → backtracked one tile':event.type==='add'?`${event.forced?'Forced placement':'Branch trial'} · generation ${event.generation}`:event.type==='checkpoint'?'Finite checkpoint · viable frontier':event.type==='budget'?'Budget reached · result unknown':'Ready · seed tile and complete local domains';
 $('#search-marking-stats').textContent=data.summary.markingComponents?`${data.summary.markingPoints} exact support points · ${data.summary.markingComponents} assigned components · ${data.summary.eliminatedMarking||0} marking removals · ${data.summary.eliminatedLearned||0} additional learned`:'No point markings assigned · geometric control';
 $('#search-graph-stats').textContent=`${data.summary.incidences} graph edges · ${(data.summary.checks||0).toLocaleString()} exact checks · ${Math.round(data.summary.elapsedMs)} ms search`;
 drawTrace(data.trace);
 if(hasSearch()&&!inspectingPair){
  if(scene){scene.mode='search';scene.updateModel(data.display,first);scene.setSearchFocus(data.nextFace,data.summary.dead>0);}
  if(data.display.tiles.length&&!exactSelection)showExact(data.display.tiles.at(-1).exact);
 }
 updateHeading();searchStatus();
};
searchWorker.onerror=()=>{status.textContent='The exact search worker could not load. Reload to retry.';};
function extendTarget(){
 if(learningPhase)return true;
 if(!searchRunning&&searchSummary?.state==='checkpoint'&&Number($('#search-target').value)<=searchSummary.tiles){const next=[60,120,240,480].find(n=>n>searchSummary.tiles);if(next)$('#search-target').value=String(next);else{status.textContent='The largest demo target is reached. Reset to try another branch order.';return false;}}
 return true;
}
$('#search-run').onclick=()=>{inspectingPair=false;if(!hasSearch()||!extendTarget())return;searchWorker.postMessage({type:searchRunning?'pause':'start',target:Number($('#search-target').value)});};
$('#search-step').onclick=()=>{inspectingPair=false;if(hasSearch()&&extendTarget())searchWorker.postMessage({type:'step',target:Number($('#search-target').value)});};
$('#search-reset').onclick=resetSearch;$('#search-rules').onchange=()=>{learnedModel=null;updateHeading();resetSearch();};$('#search-export').onclick=()=>{if(hasSearch())searchWorker.postMessage({type:'export'});};
$('#search-speed').oninput=()=>searchWorker.postMessage({type:'speed',delay:Number($('#search-speed').value)});
let pending=false;
function updateDisplay(){
 $('#cutaway-value').textContent=`${$('#cutaway').value}%`;if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;scene?.setOptions({cutaway:Number($('#cutaway').value),prolate:$('#show-prolate').checked,oblate:$('#show-oblate').checked,edges:$('#edges').checked,pointSupport:$('#show-marking-points').checked,learned:$('#show-learned').checked});});
}
for(const id of ['cutaway','show-prolate','show-oblate','edges','show-marking-points','show-learned'])$(`#${id}`).addEventListener('input',updateDisplay);
$('#spin').onchange=()=>{if(scene)scene.controls.autoRotate=$('#spin').checked;};
for(const b of document.querySelectorAll('[data-camera]'))b.onclick=()=>{document.querySelectorAll('[data-camera]').forEach(x=>x.classList.toggle('active',x===b));if(scene){scene.controls.autoRotate=false;scene.fit(b.dataset.camera);$('#spin').checked=false;}};
for(const b of document.querySelectorAll('[data-material]'))b.onclick=()=>{document.querySelectorAll('[data-material]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});scene?.setOptions({glass:b.dataset.material==='glass'});};
$('#reset-view').onclick=()=>scene?.fit();$('#snapshot').onclick=()=>scene?.saveImage();$('#close-inspector').onclick=()=>scene?.select(null);
$('.math-link').onclick=()=>{$('#mathematics').open=true;};
$('#inspect-exact').onclick=()=>{if(!selected)return;exactSelection=true;showExact(selected.exact);showPointValues(selected.pointValues);$('#mathematics').open=true;$('#sample-details').open=true;if(selected.pointValues?.length)$('#point-markings-details').open=true;$('#sample-details').scrollIntoView({behavior:'smooth',block:'center'});};
$('#sample-details').ontoggle=e=>{if(e.target.open)typeset($('#sample'));};

function saveLearned(model){
 savedModel=model;try{const runs=JSON.parse(localStorage.getItem(SAVED_KEY)||'[]');runs.push(model);localStorage.setItem(SAVED_KEY,JSON.stringify(runs,(_,v)=>typeof v==='bigint'?String(v):v));savedModel=model;}catch{$('#learning-reason').textContent+=' Browser storage is unavailable; this model remains usable for this visit.';}
}
function activateLearned(model,{reuse=false}={}){
 savedReuse=reuse;validatingSaved=reuse;
 learnedModel=model;if(reuse){$('#loading').hidden=false;$('#loading p').textContent='Validating saved evidence and exact point values';status.textContent='Replaying saved positive witnesses, classification scores and the rotation action…';updateControls();}inspectingPair=false;$('#search-rules').value='ammann';searchWorker.postMessage({type:'activate',model,config:searchConfig()});
}
function renderLearning(data){
 const previous=learningData;learningData=data;$('#learning-monitor').hidden=false;$('#marking-inset').hidden=!hasSearch();$('#learning-state').textContent=data.state==='validating'?'Independently replaying every positive witness':data.state==='accepted'?'Validated marking · starting marked growth':data.state==='incomplete'?'Unresolved pairs · continue with more search':data.state==='complete'?'Catalog complete · marking gate not passed':searchRunning?'Learning from local extension tests':'Local extension learning';
 $('#learning-progress').textContent=`${data.resolved} / ${data.total} pairs`;$('#learning-bar').max=data.total;$('#learning-bar').value=data.resolved;
 $('#learning-counts').textContent=`${data.counts.positive} positive · ${data.counts.negative} negative · ${data.counts.unresolved} unresolved`;
 const m=data.marking;$('#learning-scores').textContent=m?`${m.positivePassed} / ${data.counts.positive} positives pass · ${m.negativeBlocked} / ${data.counts.negative} negatives blocked`:'No resolved constraints yet';
 $('#learning-cost').textContent=`${(data.oracleMs/1000).toFixed(1)} s oracle · ${(data.learningMs/1000).toFixed(1)} s synthesis · ${((data.validationMs||0)/1000).toFixed(1)} s validation · ${(data.elapsedMs/1000).toFixed(1)} s elapsed`;
 $('#learning-reason').textContent=`${data.current?.reason||'Testing the next fixed pair'} · ${data.attempts} total oracle trials · ${data.backtracks} backtracks`;
 if(m){$('#marking-inset-counts').textContent=`${m.points} points · ${m.values} values across all 120 orientations`;$('#learned-field-scope').textContent=`${m.supportSlots} eligible slots across 120 orientations. ${m.points} active points and ${m.values} assigned component values. Individual * entries are free; zero is assigned. Rotation-transferred equalities; finite face-pair evidence only.`;}
 const key=`${m?.revision}:${data.orientation}`;
 if(key!==insetKey&&data.preview){insetKey=key;insetViewer??=new TileViewer($('#learned-preview'),{color:'#94ba9f'});const preview={...data.preview,dots:undefined};insetViewer.setModel(preview);renderFieldTable(data);}
 if(!previous||previous.resolved!==data.resolved){const select=$('#learning-pair'),old=select.value;select.replaceChildren();for(const [i,row]of data.rows.entries()){const option=document.createElement('option');option.value=String(i);option.textContent=`${i+1}. ${row.status} · ${row.reason}`;select.append(option);}if(old&&Number(old)<data.rows.length)select.value=old;}
 if(data.state==='accepted'&&data.model&&learnedModel?.id!==data.model.id){saveLearned(data.model);activateLearned(data.model);}
}
function renderFieldTable(data){
 const host=$('#learned-field');window.MathJax?.typesetClear?.([host]);host.replaceChildren();for(const slot of data.slots||[]){const tr=document.createElement('tr'),point=document.createElement('td');point.textContent=`\\(${texPoint(slot.point)}\\)`;tr.append(point);for(const value of slot.values){const td=document.createElement('td');td.textContent=value===null?'*':String(value);tr.append(td);}host.append(tr);}if($('#learning-monitor details').open)typeset(host);
}
$('#learning-monitor details').ontoggle=e=>{if(e.target.open)typeset($('#learned-field'));};
$('#learn-new').onclick=()=>{learnedModel=null;learningData=null;learningPhase=true;inspectingPair=false;$('#marking-inset-title').textContent='Provisional marking';$('#search-rules').value='ammann';searchWorker.postMessage({type:'learn',config:{extent:Number($('#learn-extent').value),attempts:Number($('#learn-budget').value)}});};
$('#learn-continue').onclick=()=>searchWorker.postMessage({type:'continue-learning',attempts:Number($('#learn-budget').value)});
$('#learn-reuse').onclick=()=>{if(savedModel)activateLearned(savedModel,{reuse:true});};
$('#use-learned').onchange=()=>{if(!$('#use-learned').checked){learnedModel=null;resetSearch();}else if(savedModel)activateLearned(savedModel);};
$('#marking-inset-toggle').onchange=()=>{$('#learned-preview').hidden=!$('#marking-inset-toggle').checked;};
$('#learning-pair').onchange=()=>{if(!learningData)return;searchWorker.postMessage({type:'pause'});searchWorker.postMessage({type:'inspect-pair',index:Number($('#learning-pair').value)});};
$('#learning-live').onclick=()=>{inspectingPair=false;if(liveDisplay)scene?.updateModel(liveDisplay,true);updateHeading();if(searchSummary)$('#search-live-counts').textContent=`${searchSummary.tiles} placed · ${searchSummary.attempts} trials · ${searchSummary.backtracks} backtracks`;};

setupCatalog({onSystem:selectSystem});resetSearch();
