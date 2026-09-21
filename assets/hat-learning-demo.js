import {HAT,materialize,pointDomain,incorporate} from './hat-local-learning.js?v=20260915-constraints';
import {a2Transform,a2Add} from './a2-tiling-engine.js?v=20260915-constraints';
const $=id=>document.getElementById(id),canvas=$('hat-learning-canvas'),ctx=canvas.getContext('2d');
const collectButton=$('hat-collect'),compareButton=$('hat-compare'),exportButton=$('hat-export'),picker=$('hat-patch');
let report=null,model=null,samples=[],shown=[],growth=[],worker=null,mode=null,paused=false,loadEpoch=0;
const project=([x,y,z])=>[(z-x)/Math.sqrt(2),(2*y-x-z)/Math.sqrt(6)];
function view(points,box){const pts=points.map(project),xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys);const scale=Math.min((box.w-32)/Math.max(1,maxx-minx),(box.h-40)/Math.max(1,maxy-miny));return p=>{const q=project(p);return[box.x+box.w/2+(q[0]-(minx+maxx)/2)*scale,box.y+box.h/2+(q[1]-(miny+maxy)/2)*scale];};}
function polygon(points,map,fill){ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(...map(p)):ctx.moveTo(...map(p)));ctx.closePath();ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle='#50796f';ctx.lineWidth=1;ctx.stroke();}
function mark(entries,map){for(const e of entries){const q=map(e.point),d=[1,1,1];d[e.component]=-2;const tip=map(e.point.map((v,i)=>v+.25*d[i]));ctx.strokeStyle=e.value===0?'#aebbb366':`hsl(${(Math.abs(e.value)*137.5)%360} 60% 38%)`;ctx.lineWidth=e.value===0?.65:1.7;ctx.setLineDash(e.value<0?[2,2]:[]);ctx.beginPath();ctx.moveTo(...q);ctx.lineTo(...tip);ctx.stroke();}ctx.setLineDash([]);}
function drawPatch(specs,box,withMarks,witness=null){const patches=specs.map(materialize),map=view(patches.flatMap(p=>p.loop),box);for(const p of patches){const perm=p.orientation.symmetry.permutation,sign=((perm[0]>perm[1])+(perm[0]>perm[2])+(perm[1]>perm[2]))%2?-1:1;polygon(p.loop,map,sign<0?'#efceb1':'#c2dcd5');if(withMarks&&model)mark(model.support.map(e=>({point:a2Add(a2Transform(e.point,p.orientation.symmetry),p.translation),component:perm.indexOf(e.component),value:e.value*sign})),map);}if(witness){const q=map(witness.point);ctx.strokeStyle="#b43a37";ctx.lineWidth=2;ctx.beginPath();ctx.arc(...q,7,0,2*Math.PI);ctx.stroke();ctx.fillStyle="#b43a37";ctx.font="13px system-ui";ctx.fillText(`${witness.values[0]} ≠ ${witness.values[1]}`,Math.min(280,q[0]+10),q[1]-9);}}
function draw(){ctx.clearRect(0,0,720,400);ctx.fillStyle='#fafbf7';ctx.fillRect(0,0,720,400);ctx.fillStyle='#294d43';ctx.font='15px system-ui';ctx.fillText(mode==='collect'?'Examining connections':mode==='extend'?'Searching the selected connection':'Connection & local extension',18,25);ctx.fillText('Proposed geometric point codes',374,25);ctx.strokeStyle='#e1e6df';ctx.beginPath();ctx.moveTo(356,42);ctx.lineTo(356,382);ctx.stroke();const marks=$('hat-show-marks').checked;
 if(growth.length||shown.length)drawPatch(growth.length?growth:shown,{x:0,y:38,w:352,h:330},marks,!mode&&marks?samples[+picker.value]?.codeWitness:null);else drawPatch([{orientation:0,translation:[0,0,0]}],{x:0,y:38,w:352,h:350},false);
 {const map=view([...HAT.loop,...pointDomain()],{x:366,y:38,w:354,h:350});polygon(HAT.loop,map,'#e6efdf');if(model&&marks)mark(model.support,map);else{ctx.fillStyle='#65766d';ctx.font='13px system-ui';ctx.fillText('No supplied Hat marking',444,375);}}
}
function message(text){$('hat-learning-status').textContent=text;}
function finish(){worker?.terminate();worker=null;mode=null;paused=false;collectButton.disabled=false;collectButton.textContent='Examine all connections';compareButton.disabled=!report||samples[+picker.value]?.status==='dead';compareButton.textContent='Search farther';exportButton.disabled=!report;picker.disabled=!samples.length;}
function reset(){loadEpoch++;finish();report=null;model=null;samples=[];shown=[];growth=[];picker.replaceChildren();picker.disabled=true;compareButton.disabled=true;exportButton.disabled=true;$('hat-learning-metrics').textContent='Connections → extensions & dead ends → point codes';message('Examine every legal two-Hat attachment. All evidence contributes.');draw();}
function describe(){
 const row=samples[+picker.value];if(!row)return;
 const code=!model?'No point encoding yet':row.codeConflict?'Point codes separate this pair':'Point codes agree on this pair';
 const evidence=row.status==='dead'?`Excluded: unmarked search exhausted all alternatives (${row.nodes} attempts).`:row.status==='extended'?`Extended to ${row.placements.length} Hats; infinite extension remains open.`:`Unresolved after ${row.budget} attempts; retained.`;
 const latest=row.lastAttempt?.status==='unresolved'?` Deeper search reached its budget at target ${row.lastAttempt.target}; earlier evidence retained.`:'';
 message(`${evidence} ${code}.${latest} ${report.encoding.deadSeparated}/${report.counts.dead} failures encoded; ${report.encoding.deadUnseparated} remain unseparated.${report.encoding.unresolvedRejected?` ${report.encoding.unresolvedRejected} unresolved code conflicts remain unproved.`:''}`);
 compareButton.disabled=!!mode||row.status==='dead';
}
function install(data,recorded=false,index=0){report=data;model=data.model;samples=data.connections;picker.replaceChildren(...samples.map((s,i)=>{const option=document.createElement('option');option.value=i;option.textContent=`${i+1} · ${s.status==='extended'?`extended to ${s.placements.length} Hats`:s.status==='dead'?'dead · excluded':'unresolved · retained'}`;return option;}));picker.value=String(index);shown=samples[index]?.placements||[];growth=[];
 const c=data.counts;$('hat-learning-metrics').textContent=`${recorded?'Recorded run · ':''}${data.attachmentCount} connections · ${c.extended} extended · ${c.dead} dead · ${c.unresolved} unresolved · ${data.samples.length} distinct patches`;
 finish();describe();draw();}
function launch(kind){loadEpoch++;worker?.terminate();worker=new Worker(new URL('./hat-learning-worker.js?v=20260915-constraints',import.meta.url),{type:'module'});const active=worker;mode=kind;paused=false;
 collectButton.disabled=kind!=='collect';compareButton.disabled=kind!=='extend';exportButton.disabled=true;picker.disabled=true;
 if(kind==='collect'){report=null;samples=[];model=null;shown=[];growth=[];picker.replaceChildren();collectButton.textContent='Pause collection';message('Enumerating all legal two-Hat connections…');}
 else{growth=[];compareButton.textContent='Pause search';message('Searching farther with the same two Hats fixed. Every outcome returns to the evidence.');}
 worker.onmessage=({data})=>{if(worker!==active)return;
  if(data.type==='progress'){shown=data.latest;model=data.model;const c=data.counts;$('hat-learning-metrics').textContent=`${data.attempts}/${data.total} connections · ${c.extended} extended · ${c.dead} dead · ${c.unresolved} unresolved`;message('Unmarked search · all connections examined · budget limits stay unresolved');draw();}
  else if(data.type==='collected')install(data.report);
  else if(data.type==='growth'){growth=data.placements;message(`Extending the fixed connection: ${growth.length} Hats · ${data.nodes} attempts · ${data.backtracks} backtracks`);draw();}
  else if(data.type==='extended')install(incorporate(report,data.index,data.row),false,data.index);
  else if(data.type==='error'){message(data.message);finish();}
 };
 worker.onerror=()=>{if(worker!==active)return;message('The Hat worker could not run. Reload and try again.');finish();};
 if(kind==='collect')worker.postMessage({type:'collect',seed:+$('hat-seed').value||90210});
 else{const index=+picker.value,row=samples[index],last=row.lastAttempt||row;worker.postMessage({type:'extend',index,attachment:row.attachment,seed:(+$('hat-seed').value||90210)+1000003,target:Math.max(24,last.target*2),budget:last.budget*4});}
 draw();
}
function togglePause(button,text){paused=!paused;worker.postMessage({type:paused?'pause':'resume'});button.textContent=paused?`Continue ${text}`:`Pause ${text}`;}
collectButton.addEventListener('click',()=>mode==='collect'?togglePause(collectButton,'collection'):launch('collect'));
compareButton.addEventListener('click',()=>mode==='extend'?togglePause(compareButton,'search'):launch('extend'));
$('hat-reset').addEventListener('click',reset);$('hat-show-marks').addEventListener('change',draw);picker.addEventListener('change',()=>{shown=samples[+picker.value]?.placements||[];growth=[];describe();draw();});
$('hat-seed').addEventListener('change',()=>{$('hat-seed').value=Math.max(1,Math.min(1000000,Math.round(+$('hat-seed').value||90210)));});
exportButton.addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='hat-local-patch-learning.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
$('learning-kind').addEventListener('change',()=>{const hat=$('learning-kind').value==='hat';$('hat-learning-panel').hidden=!hat;$('anchor-lane').hidden=hat;if(!hat&&worker)reset();if(hat)$('anchor-reset').click();window.dispatchEvent(new Event('resize'));});
reset();
