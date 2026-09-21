import {rememberMarking} from './marking-library.js?v=20260921-tile-system';
import {reduceMarking,activeMarkingSupport} from './marking-reduction.js?v=20260921-sublattice';
import {markingSegmentEndpoints} from './marking-segments.js?v=20260920-centered';
import {markingMetadata,markingMetadataText} from './marking-metadata.js?v=20260921-tile-system';
import {createCoronaLearner as createConnectionLearner,TILE_SETS,CORONA_CRITERION} from './tile-corona-learning.js?v=20260921-corona-animation';
const $=id=>document.getElementById(id),canvas=$('learn-canvas'),ctx=canvas.getContext('2d'),picker=$('learn-connection');
const tileSetInputs=Array.from(document.querySelectorAll('input[name="learning-tiles"]'));
const selectTiles=id=>tileSetInputs.forEach(input=>{input.checked=input.value===id;});
const embedded=window.parent!==window;if(embedded)document.body.classList.add('embedded');
let lattice='A2';
const learningKey=()=>`${setId}:${lattice}`;
let setId='turtle',learner=createConnectionLearner(setId),report=null,model=null,shown=[],worker=null,mode=null,runningSetId=null,paused=false,epoch=0;
const reports=new Map(),automaticStarts=new Set();
let searchFrame=null,searchBounds=null,frameTimer=null;
const send=(type,data={})=>{if(embedded)parent.postMessage({type,setId,lattice,...data},location.origin);};
const message=t=>$('learn-status').textContent=t;
const project=([x,y,z])=>[(z-x)/Math.sqrt(2),(2*y-x-z)/Math.sqrt(6)];
function mapFor(points,box){const p=points.map(project),xs=p.map(q=>q[0]),ys=p.map(q=>q[1]),minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys),scale=Math.min((box.w-30)/Math.max(1,maxx-minx),(box.h-30)/Math.max(1,maxy-miny));return p=>{const q=project(p);return[box.x+box.w/2+(q[0]-(minx+maxx)/2)*scale,box.y+box.h/2+(q[1]-(miny+maxy)/2)*scale];};}
function polygon(loop,map,fill,core=false){ctx.beginPath();loop.forEach((p,i)=>i?ctx.lineTo(...map(p)):ctx.moveTo(...map(p)));ctx.closePath();ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle='#52786b';ctx.lineWidth=core?2.5:1;ctx.stroke();}
function marks(entries,map){for(const e of entries){const [q,tip]=markingSegmentEndpoints(e).map(map);ctx.strokeStyle=e.value===0?'#7d9088':`hsl(${Math.abs(e.value)*137.5%360} 60% 37%)`;ctx.lineWidth=e.value===0?1:1.7;ctx.setLineDash(e.value<0?[2,2]:[]);ctx.beginPath();ctx.moveTo(...q);ctx.lineTo(...tip);ctx.stroke();}ctx.setLineDash([]);}
function draw(){$('learn-metadata').textContent=model?`${report?.model?model.marking.name:'Candidate — not saved'} · ${markingMetadataText(model)}`:'Marking: awaiting complete classification…';ctx.fillStyle='#fafbf7';ctx.fillRect(0,0,720,360);ctx.fillStyle='#294d43';ctx.font='14px system-ui';ctx.fillText(mode&&searchFrame?`Pair ${searchFrame.index+1} · ${searchFrame.type==='pair-result'?(searchFrame.status==='valid'?'1-corona filled':searchFrame.status==='invalid'?'1-corona failed':'unresolved'):'filling the 1-corona'}`:mode?'One-corona classification':'Pair & one-corona witness',15,23);ctx.fillText(report?.model?'Saved point marking':'Candidate point marking',390,23);
 const specs=shown.length?shown:[learner.roots[0]],placements=specs.map(learner.materialize);
 const entries=specs.map(spec=>model&&$('learn-marks').checked?learner.entries(spec,activeMarkingSupport(model)):[]);
 const map=mapFor(mode&&searchBounds?searchBounds:[...placements.flatMap(p=>p.loop),...entries.flat().flatMap(markingSegmentEndpoints)],{x:0,y:35,w:370,h:315});
 for(const [i,p] of placements.entries())polygon(p.loop,map,p.tile==='hat'?(i<2?'#ecd1ad':'#f6e8d4'):(i<2?'#bad9d2':'#deece7'),i<2);
 if(mode&&searchFrame){
  const pair=[searchFrame.root,searchFrame.attachment],sums=new Map();
  for(const p of placements)for(const e of p.orientation.occupancy.values()){const point=e.point.map((v,i)=>v+p.translation[i]),key=point.join();sums.set(key,(sums.get(key)||0)+e.weight);}
  for(const point of learner.corePoints(pair)){const q=map(point),complete=sums.get(point.join())===12;ctx.beginPath();ctx.arc(...q,2.5,0,2*Math.PI);ctx.fillStyle=complete?'#27806b':'#d69a30';ctx.fill();}
  if((searchFrame.type==='fail'||searchFrame.type==='pair-result'&&searchFrame.status==='invalid')&&searchFrame.choice){const point=Array.isArray(searchFrame.choice)?searchFrame.choice:searchFrame.choice.split(',').map(Number);ctx.beginPath();ctx.arc(...map(point),6,0,2*Math.PI);ctx.strokeStyle='#b5403d';ctx.lineWidth=2;ctx.stroke();}
 }
 // Draw markings after every fill, including exterior marks crossing a neighbor.
 for(const values of entries)marks(values,map);
 const row=!mode&&report?.connections[+picker.value];
 const witness=row&&model?learner.verifyPatch([row.root,row.attachment],activeMarkingSupport(model)).witness:null;
 if(witness&&$('learn-marks').checked){const q=map(witness.point);ctx.strokeStyle='#b5403d';ctx.lineWidth=2;ctx.beginPath();ctx.arc(...q,6,0,2*Math.PI);ctx.stroke();ctx.fillStyle='#b5403d';ctx.fillText(`${witness.values[0]} ≠ ${witness.values[1]}`,Math.min(q[0]+8,310),q[1]-8);}
 for(const [i,tile] of learner.config.tiles.entries()){const root=learner.roots[i],p=learner.materialize(root),n=learner.config.tiles.length,box={x:390,y:32+i*310/n,w:310,h:310/n},tileMarks=model?activeMarkingSupport(model).filter(e=>e.tile===tile):[],m=mapFor([...p.loop,...learner.pointDomain(tile),...tileMarks.flatMap(markingSegmentEndpoints)],box);polygon(p.loop,m,tile==='hat'?'#ecd1ad':'#bad9d2');if(model&&$('learn-marks').checked)marks(tileMarks,m);ctx.fillStyle='#486656';ctx.font='12px system-ui';ctx.fillText(tile,box.x,box.y+18);}
 ctx.strokeStyle='#e1e7df';ctx.beginPath();ctx.moveTo(380,35);ctx.lineTo(380,348);ctx.stroke();
}
function finish(completed=false){clearTimeout(frameTimer);frameTimer=null;searchFrame=null;searchBounds=null;if(mode==='collect'&&!completed)automaticStarts.delete(runningSetId);runningSetId=null;worker?.terminate();worker=null;mode=null;paused=false;$('learn-start').disabled=false;$('learn-start').textContent='Classify & learn';$('learn-deeper').textContent='Retry unresolved';picker.disabled=!report;$('learn-export').disabled=!report;$('learn-deeper').disabled=!report||report.connections[+picker.value]?.status!=='unresolved';}
function describe(){const row=report?.connections[+picker.value];if(!row)return;
 const actual=row.status==='valid'?'Valid: complete one-corona witness':row.status==='invalid'?'Invalid: one-corona search exhausted':'Unresolved: search budget reached';
 const c=report.classification,prediction=row.predicted?` · marking ${row.predicted==='valid'?'accepts':'rejects'} this pair${row.status==='unresolved'?'':row.predicted===row.status?' (correct)':' (incorrect)'}`:'';
 message(`${actual}${prediction}. Classification: ${c.correct}/${c.total} correct (${(100*c.correct/c.total).toFixed(1)}%). Accepts ${c.validAccepted}/${c.valid} valid pairs; blocks ${c.invalidBlocked}/${c.invalid} invalid pairs (${(100*c.invalidBlocked/Math.max(1,c.invalid)).toFixed(1)}%). ${c.accepted?'Marking saved.':'Not saved: resolve all pairs, accept every valid pair, and block more than half of invalid pairs.'}`);
 $('learn-deeper').disabled=!!mode||row.status!=='unresolved';
}
function install(data,index=0,completed=false){
 if(data.setId!==setId||(data.lattice??'A2')!==lattice||data.criterion!==CORONA_CRITERION)throw new Error('Outdated learning evidence');
 if(data.model)learner.validateModel(data.model);
 const candidate=data.model??data.candidateModel;
 if(candidate)learner.validateCandidate(candidate);
 model=candidate?(candidate.reduction?.preserveInterior?candidate:reduceMarking(candidate,{preserveInterior:true})):null;
 let persisted=false;
 if(data.model){const saved=rememberMarking({...model,trainingSettings:data.settings});model=saved.model;persisted=saved.persisted;data={...data,model};}else data={...data,candidateModel:model};
 report=data;reports.set(learningKey(),data);
 picker.replaceChildren(...data.connections.map((row,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${i+1} · ${row.root.tile}–${row.attachment.tile} · ${row.status==='valid'?'1-corona valid':row.status}`;return o;}));picker.value=index;shown=data.connections[index]?.placements||[];
 $('learn-metrics').textContent=`${TILE_SETS[setId].label} · ${data.connections.length} pairs · ${data.counts.valid} valid · ${data.counts.invalid} invalid · ${data.counts.unresolved} unresolved`;
 finish(true);describe();draw();
 if(data.model){
  $('learn-sync').textContent=`${persisted?'Saved':'Available this visit; browser storage could not save it'}: ${model.marking.name}.${model.marking.sameValuesAs?` Same values as ${model.marking.sameValuesAs.name}.`:''}${embedded?' Available in Tiling; successful training starts it automatically.':''}`;
  if(!embedded)sessionStorage.setItem('gcts-requested-marking',JSON.stringify(model));
  send('gcts-marking-ready',{model,counts:data.counts,completed});
 }else{
  $('learn-sync').textContent='Candidate only — no marking saved or transferred.';
  if(!embedded)sessionStorage.removeItem('gcts-requested-marking');
 }
}
function reset(){$('learn-sync').textContent='';epoch++;finish();report=null;model=null;shown=[];picker.replaceChildren();picker.disabled=true;$('learn-deeper').disabled=true;$('learn-export').disabled=true;$('learn-metrics').textContent=`${TILE_SETS[setId].label} · 0 pairs`;message('Classify every second-tile placement using a complete one-corona check, then train the marking.');draw();}
function choose(id,nextLattice=lattice){if(!TILE_SETS[id])return;setId=id;lattice=nextLattice;learner=createConnectionLearner(id,{lattice});$('learn-sublattice').checked=lattice==='turtle-sublattice';selectTiles(id);reset();
 if(reports.has(learningKey()))install(reports.get(learningKey()));
}
function launch(kind){$('learn-sync').textContent='Save when every valid pair passes and most invalid pairs are blocked, with none unresolved.';epoch++;worker?.terminate();worker=new Worker(new URL('./tile-learning-worker.js?v=20260921-corona-animation',import.meta.url),{type:'module'});const active=worker;mode=kind;runningSetId=learningKey();paused=false;
 $('learn-start').disabled=kind!=='collect';$('learn-deeper').disabled=kind!=='extend';$('learn-export').disabled=true;picker.disabled=true;
 searchFrame=null;searchBounds=null;clearTimeout(frameTimer);
 if(kind==='collect'){automaticStarts.add(learningKey());$('learn-start').textContent='Pause learning';report=null;model=null;shown=[];picker.replaceChildren();message('Enumerating all second-tile placements and checking each one-corona…');}else $('learn-deeper').textContent='Pause search';
 worker.onmessage=({data})=>{if(worker!==active)return;
  if(data.type==='search-frame'){
   searchFrame=data.event;shown=searchFrame.placements;
   if(searchFrame.type==='pair-start'){
    const loops=[searchFrame.root,searchFrame.attachment].flatMap(p=>learner.materialize(p).loop);
    const radius=Math.max(...learner.orientations.flatMap(o=>[0,1,2].map(i=>Math.max(...o.loop.map(p=>p[i]))-Math.min(...o.loop.map(p=>p[i])))));
    const steps=[[0,0,0],[1,-1,0],[1,0,-1],[0,1,-1],[-1,1,0],[-1,0,1],[0,-1,1]];
    searchBounds=loops.flatMap(p=>steps.map(d=>p.map((v,i)=>v+radius*d[i])));
   }
   const action=searchFrame.type==='pair-result'?(searchFrame.status==='valid'?'Succeeded: the 1-corona is filled.':searchFrame.status==='invalid'?'Failed: no complete 1-corona exists for this pair.':'Unresolved: search budget reached.'):{'pair-start':'Trying to fill the 1-corona…',placement:'Placed a tile.',backtrack:'Backtracking: removed a tile.',fail:'Dead end: trying another branch.'}[searchFrame.type];
   message(`Pair ${searchFrame.index+1} · ${action} ${searchFrame.nodes} attempts · ${searchFrame.backtracks} backtracks. Gold points still need filling; green points are complete.`);draw();
   const delay=+$('learn-speed').value*(searchFrame.type==='pair-result'?4:1);
   frameTimer=setTimeout(()=>{if(worker===active)active.postMessage({type:'frame-shown',id:data.id});},delay);
  }
  else if(data.type==='progress'){const c=data.counts;$('learn-metrics').textContent=`${TILE_SETS[setId].label} · ${data.attempts} pairs · ${c.valid} valid · ${c.invalid} invalid · ${c.unresolved} unresolved`;if(data.phase==='train'){searchFrame=null;searchBounds=null;shown=data.latest;model=data.model;message('Training a marking on all classified pairs…');draw();}}
  else if(data.type==='collected')install(data.report,0,true);
  else if(data.type==='extended')install(learner.incorporate(report,data.index,data.row),data.index,true);
  else if(data.type==='error'){finish();message(data.message);}
 };
 worker.onerror=()=>{if(worker===active){finish();message('Learning worker could not run. Reload to retry.');}};
 if(kind==='collect'){const budget=Math.max(1,Math.min(1000000,Math.round(+$('learn-budget').value||5000)));worker.postMessage({type:kind,setId,lattice,seed:90210,budget});}
 else{const index=+picker.value,row=report.connections[index],last=row.lastAttempt||row;worker.postMessage({type:kind,setId,lattice,index,root:row.root,attachment:row.attachment,seed:1090213,budget:last.budget*4});}
 draw();
}
function pause(button){paused=!paused;worker.postMessage({type:paused?'pause':'resume'});button.textContent=paused?'Continue':mode==='collect'?'Pause learning':'Pause search';}
$('learn-start').onclick=()=>mode==='collect'?pause($('learn-start')):launch('collect');$('learn-deeper').onclick=()=>mode==='extend'?pause($('learn-deeper')):launch('extend');
$('learn-reset').onclick=reset;$('learn-marks').onchange=draw;picker.onchange=()=>{shown=report.connections[+picker.value]?.placements||[];describe();draw();};tileSetInputs.forEach(input=>input.addEventListener('change',()=>{if(input.checked)choose(input.value);}));
$('learn-sublattice').onchange=()=>{choose(setId,$('learn-sublattice').checked?'turtle-sublattice':'A2');send('gcts-learning-lattice');launch('collect');};
$('learn-export').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify({...report,markingMetadata:markingMetadata(model)},null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=`${setId}-${model?.marking?.id??'candidate'}-connection-evidence.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
window.addEventListener('message',e=>{
 if(e.origin!==location.origin||e.source!==parent)return;
 const data=e.data;
 const nextLattice=data?.lattice??lattice;
 if(data?.type==='gcts-select-tiles'&&(data.setId!==setId||nextLattice!==lattice))choose(data.setId,nextLattice);
 if(data?.type==='gcts-start-learning'&&TILE_SETS[data.setId]){
  const key=`${data.setId}:${nextLattice}`;
  if(automaticStarts.has(key)){if(data.setId!==setId||nextLattice!==lattice)choose(data.setId,nextLattice);return;}
  choose(data.setId,nextLattice);launch('collect');
 }
});
choose(new URLSearchParams(location.search).get('set')||'turtle');send('gcts-learner-loaded');
