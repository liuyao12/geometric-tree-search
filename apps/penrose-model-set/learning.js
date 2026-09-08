import {knownPenroseBenchmark} from '../../assets/penrose-known-benchmark.js';
import {extendedBars} from '../../assets/penrose-mixed-markings.js';
import {embedding,cycloAdd,latticeKey} from '../../assets/cyclotomic-five.js';
import {activityText} from './search-status.js';
const $=id=>document.getElementById(id),canvas=$('learningCanvas'),ctx=canvas.getContext('2d');
let worker,state,running=false,busy=false,target=3,view=null,hits=[];
const known=knownPenroseBenchmark({});
const coordinate=p=>{const terms=p.coeff.map((v,i)=>v?`${v}${i?`ζ${i===1?'':`^${i}`}`:''}`:null).filter(Boolean);return `(${terms.join(' + ').replaceAll('+ -','− ')||'0'})${p.denominator===1?'':`/${p.denominator}`}`;};
const keyCoordinate=key=>{if(!key)return'?';const [s,d]=key.split('/');return coordinate({coeff:s.split(',').map(Number),denominator:Number(d)});};
function initialize(){worker?.terminate();state=null;running=false;busy=true;target=3;view=null;$('runLearning').textContent='Run';$('learningStatus').textContent='Initializing';$('pointInfo').textContent='';
 const mode=$('searchMode').value;$('modeInfo').textContent=mode==='learned'?'Starts empty. Learns only from certified impossible pairs.':mode==='plain'?'Geometry, corner capacity, and explicit edge-arrow matching.':'Continuous Ammann checks at extent 2, in addition to the base rules.';
 worker=new Worker(new URL('./learning-worker.js',import.meta.url),{type:'module'});
 worker.onerror=e=>{running=false;busy=false;$('learningStatus').textContent=`Worker error: ${e.message}`;};
 worker.onmessage=({data})=>{busy=false;if(data.error){running=false;$('learningStatus').textContent=data.error;return;}state=data;
  if(data.pausedCorona){running=false;target=data.pausedCorona+2;}if(data.done)running=false;
  $('runLearning').textContent=running?'Pause':data.pausedCorona?'Continue':'Run';
  const activity=activityText(data.activity,keyCoordinate);
  $('learningStatus').textContent=data.pausedCorona?`Pausing at corona ${data.pausedCorona} · ${activity}`:data.done?data.status:activity;
  $('coronaStatus').textContent=`Corona ${data.minimumFrontierGeneration??'closed'}`;
  const m=data.learning;$('learningStats').textContent=`${data.tiles.length} tiles · ${data.stats.proposals} proposals · ${data.stats.backtracks} backtracks · ${(data.computeMs/1000).toFixed(2)} s${m?` · ${m.rules} learned pair orbits · ${m.addresses} template point addresses`:''}`;
  view=null;draw();if(running)requestAnimationFrame(()=>advance(false));};
 worker.postMessage({type:'init',mode});}
function advance(step){if(busy||state?.done)return;busy=true;worker.postMessage({type:'advance',targetCorona:target,step});}
function pointData(){const points=new Map(),tables=new Map((state.learning?.tables||[]).map(t=>[t.type,t.rows]));
 const get=p=>{const key=latticeKey(p);if(!points.has(key))points.set(key,{point:p,total:0,values:new Map(),marked:false});return points.get(key);};
 for(const tile of state.tiles){tile.exactPoints.forEach((p,i)=>get(p).total+=tile.weights[i]);if($('showPoints').checked)for(const r of tables.get(tile.type)||[]){const p=get(cycloAdd(tile.origin,r.offset));p.marked=true;const old=p.values.get(r.channel);p.values.set(r.channel,old!==undefined&&old!==r.value?'conflict':r.value);}}
 return [...points.values()];}
function draw(){const bounds=canvas.getBoundingClientRect(),dpr=devicePixelRatio||1;canvas.width=Math.round(bounds.width*dpr);canvas.height=Math.round(bounds.height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,bounds.width,bounds.height);if(!state?.tiles.length)return;
 const points=pointData(),all=points.map(p=>embedding(p.point));if(!view){const xs=all.map(p=>p.x),ys=all.map(p=>p.y),loX=Math.min(...xs),hiX=Math.max(...xs),loY=Math.min(...ys),hiY=Math.max(...ys);view={x:(loX+hiX)/2,y:(loY+hiY)/2,scale:Math.min((bounds.width-70)/Math.max(1,hiX-loX),(bounds.height-70)/Math.max(1,hiY-loY))};}
 const screen=p=>({x:bounds.width/2+(p.x-view.x)*view.scale,y:bounds.height/2-(p.y-view.y)*view.scale});
 for(const tile of state.tiles){const loop=tile.exactPoints.map(p=>screen(embedding(p)));ctx.beginPath();loop.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fillStyle=tile.kind==='thick'?'#b7d8c8':'#ecc888';ctx.fill();ctx.strokeStyle='#3f5653';ctx.lineWidth=1;ctx.stroke();}
 if($('searchMode').value==='known'&&$('showPoints').checked)for(const tile of state.tiles)for(const bar of extendedBars(known.decorate(tile),2)){const a=screen(embedding(bar.from)),b=screen(embedding(bar.to));ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.strokeStyle='#733bd266';ctx.lineWidth=1;ctx.stroke();}
 hits=points.map(p=>({...p,...screen(embedding(p.point))}));for(const p of hits){ctx.beginPath();ctx.arc(p.x,p.y,p.marked?3:1.5,0,Math.PI*2);ctx.fillStyle=p.marked?'#733bd2':'#51645d';ctx.fill();}}
$('runLearning').onclick=()=>{running=!running;$('runLearning').textContent=running?'Pause':'Run';if(running)advance(false);};$('stepLearning').onclick=()=>{running=false;advance(true);};$('resetLearning').onclick=initialize;$('searchMode').onchange=initialize;$('fitLearning').onclick=()=>{view=null;draw();};$('showPoints').onchange=draw;
canvas.onpointermove=e=>{const r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;const p=hits.reduce((best,p)=>Math.hypot(p.x-x,p.y-y)<Math.min(9,best?Math.hypot(best.x-x,best.y-y):Infinity)?p:best,null);$('pointInfo').textContent=p?`${coordinate(p.point)}\n t = ${p.total}/10; m = ${p.values.size?[...p.values].sort((a,b)=>a[0]-b[0]).map(([c,v])=>`${c}:${v}`).join(', '):'undefined'}${p.values.size?' (unlisted channels undefined)':''}`:'';};
new ResizeObserver(draw).observe(canvas);initialize();
