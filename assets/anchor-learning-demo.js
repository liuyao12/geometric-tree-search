import {createModel,trainStep,freezeModel,loss,TURTLE,VERSION} from './turtle-point-learning.js';
import {a2Transform,a2Add} from './a2-tiling-engine.js';
const $=id=>document.getElementById(id),canvas=$('anchor-canvas'),ctx=canvas.getContext('2d');
const train=$('anchor-train'),tile=$('anchor-check'),seed=$('anchor-seed');
let model,initial,frozen=null,worker=null,placements=[],result=null,running=false,paused=false,animation=0;
function status(text){$('anchor-result').textContent=text;}
function reset(){cancelAnimationFrame(animation);worker?.terminate();worker=null;running=false;paused=false;frozen=null;result=null;placements=[];model=createModel(+seed.value||7);initial=structuredClone(model);train.textContent='Train Turtle';tile.textContent='Tile with learned marking';tile.disabled=true;$('anchor-export').disabled=true;status('Fit the known Turtle point data, then grow a patch.');draw();}
const project=([x,y,z])=>[(z-x)/Math.sqrt(2),(2*y-x-z)/Math.sqrt(6)];
function viewport(points,box){const pts=points.map(project),xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);const minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys);const scale=Math.min((box.w-36)/Math.max(1,maxx-minx),(box.h-45)/Math.max(1,maxy-miny));return point=>{const p=project(point);return[box.x+box.w/2+(p[0]-(minx+maxx)/2)*scale,box.y+box.h/2+(p[1]-(miny+maxy)/2)*scale];};}
function polygon(points,map,color){ctx.beginPath();points.forEach((p,i)=>{const q=map(p);i?ctx.lineTo(...q):ctx.moveTo(...q);});ctx.closePath();ctx.fillStyle=color;ctx.fill();ctx.strokeStyle='#3c716c';ctx.lineWidth=1;ctx.stroke();}
function marks(entries,map,alpha=1){for(const e of entries){if(Math.abs(e.value)<.05)continue;const direction=[1,1,1];direction[e.component]=-2;const d=.48;const a=map(e.point.map((v,i)=>v-d*direction[i])),b=map(e.point.map((v,i)=>v+d*direction[i]));ctx.globalAlpha=alpha*Math.min(1,Math.abs(e.value));ctx.strokeStyle=e.value>0?'#bb6936':'#267dab';ctx.lineWidth=1.6;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();}ctx.globalAlpha=1;}
function draw(){ctx.clearRect(0,0,720,400);ctx.fillStyle='#fafbf7';ctx.fillRect(0,0,720,400);ctx.font='15px system-ui';ctx.fillStyle='#294d43';ctx.fillText('Training the Turtle',18,25);ctx.fillText('Tiling with the learned marking',374,25);ctx.strokeStyle='#e0e5dc';ctx.beginPath();ctx.moveTo(356,42);ctx.lineTo(356,383);ctx.stroke();
 const map=viewport([...initial.anchors.map(a=>a.point),...TURTLE.loop],{x:0,y:38,w:352,h:350});polygon(TURTLE.loop,map,'#e5efdf');
 for(const a of model.anchors){if(!a.target.occupied)continue;const p=map(a.point);ctx.fillStyle='#53756c';ctx.globalAlpha=.25+.6*a.t;ctx.beginPath();ctx.arc(...p,1.2+2.5*a.t,0,2*Math.PI);ctx.fill();}ctx.globalAlpha=1;
 if($('anchor-marks').checked)marks(model.anchors.flatMap(a=>a.m.flatMap((value,component)=>value===null?[]:[{point:a.point,component,value}])),map);
 if(placements.length){const view=viewport(placements.flatMap(p=>p.loop),{x:366,y:38,w:354,h:350});for(const p of placements){const perm=p.orientation.symmetry.permutation,sign=((perm[0]>perm[1])+(perm[0]>perm[2])+(perm[1]>perm[2]))%2?-1:1;polygon(p.loop,view,sign<0?'#edcaa6':'#c4dedc');if($('anchor-marks').checked)marks(frozen.support.map(e=>({point:a2Add(a2Transform(e.point,p.orientation.symmetry),p.translation),component:perm.indexOf(e.component),value:sign*e.value})),view,.8);}}
 else{const view=viewport(TURTLE.loop,{x:390,y:85,w:300,h:245});polygon(TURTLE.loop,view,'#eff3eb');ctx.fillStyle='#63746b';ctx.font='13px system-ui';ctx.fillText(frozen?'Ready to tile':'Train to unlock tiling',464,357);}
 $('anchor-metrics').textContent=`Step ${model.step}/120 · fitting loss ${loss(model).toExponential(2)} · ${model.anchors.length} anchors`;
}
function tick(){if(!running)return;trainStep(model);draw();if(model.step>=120){running=false;train.textContent='Train again';try{frozen=freezeModel(model);tile.disabled=false;status('Turtle fitted. Ready to tile with the learned marking.');}catch(e){status(e.message);}return;}animation=requestAnimationFrame(tick);}
train.addEventListener('click',()=>{if(running){running=false;cancelAnimationFrame(animation);train.textContent='Resume training';return;}if(frozen||worker)reset();running=true;train.textContent='Pause training';status('Fitting known Turtle anchors, t-values and m-values…');animation=requestAnimationFrame(tick);});
tile.addEventListener('click',()=>{
 if(worker){paused=!paused;worker.postMessage({type:paused?'pause':'resume'});tile.textContent=paused?'Continue tiling':'Pause tiling';return;}
 if(!frozen)return;
 result=null;$('anchor-export').disabled=true;placements=[];paused=false;tile.textContent='Pause tiling';status('Growing a Turtle patch…');
 worker=new Worker(new URL('./turtle-learning-worker.js',import.meta.url),{type:'module'});
 const activeWorker=worker;
 worker.onmessage=({data})=>{if(worker!==activeWorker)return;if(data.type==='error'){status(data.message);worker?.terminate();worker=null;tile.textContent='Try tiling again';return;}
 placements=data.placements??placements;
 if(data.type==='frame')status(`${placements.length} Turtles · ${data.forced} forced moves · ${data.branches} branches · ${data.backtracks} backtracks`);
 if(data.type==='done'){result=data;status(`${data.verification.label}: ${placements.length} tiles · ${data.verification.completePoints} complete points · ${data.verification.frontierPoints} open frontier points${data.result==='unknown'?' · search limit reached':data.result==='no'?' · no continuation found':''}`);worker?.terminate();worker=null;tile.textContent='Tile again';$('anchor-export').disabled=false;}
 draw();};
 worker.onerror=()=>{if(worker!==activeWorker)return;status('The Turtle search could not start. Reload and try again.');worker?.terminate();worker=null;tile.textContent='Try tiling again';};worker.postMessage({type:'start',frozen});
});
$('anchor-reset').addEventListener('click',reset);$('anchor-marks').addEventListener('change',draw);seed.addEventListener('change',()=>{seed.value=Math.max(1,Math.min(9999,Math.round(+seed.value||7)));reset();});
$('anchor-export').addEventListener('click',()=>{const data={version:VERSION,training:'Supervised fit to the known Turtle point data and rank-3 marking',model,frozen,result};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='turtle-training-and-tiling.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
reset();
