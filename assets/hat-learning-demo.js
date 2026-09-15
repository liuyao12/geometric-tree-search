import {HAT,materialize,pointDomain} from './hat-local-learning.js';
import {a2Transform,a2Add} from './a2-tiling-engine.js';
const $=id=>document.getElementById(id),canvas=$('hat-learning-canvas'),ctx=canvas.getContext('2d');
const collectButton=$('hat-collect'),compareButton=$('hat-compare'),exportButton=$('hat-export'),picker=$('hat-patch');
let report=null,model=null,samples=[],shown=[],growth=[],variant=null,worker=null,mode=null,paused=false,loadEpoch=0;
const project=([x,y,z])=>[(z-x)/Math.sqrt(2),(2*y-x-z)/Math.sqrt(6)];
function view(points,box){const pts=points.map(project),xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys);const scale=Math.min((box.w-32)/Math.max(1,maxx-minx),(box.h-40)/Math.max(1,maxy-miny));return p=>{const q=project(p);return[box.x+box.w/2+(q[0]-(minx+maxx)/2)*scale,box.y+box.h/2+(q[1]-(miny+maxy)/2)*scale];};}
function polygon(points,map,fill){ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(...map(p)):ctx.moveTo(...map(p)));ctx.closePath();ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle='#50796f';ctx.lineWidth=1;ctx.stroke();}
function mark(entries,map){for(const e of entries){const q=map(e.point),d=[1,1,1];d[e.component]=-2;const tip=map(e.point.map((v,i)=>v+.25*d[i]));ctx.strokeStyle=e.value===0?'#aebbb366':`hsl(${(Math.abs(e.value)*137.5)%360} 60% 38%)`;ctx.lineWidth=e.value===0?.65:1.7;ctx.setLineDash(e.value<0?[2,2]:[]);ctx.beginPath();ctx.moveTo(...q);ctx.lineTo(...tip);ctx.stroke();}ctx.setLineDash([]);}
function drawPatch(specs,box,withMarks){const patches=specs.map(materialize),map=view(patches.flatMap(p=>p.loop),box);for(const p of patches){const perm=p.orientation.symmetry.permutation,sign=((perm[0]>perm[1])+(perm[0]>perm[2])+(perm[1]>perm[2]))%2?-1:1;polygon(p.loop,map,sign<0?'#efceb1':'#c2dcd5');if(withMarks&&model)mark(model.support.map(e=>({point:a2Add(a2Transform(e.point,p.orientation.symmetry),p.translation),component:perm.indexOf(e.component),value:e.value*sign})),map);}}
function draw(){ctx.clearRect(0,0,720,400);ctx.fillStyle='#fafbf7';ctx.fillRect(0,0,720,400);ctx.fillStyle='#294d43';ctx.font='15px system-ui';ctx.fillText(mode==='collect'?'Exploring local Hat patches':'Collected local patch',18,25);ctx.fillText(growth.length?(variant==='baseline'?'Fresh search · unmarked':'Fresh search · learned hypothesis'):'Learned point encoding',374,25);ctx.strokeStyle='#e1e6df';ctx.beginPath();ctx.moveTo(356,42);ctx.lineTo(356,382);ctx.stroke();const marks=$('hat-show-marks').checked;
 if(shown.length)drawPatch(shown,{x:0,y:38,w:352,h:350},marks);else drawPatch([{orientation:0,translation:[0,0,0]}],{x:0,y:38,w:352,h:350},false);
 if(growth.length)drawPatch(growth,{x:366,y:38,w:354,h:350},marks&&variant==='marked');else{const map=view([...HAT.loop,...pointDomain()],{x:366,y:38,w:354,h:350});polygon(HAT.loop,map,'#e6efdf');if(model&&marks)mark(model.support,map);else{ctx.fillStyle='#65766d';ctx.font='13px system-ui';ctx.fillText('No supplied Hat marking',444,375);}}
}
function message(text){$('hat-learning-status').textContent=text;}
function finish(){worker?.terminate();worker=null;mode=null;paused=false;collectButton.disabled=false;collectButton.textContent='Collect & learn';compareButton.disabled=!report;compareButton.textContent='Test new growth';exportButton.disabled=!report;}
function reset(){loadEpoch++;finish();report=null;model=null;samples=[];shown=[];growth=[];variant=null;picker.replaceChildren();picker.disabled=true;compareButton.disabled=true;exportButton.disabled=true;$('hat-learning-metrics').textContent='Unmarked Hat searches → overlap equations → point codes';message('Collect distinct local patches; learn a marking and check held-out patches.');draw();}
function install(data,recorded=false){report=data;model=data.model;samples=[...data.training,...data.test];picker.replaceChildren(...samples.map((s,i)=>{const option=document.createElement('option');option.value=i;option.textContent=i<data.training.length?`Training patch ${i+1}`:`Held-out patch ${i-data.training.length+1} · ${s.evaluation.compatible?'passes':'conflict'}`;return option;}));picker.disabled=!samples.length;shown=samples[0]?.placements||[];growth=[];variant=null;
 $('hat-learning-metrics').textContent=`${recorded?'Recorded run · ':''}${data.training.length} training patches · ${data.testPassed}/${data.test.length} held-out patches pass · ${model.classes} equality classes`;
 message(`${model.support.length} point/channel values · ${data.attachmentCount-data.attachmentSurvivors}/${data.attachmentCount} initial attachments excluded by the hypothesis`);finish();draw();}
function launch(kind){loadEpoch++;worker?.terminate();worker=new Worker(new URL('./hat-learning-worker.js',import.meta.url),{type:'module'});const active=worker;mode=kind;paused=false;
 collectButton.disabled=kind!=='collect';compareButton.disabled=kind!=='compare';exportButton.disabled=true;
 if(kind==='collect'){report=null;samples=[];model=null;shown=[];growth=[];variant=null;picker.replaceChildren();picker.disabled=true;collectButton.textContent='Pause collection';message('Enumerating all legal two-Hat attachments…');}
 else{growth=[];variant=null;compareButton.textContent='Pause test';message('Comparing fresh unmarked and marked searches with the same target and node budget…');}
 worker.onmessage=({data})=>{if(worker!==active)return;
  if(data.type==='progress'){model=data.model;shown=data.latest;$('hat-learning-metrics').textContent=`${data.attempts}/${data.total} attachment trials · ${data.training}/16 training · ${data.test}/8 held out`;message(`${data.duplicates} duplicate patches discarded · ${model?.classes??0} equality classes`);draw();}
  else if(data.type==='collected')install(data.report);
  else if(data.type==='growth'){growth=data.placements;variant=data.variant;message(`${variant==='baseline'?'Unmarked':'Marked hypothesis'}: ${growth.length} Hats · ${data.nodes} attempts · ${data.backtracks} backtracks`);draw();}
  else if(data.type==='compared'){report.evaluations??=[];report.evaluations.push(data.result);const {seed,baseline,marked}=data.result;growth=marked.placements;variant='marked';message(`Fresh seed ${seed}: unmarked ${baseline.placements.length} tiles / ${baseline.nodes} attempts; marked ${marked.placements.length} tiles / ${marked.nodes} attempts. Finite patches; no speedup claim.`);finish();draw();}
  else if(data.type==='error'){message(data.message);finish();}
 };
 worker.onerror=()=>{if(worker!==active)return;message('The Hat worker could not run. Reload and try again.');finish();};
 worker.postMessage(kind==='collect'?{type:'collect',seed:+$('hat-seed').value||90210}:{type:'compare',seed:(+$('hat-seed').value||90210)+1000003,support:model.support});draw();
}
function togglePause(button,text){paused=!paused;worker.postMessage({type:paused?'pause':'resume'});button.textContent=paused?`Continue ${text}`:`Pause ${text}`;}
collectButton.addEventListener('click',()=>mode==='collect'?togglePause(collectButton,'collection'):launch('collect'));
compareButton.addEventListener('click',()=>mode==='compare'?togglePause(compareButton,'test'):launch('compare'));
$('hat-reset').addEventListener('click',reset);$('hat-show-marks').addEventListener('change',draw);picker.addEventListener('change',()=>{shown=samples[+picker.value]?.placements||[];draw();});
$('hat-seed').addEventListener('change',()=>{$('hat-seed').value=Math.max(1,Math.min(1000000,Math.round(+$('hat-seed').value||90210)));});
exportButton.addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='hat-local-patch-learning.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
$('learning-kind').addEventListener('change',()=>{const hat=$('learning-kind').value==='hat';$('hat-learning-panel').hidden=!hat;$('anchor-lane').hidden=hat;if(!hat&&worker)reset();if(hat)$('anchor-reset').click();window.dispatchEvent(new Event('resize'));});
reset();const epoch=loadEpoch;
fetch(new URL('./data/hat-local-patches.json',import.meta.url)).then(r=>{if(!r.ok)throw new Error();return r.json();}).then(data=>{if(loadEpoch===epoch)install(data,true);}).catch(()=>{if(loadEpoch===epoch)message('Collect a new run to learn from local Hat patches.');});
