import {reduceMarking,activeMarkingSupport} from './marking-reduction.js?v=20260920-compact';
import {markingSegmentEndpoints} from './marking-segments.js?v=20260920-centered';
import {markingMetadata,markingMetadataText} from './marking-metadata.js?v=20260920-compact';
import {createConnectionLearner,TILE_SETS} from './tile-connection-learning.js?v=20260920-compact';
const $=id=>document.getElementById(id),canvas=$('learn-canvas'),ctx=canvas.getContext('2d'),picker=$('learn-connection');
const tileSetInputs=Array.from(document.querySelectorAll('input[name="learning-tiles"]'));
const selectTiles=id=>tileSetInputs.forEach(input=>{input.checked=input.value===id;});
const embedded=window.parent!==window;if(embedded)document.body.classList.add('embedded');
let setId='turtle',learner=createConnectionLearner(setId),report=null,model=null,shown=[],worker=null,mode=null,paused=false,epoch=0;
const reports=new Map(),recordedReports=new Map(),automaticStarts=new Set();
const send=(type,data={})=>{if(embedded)parent.postMessage({type,setId,...data},location.origin);};
const message=t=>$('learn-status').textContent=t;
const project=([x,y,z])=>[(z-x)/Math.sqrt(2),(2*y-x-z)/Math.sqrt(6)];
function mapFor(points,box){const p=points.map(project),xs=p.map(q=>q[0]),ys=p.map(q=>q[1]),minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys),scale=Math.min((box.w-30)/Math.max(1,maxx-minx),(box.h-30)/Math.max(1,maxy-miny));return p=>{const q=project(p);return[box.x+box.w/2+(q[0]-(minx+maxx)/2)*scale,box.y+box.h/2+(q[1]-(miny+maxy)/2)*scale];};}
function polygon(loop,map,fill){ctx.beginPath();loop.forEach((p,i)=>i?ctx.lineTo(...map(p)):ctx.moveTo(...map(p)));ctx.closePath();ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle='#52786b';ctx.lineWidth=1;ctx.stroke();}
function marks(entries,map){for(const e of entries){const [q,tip]=markingSegmentEndpoints(e).map(map);ctx.strokeStyle=e.value===0?'#acb9b355':`hsl(${Math.abs(e.value)*137.5%360} 60% 37%)`;ctx.lineWidth=e.value===0?.6:1.7;ctx.setLineDash(e.value<0?[2,2]:[]);ctx.beginPath();ctx.moveTo(...q);ctx.lineTo(...tip);ctx.stroke();}ctx.setLineDash([]);}
function draw(){$('learn-metadata').textContent=model?markingMetadataText(model):'Marking: collecting evidence…';ctx.fillStyle='#fafbf7';ctx.fillRect(0,0,720,360);ctx.fillStyle='#294d43';ctx.font='14px system-ui';ctx.fillText(mode?'Searching local connections':'Connection & extension',15,23);ctx.fillText('Learned point codes',390,23);
 const specs=shown.length?shown:[learner.roots[0]],placements=specs.map(learner.materialize);
 const entries=specs.map(spec=>model&&$('learn-marks').checked?learner.entries(spec,activeMarkingSupport(model)):[]);
 const map=mapFor([...placements.flatMap(p=>p.loop),...entries.flat().flatMap(markingSegmentEndpoints)],{x:0,y:35,w:370,h:315});
 for(const [i,p] of placements.entries()){polygon(p.loop,map,p.tile==='hat'?'#ecd1ad':'#bad9d2');marks(entries[i],map);}
 const witness=!mode&&report?.connections[+picker.value]?.codeWitness;
 if(witness&&$('learn-marks').checked){const q=map(witness.point);ctx.strokeStyle='#b5403d';ctx.lineWidth=2;ctx.beginPath();ctx.arc(...q,6,0,2*Math.PI);ctx.stroke();ctx.fillStyle='#b5403d';ctx.fillText(`${witness.values[0]} ≠ ${witness.values[1]}`,Math.min(q[0]+8,310),q[1]-8);}
 for(const [i,tile] of learner.config.tiles.entries()){const root=learner.roots[i],p=learner.materialize(root),n=learner.config.tiles.length,box={x:390,y:32+i*310/n,w:310,h:310/n},tileMarks=model?activeMarkingSupport(model).filter(e=>e.tile===tile):[],m=mapFor([...p.loop,...learner.pointDomain(tile),...tileMarks.flatMap(markingSegmentEndpoints)],box);polygon(p.loop,m,tile==='hat'?'#ecd1ad':'#bad9d2');if(model&&$('learn-marks').checked)marks(tileMarks,m);ctx.fillStyle='#486656';ctx.font='12px system-ui';ctx.fillText(tile,box.x,box.y+18);}
 ctx.strokeStyle='#e1e7df';ctx.beginPath();ctx.moveTo(380,35);ctx.lineTo(380,348);ctx.stroke();
}
function finish(){worker?.terminate();worker=null;mode=null;paused=false;$('learn-start').disabled=false;$('learn-start').textContent='Learn markings';$('learn-deeper').textContent='Search farther';picker.disabled=!report;$('learn-export').disabled=!report;$('learn-deeper').disabled=!report||report.connections[+picker.value]?.status==='dead';}
function describe(){const row=report?.connections[+picker.value];if(!row)return;
 message(`${row.status==='dead'?'Excluded after exhaustive unmarked search':row.status==='extended'?`Extended to ${row.placements.length} tiles`:'Unresolved; retained'} · ${report.encoding.deadSeparated}/${report.counts.dead} failures encoded; ${report.encoding.deadUnseparated} remain unseparated.${row.lastAttempt?.status==='unresolved'?' Deeper search reached its budget; earlier evidence retained.':''}`);
 $('learn-deeper').disabled=!!mode||row.status==='dead';
}
function install(data,recorded=false,index=0){if(data.setId!==setId)return;if(data.model){learner.validateModel(data.model);data={...data,model:data.model.reducedSupport?data.model:reduceMarking(data.model)};}report=data;model=data.model;reports.set(setId,data);recordedReports.set(setId,recorded);picker.replaceChildren(...data.connections.map((row,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${i+1} · ${row.root.tile}–${row.attachment.tile} · ${row.status==='extended'?`${row.placements.length} tiles`:row.status}`;return o;}));picker.value=index;shown=data.connections[index]?.placements||[];
 $('learn-metrics').textContent=`${recorded?'Recorded · ':''}${data.attachmentCount} connections · ${data.counts.extended} extended · ${data.counts.dead} dead · ${data.counts.unresolved} unresolved`;
 finish();describe();draw();
 if(model){
  $('learn-sync').textContent=embedded?'Available automatically in the Tiling view.':'Ready in the tiler when you return.';
  if(!embedded)sessionStorage.setItem('gcts-requested-marking',JSON.stringify(model));
  send('gcts-marking-ready',{model,counts:data.counts,recorded});
 }
}
function reset(){$('learn-sync').textContent='';epoch++;finish();report=null;model=null;shown=[];picker.replaceChildren();picker.disabled=true;$('learn-deeper').disabled=true;$('learn-export').disabled=true;$('learn-metrics').textContent=TILE_SETS[setId].label;message('Examine every legal connection; use all extension and failure evidence.');draw();}
async function choose(id){if(!TILE_SETS[id])return;setId=id;learner=createConnectionLearner(id);selectTiles(id);reset();const token=epoch;
 if(reports.has(id)){install(reports.get(id),recordedReports.get(id));return;}
 try{const r=await fetch(`./assets/data/tile-connections-${id}.json?v=20260915-1`);if(!r.ok)throw new Error();const data=await r.json();if(token===epoch)install(data,true);}catch{if(token===epoch)message('Learn markings to collect all connections for this tile set.');}
}
function launch(kind){$('learn-sync').textContent='The result will update the Tiling view automatically.';epoch++;worker?.terminate();worker=new Worker(new URL('./tile-learning-worker.js?v=20260920-compact',import.meta.url),{type:'module'});const active=worker;mode=kind;paused=false;
 $('learn-start').disabled=kind!=='collect';$('learn-deeper').disabled=kind!=='extend';$('learn-export').disabled=true;picker.disabled=true;
 if(kind==='collect'){$('learn-start').textContent='Pause learning';report=null;model=null;shown=[];picker.replaceChildren();message('Enumerating every legal connection…');}else $('learn-deeper').textContent='Pause search';
 worker.onmessage=({data})=>{if(worker!==active)return;
  if(data.type==='progress'){shown=data.latest;model=data.model;const c=data.counts;$('learn-metrics').textContent=`${data.attempts}/${data.total} connections · ${c.extended} extended · ${c.dead} dead · ${c.unresolved} unresolved`;draw();}
  else if(data.type==='collected')install(data.report);
  else if(data.type==='growth'){shown=data.placements;message(`${shown.length} tiles · ${data.nodes} attempts · ${data.backtracks} backtracks`);draw();}
  else if(data.type==='extended')install(learner.incorporate(report,data.index,data.row),false,data.index);
  else if(data.type==='error'){finish();message(data.message);}
 };
 worker.onerror=()=>{if(worker===active){finish();message('Learning worker could not run. Reload to retry.');}};
 if(kind==='collect'){const target=Math.max(3,Math.min(96,Math.round(+$('learn-target').value||12))),budget=Math.max(1,Math.min(100000,Math.round(+$('learn-budget').value||120)));worker.postMessage({type:kind,setId,seed:90210,target,budget});}
 else{const index=+picker.value,row=report.connections[index],last=row.lastAttempt||row;worker.postMessage({type:kind,setId,index,root:row.root,attachment:row.attachment,seed:1090213,target:Math.max(24,last.target*2),budget:last.budget*4});}
 draw();
}
function pause(button){paused=!paused;worker.postMessage({type:paused?'pause':'resume'});button.textContent=paused?'Continue':mode==='collect'?'Pause learning':'Pause search';}
$('learn-start').onclick=()=>mode==='collect'?pause($('learn-start')):launch('collect');$('learn-deeper').onclick=()=>mode==='extend'?pause($('learn-deeper')):launch('extend');
$('learn-reset').onclick=reset;$('learn-marks').onchange=draw;picker.onchange=()=>{shown=report.connections[+picker.value]?.placements||[];describe();draw();};tileSetInputs.forEach(input=>input.addEventListener('change',()=>{if(input.checked)choose(input.value);}));
$('learn-export').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify({...report,markingMetadata:markingMetadata(model)},null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=`${setId}-connection-evidence.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
window.addEventListener('message',e=>{
 if(e.origin!==location.origin||e.source!==parent)return;
 const data=e.data;
 if(data?.type==='gcts-select-tiles'&&data.setId!==setId)choose(data.setId);
 if(data?.type==='gcts-start-learning'&&TILE_SETS[data.setId]&&!automaticStarts.has(data.requestId)){
  automaticStarts.add(data.requestId);
  setId=data.setId;learner=createConnectionLearner(setId);selectTiles(setId);
  reset();launch('collect');
 }
});
choose(new URLSearchParams(location.search).get('set')||'turtle');send('gcts-learner-loaded');
